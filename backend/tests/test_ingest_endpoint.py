VALID_SESSION = {
    "session_id": "SES001",
    "student_id": "STU001",
    "school_id": "SCH001",
    "device_id": "D001",
    "platform_id": "PLT001",
    "date_id": 20250101,
    "project_id": "PRJ001",
    "session_duration_minutes": 45,
    "is_offline": True,
}


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_valid_session_accepted(client, mock_db):
    response = client.post("/api/v1/ingest/sessions", json=VALID_SESSION)
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "accepted"
    assert data["session_id"] == "SES001"
    assert mock_db.commit.called


def test_empty_session_id_quarantined(client, mock_db):
    bad = {**VALID_SESSION, "session_id": ""}
    response = client.post("/api/v1/ingest/sessions", json=bad)
    assert response.status_code == 200
    assert response.json()["status"] == "quarantined"
    assert response.json()["reason"] == "validation_failed"


def test_negative_duration_quarantined(client, mock_db):
    bad = {**VALID_SESSION, "session_id": "SES002", "session_duration_minutes": -5}
    response = client.post("/api/v1/ingest/sessions", json=bad)
    assert response.status_code == 200
    assert response.json()["status"] == "quarantined"


def test_invalid_date_id_quarantined(client, mock_db):
    bad = {**VALID_SESSION, "session_id": "SES003", "date_id": 99999}
    response = client.post("/api/v1/ingest/sessions", json=bad)
    assert response.status_code == 200
    assert response.json()["status"] == "quarantined"


def test_missing_required_field_quarantined(client, mock_db):
    bad = {k: v for k, v in VALID_SESSION.items() if k != "school_id"}
    response = client.post("/api/v1/ingest/sessions", json=bad)
    assert response.status_code == 200
    assert response.json()["status"] == "quarantined"


def test_duplicate_session_detected(client, mock_db):
    mock_db.execute.return_value.scalar.return_value = 1  # record exists
    response = client.post("/api/v1/ingest/sessions", json=VALID_SESSION)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "duplicate"
    assert data["session_id"] == "SES001"


def test_quarantined_record_stored_in_db(client, mock_db):
    bad = {**VALID_SESSION, "session_id": "SES004", "session_duration_minutes": -99}
    client.post("/api/v1/ingest/sessions", json=bad)
    assert mock_db.execute.called
    assert mock_db.commit.called
