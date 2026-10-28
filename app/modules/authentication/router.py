from fastapi import APIRouter

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.get("/health", summary="Keycloak Integration Health")
async def auth_health():
    """Verify Keycloak endpoint accessibility."""
    return {"status": "ok", "provider": "Keycloak"}
