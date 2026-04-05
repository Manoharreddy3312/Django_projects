# FlipMart — Deployment diagram (UML)

UML **deployment view**: **nodes** (hardware or execution environments), **artifacts** (deployable software), and **communication paths**.

> Also in [UML_DIAGRAMS.md §6](UML_DIAGRAMS.md#6-deployment-diagram-uml).

---

## 1. Local development

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

---

## 2. Production (reference architecture)

```mermaid
flowchart TB
    subgraph Users["«device» End users"]
        U1[Browser / mobile API client]
    end

    subgraph Edge["«execution environment» Reverse proxy / TLS"]
        NGINX["«artifact» Nginx / Caddy / ALB"]
        CDN["«artifact» CDN for static & media\noptional"]
    end

    subgraph AppFarm["«node» Application tier"]
        subgraph C1["«execution environment» WSGI / ASGI workers"]
            GUN["«artifact» Gunicorn / uWSGI / Daphne"]
            DJ["«artifact» Django + DRF\nFlipMart codebase"]
        end
    end

    subgraph DataTier["«node» Data tier"]
        PG[("«artifact» PostgreSQL")]
        REDIS[("«artifact» Redis\nOTP cache / sessions optional")]
    end

    subgraph Workers["«node» Async optional"]
        CEL["«artifact» Celery + broker\nemails, cron-style jobs"]
    end

    subgraph SaaS["«node» Third-party APIs"]
        SMTP2[SMTP relay]
        RZ2[Razorpay]
        TW2[Twilio]
        GO2[Google OAuth]
    end

    U1 -->|HTTPS 443| NGINX
    NGINX -->|HTTP / UNIX socket| GUN
    NGINX -.->|static/media| CDN
    GUN --> DJ
    DJ --> PG
    DJ -.-> REDIS
    DJ -.-> CEL
    CEL -.-> PG
    DJ --> SMTP2
    DJ --> RZ2
    DJ --> TW2
    DJ --> GO2
```

---

## 3. Node and artifact inventory

| «node» / environment | Hosts these artifacts |
|----------------------|------------------------|
| **Developer PC** | Browser, Python venv, `runserver`, SQLite file, `media/` |
| **Edge (Nginx)** | TLS termination, static file serving or redirect to CDN |
| **App server** | Gunicorn/uWSGI, Django WSGI application |
| **Database server** | PostgreSQL (schemas: django + app tables) |
| **Redis** (optional) | Cache backend for OTP rate limits, sessions |
| **Worker** (optional) | Celery: `send_mail`, `refresh_order_tracking` at scale |
| **Object storage** (optional) | `MEDIA_ROOT` offload (S3-compatible) |
| **Internet** | Razorpay, Twilio, Google OAuth, SMTP |

---

## 4. Environment → configuration mapping

| Deployment concern | Configure via |
|--------------------|----------------|
| DB host | `DATABASES` / `DB_*` in `.env` |
| Secret key | `DJANGO_SECRET_KEY` |
| Allowed hosts / CSRF | `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS` |
| Static | `collectstatic` + Nginx alias or Whitenoise |
| Media | `MEDIA_ROOT` or django-storages |
| HTTPS | Proxy sets `X-Forwarded-Proto`; `SECURE_SSL_REDIRECT` |

---

## 5. Minimal production command sketch

```bash
# Build static assets
python manage.py collectstatic --noinput

# Run app (example: 4 workers)
gunicorn Ecommerce.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

Nginx forwards `location /` to `http://127.0.0.1:8000` and serves `/static/` from `STATIC_ROOT`.

---

## Render / export

Paste any diagram into [mermaid.live](https://mermaid.live) for PNG or SVG.
