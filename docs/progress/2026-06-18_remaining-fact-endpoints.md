# 2026-06-18 – Remaining fact-table ingestion endpoints

## What was done

Added three POST endpoints to the FastAPI ingestion service, completing ingestion
coverage for all nine fact tables defined in the warehouse schema:

| Endpoint | Table | PK type |
|---|---|---|
| `POST /api/v1/ingest/school-daily-summary` | `mart.fact_school_daily_summary` | Composite (school_id + date_key) |
| `POST /api/v1/ingest/device-usage` | `mart.fact_device_usage` | Single (device_usage_id) |
| `POST /api/v1/ingest/sync-health` | `mart.fact_sync_health` | Single (sync_health_id) |

All three follow the same contract as every existing endpoint:
- Pydantic validates the payload before any DB write
- Duplicate records return `{"status": "duplicate"}` (HTTP 200)
- Invalid or malformed records go to `raw.quarantine` with the rejection reason,
  never silently dropped; caller receives `{"status": "quarantined"}` (HTTP 200)
- Valid records inserted and confirmed with `{"status": "accepted"}` (HTTP 201)

**Schema additions** (`backend/app/models/schemas.py`)

- `FactSchoolDailySummaryIn` — composite-PK table; `active_students`,
  `total_sessions`, `total_learning_minutes` are required (data contract); the four
  additional DB columns (`active_teachers`, `total_ai_queries`, `total_content_accesses`,
  `offline_sessions`) are optional with defaults of 0 so they can be omitted without
  quarantining the record
- `FactDeviceUsageIn` — requires `device_usage_id`, `device_id`, `school_id`,
  `date_id`, `total_usage_minutes`, `session_count`; all counts validated `ge=0`
- `FactSyncHealthIn` — requires `sync_health_id`, `device_id`, `school_id`, `date_id`,
  `status`; `records_synced` optional (default 0), `sync_duration_secs` nullable
  matching the DB column

**Router additions** (`backend/app/routers/ingest.py`)

- `ingest_school_daily_summary` is handled inline (like `ingest_session`) because its
  composite PK requires a two-column `WHERE school_id = :s AND date_key = :d` check
  that `_ingest_fact` does not support; the response body includes both `school_id`
  and `date_id` so callers can identify the duplicate or accepted record
- `ingest_device_usage` and `ingest_sync_health` use the existing `_ingest_fact` helper

**DB column mapping**

The warehouse schema uses `date_key` (not `date_id`). Pydantic models use the
contract name `date_id`; INSERT statements map to the actual `date_key` column.
Consistent with previous endpoints.

**Tests** (`backend/tests/test_ingest_remaining_facts.py`)

- 28 new pytest tests across 3 classes
- Synthetic records cover: valid accept, missing required field, negative numeric
  values, invalid date_id (bad month, bad day, too short), composite-PK duplicate,
  single-PK duplicate, boundary zeros, optional fields omitted, optional fields
  provided
- All tests use the existing `conftest.py` mock_db fixture

## Why it matters / which Definition-of-Done items this advances

| DoD item | Status |
|---|---|
| Ingestion endpoint | ✅ Now covers all 9 fact tables |
| JSON validation | ✅ Pydantic enforces contract on all 9 endpoints |
| Duplicate prevention | ✅ PK uniqueness checked on all 9 endpoints |
| Quarantine bad records with reason | ✅ All 9 endpoints quarantine with stored reason |
| Correct PostgreSQL storage matching data model | ✅ Column mapping verified against 003_facts.sql |
| Tests pass against synthetic data | ✅ 78 tests total (50 existing + 28 new) |

## What to review

- **Composite PK duplicate check**: the `school-daily-summary` endpoint uses a
  plain `SELECT 1 … WHERE school_id = :s AND date_key = :d` inline. No f-string
  injection risk (both params are bound), but confirm this is the right approach
  versus an `ON CONFLICT DO NOTHING` upsert if the summary data should be updated
  rather than rejected as a duplicate.
- **Optional vs required on `FactSchoolDailySummaryIn`**: `active_teachers`,
  `total_ai_queries`, `total_content_accesses`, `offline_sessions` are optional
  (default 0) so that callers sending only the contract-mandated fields are not
  quarantined. If these should always be required, switch `Field(0, …)` to
  `Field(..., …)`.
- **`sync_duration_secs` is nullable**: set to `None` when omitted. Callers that
  cannot measure sync duration can omit the field safely.
- **No auth**: all endpoints remain open. Auth is intentionally deferred to Week 7-8
  and must be reviewed by a human before production.

## What's next

1. Bulk batch endpoint (`POST /api/v1/ingest/batch`) — accept a list of records for
   one table per request to reduce HTTP round-trips from edge devices
2. Date dimension auto-populate — insert missing `date_id` rows into `mart.dim_date`
   automatically so FK constraints never reject valid new dates
3. Quarantine review endpoint (`GET /api/v1/quarantine`) — let operators inspect and
   reprocess rejected records without touching the DB directly
4. Integration tests against real PostgreSQL via a docker-compose test profile
