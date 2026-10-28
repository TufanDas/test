import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from pymongo.asynchronous.database import AsyncDatabase

from app.core.database import get_db

logger = logging.getLogger(__name__)


def generate_user_id() -> str:
    return f"user_{uuid.uuid4().hex[:12]}"


class UserRepository:
    def __init__(self, db: AsyncDatabase | None = None):
        self._db = db

    @property
    def db(self) -> AsyncDatabase:
        if self._db is not None:
            return self._db
        return get_db()

    @property
    def collection(self):
        return self.db["users"]

    async def check_user_exists_by_email(self, email: str) -> bool:
        """Check if an application user with given email already exists in MongoDB."""
        count = await self.collection.count_documents({"email": email.strip().lower()})
        return count > 0

    async def create_user(
        self,
        keycloak_user_id: str,
        email: str,
        first_name: str,
        last_name: str,
        user_id: str | None = None,
        status: str = "ACTIVE",
    ) -> dict[str, Any]:
        """Create a new user profile document in MongoDB."""
        uid = user_id or generate_user_id()
        now = datetime.now(UTC)
        doc: dict[str, Any] = {
            "_id": uid,
            "keycloak_user_id": keycloak_user_id,
            "email": email.strip().lower(),
            "first_name": first_name.strip(),
            "last_name": last_name.strip(),
            "status": status,
            "created_at": now,
            "updated_at": now,
        }
        await self.collection.insert_one(doc)
        logger.info(
            f"Created MongoDB user document: {uid} with keycloak_user_id: {keycloak_user_id}"
        )
        return doc

    async def get_user_by_id(self, user_id: str) -> dict[str, Any] | None:
        return await self.collection.find_one({"_id": user_id})

    async def get_user_by_keycloak_id(
        self, keycloak_user_id: str
    ) -> dict[str, Any] | None:
        return await self.collection.find_one({"keycloak_user_id": keycloak_user_id})

    async def delete_user(self, user_id: str) -> bool:
        """Delete a user document (used for compensation / rollback)."""
        result = await self.collection.delete_one({"_id": user_id})
        logger.info(f"Deleted MongoDB user {user_id}: {result.deleted_count} removed")
        return result.deleted_count > 0


user_repository = UserRepository()
