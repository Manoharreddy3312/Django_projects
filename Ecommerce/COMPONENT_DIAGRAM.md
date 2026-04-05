# FlipMart — Component diagram

UML-style **component view** of the FlipMart eCommerce system: subsystems, components, and dependencies.

> Also embedded in [UML_DIAGRAMS.md §2](UML_DIAGRAMS.md#2-component-diagram-uml-style) with the rest of the UML set.

---

## Diagram (Mermaid)

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

---

## Component inventory

| Component | Responsibility | Key paths |
|-----------|----------------|-----------|
| **URL gateway** | Route HTTP to apps | `Ecommerce/urls.py` |
| **accounts** | User model, registration, activation, password reset, OTP, profile, allauth adapters | `accounts/` |
| **accounts API** | JWT-adjacent register / `me` | `accounts/views_api.py`, `accounts/api_urls.py` |
| **store** | Product pages, cart/wishlist/checkout templates | `store/views.py`, `store/urls.py` |
| **store.api** | REST catalog, cart, orders, payments, reviews | `store/api/` |
| **Admin** | Staff CRUD, bank transfer confirmation | `store/admin.py`, `accounts/admin.py` |
| **Middleware** | Session, CSRF, CORS, allauth account middleware | `settings.py` `MIDDLEWARE` |
| **Persistence** | ORM models, migrations | `accounts/models.py`, `store/models.py` |

---

## External systems

| System | Used for |
|--------|----------|
| **PostgreSQL / SQLite** | Primary data store |
| **SMTP** | Transactional email (activation, OTP, orders) |
| **Twilio** | SMS OTP (optional) |
| **Google OAuth** | Social login (django-allauth) |
| **Razorpay** | Online payments |
| **Local media FS** | Product/category/user images |

---

## How to render

- **GitHub / GitLab**: open this `.md` file (native Mermaid).
- **VS Code**: Markdown preview with a Mermaid extension.
- **Export PNG/SVG**: [mermaid.live](https://mermaid.live) — paste the fenced `mermaid` block.


