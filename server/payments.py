"""Payment providers (Pesapal API 3.0, plus a simulator for local development).

Security rules (A05 / A07 / A09):
* The amount sent to Pesapal is the order total calculated on the server.
* Pesapal's IPN and the browser redirect are only *hints* that something changed. The
  order is marked paid only after we ask Pesapal directly (GetTransactionStatus, the
  verification Pesapal recommends) and the amount, currency and merchant reference all
  match our order.
* Status updates are idempotent: a repeated notification can't pay an order twice.
* No card or mobile-money details ever touch our servers; Pesapal collects them.
"""
import logging
import time
from decimal import Decimal

import requests
from flask import current_app

from errors import ApiError

log = logging.getLogger("trendify")

PESAPAL_URLS = {
    "sandbox": "https://cybqa.pesapal.com/pesapalv3",
    "live": "https://pay.pesapal.com/v3",
}
TIMEOUT_SECONDS = 15

# Pesapal status_code values from GetTransactionStatus
STATUS_INVALID, STATUS_COMPLETED, STATUS_FAILED, STATUS_REVERSED = 0, 1, 2, 3


class PaymentError(Exception):
    pass


class PaymentResult:
    """Normalised result of a verified status check."""

    def __init__(self, state, amount=None, currency=None, merchant_reference=None,
                 method=None, description=None):
        self.state = state  # "completed" | "failed" | "pending" | "reversed"
        self.amount = amount
        self.currency = currency
        self.merchant_reference = merchant_reference
        self.method = method
        self.description = description


class PesapalClient:
    _token_cache = {}  # {(base_url, key): (token, expires_monotonic)}
    _ipn_cache = {}

    def __init__(self, config):
        self.base_url = PESAPAL_URLS.get(config["PESAPAL_ENV"], PESAPAL_URLS["sandbox"])
        self.key = config.get("PESAPAL_CONSUMER_KEY")
        self.secret = config.get("PESAPAL_CONSUMER_SECRET")
        self.configured_ipn_id = config.get("PESAPAL_IPN_ID")
        self.ipn_url = f"{config['API_PUBLIC_URL']}/payments/pesapal/ipn"
        if not (self.key and self.secret):
            raise PaymentError("Pesapal credentials are not configured")

    def _request(self, method, path, *, token=None, **kwargs):
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        try:
            resp = requests.request(method, f"{self.base_url}{path}", headers=headers,
                                    timeout=TIMEOUT_SECONDS, **kwargs)
            resp.raise_for_status()
            data = resp.json()
        except (requests.RequestException, ValueError) as exc:
            raise PaymentError(f"Pesapal request to {path} failed") from exc
        if isinstance(data, dict) and data.get("error"):
            raise PaymentError(f"Pesapal returned an error for {path}: {data['error'].get('code')}")
        return data

    def token(self):
        cache_key = (self.base_url, self.key)
        cached = self._token_cache.get(cache_key)
        if cached and cached[1] > time.monotonic():
            return cached[0]
        data = self._request("POST", "/api/Auth/RequestToken",
                             json={"consumer_key": self.key, "consumer_secret": self.secret})
        token = data.get("token")
        if not token:
            raise PaymentError("Pesapal did not return a token")
        self._token_cache[cache_key] = (token, time.monotonic() + 240)  # tokens last 5 minutes
        return token

    def ipn_id(self):
        if self.configured_ipn_id:
            return self.configured_ipn_id
        cache_key = (self.base_url, self.ipn_url)
        if cache_key not in self._ipn_cache:
            data = self._request("POST", "/api/URLSetup/RegisterIPN", token=self.token(),
                                 json={"url": self.ipn_url, "ipn_notification_type": "GET"})
            self._ipn_cache[cache_key] = data["ipn_id"]
            log.info("Registered Pesapal IPN %s for %s; set PESAPAL_IPN_ID to reuse it",
                     data["ipn_id"], self.ipn_url)
        return self._ipn_cache[cache_key]

    def submit_order(self, order, user, callback_url):
        first, _, last = (user.name or "Customer").partition(" ")
        payload = {
            "id": order.reference,
            "currency": order.currency,
            "amount": float(order.total_amount),
            "description": f"Trendify order {order.reference}"[:100],
            "callback_url": callback_url,
            "notification_id": self.ipn_id(),
            "billing_address": {
                "email_address": user.email,
                "phone_number": order.phone_number or user.phone_number,
                "first_name": first[:50],
                "last_name": (last or first)[:50],
                "line_1": order.shipping_address[:100],
            },
        }
        data = self._request("POST", "/api/Transactions/SubmitOrderRequest", token=self.token(), json=payload)
        if not data.get("order_tracking_id") or not data.get("redirect_url"):
            raise PaymentError("Pesapal did not return a tracking id")
        return data["order_tracking_id"], data["redirect_url"]

    def transaction_status(self, tracking_id):
        data = self._request("GET", "/api/Transactions/GetTransactionStatus", token=self.token(),
                             params={"orderTrackingId": tracking_id})
        code = data.get("status_code")
        state = {STATUS_COMPLETED: "completed", STATUS_FAILED: "failed",
                 STATUS_REVERSED: "reversed"}.get(code, "pending")
        return PaymentResult(
            state=state,
            amount=Decimal(str(data["amount"])) if data.get("amount") is not None else None,
            currency=data.get("currency"),
            merchant_reference=data.get("merchant_reference"),
            method=data.get("payment_method"),
            description=data.get("payment_status_description"),
        )


def provider_name():
    return current_app.config["PAYMENT_PROVIDER"]


def start_payment(order, user):
    """Create the payment with the provider. Returns the URL to send the customer to."""
    callback_url = f"{current_app.config['FRONTEND_URL']}/checkout/result?ref={order.reference}"
    if provider_name() == "simulated":
        if current_app.config["ENV_NAME"] == "production":
            raise ApiError(500)
        order.payment_provider = "simulated"
        order.payment_tracking_id = order.payment_tracking_id or f"SIM-{order.reference}"
        order.payment_status = "pending"
        return f"{current_app.config['FRONTEND_URL']}/checkout/simulate?ref={order.reference}"

    try:
        client = PesapalClient(current_app.config)
        tracking_id, redirect_url = client.submit_order(order, user, callback_url)
    except PaymentError:
        log.exception("Could not start Pesapal payment for order %s", order.reference)
        raise ApiError(502, "The payment service is unavailable right now. Your order is saved; "
                            "please try paying again in a few minutes.")
    order.payment_provider = "pesapal"
    order.payment_tracking_id = tracking_id
    order.payment_status = "pending"
    return redirect_url


def fetch_verified_status(order):
    """Ask the provider for the real status of the order's payment."""
    if order.payment_provider == "simulated":
        return None  # simulated payments are settled by the simulator endpoint
    if not order.payment_tracking_id:
        return PaymentResult("pending")
    try:
        return PesapalClient(current_app.config).transaction_status(order.payment_tracking_id)
    except PaymentError:
        log.exception("Could not verify Pesapal payment for order %s", order.reference)
        return None
