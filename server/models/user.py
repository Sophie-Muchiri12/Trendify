from datetime import datetime, timezone

from database import db


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class User(db.Model):
    __tablename__ = 'users'

    ROLES = ('customer', 'admin')

    user_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    phone_number = db.Column(db.String(20), nullable=False, default='')
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='customer')
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    email_verified_at = db.Column(db.DateTime)

    # Brute-force protection (A06)
    failed_login_count = db.Column(db.Integer, nullable=False, default=0)
    locked_until = db.Column(db.DateTime)
    last_login_at = db.Column(db.DateTime)

    # Bumped on password change, logout-everywhere and deactivation; tokens carrying an
    # older version are rejected, which ends every existing session at once.
    token_version = db.Column(db.Integer, nullable=False, default=0)

    # Optional TOTP multi-factor authentication. The secret is encrypted at rest (A03).
    mfa_secret_encrypted = db.Column(db.String(255))
    mfa_enabled = db.Column(db.Boolean, nullable=False, default=False)

    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)

    # Relationships (orders are kept when an account is closed, so no delete cascade)
    orders = db.relationship('Order', back_populates='user')
    reviews = db.relationship('Review', back_populates='user', cascade='all, delete-orphan')

    def is_admin(self):
        return self.role == 'admin'

    @property
    def email_verified(self):
        return self.email_verified_at is not None

    def is_locked(self, now=None):
        return self.locked_until is not None and self.locked_until > (now or utcnow())

    def to_dict(self):
        """What the user may see about themselves."""
        return {
            "user_id": self.user_id,
            "name": self.name,
            "email": self.email,
            "phone_number": self.phone_number,
            "role": self.role,
            "email_verified": self.email_verified,
            "mfa_enabled": self.mfa_enabled,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def to_admin_dict(self):
        data = self.to_dict()
        data.update({
            "is_active": self.is_active,
            "locked": self.is_locked(),
            "failed_login_count": self.failed_login_count,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
            "order_count": len(self.orders),
        })
        return data
