# Trendify-Shopping-Website
Trendify is a modern e-commerce platform designed to deliver a
personalized and trend-focused shopping experience. 

Our app curates trending items from multiple categories, allowing users to
effortlessly find, review, and purchase what's popular right now. 

By integrating user reviews, seamless checkout, and order tracking,
Trendify offers a complete shopping experience that is intuitive and
reliable.

Target Audience:

Trendify is tailored to trend-conscious consumers who want quick
access to the latest products. 

Whether you're looking for the newest fashion, tech gadgets, or home decor, Trendify will serve as a
one-stop shop for users who prioritize staying on top of trends.

Key Features:
1. User Authentication: Users can create accounts and log in
securely, with the option to use social media for faster access.

2. Product Search and Filter: Advanced search and filtering
options allow users to find products by category, price range,
rating, and more.

3. Shopping Cart and Checkout: Customers can add items to
their cart, modify quantities, and seamlessly complete purchases
with integrated payment options like PayPal or Stripe.

4. Order Tracking: After placing an order, users can track their
delivery status and receive notifications at key points during
shipping.

5. Reviews and Ratings: Users can provide feedback on
purchases, helping other shoppers make informed decisions.

## Running locally

**Backend** (Flask, http://127.0.0.1:5000)

```bash
cd server
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python seed.py   # (re)creates instance/trendify.db with the catalog in catalog.py
.venv/bin/python app.py
```

Set `SECRET_KEY` in the environment for anything other than local development.
Product photos live in `server/static/products/`; their sources (all CC0 / public
domain) are listed in `server/static/image-sources.json`.

**Frontend** (React + Vite, http://localhost:5173)

```bash
cd trendify-frontend
npm install
npm run dev
```
