from datetime import datetime
from werkzeug.security import generate_password_hash
from app import create_app
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

    # Seed Products
    products = [
        Product(
            name="Vintage Leather Jacket",
            description="A high-quality leather jacket with a vintage feel.",
            price=120.00,
            stock_quantity=10,
            category="Men's Wear",
            image_url="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTTvFW3vxZrIj2kdJfjFoG7L6M8y51rUrct3w&s",
        ),
        Product(
            name="Handmade Silver Necklace",
            description="A beautiful handmade silver necklace perfect for any occasion.",
            price=80.00,
            stock_quantity=25,
            category="Jewelry",
            image_url="https://th.bing.com/th/id/OIP.3u9XwOoXe4B946OlBxiZMwAAAA?w=474&h=474&rs=1&pid=ImgDetMain",
        ),
        Product(
            name="Running Shoes",
            description="Lightweight running shoes designed for maximum comfort and performance.",
            price=60.00,
            stock_quantity=50,
            category="Footwear",
            image_url="https://th.bing.com/th/id/R.94d9d4c622bc2bd88bc90210b12f63c6?rik=r5KR74hiWnr6nA&pid=ImgRaw&r=0",
        ),
        Product(
            name="Classic White T-Shirt",
            description="A staple piece for any wardrobe, this classic white t-shirt is comfortable and versatile.",
            price=20.00,
            stock_quantity=100,
            category="Men's Wear",
            image_url="https://5fbb4b60e5a371522c26-c46478628be7be7c70f96ec65a31d1c7.ssl.cf3.rackcdn.com/Images/ProductImages/BadRhino_White_Basic_Plain_Crew_Neck_T-Shirt_-_REG_54617_a41d.jpg",
        ),
        Product(
            name="Blue Denim Jeans",
            description="Stylish blue denim jeans that fit perfectly and are ideal for any casual outing.",
            price=40.00,
            stock_quantity=30,
            category="Men's Wear",
            image_url="https://www.bing.com/images/search?view=detailV2&ccid=gljsAkzx&id=614B98E18EBB3FEA543221AEA848B4522060F01E&thid=OIP.gljsAkzxOY4MezNJxcH31AHaJQ&mediaurl=https%3a%2f%2ffuturevisions.pe%2f22957-large_default%2f001-denim-blue.jpg&cdnurl=https%3a%2f%2fth.bing.com%2fth%2fid%2fR.8258ec024cf1398e0c7b3349c5c1f7d4%3frik%3dHvBgIFK0SKiuIQ%26pid%3dImgRaw%26r%3d0&exph=2160&expw=1728&q=blue+denim+jeans&simid=608036412178438865&FORM=IRPRST&ck=52DE6EFB24815D98198BE918E36DCAFE&selectedIndex=24&itb=0",
        ),
        Product(
            name="Leather Backpack",
            description="A durable and stylish leather backpack for everyday use.",
            price=90.00,
            stock_quantity=15,
            category="Accessories",
            image_url="https://i.etsystatic.com/10716722/r/il/931f9a/3055164170/il_fullxfull.3055164170_2qn3.jpg",
        ),
        Product(
            name="Sports Watch",
            description="A rugged sports watch that can withstand the elements.",
            price=70.00,
            stock_quantity=20,
            category="Accessories",
            image_url="https://th.bing.com/th/id/R.4274fe3b3fbf1ab6ac09d036cfe8fb9d?rik=ZeaC2PODPsP1TQ&pid=ImgRaw&r=0",
        ),
        Product(
            name="Summer Dress",
            description="A light and breezy summer dress perfect for sunny days.",
            price=55.00,
            stock_quantity=40,
            category="Women's Wear",
            image_url="https://th.bing.com/th/id/R.367e1be2960671f136a11eecf037bf95?rik=YitNXMJbRKw6Pg&pid=ImgRaw&r=0",
        ),
        Product(
            name="Canvas Sneakers",
            description="Casual canvas sneakers that are perfect for everyday wear.",
            price=45.00,
            stock_quantity=60,
            category="Footwear",
            image_url="https://th.bing.com/th/id/OIP.pppK_cCRITRqgHJDl5qe_wHaHa?rs=1&pid=ImgDetMain",
        ),
        Product(
            name="Silk Scarf",
            description="A luxurious silk scarf that adds elegance to any outfit.",
            price=35.00,
            stock_quantity=25,
            category="Accessories",
            image_url="https://th.bing.com/th/id/R.0833cf0f46d8c2f91ab81d4052335aa8?rik=I%2bd5OyWa1gPuYg&pid=ImgRaw&r=0",
        ),
        Product(
            name="Floral Print Blouse",
            description="A stylish floral print blouse that is perfect for spring.",
            price=50.00,
            stock_quantity=20,
            category="Women's Wear",
            image_url="https://th.bing.com/th/id/OIP.XuDgr8Nai01lZttjxeSXqAAAAA?rs=1&pid=ImgDetMain",
        ),
        Product(
            name="Wool Sweater",
            description="A cozy wool sweater for the colder months.",
            price=75.00,
            stock_quantity=18,
            category="Men's Wear",
            image_url="https://th.bing.com/th/id/OIP.ifyv9QHFZoe829hayURH5gHaHa?rs=1&pid=ImgDetMain",
        ),
        Product(
            name="Classic Sunglasses",
            description="Timeless sunglasses that protect your eyes in style.",
            price=60.00,
            stock_quantity=30,
            category="Accessories",
            image_url="https://th.bing.com/th/id/OIP.epndKA3h6-985p3mxGyZjgHaE8?rs=1&pid=ImgDetMain",
        ),
        Product(
            name="Leather Wallet",
            description="A sleek leather wallet that is perfect for everyday use.",
            price=40.00,
            stock_quantity=50,
            category="Accessories",
            image_url="https://th.bing.com/th/id/OIP.GpnJ4IhgtY959y3SWGk_sAAAAA?rs=1&pid=ImgDetMain",
        ),
        Product(
            name="Winter Coat",
            description="A warm and stylish winter coat to keep you cozy.",
            price=150.00,
            stock_quantity=12,
            category="Women's Wear",
            image_url="https://th.bing.com/th/id/OIP.C48KSTYpiZ75pZokqENx9AHaIt?rs=1&pid=ImgDetMain",
        ),
        Product(
            name="Casual Shorts",
            description="Comfortable casual shorts for summer outings.",
            price=30.00,
            stock_quantity=70,
            category="Men's Wear",
            image_url="https://th.bing.com/th/id/OIP.HBjTDG0w5rwQ68ryZ5kMwwHaGT?rs=1&pid=ImgDetMain",
        ),
        Product(
            name="Yoga Mat",
            description="A non-slip yoga mat for all your fitness needs.",
            price=25.00,
            stock_quantity=35,
            category="Fitness",
            image_url="https://th.bing.com/th/id/OIP.5h2H8WmIodRhFNx9d45DGAAAAA?rs=1&pid=ImgDetMain",
        ),
        Product(
            name="Bluetooth Headphones",
            description="High-quality Bluetooth headphones with noise cancellation.",
            price=120.00,
            stock_quantity=22,
            category="Electronics",
            image_url="https://th.bing.com/th/id/R.d7ad97800dcb82d10ff1d11ec00e844c?rik=00dE6coLOX65hA&pid=ImgRaw&r=0",
        ),
        Product(
            name="Smartphone Stand",
            description="An adjustable smartphone stand for convenient use.",
            price=15.00,
            stock_quantity=100,
            category="Electronics",
            image_url="https://images-na.ssl-images-amazon.com/images/I/61If5TV5RAL._SL1500_.jpg",
        ),
        Product(
            name="Cookbook",
            description="A delightful cookbook filled with delicious recipes.",
            price=25.00,
            stock_quantity=50,
            category="Books",
            image_url="https://th.bing.com/th/id/OIP.ssvk_LoxofEfwadwgQEIlAHaJI?rs=1&pid=ImgDetMain",
        ),
        Product(
            name="Ceramic Mug",
            description="A beautifully crafted ceramic mug for your morning coffee.",
            price=15.00,
            stock_quantity=200,
            category="Home & Kitchen",
            image_url="https://th.bing.com/th/id/OIP.YxVfKSMDFLE0JA0CbEHnBwHaF7?rs=1&pid=ImgDetMain",
        ),
        Product(
            name="Wall Art",
            description="Stunning wall art to brighten up your living space.",
            price=80.00,
            stock_quantity=10,
            category="Home Decor",
            image_url="https://th.bing.com/th/id/R.4e92484cbed11ebe4ac1efbf8ec837c5?rik=dj71jQgAlPcJdg&riu=http%3a%2f%2fwww.meetboxon.com%2fwp-content%2fuploads%2f2017%2f03%2fARTLAND-Modern-100-Hand-Painted-Flower-Oil-Painting-on-Canvas-Orange-Plum-Blossom-3-Piece-Gallery-Wrapped-Framed-Wall-Art-Ready-to-Hang-for-Living-Room-for-Wall-Decor-Home-Decoration-24x48inches.jpg&ehk=cxZOmWGtuO8xga1dxl2NkG8KG%2fBeE5lCSLT2NAiiKYM%3d&risl=&pid=ImgRaw&r=0",
        ),
        Product(
            name="Guitar",
            description="An acoustic guitar perfect for beginners and experienced players alike.",
            price=200.00,
            stock_quantity=8,
            category="Musical Instruments",
            image_url="https://th.bing.com/th/id/OIP.CGjvoDnANpMyY4_wyZFf8gHaLO?rs=1&pid=ImgDetMain",
        ),
        Product(
            name="Fitness Tracker",
            description="A stylish fitness tracker to monitor your health.",
            price=70.00,
            stock_quantity=30,
            category="Electronics",
            image_url="https://th.bing.com/th/id/OIP.S-3iJDXNyUkeGAAJ4csb6gHaHa?rs=1&pid=ImgDetMain",
        ),
        Product(
            name="Table Lamp",
            description="A modern table lamp to enhance your decor.",
            price=40.00,
            stock_quantity=15,
            category="Home Decor",
            image_url="https://th.bing.com/th/id/OIP.TjnznBlujMM78AmkjHiNEgHaHa?rs=1&pid=ImgDetMain",
        ),
        Product(
            name="Pet Bed",
            description="A cozy bed for your beloved pet.",
            price=60.00,
            stock_quantity=10,
            category="Pets",
            image_url="https://th.bing.com/th/id/OIP.iAk3S__UZNRGBlNkf91d_wHaHa?rs=1&pid=ImgDetMain",
        ),
        Product(
            name="Gardening Tools Set",
            description="A complete set of gardening tools for plant lovers.",
            price=50.00,
            stock_quantity=25,
            category="Gardening",
            image_url="https://th.bing.com/th/id/R.c397f85f973ae33de1d85cf96da8efb5?rik=0Sd63IgmMiEqtA&pid=ImgRaw&r=0",
        ),
        Product(
            name="Wireless Charger",
            description="A convenient wireless charger for your devices.",
            price=30.00,
            stock_quantity=40,
            category="Electronics",
            image_url="https://i5.walmartimages.com/asr/d3eac7fd-22ba-474d-8c86-2441db11e1b1.f6713232f2513fbaaca8925d8812ecf9.jpeg",
        ),
        Product(
            name="Board Game",
            description="A fun board game for family game nights.",
            price=35.00,
            stock_quantity=60,
            category="Toys",
            image_url="https://th.bing.com/th/id/R.2ee4c6ccb7f2f480e7e486385db8b10b?rik=Te5Q1rL8IN4XkQ&pid=ImgRaw&r=0",
        ),
    ]

    # Add all products to the session and commit
    db.session.add_all(products)
    db.session.commit()  # Commit products to ensure they have IDs

    # Retrieve product IDs after committing
    product1 = Product.query.filter_by(name="Vintage Leather Jacket").first()
    product2 = Product.query.filter_by(name="Handmade Silver Necklace").first()
    product3 = Product.query.filter_by(name="Running Shoes").first()
    product4 = Product.query.filter_by(name="Classic White T-Shirt").first()
    product5 = Product.query.filter_by(name="Blue Denim Jeans").first()
    product6 = Product.query.filter_by(name="Leather Backpack").first()
    product7 = Product.query.filter_by(name="Sports Watch").first()
    product8 = Product.query.filter_by(name="Summer Dress").first()
    product9 = Product.query.filter_by(name="Canvas Sneakers").first()
    product10 = Product.query.filter_by(name="Silk Scarf").first()
    product11 = Product.query.filter_by(name="Floral Print Blouse").first()
    product12 = Product.query.filter_by(name="Wool Sweater").first()
    product13 = Product.query.filter_by(name="Classic Sunglasses").first()
    product14 = Product.query.filter_by(name="Leather Wallet").first()
    product15 = Product.query.filter_by(name="Winter Coat").first()
    product16 = Product.query.filter_by(name="Casual Shorts").first()
    product17 = Product.query.filter_by(name="Yoga Mat").first()
    product18 = Product.query.filter_by(name="Bluetooth Headphones").first()
    product19 = Product.query.filter_by(name="Smartphone Stand").first()
    product20 = Product.query.filter_by(name="Cookbook").first()
    product21 = Product.query.filter_by(name="Ceramic Mug").first()
    product22 = Product.query.filter_by(name="Wall Art").first()
    product23 = Product.query.filter_by(name="Guitar").first()
    product24 = Product.query.filter_by(name="Fitness Tracker").first()
    product25 = Product.query.filter_by(name="Table Lamp").first()
    product26 = Product.query.filter_by(name="Pet Bed").first()
    product27 = Product.query.filter_by(name="Gardening Tools Set").first()
    product28 = Product.query.filter_by(name="Wireless Charger").first()
    product29 = Product.query.filter_by(name="Board Game").first()
    
    # Seed Reviews
    review1 = Review(
        product_id=product1.product_id,
        user_id=user1.user_id,
        rating=5,
        review_text="Amazing quality and perfect fit!",
        created_at=datetime.utcnow(),
    )
    review2 = Review(
        product_id=product2.product_id,
        user_id=user2.user_id,
        rating=4,
        review_text="Beautiful necklace, but a bit overpriced.",
        created_at=datetime.utcnow(),
    )
    # Add more reviews as needed, using other products and users
    review3 = Review(
        product_id=product3.product_id,
        user_id=user1.user_id,
        rating=5,
        review_text="These running shoes are super comfortable!",
        created_at=datetime.utcnow(),
    )
    
    db.session.add_all([review1, review2, review3])
    db.session.commit()  # Commit reviews

    # Seed Orders and Order Items
    order1 = Order(
        user_id=user1.user_id,
        total_amount=120.00,
        status="completed",
        shipping_address="123 Main Street, Cityville",
        created_at=datetime.utcnow(),
    )
    order_item1 = OrderItem(
        order=order1,
        product_id=product1.product_id,
        quantity=1,
        price_at_purchase=120.00,
    )
    db.session.add(order1)
    db.session.add(order_item1)

    order2 = Order(
        user_id=user2.user_id,
        total_amount=140.00,
        status="pending",
        shipping_address="456 Maple Avenue, Townsville",
        created_at=datetime.utcnow(),
    )
    order_item2a = OrderItem(
        order=order2,
        product_id=product2.product_id,
        quantity=1,
        price_at_purchase=80.00,
    )
    order_item2b = OrderItem(
        order=order2,
        product_id=product3.product_id,
        quantity=1,
        price_at_purchase=60.00,
    )
    db.session.add(order2)
    db.session.add_all([order_item2a, order_item2b])

    # Commit all orders and order items
    db.session.commit()
    print("Database seeded successfully!")
