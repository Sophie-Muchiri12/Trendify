"""Security logging, audit trail and alerting (A08).

* audit() writes an entry to the hash-chained AuditLog table and to the security log
  file (instance/logs/security.log, JSON lines).
* Secrets are scrubbed before anything is recorded: passwords, tokens, OTP codes and
  card/payment credentials never reach the logs.
* alert() flags significant events (account lockouts, repeated authorization failures,
  payment mismatches) in the log and, if SECURITY_ALERT_EMAIL is set, by email.
"""
import json
import logging
import os
import time
from datetime import timedelta
from logging.handlers import RotatingFileHandler

from flask import current_app, g, has_request_context, request

from database import db
from models.security import AuditLog
from models.user import utcnow

security_log = logging.getLogger("trendify.security")

SENSITIVE_KEYS = {
    "password", "current_password", "new_password", "token", "access_token", "refresh_token",
    "otp", "code", "mfa_secret", "secret", "authorization", "cookie", "card", "cvv",
    "consumer_secret", "csrf",
}

GENESIS_HASH = "0" * 64


def scrub(value):
    """Recursively replace sensitive values with '[redacted]'."""
    if isinstance(value, dict):
        return {
            k: "[redacted]" if any(s in str(k).lower() for s in SENSITIVE_KEYS) else scrub(v)
            for k, v in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [scrub(v) for v in value]
    return value


class JsonLineFormatter(logging.Formatter):
    def format(self, record):
        entry = getattr(record, "entry", None) or {"message": record.getMessage()}
        entry = {"ts": utcnow().isoformat(), "level": record.levelname, **entry}
        return json.dumps(entry, default=str)


def configure_security_logging(app):
    if app.testing:
        return
    log_dir = os.path.join(app.instance_path, "logs")
    os.makedirs(log_dir, mode=0o700, exist_ok=True)
    path = os.path.join(log_dir, "security.log")
    if not any(isinstance(h, RotatingFileHandler) and h.baseFilename == path for h in security_log.handlers):
        handler = RotatingFileHandler(path, maxBytes=5 * 1024 * 1024, backupCount=10)
        handler.setFormatter(JsonLineFormatter())
        security_log.addHandler(handler)
        try:
            os.chmod(path, 0o600)  # readable only by the account running the server
        except OSError:
            pass
    security_log.setLevel(logging.INFO)


def _last_hash():
    last = AuditLog.query.order_by(AuditLog.id.desc()).first()
    return last.hash if last else GENESIS_HASH


def audit(action, outcome="success", *, actor=None, actor_email=None, target=None,
          target_type=None, target_id=None, details=None, commit=False):
    """Record a security-relevant event.

    The entry is added to the current database session so that it commits together
    with the change it describes (an audit row can't exist for a change that was rolled
    back, and vice versa). Pass commit=True for events that have no other change to go
    with, such as failed logins or denied requests.
    """
    if target is not None:
        target_type = target_type or target.__tablename__.rstrip("s")
        pk = target.__mapper__.primary_key[0].name
        target_id = target_id or getattr(target, pk)
    entry = AuditLog(
        created_at=utcnow(),
        action=action,
        outcome=outcome,
        actor_user_id=getattr(actor, "user_id", None),
        actor_email=actor_email or getattr(actor, "email", None),
        ip_address=request.remote_addr if has_request_context() else None,
        target_type=target_type,
        target_id=str(target_id) if target_id is not None else None,
        # Round-trip through JSON so the hashed value equals what is read back later.
        details=json.loads(json.dumps(scrub(details), default=str)) if details else None,
    )
    db.session.flush()  # make sure earlier audit rows in this transaction have ids
    entry.prev_hash = _last_hash()
    entry.hash = entry.compute_hash()
    db.session.add(entry)
    db.session.flush()
    if commit:
        db.session.commit()

    level = logging.WARNING if outcome in ("failure", "denied") else logging.INFO
    security_log.log(level, action, extra={"entry": {
        **entry.to_dict(),
        "request_id": g.get("request_id") if has_request_context() else None,
    }})
    return entry


def verify_chain():
    """Recompute every hash. Returns (ok, first_bad_id, checked_count)."""
    prev = GENESIS_HASH
    count = 0
    for entry in AuditLog.query.order_by(AuditLog.id).yield_per(500):
        count += 1
        if entry.prev_hash != prev or entry.compute_hash() != entry.hash:
            return False, entry.id, count
        prev = entry.hash
    return True, None, count


# --- Alerting ----------------------------------------------------------------------

_last_alert_sent = {}
ALERT_EMAIL_COOLDOWN_SECONDS = 600


def alert(kind, message, **details):
    """Raise a security alert: always logged at CRITICAL, optionally emailed."""
    details = scrub(details)
    security_log.critical("SECURITY ALERT: %s", kind, extra={"entry": {
        "alert": kind, "message": message, "details": details,
    }})
    audit(f"alert.{kind}", "failure", details={"message": message, **details})

    recipient = current_app.config.get("SECURITY_ALERT_EMAIL")
    now = time.monotonic()
    if recipient and now - _last_alert_sent.get(kind, -1e9) > ALERT_EMAIL_COOLDOWN_SECONDS:
        _last_alert_sent[kind] = now
        from mailer import send_email
        send_email(recipient, f"[Trendify security] {kind}",
                   f"{message}\n\nDetails: {json.dumps(details, default=str, indent=2)}")


def recent_count(action, outcome, *, within=timedelta(minutes=10), actor_user_id=None, ip_address=None):
    q = AuditLog.query.filter(AuditLog.action == action, AuditLog.outcome == outcome,
                              AuditLog.created_at >= utcnow() - within)
    if actor_user_id is not None:
        q = q.filter(AuditLog.actor_user_id == actor_user_id)
    if ip_address is not None:
        q = q.filter(AuditLog.ip_address == ip_address)
    return q.count()


AUTHZ_ALERT_THRESHOLD = 5


def check_authz_failures(user):
    """Alert when one account keeps hitting endpoints it isn't allowed to use."""
    count = recent_count("authz.denied", "denied", actor_user_id=user.user_id)
    if count == AUTHZ_ALERT_THRESHOLD:
        alert("repeated_authorization_failures",
              f"User {user.user_id} was denied access {count} times in 10 minutes",
              user_id=user.user_id, ip=request.remote_addr)
        db.session.commit()


FAILED_LOGIN_IP_THRESHOLD = 20


def check_login_failures(ip):
    """Alert on many failed logins from one IP (credential stuffing / brute force)."""
    count = recent_count("auth.login", "failure", ip_address=ip)
    if count == FAILED_LOGIN_IP_THRESHOLD:
        alert("credential_stuffing_suspected",
              f"{count} failed logins from {ip} in 10 minutes", ip=ip)
        db.session.commit()
