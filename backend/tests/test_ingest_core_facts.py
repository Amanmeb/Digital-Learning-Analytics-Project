"""Tests for the four core fact-table ingestion endpoints added in week 3-4.

Synthetic records cover: valid accept, duplicate detection, missing required field,
out-of-range numeric value, and invalid date_id — for each endpoint.
"""

VALID_TEACHER_SESSION = {
    "teacher_session_id": "TSS001",
    "teacher_id": "TCH001",
    "school_id": "SCH001",
    "device_id": "D001",
    "platform_id": "PLT001",
    "date_id": 20250101,
    "session_duration_minutes": 60,
    "is_offline": False,
}

VALID_CONTENT_USAGE = {
    "content_usage_id": "CU001",
    "session_id": "SES001",
    "content_id": "CNT001",
    "platform_id": "PLT001",
    "date_id": 20250101,
    "time_spent_minutes": 30,
    "completion_status": "completed",
}

VALID_AI_USAGE = {
    "ai_usage_id": "AIU001",
    "session_id": "SES001",
    "ai_service_id": "AIS001",
    "subject_id": "SUB001",
    "date_id": 20250101,
    "query_count": 5,
    "time_spent_minutes": 15,
    "query_type": "question_answering",
}

VALID_ASSESSMENT = {
    "assessment_attempt_id": "ATT001",
    "student_id": "STU001",
    "content_id": "CNT001",
    "date_id": 20250101,
    "score": 85,
    "completion_status": "completed",
}


class TestTeacherSessionEndpoint:
    def test_valid_accepted(self, client, mock_db):
        response = client.post("/api/v1/ingest/teacher-sessions", json=VALID_TEACHER_SESSION)
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "accepted"
        assert data["teacher_session_id"] == "TSS001"
        assert mock_db.commit.called

    def test_missing_teacher_id_quarantined(self, client, mock_db):
        bad = {k: v for k, v in VALID_TEACHER_SESSION.items() if k != "teacher_id"}
        response = client.post("/api/v1/ingest/teacher-sessions", json=bad)
        assert response.status_code == 200
        assert response.json()["status"] == "quarantined"
        assert response.json()["reason"] == "validation_failed"

    def test_negative_duration_quarantined(self, client, mock_db):
        bad = {**VALID_TEACHER_SESSION, "teacher_session_id": "TSS002",
               "session_duration_minutes": -1}
        response = client.post("/api/v1/ingest/teacher-sessions", json=bad)
        assert response.status_code == 200
        assert response.json()["status"] == "quarantined"

    def test_invalid_date_id_too_short_quarantined(self, client, mock_db):
        bad = {**VALID_TEACHER_SESSION, "teacher_session_id": "TSS003", "date_id": 2025}
        response = client.post("/api/v1/ingest/teacher-sessions", json=bad)
        assert response.status_code == 200
        assert response.json()["status"] == "quarantined"

    def test_invalid_date_id_bad_month_quarantined(self, client, mock_db):
        bad = {**VALID_TEACHER_SESSION, "teacher_session_id": "TSS004", "date_id": 20251399}
        response = client.post("/api/v1/ingest/teacher-sessions", json=bad)
        assert response.status_code == 200
        assert response.json()["status"] == "quarantined"

    def test_duplicate_detected(self, client, mock_db):
        mock_db.execute.return_value.scalar.return_value = 1
        response = client.post("/api/v1/ingest/teacher-sessions", json=VALID_TEACHER_SESSION)
        assert response.status_code == 200
        assert response.json()["status"] == "duplicate"

    def test_zero_duration_accepted(self, client, mock_db):
        record = {**VALID_TEACHER_SESSION, "teacher_session_id": "TSS005",
                  "session_duration_minutes": 0}
        response = client.post("/api/v1/ingest/teacher-sessions", json=record)
        assert response.status_code == 201
        assert response.json()["status"] == "accepted"


class TestContentUsageEndpoint:
    def test_valid_accepted(self, client, mock_db):
        response = client.post("/api/v1/ingest/content-usage", json=VALID_CONTENT_USAGE)
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "accepted"
        assert data["content_usage_id"] == "CU001"

    def test_missing_session_id_quarantined(self, client, mock_db):
        bad = {k: v for k, v in VALID_CONTENT_USAGE.items() if k != "session_id"}
        response = client.post("/api/v1/ingest/content-usage", json=bad)
        assert response.status_code == 200
        assert response.json()["status"] == "quarantined"
        assert response.json()["reason"] == "validation_failed"

    def test_missing_content_id_quarantined(self, client, mock_db):
        bad = {k: v for k, v in VALID_CONTENT_USAGE.items() if k != "content_id"}
        response = client.post("/api/v1/ingest/content-usage", json=bad)
        assert response.status_code == 200
        assert response.json()["status"] == "quarantined"

    def test_negative_time_spent_quarantined(self, client, mock_db):
        bad = {**VALID_CONTENT_USAGE, "content_usage_id": "CU002", "time_spent_minutes": -10}
        response = client.post("/api/v1/ingest/content-usage", json=bad)
        assert response.status_code == 200
        assert response.json()["status"] == "quarantined"

    def test_invalid_date_id_quarantined(self, client, mock_db):
        bad = {**VALID_CONTENT_USAGE, "content_usage_id": "CU003", "date_id": 99999999}
        response = client.post("/api/v1/ingest/content-usage", json=bad)
        assert response.status_code == 200
        assert response.json()["status"] == "quarantined"

    def test_duplicate_detected(self, client, mock_db):
        mock_db.execute.return_value.scalar.return_value = 1
        response = client.post("/api/v1/ingest/content-usage", json=VALID_CONTENT_USAGE)
        assert response.status_code == 200
        assert response.json()["status"] == "duplicate"

    def test_zero_time_spent_accepted(self, client, mock_db):
        record = {**VALID_CONTENT_USAGE, "content_usage_id": "CU004", "time_spent_minutes": 0}
        response = client.post("/api/v1/ingest/content-usage", json=record)
        assert response.status_code == 201
        assert response.json()["status"] == "accepted"


class TestAiUsageEndpoint:
    def test_valid_accepted(self, client, mock_db):
        response = client.post("/api/v1/ingest/ai-usage", json=VALID_AI_USAGE)
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "accepted"
        assert data["ai_usage_id"] == "AIU001"

    def test_missing_ai_service_id_quarantined(self, client, mock_db):
        bad = {k: v for k, v in VALID_AI_USAGE.items() if k != "ai_service_id"}
        response = client.post("/api/v1/ingest/ai-usage", json=bad)
        assert response.status_code == 200
        assert response.json()["status"] == "quarantined"
        assert response.json()["reason"] == "validation_failed"

    def test_missing_subject_id_quarantined(self, client, mock_db):
        bad = {k: v for k, v in VALID_AI_USAGE.items() if k != "subject_id"}
        response = client.post("/api/v1/ingest/ai-usage", json=bad)
        assert response.status_code == 200
        assert response.json()["status"] == "quarantined"

    def test_negative_query_count_quarantined(self, client, mock_db):
        bad = {**VALID_AI_USAGE, "ai_usage_id": "AIU002", "query_count": -3}
        response = client.post("/api/v1/ingest/ai-usage", json=bad)
        assert response.status_code == 200
        assert response.json()["status"] == "quarantined"

    def test_empty_query_type_quarantined(self, client, mock_db):
        bad = {**VALID_AI_USAGE, "ai_usage_id": "AIU003", "query_type": ""}
        response = client.post("/api/v1/ingest/ai-usage", json=bad)
        assert response.status_code == 200
        assert response.json()["status"] == "quarantined"

    def test_invalid_date_id_quarantined(self, client, mock_db):
        bad = {**VALID_AI_USAGE, "ai_usage_id": "AIU004", "date_id": 20250032}
        response = client.post("/api/v1/ingest/ai-usage", json=bad)
        assert response.status_code == 200
        assert response.json()["status"] == "quarantined"

    def test_duplicate_detected(self, client, mock_db):
        mock_db.execute.return_value.scalar.return_value = 1
        response = client.post("/api/v1/ingest/ai-usage", json=VALID_AI_USAGE)
        assert response.status_code == 200
        assert response.json()["status"] == "duplicate"

    def test_zero_counts_accepted(self, client, mock_db):
        record = {**VALID_AI_USAGE, "ai_usage_id": "AIU005",
                  "query_count": 0, "time_spent_minutes": 0}
        response = client.post("/api/v1/ingest/ai-usage", json=record)
        assert response.status_code == 201
        assert response.json()["status"] == "accepted"


class TestAssessmentAttemptEndpoint:
    def test_valid_accepted(self, client, mock_db):
        response = client.post("/api/v1/ingest/assessment-attempts", json=VALID_ASSESSMENT)
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "accepted"
        assert data["attempt_id"] == "ATT001"

    def test_score_over_100_quarantined(self, client, mock_db):
        bad = {**VALID_ASSESSMENT, "assessment_attempt_id": "ATT002", "score": 101}
        response = client.post("/api/v1/ingest/assessment-attempts", json=bad)
        assert response.status_code == 200
        assert response.json()["status"] == "quarantined"

    def test_negative_score_quarantined(self, client, mock_db):
        bad = {**VALID_ASSESSMENT, "assessment_attempt_id": "ATT003", "score": -5}
        response = client.post("/api/v1/ingest/assessment-attempts", json=bad)
        assert response.status_code == 200
        assert response.json()["status"] == "quarantined"

    def test_missing_student_id_quarantined(self, client, mock_db):
        bad = {k: v for k, v in VALID_ASSESSMENT.items() if k != "student_id"}
        response = client.post("/api/v1/ingest/assessment-attempts", json=bad)
        assert response.status_code == 200
        assert response.json()["status"] == "quarantined"
        assert response.json()["reason"] == "validation_failed"

    def test_missing_content_id_quarantined(self, client, mock_db):
        bad = {k: v for k, v in VALID_ASSESSMENT.items() if k != "content_id"}
        response = client.post("/api/v1/ingest/assessment-attempts", json=bad)
        assert response.status_code == 200
        assert response.json()["status"] == "quarantined"

    def test_score_zero_accepted(self, client, mock_db):
        record = {**VALID_ASSESSMENT, "assessment_attempt_id": "ATT004", "score": 0}
        response = client.post("/api/v1/ingest/assessment-attempts", json=record)
        assert response.status_code == 201
        assert response.json()["status"] == "accepted"

    def test_score_100_accepted(self, client, mock_db):
        record = {**VALID_ASSESSMENT, "assessment_attempt_id": "ATT005", "score": 100}
        response = client.post("/api/v1/ingest/assessment-attempts", json=record)
        assert response.status_code == 201
        assert response.json()["status"] == "accepted"

    def test_duplicate_detected(self, client, mock_db):
        mock_db.execute.return_value.scalar.return_value = 1
        response = client.post("/api/v1/ingest/assessment-attempts", json=VALID_ASSESSMENT)
        assert response.status_code == 200
        assert response.json()["status"] == "duplicate"

    def test_invalid_date_id_quarantined(self, client, mock_db):
        bad = {**VALID_ASSESSMENT, "assessment_attempt_id": "ATT006", "date_id": 20251300}
        response = client.post("/api/v1/ingest/assessment-attempts", json=bad)
        assert response.status_code == 200
        assert response.json()["status"] == "quarantined"
