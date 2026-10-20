"""A01 Broken access control (plus the A08 logging/alerting that goes with it)."""
import pytest

from conftest import place_order
from extensions import db
from models import AuditLog, Order, User

ADMIN_ENDPOINTS = [
    ("get", "/admin/stats"), ("get", "/admin/users"), ("get", "/admin/orders"),
    ("get", "/admin/products"), ("get", "/admin/reviews"), ("get", "/admin/audit-logs"),
    ("post", "/admin/products"), ("patch", "/admin/users/1"), ("delete", "/admin/products/1"),
]


@pytest.mark.parametrize("method,url", ADMIN_ENDPOINTS)
def test_admin_endpoints_reject_anonymous(client, method, url):
    resp = getattr(client, method)(url) if method == "get" else getattr(client, method)(url, {})
    assert resp.status_code == 401


@pytest.mark.parametrize("method,url", ADMIN_ENDPOINTS)
def test_admin_endpoints_reject_customers(customer_client, method, url):
    resp = getattr(customer_client, method)(url) if method == "get" else getattr(customer_client, method)(url, {})
    assert resp.status_code == 403


def test_denied_admin_access_is_logged_and_alerts(customer_client, customer):
    for _ in range(5):
        customer_client.get("/admin/users")
    denied = AuditLog.query.filter_by(action="authz.denied", actor_user_id=customer.user_id).count()
    assert denied == 5
    assert AuditLog.query.filter_by(action="alert.repeated_authorization_failures").count() == 1


def test_customer_endpoints_require_login(client):
    assert client.get("/orders").status_code == 401
    assert client.get("/account").status_code == 401
    assert client.post("/orders", {}).status_code == 401


def test_customer_cannot_view_or_cancel_someone_elses_order(new_client, make_user):
    alice, bob = make_user(email="alice@example.com"), make_user(email="bob@example.com")
    a, b = new_client(), new_client()
    a.login(alice.email)
    b.login(bob.email)
    ref = place_order(a).get_json()["order"]["reference"]

    assert b.get(f"/orders/{ref}").status_code == 404
    assert b.post(f"/orders/{ref}/cancel").status_code == 404
    assert b.post(f"/payments/simulated/{ref}", {"outcome": "success"}).status_code == 404
    assert Order.query.filter_by(reference=ref).one().status == "pending_payment"
    assert AuditLog.query.filter_by(action="authz.denied", actor_user_id=bob.user_id).count() == 3
    # Bob's order list doesn't include Alice's order
    assert b.get("/orders").get_json()["items"] == []


def test_deactivated_user_session_stops_working(customer_client, customer):
    user = db.session.get(User, customer.user_id)
    user.is_active = False
    db.session.commit()
    assert customer_client.get("/account").status_code == 401


def test_role_change_ends_target_sessions(admin_client, new_client, make_user):
    target = make_user(email="target@example.com")
    c = new_client()
    c.login(target.email)
    resp = admin_client.patch(f"/admin/users/{target.user_id}", {"role": "admin"})
    assert resp.status_code == 200
    assert c.get("/account").status_code == 401  # must sign in again to get the new role
    assert AuditLog.query.filter_by(action="alert.admin_granted").count() == 1


def test_admin_cannot_demote_or_deactivate_self(admin_client, admin):
    assert admin_client.patch(f"/admin/users/{admin.user_id}", {"role": "customer"}).status_code == 409
    assert admin_client.patch(f"/admin/users/{admin.user_id}", {"is_active": False}).status_code == 409


def test_last_admin_cannot_be_removed(admin_client, make_user, admin):
    other = make_user(email="admin2@example.com", role="admin")
    assert admin_client.patch(f"/admin/users/{other.user_id}", {"role": "customer"}).status_code == 200
    # Now `admin` is the only one left; closing their own account is blocked.
    from conftest import PASSWORD
    assert admin_client.delete("/account", {"password": PASSWORD}).status_code == 409


def test_unverified_customer_cannot_order(new_client, make_user):
    user = make_user(email="new@example.com", verified=False)
    c = new_client()
    c.login(user.email)
    resp = place_order(c)
    assert resp.status_code == 403 and resp.get_json()["code"] == "email_unverified"


def test_no_admin_self_registration_route(client):
    assert client.post("/register-admin", {}, csrf=False).status_code == 404
    assert client.post("/auth/register-admin", {}, csrf=False).status_code == 404
