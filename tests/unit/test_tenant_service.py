from unittest.mock import AsyncMock

import pytest

from app.core.exceptions import DatabaseException, DuplicateResourceException
from app.modules.tenants.schemas import OwnerSignupRequest, TenantSignupRequest
from app.modules.tenants.service import TenantService


@pytest.fixture
def sample_request():
    return TenantSignupRequest(
        tenant_name="The Food House",
        owner=OwnerSignupRequest(
            first_name="Sneha",
            last_name="Roy",
            email="sneha@example.com",
            password="StrongPassword123!",
        ),
    )


@pytest.mark.asyncio
async def test_signup_successful_orchestration(sample_request):
    mock_tenant_repo = AsyncMock()
    mock_user_repo = AsyncMock()
    mock_kc_client = AsyncMock()

    # Pre-validation checks pass
    mock_user_repo.check_user_exists_by_email.return_value = False
    mock_tenant_repo.check_tenant_name_exists.return_value = False

    # Keycloak creates user
    mock_kc_client.create_user.return_value = "kc_user_123"

    # MongoDB creations
    mock_user_repo.create_user.return_value = {
        "_id": "user_001",
        "email": "sneha@example.com",
    }
    mock_tenant_repo.create_tenant.return_value = {
        "_id": "tenant_001",
        "name": "The Food House",
    }
    mock_tenant_repo.create_membership.return_value = {
        "_id": "membership_001",
        "user_id": "user_001",
        "tenant_id": "tenant_001",
        "role": "OWNER",
        "scope": "TENANT",
    }

    service = TenantService(
        tenant_repo=mock_tenant_repo,
        user_repo=mock_user_repo,
        kc_client=mock_kc_client,
    )

    result = await service.signup_tenant(sample_request)

    assert result.tenant_id == "tenant_001"
    assert result.user_id == "user_001"
    assert result.message == "Tenant registration successful"

    # Verify calls
    mock_kc_client.create_user.assert_awaited_once_with(
        email="sneha@example.com",
        first_name="Sneha",
        last_name="Roy",
        password="StrongPassword123!",
        enabled=True,
        email_verified=True,
    )
    mock_user_repo.create_user.assert_awaited_once_with(
        keycloak_user_id="kc_user_123",
        email="sneha@example.com",
        first_name="Sneha",
        last_name="Roy",
        status="ACTIVE",
    )
    mock_tenant_repo.create_tenant.assert_awaited_once_with(
        name="The Food House",
        status="ACTIVE",
    )
    mock_tenant_repo.create_membership.assert_awaited_once_with(
        user_id="user_001",
        tenant_id="tenant_001",
        role="OWNER",
        scope="TENANT",
        status="ACTIVE",
    )
    # Rollback should NOT be called
    mock_kc_client.delete_user.assert_not_called()


@pytest.mark.asyncio
async def test_signup_rejects_duplicate_email_before_keycloak(sample_request):
    mock_tenant_repo = AsyncMock()
    mock_user_repo = AsyncMock()
    mock_kc_client = AsyncMock()

    mock_user_repo.check_user_exists_by_email.return_value = True

    service = TenantService(
        tenant_repo=mock_tenant_repo,
        user_repo=mock_user_repo,
        kc_client=mock_kc_client,
    )

    with pytest.raises(DuplicateResourceException) as exc_info:
        await service.signup_tenant(sample_request)

    assert "email already exists" in str(exc_info.value.message)
    mock_kc_client.create_user.assert_not_called()


@pytest.mark.asyncio
async def test_signup_rejects_duplicate_tenant_before_keycloak(sample_request):
    mock_tenant_repo = AsyncMock()
    mock_user_repo = AsyncMock()
    mock_kc_client = AsyncMock()

    mock_user_repo.check_user_exists_by_email.return_value = False
    mock_tenant_repo.check_tenant_name_exists.return_value = True

    service = TenantService(
        tenant_repo=mock_tenant_repo,
        user_repo=mock_user_repo,
        kc_client=mock_kc_client,
    )

    with pytest.raises(DuplicateResourceException) as exc_info:
        await service.signup_tenant(sample_request)

    assert "tenant with this name already exists" in str(exc_info.value.message)
    mock_kc_client.create_user.assert_not_called()


@pytest.mark.asyncio
async def test_signup_rollback_on_mongodb_failure(sample_request):
    mock_tenant_repo = AsyncMock()
    mock_user_repo = AsyncMock()
    mock_kc_client = AsyncMock()

    mock_user_repo.check_user_exists_by_email.return_value = False
    mock_tenant_repo.check_tenant_name_exists.return_value = False

    # Keycloak succeeds
    mock_kc_client.create_user.return_value = "kc_user_failed_step"
    mock_user_repo.create_user.return_value = {"_id": "user_created_id"}

    # Tenant creation fails!
    mock_tenant_repo.create_tenant.side_effect = Exception("MongoDB connection lost")

    service = TenantService(
        tenant_repo=mock_tenant_repo,
        user_repo=mock_user_repo,
        kc_client=mock_kc_client,
    )

    with pytest.raises(DatabaseException):
        await service.signup_tenant(sample_request)

    # Rollback verification: Keycloak user and MongoDB user deleted!
    mock_user_repo.delete_user.assert_awaited_once_with("user_created_id")
    mock_kc_client.delete_user.assert_awaited_once_with("kc_user_failed_step")
