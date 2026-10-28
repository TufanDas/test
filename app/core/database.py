import logging

from pymongo import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase

from app.core.config import settings

logger = logging.getLogger(__name__)


class DatabaseManager:
    client: AsyncMongoClient | None = None
    db: AsyncDatabase | None = None

    @classmethod
    async def connect_to_database(
        cls, uri: str | None = None, db_name: str | None = None
    ):
        mongo_url = uri or settings.MONGODB_URL
        database_name = db_name or settings.MONGODB_DATABASE
        logger.info(f"Connecting to MongoDB at {mongo_url}, database: {database_name}")
        cls.client = AsyncMongoClient(mongo_url)
        cls.db = cls.client[database_name]
        logger.info("Connected to MongoDB successfully.")

    @classmethod
    async def close_database_connection(cls):
        if cls.client is not None:
            logger.info("Closing MongoDB connection...")
            await cls.client.close()
            cls.client = None
            cls.db = None
            logger.info("MongoDB connection closed.")

    @classmethod
    def get_database(cls) -> AsyncDatabase:
        if cls.db is None:
            mongo_url = settings.MONGODB_URL
            database_name = settings.MONGODB_DATABASE
            cls.client = AsyncMongoClient(mongo_url)
            cls.db = cls.client[database_name]
        return cls.db


db_manager = DatabaseManager


def get_db() -> AsyncDatabase:
    return db_manager.get_database()
