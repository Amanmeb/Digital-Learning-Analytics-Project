"""Tests for the three remaining fact-table ingestion endpoints.

Synthetic records cover: valid accept, duplicate detection, missing required fields,
out-of-range numerics, invalid date_id, and boundary values — per endpoint.
"""

VALID_SCHOOL_DAILY = {
    "school_id": "SCH001",
    "date_id": 20250101,
    "active_students": 120,
    "total_sessions": 85,
    "total_learning_minutes": 4200,
}

VALID_DEVICE_USAGE = {
    "device_usage_id": "DU001",
    "device_id": "D001",
    "school_id": "SCH001",
    "date_id": 20250101,
    "total_usage_minutes": 180,
    "session_count": 6,
}

VALID_SYNC_HEALTH = {
    "sync_health_id": "SH001",
    "device_id": "D001",
    "school_id": "SCH001",
    "date_id": 20250101,
    "status": "success",
}


class TestSchoolDailySummaryEndpoint:
    def test_valid_accepted(self, client, mock_db):
        response = client.post("/api/v1/ingest/school-daily-summary", json=VALID_SCHOOL_DAILY)
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "accepted"
        assert data["school_id"] == "SCH001"
        assert data["date_id"] == 20250101
        assert mock_db.commit.called

    def test_missing_school_id_quarantined(self, client, mock_db):
        bad = {k: v for k, v in VALID_SCHOOL_DAILY.items() if k != "school_id"}
        response = client.post("/api/v1/ingest/school-daily-summary", json=bad)
        assert response.status_code == 200
        assert response.json()["status"] == "quarantined"
        assert response.json()["reason"] == "validation_failed"

    def test_missing_active_students_quarantined(self, client, mock_db):
        bad = {k: v for k, v in VALID_SCHOOL_DAILY.items() if k != "active_students"}
        response = client.post("/api/v1/ingest/school-daily-summary", json=bad)
        assert response.status_code == 200
        assert response.json()["status"] == "quarantined"

    def test_negative_total_sessions_quarantined(self, client, mock_db):
        bad = {**VALID_SCHOOL_DAILY, "school_id": "SCH002", "total_sessions": -1}
        response = client.post("/api/v1/ingest/school-daily-summary", json=bad)
        assert response.status_code == 200
        assert response.json()["status"] == "quarantined"

    def test_negative_learning_minutes_quarantined(self, client, mock_db):
        bad = {**VALID_SCHOOL_DAILY, "school_id": "SCH003", "total_learning_minutes": -10}
        response = client.post("/api/v1/ingest/school-daily-summary", json=bad)
        assert response.status_code == 200
        assert response.json()["status"] == "quarantined"

    def test_invalid_date_id_bad_month_quarantined(self, client, mock_db):
        bad = {**VALID_SCHOOL_DAILY, "school_id": "SCH004", "date_id": 20251399}
        response = client.post("/api/v1/ingest/school-daily-summary", json=bad)
        assert response.status_code == 200
        assert response.json()["status"] == "quarantined"

    def test_duplicate_composite_pk_detected(self, client, mock_db):
        mock_db.execute.return_value.scalar.return_value = 1
        response = client.post("/api/v1/ingest/school-daily-summary", json=VALID_SCHOOL_DAILY)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "duplicate"
        assert data["school_id"] == "SCH001"
        assert data["date_id"] == 20250101

    def test_optional_fields_default_accepted(self, client, mock_db):
        record = {**VALID_SCHOOL_DAILY, "school_id": "SCH005"}
        response = client.post("/api/v1/ingest/school-daily-summary", json=record)
        assert response.status_code == 201
        assert response.json()["status"] == "accepted"

    def test_zero_counts_accepted(self, client, mock_db):
        record = {
            **VALID_SCHOOL_DAILY,
            "school_id": "SCH006",
            "active_students": 0,
            "total_sessions": 0,
            "total_learning_minutes": 0,
        }
        response = client.post("/api/v1/ingest/school-daily-summary", json=record)
        assert response.status_code == 201
        assert response.json()["status"] == "accepted"

    def test_all_optional_fields_provided(self, client, mock_db):
        record = {
            **VALID_SCHOOL_DAILY,
            "school_id": "SCH007",
            "active_teachers": 5,
            "total_ai_queries": 30,
            "total_content_accesses": 200,
            "offline_sessions": 10,
        }
        response = client.post("/api/v1/ingest/school-daily-summary", json=record)
        assert response.status_code == 201
        assert response.json()["status"] == "accepted"


class TestDeviceUsageEndpoint:
    def test_valid_accepted(self, client, mock_db):
        response = client.post("/api/v1/ingest/device-usage", json=VALID_DEVICE_USAGE)
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "accepted"
        assert data["device_usage_id"] == "DU001"
        assert mock_db.commit.called

    def test_missing_device_id_quarantined(self, client, mock_db):
        bad = {k: v for k, v in VALID_DEVICE_USAGE.items() if k != "device_id"}
        response = client.post("/api/v1/ingest/device-usage", json=bad)
        assert response.status_code == 200
        assert response.json()["status"] == "quarantined"
        assert response.json()["reason"] == "validation_failed"

    def test_missing_school_id_quarantined(self, client, mock_db):
        bad = {k: v for k, v in VALID_DEVICE_USAGE.items() if k != "school_id"}
        response = client.post("/api/v1/ingest/device-usage", json=bad)
        assert response.status_code == 200
        assert response.json()["status"] == "quarantined"

    def test_negative_usage_minutes_quarantined(self, client, mock_db):
        bad = {**VALID_DEVICE_USAGE, "device_usage_id": "DU002", "total_usage_minutes": -5}
        response = client.post("/api/v1/ingest/device-usage", json=bad)
        assert response.status_code == 200
        assert response.json()["status"] == "quarantined"

    def test_negative_session_count_quarantined(self, client, mock_db):
        bad = {**VALID_DEVICE_USAGE, "device_usage_id": "DU003", "session_count": -1}
        response = client.post("/api/v1/ingest/device-usage", json=bad)
        assert response.status_code == 200
        assert response.json()["status"] == "quarantined"

    def test_invalid_date_id_too_short_quarantined(self, client, mock_db):
        bad = {**VALID_DEVICE_USAGE, "device_usage_id": "DU004", "date_id": 2025}
        response = client.post("/api/v1/ingest/device-usage", json=bad)
        assert response.status_code == 200
        assert response.json()["status"] == "quarantined"

    def test_duplicate_detected(self, client, mock_db):
        mock_db.execute.return_value.scalar.return_value = 1
        response = client.post("/api/v1/ingest/device-usage", json=VALID_DEVICE_USAGE)
        assert response.status_code == 200
        assert response.json()["status"] == "duplicate"
        assert response.json()["device_usage_id"] == "DU001"

    def test_zero_values_accepted(self, client, mock_db):
        record = {
            **VALID_DEVICE_USAGE,
            "device_usage_id": "DU005",
            "total_usage_minutes": 0,
            "session_count": 0,
        }
        response = client.post("/api/v1/ingest/device-usage", json=record)
        assert response.status_code == 201
        assert response.json()["status"] == "accepted"


class TestSyncHealthEndpoint:
    def test_valid_accepted(self, client, mock_db):
        response = client.post("/api/v1/ingest/sync-health", json=VALID_SYNC_HEALTH)
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "accepted"
        assert data["sync_health_id"] == "SH001"
        assert mock_db.commit.called

    def test_missing_device_id_quarantined(self, client, mock_db):
        bad = {k: v for k, v in VALID_SYNC_HEALTH.items() if k != "device_id"}
        response = client.post("/api/v1/ingest/sync-health", json=bad)
        assert response.status_code == 200
        assert response.json()["status"] == "quarantined"
        assert response.json()["reason"] == "validation_failed"

    def test_missing_status_quarantined(self, client, mock_db):
        bad = {k: v for k, v in VALID_SYNC_HEALTH.items() if k != "status"}
        response = client.post("/api/v1/ingest/sync-health", json=bad)
        assert response.status_code == 200
        assert response.json()["status"] == "quarantined"

    def test_empty_status_quarantined(self, client, mock_db):
        bad = {**VALID_SYNC_HEALTH, "sync_health_id": "SH002", "status": ""}
        response = client.post("/api/v1/ingest/sync-health", json=bad)
        assert response.status_code == 200
        assert response.json()["status"] == "quarantined"

    def test_negative_records_synced_quarantined(self, client, mock_db):
        bad = {**VALID_SYNC_HEALTH, "sync_health_id": "SH003", "records_synced": -1}
        response = client.post("/api/v1/ingest/sync-health", json=bad)
        assert response.status_code == 200
        assert response.json()["status"] == "quarantined"

    def test_invalid_date_id_bad_day_quarantined(self, client, mock_db):
        bad = {**VALID_SYNC_HEALTH, "sync_health_id": "SH004", "date_id": 20250132}
        response = client.post("/api/v1/ingest/sync-health", json=bad)
        assert response.status_code == 200
        assert response.json()["status"] == "quarantined"

    def test_duplicate_detected(self, client, mock_db):
        mock_db.execute.return_value.scalar.return_value = 1
        response = client.post("/api/v1/ingest/sync-health", json=VALID_SYNC_HEALTH)
        assert response.status_code == 200
        assert response.json()["status"] == "duplicate"
        assert response.json()["sync_health_id"] == "SH001"

    def test_optional_sync_duration_omitted(self, client, mock_db):
        record = {**VALID_SYNC_HEALTH, "sync_health_id": "SH005"}
        response = client.post("/api/v1/ingest/sync-health", json=record)
        assert response.status_code == 201
        assert response.json()["status"] == "accepted"

    def test_optional_fields_provided(self, client, mock_db):
        record = {
            **VALID_SYNC_HEALTH,
            "sync_health_id": "SH006",
            "records_synced": 50,
            "sync_duration_secs": 30,
        }
        response = client.post("/api/v1/ingest/sync-health", json=record)
        assert response.status_code == 201
        assert response.json()["status"] == "accepted"

    def test_zero_records_synced_accepted(self, client, mock_db):
        record = {**VALID_SYNC_HEALTH, "sync_health_id": "SH007", "records_synced": 0}
        response = client.post("/api/v1/ingest/sync-health", json=record)
        assert response.status_code == 201
        assert response.json()["status"] == "accepted"
