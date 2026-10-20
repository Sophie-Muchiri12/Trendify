"""A06 Authentication failures, A03 cryptographic storage, A08 logging of auth events."""
from datetime import timedelta

import pyotp
from werkzeug.security import generate_password_hash

from conftest import PASSWORD, outbox, token_from_last_email
from extensions import db
from models import AuditLog, User, UserToken
from models.user import utcnow

NEW_USER = {"name": "Wanjiku Kamau", "email": "Wanjiku@Example.com", "phone_number": "+254711222333",
            "password": PASSWORD}


def test_register_creates_customer_with_argon2_hash_and_sends_verification(app, client):
    resp = client.post("/auth/register", NEW_USER, csrf=False)
    assert resp.status_code == 201
    user = User.query.filter_by(email="wanjiku@example.com").one()
    assert user.role == "customer"
    assert user.password_hash.startswith("$argon2id$")
    assert PASSWORD not in user.password_hash
    assert not user.email_verified
    assert "verify-email?token=" in outbox(app)[-1]["body"]


def test_register_rejects_mass_assignment_of_role(client):
    resp = client.post("/auth/register", {**NEW_USER, "role": "admin"}, csrf=False)
    assert resp.status_code == 400
    assert "role" in resp.get_json()["fields"]
    assert User.query.count() == 0


def test_register_enforces_password_policy(client):
    for weak in ["short1A", "alllowercase123", "NoDigitsHereAtAll", "Password123"[:8]]:
        resp = client.post("/auth/register", {**NEW_USER, "password": weak}, csrf=False)
        assert resp.status_code == 400, weak
        assert "password" in resp.get_json()["fields"]


def test_register_duplicate_email_gives_same_answer(app, client, customer):
    resp = client.post("/auth/register", {**NEW_USER, "email": customer.email}, csrf=False)
    assert resp.status_code == 201
    assert User.query.filter_by(email=customer.email).count() == 1
    assert "already have an account" in outbox(app)[-1]["body"]


def test_login_sets_httponly_strict_cookies_and_no_token_in_body(client, customer):
    resp = client.login(customer.email)
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert "access_token" not in body and "eyJ" not in body
    cookies = resp.headers.getlist("Set-Cookie")
    access = next(c for c in cookies if c.startswith("access_token_cookie="))
    assert "HttpOnly" in access and "SameSite=Strict" in access
    csrf = next(c for c in cookies if c.startswith("csrf_access_token="))
    assert "HttpOnly" not in csrf  # the frontend must be able to read it to send the header


def test_login_failures_are_generic(client, customer):
    wrong = client.login(customer.email, "Wr0ngPasswordX")
    unknown = client.login("nobody@example.com", "Wr0ngPasswordX")
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.get_json()["error"] == unknown.get_json()["error"] == "Invalid email or password."


def test_account_locks_after_repeated_failures(client, customer):
    for _ in range(5):
        assert client.login(customer.email, "Wr0ngPasswordX").status_code == 401
    resp = client.login(customer.email)  # correct password, but locked
    assert resp.status_code == 423
    assert AuditLog.query.filter_by(action="alert.account_locked").count() == 1


def test_lockout_expires(client, customer):
    for _ in range(5):
        client.login(customer.email, "Wr0ngPasswordX")
    user = db.session.get(User, customer.user_id)
    user.locked_until = utcnow() - timedelta(seconds=1)
    db.session.commit()
    assert client.login(customer.email).status_code == 200


def test_login_is_rate_limited(client):
    statuses = [client.login(f"user{i}@example.com", "Wr0ngPasswordX").status_code for i in range(11)]
    assert statuses[:10] == [401] * 10
    assert statuses[10] == 429


def test_legacy_werkzeug_hash_is_upgraded(client, make_user):
    user = make_user(email="legacy@example.com")
    user.password_hash = generate_password_hash(PASSWORD)
    db.session.commit()
    assert client.login("legacy@example.com").status_code == 200
    assert db.session.get(User, user.user_id).password_hash.startswith("$argon2")


def test_auth_events_are_audited_without_secrets(client, customer):
    client.login(customer.email, "Wr0ngPasswordX")
    client.login(customer.email)
    actions = [(a.action, a.outcome) for a in AuditLog.query.order_by(AuditLog.id)]
    assert ("auth.login", "failure") in actions and ("auth.login", "success") in actions
    for entry in AuditLog.query:
        assert PASSWORD not in str(entry.details) and "Wr0ngPasswordX" not in str(entry.details)


def test_mutations_require_csrf_header(customer_client):
    resp = customer_client.patch("/account", {"name": "New"}, csrf=False)
    assert resp.status_code == 401
    assert customer_client.patch("/account", {"name": "New"}).status_code == 200


def test_logout_revokes_tokens(customer_client):
    stolen = customer_client.client.get_cookie("access_token_cookie").value
    assert customer_client.post("/auth/logout").status_code == 200
    customer_client.client.set_cookie("access_token_cookie", stolen)
    assert customer_client.get("/account").status_code == 401


def test_password_change_signs_out_other_sessions(new_client, customer):
    phone, laptop = new_client(), new_client()
    phone.login(customer.email)
    laptop.login(customer.email)
    resp = laptop.post("/account/change-password",
                       {"current_password": PASSWORD, "new_password": "N3wSecurePassword"})
    assert resp.status_code == 200
    assert laptop.get("/account").status_code == 200  # this session got fresh tokens
    assert phone.get("/account").status_code == 401   # the other one is signed out


def test_change_password_requires_current_password(customer_client):
    resp = customer_client.post("/account/change-password",
                                {"current_password": "Wr0ngPasswordX", "new_password": "N3wSecurePassword"})
    assert resp.status_code == 400


def test_logout_all(new_client, customer):
    a, b = new_client(), new_client()
    a.login(customer.email)
    b.login(customer.email)
    assert a.post("/auth/logout-all").status_code == 200
    assert b.get("/account").status_code == 401


def test_refresh_issues_new_access_token(customer_client):
    customer_client.client.delete_cookie("access_token_cookie")
    assert customer_client.get("/account").status_code == 401
    assert customer_client.post("/auth/refresh", refresh=True).status_code == 200
    assert customer_client.get("/account").status_code == 200


def test_email_verification_flow(app, client):
    client.post("/auth/register", NEW_USER, csrf=False)
    token = token_from_last_email(app)
    assert client.post("/auth/verify-email", {"token": token}, csrf=False).status_code == 200
    assert User.query.filter_by(email="wanjiku@example.com").one().email_verified
    # Single use
    assert client.post("/auth/verify-email", {"token": token}, csrf=False).status_code == 400


def test_tokens_are_stored_hashed(app, client):
    client.post("/auth/register", NEW_USER, csrf=False)
    raw = token_from_last_email(app)
    assert UserToken.query.filter_by(token_hash=raw).first() is None


def test_password_reset_flow(app, client, customer):
    resp = client.post("/auth/forgot-password", {"email": customer.email}, csrf=False)
    unknown = client.post("/auth/forgot-password", {"email": "nobody@example.com"}, csrf=False)
    assert resp.get_json() == unknown.get_json()  # no account enumeration
    token = token_from_last_email(app)

    weak = client.post("/auth/reset-password", {"token": token, "password": "weak"}, csrf=False)
    assert weak.status_code == 400
    ok = client.post("/auth/reset-password", {"token": token, "password": "BrandN3wPassword"}, csrf=False)
    assert ok.status_code == 200
    assert client.login(customer.email).status_code == 401
    assert client.login(customer.email, "BrandN3wPassword").status_code == 200
    again = client.post("/auth/reset-password", {"token": token, "password": "An0therPassword"}, csrf=False)
    assert again.status_code == 400


def test_password_reset_token_expires(app, client, customer):
    client.post("/auth/forgot-password", {"email": customer.email}, csrf=False)
    token = token_from_last_email(app)
    UserToken.query.update({"expires_at": utcnow() - timedelta(minutes=1)})
    db.session.commit()
    resp = client.post("/auth/reset-password", {"token": token, "password": "BrandN3wPassword"}, csrf=False)
    assert resp.status_code == 400


def test_mfa_enrolment_and_login(customer_client, new_client, customer):
    setup = customer_client.post("/account/mfa/setup", {"password": PASSWORD}).get_json()
    secret = setup["secret"]
    assert setup["otpauth_uri"].startswith("otpauth://totp/")
    stored = db.session.get(User, customer.user_id).mfa_secret_encrypted
    assert stored and secret not in stored  # encrypted at rest

    assert customer_client.post("/account/mfa/enable", {"code": "000000"}).status_code == 400
    assert customer_client.post("/account/mfa/enable", {"code": pyotp.TOTP(secret).now()}).status_code == 200

    c = new_client()
    first = c.login(customer.email)
    assert first.status_code == 401 and first.get_json()["code"] == "mfa_required"
    assert c.login(customer.email, otp="123456").status_code == 401
    assert c.login(customer.email, otp=pyotp.TOTP(secret).now()).status_code == 200


def test_me_endpoint(client, customer):
    assert client.get("/auth/me").get_json() == {"user": None}
    client.login(customer.email)
    assert client.get("/auth/me").get_json()["user"]["email"] == customer.email


def test_close_account_removes_personal_data(customer_client, customer):
    resp = customer_client.delete("/account", {"password": PASSWORD})
    assert resp.status_code == 200
    user = db.session.get(User, customer.user_id)
    assert not user.is_active and user.email.endswith("@deleted.invalid") and user.name == "Deleted user"
    assert customer_client.get("/account").status_code == 401
