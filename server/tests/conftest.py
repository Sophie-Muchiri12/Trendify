import os
import re
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app  # noqa: E402
from catalog import PRODUCTS  # noqa: E402
from extensions import db, limiter  # noqa: E402
from models import Product, User  # noqa: E402
from models.user import utcnow  # noqa: E402
from security import hash_password  # noqa: E402

PASSWORD = "Corr3ctHorseBattery"


@pytest.fixture
def app():
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        db.session.add_all([Product(**data) for data in PRODUCTS])
        db.session.commit()
        yield app
        db.session.remove()
        db.drop_all()
    limiter.reset()


class ApiClient:
    """Test client that behaves like the browser frontend: cookies + CSRF header."""

    def __init__(self, app):
        self.app = app
        self.client = app.test_client()

    def _csrf(self, refresh=False):
        cookie = self.client.get_cookie("csrf_refresh_token" if refresh else "csrf_access_token")
        return {"X-CSRF-TOKEN": cookie.value} if cookie else {}

    def get(self, url, **kw):
        return self.client.get(url, **kw)

    def _send(self, method, url, json=None, headers=None, csrf=True, refresh=False, **kw):
        h = dict(self._csrf(refresh) if csrf else {})
        h.update(headers or {})
        return getattr(self.client, method)(url, json=json, headers=h, **kw)

    def post(self, url, json=None, **kw):
        return self._send("post", url, json, **kw)

    def patch(self, url, json=None, **kw):
        return self._send("patch", url, json, **kw)

    def delete(self, url, json=None, **kw):
        return self._send("delete", url, json, **kw)

    def login(self, email, password=PASSWORD, **extra):
        resp = self.post("/auth/login", {"email": email, "password": password, **extra}, csrf=False)
        return resp


@pytest.fixture
def make_user(app):
    def _make(email="customer@example.com", role="customer", verified=True, name="Test Customer",
              password=PASSWORD, **kw):
        user = User(email=email, name=name, phone_number="+254700000000", role=role,
                    password_hash=hash_password(password), email_verified_at=utcnow() if verified else None, **kw)
        db.session.add(user)
        db.session.commit()
        return user
    return _make


@pytest.fixture
def client(app):
    return ApiClient(app)


@pytest.fixture
def new_client(app):
    return lambda: ApiClient(app)


@pytest.fixture
def customer(make_user):
    return make_user()


@pytest.fixture
def admin(make_user):
    return make_user(email="admin@example.com", role="admin", name="Site Admin")


@pytest.fixture
def customer_client(client, customer):
    assert client.login(customer.email).status_code == 200
    return client


@pytest.fixture
def admin_client(new_client, admin):
    c = new_client()
    assert c.login(admin.email).status_code == 200
    return c


def outbox(app):
    return app.extensions.get("test_outbox", [])


def token_from_last_email(app):
    body = outbox(app)[-1]["body"]
    return re.search(r"token=([A-Za-z0-9_\-]+)", body).group(1)


def place_order(c, items=None, key=None, **overrides):
    payload = {
        "items": items or [{"slug": "chalk-stoneware-mug", "quantity": 2}],
        "shipping_address": "123 Moi Avenue, Nairobi",
        "phone_number": "+254700000000",
        **overrides,
    }
    headers = {"Idempotency-Key": key} if key else None
    return c.post("/orders", payload, headers=headers)
