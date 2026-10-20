"""Orders and payments: A05 insecure design, A07 integrity of payment data, A09 failures."""
from decimal import Decimal

import api.orders
from conftest import place_order
from extensions import db
from models import AuditLog, Order, Product
from payments import PaymentResult
from services import apply_payment_result


def stock(slug):
    db.session.expire_all()
    return Product.query.filter_by(slug=slug).one().stock_quantity


def test_order_total_uses_database_prices(customer_client):
    resp = place_order(customer_client, [{"slug": "chalk-stoneware-mug", "quantity": 3},
                                         {"slug": "vortex-runner", "quantity": 1, "size": "42"}])
    assert resp.status_code == 201
    order = resp.get_json()["order"]
    assert order["total_amount"] == 3 * 32 + 140
    assert order["status"] == "pending_payment"
    assert resp.get_json()["payment_url"].endswith(f"/checkout/simulate?ref={order['reference']}")


def test_client_supplied_prices_are_rejected(customer_client):
    resp = place_order(customer_client, [{"slug": "kilim-runner", "quantity": 1, "price": 0.01}])
    assert resp.status_code == 400
    resp = place_order(customer_client, total_amount=1)
    assert resp.status_code == 400
    assert Order.query.count() == 0


def test_quantity_must_be_positive_and_bounded(customer_client):
    for qty in [0, -1, 11, "2", 1.5]:
        resp = place_order(customer_client, [{"slug": "chalk-stoneware-mug", "quantity": qty}])
        assert resp.status_code == 400, qty
    assert Order.query.count() == 0


def test_size_is_validated(customer_client):
    assert place_order(customer_client, [{"slug": "vortex-runner", "quantity": 1}]).status_code == 400
    assert place_order(customer_client, [{"slug": "vortex-runner", "quantity": 1, "size": "99"}]).status_code == 400


def test_stock_failure_rolls_back_whole_order(customer_client):
    product = Product.query.filter_by(slug="moss-lamp").one()
    product.stock_quantity = 1
    db.session.commit()
    before = stock("chalk-stoneware-mug")
    resp = place_order(customer_client, [{"slug": "chalk-stoneware-mug", "quantity": 2},
                                         {"slug": "moss-lamp", "quantity": 2}])
    assert resp.status_code == 409
    assert stock("chalk-stoneware-mug") == before  # first line's reservation was undone
    assert stock("moss-lamp") == 1
    assert Order.query.count() == 0


def test_stock_is_reserved(customer_client):
    before = stock("chalk-stoneware-mug")
    place_order(customer_client, [{"slug": "chalk-stoneware-mug", "quantity": 2}])
    assert stock("chalk-stoneware-mug") == before - 2


def test_idempotency_key_prevents_duplicate_orders(customer_client):
    first = place_order(customer_client, key="checkout-123456")
    second = place_order(customer_client, key="checkout-123456")
    assert first.status_code == 201 and second.status_code == 200
    assert second.get_json()["duplicate"] is True
    assert first.get_json()["order"]["reference"] == second.get_json()["order"]["reference"]
    assert Order.query.count() == 1


def test_archived_products_cannot_be_ordered(customer_client):
    Product.query.filter_by(slug="moss-lamp").update({"is_active": False})
    db.session.commit()
    assert place_order(customer_client, [{"slug": "moss-lamp", "quantity": 1}]).status_code == 400


def test_simulated_payment_marks_order_paid_once(customer_client):
    ref = place_order(customer_client).get_json()["order"]["reference"]
    resp = customer_client.post(f"/payments/simulated/{ref}", {"outcome": "success"})
    assert resp.get_json()["order"]["status"] == "paid"
    customer_client.post(f"/payments/simulated/{ref}", {"outcome": "success"})
    assert AuditLog.query.filter_by(action="payment.completed").count() == 1


def test_failed_payment_leaves_order_payable(customer_client):
    ref = place_order(customer_client).get_json()["order"]["reference"]
    order = customer_client.post(f"/payments/simulated/{ref}", {"outcome": "failure"}).get_json()["order"]
    assert order["status"] == "pending_payment" and order["payment_status"] == "failed" and order["can_pay"]


def test_payment_with_wrong_amount_is_not_accepted(customer_client):
    ref = place_order(customer_client).get_json()["order"]["reference"]
    order = Order.query.filter_by(reference=ref).one()
    apply_payment_result(order, PaymentResult("completed", amount=Decimal("1.00"), currency=order.currency,
                                              merchant_reference=ref), source="ipn")
    assert order.status == "pending_payment" and order.payment_status == "mismatch"
    assert AuditLog.query.filter_by(action="alert.payment_mismatch").count() == 1


def test_payment_for_other_reference_is_not_accepted(customer_client):
    ref = place_order(customer_client).get_json()["order"]["reference"]
    order = Order.query.filter_by(reference=ref).one()
    apply_payment_result(order, PaymentResult("completed", amount=order.total_amount, currency=order.currency,
                                              merchant_reference="TR-0000000000"), source="ipn")
    assert order.status == "pending_payment"


def test_ipn_verifies_with_provider_before_marking_paid(customer_client, monkeypatch):
    ref = place_order(customer_client).get_json()["order"]["reference"]
    order = Order.query.filter_by(reference=ref).one()
    order.payment_provider, order.payment_tracking_id = "pesapal", "abc-123"
    db.session.commit()
    checked = []

    def fake_status(o):
        checked.append(o.reference)
        return PaymentResult("completed", amount=o.total_amount, currency=o.currency,
                             merchant_reference=o.reference, method="M-Pesa")
    monkeypatch.setattr(api.orders, "fetch_verified_status", fake_status)

    resp = customer_client.get(f"/payments/pesapal/ipn?OrderTrackingId=abc-123&OrderMerchantReference={ref}"
                               "&OrderNotificationType=IPNCHANGE")
    assert resp.get_json()["status"] == 200
    assert checked == [ref]
    db.session.expire_all()
    assert Order.query.filter_by(reference=ref).one().status == "paid"


def test_ipn_for_unknown_order_is_rejected(client):
    resp = client.get("/payments/pesapal/ipn?OrderTrackingId=nope&OrderMerchantReference=TR-0000000000")
    assert resp.get_json()["status"] == 500
    assert AuditLog.query.filter_by(action="payment.ipn", outcome="failure").count() == 1


def test_ipn_cannot_be_used_to_mark_paid_without_provider_confirmation(customer_client, monkeypatch):
    ref = place_order(customer_client).get_json()["order"]["reference"]
    order = Order.query.filter_by(reference=ref).one()
    order.payment_provider, order.payment_tracking_id = "pesapal", "abc-123"
    db.session.commit()
    monkeypatch.setattr(api.orders, "fetch_verified_status", lambda o: PaymentResult("pending"))
    customer_client.get(f"/payments/pesapal/ipn?OrderTrackingId=abc-123&OrderMerchantReference={ref}")
    db.session.expire_all()
    assert Order.query.filter_by(reference=ref).one().status == "pending_payment"


def test_customer_can_cancel_unpaid_order_and_stock_returns(customer_client):
    before = stock("chalk-stoneware-mug")
    ref = place_order(customer_client).get_json()["order"]["reference"]
    resp = customer_client.post(f"/orders/{ref}/cancel")
    assert resp.status_code == 200 and resp.get_json()["order"]["status"] == "cancelled"
    assert stock("chalk-stoneware-mug") == before


def test_customer_cannot_cancel_paid_order(customer_client):
    ref = place_order(customer_client).get_json()["order"]["reference"]
    customer_client.post(f"/payments/simulated/{ref}", {"outcome": "success"})
    assert customer_client.post(f"/orders/{ref}/cancel").status_code == 409


def test_admin_status_transitions_follow_rules(customer_client, admin_client):
    ref = place_order(customer_client).get_json()["order"]["reference"]
    # Can't ship an unpaid order
    assert admin_client.patch(f"/admin/orders/{ref}/status", {"status": "shipped"}).status_code == 409
    customer_client.post(f"/payments/simulated/{ref}", {"outcome": "success"})
    assert admin_client.patch(f"/admin/orders/{ref}/status", {"status": "shipped"}).status_code == 200
    assert admin_client.patch(f"/admin/orders/{ref}/status", {"status": "paid"}).status_code == 409
    assert admin_client.patch(f"/admin/orders/{ref}/status", {"status": "delivered"}).status_code == 200
    assert admin_client.patch(f"/admin/orders/{ref}/status", {"status": "refunded"}).status_code == 200


def test_refund_before_shipping_restocks(customer_client, admin_client):
    before = stock("chalk-stoneware-mug")
    ref = place_order(customer_client).get_json()["order"]["reference"]
    customer_client.post(f"/payments/simulated/{ref}", {"outcome": "success"})
    admin_client.patch(f"/admin/orders/{ref}/status", {"status": "refunded"})
    assert stock("chalk-stoneware-mug") == before


def test_order_history_and_detail(customer_client):
    ref = place_order(customer_client).get_json()["order"]["reference"]
    items = customer_client.get("/orders").get_json()["items"]
    assert [o["reference"] for o in items] == [ref]
    detail = customer_client.get(f"/orders/{ref}").get_json()["order"]
    assert detail["items"][0]["product_name"] == "Chalk Stoneware Mug"
