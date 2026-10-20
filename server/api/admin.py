"""Administrator API. Every route here requires the admin role (A01: deny by default)."""
import os
import re
import secrets
from datetime import timedelta
from decimal import Decimal

from flask import Blueprint, current_app, jsonify, request
from PIL import Image, UnidentifiedImageError
from sqlalchemy import func, or_

from api.catalog import escape_like, filtered_products, paginate
from audit import alert, audit, verify_chain
from errors import ApiError
from extensions import db, limiter
from models import AuditLog, Order, Product, Review, User
from models.user import utcnow
from security import admin_required, current_user
from services import apply_payment_result, change_status, refresh_product_rating
from payments import fetch_verified_status
from validation import (AdminProductQuerySchema, AdminUserUpdateSchema, AuditQuerySchema,
                        OrderQuerySchema, OrderStatusSchema, ProductSchema, ProductUpdateSchema,
                        ReviewModerationSchema, ReviewQuerySchema, UserQuerySchema, load_json, load_query)

bp = Blueprint("admin", __name__, url_prefix="/admin")


@bp.before_request
@admin_required
def require_admin():
    """Runs before every admin route, so a forgotten decorator can't open one up."""


# --- Dashboard ---------------------------------------------------------------------

@bp.get("/stats")
def stats():
    by_status = dict(db.session.query(Order.status, func.count(Order.order_id)).group_by(Order.status).all())
    revenue = db.session.query(func.coalesce(func.sum(Order.total_amount), 0)) \
        .filter(Order.status.in_(("paid", "shipped", "delivered"))).scalar()
    return jsonify(
        users=User.query.filter_by(is_active=True).count(),
        products=Product.query.filter_by(is_active=True).count(),
        low_stock=Product.query.filter(Product.is_active.is_(True), Product.stock_quantity < 5).count(),
        orders_by_status=by_status,
        revenue=float(revenue or 0),
        pending_reviews=Review.query.filter_by(status="pending").count(),
        security_events_24h=AuditLog.query.filter(
            AuditLog.outcome.in_(("failure", "denied")),
            AuditLog.created_at >= utcnow() - timedelta(days=1)).count(),
    )


# --- Products ----------------------------------------------------------------------

def slugify(name):
    base = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:100] or "product"
    slug, n = base, 2
    while Product.query.filter_by(slug=slug).first():
        slug, n = f"{base}-{n}", n + 1
    return slug


def get_product_or_404(product_id):
    product = db.session.get(Product, product_id)
    if product is None:
        raise ApiError(404, "Product not found.")
    return product


@bp.get("/products")
def admin_list_products():
    args = load_query(AdminProductQuerySchema())
    query = Product.query
    if args["status"] == "active":
        query = query.filter(Product.is_active.is_(True))
    elif args["status"] == "archived":
        query = query.filter(Product.is_active.is_(False))
    return jsonify(paginate(filtered_products(args, query), args, Product.to_admin_dict))


@bp.get("/products/<int:product_id>")
def admin_get_product(product_id):
    return jsonify(product=get_product_or_404(product_id).to_admin_dict())


@bp.post("/products")
def admin_create_product():
    data = load_json(ProductSchema())
    if data.get("slug") and Product.query.filter_by(slug=data["slug"]).first():
        raise ApiError(409, "That URL slug is already used by another product.", fields={"slug": ["Already in use."]})
    product = Product(**{**data, "slug": data.get("slug") or slugify(data["name"])}, is_active=True)
    db.session.add(product)
    db.session.flush()
    audit("product.create", actor=current_user(), target=product, details={"slug": product.slug})
    db.session.commit()
    return jsonify(product=product.to_admin_dict()), 201


@bp.patch("/products/<int:product_id>")
def admin_update_product(product_id):
    product = get_product_or_404(product_id)
    data = load_json(ProductUpdateSchema())
    if "slug" in data and data["slug"] != product.slug and Product.query.filter_by(slug=data["slug"]).first():
        raise ApiError(409, "That URL slug is already used by another product.", fields={"slug": ["Already in use."]})
    new_price = data.get("price", product.price)
    new_old = data.get("old_price", product.old_price)
    if new_old is not None and Decimal(new_old) <= Decimal(new_price):
        raise ApiError(400, "The old price must be higher than the price.",
                       fields={"old_price": ["Must be higher than the price."]})
    changes = {}
    for key, value in data.items():
        if getattr(product, key) != value:
            changes[key] = {"from": getattr(product, key), "to": value}
            setattr(product, key, value)
    if changes:
        audit("product.update", actor=current_user(), target=product, details={"changes": changes})
    db.session.commit()
    return jsonify(product=product.to_admin_dict())


@bp.delete("/products/<int:product_id>")
def admin_archive_product(product_id):
    """Archive (soft-delete) so existing orders keep pointing at the product."""
    product = get_product_or_404(product_id)
    product.is_active = False
    audit("product.archive", actor=current_user(), target=product)
    db.session.commit()
    return jsonify(product=product.to_admin_dict())


@bp.post("/products/<int:product_id>/restore")
def admin_restore_product(product_id):
    product = get_product_or_404(product_id)
    product.is_active = True
    audit("product.restore", actor=current_user(), target=product)
    db.session.commit()
    return jsonify(product=product.to_admin_dict())


ALLOWED_IMAGE_FORMATS = {"JPEG", "PNG", "WEBP"}
MAX_IMAGE_PIXELS = 40_000_000
IMAGE_SIZE = 816


@bp.post("/uploads/product-image")
@limiter.limit("30 per hour")
def upload_product_image():
    """Accept an image and store a re-encoded copy.

    The file is opened with Pillow (so its real type is checked, not its name),
    size-limited, cropped to a square and saved as a brand-new JPEG with a random
    name. Re-encoding drops metadata and anything hidden inside the original (A04).
    """
    upload = request.files.get("file")
    if upload is None or not upload.filename:
        raise ApiError(400, "Choose an image to upload.")
    try:
        # formats= stops Pillow from even trying its other parsers (TIFF, GIF, EPS, PDF...),
        # which keeps their known advisories out of reach of uploaded files.
        with Image.open(upload.stream, formats=sorted(ALLOWED_IMAGE_FORMATS)) as img:
            if img.width * img.height > MAX_IMAGE_PIXELS:
                raise ApiError(413, "That image is too large.")
            img.load()
            img = img.convert("RGB")
            side = min(img.size)
            left, top = (img.width - side) // 2, (img.height - side) // 2
            img = img.crop((left, top, left + side, top + side)).resize((IMAGE_SIZE, IMAGE_SIZE), Image.LANCZOS)
            name = f"u-{secrets.token_hex(8)}.jpg"
            folder = os.path.join(current_app.static_folder, "products")
            os.makedirs(folder, exist_ok=True)
            img.save(os.path.join(folder, name), "JPEG", quality=85, optimize=True)
    except (UnidentifiedImageError, Image.DecompressionBombError, OSError):
        raise ApiError(415, "That file isn't a valid image.")
    url = f"/static/products/{name}"
    audit("product.image_upload", actor=current_user(), details={"image_url": url})
    db.session.commit()
    return jsonify(image_url=url), 201


# --- Orders ------------------------------------------------------------------------

def get_order_or_404(reference):
    order = Order.query.filter_by(reference=reference).first()
    if order is None:
        raise ApiError(404, "Order not found.")
    return order


@bp.get("/orders")
def admin_list_orders():
    args = load_query(OrderQuerySchema())
    query = Order.query.join(User)
    if args.get("status"):
        query = query.filter(Order.status == args["status"])
    if args.get("q"):
        pattern = f"%{escape_like(args['q'])}%"
        query = query.filter(or_(Order.reference.ilike(pattern, escape="\\"),
                                 User.email.ilike(pattern, escape="\\")))
    return jsonify(paginate(query.order_by(Order.created_at.desc()), args, Order.to_admin_dict))


@bp.get("/orders/<reference>")
def admin_get_order(reference):
    return jsonify(order=get_order_or_404(reference).to_admin_dict())


@bp.patch("/orders/<reference>/status")
def admin_update_order_status(reference):
    data = load_json(OrderStatusSchema())
    order = change_status(get_order_or_404(reference), data["status"], current_user(), by_admin=True)
    return jsonify(order=order.to_admin_dict())


@bp.post("/orders/<reference>/refresh-payment")
def admin_refresh_payment(reference):
    order = get_order_or_404(reference)
    apply_payment_result(order, fetch_verified_status(order), source="admin")
    return jsonify(order=order.to_admin_dict())


# --- Users -------------------------------------------------------------------------

def get_user_or_404(user_id):
    user = db.session.get(User, user_id)
    if user is None:
        raise ApiError(404, "User not found.")
    return user


@bp.get("/users")
def admin_list_users():
    args = load_query(UserQuerySchema())
    query = User.query
    if args.get("role"):
        query = query.filter(User.role == args["role"])
    if args.get("q"):
        pattern = f"%{escape_like(args['q'])}%"
        query = query.filter(or_(User.email.ilike(pattern, escape="\\"), User.name.ilike(pattern, escape="\\")))
    return jsonify(paginate(query.order_by(User.user_id), args, User.to_admin_dict))


@bp.get("/users/<int:user_id>")
def admin_get_user(user_id):
    return jsonify(user=get_user_or_404(user_id).to_admin_dict())


@bp.patch("/users/<int:user_id>")
def admin_update_user(user_id):
    admin = current_user()
    user = get_user_or_404(user_id)
    data = load_json(AdminUserUpdateSchema())
    if user.user_id == admin.user_id and (data.get("role", "admin") != "admin" or data.get("is_active") is False):
        raise ApiError(409, "You can't remove your own admin access or deactivate yourself.")
    losing_admin = user.role == "admin" and (data.get("role") == "customer" or data.get("is_active") is False)
    if losing_admin and User.query.filter_by(role="admin", is_active=True).count() <= 1:
        raise ApiError(409, "There must always be at least one active administrator.")

    changes = {k: {"from": getattr(user, k), "to": v} for k, v in data.items() if getattr(user, k) != v}
    for key, value in data.items():
        setattr(user, key, value)
    if changes:
        user.token_version += 1  # role or status changed: existing sessions must sign in again
        audit("user.update", actor=admin, target=user, details={"changes": changes})
        if data.get("role") == "admin" and "role" in changes:
            alert("admin_granted", f"User {user.user_id} was made an administrator by {admin.user_id}",
                  user_id=user.user_id, granted_by=admin.user_id)
    db.session.commit()
    return jsonify(user=user.to_admin_dict())


@bp.post("/users/<int:user_id>/unlock")
def admin_unlock_user(user_id):
    user = get_user_or_404(user_id)
    user.locked_until = None
    user.failed_login_count = 0
    audit("user.unlock", actor=current_user(), target=user)
    db.session.commit()
    return jsonify(user=user.to_admin_dict())


# --- Reviews -----------------------------------------------------------------------

def get_review_or_404(review_id):
    review = db.session.get(Review, review_id)
    if review is None:
        raise ApiError(404, "Review not found.")
    return review


@bp.get("/reviews")
def admin_list_reviews():
    args = load_query(ReviewQuerySchema())
    query = Review.query
    if args.get("status"):
        query = query.filter(Review.status == args["status"])
    return jsonify(paginate(query.order_by(Review.created_at.desc()), args, Review.to_admin_dict))


@bp.patch("/reviews/<int:review_id>")
def admin_moderate_review(review_id):
    review = get_review_or_404(review_id)
    data = load_json(ReviewModerationSchema())
    old = review.status
    review.status = data["status"]
    db.session.flush()
    refresh_product_rating(review.product)
    audit("review.moderate", actor=current_user(), target=review, details={"from": old, "to": review.status})
    db.session.commit()
    return jsonify(review=review.to_admin_dict())


@bp.delete("/reviews/<int:review_id>")
def admin_delete_review(review_id):
    review = get_review_or_404(review_id)
    product = review.product
    audit("review.delete", actor=current_user(), target=review, details={"by_admin": True})
    db.session.delete(review)
    db.session.flush()
    refresh_product_rating(product)
    db.session.commit()
    return jsonify(message="Review deleted.")


# --- Audit log ---------------------------------------------------------------------

@bp.get("/audit-logs")
def admin_audit_logs():
    args = load_query(AuditQuerySchema())
    query = AuditLog.query
    if args.get("action"):
        query = query.filter(AuditLog.action.ilike(f"{escape_like(args['action'])}%", escape="\\"))
    if args.get("outcome"):
        query = query.filter(AuditLog.outcome == args["outcome"])
    return jsonify(paginate(query.order_by(AuditLog.id.desc()), args, AuditLog.to_dict))


@bp.get("/audit-logs/verify")
def admin_verify_audit_logs():
    ok, bad_id, count = verify_chain()
    if not ok:
        alert("audit_log_tampering", f"Audit log chain broken at entry {bad_id}", entry_id=bad_id)
        db.session.commit()
    return jsonify(ok=ok, first_bad_id=bad_id, checked=count)
