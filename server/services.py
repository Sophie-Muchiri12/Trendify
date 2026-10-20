"""Business rules for orders, stock and reviews (A05 / A09)."""
import secrets
from decimal import Decimal

from flask import current_app
from sqlalchemy import func, update
from sqlalchemy.exc import IntegrityError

from audit import alert, audit
from database import db
from errors import ApiError
from models import Order, OrderItem, Product, Review
from models.user import utcnow


def new_order_reference():
    return "TR-" + secrets.token_hex(5).upper()


def create_order(user, data, idempotency_key=None):
    """Create an order from validated input, all-or-nothing.

    * Prices come from the database, never from the client.
    * Stock is reserved with a conditional UPDATE (stock >= qty), so two simultaneous
      checkouts can't both buy the last item.
    * Any failure rolls back the whole transaction, including the stock reservations.
    * Re-sending the same Idempotency-Key returns the existing order instead of a
      duplicate.
    """
    if idempotency_key:
        existing = Order.query.filter_by(user_id=user.user_id, idempotency_key=idempotency_key).first()
        if existing:
            return existing, False

    slugs = [item["slug"] for item in data["items"]]
    products = {p.slug: p for p in Product.query.filter(Product.slug.in_(slugs), Product.is_active.is_(True))}

    try:
        order = Order(
            reference=new_order_reference(),
            user_id=user.user_id,
            shipping_address=data["shipping_address"],
            phone_number=data["phone_number"],
            currency=current_app.config["CURRENCY"],
            status="pending_payment",
            idempotency_key=idempotency_key,
            total_amount=Decimal("0"),
        )
        db.session.add(order)
        total = Decimal("0")
        for item in data["items"]:
            product = products.get(item["slug"])
            if product is None:
                raise ApiError(400, "One of the products in your cart is no longer available.",
                               fields={"items": [f"{item['slug']} is not available"]})
            size = item.get("size")
            if product.sizes and size not in product.sizes:
                raise ApiError(400, f"Choose a valid size for {product.name}.",
                               fields={"items": [f"invalid size for {item['slug']}"]})
            if not product.sizes:
                size = None
            qty = item["quantity"]
            reserved = db.session.execute(
                update(Product)
                .where(Product.product_id == product.product_id, Product.stock_quantity >= qty)
                .values(stock_quantity=Product.stock_quantity - qty)
            ).rowcount
            if reserved != 1:
                raise ApiError(409, f"Sorry, there isn't enough stock of {product.name}.",
                               fields={"items": [f"insufficient stock for {item['slug']}"]})
            total += product.price * qty
            db.session.add(OrderItem(order=order, product_id=product.product_id, quantity=qty,
                                     price_at_purchase=product.price, product_name=product.name, size=size))
        order.total_amount = total
        db.session.flush()
        audit("order.create", actor=user, target=order,
              details={"reference": order.reference, "total": str(total), "items": len(data["items"])})
        db.session.commit()
    except IntegrityError:
        # Two simultaneous requests with the same Idempotency-Key: return the winner.
        db.session.rollback()
        existing = idempotency_key and Order.query.filter_by(
            user_id=user.user_id, idempotency_key=idempotency_key).first()
        if existing:
            return existing, False
        raise
    except Exception:
        db.session.rollback()
        raise
    return order, True


def restock(order):
    for item in order.order_items:
        db.session.execute(
            update(Product).where(Product.product_id == item.product_id)
            .values(stock_quantity=Product.stock_quantity + item.quantity)
        )


def change_status(order, new_status, actor, *, by_admin):
    """Apply a status change if the business rules allow it."""
    old = order.status
    if by_admin:
        allowed = Order.ADMIN_TRANSITIONS.get(old, set())
    else:
        allowed = {"cancelled"} if old in Order.CUSTOMER_CANCELLABLE else set()
    if new_status not in allowed:
        raise ApiError(409, f"An order that is {old.replace('_', ' ')} can't be changed to "
                            f"{new_status.replace('_', ' ')}.")
    # Return stock for orders that never shipped.
    if new_status in ("cancelled", "refunded") and old in ("pending_payment", "paid"):
        restock(order)
    order.status = new_status
    if new_status == "cancelled":
        order.cancelled_at = utcnow()
    audit("order.status", actor=actor, target=order,
          details={"reference": order.reference, "from": old, "to": new_status, "by_admin": by_admin})
    db.session.commit()
    return order


def apply_payment_result(order, result, source):
    """Update an order from a *verified* provider status. Safe to call repeatedly."""
    if result is None:
        return order
    if result.state == "completed":
        problems = []
        if result.merchant_reference and result.merchant_reference != order.reference:
            problems.append("merchant reference mismatch")
        if result.amount is not None and Decimal(result.amount).quantize(Decimal("0.01")) != order.total_amount:
            problems.append(f"amount {result.amount} != {order.total_amount}")
        if result.currency and result.currency.upper() != order.currency.upper():
            problems.append(f"currency {result.currency} != {order.currency}")
        if problems:
            order.payment_status = "mismatch"
            alert("payment_mismatch", f"Payment for order {order.reference} did not match the order",
                  reference=order.reference, problems=problems, source=source)
            db.session.commit()
            return order
        if order.status == "pending_payment":
            order.status = "paid"
            order.paid_at = utcnow()
            order.payment_status = "completed"
            order.payment_method = (result.method or order.payment_method or "")[:50] or None
            audit("payment.completed", target=order, actor_email="pesapal" if source != "simulated" else "simulator",
                  details={"reference": order.reference, "amount": str(order.total_amount), "source": source})
        elif order.status == "cancelled":
            # Paid after the customer cancelled: flag it so staff can refund.
            order.payment_status = "completed_after_cancel"
            alert("payment_after_cancellation", f"Order {order.reference} was paid after being cancelled",
                  reference=order.reference)
        db.session.commit()
    elif result.state in ("failed", "reversed"):
        if order.payment_status != result.state:
            order.payment_status = result.state
            audit("payment." + result.state, "failure", target=order,
                  details={"reference": order.reference, "source": source})
            db.session.commit()
    return order


def customer_can_review(user, product):
    """Only customers who received (or at least paid for) the product may review it."""
    return db.session.query(OrderItem.order_item_id).join(Order).filter(
        Order.user_id == user.user_id,
        Order.status.in_(("paid", "shipped", "delivered")),
        OrderItem.product_id == product.product_id,
    ).first() is not None


def refresh_product_rating(product):
    avg, count = db.session.query(func.avg(Review.rating), func.count(Review.review_id)).filter(
        Review.product_id == product.product_id, Review.status == "approved").one()
    product.review_count = count or 0
    if count:
        product.rating = round(float(avg), 1)
