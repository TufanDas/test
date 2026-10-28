from typing import Any

from app.modules.users.repository import UserRepository, user_repository


class UserService:
    def __init__(self, repo: UserRepository | None = None):
        self.repo = repo or user_repository

    async def get_user_by_id(self, user_id: str) -> dict[str, Any] | None:
        return await self.repo.get_user_by_id(user_id)

    async def get_user_by_keycloak_id(
        self, keycloak_user_id: str
    ) -> dict[str, Any] | None:
        return await self.repo.get_user_by_keycloak_id(keycloak_user_id)


user_service = UserService()
