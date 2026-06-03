from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.database import get_db
from app.main import app


@pytest.fixture
def mock_db():
    db = AsyncMock()
    result = MagicMock()
    result.scalar.return_value = None  # default: no duplicate
    db.execute.return_value = result
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    return db


@pytest.fixture
def client(mock_db):
    async def _override():
        yield mock_db

    app.dependency_overrides[get_db] = _override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
