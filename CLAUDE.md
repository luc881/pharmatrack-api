# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
poetry install

# Run development server (auto-reload)
uvicorn pharmatrack.main:app --reload

# Run all tests
poetry run pytest

# Run a single test file
poetry run pytest tests/test_sales.py -v

# Run a single test by name
poetry run pytest tests/test_products.py::test_create_product -v

# Database migrations
alembic upgrade head
alembic revision --autogenerate -m "description"
alembic downgrade -1

# Dev-only scripts (require ENVIRONMENT=development)
poetry run reset-db          # truncates data and re-runs seeds
poetry run reset-migrations  # drops and regenerates the initial migration
```

## Architecture

### Module layout

Every domain module lives under `src/pharmatrack/models/<module>/` with two files:
- `orm.py` — SQLAlchemy ORM model (inherits `Base` from `db/session.py`)
- `schemas.py` — Pydantic v2 Create / Update / Response schemas

Routes live in `src/pharmatrack/api/routes/<module>.py` and are registered in `src/pharmatrack/api/v1.py`.

### Request lifecycle

```
Request → CORS middleware → rate limiter → router → permission dependency → endpoint → SQLAlchemy session → response
```

All endpoints are mounted under `/api/v1`. The `get_db` dependency (in `db/session.py`) yields a SQLAlchemy session that is closed in a `finally` block.

### Auth and permissions

- Login (`POST /api/v1/auth/token`) returns a short-lived **JWT access token** (HS256) and an opaque **refresh token** stored in `users.remember_token`.
- The JWT payload includes `sub` (email), `id`, `role`, and `permissions`.
- `utils/security.py` exposes `require_permission(name)`, a dependency factory. Per-resource permission lists are pre-built in `utils/permissions.py` (e.g. `CAN_READ_SALES`) and applied via `dependencies=` on router decorators.
- Permission checks hit the DB each request to verify the user still has the role and that the role has the required permission string (e.g. `"sales.read"`).

### Pagination

All list endpoints use the shared `paginate(query, params)` helper from `utils/pagination.py`. It receives a filtered `SQLAlchemy Query` and `PaginationParams` (defined in `models/products/schemas.py` and reused everywhere). Returns a dict matching `PaginatedResponse[T]`.

### Sale flow (stateful)

Sales follow a state machine: `draft → completed` (or `cancelled`, `refunded`, `partially_refunded`).

1. `POST /sales` creates a `DRAFT` sale with zero totals.
2. `POST /sales/{id}/sale-details` adds line items to the draft.
3. `POST /sales/{id}/complete` triggers:
   - `allocate_batches_for_sale_detail` (`utils/sales_stock.py`) — FIFO batch deduction from `product_batches.quantity`
   - `recalc_sale_totals` (`utils/sales_calculations.py`) — recomputes subtotal, tax, discount, total on the `Sale`
4. Refunds set status to `refunded` or `partially_refunded` automatically via the refund system; these values cannot be set manually via `PUT /sales`.

### Product model

Products support two sale modes controlled by `is_unit_sale`:
- **Pack** (`is_unit_sale=False`): has `base_unit_name` + `units_per_base` (e.g. "caja" of 10 "tabletas")
- **Unit** (`is_unit_sale=True`): sold individually; `base_unit_name` and `units_per_base` must be `None`

Validation is enforced in `utils/validators.py` (`validate_units_schema`, `validate_unit_name_for_sale`). Slugs are auto-generated from `title + sku` via `@model_validator`.

Stock is tracked via `ProductBatch` records (FIFO). `sale_batch_usage` records the per-batch deductions for traceability.

### Seeds (run at startup)

`main.py` lifespan calls `seeds/init_db.py` on every startup. Seeders are idempotent (they skip records that already exist). They populate permissions, roles, a superuser, branches, and a full product catalog.

### Rate limiting

SlowAPI (`utils/rate_limit.py`) decorates endpoints with `@limiter.limit(LIMIT_*)`. Constants: `LIMIT_READ = "60/minute"`, `LIMIT_SEARCH = "40/minute"`, `LIMIT_WRITE = "30/minute"`, auth is `"5/minute"`.

### Settings

`config.py` uses `pydantic-settings`. All settings come from `.env`. `settings.is_production` gates docs exposure, CORS wildcard, and dev scripts.

## Test setup

Tests require a real PostgreSQL database. The URL defaults to `postgresql://luc:1278972@localhost/pharmatrack_test` and can be overridden via a `.env.test` file.

`tests/conftest.py` creates tables once per session, then truncates all tables and resets identity sequences before each test. A single `Session` is shared between pytest fixtures and the FastAPI `TestClient` via a dependency override (`override_get_db` in `tests/utils.py`). This ensures fixtures and endpoint handlers see the same transaction.

Fixtures for each domain are in `tests/fixtures/<module>.py` and wildcard-imported into `conftest.py`.
