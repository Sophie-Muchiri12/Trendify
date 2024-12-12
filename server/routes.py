# routes.py
from flask import Blueprint, request, jsonify, make_response
from models import db, User, Product, Review, Order, OrderItem
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity

# Initialize Blueprint
routes = Blueprint('routes', __name__)

# Initialize JWT Manager
jwt = JWTManager()

# CORS CONFIGURATIONS
def _build_cors_prelight_response():
    response = make_response()
    response.headers.add("Access-Control-Allow-Origin", "http://localhost:3000")  # Allow requests from React app
    response.headers.add("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type, Authorization")
    response.headers.add("Access-Control-Allow-Credentials", "true")
    return response

# Error response function
def error_response(message, status_code):
    return jsonify({"error": message}), status_code

# Admin authorization decorator
def admin_required(f):
    @wraps(f)
    @jwt_required()  # Require a valid JWT to access this route
    def decorated_function(*args, **kwargs):
        user_id = get_jwt_identity()  # Get the current user's ID from the JWT
        current_app.logger.debug(f"User ID from token: {user_id}")
        user = User.query.get(user_id)
        if not user:
            current_app.logger.warning(f"User not found for ID: {user_id}")
            return jsonify({"message": "User not found"}), 403
        if not user.is_admin():
            current_app.logger.warning(f"User ID {user_id} is not an admin")
            return jsonify({"message": "Admin access required"}), 403
        return f(*args, **kwargs)
    return decorated_function

# Admin Registration Route
@routes.route('/register-admin', methods=['POST'])
def register_admin():
    data = request.get_json()
    required_fields = ['name', 'email', 'password', 'phone_number']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"{field} is required"}), 400

    if User.query.filter_by(email=data['email']).first():
        return jsonify({"message": "Admin already exists"}), 400

    hashed_password = generate_password_hash(data['password'])
    admin_user = User(
        name=data['name'],
        email=data['email'],
        phone_number=data['phone_number'],
        password_hash=hashed_password,
        role='admin'  # Ensure 'admin' role is set correctly in your User model
    )
    db.session.add(admin_user)
    db.session.commit()

    return jsonify({"message": "Admin registered successfully"}), 201

# User Registration Route
@routes.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data or not isinstance(data, dict):
        return error_response("Invalid data format", 400)

    required_fields = ['name', 'email', 'password', 'phone_number']
    missing_fields = [field for field in required_fields if field not in data]
    
    if missing_fields:
        return error_response(f"Missing fields: {', '.join(missing_fields)}", 400)

    if User.query.filter_by(email=data['email']).first():
        return error_response("User already exists", 400)

    user = User(
        name=data['name'],
        email=data['email'],
        phone_number=data['phone_number'],
        role='user'  # Default role for normal users
    )
    user.set_password(data['password'])  # Use set_password to hash the password
    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "User registered successfully"}), 201

# User Login Route
@routes.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or not isinstance(data, dict):
        return error_response("Invalid data format", 400)

    email = data.get('email')
    password = data.get('password')

    # Check for missing fields
    if not email or not password:
        return error_response("Email and password are required", 400)

    user = User.query.filter_by(email=email).first()
    
    if user and user.check_password(password):  # Use the method defined in your User model
        # Create JWT token using the correct user ID attribute
        access_token = create_access_token(identity=user.user_id)  # Correctly reference user_id
        return jsonify({"message": "Login successful", "access_token": access_token, "role": user.role}), 200

    return error_response("Invalid credentials", 401)

# Retrieve All Users (Admin Only)
@routes.route('/users', methods=['GET'])
@admin_required
def get_all_users():
    current_app.logger.debug(f"Request headers: {request.headers}")
    
    # Get the user ID from the JWT token
    user_id = get_jwt_identity()
    current_app.logger.debug(f"User ID from token: {user_id}")
    users = User.query.all()
    return jsonify([{
        "user_id": user.user_id,
        "name": user.name,
        "email": user.email,
        "phone_number": user.phone_number,
        "role": user.role
    } for user in users]), 200

# Update User Role (Admin Only)
@routes.route('/users/<int:user_id>/role', methods=['PATCH'])
@admin_required
def update_user_role(user_id):
    data = request.get_json()
    user = User.query.get(user_id)
    if not user:
        return error_response("User not found", 404)

    new_role = data.get('role')
    if new_role not in ['user', 'admin']:
        return error_response("Invalid role", 400)

    user.role = new_role
    db.session.commit()
    return jsonify({"message": "User role updated successfully"}), 200

# Retrieve All Products
@routes.route('/products', methods=['GET'])
def get_products():
    products = Product.query.all()
    return jsonify([{
        "product_id": p.product_id,
        "name": p.name,
        "description": p.description,
        "price": float(p.price),
        "stock_quantity": p.stock_quantity,
        "category": p.category,
        "image_url": p.image_url
    } for p in products]), 200

# Retrieve Single Product
@routes.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    product = Product.query.get(product_id)
    if not product:
        return error_response("Product not found", 404)
    return jsonify({
        "product_id": product.product_id,
        "name": product.name,
        "description": product.description,
        "price": float(product.price),
        "stock_quantity": product.stock_quantity,
        "category": product.category,
        "image_url": product.image_url
    }), 200

# Add New Product (Admin Only)
@routes.route('/products', methods=['POST'])
@admin_required
def add_product():
    data = request.get_json()
    required_fields = ['name', 'description', 'price', 'stock_quantity', 'category']
    
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return error_response(f"Missing fields: {', '.join(missing_fields)}", 400)

    product = Product(
        name=data['name'],
        description=data['description'],
        price=data['price'],
        stock_quantity=data['stock_quantity'],
        category=data['category'],
        image_url=data.get('image_url')
    )
    db.session.add(product)
    db.session.commit()
    return jsonify({"message": "Product added successfully"}), 201

# Update Product (Admin Only)
@routes.route('/products/<int:product_id>', methods=['PUT'])
@admin_required
def update_product(product_id):
    data = request.get_json()
    product = Product.query.get(product_id)
    if not product:
        return error_response("Product not found", 404)

    product.name = data.get('name', product.name)
    product.description = data.get('description', product.description)
    product.price = data.get('price', product.price)
    product.stock_quantity = data.get('stock_quantity', product.stock_quantity)
    product.category = data.get('category', product.category)
    product.image_url = data.get('image_url', product.image_url)
    db.session.commit()
    return jsonify({"message": "Product updated successfully"}), 200

# Delete Product (Admin Only)
@routes.route('/products/<int:product_id>', methods=['DELETE'])
@admin_required
def delete_product(product_id):
    product = Product.query.get(product_id)
    if not product:
        return error_response("Product not found", 404)
    db.session.delete(product)
    db.session.commit()
    return jsonify({"message": "Product deleted successfully"}), 200

# Create Review for a Product
@routes.route('/products/<int:product_id>/reviews', methods=['POST'])
def add_review(product_id):
    data = request.get_json()
    user_id = data.get('user_id')

    # Check if the user exists
    user = User.query.get(user_id)
    if not user:
        return error_response("User not found", 404)

    required_fields = ['rating']
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return error_response(f"Missing fields: {', '.join(missing_fields)}", 400)

    review = Review(
        product_id=product_id,
        user_id=user_id,
        rating=data['rating'],
        review_text=data.get('review_text'),
        status='pending'  # Default status for new reviews
    )
    db.session.add(review)
    db.session.commit()
    return jsonify({"message": "Review added successfully"}), 201

# View Reviews for a Product
@routes.route('/products/<int:product_id>/reviews', methods=['GET'])
def get_reviews(product_id):
    reviews = Review.query.filter_by(product_id=product_id).all()
    return jsonify([{
        "review_id": r.review_id,
        "user_id": r.user_id,
        "rating": r.rating,
        "review_text": r.review_text,
        "status": r.status
    } for r in reviews]), 200

# Approve Review (Admin Only)
@routes.route('/reviews/<int:review_id>/approve', methods=['PATCH'])
@admin_required
def approve_review(review_id):
    review = Review.query.get(review_id)
    if not review:
        return error_response("Review not found", 404)

    review.status = 'approved'
    db.session.commit()
    return jsonify({"message": "Review approved successfully"}), 200

# Reject Review (Admin Only)
@routes.route('/reviews/<int:review_id>/reject', methods=['PATCH'])
@admin_required
def reject_review(review_id):
    review = Review.query.get(review_id)
    if not review:
        return error_response("Review not found", 404)

    review.status = 'rejected'
    db.session.commit()
    return jsonify({"message": "Review rejected successfully"}), 200
from flask import current_app

@routes.route('/orders', methods=['POST'])
@jwt_required()
def place_order():
    # Log the incoming request headers for debugging
    current_app.logger.debug(f"Request headers: {request.headers}")
    
    # Get the user ID from the JWT token
    user_id = get_jwt_identity()
    current_app.logger.debug(f"User ID from token: {user_id}")
    
    if not user_id:
        return jsonify({"error": "User authentication failed"}), 401

    data = request.get_json()

    # Check for 'items' and 'shipping_address' in request data
    if not data or 'items' not in data or 'shipping_address' not in data:
        return jsonify({"error": "Items and shipping address are required"}), 400

    items = data['items']
    shipping_address = data['shipping_address']

    # Validate 'items' format
    if not isinstance(items, list) or any(not isinstance(item, dict) for item in items):
        return jsonify({"error": "Items should be a list of objects with 'product_id' and 'quantity'"}), 400

    # Create a new order
    order = Order(user_id=user_id, shipping_address=shipping_address)
    db.session.add(order)

    total_price = 0
    for item in items:
        product_id = item.get('product_id')
        quantity = item.get('quantity')

        if product_id is None or quantity is None:
            return jsonify({"error": "Each item must have 'product_id' and 'quantity'"}), 400

        # Retrieve product
        product = Product.query.get(product_id)
        if not product:
            return jsonify({"error": f"Product with ID {product_id} does not exist"}), 400

        if product.stock_quantity < quantity:
            return jsonify({"error": f"Insufficient stock for product ID {product_id}"}), 400

        # Calculate item price and update total
        item_total_price = product.price * quantity
        total_price += item_total_price

        order_item = OrderItem(
            order=order,
            product=product,
            quantity=quantity,
            price_at_purchase=product.price
        )
        db.session.add(order_item)

        # Update product stock
        product.stock_quantity -= quantity

    # Set order total amount and commit
    order.total_amount = total_price
    db.session.commit()

    current_app.logger.info(f"Order placed successfully for user {user_id} with order ID {order.order_id}")
    return jsonify({"message": "Order placed successfully", "order_id": order.order_id}), 201

# Retrieve User Orders
@routes.route('/orders', methods=['GET'])
@jwt_required()
def get_orders():
    user_id = get_jwt_identity()  # Get the ID of the logged-in user
    orders = Order.query.filter_by(user_id=user_id).all()
    return jsonify([{
        "order_id": order.order_id,
        "total_price": float(order.total_price),
        "status": order.status,
        "items": [{
            "product_id": item.product_id,
            "quantity": item.quantity
        } for item in order.order_items]
    } for order in orders]), 200

