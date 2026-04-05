# FlipMart REST API (`/api/v1/`)

Authentication: **JWT** (`Authorization: Bearer <access>`) and **session** (browser cookies + CSRF for unsafe methods).

Obtain tokens:

- `POST /api/v1/auth/token/` — body: `{"username": "<email>", "password": "..."}`  
- `POST /api/v1/auth/token/refresh/` — body: `{"refresh": "..."}`

Accounts:

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/auth/register/` | Register (inactive until email link) |
| GET | `/api/v1/auth/me/` | Current user + profile (auth required) |

Categories (staff: write; others: read):

| Method | Path |
|--------|------|
| GET, POST | `/api/v1/categories/` |
| GET, PUT, PATCH, DELETE | `/api/v1/categories/<slug>/` |

Products:

| Method | Path | Notes |
|--------|------|-------|
| GET | `/api/v1/products/` | List, filter `?category=<id>`, search `?search=`, order `?ordering=price` |
| GET | `/api/v1/products/<pk>/` | **Requires authentication** |

Cart (auth):

| Method | Path |
|--------|------|
| GET | `/api/v1/cart/` |
| POST | `/api/v1/cart/items/` — body `{"product_id": N, "quantity": 1}` |
| PATCH | `/api/v1/cart/items/<item_id>/` — body `{"quantity": N}` |
| DELETE | `/api/v1/cart/items/<item_id>/remove/` |

Wishlist (auth):

| Method | Path |
|--------|------|
| GET, POST | `/api/v1/wishlist/` |
| DELETE | `/api/v1/wishlist/<pk>/` |
| POST | `/api/v1/wishlist/toggle/` — body `{"product_id": N}` |

Addresses (auth):

| Method | Path |
|--------|------|
| GET, POST | `/api/v1/addresses/` |
| GET, PUT, PATCH, DELETE | `/api/v1/addresses/<pk>/` |

Bank details (auth) — accounts for NEFT/IMPS/UPI instructions:

| Method | Path |
|--------|------|
| GET | `/api/v1/bank-details/` — active records only |

Orders (auth):

| Method | Path |
|--------|------|
| GET | `/api/v1/orders/` |
| GET | `/api/v1/orders/<pk>/` |
| GET | `/api/v1/orders/<pk>/tracking/` | Refresh stage + response for progress UI |
| POST | `/api/v1/orders/checkout/` — body `{"address_id": N, "payment_method": "razorpay" \| "bank_transfer"}` |

Payments (auth):

| Method | Path |
|--------|------|
| POST | `/api/v1/payments/verify/` — Razorpay only: `order_id`, `razorpay_order_id`, `razorpay_payment_id`, `razorpay_signature` |
| POST | `/api/v1/payments/bank-reference/` — after manual transfer: `order_id`, `bank_reference` (UTR) |

**Admin:** confirm bank transfers under **Payments** → action **Confirm bank transfer — mark paid & fulfill order** (sets order placed, clears cart, adjusts stock, sends email).

Reviews:

| Method | Path |
|--------|------|
| GET | `/api/v1/reviews/?product=<id>` |
| POST | `/api/v1/reviews/` (auth) |

HTML OTP (session CSRF):

- `POST /accounts/api/otp/request/` — `{"identifier": "email or phone"}`
- `POST /accounts/api/otp/verify/` — `{"identifier", "code", "next"}`

Google OAuth (browser):

- `/oauth/google/login/?next=...`
