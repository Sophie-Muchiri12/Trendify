"""Request validation (A04).

Every request body and query string is validated against a schema before it is used.
Unknown fields are rejected (RAISE), which prevents mass assignment such as a customer
sending {"role": "admin"} when registering.
"""
import re
from decimal import Decimal

from flask import request
from marshmallow import (RAISE, Schema, ValidationError, fields, pre_load, validate,
                         validates, validates_schema)

from errors import ApiError
from models.order import Order
from models.product import Product
from models.review import Review

PHONE_RE = re.compile(r"^\+?[0-9]{7,15}$")
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
IMAGE_PATH_RE = re.compile(r"^/static/products/[A-Za-z0-9_-]{1,80}\.(jpg|jpeg|png|webp)$")


class StrictSchema(Schema):
    class Meta:
        unknown = RAISE

    @pre_load
    def strip_strings(self, data, **kwargs):
        if isinstance(data, dict):
            return {k: (v.strip() if isinstance(v, str) and k not in self.NO_STRIP else v)
                    for k, v in data.items()}
        return data

    # Passwords are used exactly as typed.
    NO_STRIP = {"password", "current_password", "new_password"}


def Name():
    return fields.String(required=True, validate=validate.Length(min=1, max=120))


def Email():
    return fields.Email(required=True, validate=validate.Length(max=255))


def Phone(required=True):
    return fields.String(required=required, validate=validate.Regexp(
        PHONE_RE, error="Enter a phone number with 7-15 digits, optionally starting with +."))


def Password():
    return fields.String(required=True, validate=validate.Length(min=1, max=128))


# --- Auth & account --------------------------------------------------------------

class RegisterSchema(StrictSchema):
    name = Name()
    email = Email()
    phone_number = Phone()
    password = Password()


class LoginSchema(StrictSchema):
    email = Email()
    password = Password()
    otp = fields.String(load_default=None, validate=validate.Regexp(r"^\d{6}$", error="Enter the 6-digit code."))


class EmailOnlySchema(StrictSchema):
    email = Email()


class TokenSchema(StrictSchema):
    token = fields.String(required=True, validate=validate.Length(min=20, max=200))


class ResetPasswordSchema(StrictSchema):
    token = fields.String(required=True, validate=validate.Length(min=20, max=200))
    password = Password()


class ProfileUpdateSchema(StrictSchema):
    name = fields.String(validate=validate.Length(min=1, max=120))
    phone_number = Phone(required=False)


class ChangePasswordSchema(StrictSchema):
    current_password = Password()
    new_password = Password()


class PasswordConfirmSchema(StrictSchema):
    password = Password()


class MfaCodeSchema(StrictSchema):
    code = fields.String(required=True, validate=validate.Regexp(r"^\d{6}$", error="Enter the 6-digit code."))


class MfaDisableSchema(StrictSchema):
    password = Password()
    code = fields.String(required=True, validate=validate.Regexp(r"^\d{6}$", error="Enter the 6-digit code."))


# --- Products ---------------------------------------------------------------------

class ProductQuerySchema(StrictSchema):
    q = fields.String(load_default=None, validate=validate.Length(max=100))
    category = fields.String(load_default=None, validate=validate.OneOf(Product.CATEGORIES))
    min_price = fields.Decimal(load_default=None, validate=validate.Range(min=0, max=1_000_000))
    max_price = fields.Decimal(load_default=None, validate=validate.Range(min=0, max=1_000_000))
    sort = fields.String(load_default="featured",
                         validate=validate.OneOf(["featured", "price_asc", "price_desc", "rating", "newest"]))
    page = fields.Integer(load_default=1, validate=validate.Range(min=1, max=10_000))
    per_page = fields.Integer(load_default=100, validate=validate.Range(min=1, max=100))


class AdminProductQuerySchema(ProductQuerySchema):
    status = fields.String(load_default="all", validate=validate.OneOf(["all", "active", "archived"]))


Money = lambda **kw: fields.Decimal(places=2, as_string=False,  # noqa: E731
                                    validate=validate.Range(min=Decimal("0.01"), max=Decimal("100000")), **kw)


class ProductSchema(StrictSchema):
    name = fields.String(required=True, validate=validate.Length(min=1, max=255))
    slug = fields.String(load_default=None, validate=[
        validate.Length(min=1, max=120),
        validate.Regexp(SLUG_RE, error="Use lower-case letters, numbers and hyphens only."),
    ])
    description = fields.String(required=True, validate=validate.Length(min=1, max=5000))
    price = Money(required=True)
    old_price = Money(load_default=None, allow_none=True)
    stock_quantity = fields.Integer(required=True, strict=True, validate=validate.Range(min=0, max=100_000))
    category = fields.String(required=True, validate=validate.OneOf(Product.CATEGORIES))
    image_url = fields.String(load_default=None, allow_none=True, validate=validate.Regexp(
        IMAGE_PATH_RE, error="Upload the image first and use the path it returns."))
    badge = fields.String(load_default=None, allow_none=True, validate=validate.Length(max=40))
    sizes = fields.List(fields.String(validate=validate.Length(min=1, max=10)),
                        load_default=list, validate=validate.Length(max=20))

    @validates_schema
    def old_price_above_price(self, data, **kwargs):
        if data.get("old_price") is not None and data.get("price") is not None \
                and data["old_price"] <= data["price"]:
            raise ValidationError("The old price must be higher than the price.", "old_price")


class ProductUpdateSchema(ProductSchema):
    """Same rules as ProductSchema, but every field is optional (PATCH)."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, partial=True, **kwargs)


# --- Reviews ----------------------------------------------------------------------

class ReviewSchema(StrictSchema):
    rating = fields.Integer(required=True, strict=True, validate=validate.Range(min=1, max=5))
    review_text = fields.String(load_default="", validate=validate.Length(max=2000))


class ReviewUpdateSchema(ReviewSchema):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, partial=True, **kwargs)


class ReviewModerationSchema(StrictSchema):
    status = fields.String(required=True, validate=validate.OneOf(["approved", "rejected"]))


class ReviewQuerySchema(StrictSchema):
    status = fields.String(load_default=None, validate=validate.OneOf(Review.STATUSES))
    page = fields.Integer(load_default=1, validate=validate.Range(min=1, max=10_000))
    per_page = fields.Integer(load_default=50, validate=validate.Range(min=1, max=100))


# --- Orders -----------------------------------------------------------------------

class OrderItemSchema(StrictSchema):
    slug = fields.String(required=True, validate=validate.Regexp(SLUG_RE))
    quantity = fields.Integer(required=True, strict=True, validate=validate.Range(min=1, max=10))
    size = fields.String(load_default=None, allow_none=True, validate=validate.Length(max=10))


class OrderCreateSchema(StrictSchema):
    items = fields.List(fields.Nested(OrderItemSchema), required=True,
                        validate=validate.Length(min=1, max=50))
    shipping_address = fields.String(required=True, validate=validate.Length(min=5, max=255))
    phone_number = Phone()

    @validates("items")
    def no_duplicate_lines(self, items, **kwargs):
        keys = [(i["slug"], i.get("size")) for i in items]
        if len(keys) != len(set(keys)):
            raise ValidationError("Each product and size may only appear once.")


class OrderStatusSchema(StrictSchema):
    status = fields.String(required=True, validate=validate.OneOf(Order.STATUSES))


class OrderQuerySchema(StrictSchema):
    status = fields.String(load_default=None, validate=validate.OneOf(Order.STATUSES))
    q = fields.String(load_default=None, validate=validate.Length(max=100))
    page = fields.Integer(load_default=1, validate=validate.Range(min=1, max=10_000))
    per_page = fields.Integer(load_default=50, validate=validate.Range(min=1, max=100))


class PaymentOutcomeSchema(StrictSchema):
    outcome = fields.String(required=True, validate=validate.OneOf(["success", "failure"]))


# --- Admin: users & audit -----------------------------------------------------------

class AdminUserUpdateSchema(StrictSchema):
    role = fields.String(validate=validate.OneOf(("customer", "admin")))
    is_active = fields.Boolean()


class UserQuerySchema(StrictSchema):
    q = fields.String(load_default=None, validate=validate.Length(max=100))
    role = fields.String(load_default=None, validate=validate.OneOf(("customer", "admin")))
    page = fields.Integer(load_default=1, validate=validate.Range(min=1, max=10_000))
    per_page = fields.Integer(load_default=50, validate=validate.Range(min=1, max=100))


class AuditQuerySchema(StrictSchema):
    action = fields.String(load_default=None, validate=validate.Length(max=64))
    outcome = fields.String(load_default=None, validate=validate.OneOf(("success", "failure", "denied")))
    page = fields.Integer(load_default=1, validate=validate.Range(min=1, max=10_000))
    per_page = fields.Integer(load_default=50, validate=validate.Range(min=1, max=200))


# --- Helpers ----------------------------------------------------------------------

def load_json(schema):
    """Validate the JSON body. Non-JSON or non-object bodies are rejected."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ApiError(400, "Send a JSON object with Content-Type: application/json.")
    return schema.load(data)


def load_query(schema):
    return schema.load(request.args.to_dict())
