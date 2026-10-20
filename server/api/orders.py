"""Customer orders, checkout and payment callbacks."""
import logging
import re

from flask import Blueprint, current_app, jsonify, request

from audit import audit, check_authz_failures
from errors import ApiError
from extensions import db, limiter
from models import Order
from payments import PaymentResult, fetch_verified_status, start_payment
from security import current_user, login_required, verified_required
from services import apply_payment_result, change_status, create_order
from validation import OrderCreateSchema, PaymentOutcomeSchema, load_json

log = logging.getLogger("trendify")

bp = Blueprint("orders", __name__)

IDEMPOTENCY_KEY_RE = re.compile(r"^[A-Za-z0-9_-]{8,64}$")
REFERENCE_RE = re.compile(r"^TR-[0-9A-F]{10}$")
TRACKING_ID_RE = re.compile(r"^[A-Za-z0-9-]{1,64}$")


def own_order(reference):
    """Return the signed-in customer's order, or 404 (A01: verify ownership)."""
    user = current_user()
    order = Order.query.filter_by(reference=reference).first() if REFERENCE_RE.match(reference) else None
    if order is None or order.user_id != user.user_id:
        if order is not None:
            audit("authz.denied", "denied", actor=user, target=order,
                  details={"reason": "not_order_owner"}, commit=True)
            check_authz_failures(user)
        # Same answer for "doesn't exist" and "not yours".
        raise ApiError(404, "Order not found.")
    return order


@bp.post("/orders")
@limiter.limit("10 per minute; 50 per day")
@verified_required
def place_order():
    user = current_user()
    data = load_json(OrderCreateSchema())
    key = request.headers.get("Idempotency-Key")
    if key is not None and not IDEMPOTENCY_KEY_RE.match(key):
        raise ApiError(400, "Invalid Idempotency-Key header.")

    order, created = create_order(user, data, idempotency_key=key)
    if not created:
        # A retry of a request we've already handled: don't create or charge twice.
        return jsonify(order=order.to_dict(), payment_url=None, duplicate=True), 200

    try:
        payment_url = start_payment(order, user)
        db.session.commit()
    except ApiError as err:
        db.session.rollback()
        return jsonify(order=order.to_dict(), payment_url=None, payment_error=err.message), 201
    return jsonify(order=order.to_dict(), payment_url=payment_url), 201


@bp.get("/orders")
@login_required
def list_orders():
    orders = Order.query.filter_by(user_id=current_user().user_id).order_by(Order.created_at.desc()).all()
    return jsonify(items=[o.to_dict() for o in orders])


@bp.get("/orders/<reference>")
@login_required
def get_order(reference):
    return jsonify(order=own_order(reference).to_dict())


@bp.post("/orders/<reference>/cancel")
@limiter.limit("20 per hour")
@login_required
def cancel_order(reference):
    order = change_status(own_order(reference), "cancelled", current_user(), by_admin=False)
    return jsonify(order=order.to_dict())


@bp.post("/orders/<reference>/pay")
@limiter.limit("10 per hour")
@verified_required
def pay_order(reference):
    order = own_order(reference)
    if order.status != "pending_payment":
        raise ApiError(409, "This order doesn't need paying.")
    # If a payment was already started, check it first so we never charge twice.
    apply_payment_result(order, fetch_verified_status(order), source="retry")
    if order.status != "pending_payment":
        return jsonify(order=order.to_dict(), payment_url=None)
    payment_url = start_payment(order, current_user())
    db.session.commit()
    return jsonify(order=order.to_dict(), payment_url=payment_url)


@bp.post("/orders/<reference>/refresh-payment")
@limiter.limit("30 per hour")
@login_required
def refresh_payment(reference):
    """Called when the customer returns from Pesapal. Confirms the result with Pesapal."""
    order = own_order(reference)
    if order.status == "pending_payment":
        apply_payment_result(order, fetch_verified_status(order), source="callback")
    return jsonify(order=order.to_dict())


# --- Provider notifications --------------------------------------------------------

@bp.route("/payments/pesapal/ipn", methods=["GET", "POST"])
@limiter.limit("120 per minute")
def pesapal_ipn():
    """Pesapal Instant Payment Notification.

    The notification itself isn't trusted (A07): it only tells us *which* order to
    re-check, and the status is fetched from Pesapal's API before anything changes.
    """
    params = request.args if request.method == "GET" else (request.get_json(silent=True) or {})
    tracking_id = str(params.get("OrderTrackingId", ""))
    reference = str(params.get("OrderMerchantReference", ""))
    notification_type = str(params.get("OrderNotificationType", ""))[:30]
    reply = {"orderNotificationType": notification_type, "orderTrackingId": tracking_id,
             "orderMerchantReference": reference}

    order = None
    if REFERENCE_RE.match(reference) and TRACKING_ID_RE.match(tracking_id):
        order = Order.query.filter_by(reference=reference, payment_tracking_id=tracking_id).first()
    if order is None:
        audit("payment.ipn", "failure", details={"reason": "unknown_order", "reference": reference[:40]},
              commit=True)
        return jsonify(**reply, status=500)

    result = fetch_verified_status(order)
    if result is None:
        return jsonify(**reply, status=500)  # Pesapal will retry
    apply_payment_result(order, result, source="ipn")
    return jsonify(**reply, status=200)


@bp.post("/payments/simulated/<reference>")
@limiter.limit("30 per hour")
@login_required
def simulated_payment(reference):
    """Development-only stand-in for Pesapal's hosted payment page."""
    if current_app.config["PAYMENT_PROVIDER"] != "simulated" or current_app.config["ENV_NAME"] == "production":
        raise ApiError(404)
    order = own_order(reference)
    data = load_json(PaymentOutcomeSchema())
    if order.payment_provider != "simulated":
        raise ApiError(409, "This order isn't using the payment simulator.")
    result = PaymentResult(
        "completed" if data["outcome"] == "success" else "failed",
        amount=order.total_amount, currency=order.currency,
        merchant_reference=order.reference, method="Simulated card",
    )
    apply_payment_result(order, result, source="simulated")
    return jsonify(order=order.to_dict())
