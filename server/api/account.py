"""The signed-in customer's own account: profile, password, MFA, reviews, closing the account."""
import secrets

import pyotp
from flask import Blueprint, current_app, jsonify
from flask_jwt_extended import unset_jwt_cookies

from api.auth import issue_session
from audit import audit
from errors import ApiError
from extensions import db, limiter
from mailer import send_email
from models import Review, User
from security import (current_user, decrypt_value, encrypt_value, hash_password, login_required,
                      require_strong_password, verify_password)
from services import refresh_product_rating
from validation import (ChangePasswordSchema, MfaCodeSchema, MfaDisableSchema, PasswordConfirmSchema,
                        ProfileUpdateSchema, load_json)

bp = Blueprint("account", __name__, url_prefix="/account")


def _require_password(user, password, action):
    ok, _ = verify_password(user.password_hash, password)
    if not ok:
        audit(action, "failure", actor=user, details={"reason": "bad_password"}, commit=True)
        raise ApiError(400, "Your current password is incorrect.", fields={"password": ["Incorrect password."]})


@bp.get("")
@login_required
def get_account():
    return jsonify(user=current_user().to_dict())


@bp.patch("")
@login_required
def update_account():
    user = current_user()
    data = load_json(ProfileUpdateSchema())
    changed = {k: v for k, v in data.items() if getattr(user, k) != v}
    for key, value in changed.items():
        setattr(user, key, value)
    if changed:
        audit("account.update", actor=user, target=user, details={"fields": sorted(changed)})
    db.session.commit()
    return jsonify(user=user.to_dict())


@bp.post("/change-password")
@limiter.limit("5 per hour")
@login_required
def change_password():
    user = current_user()
    data = load_json(ChangePasswordSchema())
    _require_password(user, data["current_password"], "account.change_password")
    require_strong_password(data["new_password"], user.email, user.name, field="new_password")
    if data["new_password"] == data["current_password"]:
        raise ApiError(400, "Choose a password you haven't used here before.",
                       fields={"new_password": ["Must differ from your current password."]})
    user.password_hash = hash_password(data["new_password"])
    user.token_version += 1  # other devices are signed out
    audit("account.change_password", actor=user, target=user)
    db.session.commit()
    send_email(user.email, "Your Trendify password was changed",
               "Your password was just changed. If this wasn't you, reset it immediately.")
    # Keep *this* session signed in with fresh tokens.
    return issue_session(jsonify(message="Password updated. Other devices have been signed out."), user)


@bp.delete("")
@limiter.limit("5 per hour")
@login_required
def close_account():
    user = current_user()
    data = load_json(PasswordConfirmSchema())
    _require_password(user, data["password"], "account.close")
    if user.is_admin() and User.query.filter_by(role="admin", is_active=True).count() <= 1:
        raise ApiError(409, "You're the only administrator. Make someone else an admin first.")

    # Orders are kept for accounting, but personal data is removed and the account disabled.
    products = {r.product for r in user.reviews}
    for review in list(user.reviews):
        db.session.delete(review)
    db.session.flush()
    for product in products:
        refresh_product_rating(product)
    original_id = user.user_id
    user.name = "Deleted user"
    user.email = f"deleted-{original_id}-{secrets.token_hex(4)}@deleted.invalid"
    user.phone_number = ""
    user.password_hash = hash_password(secrets.token_urlsafe(32))
    user.is_active = False
    user.mfa_enabled = False
    user.mfa_secret_encrypted = None
    user.token_version += 1
    audit("account.close", actor=user, target=user)
    db.session.commit()
    response = jsonify(message="Your account has been closed.")
    unset_jwt_cookies(response)
    return response


@bp.get("/reviews")
@login_required
def my_reviews():
    reviews = Review.query.filter_by(user_id=current_user().user_id).order_by(Review.created_at.desc()).all()
    return jsonify(items=[r.to_owner_dict() for r in reviews])


# --- Multi-factor authentication (TOTP) ------------------------------------------------

@bp.post("/mfa/setup")
@limiter.limit("10 per hour")
@login_required
def mfa_setup():
    user = current_user()
    data = load_json(PasswordConfirmSchema())
    _require_password(user, data["password"], "account.mfa_setup")
    if user.mfa_enabled:
        raise ApiError(409, "Two-factor authentication is already on.")
    secret = pyotp.random_base32()
    user.mfa_secret_encrypted = encrypt_value(secret)
    db.session.commit()
    uri = pyotp.TOTP(secret).provisioning_uri(name=user.email, issuer_name=current_app.config["MFA_ISSUER"])
    # The secret is shown once so it can be added to an authenticator app.
    return jsonify(secret=secret, otpauth_uri=uri)


@bp.post("/mfa/enable")
@limiter.limit("10 per hour")
@login_required
def mfa_enable():
    user = current_user()
    data = load_json(MfaCodeSchema())
    secret = decrypt_value(user.mfa_secret_encrypted or "")
    if not secret:
        raise ApiError(400, "Start two-factor setup first.")
    if not pyotp.TOTP(secret).verify(data["code"], valid_window=1):
        audit("account.mfa_enable", "failure", actor=user, details={"reason": "bad_code"}, commit=True)
        raise ApiError(400, "That code isn't valid. Check the time on your phone and try again.",
                       fields={"code": ["Invalid code."]})
    user.mfa_enabled = True
    audit("account.mfa_enable", actor=user, target=user)
    db.session.commit()
    send_email(user.email, "Two-factor authentication turned on",
               "Two-factor authentication is now required when you sign in to Trendify.")
    return jsonify(user=user.to_dict())


@bp.post("/mfa/disable")
@limiter.limit("10 per hour")
@login_required
def mfa_disable():
    user = current_user()
    data = load_json(MfaDisableSchema())
    _require_password(user, data["password"], "account.mfa_disable")
    secret = decrypt_value(user.mfa_secret_encrypted or "")
    if not user.mfa_enabled or not secret or not pyotp.TOTP(secret).verify(data["code"], valid_window=1):
        audit("account.mfa_disable", "failure", actor=user, details={"reason": "bad_code"}, commit=True)
        raise ApiError(400, "That code isn't valid.", fields={"code": ["Invalid code."]})
    user.mfa_enabled = False
    user.mfa_secret_encrypted = None
    audit("account.mfa_disable", actor=user, target=user)
    db.session.commit()
    send_email(user.email, "Two-factor authentication turned off",
               "Two-factor authentication was turned off for your Trendify account. "
               "If this wasn't you, reset your password immediately.")
    return jsonify(user=user.to_dict())

