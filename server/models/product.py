from database import db
from models.user import utcnow


class Product(db.Model):
    __tablename__ = 'products'

    CATEGORIES = ('Footwear', 'Apparel', 'Ceramics', 'Home')

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
    review_count = db.Column(db.Integer, nullable=False, default=0)
    badge = db.Column(db.String(40))
    sizes = db.Column(db.JSON)
    # Products are archived rather than deleted so past orders keep their history.
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)

    # Relationships
    order_items = db.relationship('OrderItem', back_populates='product')
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
            "in_stock": self.stock_quantity > 0,
            "category": self.category,
            "image_url": self.image_url,
            "rating": self.rating,
            "review_count": self.review_count,
            "badge": self.badge,
            "sizes": self.sizes or [],
        }

    def to_admin_dict(self):
        data = self.to_dict()
        data.update({
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        })
        return data
