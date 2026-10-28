import logging
import time
from typing import Any

import httpx

from app.core.config import settings
from app.core.exceptions import (
    KeycloakAuthException,
    KeycloakConflictException,
    KeycloakException,
)

logger = logging.getLogger(__name__)


class KeycloakClient:
    """Handles direct communication with Keycloak's OpenID Connect and Admin REST API."""

    def __init__(
        self,
        base_url: str | None = None,
        realm: str | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
    ):
        self.base_url = (base_url or settings.KEYCLOAK_URL).rstrip("/")
        self.realm = realm or settings.KEYCLOAK_REALM
        self.client_id = client_id or settings.KEYCLOAK_CLIENT_ID
        self.client_secret = client_secret or settings.KEYCLOAK_CLIENT_SECRET

        self._token: str | None = None
        self._token_expires_at: float = 0.0

    @property
    def token_url(self) -> str:
        return f"{self.base_url}/realms/{self.realm}/protocol/openid-connect/token"

    @property
    def admin_users_url(self) -> str:
        return f"{self.base_url}/admin/realms/{self.realm}/users"

    async def get_service_account_token(self, force_refresh: bool = False) -> str:
        """Obtain or return cached service-account access token via client credentials grant."""
        now = time.time()
        if not force_refresh and self._token and now < (self._token_expires_at - 30):
            return self._token

        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(self.token_url, data=data)
        except httpx.RequestError as exc:
            logger.error(f"Network error connecting to Keycloak token endpoint: {exc}")
            raise KeycloakException("Unable to connect to authentication server")

        if response.status_code == 200:
            token_data = response.json()
            self._token = token_data.get("access_token")
            expires_in = token_data.get("expires_in", 300)
            self._token_expires_at = now + expires_in
            return self._token

        logger.error(
            f"Keycloak service account authentication failed with status {response.status_code}: {response.text}"
        )
        if response.status_code in (401, 403):
            raise KeycloakAuthException(
                "Failed to authenticate service account with identity provider"
            )
        raise KeycloakException(
            f"Identity provider token request failed: {response.status_code}"
        )

    async def create_user(
        self,
        email: str,
        first_name: str,
        last_name: str,
        password: str,
        enabled: bool = True,
        email_verified: bool = True,
    ) -> str:
        """Create a user in Keycloak and configure credentials.

        Returns the Keycloak user ID.
        """
        token = await self.get_service_account_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        user_payload: dict[str, Any] = {
            "username": email,
            "email": email,
            "firstName": first_name,
            "lastName": last_name,
            "enabled": enabled,
            "emailVerified": email_verified,
            "credentials": [
                {
                    "type": "password",
                    "value": password,
                    "temporary": False,
                }
            ],
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    self.admin_users_url, json=user_payload, headers=headers
                )
        except httpx.RequestError as exc:
            logger.error(f"Network error calling Keycloak create user: {exc}")
            raise KeycloakException("Unable to connect to authentication server")

        if response.status_code == 201:
            location = response.headers.get("Location")
            if location:
                keycloak_user_id = location.rstrip("/").split("/")[-1]
                logger.info(f"Successfully created Keycloak user: {keycloak_user_id}")
                return keycloak_user_id

            # Fallback: look up user by email if Location header is missing
            user_info = await self.find_user_by_email(email)
            if user_info and "id" in user_info:
                return user_info["id"]
            raise KeycloakException(
                "Keycloak user created but user ID could not be retrieved"
            )

        if response.status_code == 409:
            logger.warning(f"Keycloak user creation conflict for email {email}")
            raise KeycloakConflictException("A user with this email already exists.")

        if response.status_code in (401, 403):
            logger.error(
                f"Keycloak permission error {response.status_code}: {response.text}"
            )
            raise KeycloakException(
                "Insufficient permissions to manage users in Keycloak", status_code=502
            )

        logger.error(
            f"Keycloak create user failed with status {response.status_code}: {response.text}"
        )
        raise KeycloakException(
            f"Failed to create user in Keycloak: status {response.status_code}"
        )

    async def find_user_by_email(self, email: str) -> dict[str, Any] | None:
        """Look up a user in Keycloak by exact email."""
        token = await self.get_service_account_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }
        params = {"email": email, "exact": "true"}

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    self.admin_users_url, headers=headers, params=params
                )
        except httpx.RequestError as exc:
            logger.error(f"Network error querying Keycloak users: {exc}")
            raise KeycloakException("Unable to connect to authentication server")

        if response.status_code == 200:
            users: list[dict[str, Any]] = response.json()
            if users:
                return users[0]
            return None

        logger.error(
            f"Failed to query Keycloak users: {response.status_code} - {response.text}"
        )
        raise KeycloakException("Failed to lookup user in Keycloak")

    async def set_user_password(
        self, user_id: str, password: str, temporary: bool = False
    ) -> None:
        """Set credentials for an existing Keycloak user."""
        token = await self.get_service_account_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        url = f"{self.admin_users_url}/{user_id}/reset-password"
        payload = {
            "type": "password",
            "value": password,
            "temporary": temporary,
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.put(url, json=payload, headers=headers)
        except httpx.RequestError as exc:
            logger.error(f"Network error setting Keycloak user password: {exc}")
            raise KeycloakException("Unable to connect to authentication server")

        if response.status_code != 204:
            logger.error(
                f"Failed to set user password in Keycloak: {response.status_code} - {response.text}"
            )
            raise KeycloakException("Failed to configure user credentials in Keycloak")

    async def delete_user(self, user_id: str) -> bool:
        """Delete a user in Keycloak (used for rollback/compensation)."""
        try:
            token = await self.get_service_account_token()
            headers = {"Authorization": f"Bearer {token}"}
            url = f"{self.admin_users_url}/{user_id}"

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.delete(url, headers=headers)

            if response.status_code in (204, 404):
                logger.info(f"Successfully rolled back/deleted Keycloak user {user_id}")
                return True

            logger.error(
                f"Failed to delete Keycloak user {user_id}: {response.status_code} - {response.text}"
            )
            return False
        except Exception as exc:
            logger.error(
                f"Exception during Keycloak user rollback for {user_id}: {exc}"
            )
            return False


keycloak_client = KeycloakClient()
