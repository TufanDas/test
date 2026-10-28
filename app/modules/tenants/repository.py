import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from pymongo.asynchronous.database import AsyncDatabase

from app.core.database import get_db

logger = logging.getLogger(__name__)


def generate_tenant_id() -> str:
    return f"tenant_{uuid.uuid4().hex[:12]}"


def generate_membership_id() -> str:
    return f"membership_{uuid.uuid4().hex[:12]}"


class TenantRepository:
    def __init__(self, db: AsyncDatabase | None = None):
        self._db = db

    @property
    def db(self) -> AsyncDatabase:
        if self._db is not None:
            return self._db
        return get_db()

    @property
    def tenants_collection(self):
        return self.db["tenants"]

    @property
    def memberships_collection(self):
        return self.db["memberships"]

    async def check_tenant_name_exists(self, name: str) -> bool:
        """Check whether a tenant with this name (case-insensitive) already exists."""
        # Using exact case-insensitive regex match
        query = {"name": {"$regex": f"^{name.strip()}$", "$options": "i"}}
        count = await self.tenants_collection.count_documents(query)
        return count > 0

    async def create_tenant(
        self,
        name: str,
        tenant_id: str | None = None,
        status: str = "ACTIVE",
    ) -> dict[str, Any]:
        """Create a new tenant document in MongoDB."""
        tid = tenant_id or generate_tenant_id()
        now = datetime.now(UTC)
        doc: dict[str, Any] = {
            "_id": tid,
            "name": name.strip(),
            "status": status,
            "created_at": now,
            "updated_at": now,
        }
        await self.tenants_collection.insert_one(doc)
        logger.info(f"Created MongoDB tenant document: {tid} ('{name}')")
        return doc

    async def create_membership(
        self,
        user_id: str,
        tenant_id: str,
        role: str = "OWNER",
        scope: str = "TENANT",
        membership_id: str | None = None,
        status: str = "ACTIVE",
    ) -> dict[str, Any]:
        """Create a new membership linking user to tenant."""
        mid = membership_id or generate_membership_id()
        now = datetime.now(UTC)
        doc: dict[str, Any] = {
            "_id": mid,
            "user_id": user_id,
            "tenant_id": tenant_id,
            "role": role,
            "scope": scope,
            "status": status,
            "created_at": now,
            "updated_at": now,
        }
        await self.memberships_collection.insert_one(doc)
        logger.info(
            f"Created MongoDB membership document: {mid} (User {user_id} -> Tenant {tenant_id})"
        )
        return doc

    async def get_tenant_by_id(self, tenant_id: str) -> dict[str, Any] | None:
        return await self.tenants_collection.find_one({"_id": tenant_id})

    async def get_membership_by_id(self, membership_id: str) -> dict[str, Any] | None:
        return await self.memberships_collection.find_one({"_id": membership_id})

    async def delete_tenant(self, tenant_id: str) -> bool:
        """Delete tenant document (used for compensation / rollback)."""
        result = await self.tenants_collection.delete_one({"_id": tenant_id})
        logger.info(
            f"Deleted MongoDB tenant {tenant_id}: {result.deleted_count} removed"
        )
        return result.deleted_count > 0

    async def delete_membership(self, membership_id: str) -> bool:
        """Delete membership document (used for compensation / rollback)."""
        result = await self.memberships_collection.delete_one({"_id": membership_id})
        logger.info(
            f"Deleted MongoDB membership {membership_id}: {result.deleted_count} removed"
        )
        return result.deleted_count > 0


tenant_repository = TenantRepository()
