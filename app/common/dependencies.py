from pymongo.asynchronous.database import AsyncDatabase

from app.core.database import get_db


async def get_database_dependency() -> AsyncDatabase:
    return get_db()
