from database import db
from datetime import datetime

class Product(db.Model):
    __tablename__ = 'products'

    product_id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(120), unique=True, index=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    old_price = db.Column(db.Numeric(10, 2))
    stock_quantity = db.Column(db.Integer, nullable=False)
    category = db.Column(db.String(100), nullable=False)
    image_url = db.Column(db.String(255))
    rating = db.Column(db.Float)
    badge = db.Column(db.String(40))
    sizes = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    order_items = db.relationship('OrderItem', back_populates='product', cascade='all, delete-orphan')
    reviews = db.relationship('Review', back_populates='product', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            "product_id": self.product_id,
            "slug": self.slug,
            "name": self.name,
            "description": self.description,
            "price": float(self.price),
            "old_price": float(self.old_price) if self.old_price is not None else None,
            "stock_quantity": self.stock_quantity,
            "category": self.category,
            "image_url": self.image_url,
            "rating": self.rating,
            "badge": self.badge,
            "sizes": self.sizes or [],
        }
