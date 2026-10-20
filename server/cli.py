"""Management commands: `flask create-admin`, `flask prune-tokens`, `flask verify-audit-log`."""
import click

from audit import audit, verify_chain
from database import db
from models import RevokedToken, User, UserToken
from models.user import utcnow
from security import hash_password, password_problems


def register_cli(app):
    @app.cli.command("create-admin")
    @click.option("--email", prompt=True, help="Email address of the administrator")
    @click.option("--name", prompt=True, default="Administrator", help="Display name")
    @click.option("--phone", default="", help="Phone number (optional)")
    @click.password_option(help="Password (prompted and confirmed if omitted)")
    def create_admin(email, name, phone, password):
        """Create an administrator, or promote an existing account.

        There is deliberately no HTTP endpoint for this: admins can only be created by
        someone with shell access to the server, or by another admin in the admin panel.
        """
        email = email.strip().lower()
        problems = password_problems(password, email, name)
        if problems:
            raise click.ClickException("Password too weak: " + " ".join(problems))
        user = User.query.filter_by(email=email).first()
        if user:
            user.role = "admin"
            user.password_hash = hash_password(password)
            user.is_active = True
            user.token_version += 1
            action = "promoted"
        else:
            user = User(email=email, name=name.strip() or "Administrator", phone_number=phone,
                        password_hash=hash_password(password), role="admin")
            db.session.add(user)
            action = "created"
        user.email_verified_at = user.email_verified_at or utcnow()
        db.session.flush()
        audit("user.create_admin_cli", target=user, actor_email="cli", details={"action": action})
        db.session.commit()
        click.echo(f"Administrator {email} {action}.")

    @app.cli.command("prune-tokens")
    def prune_tokens():
        """Delete expired revoked-token and one-time-token rows."""
        now = utcnow()
        revoked = RevokedToken.query.filter(RevokedToken.expires_at < now).delete()
        tokens = UserToken.query.filter(UserToken.expires_at < now).delete()
        db.session.commit()
        click.echo(f"Removed {revoked} revoked tokens and {tokens} expired one-time tokens.")

    @app.cli.command("verify-audit-log")
    def verify_audit_log():
        """Check the audit log hash chain for tampering."""
        ok, bad_id, count = verify_chain()
        if ok:
            click.echo(f"Audit log intact ({count} entries checked).")
        else:
            raise click.ClickException(f"Audit log has been modified: chain breaks at entry {bad_id}.")
