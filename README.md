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

1. User Authentication: Users can create accounts, verify their email and log in
   securely, with optional two-factor authentication.

2. Product Search and Filter: Advanced search and filtering
   options allow users to find products by category, price range,
   rating, and more.

3. Shopping Cart and Checkout: Customers can add items to
   their cart, modify quantities, and seamlessly complete purchases
   with Pesapal (card, M-Pesa and Airtel Money).

4. Order Tracking: After placing an order, users can track their
   delivery status and receive notifications at key points during
   shipping.

5. Reviews and Ratings: Users can provide feedback on
   purchases, helping other shoppers make informed decisions.

6. Administration: Administrators manage products, orders, users and reviews, and can
   inspect a tamper-evident audit log.

## Security

Trendify applies the **OWASP Top 10:2025**: role-based access control, Argon2 password
hashing, HttpOnly session cookies with CSRF protection, rate limiting and account
lockout, email verification, two-factor authentication, strict input validation,
security headers and CSP, server-side pricing, verified Pesapal payments, hash-locked
dependencies with automated scanning, a hash-chained audit log with alerts, and safe
error handling. **[SECURITY.md](SECURITY.md)** maps every measure to the code that
implements it and the test that proves it.

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
pip install -r requirements-dev.txt
```

`requirements-dev.txt` installs the app's packages plus the test and audit tools
(pytest, pip-audit, pip-tools). On a server that only runs the app, use
`pip install -r requirements.txt`.

`requirements.txt` pins every package, including indirect ones, **with a SHA-256
hash**. pip checks each download against its hash and refuses anything that doesn't
match, which protects against tampered packages. To add or upgrade a package, edit
`requirements.in` and regenerate the locked file:

```bash
pip-compile --generate-hashes --strip-extras --allow-unsafe requirements.in
pip-compile --generate-hashes --strip-extras --allow-unsafe -o requirements-dev.txt requirements-dev.in
```

### Step 5: Create the database with sample data

```bash
python seed.py
```

Expected output (your passwords will be different):

```
Database seeded successfully!

Demo accounts (shown only now; run seed.py again or use 'Forgot password' to reset):
  admin     admin@example.com    QH018dvqxwgZAEhm
  customer  john@example.com     uFSnbQxmRPh0kSHX
  customer  jane@example.com     V67EPEcuWcAiIoK8
```

**Copy these passwords now.** There are no built-in default passwords: each run
generates new random ones. For a class demo where everyone needs the same login, set
`SEED_PASSWORD` first (it must meet the password rules):

```bash
SEED_PASSWORD="Demo-Password-2026" python seed.py   # Windows: $env:SEED_PASSWORD="..."; python seed.py
```

What this does:

- creates the SQLite database at `server/instance/trendify.db` (git-ignored)
- creates all tables (users, products, reviews, orders, audit log, …)
- loads the 22 products from `server/catalog.py`, an admin and two customers (all
  with verified emails), 6 approved reviews and 3 orders
- records the current migration version, so `flask db upgrade` works later

> ⚠️ `seed.py` **deletes and recreates every table** each time you run it, which
> wipes any users, orders or reviews you created. Run it on first setup, or when you
> deliberately want a fresh database. It refuses to run when `APP_ENV=production`.

To create an administrator without reseeding (for example on a real server):

```bash
flask create-admin --email you@example.com --name "Your Name"
```

It asks for a password twice. There is deliberately no web endpoint for this.

### Step 6: Settings (optional for local development)

The backend reads its settings from environment variables. **Nothing needs to be
set for local development**: the development profile uses safe defaults, sends no
real email and uses a payment simulator. `server/.env.example` lists every setting.

The ones you're most likely to want:

| Variable                                                         | What it's for                                                          |
| ---------------------------------------------------------------- | ---------------------------------------------------------------------- |
| `SECRET_KEY`                                                     | Signs login tokens. Required (32+ random characters) in production.    |
| `ENCRYPTION_KEY`                                                 | Encrypts two-factor secrets in the database. Required in production.   |
| `PAYMENT_PROVIDER`                                               | `simulated` (development default) or `pesapal`.                        |
| `PESAPAL_CONSUMER_KEY`, `PESAPAL_CONSUMER_SECRET`, `PESAPAL_ENV` | Your Pesapal sandbox or live credentials.                              |
| `MAIL_SERVER`, `MAIL_USERNAME`, `MAIL_PASSWORD`                  | Send real emails. Without them, emails are saved as files (see below). |
| `SECURITY_ALERT_EMAIL`                                           | Where security alerts are emailed.                                     |

Generate the two keys with:

```bash
python -c "import secrets; print(secrets.token_hex(32))"                                  # SECRET_KEY
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"  # ENCRYPTION_KEY
```

Set a variable in the terminal before starting the server:

```bash
# macOS / Linux
export SECRET_KEY="paste-the-value-here"

# Windows PowerShell
$env:SECRET_KEY = "paste-the-value-here"
```

Never commit real values. `.env` files are git-ignored. Changing `SECRET_KEY` signs
everyone out.

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

Leave this terminal open. In development the server **reloads automatically** when you
save a Python file. Press `Ctrl+C` to stop it. Debug mode is only on in the development
profile; with `APP_ENV=production` it's always off.

### Step 8: Check it works

Open http://127.0.0.1:5000/products in a browser, or run:

```bash
curl http://127.0.0.1:5000/products
```

You should get JSON with an `items` list of 22 products. Opening
http://127.0.0.1:5000/ itself returns `{"error": "Not found."}`. That is expected,
because the API has no home page. http://127.0.0.1:5000/health returns
`{"status": "ok"}`.

### Emails in development

Sign-up verification links, password-reset links and security notices are emailed.
Without `MAIL_SERVER` set, each email is **saved as a file** in
`server/instance/outbox/` instead. Open the newest `.eml` file in a text editor (or
your mail app) and copy the link into your browser.

### Payments

Checkout uses **Pesapal** (card, M-Pesa, Airtel Money). Trendify never sees card details:
customers pay on Pesapal's own page, and the server confirms every payment with
Pesapal's API before marking an order paid.

- **Development (default):** `PAYMENT_PROVIDER=simulated`. After "Place order and pay",
  a simulator page lets you choose a successful or failed payment. No money moves.
- **Pesapal sandbox:** create a sandbox account at https://developer.pesapal.com, then
  set `PAYMENT_PROVIDER=pesapal`, `PESAPAL_ENV=sandbox`, `PESAPAL_CONSUMER_KEY` and
  `PESAPAL_CONSUMER_SECRET`. Pesapal must be able to reach `API_PUBLIC_URL` for payment
  notifications, so on your own machine expose it with a tunnel (for example
  `ngrok http 5173`) and set `API_PUBLIC_URL=https://<your-tunnel>/api` and
  `FRONTEND_URL=https://<your-tunnel>`.

### Run the backend tests

```bash
python -m pytest -q
```

About 100 tests run in around 30 seconds. They cover sign-up, login, sessions, access
control, orders, payments, reviews, the admin API and the security controls (see
[SECURITY.md](SECURITY.md)). They use a temporary in-memory database, so your data isn't
touched.

Check the locked packages for known vulnerabilities with:

```bash
pip-audit -r requirements.txt --require-hashes --disable-pip
```

### Accounts and roles

There are two roles:

- **customer**: browse, buy, track orders, review products they bought, manage their
  account. Ordering and reviewing need a verified email.
- **admin**: everything above, plus the **Admin** area (header menu → Admin):
  dashboard, products (create, edit, archive, photo upload), orders (status updates and
  refunds), users (roles, deactivation, unlocking), review moderation and the audit log.

Security behaviour you'll notice while testing:

- 5 wrong passwords lock an account for 15 minutes (an admin can unlock it under
  Admin → Users).
- Too many requests return "Too many requests" (HTTP 429) for a short while.
- Changing your password or clicking "Sign out everywhere" signs out all other devices.
- Two-factor authentication can be turned on under Account → Two-factor
  authentication, using any authenticator app.

### Main API endpoints

The browser keeps the session in secure cookies. To call the API from the command line,
use a cookie jar and send the `csrf_access_token` cookie back in an `X-CSRF-TOKEN` header
on every POST/PATCH/DELETE:

```bash
curl -c jar -H "Content-Type: application/json" \
  -d '{"email": "john@example.com", "password": "<password from seed.py>"}' \
  http://127.0.0.1:5000/auth/login
curl -b jar http://127.0.0.1:5000/orders
```

| Method             | Path                                                | Who                     | Description                                            |
| ------------------ | --------------------------------------------------- | ----------------------- | ------------------------------------------------------ |
| POST               | `/auth/register`                                    | anyone                  | Create a customer account (sends a verification email) |
| POST               | `/auth/login`                                       | anyone                  | Sign in (sets session cookies; add `otp` if 2FA is on) |
| POST               | `/auth/logout`, `/auth/logout-all`                  | signed in               | Sign out here / everywhere                             |
| POST               | `/auth/refresh`                                     | signed in               | Renew the short-lived access cookie                    |
| GET                | `/auth/me`                                          | anyone                  | The signed-in user, or `null`                          |
| POST               | `/auth/verify-email`, `/auth/resend-verification`   |                         | Email verification                                     |
| POST               | `/auth/forgot-password`, `/auth/reset-password`     | anyone                  | Password reset                                         |
| GET, PATCH, DELETE | `/account`                                          | signed in               | View, update or close your account                     |
| POST               | `/account/change-password`                          | signed in               | Change password                                        |
| POST               | `/account/mfa/setup`, `/mfa/enable`, `/mfa/disable` | signed in               | Two-factor authentication                              |
| GET                | `/products?q=&category=&sort=&page=`                | anyone                  | Search and list products                               |
| GET                | `/products/<slug>`                                  | anyone                  | One product                                            |
| GET, POST          | `/products/<slug>/reviews`                          | anyone / verified buyer | Read or write reviews                                  |
| PATCH, DELETE      | `/reviews/<id>`                                     | review owner            | Edit or delete your review                             |
| POST, GET          | `/orders`                                           | verified / signed in    | Place an order, or list yours                          |
| GET                | `/orders/<reference>`                               | order owner             | One of your orders                                     |
| POST               | `/orders/<reference>/cancel`, `/pay`                | order owner             | Cancel an unpaid order, or pay                         |
| GET, POST          | `/payments/pesapal/ipn`                             | Pesapal                 | Payment notifications                                  |
| *                  | `/admin/...`                                        | admin                   | Products, orders, users, reviews, stats, audit log     |

The route code is in `server/api/` (`auth.py`, `account.py`, `catalog.py`, `orders.py`,
`admin.py`).

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

It should end with `found 0 vulnerabilities`. If a future `npm audit` reports something,
**don't run `npm audit fix --force`**: it can jump to incompatible major versions and
break the build. Update the affected package deliberately instead (Dependabot opens pull
requests for this automatically).

For a clean, exact install that matches `package-lock.json` (what CI does), use
`npm ci` instead of `npm install`.

### Step 3: Start the development server

Make sure the backend is running (Backend step 7), then:

```bash
npm run dev
```

Expected output:

```
  VITE v8.3.3  ready in 900 ms

  ➜  Local:   http://localhost:5173/
```

Open **http://localhost:5173**. The page updates instantly when you save a file.
Press `Ctrl+C` to stop the server.

### Step 4: Check it works

- The home page shows a "Best sellers" row with product photos.
- **Shop all** lists 22 products, and the category buttons filter them.
- Clicking a product opens its page with sizes, price and "You may also like".
- Adding something to the cart updates the cart counter in the header.
- **Sign in** (top right) with an account from `seed.py`. Your name replaces the
  button, and its menu has **Your account**, **Your orders** and, for the admin,
  **Admin**.
- Checkout from the cart → "Place order and pay" → the payment simulator → **Simulate
  successful payment** → the order shows as **Paid** under Your orders.
- As the admin, open **Admin → Orders** and mark that order as shipped; the customer
  sees the new status.

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
pip install -r requirements-dev.txt
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
  config.py               Settings from environment variables (dev/test/production profiles)
  api/                    API endpoints: auth, account, catalog, orders/payments, admin
  models/                 SQLAlchemy models (users, products, orders, reviews, audit log…)
  security.py             Password hashing and policy, encryption, access-control decorators
  validation.py           Input validation schemas for every request
  services.py             Business rules for orders, stock, payments and reviews
  payments.py             Pesapal API 3.0 client (and the development simulator)
  audit.py                Audit trail, security log and alerts
  errors.py               Generic error responses
  cli.py                  flask create-admin / prune-tokens / verify-audit-log
  tests/                  Backend test suite (pytest)
  catalog.py              Storefront products used by seed.py
  seed.py                 Resets the database with sample data
  migrations/             Alembic migrations (Flask-Migrate)
  static/products/        Product photos, served at /static/products/
  static/image-sources.json  Where each photo came from (CC0 / public domain)
  requirements.in         Direct Python dependencies
  requirements.txt        All Python packages, pinned with hashes (generated)
  .env.example            Every setting, with no real values
  instance/               Database, logs/security.log and outbox/ (git-ignored)
trendify-frontend/        React storefront
  src/routes/             One file per page (file-based routing)
  src/routes/admin*.tsx   Admin area
  src/lib/api.ts          API client (cookies, CSRF header, session refresh)
  src/lib/auth.tsx        Signed-in user
  src/lib/products.ts     Fetches products from the API
  src/lib/cart.tsx        Cart and wishlist (localStorage)
  vite.config.ts          Dev server, proxy to the backend, CSP for builds
  public/_headers         Security headers for static hosts
.github/                  CI (tests + dependency scans) and Dependabot
SECURITY.md               How each OWASP Top 10 risk is handled
```

## Deploying to production

A short checklist (details in [SECURITY.md](SECURITY.md)):

1. Set `APP_ENV=production` and every required variable from `server/.env.example`
   (`SECRET_KEY`, `ENCRYPTION_KEY`, `CORS_ORIGINS`, `FRONTEND_URL`, `API_PUBLIC_URL`,
   Pesapal credentials, mail settings). The app refuses to start if a required one is
   missing or unsafe.
2. Serve both parts over **HTTPS** only. Behind a reverse proxy, set
   `TRUSTED_PROXY_COUNT`.
3. Run the API with a production server, not `python app.py`, for example
   `pip install gunicorn` then `gunicorn -w 2 -b 127.0.0.1:5000 "app:create_app()"`.
4. Use Redis for rate limits if you run more than one process
   (`RATELIMIT_STORAGE_URI=redis://...`).
5. Create the database with `flask db upgrade` and the first admin with
   `flask create-admin`. Don't run `seed.py`.
6. Build the frontend with `VITE_API_URL=https://your-api npm run build` and upload
   `dist/`. Make sure the host sends the headers in `public/_headers`.
7. On GitHub, protect `main`: Settings → Branches → require a pull request with a review
   and passing CI before merging.

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
| I don't know the demo passwords                                         | They're printed once by `seed.py`. Run it again (it resets the data), or use "Forgot password" and open the link from `server/instance/outbox/`.                                                                                                                                          |
| "Please verify your email address first" when ordering                  | Open the verification email in `server/instance/outbox/` (development) or your inbox, or request a new link on the Account page.                                                                                                                                                          |
| "Too many failed attempts" / HTTP 423                                   | The account is locked for 15 minutes after 5 wrong passwords. Wait, reset the password, or have an admin click **Unlock** under Admin → Users.                                                                                                                                            |
| "Too many requests" / HTTP 429                                          | A rate limit was hit (for example 10 sign-in attempts a minute). Wait a minute and try again.                                                                                                                                                                                             |
| Signed in, but every page then asks you to sign in again                | You're running with `APP_ENV=production` over plain `http://`. Production cookies are `Secure` and only sent over HTTPS. Use the development profile locally, or serve the site over HTTPS.                                                                                               |
| `RuntimeError: Unsafe production configuration`                         | `APP_ENV=production` is set but a required secret is missing; the message lists which.                                                                                                                                                                                                    |
| `ERROR: THESE PACKAGES DO NOT MATCH THE HASHES` from pip                | A download didn't match the locked hash. Retry; if it persists, don't bypass it: the package may have been tampered with.                                                                                                                                                                 |
