import pytest
from pydantic import ValidationError

from app.models.schemas import FactSessionIn

VALID = {
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


def test_valid_session_passes():
    s = FactSessionIn(**VALID)
    assert s.session_id == "SES001"
    assert s.date_id == 20250101
    assert s.session_duration_minutes == 45
    assert s.is_offline is True


def test_zero_duration_accepted():
    s = FactSessionIn(**{**VALID, "session_duration_minutes": 0})
    assert s.session_duration_minutes == 0


def test_default_is_offline_true():
    data = {k: v for k, v in VALID.items() if k != "is_offline"}
    s = FactSessionIn(**data)
    assert s.is_offline is True


def test_empty_session_id_rejected():
    with pytest.raises(ValidationError):
        FactSessionIn(**{**VALID, "session_id": ""})


def test_empty_student_id_rejected():
    with pytest.raises(ValidationError):
        FactSessionIn(**{**VALID, "student_id": ""})


def test_empty_school_id_rejected():
    with pytest.raises(ValidationError):
        FactSessionIn(**{**VALID, "school_id": ""})


def test_negative_duration_rejected():
    with pytest.raises(ValidationError):
        FactSessionIn(**{**VALID, "session_duration_minutes": -1})


def test_date_id_too_short_rejected():
    with pytest.raises(ValidationError):
        FactSessionIn(**{**VALID, "date_id": 99999})


def test_date_id_bad_month_rejected():
    with pytest.raises(ValidationError):
        FactSessionIn(**{**VALID, "date_id": 20251301})  # month 13


def test_date_id_bad_day_rejected():
    with pytest.raises(ValidationError):
        FactSessionIn(**{**VALID, "date_id": 20250100})  # day 0


def test_date_id_boundary_valid():
    s = FactSessionIn(**{**VALID, "date_id": 20241231})
    assert s.date_id == 20241231
