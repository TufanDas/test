import logging

from app.modules.authentication.keycloak import KeycloakClient, keycloak_client

logger = logging.getLogger(__name__)


class AuthenticationService:
    def __init__(self, kc_client: KeycloakClient | None = None):
        self.keycloak_client = kc_client or keycloak_client

    async def verify_keycloak_connectivity(self) -> bool:
        """Check if Keycloak is reachable and service account can authenticate."""
        try:
            token = await self.keycloak_client.get_service_account_token()
            return bool(token)
        except Exception as e:
            logger.error(f"Keycloak connectivity check failed: {e}")
            return False


auth_service = AuthenticationService()
