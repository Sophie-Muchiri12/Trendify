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

The project has two parts that run side by side:

| Part         | Folder               | Tech                                      | Runs on               |
| ------------ | -------------------- | ----------------------------------------- | --------------------- |
| **Backend**  | `server/`            | Python, Flask, SQLAlchemy, SQLite         | http://127.0.0.1:5000 |
| **Frontend** | `trendify-frontend/` | React 19, Vite, TanStack Router, Tailwind | http://localhost:5173 |

The frontend gets all product data and product photos from the backend, so **both
must be running** to use the shop.

### Prerequisites

Install these once on your machine and check the versions:

| Tool    | Version                     | Check with                                    | Get it from                              |
| ------- | --------------------------- | --------------------------------------------- | ---------------------------------------- |
| Git     | any recent                  | `git --version`                               | https://git-scm.com                      |
| Python  | 3.10 or newer (3.13 tested) | `python3 --version` (Windows: `py --version`) | https://www.python.org/downloads         |
| Node.js | 20.19+ or 22.12+            | `node --version`                              | https://nodejs.org (or `nvm install 22`) |
| npm     | comes with Node             | `npm --version`                               |                                          |

Python must include the `sqlite3` module. Check it with:

```bash
python3 -c "import sqlite3, ctypes; print('ok')"
```

If that prints an error, see [Troubleshooting](#troubleshooting).

### Get the code

```bash
git clone git@github.com:Sophie-Muchiri12/Trendify.git
cd Trendify
```

(No SSH key on GitHub? Use `https://github.com/Sophie-Muchiri12/Trendify.git` instead.)

---

## Backend setup (`server/`)

All backend commands below are run from inside the `server/` folder. `flask`
commands in particular only find the app when you are in that folder.

### Step 1: Go to the backend folder

```bash
cd server
```

### Step 2: Create a virtual environment

A virtual environment (`.venv/`) keeps this project's Python packages separate from
the rest of your system. It is git-ignored, so each person creates their own.

```bash
# macOS / Linux
python3 -m venv .venv

# Windows (PowerShell or Command Prompt)
py -m venv .venv
```

This creates a `server/.venv/` folder. You only do this once per clone.

### Step 3: Activate the virtual environment

Activate it **every time you open a new terminal** for the backend:

```bash
# macOS / Linux
source .venv/bin/activate

# Windows PowerShell
.venv\Scripts\Activate.ps1

# Windows Command Prompt
.venv\Scripts\activate.bat
```

Your prompt now starts with `(.venv)`. While it is active, `python` and `pip` refer
to the project's environment. Run `deactivate` to leave it.

> PowerShell says "running scripts is disabled"? Run
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once, then try again.

### Step 4: Install the Python packages

```bash
pip install -r requirements.txt
```

This installs the exact versions listed in `requirements.txt` (Flask, Flask-SQLAlchemy,
Flask-Migrate, Flask-JWT-Extended, Flask-Cors, Flask-Mail and their dependencies).
It should finish with a line like:

```
Successfully installed Flask-3.0.3 Flask-Cors-5.0.0 Flask-JWT-Extended-4.6.0 ...
```

### Step 5: Create the database with sample data

```bash
python seed.py
```

Expected output:

```
INFO  [alembic.runtime.migration] Running stamp_revision  -> 3b7e1c2d9a41
Database seeded successfully!
```

What this does:

- creates the SQLite database at `server/instance/trendify.db` (git-ignored)
- creates all tables (users, products, reviews, orders, order items)
- loads the 22 products from `server/catalog.py`, plus 3 sample users, 6 reviews
  and 2 orders
- records the current migration version, so `flask db upgrade` works later

> ⚠️ `seed.py` **deletes and recreates every table** each time you run it, which
> wipes any users, orders or reviews you created. Run it on first setup, or when you
> deliberately want a fresh database.

### Step 6 (optional): Set a secret key

The backend signs login tokens (JWTs) with `SECRET_KEY`. Without it, a built-in
development key is used, which is fine on your own machine. **Set a real one on
any shared or deployed server.**

Generate one:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Set it in the terminal before starting the server:

```bash
# macOS / Linux
export SECRET_KEY="paste-the-value-here"

# Windows PowerShell
$env:SECRET_KEY = "paste-the-value-here"
```

Changing the key logs everyone out, because existing tokens stop being valid.

### Step 7: Start the backend

```bash
python app.py
```

Expected output:

```
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://127.0.0.1:5000
 * Debugger is active!
```

Leave this terminal open. The server is in debug mode, so it **reloads
automatically** when you save a Python file. Press `Ctrl+C` to stop it.

### Step 8: Check it works

Open http://127.0.0.1:5000/products in a browser, or run:

```bash
curl http://127.0.0.1:5000/products
```

You should get a JSON list of 22 products. Opening http://127.0.0.1:5000/ itself
returns "404 Not Found". That is expected, because the API has no home page.

Product photos are served from `server/static/products/`, for example
http://127.0.0.1:5000/static/products/p-sneaker1.jpg.

### Sample accounts

`seed.py` creates these users (passwords are for local development only):

| Email             | Password       | Role |
| ----------------- | -------------- | ---- |
| john@example.com  | password123    | user |
| jane@example.com  | securepassword | user |
| admin@example.com | adminpassword  | user |

Despite its name, the seeded `admin@example.com` has the normal `user` role. To get
an admin account, create one with `POST /register-admin`.

Log in to get a token:

```bash
curl -X POST http://127.0.0.1:5000/login \
  -H "Content-Type: application/json" \
  -d '{"email": "john@example.com", "password": "password123"}'
```

The response contains an `access_token`. Send it as `Authorization: Bearer <token>`
on endpoints that need a login.

### Main API endpoints

| Method | Path                     | Auth  | Description                              |
| ------ | ------------------------ | ----- | ---------------------------------------- |
| POST   | `/register`              | none  | Create a user account                    |
| POST   | `/login`                 | none  | Log in, returns a JWT                    |
| GET    | `/products`              | none  | List all products                        |
| GET    | `/products/<id>`         | none  | One product by numeric ID                |
| GET    | `/products/<slug>`       | none  | One product by slug, e.g. `kilim-runner` |
| POST   | `/products`              | admin | Add a product                            |
| PUT    | `/products/<id>`         | admin | Update a product                         |
| DELETE | `/products/<id>`         | admin | Delete a product                         |
| GET    | `/products/<id>/reviews` | none  | Reviews for a product                    |
| POST   | `/orders`                | login | Place an order                           |
| GET    | `/orders`                | login | List your orders                         |

See `server/routes.py` for the full list.

### Database migrations

Schema changes are tracked with Flask-Migrate (Alembic) in `server/migrations/`.
With the virtual environment active, from `server/` (Flask finds the app in
`app.py` automatically):

```bash
flask db upgrade                      # apply new migrations (keeps your data)
flask db migrate -m "describe change" # after editing a model: generate a migration
flask db current                      # show which migration the database is on
```

Check a generated migration file before you commit it, and commit it together with
the model change.

### Changing the product catalog

1. Add or edit an entry in `server/catalog.py`. `slug` must be unique; it becomes
   the product URL (`/product/<slug>`) and the ID the cart stores.
2. Put the photo in `server/static/products/` as a square JPG (816 × 816 matches
   the others) and reference it with `img("file-name-without-extension")`.
3. Note where the photo came from in `server/static/image-sources.json`.
4. Run `python seed.py` to reload the database. This also resets users and orders.

---

## Frontend setup (`trendify-frontend/`)

Open a **second terminal**. The backend keeps running in the first one.

### Step 1: Go to the frontend folder

From the project root:

```bash
cd trendify-frontend
```

### Step 2: Install the packages

```bash
npm install
```

This reads `package.json` and `package-lock.json` and downloads everything into
`node_modules/` (git-ignored). It takes a minute the first time.

npm may print "N vulnerabilities" at the end. These are in development-only tools
(Vite, Vitest), not in the code that ships to users. **Do not run
`npm audit fix --force`**: it can install incompatible major versions and break the
build.

### Step 3: Start the development server

Make sure the backend is running (Backend step 7), then:

```bash
npm run dev
```

Expected output:

```
  VITE v8.1.5  ready in 900 ms

  ➜  Local:   http://localhost:5173/
```

Open **http://localhost:5173**. The page updates instantly when you save a file.
Press `Ctrl+C` to stop the server.

### Step 4: Check it works

- The home page shows a "Best sellers" row with product photos.
- **Shop all** lists 22 products, and the category buttons filter them.
- Clicking a product opens its page with sizes, price and "You may also like".
- Adding something to the cart updates the cart counter in the header.

If you see **"Something went wrong: Could not load products"**, the frontend can't
reach the backend. Start it (or seed it), then click **Try again**.

### How the frontend talks to the backend

In development, the Vite dev server forwards two kinds of request to Flask (see
`vite.config.ts`):

| Browser requests         | Forwarded to                                  |
| ------------------------ | --------------------------------------------- |
| `/api/products`          | `http://127.0.0.1:5000/products`              |
| `/static/products/x.jpg` | `http://127.0.0.1:5000/static/products/x.jpg` |

The code calls `/api/...` (see `src/lib/products.ts`), so no API address or CORS
setup is needed while you develop. The cart and wishlist are stored in the
browser's `localStorage`.

To use a different API (for example a deployed backend), create
`trendify-frontend/.env.local` (git-ignored):

```bash
VITE_API_URL=https://your-api.example.com
```

Restart `npm run dev` after creating or changing `.env.local`.

### Frontend commands

Run these from `trendify-frontend/`:

| Command              | What it does                                          |
| -------------------- | ----------------------------------------------------- |
| `npm run dev`        | Start the dev server on http://localhost:5173         |
| `npm test`           | Run the tests once (Vitest)                           |
| `npm run test:watch` | Rerun tests on every save                             |
| `npm run lint`       | Check code style with ESLint and Prettier             |
| `npm run format`     | Reformat every file with Prettier                     |
| `npm run build`      | Build the production site into `dist/` and type-check |
| `npm run preview`    | Serve the `dist/` build locally to try it             |

`src/routeTree.gen.ts` is generated from the files in `src/routes/` whenever the dev
server, build or tests run. Don't edit it by hand. Commit it when it changes.

For a full tour of the frontend code, see
[`trendify-frontend/README.md`](trendify-frontend/README.md).

---

## Day-to-day: running the app again

Once setup is done, starting work only takes two terminals:

```bash
# Terminal 1: backend
cd server
source .venv/bin/activate      # Windows: .venv\Scripts\Activate.ps1
python app.py
```

```bash
# Terminal 2: frontend
cd trendify-frontend
npm run dev
```

## After pulling new changes

Each time you `git pull`, other people may have added packages or changed the
database. Bring your setup up to date:

```bash
# Backend
cd server
source .venv/bin/activate      # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
flask db upgrade
cd ..

# Frontend
cd trendify-frontend
npm install
cd ..
```

Then restart both servers.

- `pip install` and `npm install` add or update only the packages that changed.
- `flask db upgrade` applies new migrations and **keeps your existing data**.
- If the **product catalog** changed (`server/catalog.py` or new photos), also run
  `python seed.py` in `server/`. This resets the database, so copy
  `server/instance/trendify.db` first if you need to keep anything.

## Project layout

```
server/                   Flask API
  app.py                  App factory and dev-server entry point
  config.py               Settings (SECRET_KEY, database location)
  routes.py               API endpoints: auth, users, products, reviews, orders
  models/                 SQLAlchemy models (one file per table)
  catalog.py              Storefront products used by seed.py
  seed.py                 Resets the database with sample data
  migrations/             Alembic migrations (Flask-Migrate)
  static/products/        Product photos, served at /static/products/
  static/image-sources.json  Where each photo came from (CC0 / public domain)
  requirements.txt        Pinned Python packages
  instance/trendify.db    SQLite database (created by seed.py, git-ignored)
trendify-frontend/        React storefront
  src/routes/             One file per page (file-based routing)
  src/lib/products.ts     Fetches products from the API
  src/lib/cart.tsx        Cart and wishlist (localStorage)
  vite.config.ts          Dev server and the proxy to the backend
```

## Troubleshooting

| Problem                                                                 | Cause and fix                                                                                                                                                                                                                                                                             |
| ----------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Shop shows **"Could not load products"**                                | The backend isn't running or isn't seeded. Start `python app.py` in `server/` (venv active), run `python seed.py` if you never have, then click **Try again**.                                                                                                                            |
| `ModuleNotFoundError: No module named 'flask'`                          | The virtual environment isn't active. Run `source .venv/bin/activate` (Windows: `.venv\Scripts\Activate.ps1`) in `server/`.                                                                                                                                                               |
| `No module named '_sqlite3'` or `'_ctypes'`                             | Your Python was built without those modules (common with some pyenv builds). Delete `server/.venv` and recreate it with a different Python, e.g. `/usr/bin/python3 -m venv .venv`, then reinstall.                                                                                        |
| `no such column: products.slug` (or another missing column)             | Your database is behind the code. Run `flask db upgrade` (see "After pulling new changes").                                                                                                                                                                                               |
| `Error: No such command 'db'` or `Could not locate a Flask application` | You ran `flask` outside `server/`. `cd server` first (with the venv active).                                                                                                                                                                                                              |
| `Address already in use` (port 5000 or 5173)                            | Another copy is already running; stop it. On macOS, AirPlay Receiver also uses port 5000: turn it off in System Settings → General → AirDrop & Handoff. For the frontend you can use `npm run dev -- --port 5174`.                                                                        |
| `npm run dev` fails with a Node version error                           | Vite needs Node 20.19+ or 22.12+. Check `node --version` and upgrade.                                                                                                                                                                                                                     |
| Products load but **photos are broken**                                 | Check the photo opens directly, e.g. http://127.0.0.1:5000/static/products/p-sneaker1.jpg. If it 404s, the file is missing from `server/static/products/`: pull the latest code. If it works there but not in the shop, restart `npm run dev` so the proxy in `vite.config.ts` is loaded. |
| Login stopped working after changing `SECRET_KEY`                       | Expected: old tokens are no longer valid. Log in again.                                                                                                                                                                                                                                   |
