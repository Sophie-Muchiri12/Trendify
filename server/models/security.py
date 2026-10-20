"""Security-related tables: one-time tokens, revoked JWTs and the audit trail."""
import hashlib
import json

from database import db
from models.user import utcnow


class UserToken(db.Model):
    """Single-use, time-limited tokens for email verification and password reset.

    Only a SHA-256 hash of the token is stored, so a database leak does not expose
    usable links (A03 / A06).
    """
    __tablename__ = 'user_tokens'

    PURPOSES = ('verify_email', 'reset_password')

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False, index=True)
    purpose = db.Column(db.String(20), nullable=False)
    token_hash = db.Column(db.String(64), nullable=False, unique=True)
    expires_at = db.Column(db.DateTime, nullable=False)
    used_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=utcnow)

    user = db.relationship('User')


class RevokedToken(db.Model):
    """JWT ids invalidated by logout before they expire."""
    __tablename__ = 'revoked_tokens'

    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(36), nullable=False, unique=True, index=True)
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow)


class AuditLog(db.Model):
    """Append-only audit trail (A08).

    Each row stores a SHA-256 hash of its own content plus the previous row's hash, so
    editing or deleting a past entry breaks the chain and is detected by verify_chain().
    """
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow, index=True)
    action = db.Column(db.String(64), nullable=False, index=True)
    outcome = db.Column(db.String(10), nullable=False)  # success | failure | denied
    actor_user_id = db.Column(db.Integer, index=True)
    actor_email = db.Column(db.String(255))
    ip_address = db.Column(db.String(45), index=True)
    target_type = db.Column(db.String(30))
    target_id = db.Column(db.String(64))
    details = db.Column(db.JSON)
    prev_hash = db.Column(db.String(64), nullable=False)
    hash = db.Column(db.String(64), nullable=False)

    def compute_hash(self):
        payload = json.dumps({
            "created_at": self.created_at.isoformat(timespec="microseconds"),
            "action": self.action,
            "outcome": self.outcome,
            "actor_user_id": self.actor_user_id,
            "actor_email": self.actor_email,
            "ip_address": self.ip_address,
            "target_type": self.target_type,
            "target_id": self.target_id,
            "details": self.details,
            "prev_hash": self.prev_hash,
        }, sort_keys=True, separators=(",", ":"), default=str)
        return hashlib.sha256(payload.encode()).hexdigest()

    def to_dict(self):
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat(),
            "action": self.action,
            "outcome": self.outcome,
            "actor_user_id": self.actor_user_id,
            "actor_email": self.actor_email,
            "ip_address": self.ip_address,
            "target_type": self.target_type,
            "target_id": self.target_id,
            "details": self.details,
        }
