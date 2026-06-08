# 2026-06-08 – Core fact-table ingestion endpoints

## What was done

Added four new POST endpoints to the FastAPI ingestion service, completing the core
fact-table coverage for the analytics platform:

| Endpoint | Table |
|---|---|
| `POST /api/v1/ingest/teacher-sessions` | `mart.fact_teacher_session` |
| `POST /api/v1/ingest/content-usage` | `mart.fact_content_usage` |
| `POST /api/v1/ingest/ai-usage` | `mart.fact_ai_usage` |
| `POST /api/v1/ingest/assessment-attempts` | `mart.fact_assessment_attempt` |

Every endpoint follows the same contract as the existing `/ingest/sessions`:
- Pydantic validates the payload against the data contract before any DB write
- Duplicate primary keys are detected and returned as `{"status": "duplicate"}` (HTTP 200)
- Invalid or malformed records are written to `raw.quarantine` with the rejection reason,
  never silently dropped; the caller gets `{"status": "quarantined"}` (HTTP 200)
- Valid records are inserted and confirmed with `{"status": "accepted"}` (HTTP 201)

**Schema additions** (`backend/app/models/schemas.py`)

- Added `FactTeacherSessionIn`, `FactContentUsageIn`, `FactAiUsageIn`,
  `FactAssessmentAttemptIn` — each field matches the data contract exactly
- Added a `DateId = Annotated[int, AfterValidator(_check_date_id)]` type so the
  8-digit yyyymmdd date validation is defined once and shared across all four new
  schemas; the existing `FactSessionIn` is left unchanged with its own validator
- Score field on `FactAssessmentAttemptIn` enforces `ge=0, le=100` (rejects 101, rejects -1)

**Router additions** (`backend/app/routers/ingest.py`)

- Added `_ingest_fact` helper that owns the duplicate-check → insert → error/quarantine
  flow; the four new endpoint functions handle only validation + call the helper.
  `mart_table` and `pk_col` are hardcoded by the caller, not user-supplied, so the
  f-string SELECT is not an injection risk
- Existing `ingest_session` endpoint is untouched

**DB column mapping notes**

The actual PostgreSQL schema (migration `003_facts.sql`) uses `date_key` (not `date_id`)
and uses `attempt_id` as the PK column for `fact_assessment_attempt` (the data contract
calls it `assessment_attempt_id`). The Pydantic models use the contract names; the INSERT
statements map to the actual column names. This is the same approach used by the original
`fact_session` endpoint.

**Tests** (`backend/tests/test_ingest_core_facts.py`)

- 31 new pytest tests across 4 classes (one per endpoint)
- Synthetic records cover: valid accept, boundary values (score=0, score=100,
  duration=0, time=0), missing required field, negative numerics, out-of-range
  score, invalid date_id (too short, bad month, bad day), empty string, duplicate
- All 50 tests (31 new + 19 existing) pass; ruff reports no lint errors

## Why it matters / which Definition-of-Done items this advances

| DoD item | Status |
|---|---|
| Ingestion endpoint | ✅ Now covers 5 of 9 fact tables |
| JSON validation | ✅ Pydantic enforces contract on all 5 endpoints |
| Duplicate prevention | ✅ PK uniqueness checked on all 5 endpoints |
| Quarantine bad records with reason | ✅ All 5 endpoints quarantine with stored reason |
| Correct PostgreSQL storage matching data model | ✅ Column mapping verified against 003_facts.sql |
| Tests pass against synthetic data | ✅ 50 tests total, valid + broken records |

## PR

See pull request for diff. No authentication is added yet — that is tracked in Week 7-8.

## What to review

- **`_ingest_fact` helper f-string SELECT**: `mart_table` and `pk_col` are hardcoded
  per-endpoint, not derived from user input, so injection is not possible. Confirm
  this is acceptable or request a whitelist approach.
- **`assessment_attempt_id` → `attempt_id` mapping**: the data contract names the PK
  `assessment_attempt_id` but the DB column is `attempt_id`. The response body uses
  `attempt_id` (the DB name). If the contract is authoritative, the migration column
  should be renamed — worth aligning with henok.
- **`completion_status` is required**: the DB columns are nullable, but the Pydantic
  schemas require it. Records without a completion_status will be quarantined. This
  is stricter than the DB allows; relax to `Optional[str]` if needed.
- **No auth**: all four new endpoints are open. Auth is intentionally deferred to
  Week 7-8 and must be reviewed by a human before production.

## What's next

1. `fact_school_daily_summary`, `fact_device_usage`, `fact_sync_health` endpoints
2. Bulk batch endpoint (`POST /api/v1/ingest/batch`) for efficient multi-record ingestion
3. Date dimension auto-populate — insert missing `date_id` rows into `mart.dim_date`
   automatically so FK constraints don't reject valid dates
4. Quarantine review endpoint (`GET /api/v1/quarantine`) so operators can inspect
   and reprocess rejected records
