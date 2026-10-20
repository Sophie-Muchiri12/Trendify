"""Admin CRUD for products, users, orders, reviews and the audit trail."""
import io
import os

from PIL import Image

from extensions import db
from models import AuditLog, Product

NEW_PRODUCT = {"name": "Sisal Market Bag", "description": "Hand-woven sisal bag with leather handles.",
               "price": 45, "stock_quantity": 12, "category": "Home"}


def test_product_crud(admin_client, client):
    created = admin_client.post("/admin/products", NEW_PRODUCT)
    assert created.status_code == 201
    product = created.get_json()["product"]
    assert product["slug"] == "sisal-market-bag"
    assert client.get("/products/sisal-market-bag").status_code == 200

    updated = admin_client.patch(f"/admin/products/{product['product_id']}", {"price": 39.99, "stock_quantity": 3})
    assert updated.get_json()["product"]["price"] == 39.99

    assert admin_client.delete(f"/admin/products/{product['product_id']}").status_code == 200
    assert client.get("/products/sisal-market-bag").status_code == 404
    assert admin_client.get(f"/admin/products/{product['product_id']}").get_json()["product"]["is_active"] is False

    assert admin_client.post(f"/admin/products/{product['product_id']}/restore").status_code == 200
    assert client.get("/products/sisal-market-bag").status_code == 200
    actions = [a.action for a in AuditLog.query.filter(AuditLog.action.like("product.%"))]
    assert actions == ["product.create", "product.update", "product.archive", "product.restore"]


def test_duplicate_names_get_unique_slugs(admin_client):
    a = admin_client.post("/admin/products", NEW_PRODUCT).get_json()["product"]["slug"]
    b = admin_client.post("/admin/products", NEW_PRODUCT).get_json()["product"]["slug"]
    assert a != b


def test_product_validation(admin_client):
    bad_inputs = [
        {**NEW_PRODUCT, "price": -5},
        {**NEW_PRODUCT, "price": 0},
        {**NEW_PRODUCT, "category": "Weapons"},
        {**NEW_PRODUCT, "old_price": 40},  # must be above price
        {**NEW_PRODUCT, "rating": 5},       # ratings come from reviews only
        {**NEW_PRODUCT, "image_url": "javascript:alert(1)"},
        {**NEW_PRODUCT, "image_url": "https://evil.example/x.jpg"},
        {**NEW_PRODUCT, "slug": "Bad Slug!"},
        {**NEW_PRODUCT, "stock_quantity": "10"},
        {k: v for k, v in NEW_PRODUCT.items() if k != "name"},
    ]
    for body in bad_inputs:
        assert admin_client.post("/admin/products", body).status_code == 400, body
    pid = Product.query.filter_by(slug="moss-lamp").one().product_id
    assert admin_client.patch(f"/admin/products/{pid}", {"old_price": 1}).status_code == 400


def _image_bytes(fmt="PNG", size=(1200, 900)):
    buf = io.BytesIO()
    Image.new("RGB", size, (200, 120, 80)).save(buf, fmt)
    buf.seek(0)
    return buf


def test_image_upload_is_reencoded(app, admin_client):
    resp = admin_client.post("/admin/uploads/product-image", json=None,
                             data={"file": (_image_bytes(), "photo.png")}, content_type="multipart/form-data")
    assert resp.status_code == 201
    url = resp.get_json()["image_url"]
    assert url.startswith("/static/products/u-") and url.endswith(".jpg")
    path = os.path.join(app.static_folder, "products", os.path.basename(url))
    try:
        with Image.open(path) as img:
            assert img.format == "JPEG" and img.size == (816, 816)
    finally:
        os.remove(path)


def test_non_images_are_rejected(admin_client):
    fake = io.BytesIO(b"<?php system($_GET['c']); ?>")
    resp = admin_client.post("/admin/uploads/product-image", json=None,
                             data={"file": (fake, "shell.php.jpg")}, content_type="multipart/form-data")
    assert resp.status_code == 415


def test_user_management(admin_client, make_user):
    user = make_user(email="someone@example.com")
    users = admin_client.get("/admin/users?q=someone").get_json()["items"]
    assert [u["email"] for u in users] == ["someone@example.com"]
    assert "password_hash" not in str(users) and "mfa_secret" not in str(users)

    resp = admin_client.patch(f"/admin/users/{user.user_id}", {"is_active": False})
    assert resp.get_json()["user"]["is_active"] is False
    assert admin_client.patch(f"/admin/users/{user.user_id}", {"role": "superuser"}).status_code == 400
    assert admin_client.post(f"/admin/users/{user.user_id}/unlock").status_code == 200


def test_stats(admin_client):
    data = admin_client.get("/admin/stats").get_json()
    assert data["products"] == 22 and "revenue" in data


def test_audit_log_is_tamper_evident(admin_client, client, customer):
    client.login(customer.email, "Wr0ngPasswordX")
    client.login(customer.email)
    assert admin_client.get("/admin/audit-logs/verify").get_json()["ok"] is True

    entry = AuditLog.query.filter_by(action="auth.login", outcome="failure").first()
    entry.outcome = "success"  # an attacker trying to hide a failed login
    db.session.commit()
    result = admin_client.get("/admin/audit-logs/verify").get_json()
    assert result["ok"] is False and result["first_bad_id"] == entry.id
    assert AuditLog.query.filter_by(action="alert.audit_log_tampering").count() == 1


def test_audit_log_listing(admin_client):
    data = admin_client.get("/admin/audit-logs?action=auth.").get_json()
    assert data["items"][0]["action"] == "auth.login"


def test_only_jpeg_png_webp_are_parsed(admin_client):
    """GIF/TIFF/etc. parsers (which have open Pillow advisories) never see uploads."""
    for fmt in ("GIF", "TIFF", "BMP"):
        resp = admin_client.post("/admin/uploads/product-image", json=None,
                                 data={"file": (_image_bytes(fmt, (50, 50)), f"x.{fmt.lower()}")},
                                 content_type="multipart/form-data")
        assert resp.status_code == 415, fmt
