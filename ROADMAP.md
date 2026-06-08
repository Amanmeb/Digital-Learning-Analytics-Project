# CDLAID Analytics Platform – Roadmap

12-week backend build for the Camara Education Ethiopia Phase 2 digital learning analytics platform.

## Status key
- ✅ Done (merged to main)
- 🔄 In progress (open PR)
- ⬜ Not started

---

## Week 1–2: Foundation

### Data Engineering / Schema (henok)
- ✅ PostgreSQL warehouse schema: 16 dimension tables, 9 fact tables, indexes, RLS
- ✅ Moodle + MySQL in Docker (`docker-compose.central.yml`)

### Backend / API (Bityana)
- ✅ FastAPI ingestion service skeleton + `POST /api/v1/ingest/sessions` endpoint
- ✅ Quarantine table (`raw.quarantine`) for malformed records
- ✅ CI pipeline: ruff lint + pytest on every PR

## Week 3–4: Core Ingestion

- 🔄 Ingestion endpoints for remaining fact tables: `fact_teacher_session`, `fact_content_usage`, `fact_ai_usage`, `fact_assessment_attempt`
- ⬜ Bulk batch ingestion endpoint (`POST /api/v1/ingest/batch`)
- ⬜ `fact_school_daily_summary`, `fact_device_usage`, `fact_sync_health` endpoints
- ⬜ Date dimension auto-populate for new date_ids

## Week 5–6: Reliability & Ops

- ⬜ Quarantine review endpoint (`GET /api/v1/quarantine`) + reprocess
- ⬜ Structured logging to `ops.system_log`
- ⬜ Sync health status endpoint
- ⬜ Integration tests against real PostgreSQL (docker-compose test profile)

## Week 7–8: Auth & Docs

- ⬜ API key middleware — **SECURITY, needs human review before production**
- ⬜ Per-school request scoping
- ⬜ OpenAPI documentation complete with examples
- ⬜ Dimension reference data CRUD (read-only at minimum)

## Week 9–12: Hardening & Integration

- ⬜ Performance testing under realistic load
- ⬜ BI Dashboard integration points (coordinate with dashboard volunteer)
- ⬜ Edge sync agent integration (coordinate with edge volunteer)
- ⬜ Production deployment checklist and secrets management
