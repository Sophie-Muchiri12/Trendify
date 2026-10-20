"""Reset the database and load demo data.

    python seed.py

Drops and recreates every table, then loads the catalog from catalog.py plus demo
accounts, reviews and orders. There are no built-in default passwords (A02): each demo
account gets a random password that is printed once, unless you set SEED_PASSWORD to a
password that meets the password policy (handy for a class demo).

Refuses to run with APP_ENV=production.
"""
import os
import secrets
import string
import sys
from decimal import Decimal

from flask_migrate import stamp

from app import create_app
from catalog import PRODUCTS
from database import db
from models import Order, OrderItem, Product, Review, User
from models.user import utcnow
from security import hash_password, password_problems
from services import new_order_reference, refresh_product_rating

DEMO_USERS = [
    ("admin@example.com", "Ada Admin", "+254700000001", "admin"),
    ("john@example.com", "John Doe", "+254700000002", "customer"),
    ("jane@example.com", "Jane Smith", "+254700000003", "customer"),
]


def random_password():
    alphabet = string.ascii_letters + string.digits
    while True:
        pw = "".join(secrets.choice(alphabet) for _ in range(16))
        if not password_problems(pw):
            return pw


def main():
    if os.environ.get("APP_ENV", "development").lower() == "production":
        sys.exit("Refusing to seed: this deletes all data and APP_ENV is production.")

    shared_password = os.environ.get("SEED_PASSWORD")
    if shared_password and password_problems(shared_password):
        sys.exit("SEED_PASSWORD is too weak: " + " ".join(password_problems(shared_password)))

    app = create_app()
    with app.app_context():
        db.drop_all()
        db.create_all()

        credentials = []
        users = {}
        for email, name, phone, role in DEMO_USERS:
            password = shared_password or random_password()
            user = User(email=email, name=name, phone_number=phone, role=role,
                        password_hash=hash_password(password), email_verified_at=utcnow())
            db.session.add(user)
            users[email] = user
            credentials.append((email, role, password))
        db.session.commit()

        db.session.add_all([Product(**data) for data in PRODUCTS])
        db.session.commit()

        def product(slug):
            return Product.query.filter_by(slug=slug).one()

        def order(user, status, address, lines):
            o = Order(reference=new_order_reference(), user_id=user.user_id, status=status,
                      shipping_address=address, phone_number=user.phone_number,
                      currency=app.config["CURRENCY"], total_amount=Decimal("0"),
                      payment_provider="simulated", payment_status="completed" if status != "pending_payment" else None,
                      paid_at=utcnow() if status != "pending_payment" else None)
            db.session.add(o)
            for slug, qty, size in lines:
                p = product(slug)
                o.order_items.append(OrderItem(product_id=p.product_id, quantity=qty, size=size,
                                               price_at_purchase=p.price, product_name=p.name))
                o.total_amount += p.price * qty
            return o

        john, jane = users["john@example.com"], users["jane@example.com"]
        order(john, "delivered", "123 Moi Avenue, Nairobi",
              [("vortex-runner", 1, "42"), ("chalk-stoneware-mug", 2, None), ("fern-trail-boot", 1, "43"),
               ("kilim-runner", 1, None)])
        order(jane, "shipped", "456 Kenyatta Road, Mombasa",
              [("lena-linen-shirt", 1, "M"), ("vortex-runner", 1, "39")])
        order(jane, "pending_payment", "456 Kenyatta Road, Mombasa", [("cedar-fig-candle", 2, None)])
        db.session.commit()

        reviews = [
            ("vortex-runner", john, 5, "So comfortable I bought a second pair. Walked all day with no sore feet."),
            ("vortex-runner", jane, 4, "Great cushioning. Runs slightly large, so size down if you're between sizes."),
            ("lena-linen-shirt", jane, 5, "Beautiful colour, and it softens with every wash."),
            ("chalk-stoneware-mug", john, 5, "Lovely weight in the hand and keeps coffee warm."),
            ("kilim-runner", john, 5, "Even richer colours in person. It completely changed our hallway."),
            ("fern-trail-boot", john, 4, "Solid boots. They took a couple of walks to break in, then they were perfect."),
        ]
        for slug, user, rating, text in reviews:
            db.session.add(Review(product_id=product(slug).product_id, user_id=user.user_id,
                                  rating=rating, review_text=text, status="approved"))
        db.session.flush()
        for slug in {r[0] for r in reviews}:
            refresh_product_rating(product(slug))
        db.session.commit()

        # create_all() built the latest schema, so record that in alembic_version
        stamp(directory=os.path.join(os.path.dirname(os.path.abspath(__file__)), "migrations"))

    print("\nDatabase seeded successfully!\n")
    print("Demo accounts (shown only now; run seed.py again or use 'Forgot password' to reset):")
    for email, role, password in credentials:
        print(f"  {role:<9} {email:<20} {password}")
    print()


if __name__ == "__main__":
    main()
