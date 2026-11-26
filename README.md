# Pixel Reviews API

[![CI](https://github.com/Yisusocanto/pixel-reviews-api/actions/workflows/ci.yml/badge.svg)](https://github.com/Yisusocanto/pixel-reviews-api/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](./LICENSE)
[![Python](https://img.shields.io/badge/Python-3.14-3776AB.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.141-009688.svg)](https://fastapi.tiangolo.com/)

RESTful backend service for **Pixel Reviews**, an open-source video game discovery, review, and cataloging platform.

> **Version Notice (v2):** This repository contains the second generation of the Pixel Reviews backend, rebuilt from the ground up with an asynchronous architecture, modular domain separation, Redis caching, RabbitMQ message queues, and automated testing. The first version of the project is now deprecated and archived for historical reference at [Pixel Reviews v1 (Deprecated)](https://github.com/Yisusocanto/pixel_reviews).
>
> **Companion Repositories:**
> - Frontend Application (Next.js): [pixel-reviews-frontend](https://github.com/Yisusocanto/pixel-reviews-frontend)
> - Content Moderation Worker (Go): [pixel-reviews-moderator](https://github.com/Yisusocanto/pixel-reviews-moderator)

---

## Architecture & Engineering Highlights

- **Domain-Driven Modular Structure:** Organized by domain (`auth`, `users`, `games`, `reviews`, `comments`, `likes`, `wishlists`, `reports`, `review_moderation`, `comment_moderation`, `social_studio`, `discover`, `developers`, `publishers`, `genres`, `platforms`, `stores`) using a strict `Router -> Service -> Repository` layered pattern and FastAPI dependency injection.
- **Pixel Social Studio & Gemini AI Service (`social_studio` + `services/gemini`):**
  - Admin-only content engine (`/admin/social/candidates`, `/admin/social/generate`, `/admin/social/tts`) powered by Google Gemini with automatic resilient model fallback (`gemini-3.1-pro-preview` → `gemini-3-flash-preview`, `gemini-3.8-flash-tts` → `gemini-2.5-flash-preview-tts`).
  - Synthesizes 24 kHz mono PCM studio voiceovers wrapped into standard RIFF WAV and archived to Cloudflare R2.
- **Lazy Bilingual Game Translation & Programmatic Catalog Endpoints:**
  - `GET /games/{slug}?lang=es` returns immediately and schedules a Redis-locked background task to translate English IGDB `description` and `storyline` into Spanish (`description_es`, `storyline_es`) permanently cached in PostgreSQL.
  - Public paginated SEO endpoints under `/genres`, `/genres/{slug}/games`, `/platforms`, and `/platforms/{slug}/games`.
- **Asynchronous Data Layer:** Built on `SQLModel` and `SQLAlchemy` async engines (`asyncpg`) with schema migrations managed via `Alembic`.
- **Asynchronous Content Moderation & RabbitMQ:**
  - **Decoupled Publishing:** When a review with text is created or edited, it is published to a RabbitMQ quorum queue (`moderation.review.check`) with a Dead Letter Exchange (`moderation.dlx`) and delivery limit of 3.
  - **Internal Callback Endpoint:** A Go worker processes rules and Gemini AI evaluation, reporting back via `POST /internal/moderation/verdicts` with timing-safe service key verification (`X-Service-Key`).
  - **Self-Healing Sweeper:** A background reconciler runs periodically in the lifespan context using `SELECT ... FOR UPDATE SKIP LOCKED` to requeue unmoderated or stalled reviews.
  - **Optimistic Locking:** Reviews maintain `content_version` and `moderated_version` to prevent race conditions between author edits and moderator decisions (409 Conflict).
- **Administration & Appeals:**
  - Dedicated admin endpoints (`/admin/moderation/reviews/*`) protected by `AdminDep` (`user.role == 'admin'`).
  - Authors can appeal rejected reviews once per version (`POST /reviews/{id}/appeal`), moving them to manual review.
- **Resilient Caching & Rate Limiting (Redis):**
  - Implements a **Cache-Aside** strategy in `IgdbService` backed by `redis.asyncio` to cache Twitch OAuth2 tokens and search queries, designed with **Fail-Open** degradation so cache outages never interrupt core traffic.
  - Distributed IP and account-level rate limiting via `SlowAPI` + Redis on sensitive authentication and password-recovery endpoints.
- **Connection Lifecycle Management:** Manages persistent outbound HTTP connection pools (`httpx.AsyncClient`), Redis connections, RabbitMQ client, and SQLAlchemy engine disposal through FastAPI's `lifespan` context manager.
- **Authentication & Security:** Stateless JWT authentication (`access` + `refresh` tokens), Google OAuth 2.0 ID token verification, `bcrypt` password hashing, and SHA-256 hashed single-use password reset tokens with expiration windows.
- **External Integrations:**
  - **IGDB API v4 (Twitch / Amazon)** with automated OAuth2 client-credentials token rotation.
  - **Cloudflare R2 (S3-compatible)** via `boto3` for immutable profile photo storage.
  - **Resend** for asynchronous transactional emails dispatched via background tasks.

---

## Tech Stack

| Layer | Technology |
| :--- | :--- |
| **Framework** | FastAPI, Uvicorn |
| **Language & Runtime** | Python 3.14+ |
| **Database & ORM** | PostgreSQL 17, SQLModel, AsyncPG, Alembic |
| **Message Broker** | RabbitMQ 4 (Quorum Queues, DLX) via `aio-pika` |
| **Cache & Rate Limiting** | Redis 7, SlowAPI |
| **Authentication** | PyJWT, Bcrypt, Google OAuth2 |
| **External Game Data** | IGDB API v4 (Twitch OAuth2) |
| **Generative AI & TTS** | Google Gemini API (Structured JSON + Native 24 kHz TTS) |
| **Storage & Email** | Cloudflare R2 (`boto3`), Resend |
| **Package & Env Manager** | `uv` (Astral) |
| **Testing & Quality** | Pytest, Pytest-Asyncio, HTTPX, Ruff |
| **Containerization & CI** | Docker, Docker Compose, GitHub Actions |

---

## Project Structure

```text
pixel-reviews-api/
├── .github/workflows/       # Automated CI pipeline (Ruff, Alembic, Pytest)
├── migrations/              # Alembic database migration scripts
├── src/
│   ├── core/                # Application settings (Pydantic) and model mixins
│   ├── db/                  # Async SQLAlchemy engine and session dependency
│   ├── lib/                 # Shared utilities (rate limiter, password hashing, dates)
│   ├── modules/             # Domain modules (auth, reviews, review_moderation, users, games...)
│   ├── schemas/             # Shared & external response schemas
│   └── services/            # Infrastructure clients (broker, cache, igdb, mailer, storage)
├── templates/               # Transactional HTML email templates
├── tests/
│   ├── conftest.py          # Isolated test DB setup, fixtures, and dependency overrides
│   ├── integration/         # Integration tests (auth, reviews, moderation, appeals, admin)
│   └── unit/                # Unit tests for security, cache, and token lifecycles
├── Dockerfile               # Production container image definition
├── docker-compose.yml       # Full stack (PostgreSQL, Redis, RabbitMQ, API, Go Moderator)
├── main.py                  # FastAPI application entrypoint and lifespan configuration
└── pyproject.toml           # Project dependencies and tool configurations
```

---

## Getting Started

### Prerequisites

- **Docker** and **Docker Compose** (recommended for running PostgreSQL, Redis, RabbitMQ, API, and Go Moderator).
- **uv** (optional, for running Python commands locally): [Installation Guide](https://docs.astral.sh/uv/getting-started/installation/).

### 1. Clone the repository

```bash
git clone https://github.com/Yisusocanto/pixel-reviews-api.git
cd pixel-reviews-api
```

### 2. Configure environment variables

Copy the example environment file and populate your credentials:

```bash
cp .env.example .env
```

| Variable | Description | Default / Example |
| :--- | :--- | :--- |
| `ENVIRONMENT` | Runtime environment (`development` or `production`) | `development` |
| `DATABASE_URL` | Async PostgreSQL connection string | `postgresql+asyncpg://postgres:postgres@localhost:5432/pixel_reviews` |
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379/0` |
| `RABBITMQ_URL` | RabbitMQ connection URL | `amqp://pixel:pixel@localhost:5672` |
| `MODERATION_SERVICE_KEY` | Shared secret key for internal moderation callbacks | `openssl rand -hex 32` |
| `MODERATION_SWEEPER_INTERVAL_SECONDS` | Interval for sweeper reconciler (seconds) | `600` |
| `BACKEND_URL` | Public URL of this API | `http://localhost:8000` |
| `FRONTEND_URL` | Allowed CORS origin and base URL for reset links | `http://localhost:3000` |
| `JWT_SECRET_KEY` | Secret key for signing JWT tokens | `openssl rand -hex 32` |
| `TWITCH_CLIENT_ID` | Twitch Developer Client ID for IGDB v4 | `your_twitch_client_id` |
| `TWITCH_CLIENT_SECRET` | Twitch Developer Client Secret for IGDB v4 | `your_twitch_client_secret` |
| `GOOGLE_CLIENT_ID` | Google OAuth 2.0 Client ID | `your_client_id.apps.googleusercontent.com` |
| `GEMINI_API_KEY` | Google AI Studio API key for Social Studio & lazy ES translations | `AIza...` |
| `GEMINI_CREATIVE_MODEL` | Primary Gemini model for social scripts/carousels (auto-falls back on 404/429) | `gemini-3.1-pro-preview` |
| `GEMINI_TTS_MODEL` | Primary Gemini TTS model for 24 kHz studio voiceovers | `gemini-3.8-flash-tts` |
| `GEMINI_TTS_VOICE` | Prebuilt Gemini voice (`Orus`, `Puck`, `Kore`, `Charon`, `Aoede`) | `Orus` |
| `GEMINI_TRANSLATION_MODEL` | Gemini model used for lazy Spanish game copy translation | `gemini-3-flash-preview` |
| `RESEND_API_KEY` | API key from [resend.com](https://resend.com) | `re_...` |
| `CF_ACCOUNT_ID` | Cloudflare account identifier for R2 storage | `your_cloudflare_account_id` |
| `CF_BUCKET` | Cloudflare R2 bucket name | `your_r2_bucket_name` |
| `CF_PUBLIC_URL` | Public domain mapped to the R2 bucket | `https://cdn.example.com` |
| `CF_ACCESS_KEY_ID` | Cloudflare R2 S3 access key ID | `your_r2_access_key_id` |
| `CF_SECRET_ACCESS_KEY` | Cloudflare R2 S3 secret access key | `your_r2_secret_access_key` |

### 3. Run the stack with Docker Compose (Recommended)

Start PostgreSQL 17, Redis 7, RabbitMQ 4, the API, and the Go Moderator:

```bash
docker compose up -d
```

- **API Base URL:** `http://localhost:8000`
- **Interactive OpenAPI Docs (Swagger UI):** `http://localhost:8000/docs`
- **RabbitMQ Management Dashboard:** `http://localhost:15672` (user: `pixel`, pass: `pixel`)
- **Health Check Endpoint:** `http://localhost:8000/health`

### Alternative: Run the API natively with `uv`

If you run PostgreSQL, Redis, and RabbitMQ via Docker while running FastAPI natively:

```bash
docker compose up -d db redis rabbitmq
uv sync
uv run alembic upgrade head
uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

---

## Running Tests & Code Quality

The test suite runs against an isolated PostgreSQL database (`pixel_reviews_test`). External dependencies (Mailer, Storage, IGDB, RabbitMQ producer) are stubbed via `conftest.py`.

```bash
# Run the full unit and integration test suite
uv run pytest -v

# Run static linting checks
uv run ruff check

# Verify code formatting
uv run ruff format --check
```

---

## License

Distributed under the MIT License. See [`LICENSE`](./LICENSE) for more information.
