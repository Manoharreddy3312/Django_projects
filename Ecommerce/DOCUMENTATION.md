# FlipMart — Complete Project Documentation

This document describes the **FlipMart** eCommerce project: architecture, setup, configuration, features, APIs, admin workflows, and operations.

**Related files**

| Document | Purpose |
|----------|---------|
| [README.md](README.md) | Quick start, install, run server |
| [API_ENDPOINTS.md](API_ENDPOINTS.md) | REST API path reference |
| [UML_DIAGRAMS.md](UML_DIAGRAMS.md) | UML diagrams (Mermaid): models, component, sequences |
| [COMPONENT_DIAGRAM.md](COMPONENT_DIAGRAM.md) | Component diagram + inventory |
| [DEPLOYMENT_DIAGRAM.md](DEPLOYMENT_DIAGRAM.md) | Deployment diagram (dev + production) |
| [.env.example](.env.example) | Environment variable template |

---

## 1. Project overview

FlipMart is a **Django** web application with **Django REST Framework (DRF)** APIs, **Bootstrap 5** templates, and **vanilla JavaScript** for AJAX (cart, wishlist, checkout, search, OTP modal). It is structured for learning and as a base for production-style deployments.

**High-level capabilities**

- User registration with **email activation**, **password reset**, **profile**
- **OTP login** (email; SMS via Twilio when configured)
- **Google OAuth** (django-allauth)
- **Product catalog** with categories, search, filters, reviews
- **Login required** for product detail (web + API retrieve)
- **Cart & wishlist** (session + API, AJAX)
- **Checkout** with shipping addresses
- **Payments**: **Razorpay** (card/UPI/etc.) and **bank transfer** (manual verification in admin)
- **Order tracking** with time-based stages and optional emails
- **JWT** for API clients; **session + CSRF** for browser forms and AJAX

---

## 2. Technology stack

| Layer | Technology |
|-------|------------|
| Backend | Python, Django 5.x / 6.x |
| API | Django REST Framework, djangorestframework-simplejwt |
| Auth (OAuth) | django-allauth (Google) |
| Database | PostgreSQL (recommended prod) or SQLite (dev default) |
| Payments | Razorpay API |
| SMS OTP | Twilio (optional) |
| Frontend | HTML, CSS, Bootstrap 5, JavaScript (fetch) |
| Images | Pillow (seed placeholders) |

**Python packages** (see `requirements.txt`): `djangorestframework`, `djangorestframework-simplejwt`, `django-allauth`, `django-cors-headers`, `django-filter`, `psycopg2-binary`, `python-dotenv`, `razorpay`, `twilio`, `Pillow`, `cryptography`.

---

## 3. Repository structure

```
Ecommerce/
├── manage.py
├── requirements.txt
├── .env.example
├── README.md
├── DOCUMENTATION.md          ← this file
├── API_ENDPOINTS.md
├── Ecommerce/                # Django project package
│   ├── settings.py         # Installed apps, DB, DRF, JWT, email, Razorpay, allauth
│   ├── urls.py             # Root URL routing
│   ├── wsgi.py / asgi.py
├── accounts/               # Users, OTP, profile, activation, password reset
│   ├── models.py           # User (email login), UserProfile, tokens, OTPChallenge
│   ├── views.py            # Web auth + OTP JSON views
│   ├── views_api.py        # DRF register / me
│   ├── urls.py
│   ├── api_urls.py         # JWT token URLs
│   ├── forms.py
│   ├── otp_utils.py        # OTP generation, rate limit, email/SMS
│   ├── mailing.py          # Activation & password reset emails
│   ├── adapters.py         # allauth social account hooks
│   ├── admin.py
│   └── migrations/
├── store/                  # Catalog, commerce, orders, payments
│   ├── models.py           # Category, Product, Cart, Wishlist, Order, Payment, BankDetail, …
│   ├── views.py            # Template views (home, products, cart, checkout, …)
│   ├── urls.py
│   ├── admin.py            # Includes bank-transfer confirmation action
│   ├── payment_flow.py     # finalize_order_after_payment()
│   ├── tracking.py         # Time-based order stages + emails
│   ├── emails.py           # Order confirmation email
│   ├── context_processors.py  # cart_item_count
│   ├── placeholder_images.py  # Pillow PNGs for seed
│   ├── api/
│   │   ├── urls.py         # DRF router
│   │   ├── views.py        # ViewSets
│   │   ├── serializers.py
│   │   └── permissions.py
│   ├── management/commands/
│   │   ├── seed_demo.py    # Demo data + images + default bank row
│   │   └── refresh_order_tracking.py
│   └── migrations/
├── templates/              # Django templates (base.html, store/*, accounts/*)
├── static/
│   ├── js/                 # app.js, checkout.js, cart_page.js, wishlist_page.js
│   ├── css/custom.css
│   └── img/no-image.svg
└── media/                  # User uploads (created at runtime; gitignored in real projects)
```

---

## 4. URL routing (high level)

| Prefix | Purpose |
|--------|---------|
| `/admin/` | Django admin |
| `/oauth/` | django-allauth (e.g. Google); kept separate so `/accounts/login/` stays custom |
| `/accounts/…` | Register, login, logout (**POST**), profile, activation, password reset, OTP API |
| `/` | Store: home, products, cart, wishlist, checkout, orders |
| `/api/v1/` | Store REST API |
| `/api/v1/auth/` | JWT obtain/refresh, API register, `me` |

**Important:** Logout must use **POST** (navbar uses a form with CSRF). A GET to `/accounts/logout/` returns **405 Method Not Allowed**.

---

## 5. Installation and first run

### 5.1 Prerequisites

- Python 3.11+ (project tested with Django 6.x)
- Optional: PostgreSQL, Razorpay account, Google OAuth client, SMTP, Twilio

### 5.2 Steps

```bash
cd Ecommerce
python -m venv .venv
# Windows:
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env   # then edit .env
python manage.py migrate
python manage.py createsuperuser   # email + password
python manage.py seed_demo         # optional demo catalog, images, bank row
python manage.py runserver
```

- **Shop:** `http://127.0.0.1:8000/`
- **Admin:** `http://127.0.0.1:8000/admin/`

### 5.3 Database

- If **`DB_NAME`** (and related vars) are set in `.env`, **PostgreSQL** is used.
- If **`DB_NAME` is omitted**, Django uses **`db.sqlite3`** in the project directory.

### 5.4 Static and media (production)

```bash
python manage.py collectstatic --noinput
```

Serve `STATIC_ROOT` and `MEDIA_ROOT` via the web server or object storage; `DEBUG=False` does not serve media automatically.

---

## 6. Environment variables

Copy **`.env.example`** to **`.env`**. Main variables:

| Variable | Role |
|----------|------|
| `DJANGO_SECRET_KEY` | Cryptographic signing; **required in production** |
| `DJANGO_DEBUG` | `True` / `False` |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated hosts |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | PostgreSQL (optional) |
| `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USE_TLS`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` | SMTP |
| `DEFAULT_FROM_EMAIL` | From address for outbound mail |
| `SITE_URL` | Base URL for activation/reset links (no trailing slash issues—code uses `rstrip('/')`) |
| `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` | Google OAuth (also configurable in admin Social applications) |
| `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET` | Razorpay |
| `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER` | SMS OTP (optional) |
| `CSRF_TRUSTED_ORIGINS` | HTTPS origins in production (e.g. `https://yourdomain.com`) |

**Email in development:** If `DEBUG=True` and `EMAIL_HOST_USER` is empty, settings fall back to **console email backend** (OTP and mails print in the terminal).

**OTP tuning** (optional in `settings.py`): `OTP_EXPIRE_MINUTES`, `OTP_RATE_LIMIT_SECONDS`, `OTP_MAX_PER_WINDOW`, `OTP_WINDOW_SECONDS`.

---

## 7. Django Site and Google OAuth

1. **Admin → Sites:** set **Site** ID **1** domain to your host (e.g. `127.0.0.1:8000` without `http://`).
2. **Google Cloud Console:** OAuth 2.0 client (Web application).
3. **Authorized redirect URI** (allauth mounted at `/oauth/`):

   `http://127.0.0.1:8000/oauth/google/login/callback/`

4. **Admin → Social applications** (optional): add Google provider, or rely on `SOCIALACCOUNT_PROVIDERS` + env in `settings.py`.

5. **Login with Google** links use: `/oauth/google/login/?next=...`

---

## 8. Authentication flows

### 8.1 Email / password

1. **Register** → user created **inactive**; **activation email** with token.
2. User opens link → account **active** and **email verified**.
3. **Login** requires **active** user and **verified email** (unless using social login path handled in adapters).

### 8.2 Password reset

Request form sends email with one-time token; user sets a new password on the confirm URL.

### 8.3 OTP (modal + API)

- **Request:** `POST /accounts/api/otp/request/` JSON `{"identifier": "email or phone"}` with **CSRF** header (`X-CSRFToken`) from the hidden form in `base.html`.
- **Verify:** `POST /accounts/api/otp/verify/` JSON `identifier`, `code`, optional `next`.
- **Email:** always supported if SMTP or console backend works.
- **SMS:** only if Twilio env vars are set; otherwise use email OTP.
- **Rate limiting:** cache-backed (default **LocMem**; use **Redis** in production).

### 8.4 Google

Handled by **allauth**; adapter sets **email verified** and syncs profile hints. New users are created automatically.

### 8.5 Logout

**POST** only. The navbar submits a small form to `/accounts/logout/` with `{% csrf_token %}`.

---

## 9. Store and access control

### 9.1 Product visibility

- **Product list** and **search** (web + API list): public (for SEO and autocomplete).
- **Product detail** (web page + **API retrieve**): **login required** (`LoginRequiredMixin` / `IsAuthenticated`).

Unauthenticated users clicking a product are redirected to login with `?next=` back to the product.

### 9.2 Cart, wishlist, checkout

Protected on the web with **LoginRequiredMixin**; API endpoints require authentication.

### 9.3 Main models (`store.models`)

- **Category**, **Product**, **ProductImage**, **Review**
- **ShippingAddress**
- **Cart**, **CartItem** (one cart per user)
- **WishlistItem**
- **Order**, **OrderItem**
- **Payment** (Razorpay + bank transfer fields; `method`, `status`, `bank_reference`, …)
- **BankDetail** (accounts shown for manual transfer)

---

## 10. Payments

### 10.1 Razorpay

1. Checkout with `payment_method: "razorpay"` (default in UI).
2. Server creates **Order** (`PENDING_PAYMENT`) and **Payment**, then Razorpay **order**.
3. Browser opens Razorpay Checkout; on success, **POST** `/api/v1/payments/verify/` with signature fields.
4. **`finalize_order_after_payment`** sets order **placed**, clears **cart**, adjusts **stock**, sends **order confirmation email**.

### 10.2 Bank transfer

1. **Admin → Bank details:** create at least one **active** row (seed may create a demo row).
2. Checkout with `payment_method: "bank_transfer"`.
3. Response includes **`bank_details`** and order id; customer pays externally and submits **UTR** via `/api/v1/payments/bank-reference/`.
4. **Admin → Payments:** select row → action **Confirm bank transfer — mark paid & fulfill order** (same fulfillment as Razorpay success).

Shared logic lives in **`store/payment_flow.py`**.

---

## 11. Order tracking

- **`store/tracking.py`:** from **`confirmed_at`** (set when payment succeeds), elapsed time drives **progress %** and **labels** (Placed → Shipping → Dispatched → Delivered).
- **`GET /api/v1/orders/<id>/tracking/`** and order detail page refresh stages (and can send stage emails when phase advances).
- **Cron (recommended):** `python manage.py refresh_order_tracking` (e.g. hourly) so stages update without the user opening the page.

---

## 12. REST API

Full path table: **[API_ENDPOINTS.md](API_ENDPOINTS.md)**.

**Authentication**

- **Session** + **CSRF** for browser `fetch` to same origin.
- **JWT:** `POST /api/v1/auth/token/` with body `{"username": "<email>", "password": "..."}` (SimpleJWT uses the key `username` for the email field).

**Pagination:** list endpoints use DRF page size (default 12); `?page_size=` supported where configured.

---

## 13. Frontend notes

- **`templates/base.html`:** navbar, CSRF store form (`#flipmart-csrf-store`), auth modal (email links, OTP, Google), toast, global scripts.
- **`static/js/app.js`:** `FlipMart.apiJson`, `getCsrfToken`, cart/wishlist helpers, OTP handlers, search suggestions (public product list API).
- **`checkout.js`:** address CRUD, Razorpay vs bank transfer, bank UTR submit.
- **Product detail:** add to cart / wishlist / review via API + CSRF.

---

## 14. Management commands

| Command | Purpose |
|---------|---------|
| `seed_demo` | Categories, products, Pillow images, default **BankDetail** if none exist |
| `seed_demo --images-only` | Only fill missing category/product images |
| `refresh_order_tracking` | Advance tracking stages + emails (cron) |

---

## 15. Admin panel

Register/manage:

- **Users**, **Bank details**, **Categories**, **Products** (+ images), **Orders**, **Payments**, **Reviews**, **Addresses**, etc.

**Bank transfer:** use **Payment** list → **Confirm bank transfer** action on pending bank payments.

---

## 16. Security checklist (production)

- [ ] `DEBUG=False`, strong `SECRET_KEY`, correct `ALLOWED_HOSTS`
- [ ] `CSRF_TRUSTED_ORIGINS` for HTTPS
- [ ] Secure cookies: `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE` behind HTTPS
- [ ] PostgreSQL credentials in env, not in code
- [ ] Redis (or similar) for cache / OTP rate limits
- [ ] Restrict **Bank detail** and payment data in admin (staff only)
- [ ] Celery (or queue) for email and heavy tasks at scale
- [ ] Regular dependency updates

---

## 17. Troubleshooting

| Symptom | Likely cause | What to do |
|---------|----------------|------------|
| **405** on `/accounts/logout/` | GET request | Use navbar **Logout** (POST form), not a bookmarked GET URL |
| **403** on OTP / AJAX POST | Missing CSRF | Ensure `{% csrf_token %}` form exists in `base.html`; hard refresh |
| **OTP email not received** | SMTP not set | Use console backend in dev or configure `EMAIL_*` |
| **SMS OTP fails** | Twilio unset | Use email OTP or set Twilio env vars |
| **Google OAuth error** | Wrong redirect URI / Site domain | Match Google console + Sites + `SITE_URL` |
| **Razorpay not opening** | Missing keys | Set `RAZORPAY_*` in `.env` |
| **Bank transfer unavailable** | No active bank rows | Admin → Bank details → add + activate |
| **SQLite locked** | Concurrent writes | Use PostgreSQL for multi-worker prod |

---

## 18. License and credits

This project is a **demo / educational** codebase. Razorpay, Google, Twilio, and Django are trademarks of their respective owners. Configure all third-party keys in **`.env`** and never commit secrets to version control.

---

*Last updated to match the FlipMart codebase structure and features described above.*
