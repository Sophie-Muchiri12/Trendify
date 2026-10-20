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

## Getting started

### Prerequisites

- **Python 3.10+** with the `sqlite3` module (the system Python on most Linux/macOS
  machines works; some pyenv builds are missing it, see Troubleshooting)
- **Node.js 20+** and npm
- Git

### 1. First-time setup (after cloning)

```bash
git clone git@github.com:Sophie-Muchiri12/Trendify.git
cd Trendify
```

**Backend** (Flask API in `server/`)

```bash
cd server
python3 -m venv .venv                     # Windows: py -m venv .venv
.venv/bin/pip install -r requirements.txt # Windows: .venv\Scripts\pip install -r requirements.txt
.venv/bin/python seed.py                  # creates instance/trendify.db with sample data
cd ..
```

**Frontend** (React storefront in `trendify-frontend/`)

```bash
cd trendify-frontend
npm install
cd ..
```

The database, the virtual environment and `node_modules` are not stored in git, so
every new clone needs these steps once.

### 2. Run the app

Use two terminals and start the backend first. The storefront loads its products
from it.

```bash
# Terminal 1: API on http://127.0.0.1:5000
cd server
.venv/bin/python app.py
```

```bash
# Terminal 2: storefront on http://localhost:5173
cd trendify-frontend
npm run dev
```

Open **http://localhost:5173**. In development Vite forwards `/api/*` and
`/static/*` to the Flask server, so you don't need to configure CORS or a URL.

Quick check that the API is up: http://127.0.0.1:5000/products should return JSON.

### 3. After pulling new changes

Each time you `git pull`, bring your local setup up to date:

```bash
# Backend: new packages and database migrations
cd server
.venv/bin/pip install -r requirements.txt
FLASK_APP=app:create_app .venv/bin/flask db upgrade
cd ..

# Frontend: new packages
cd trendify-frontend
npm install
cd ..
```

Then restart both servers. `flask db upgrade` keeps the data you already have and
only adds new tables or columns.

If the **product catalog** changed (`server/catalog.py` or new images in
`server/static/products/`), reseed to load it:

```bash
cd server
.venv/bin/python seed.py
```

> ⚠️ `seed.py` drops and recreates **every** table, which wipes users, orders and
> reviews you created locally. Copy `server/instance/trendify.db` first if you
> want to keep them.

### Sample accounts

`seed.py` creates these users (passwords are for local development only):

| Email               | Password         |
| ------------------- | ---------------- |
| john@example.com    | password123      |
| jane@example.com    | securepassword   |
| admin@example.com   | adminpassword    |

All three have the `user` role. Admin-only endpoints need an account created with
`POST /register-admin`.

### Configuration

| Variable       | Where     | Default                 | Notes                                          |
| -------------- | --------- | ----------------------- | ---------------------------------------------- |
| `SECRET_KEY`   | backend   | `dev-only-insecure-key` | Signs sessions and JWTs. Set it outside local dev. |
| `VITE_API_URL` | frontend  | `/api` (dev proxy)      | API base URL for a deployed frontend build.    |

### Useful commands

| Where               | Command                                               | What it does                     |
| ------------------- | ----------------------------------------------------- | -------------------------------- |
| `server/`           | `.venv/bin/python seed.py`                            | Reset the database with sample data |
| `server/`           | `FLASK_APP=app:create_app .venv/bin/flask db upgrade` | Apply database migrations        |
| `trendify-frontend/`| `npm test`                                            | Run the frontend tests           |
| `trendify-frontend/`| `npm run lint`                                        | Lint and check formatting        |
| `trendify-frontend/`| `npm run build`                                       | Type-check and build to `dist/`  |

### Project layout

```
server/                 Flask API
  app.py                App factory and dev server entry point
  routes.py             API endpoints (auth, users, products, reviews, orders)
  models/               SQLAlchemy models
  catalog.py            Storefront products used by seed.py
  seed.py               Resets the database with sample data
  migrations/           Alembic migrations (Flask-Migrate)
  static/products/      Product photos, served at /static/products/
trendify-frontend/      React 19 + Vite + TanStack Router storefront
```

Product photos are CC0 / public domain. Their sources are listed in
`server/static/image-sources.json`.

### Troubleshooting

- **The storefront shows "Something went wrong / Could not load products"**: the
  backend isn't running (start `python app.py` in `server/`) or the database hasn't
  been seeded (run `seed.py`). Then click **Try again**.
- **`ModuleNotFoundError: No module named '_sqlite3'` (or `_ctypes`)**: your Python
  was built without those modules, which happens with some pyenv builds. Delete
  `server/.venv` and recreate it with another Python, e.g. `/usr/bin/python3 -m venv .venv`.
- **`no such column: products.slug`** (or a similar missing column): your database is
  behind the code. Run `flask db upgrade` as shown in step 3.
- **`Address already in use` on port 5000 or 5173**: another copy is already running.
  Stop it, or for the frontend use `npm run dev -- --port 5174`.
