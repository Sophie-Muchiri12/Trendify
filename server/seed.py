import os
from datetime import datetime
from flask_migrate import stamp
from werkzeug.security import generate_password_hash
from app import create_app
from catalog import PRODUCTS
from database import db
from models import User, Product, Review, Order, OrderItem

app = create_app()

with app.app_context():
    # Drop all tables and recreate them for clean seeding (optional, use with caution)
    db.drop_all()
    db.create_all()

    # Seed Users
    user1 = User(
        name="John Doe",
        email="john@example.com",
        phone_number="1234567890",
        password_hash=generate_password_hash("password123"),
    )
    user2 = User(
        name="Jane Smith",
        email="jane@example.com",
        phone_number="0987654321",
        password_hash=generate_password_hash("securepassword"),
    )
    admin = User(
        name="Admin User",
        email="admin@example.com",
        phone_number="1112223333",
        password_hash=generate_password_hash("adminpassword"),
    )
    db.session.add_all([user1, user2, admin])
    db.session.commit()  # Commit here to ensure users have IDs assigned

    # Seed Products (catalog.py holds the storefront catalog)
    db.session.add_all([Product(**data) for data in PRODUCTS])
    db.session.commit()  # Commit products to ensure they have IDs

    def product(slug):
        return Product.query.filter_by(slug=slug).one()

    # Seed Reviews
    reviews = [
        ("vortex-runner", user1, 5, "So comfortable I bought a second pair. Walked all day with no sore feet."),
        ("vortex-runner", user2, 4, "Great cushioning. Runs slightly large, so size down if you're between sizes."),
        ("lena-linen-shirt", user2, 5, "Beautiful colour, and it softens with every wash."),
        ("chalk-stoneware-mug", user1, 5, "Lovely weight in the hand and keeps coffee warm."),
        ("kilim-runner", user2, 5, "Even richer colours in person. It completely changed our hallway."),
        ("fern-trail-boot", user1, 4, "Solid boots. They took a couple of walks to break in, then they were perfect."),
    ]
    db.session.add_all([
        Review(
            product_id=product(slug).product_id,
            user_id=user.user_id,
            rating=rating,
            review_text=text,
            created_at=datetime.utcnow(),
        )
        for slug, user, rating, text in reviews
    ])
    db.session.commit()  # Commit reviews

    # Seed Orders and Order Items
    def order(user, status, address, lines):
        o = Order(
            user_id=user.user_id,
            total_amount=sum(product(slug).price * qty for slug, qty in lines),
            status=status,
            shipping_address=address,
            created_at=datetime.utcnow(),
        )
        db.session.add(o)
        for slug, qty in lines:
            p = product(slug)
            db.session.add(OrderItem(order=o, product_id=p.product_id, quantity=qty, price_at_purchase=p.price))

    order(user1, "completed", "123 Main Street, Cityville", [("vortex-runner", 1)])
    order(user2, "pending", "456 Maple Avenue, Townsville", [("lena-linen-shirt", 1), ("chalk-stoneware-mug", 2)])

    # Commit all orders and order items
    db.session.commit()

    # create_all() built the latest schema, so record that in alembic_version
    stamp(directory=os.path.join(os.path.dirname(os.path.abspath(__file__)), "migrations"))
    print("Database seeded successfully!")
