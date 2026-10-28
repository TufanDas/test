import logging
from typing import Any

import jwt
from jwt import PyJWKClient

from app.core.config import settings
from app.core.exceptions import AppException

logger = logging.getLogger(__name__)


class SecurityService:
    def __init__(self):
        self._jwks_client: PyJWKClient | None = None

    @property
    def jwks_client(self) -> PyJWKClient:
        if self._jwks_client is None:
            self._jwks_client = PyJWKClient(settings.keycloak_certs_url)
        return self._jwks_client

    def decode_and_verify_token(
        self,
        token: str,
        audience: str | None = None,
        verify_exp: bool = True,
    ) -> dict[str, Any]:
        """Validate and decode a Keycloak-issued JWT token.

        Validates:
        - Signature (via Keycloak JWKS public key)
        - Issuer
        - Expiration
        - Algorithm (RS256)
        - Subject
        """
        try:
            signing_key = self.jwks_client.get_signing_key_from_jwt(token)
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=[settings.JWT_ALGORITHM],
                issuer=settings.keycloak_issuer_url,
                audience=audience or settings.KEYCLOAK_CLIENT_ID,
                options={
                    "verify_signature": True,
                    "verify_exp": verify_exp,
                    "verify_iss": True,
                    "require": ["exp", "iss", "sub"],
                },
            )
            return payload
        except jwt.PyJWTError as e:
            logger.warning(f"JWT validation failed: {e}")
            raise AppException(
                message=f"Invalid or expired token: {e!s}", status_code=401
            )


security_service = SecurityService()
