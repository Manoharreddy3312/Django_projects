# FlipMart — Django + DRF eCommerce demo

Production-style structure with PostgreSQL (optional), JWT APIs, Razorpay payments, email flows, OTP login (email + Twilio SMS), Google OAuth (django-allauth), Bootstrap UI, and AJAX cart/wishlist/checkout.

**Documentation**

- **[DOCUMENTATION.md](DOCUMENTATION.md)** — full project documentation (architecture, setup, auth, payments, admin, troubleshooting)
- **[API_ENDPOINTS.md](API_ENDPOINTS.md)** — REST API reference

## 1. Prerequisites

- Python 3.11+ (tested with Django 6.x)
- PostgreSQL (optional — without `DB_NAME` in `.env` the project uses SQLite)
- [Razorpay](https://razorpay.com/) test keys for payments
- [Google Cloud OAuth](https://console.cloud.google.com/) client for “Sign in with Google”
- SMTP account for real emails (otherwise `DEBUG=True` without `EMAIL_HOST_USER` uses **console** email)

## 2. Install

```bash
cd Ecommerce
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

## 3. Environment

Copy `.env.example` to `.env` and set at least:

- `DJANGO_SECRET_KEY` — long random string for production
- `DJANGO_DEBUG=False` in production; `True` locally
- `DJANGO_ALLOWED_HOSTS` — your domain(s)
- PostgreSQL: `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` (omit `DB_NAME` to use SQLite)
- `SITE_URL` — e.g. `http://127.0.0.1:8000` (used in activation/reset links)
- `EMAIL_*` and `DEFAULT_FROM_EMAIL` for SMTP
- `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET`
- `RAZORPAY_KEY_ID` / `RAZORPAY_KEY_SECRET`
- Twilio (optional, for SMS OTP): `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER`

## 4. Database and static files

```bash
python manage.py migrate
python manage.py createsuperuser   # use email + password
python manage.py seed_demo         # optional sample products + generated PNG images (Pillow)
python manage.py seed_demo --images-only   # add images to categories/products missing files
python manage.py collectstatic --noinput   # production only
```

### Django `Site` for OAuth

In **Django admin → Sites**, set site **ID 1** domain to your host, e.g. `127.0.0.1:8000` (no `http://`).

In **Social applications**, add Google with the same client ID/secret as in `.env` (or rely on `SOCIALACCOUNT_PROVIDERS` in `settings.py` when keys are in env).

Authorized redirect URI in Google Cloud (with default allauth paths under `/oauth/`):

- `http://127.0.0.1:8000/oauth/google/login/callback/`

## 5. Run development server

```bash
python manage.py runserver
```

- Shop: `http://127.0.0.1:8000/`
- Admin: `http://127.0.0.1:8000/admin/`
- API root: `http://127.0.0.1:8000/api/v1/`

## 6. Behaviour summary

| Area | Implementation |
|------|----------------|
| Email/password | Register → inactive until activation link; login requires active + verified email |
| OTP | Email always; SMS via Twilio when configured |
| Google | `/oauth/google/login/`; profile fields synced in `accounts/adapters.py` |
| Product pages | **Login required** (web + API product detail) |
| Cart / wishlist / checkout | Login required (web + API) |
| Bank details | **Admin → Bank details**: account name, bank, IFSC, UPI, instructions; exposed on checkout for `bank_transfer` |
| Payments | **Razorpay** (order + verify) or **bank transfer** (pending until staff confirms in admin) |
| Order tracking | Time-based stages from `confirmed_at`: 0–24h 50% “Order Placed”, 24–48h 75% “Order Shipping”, 48–72h 100% “Order Dispatched”, then delivered; emails on stage changes |
| Cron | `python manage.py refresh_order_tracking` hourly (or similar) in production |

## 7. API reference

See [API_ENDPOINTS.md](API_ENDPOINTS.md).

JWT: `POST /api/v1/auth/token/` with `{"username":"<email>","password":"..."}`.

## 8. Security notes

- Keep `SECRET_KEY` and DB credentials out of git; use `.env`.
- Use HTTPS in production; set `CSRF_TRUSTED_ORIGINS` and `SECURE_*` cookies as appropriate.
- Prefer **Redis** cache for OTP rate limits in production instead of `LocMemCache`.
- Run emails and tracking updates asynchronously (e.g. Celery) under real load.

## Project layout (main files)

- `Ecommerce/settings.py` — DRF, JWT, allauth, DB, email, Razorpay, Twilio
- `accounts/` — custom `User`, activation/reset tokens, OTP, profile, adapters
- `store/` — catalog, cart, wishlist, orders, payments, reviews, tracking
- `store/api/` — serializers, viewsets, routers
- `templates/` — Bootstrap pages + auth modal
- `static/js/` — AJAX, Razorpay checkout, cart/wishlist pages, search suggestions
