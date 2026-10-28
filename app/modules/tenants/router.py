from fastapi import APIRouter, Depends, status

from app.modules.tenants.schemas import TenantSignupRequest, TenantSignupResponse
from app.modules.tenants.service import TenantService, tenant_service

router = APIRouter(prefix="/tenants", tags=["Tenants"])


@router.post(
    "/signup",
    response_model=TenantSignupResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new restaurant business/tenant and initial owner",
)
async def signup_tenant(
    request: TenantSignupRequest,
    service: TenantService = Depends(lambda: tenant_service),
) -> TenantSignupResponse:
    """Public tenant registration endpoint.

    Registers:
    1. Keycloak identity for the owner
    2. MongoDB application user profile
    3. MongoDB tenant organization
    4. MongoDB membership with OWNER role and TENANT scope
    """
    return await service.signup_tenant(request)
