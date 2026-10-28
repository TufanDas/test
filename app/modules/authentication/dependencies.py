from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import security_service
from app.modules.authentication.models import AuthenticatedUser

http_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(http_bearer),
) -> AuthenticatedUser:
    """Dependency for endpoints requiring Keycloak JWT authentication."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    payload = security_service.decode_and_verify_token(token)
    sub = payload.get("sub")
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing subject identifier",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return AuthenticatedUser(
        keycloak_user_id=sub,
        email=payload.get("email"),
        username=payload.get("preferred_username"),
    )
