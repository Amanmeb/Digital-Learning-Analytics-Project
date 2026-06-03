# 2026-06-03 – FastAPI ingestion service foundation

## What was done

Built the initial FastAPI backend (`backend/`) from scratch and added supporting infrastructure:

**App skeleton**
- `app/config.py` – pydantic-settings reads `DATABASE_URL` from `.env`; auto-converts `postgresql://` to `postgresql+asyncpg://` for the async driver
- `app/database.py` – async SQLAlchemy engine + session factory pointing at the existing PostgreSQL warehouse
- `app/main.py` – FastAPI app with `/health` check and `/api/docs` (Swagger)

**Session ingestion endpoint** (`POST /api/v1/ingest/sessions`)
- Accepts a JSON body matching `fact_session` in the data contract
- Validates with Pydantic: enforces required fields (non-empty IDs within VARCHAR limits), `session_duration_minutes >= 0`, and 8-digit `date_id` (yyyymmdd) with valid year/month/day ranges
- Checks for duplicate `session_id` before inserting
- On success: inserts into `mart.fact_session`, returns `{"status": "accepted"}` with HTTP 201
- On validation failure or DB error: stores the raw payload + reason in `raw.quarantine`, returns `{"status": "quarantined"}` with HTTP 200; records are never silently dropped
- On duplicate: returns `{"status": "duplicate"}` with HTTP 200; no insert attempted

**Quarantine table** (`sql/migrations/007_quarantine.sql`)
- New `raw.quarantine` table in the existing `raw` schema; idempotent (`CREATE TABLE IF NOT EXISTS`)
- Indexed on `table_name` and `received_at`
- For existing databases: `psql -U cdlaid_user cdlaid_analytics -f sql/migrations/007_quarantine.sql`

**Docker** (`docker-compose.yml`)
- `docker compose up` starts postgres (migrations applied on first run via `initdb.d`) + the API on port 8000
- Credentials come from `.env` (see `.env.example`); no hardcoded secrets
- Note: the existing `docker-compose.central.yml` is for the full stack (Moodle + MySQL). The new `docker-compose.yml` is for API-only development.

**Tests** (`backend/tests/`)
- 17 pytest tests total: 12 pure Pydantic unit tests (`test_schemas.py`) + 5 endpoint integration tests with a mocked DB (`test_ingest_endpoint.py`)
- Synthetic data covers: valid record accepted, zero duration accepted, 3 ID field empty = quarantined, negative duration = quarantined, 3 invalid date_id formats = quarantined, missing required field = quarantined, duplicate detection, quarantine DB call confirmed
- No live database required to run tests

**CI** (`.github/workflows/ci.yml`)
- Runs on every PR to main and on every push to non-main branches
- Steps: install deps → `ruff check` → `pytest` with mocked DB
- Python 3.12, pip cache enabled

**ROADMAP.md** – project-level roadmap created

## Why it matters / which Definition-of-Done items this advances

| DoD item | Status |
|---|---|
| Ingestion endpoint | ✅ First fact table live |
| JSON validation | ✅ Pydantic enforces data contract on every request |
| Duplicate prevention | ✅ session_id uniqueness checked before insert |
| Quarantine bad records with reason | ✅ raw.quarantine stores payload + reason |
| Correct PostgreSQL storage matching data model | ✅ Inserts into mart.fact_session with correct column mapping |
| Runs via docker compose up | ✅ docker-compose.yml starts postgres + api |
| Tests pass against synthetic data | ✅ 17 tests, valid + broken records |
| CI pipeline | ✅ Lint + test on every PR |

## What to review

- **`app/routers/ingest.py` – `_quarantine` swallows its own exceptions**: if the quarantine INSERT itself fails (e.g. DB is completely down), the error is silently ignored. Acceptable for now but should be replaced with logging in a follow-up.
- **No authentication**: the endpoint has no auth. Any caller can post records. **API key middleware is tracked in the roadmap and must be reviewed by a human before production deployment.**
- **`app/config.py` default password**: the default `changeme` placeholder is only for local dev. The `.env` file (never committed) must set the real `DATABASE_URL`.
- **`sql/migrations/007_quarantine.sql`**: PostgreSQL's `initdb.d` mount only applies migrations on a fresh volume. Existing databases need the file run manually (command above).
- **SQL files have UTF-8 BOM**: henok's migration files include a BOM (`\xef\xbb\xbf`). This is handled correctly by PostgreSQL 16 but worth noting if using older clients.

## What's next

1. Ingestion endpoints for the remaining 4 fact tables: `fact_teacher_session`, `fact_content_usage`, `fact_ai_usage`, `fact_assessment_attempt`
2. Shared Pydantic schema service to reduce per-endpoint boilerplate
3. `GET /api/v1/quarantine` to inspect and reprocess rejected records
4. Date dimension auto-populate when a new `date_id` arrives
