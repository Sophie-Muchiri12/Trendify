"""Registration, login, sessions, email verification and password reset (A06)."""
from datetime import datetime, timezone

import pyotp
from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import (create_access_token, create_refresh_token, decode_token,
                                get_jwt_identity, jwt_required, set_access_cookies,
                                set_refresh_cookies, unset_jwt_cookies, verify_jwt_in_request)
from flask_jwt_extended.exceptions import JWTExtendedException
from jwt import PyJWTError

from audit import alert, audit, check_login_failures
from errors import ApiError
from extensions import db, limiter
from mailer import frontend_link, send_email
from models import RevokedToken, User, UserToken
from models.user import utcnow
from security import (burn_password_check, client_ip, current_user, decrypt_value, hash_password,
                      hash_token, login_required, new_token, require_strong_password, verify_password)
from validation import (EmailOnlySchema, LoginSchema, RegisterSchema, ResetPasswordSchema,
                        TokenSchema, load_json)

bp = Blueprint("auth", __name__, url_prefix="/auth")


# --- helpers ------------------------------------------------------------------

def issue_session(response, user):
    """Set HttpOnly access + refresh cookies (plus their CSRF companions)."""
    claims = {"tv": user.token_version, "role": user.role}
    set_access_cookies(response, create_access_token(identity=str(user.user_id), additional_claims=claims))
    set_refresh_cookies(response, create_refresh_token(identity=str(user.user_id),
                                                       additional_claims={"tv": user.token_version}))
    return response


def _create_user_token(user, purpose, lifetime):
    # Only the newest link of each kind works.
    UserToken.query.filter_by(user_id=user.user_id, purpose=purpose, used_at=None).update({"used_at": utcnow()})
    raw, digest = new_token()
    db.session.add(UserToken(user_id=user.user_id, purpose=purpose, token_hash=digest,
                             expires_at=utcnow() + lifetime))
    return raw


def _find_user_token(raw, purpose):
    """Return the valid, unused token row for this link, or None."""
    token = UserToken.query.filter_by(token_hash=hash_token(raw), purpose=purpose).first()
    if token is None or token.used_at is not None or token.expires_at < utcnow() or not token.user.is_active:
        return None
    return token


def send_verification_email(user):
    raw = _create_user_token(user, "verify_email", current_app.config["EMAIL_TOKEN_EXPIRES"])
    link = frontend_link("/verify-email", token=raw)
    send_email(user.email, "Verify your Trendify email address",
               f"Hi {user.name},\n\nConfirm your email address to start shopping:\n{link}\n\n"
               "The link expires in 24 hours. If you didn't create an account, ignore this email.")


def _register_failed_login(user, reason):
    user.failed_login_count += 1
    if user.failed_login_count >= current_app.config["LOGIN_MAX_FAILED_ATTEMPTS"]:
        user.locked_until = utcnow() + current_app.config["LOGIN_LOCKOUT_PERIOD"]
        user.failed_login_count = 0
        alert("account_locked", f"Account {user.user_id} locked after repeated failed logins",
              user_id=user.user_id, ip=client_ip())
        send_email(user.email, "Your Trendify account was temporarily locked",
                   "We locked your account for 15 minutes after several failed sign-in attempts.\n"
                   "If this wasn't you, reset your password: " + frontend_link("/forgot-password"))
    audit("auth.login", "failure", actor=user, details={"reason": reason}, commit=True)
    check_login_failures(client_ip())


# --- endpoints ------------------------------------------------------------------

@bp.post("/register")
@limiter.limit("5 per hour; 20 per day")
def register():
    data = load_json(RegisterSchema())
    email = data["email"].lower()
    require_strong_password(data["password"], email, data["name"])
    # The same answer whether or not the email is taken, so the endpoint can't be used
    # to find out who has an account.
    response = jsonify(message="Thanks! Check your email for a link to verify your account."), 201

    if User.query.filter_by(email=email).first():
        send_email(email, "Someone tried to create a Trendify account with your email",
                   "If that was you, you already have an account. Sign in or reset your password here: "
                   + frontend_link("/forgot-password"))
        audit("auth.register", "failure", actor_email=email, details={"reason": "email_exists"}, commit=True)
        return response

    user = User(name=data["name"], email=email, phone_number=data["phone_number"],
                password_hash=hash_password(data["password"]), role="customer")
    db.session.add(user)
    db.session.flush()
    send_verification_email(user)
    audit("auth.register", actor=user, target=user)
    db.session.commit()
    return response


@bp.post("/login")
@limiter.limit("10 per minute; 100 per hour")
def login():
    data = load_json(LoginSchema())
    email = data["email"].lower()
    user = User.query.filter_by(email=email).first()

    if user is None or not user.is_active:
        burn_password_check(data["password"])  # keep timing the same as a real check
        audit("auth.login", "failure", actor_email=email, details={"reason": "unknown_or_inactive"}, commit=True)
        check_login_failures(client_ip())
        raise ApiError(401, "Invalid email or password.")

    if user.is_locked():
        audit("auth.login", "failure", actor=user, details={"reason": "locked"}, commit=True)
        raise ApiError(423, "Too many failed attempts. Try again in 15 minutes or reset your password.",
                       code="account_locked")

    ok, needs_rehash = verify_password(user.password_hash, data["password"])
    if not ok:
        _register_failed_login(user, "bad_password")
        raise ApiError(401, "Invalid email or password.")

    if user.mfa_enabled:
        if not data.get("otp"):
            return jsonify(error="Enter the 6-digit code from your authenticator app.",
                           code="mfa_required"), 401
        secret = decrypt_value(user.mfa_secret_encrypted or "")
        if not secret or not pyotp.TOTP(secret).verify(data["otp"], valid_window=1):
            _register_failed_login(user, "bad_otp")
            raise ApiError(401, "That code isn't valid. Check your authenticator app and try again.",
                           code="mfa_invalid")

    user.failed_login_count = 0
    user.locked_until = None
    user.last_login_at = utcnow()
    if needs_rehash:
        user.password_hash = hash_password(data["password"])  # upgrade old hashes to Argon2
    audit("auth.login", actor=user, details={"mfa": user.mfa_enabled})
    db.session.commit()
    return issue_session(jsonify(user=user.to_dict()), user)


@bp.post("/refresh")
@limiter.limit("60 per minute")
@jwt_required(refresh=True)
def refresh():
    # The blocklist loader has already rejected revoked/stale refresh tokens.
    user = db.session.get(User, int(get_jwt_identity()))
    response = jsonify(user=user.to_dict())
    claims = {"tv": user.token_version, "role": user.role}
    set_access_cookies(response, create_access_token(identity=str(user.user_id), additional_claims=claims))
    return response


@bp.post("/logout")
def logout():
    """Revoke the current access and refresh tokens, even if the access token expired."""
    actor = None
    for cookie in (current_app.config["JWT_ACCESS_COOKIE_NAME"], current_app.config["JWT_REFRESH_COOKIE_NAME"]):
        raw = request.cookies.get(cookie)
        if not raw:
            continue
        try:
            payload = decode_token(raw, allow_expired=True)
        except (JWTExtendedException, PyJWTError):
            continue
        if not RevokedToken.query.filter_by(jti=payload["jti"]).first():
            expires = datetime.fromtimestamp(payload["exp"], timezone.utc).replace(tzinfo=None)
            db.session.add(RevokedToken(jti=payload["jti"], expires_at=expires))
        actor = actor or db.session.get(User, int(payload["sub"]))
    if actor:
        audit("auth.logout", actor=actor)
    db.session.commit()
    response = jsonify(message="Signed out.")
    unset_jwt_cookies(response)
    return response


@bp.post("/logout-all")
@login_required
def logout_all():
    """End every session on every device by bumping the token version."""
    user = current_user()
    user.token_version += 1
    audit("auth.logout_all", actor=user)
    db.session.commit()
    response = jsonify(message="Signed out on all devices.")
    unset_jwt_cookies(response)
    return response


@bp.get("/me")
def me():
    try:
        verify_jwt_in_request(optional=True)
    except (JWTExtendedException, PyJWTError):
        raise ApiError(401, "Please sign in again.", code="token_invalid")
    identity = get_jwt_identity()
    if identity is None:
        return jsonify(user=None)
    user = db.session.get(User, int(identity))
    return jsonify(user=user.to_dict() if user and user.is_active else None)


@bp.post("/verify-email")
@limiter.limit("20 per hour")
def verify_email():
    data = load_json(TokenSchema())
    token = _find_user_token(data["token"], "verify_email")
    if token is None:
        raise ApiError(400, "This verification link is invalid or has expired.", code="token_invalid")
    token.used_at = utcnow()
    user = token.user
    user.email_verified_at = user.email_verified_at or utcnow()
    audit("auth.verify_email", actor=user, target=user)
    db.session.commit()
    return jsonify(message="Email verified. You can now place orders.", user=user.to_dict())


@bp.post("/resend-verification")
@limiter.limit("3 per hour")
@login_required
def resend_verification():
    user = current_user()
    if not user.email_verified:
        send_verification_email(user)
        audit("auth.resend_verification", actor=user)
        db.session.commit()
    return jsonify(message="We've sent a new verification link.")


@bp.post("/forgot-password")
@limiter.limit("5 per hour")
def forgot_password():
    data = load_json(EmailOnlySchema())
    email = data["email"].lower()
    user = User.query.filter_by(email=email).first()
    if user and user.is_active:
        raw = _create_user_token(user, "reset_password", current_app.config["PASSWORD_RESET_EXPIRES"])
        send_email(user.email, "Reset your Trendify password",
                   f"Hi {user.name},\n\nReset your password here (the link expires in 30 minutes):\n"
                   f"{frontend_link('/reset-password', token=raw)}\n\n"
                   "If you didn't ask for this, you can ignore this email.")
        audit("auth.password_reset_requested", actor=user)
        db.session.commit()
    else:
        audit("auth.password_reset_requested", "failure", actor_email=email,
              details={"reason": "unknown_or_inactive"}, commit=True)
    # Same response either way (no account enumeration).
    return jsonify(message="If that email has an account, we've sent a reset link.")


@bp.post("/reset-password")
@limiter.limit("10 per hour")
def reset_password():
    data = load_json(ResetPasswordSchema())
    token = _find_user_token(data["token"], "reset_password")
    if token is None:
        raise ApiError(400, "This reset link is invalid or has expired.", code="token_invalid")
    user = token.user
    # Check the new password before using up the link, so a typo doesn't waste it.
    require_strong_password(data["password"], user.email, user.name)
    token.used_at = utcnow()
    user.password_hash = hash_password(data["password"])
    user.token_version += 1  # sign out every existing session
    user.failed_login_count = 0
    user.locked_until = None
    user.email_verified_at = user.email_verified_at or utcnow()  # they proved they own the inbox
    audit("auth.password_reset", actor=user, target=user)
    db.session.commit()
    send_email(user.email, "Your Trendify password was changed",
               "Your password was just reset. If this wasn't you, contact support immediately.")
    return jsonify(message="Your password has been reset. Please sign in.")
