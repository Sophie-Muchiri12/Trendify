from database import db
from models.user import utcnow


class Order(db.Model):
    __tablename__ = 'orders'
    # The same idempotency key from the same user always maps to one order (A05 / A09).
    __table_args__ = (db.UniqueConstraint('user_id', 'idempotency_key', name='uq_orders_user_idempotency'),)

    STATUSES = ('pending_payment', 'paid', 'shipped', 'delivered', 'cancelled', 'refunded')
    # Allowed status changes. Anything else is rejected (A05: explicit business rules).
    ADMIN_TRANSITIONS = {
        'pending_payment': {'cancelled'},
        'paid': {'shipped', 'refunded'},
        'shipped': {'delivered', 'refunded'},
        'delivered': {'refunded'},
        'cancelled': set(),
        'refunded': set(),
    }
    CUSTOMER_CANCELLABLE = {'pending_payment'}

    order_id = db.Column(db.Integer, primary_key=True)
    # Random public reference (also the Pesapal merchant reference), so ids aren't guessable.
    reference = db.Column(db.String(32), unique=True, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(3), nullable=False, default='USD')
    status = db.Column(db.String(20), nullable=False, default='pending_payment')
    shipping_address = db.Column(db.String(255), nullable=False)
    phone_number = db.Column(db.String(20))
    idempotency_key = db.Column(db.String(64))

    payment_provider = db.Column(db.String(20))
    payment_tracking_id = db.Column(db.String(64), unique=True)
    payment_status = db.Column(db.String(30))
    payment_method = db.Column(db.String(50))
    paid_at = db.Column(db.DateTime)
    cancelled_at = db.Column(db.DateTime)

    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)

    # Relationships
    user = db.relationship('User', back_populates='orders')
    order_items = db.relationship('OrderItem', back_populates='order', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            "order_id": self.order_id,
            "reference": self.reference,
            "status": self.status,
            "total_amount": float(self.total_amount),
            "currency": self.currency,
            "shipping_address": self.shipping_address,
            "phone_number": self.phone_number,
            "payment_status": self.payment_status,
            "payment_method": self.payment_method,
            "paid_at": self.paid_at.isoformat() if self.paid_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "can_cancel": self.status in self.CUSTOMER_CANCELLABLE,
            "can_pay": self.status == 'pending_payment',
            "items": [item.to_dict() for item in self.order_items],
        }

    def to_admin_dict(self):
        data = self.to_dict()
        data.update({
            "user_id": self.user_id,
            "user_email": self.user.email if self.user else None,
            "payment_provider": self.payment_provider,
            "payment_tracking_id": self.payment_tracking_id,
            "allowed_transitions": sorted(self.ADMIN_TRANSITIONS.get(self.status, ())),
        })
        return data
