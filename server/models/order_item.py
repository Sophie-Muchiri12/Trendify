from database import db


class OrderItem(db.Model):
    __tablename__ = 'order_items'

    order_item_id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.order_id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.product_id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    # Snapshot of the trusted database price and name at the moment of purchase.
    price_at_purchase = db.Column(db.Numeric(10, 2), nullable=False)
    product_name = db.Column(db.String(255))
    size = db.Column(db.String(10))

    # Relationships
    order = db.relationship('Order', back_populates='order_items')
    product = db.relationship('Product', back_populates='order_items')

    def to_dict(self):
        return {
            "product_id": self.product_id,
            "product_slug": self.product.slug if self.product else None,
            "product_name": self.product_name or (self.product.name if self.product else None),
            "image_url": self.product.image_url if self.product else None,
            "quantity": self.quantity,
            "size": self.size,
            "price": float(self.price_at_purchase),
            "line_total": float(self.price_at_purchase * self.quantity),
        }
