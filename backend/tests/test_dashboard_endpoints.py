from unittest.mock import MagicMock

from app.auth.security import create_access_token


def auth_headers(role="admin"):
    token = create_access_token({"sub": "USR001", "user_id": "USR001", "role": role})
    return {"Authorization": f"Bearer {token}"}


def mock_query_rows(mock_db, rows):
    result = MagicMock()
    mappings = MagicMock()
    mappings.first.return_value = rows[0] if rows else None
    mappings.all.return_value = rows
    result.mappings.return_value = mappings
    mock_db.execute.return_value = result


def test_dashboard_summary_route_works_for_admin(client, mock_db):
    mock_query_rows(
        mock_db,
        [
            {
                "students": 120,
                "teachers": 8,
                "schools": 3,
                "sessions": 450,
                "devices": 24,
            }
        ],
    )

    response = client.get("/api/v1/dashboard/summary", headers=auth_headers())

    assert response.status_code == 200
    assert response.json() == {
        "scope": "admin",
        "cards": {
            "sessions": 450,
            "learning_minutes": None,
            "assignments_completed": None,
            "average_score": None,
            "students": 120,
            "active_sessions": None,
            "average_completion": None,
            "teachers": 8,
            "schools": 3,
            "devices": 24,
        },
        "charts": [],
        "recent_activity": [],
    }


def test_school_dashboard_route_works(client, mock_db):
    mock_query_rows(
        mock_db,
        [
            {
                "school_id": "SCH001",
                "date_key": 20250101,
                "total_syncs": 10,
                "successful_syncs": 9,
                "sync_health_pct": 90,
                "active_devices": 5,
                "avg_usage_minutes": 25,
                "total_sessions": 75,
                "total_usage_minutes": 125,
                "refreshed_at": None,
            }
        ],
    )

    response = client.get("/api/v1/dashboard/school", headers=auth_headers())

    assert response.status_code == 200
    assert response.json()["data"][0]["school_id"] == "SCH001"


def test_platform_dashboard_route_works(client, mock_db):
    mock_query_rows(
        mock_db,
        [
            {
                "school_id": "SCH001",
                "platform_id": "PLT001",
                "platform_name": "Moodle",
                "platform_type": "lms",
                "tracking_depth": "session",
                "unique_students": 45,
                "total_sessions": 200,
                "avg_session_minutes": 35,
                "total_minutes": 7000,
                "offline_sessions": 20,
                "offline_pct": 10,
                "sync_health_pct": 95,
                "total_syncs": 40,
                "successful_syncs": 38,
                "active_devices": 12,
                "avg_usage_minutes": 50,
                "total_usage_minutes": 600,
                "refreshed_at": None,
            }
        ],
    )

    response = client.get("/api/v1/dashboard/platform", headers=auth_headers())

    assert response.status_code == 200
    assert response.json()["data"][0]["platform_id"] == "PLT001"


def test_device_dashboard_route_works(client, mock_db):
    mock_query_rows(
        mock_db,
        [
            {
                "school_id": "SCH001",
                "date_key": 20250101,
                "total_syncs": 10,
                "successful_syncs": 9,
                "sync_health_pct": 90,
                "active_devices": 5,
                "avg_usage_minutes": 25,
                "total_sessions": 75,
                "total_usage_minutes": 125,
                "refreshed_at": None,
            }
        ],
    )

    response = client.get("/api/v1/dashboard/device", headers=auth_headers())

    assert response.status_code == 200
    assert response.json()["data"][0]["active_devices"] == 5


def test_dashboard_reports_route_works_for_admin(client):
    response = client.get("/api/v1/dashboard/reports", headers=auth_headers())

    assert response.status_code == 200
    assert response.json()["message"] == "Teacher or admin access granted"


def test_dashboard_routes_reject_invalid_tokens(client):
    response = client.get(
        "/api/v1/dashboard/summary",
        headers={"Authorization": "Bearer not-a-valid-token"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or expired token"
