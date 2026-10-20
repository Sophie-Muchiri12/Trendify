"""Public product catalog and customer reviews."""
from flask import Blueprint, jsonify
from sqlalchemy import or_

from audit import audit, check_authz_failures
from errors import ApiError
from extensions import db, limiter
from models import Product, Review
from security import current_user, login_required, verified_required
from services import customer_can_review, refresh_product_rating
from validation import ProductQuerySchema, ReviewSchema, ReviewUpdateSchema, load_json, load_query

bp = Blueprint("catalog", __name__)


def escape_like(term):
    """Escape LIKE wildcards so a search for '%' doesn't match everything."""
    return term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def filtered_products(args, base_query):
    """Build a product query from validated arguments.

    Everything goes through SQLAlchemy's parameterized expressions; user input is never
    concatenated into SQL (A04).
    """
    query = base_query
    if args.get("q"):
        pattern = f"%{escape_like(args['q'])}%"
        query = query.filter(or_(Product.name.ilike(pattern, escape="\\"),
                                 Product.description.ilike(pattern, escape="\\"),
                                 Product.category.ilike(pattern, escape="\\")))
    if args.get("category"):
        query = query.filter(Product.category == args["category"])
    if args.get("min_price") is not None:
        query = query.filter(Product.price >= args["min_price"])
    if args.get("max_price") is not None:
        query = query.filter(Product.price <= args["max_price"])
    order = {
        "price_asc": (Product.price.asc(),),
        "price_desc": (Product.price.desc(),),
        "rating": (Product.rating.desc().nullslast(), Product.review_count.desc()),
        "newest": (Product.created_at.desc(), Product.product_id.desc()),
    }.get(args.get("sort"), (Product.product_id.asc(),))
    return query.order_by(*order)


def paginate(query, args, serialize):
    page = query.paginate(page=args["page"], per_page=args["per_page"], error_out=False)
    return {"items": [serialize(item) for item in page.items], "total": page.total,
            "page": page.page, "per_page": page.per_page, "pages": page.pages}


def get_active_product(slug):
    product = Product.query.filter_by(slug=slug, is_active=True).first()
    if product is None:
        raise ApiError(404, "Product not found.")
    return product


@bp.get("/products")
def list_products():
    args = load_query(ProductQuerySchema())
    query = filtered_products(args, Product.query.filter(Product.is_active.is_(True)))
    return jsonify(paginate(query, args, Product.to_dict))


@bp.get("/products/<int:product_id>")
def get_product(product_id):
    product = Product.query.filter_by(product_id=product_id, is_active=True).first()
    if product is None:
        raise ApiError(404, "Product not found.")
    return jsonify(product.to_dict())


@bp.get("/products/<string:slug>")
def get_product_by_slug(slug):
    return jsonify(get_active_product(slug).to_dict())


# --- Reviews --------------------------------------------------------------------

@bp.get("/products/<string:slug>/reviews")
def list_reviews(slug):
    product = get_active_product(slug)
    reviews = Review.query.filter_by(product_id=product.product_id, status="approved") \
        .order_by(Review.created_at.desc()).limit(100).all()
    return jsonify(items=[r.to_public_dict() for r in reviews], rating=product.rating,
                   review_count=product.review_count)


@bp.get("/products/<string:slug>/reviews/eligibility")
@login_required
def review_eligibility(slug):
    product = get_active_product(slug)
    user = current_user()
    existing = Review.query.filter_by(product_id=product.product_id, user_id=user.user_id).first()
    return jsonify(
        can_review=user.email_verified and existing is None and customer_can_review(user, product),
        has_purchased=customer_can_review(user, product),
        review=existing.to_owner_dict() if existing else None,
    )


@bp.post("/products/<string:slug>/reviews")
@limiter.limit("10 per hour")
@verified_required
def create_review(slug):
    product = get_active_product(slug)
    user = current_user()
    data = load_json(ReviewSchema())
    if not customer_can_review(user, product):
        raise ApiError(403, "You can review products after you've bought them.", code="not_purchased")
    if Review.query.filter_by(product_id=product.product_id, user_id=user.user_id).first():
        raise ApiError(409, "You've already reviewed this product. Edit your existing review instead.")
    review = Review(product_id=product.product_id, user_id=user.user_id, rating=data["rating"],
                    review_text=data.get("review_text") or None, status="pending")
    db.session.add(review)
    db.session.flush()
    audit("review.create", actor=user, target=review, details={"product": product.slug})
    db.session.commit()
    return jsonify(review=review.to_owner_dict(),
                   message="Thanks! Your review will appear once it's been checked."), 201


def _own_review(review_id):
    review = db.session.get(Review, review_id)
    user = current_user()
    if review is None or review.user_id != user.user_id:
        if review is not None:
            # Someone else's review: log it, but answer as if it didn't exist (A01).
            audit("authz.denied", "denied", actor=user, target=review, commit=True)
            check_authz_failures(user)
        raise ApiError(404, "Review not found.")
    return review


@bp.patch("/reviews/<int:review_id>")
@limiter.limit("20 per hour")
@verified_required
def update_review(review_id):
    review = _own_review(review_id)
    data = load_json(ReviewUpdateSchema())
    if "rating" in data:
        review.rating = data["rating"]
    if "review_text" in data:
        review.review_text = data["review_text"] or None
    was_approved = review.status == "approved"
    review.status = "pending"  # edited reviews are checked again
    if was_approved:
        db.session.flush()
        refresh_product_rating(review.product)
    audit("review.update", actor=current_user(), target=review)
    db.session.commit()
    return jsonify(review=review.to_owner_dict())


@bp.delete("/reviews/<int:review_id>")
@login_required
def delete_review(review_id):
    review = _own_review(review_id)
    product = review.product
    audit("review.delete", actor=current_user(), target=review)
    db.session.delete(review)
    db.session.flush()
    refresh_product_rating(product)
    db.session.commit()
    return jsonify(message="Review deleted.")
