"""Password hashing, password policy, encryption, one-time tokens and access-control decorators."""
import base64
import hashlib
import secrets
from functools import wraps

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from flask import current_app, g, request
from flask_jwt_extended import get_jwt, get_jwt_identity, verify_jwt_in_request
from werkzeug.security import check_password_hash

from errors import ApiError

# --- Passwords (A03 / A06) ------------------------------------------------------

_hasher = PasswordHasher()  # Argon2id with the library's recommended parameters

# A small blocklist of the most common passwords; length + variety rules catch the rest.
COMMON_PASSWORDS = {
    "password", "password1", "password123", "123456789", "1234567890", "qwerty123",
    "qwertyuiop", "iloveyou1", "admin12345", "welcome123", "letmein123", "trendify123",
    "abc1234567", "passw0rd123", "football123", "monkey12345", "dragon12345",
}


def hash_password(password):
    return _hasher.hash(password)


def verify_password(stored_hash, password):
    """Return (matches, needs_rehash).

    Accepts Argon2 hashes and the older Werkzeug (pbkdf2/scrypt) hashes created before
    the switch, so existing users can still log in; those are upgraded on success.
    """
    if not stored_hash:
        return False, False
    if stored_hash.startswith("$argon2"):
        try:
            _hasher.verify(stored_hash, password)
        except (VerifyMismatchError, VerificationError, InvalidHashError):
            return False, False
        return True, _hasher.check_needs_rehash(stored_hash)
    try:
        return check_password_hash(stored_hash, password), True
    except ValueError:
        return False, False


# Compared against when the email doesn't exist, so response time doesn't reveal accounts.
_DUMMY_HASH = _hasher.hash(secrets.token_urlsafe(16))


def burn_password_check(password):
    verify_password(_DUMMY_HASH, password)


def password_problems(password, email="", name=""):
    """Return a list of reasons the password is too weak (empty list = acceptable)."""
    problems = []
    if not isinstance(password, str):
        return ["Password is required."]
    if len(password) < 10:
        problems.append("Use at least 10 characters.")
    if len(password) > 128:
        problems.append("Use at most 128 characters.")
    if not any(c.isalpha() for c in password) or not any(c.isdigit() for c in password):
        problems.append("Use both letters and numbers.")
    if not (any(c.islower() for c in password) and any(c.isupper() for c in password)):
        problems.append("Use both upper- and lower-case letters.")
    lowered = password.lower()
    if lowered in COMMON_PASSWORDS:
        problems.append("This password is too common.")
    local_part = (email or "").split("@")[0].lower()
    if len(local_part) >= 4 and local_part in lowered:
        problems.append("Don't include your email address in your password.")
    for part in (name or "").lower().split():
        if len(part) >= 4 and part in lowered:
            problems.append("Don't include your name in your password.")
            break
    return problems


def require_strong_password(password, email="", name="", field="password"):
    problems = password_problems(password, email, name)
    if problems:
        raise ApiError(400, "Password does not meet the requirements.", fields={field: problems})


# --- Encryption of sensitive columns (A03) -------------------------------------------

def _fernet():
    key = current_app.config.get("ENCRYPTION_KEY")
    if not key:
        # Development fallback: derive a stable key from SECRET_KEY. Production must set
        # ENCRYPTION_KEY explicitly (enforced by ProductionConfig.validate).
        derived = HKDF(
            algorithm=hashes.SHA256(), length=32, salt=b"trendify-field-encryption", info=b"fernet"
        ).derive(current_app.config["SECRET_KEY"].encode())
        key = base64.urlsafe_b64encode(derived)
    return Fernet(key)


def encrypt_value(plaintext):
    return _fernet().encrypt(plaintext.encode()).decode()


def decrypt_value(ciphertext):
    try:
        return _fernet().decrypt(ciphertext.encode()).decode()
    except (InvalidToken, AttributeError):
        return None


# --- One-time tokens ----------------------------------------------------------------

def new_token():
    """Return (raw_token_for_the_link, sha256_hash_to_store)."""
    raw = secrets.token_urlsafe(32)
    return raw, hash_token(raw)


def hash_token(raw):
    return hashlib.sha256(raw.encode()).hexdigest()


# --- Request helpers -------------------------------------------------------------------

def client_ip():
    return request.remote_addr or "unknown"


# --- Access control (A01) ----------------------------------------------------------------
# Every protected endpoint must use one of these decorators; the default for anything
# else in the API is public read-only catalog data.

def _load_current_user():
    from models import User, db  # local import avoids a circular import at module load

    verify_jwt_in_request()
    user = db.session.get(User, int(get_jwt_identity()))
    # The token blocklist loader already rejects inactive users and stale token
    # versions; this is a second, explicit check.
    if user is None or not user.is_active or get_jwt().get("tv") != user.token_version:
        raise ApiError(401, "Please sign in again.")
    g.current_user = user
    return user


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        _load_current_user()
        return fn(*args, **kwargs)
    return wrapper


def verified_required(fn):
    """Signed in *and* email verified (needed to order or review)."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = _load_current_user()
        if not user.email_verified:
            raise ApiError(403, "Please verify your email address first.", code="email_unverified")
        return fn(*args, **kwargs)
    return wrapper


def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        from audit import audit, check_authz_failures

        user = _load_current_user()
        if not user.is_admin():
            audit("authz.denied", "denied", actor=user,
                  details={"method": request.method, "path": request.path}, commit=True)
            check_authz_failures(user)
            raise ApiError(403, "You don't have permission to do that.")
        return fn(*args, **kwargs)
    return wrapper


def current_user():
    return g.get("current_user")
