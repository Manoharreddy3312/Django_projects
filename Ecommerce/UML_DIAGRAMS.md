# FlipMart — UML diagrams

Diagrams use [Mermaid](https://mermaid.js.org/) (renders on GitHub, many IDEs, and Markdown previewers).

---

## 1. Domain model — class diagram (Django ORM)

`User` extends Django’s **`AbstractUser`** (fields such as `is_staff`, `is_active`, `date_joined` are inherited; **`username` is removed** — login is **`email`**).

```mermaid
classDiagram
    direction TB

    class User {
        <<extends AbstractUser>>
        +email PK
        +phone
        +is_email_verified
        +avatar
    }

    class UserProfile {
        +full_name
        +address_line1
        +city
        +state
        +postal_code
        +country
    }

    class EmailActivationToken {
        +token
        +created_at
    }

    class PasswordResetToken {
        +token
        +created_at
    }

    class OTPChallenge {
        +identifier
        +channel
        +code_hash
        +expires_at
        +attempts
    }

    class Category {
        +name
        +slug
        +description
        +is_active
    }

    class Product {
        +name
        +slug
        +sku
        +price
        +stock
        +is_active
    }

    class ProductImage {
        +image
        +sort_order
    }

    class Review {
        +rating
        +title
        +body
    }

    class ShippingAddress {
        +full_name
        +phone
        +line1
        +city
        +postal_code
    }

    class Cart {
        +updated_at
    }

    class CartItem {
        +quantity
    }

    class WishlistItem {
    }

    class Order {
        +status
        +shipping_address
        +subtotal
        +total
        +confirmed_at
        +tracking_email_phase
    }

    class OrderItem {
        +quantity
        +unit_price
    }

    class Payment {
        +method
        +provider
        +status
        +amount_paise
        +razorpay_order_id
        +bank_reference
    }

    class BankDetail {
        +title
        +account_holder_name
        +bank_name
        +account_number
        +ifsc_code
        +upi_id
        +is_active
    }

    User "1" --> "1" UserProfile : profile
    User "1" --> "*" EmailActivationToken
    User "1" --> "*" PasswordResetToken

    Category "1" --> "*" Product
    Product "1" --> "*" ProductImage
    Product "1" --> "*" Review
    User "1" --> "*" Review

    User "1" --> "*" ShippingAddress
    User "1" --> "1" Cart
    Cart "1" --> "*" CartItem
    CartItem "*" --> "1" Product

    User "1" --> "*" WishlistItem
    WishlistItem "*" --> "1" Product

    User "1" --> "*" Order
    Order "1" --> "*" OrderItem
    OrderItem "*" --> "1" Product
    Order "1" --> "1" Payment : payment

    note for BankDetail "No FK to Order.\nGlobal payout instructions\nfor bank_transfer checkout."
```

---

## 2. Component diagram (UML-style)

Shows **software components**, **dependencies** (labeled arrows), and **external systems**.

```mermaid
flowchart TB
    subgraph External["«external system»"]
        RZ["Razorpay API"]
        TW["Twilio API"]
        GGL["Google OAuth 2.0"]
        SMTP["SMTP server"]
    end

    subgraph ClientTier["«component» Client tier"]
        WEB["Web browser\nTemplates + Bootstrap + static JS"]
        API_CLIENT["API client\nJWT Bearer"]
    end

    subgraph Server["«subsystem» FlipMart server (Django)"]
        direction TB
        GW["«component» URL gateway\nEcommerce/urls.py"]

        subgraph ACC_PKG["«component» accounts"]
            ACC_V["Views: register, login, OTP, profile"]
            ACC_API["views_api: register, me"]
            ACC_M["mailing, otp_utils, adapters"]
        end

        subgraph STO_PKG["«component» store"]
            STO_V["Views: home, products, cart UI"]
            STO_CTX["context_processors"]
        end

        subgraph API_PKG["«component» store.api"]
            DRF["DRF: ViewSets + routers\n/api/v1/*"]
            AUTH_JWT["SimpleJWT\n/api/v1/auth/token/"]
        end

        subgraph ADM_PKG["«component» django.contrib.admin"]
            ADM_UI["Admin UI"]
        end

        subgraph CFG["«artifact» configuration"]
            SET["settings.py + .env"]
        end

        MW["«component» Middleware stack\nSession, CSRF, CORS, allauth"]
    end

    subgraph DataTier["«component» Persistence"]
        DB[("PostgreSQL / SQLite")]
        FS["File system\nmedia/ uploads"]
    end

    WEB -->|"HTTP(S) HTML + form POST"| GW
    API_CLIENT -->|"HTTPS JSON REST"| GW

    GW --> ACC_V
    GW --> STO_V
    GW --> DRF
    GW --> AUTH_JWT
    GW --> ADM_UI
    GW --> MW

    ACC_V --> ACC_M
    ACC_API --> ACC_M
    ACC_M --> SMTP
    ACC_M --> TW
    ACC_M --> GGL

    ACC_V --> DB
    ACC_API --> DB
    STO_V --> DB
    STO_CTX --> DB
    DRF --> DB
    AUTH_JWT --> DB
    ADM_UI --> DB

    DRF --> RZ
    STO_V --> FS

    SET -.->|"configures"| Server
```

**Dependency summary**

| From | To | Interface / protocol |
|------|-----|----------------------|
| Web browser | URL gateway | HTTP(S), cookies, CSRF |
| API client | URL gateway | HTTPS JSON, `Authorization: Bearer` |
| accounts | SMTP / Twilio / Google | Email, SMS, OAuth |
| store.api | Razorpay | HTTPS REST (server-side) |
| Django apps | Database | ORM → SQL |
| store | File system | `MEDIA_ROOT` uploads |

Full component inventory: [COMPONENT_DIAGRAM.md](COMPONENT_DIAGRAM.md).

---

## 3. Checkout and payment — sequence diagram (Razorpay)

```mermaid
sequenceDiagram
    actor U as User
    participant UI as Checkout JS
    participant API as DRF /orders /payments
    participant RZ as Razorpay
    participant DB as Database

    U->>UI: Select address + Pay
    UI->>API: POST checkout address_id, payment_method=razorpay
    API->>DB: Create Order, OrderItems, Payment
    API->>RZ: Create order
    RZ-->>API: order_id
    API-->>UI: order + razorpay options
    UI->>RZ: Open Checkout widget
    U->>RZ: Complete payment
    RZ-->>UI: payment_id, signature
    UI->>API: POST payments/verify
    API->>RZ: Verify signature
    API->>DB: finalize order, stock, clear cart
    API-->>UI: success
    UI->>U: Redirect to order detail
```

---

## 4. Bank transfer checkout — sequence diagram

```mermaid
sequenceDiagram
    actor U as User
    participant UI as Checkout JS
    participant API as DRF
    participant DB as Database
    actor A as Admin

    U->>UI: Bank transfer + Place order
    UI->>API: POST checkout payment_method=bank_transfer
    API->>DB: Order PENDING, Payment pending_verification
    API-->>UI: bank_details + order
    U->>U: NEFT / IMPS / UPI
    U->>UI: Submit UTR
    UI->>API: POST payments/bank-reference
    API->>DB: Save bank_reference
    A->>DB: Admin: Confirm bank transfer
    DB->>DB: finalize_order_after_payment
    Note over DB: Order PLACED, stock, cart, email
```

---

## 5. Authentication options (conceptual)

```mermaid
flowchart LR
    subgraph Login["Sign-in paths"]
        E[Email + password]
        O[OTP email/SMS]
        G[Google OAuth]
    end

    subgraph Outcomes["Session"]
        S[Django session cookie]
    end

    E --> S
    O --> S
    G --> S

    subgraph APIAuth["API only"]
        J[JWT access/refresh]
    end

    E -.->|token endpoint| J
```

---

## 6. Deployment diagram (UML)

**Nodes** = execution environments or devices; **artifacts** = deployable pieces; dashed lines = optional.

### 6.1 Local development

```mermaid
flowchart TB
    subgraph DevMachine["«device» Developer machine"]
        subgraph BrowserNode["«execution environment» Browser"]
            BR[Chrome / Firefox / Edge]
        end
        subgraph PyNode["«execution environment» Python venv"]
            RUN["manage.py runserver\n:8000"]
            ART1["«artifact» Django project\nEcommerce/"]
        end
        subgraph LocalFS["«node» Local disk"]
            SQLITE[("«artifact» db.sqlite3")]
            MEDIA["«artifact» media/"]
            STATIC["«artifact» staticfiles/"]
        end
    end

    subgraph Internet["«node» Internet"]
        EXT_SMTP[SMTP]
        EXT_RZ[Razorpay]
        EXT_TW[Twilio]
        EXT_GO[Google OAuth]
    end

    BR <-->|HTTP localhost:8000| RUN
    RUN --- ART1
    ART1 --> SQLITE
    ART1 --> MEDIA
    RUN -.->|optional| EXT_SMTP
    RUN -.->|optional| EXT_RZ
    RUN -.->|optional| EXT_TW
    RUN -.->|optional| EXT_GO
```

### 6.2 Production (typical)

```mermaid
flowchart TB
    subgraph Users["«device» End users"]
        U1[Browser / mobile app]
    end

    subgraph Edge["«execution environment» Edge / CDN"]
        NGINX["«artifact» Nginx\n(or Caddy / ALB)"]
        CDN["«artifact» Static + media CDN\noptional"]
    end

    subgraph AppFarm["«node» App tier (VM / container / PaaS)"]
        subgraph C1["«execution environment» Container / process"]
            GUN["«artifact» Gunicorn / uWSGI\nworkers"]
            DJ["«artifact» Django + DRF\nFlipMart"]
        end
    end

    subgraph DataTier["«node» Data tier"]
        PG[("«artifact» PostgreSQL")]
        REDIS[("«artifact» Redis\noptional: cache / OTP rate limit")]
    end

    subgraph Workers["«node» Background optional"]
        CEL["«artifact» Celery workers\nemail / tracking"]
    end

    subgraph SaaS["«node» External services"]
        SMTP2[SMTP]
        RZ2[Razorpay]
        TW2[Twilio]
        GO2[Google OAuth]
    end

    U1 -->|HTTPS| NGINX
    NGINX -->|proxy_pass /| GUN
    NGINX -->|/static /media or CDN| CDN
    GUN --> DJ
    DJ --> PG
    DJ -.->|optional| REDIS
    DJ -.->|optional queue| CEL
    CEL -.-> PG
    DJ --> SMTP2
    DJ --> RZ2
    DJ --> TW2
    DJ --> GO2
```

**Deployment notes**

| Artifact | Typical location |
|----------|------------------|
| Django app | App server (Gunicorn), immutable image in K8s/ECS |
| `STATIC_ROOT` | Nginx volume, S3 + CloudFront, Whitenoise |
| `MEDIA_ROOT` | Object storage (S3, GCS) with signed URLs |
| `SECRET_KEY`, DB URL | Env vars / secrets manager (not in image) |

Full node list and checklists: [DEPLOYMENT_DIAGRAM.md](DEPLOYMENT_DIAGRAM.md).

---

## Exporting to PNG/SVG

- [Mermaid Live Editor](https://mermaid.live) — paste a diagram and export.
- VS Code: “Markdown Preview Mermaid Support” or similar extensions.
- CLI: `@mermaid-js/mermaid-cli` (`mmdc -i file.mmd -o out.png`).

---

*Diagrams reflect the FlipMart codebase under `accounts/` and `store/`.*
