"""A02 security misconfiguration, A08 log hygiene, A09 exceptional conditions."""
import pytest

from audit import scrub
from config import ProductionConfig


def test_security_headers(client):
    resp = client.get("/products")
    h = resp.headers
    assert h["X-Content-Type-Options"] == "nosniff"
    assert h["X-Frame-Options"] == "DENY"
    assert "frame-ancestors 'none'" in h["Content-Security-Policy"]
    assert h["Referrer-Policy"] == "no-referrer"
    assert h["Cache-Control"] == "no-store"
    assert h["X-Request-ID"]


def test_cors_only_allows_trusted_origin(client):
    ok = client.get("/products", headers={"Origin": "http://localhost:5173"})
    bad = client.get("/products", headers={"Origin": "https://evil.example"})
    assert ok.headers.get("Access-Control-Allow-Origin") == "http://localhost:5173"
    assert "Access-Control-Allow-Origin" not in bad.headers


def test_errors_are_generic_json(client):
    resp = client.get("/no-such-page")
    assert resp.status_code == 404 and resp.get_json()["error"] == "Not found."
    resp = client.post("/auth/login", data="not json", content_type="text/plain", csrf=False)
    assert resp.status_code == 400 and "Traceback" not in resp.get_data(as_text=True)


def test_unexpected_exceptions_hide_details(app, client):
    @app.get("/boom")
    def boom():
        raise RuntimeError("database password is hunter2")

    resp = client.get("/boom")
    body = resp.get_data(as_text=True)
    assert resp.status_code == 500
    assert "hunter2" not in body and "RuntimeError" not in body
    assert resp.get_json()["request_id"]


def test_debug_is_off_outside_development(app):
    assert app.debug is False
    assert ProductionConfig.DEBUG is False


def test_production_refuses_unsafe_config(monkeypatch):
    monkeypatch.setattr(ProductionConfig, "SECRET_KEY", "short")
    monkeypatch.setattr(ProductionConfig, "CORS_ORIGINS", ["*"])
    monkeypatch.setattr(ProductionConfig, "PAYMENT_PROVIDER", "simulated")
    with pytest.raises(RuntimeError) as exc:
        ProductionConfig.validate()
    message = str(exc.value)
    assert "SECRET_KEY" in message and "CORS_ORIGINS" in message and "PAYMENT_PROVIDER" in message


def test_scrub_removes_secrets():
    cleaned = scrub({"email": "a@b.c", "password": "x", "nested": {"access_token": "y", "otp": "1"},
                     "items": [{"new_password": "z"}]})
    assert cleaned == {"email": "a@b.c", "password": "[redacted]",
                       "nested": {"access_token": "[redacted]", "otp": "[redacted]"},
                       "items": [{"new_password": "[redacted]"}]}


def test_oversized_requests_are_rejected(client):
    resp = client.post("/auth/login", data="x" * (6 * 1024 * 1024), content_type="application/json", csrf=False)
    assert resp.status_code == 413


def test_health(client):
    assert client.get("/health").get_json() == {"status": "ok"}
