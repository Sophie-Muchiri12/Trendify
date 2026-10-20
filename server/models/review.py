from database import db
from models.user import utcnow


class Review(db.Model):
    __tablename__ = 'reviews'
    # One review per customer per product (A05: stops repeated/fake reviews).
    __table_args__ = (db.UniqueConstraint('user_id', 'product_id', name='uq_reviews_user_product'),)

    STATUSES = ('pending', 'approved', 'rejected')

    review_id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.product_id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    review_text = db.Column(db.Text)
    status = db.Column(db.String(20), nullable=False, default='pending')
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)

    # Relationships
    product = db.relationship('Product', back_populates='reviews')
    user = db.relationship('User', back_populates='reviews')

    def to_public_dict(self):
        return {
            "review_id": self.review_id,
            "rating": self.rating,
            "review_text": self.review_text,
            # Only a first name is shown publicly.
            "author": (self.user.name.split()[0] if self.user and self.user.name else "Customer"),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def to_owner_dict(self):
        data = self.to_public_dict()
        data.update({
            "status": self.status,
            "product_slug": self.product.slug if self.product else None,
            "product_name": self.product.name if self.product else None,
        })
        return data

    def to_admin_dict(self):
        data = self.to_owner_dict()
        data.update({"user_id": self.user_id, "user_email": self.user.email if self.user else None})
        return data
