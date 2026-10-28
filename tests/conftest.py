from collections.abc import AsyncGenerator

import httpx
import pytest_asyncio
from pymongo import AsyncMongoClient

from app.core.config import settings
from app.core.database import db_manager
from app.main import app

TEST_DB_NAME = "test_restaurant_management_backend"


@pytest_asyncio.fixture
async def test_db() -> AsyncGenerator:
    """Function-scoped MongoDB test database fixture bound to the active test loop."""
    client = AsyncMongoClient(settings.MONGODB_URL)
    db = client[TEST_DB_NAME]

    # Point db_manager to the test client & database
    db_manager.client = client
    db_manager.db = db

    # Clear collections before test
    for col_name in ["users", "tenants", "memberships"]:
        await db[col_name].delete_many({})

    yield db

    # Clean up after test
    for col_name in ["users", "tenants", "memberships"]:
        await db[col_name].delete_many({})

    await client.drop_database(TEST_DB_NAME)
    await client.close()
    db_manager.client = None
    db_manager.db = None


@pytest_asyncio.fixture
async def async_client(test_db) -> AsyncGenerator[httpx.AsyncClient, None]:
    """Test client for invoking FastAPI endpoints."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
