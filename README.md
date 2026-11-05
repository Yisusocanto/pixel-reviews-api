# Pixel Reviews API

[![CI](https://github.com/Yisusocanto/pixel-reviews-api/actions/workflows/ci.yml/badge.svg)](https://github.com/Yisusocanto/pixel-reviews-api/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](./LICENSE)
[![Python](https://img.shields.io/badge/Python-3.14-3776AB.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.141-009688.svg)](https://fastapi.tiangolo.com/)

RESTful backend service for **Pixel Reviews**, an open-source video game discovery, review, and cataloging platform.

> **Version Notice (v2):** This repository contains the second generation of the Pixel Reviews backend, rebuilt from the ground up with an asynchronous architecture, modular domain separation, Redis caching, and automated testing. The first version of the project is now deprecated and archived for historical reference at [Pixel Reviews v1 (Deprecated)](https://github.com/Yisusocanto/pixel_reviews).
>
> **Companion Repository:** The Next.js frontend application is maintained at [pixel-reviews-frontend](https://github.com/Yisusocanto/pixel-reviews-frontend).

---

## Architecture & Engineering Highlights

- **Domain-Driven Modular Structure:** Organized by domain (`auth`, `users`, `games`, `reviews`, `comments`, `likes`, `wishlists`, `developers`, `publishers`, `genres`, `platforms`, `stores`) using a strict `Router -> Service -> Repository` layered pattern and FastAPI dependency injection.
- **Asynchronous Data Layer:** Built on `SQLModel` and `SQLAlchemy` async engines (`asyncpg`) with schema migrations managed via `Alembic`.
- **Resilient Caching & Rate Limiting (Redis):**
  - Implements a **Cache-Aside** strategy in `RawgService` backed by `redis.asyncio` to reduce external API latency and preserve rate-limit quotas, designed with **Fail-Open** degradation so cache outages never interrupt core traffic.
  - Distributed IP and account-level rate limiting via `SlowAPI` + Redis on sensitive authentication and password-recovery endpoints.
- **Connection Lifecycle Management:** Manages persistent outbound HTTP connection pools (`httpx.AsyncClient`), Redis connections, and SQLAlchemy engine disposal through FastAPI's `lifespan` context manager.
- **Authentication & Security:** Stateless JWT authentication (`access` + `refresh` tokens), Google OAuth 2.0 ID token verification, `bcrypt` password hashing, and SHA-256 hashed single-use password reset tokens with expiration windows.
- **External Integrations:**
  - **RAWG Video Games Database API** for on-demand game search, metadata hydration, and canonical slug resolution.
  - **Cloudflare R2 (S3-compatible)** via `boto3` for immutable profile photo storage with automatic orphan cleanup.
  - **Resend** for asynchronous transactional emails dispatched via background tasks.

---

## Tech Stack

| Layer | Technology |
| :--- | :--- |
| **Framework** | FastAPI, Uvicorn |
| **Language & Runtime** | Python 3.14+ |
| **Database & ORM** | PostgreSQL 17, SQLModel, AsyncPG, Alembic |
| **Cache & Rate Limiting** | Redis 7, SlowAPI |
| **Authentication** | PyJWT, Bcrypt, Google OAuth2 |
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
│   ├── modules/             # Domain modules (router, service, repository, models, schemas)
│   ├── schemas/             # External API response schemas
│   └── services/            # Infrastructure clients (cache, mailer, rawg, storage)
├── templates/               # Transactional HTML email templates
├── tests/
│   ├── conftest.py          # Isolated test DB setup, fixtures, and dependency overrides
│   ├── integration/         # End-to-end API route and database integration tests
│   └── unit/                # Isolated unit tests for security, caching, and clients
├── Dockerfile               # Production container image definition
├── docker-compose.yml       # Local development stack (PostgreSQL 17, Redis 7, API)
├── main.py                  # FastAPI application entrypoint and lifespan configuration
└── pyproject.toml           # Project dependencies and tool configurations
```

---

## Getting Started

### Prerequisites

- **Docker** and **Docker Compose** (recommended for running PostgreSQL, Redis, and the API).
- **uv** (optional, required if running Python commands directly on your host machine): [Installation Guide](https://docs.astral.sh/uv/getting-started/installation/).

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
| `BACKEND_URL` | Public URL of this API | `http://localhost:8000` |
| `FRONTEND_URL` | Allowed CORS origin and base URL for password reset links | `http://localhost:3000` |
| `JWT_SECRET_KEY` | Secret key for signing JWT tokens (required in production) | `openssl rand -hex 32` |
| `API_RAWG_KEY` | API key from [rawg.io/apidocs](https://rawg.io/apidocs) | `your_rawg_api_key` |
| `GOOGLE_CLIENT_ID` | Google OAuth 2.0 Client ID | `your_client_id.apps.googleusercontent.com` |
| `RESEND_API_KEY` | API key from [resend.com](https://resend.com) | `re_...` |
| `CF_ACCOUNT_ID` | Cloudflare account identifier for R2 storage | `your_cloudflare_account_id` |
| `CF_BUCKET` | Cloudflare R2 bucket name | `your_r2_bucket_name` |
| `CF_PUBLIC_URL` | Public domain mapped to the R2 bucket | `https://cdn.example.com` |
| `CF_ACCESS_KEY_ID` | Cloudflare R2 S3 access key ID | `your_r2_access_key_id` |
| `CF_SECRET_ACCESS_KEY` | Cloudflare R2 S3 secret access key | `your_r2_secret_access_key` |

### 3. Run the stack with Docker Compose (Recommended)

Start PostgreSQL 17, Redis 7, and the FastAPI server with automatic database migrations and live hot-reload:

```bash
docker compose up -d
```

- **API Base URL:** `http://localhost:8000`
- **Interactive OpenAPI Docs (Swagger UI):** `http://localhost:8000/docs`
- **Health Check Endpoint:** `http://localhost:8000/health`

To follow the API logs in real time:

```bash
docker compose logs -f api
```

### Alternative: Run the API natively with `uv`

If you prefer running only PostgreSQL and Redis in Docker while executing FastAPI directly on your host machine:

```bash
docker compose up -d db redis
uv sync
uv run alembic upgrade head
uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

---

## Running Tests & Code Quality

The test suite uses an isolated PostgreSQL database (`pixel_reviews_test`) created automatically on the running PostgreSQL instance, ensuring development data in `pixel_reviews` is never modified or erased. External services (`MailerService`, `StorageService`, `RawgService`) are replaced via FastAPI `dependency_overrides` and mock transports.

Make sure the `db` container is running (`docker compose up -d db`), then execute:

```bash
# Run the full unit and integration test suite
uv run pytest -v

# Run static linting checks
uv run ruff check

# Verify code formatting
uv run ruff format --check
```

---

## Contributing

Contributions, bug reports, and feature requests are welcome. To keep the commit history and review process consistent, please follow this workflow:

1. **Fork and clone** the repository.
2. **Create a branch** from `main` using semantic prefixes:
   - `feat/<short-description>` for new features
   - `fix/<short-description>` for bug fixes
   - `perf/<short-description>` for performance improvements
   - `refactor/<short-description>` for internal code restructuring
   - `test/<short-description>` for adding or updating tests
   - `chore/<short-description>` or `docs/<short-description>` for maintenance and documentation
3. **Write tests** covering any new business logic or endpoints.
4. **Verify quality checks locally** before committing:
   ```bash
   uv run ruff format
   uv run ruff check
   uv run pytest -v
   ```
5. **Commit your changes** following the [Conventional Commits](https://www.conventionalcommits.org/) specification (e.g., `feat(reviews): add pagination metadata to user reviews`).
6. **Open a Pull Request** against `main`. All GitHub Actions CI checks (`Lint, Migrations & Tests`) must pass before merging.

---

## License

Distributed under the MIT License. See [`LICENSE`](./LICENSE) for more information.
