from unittest.mock import AsyncMock, patch

import httpx
import pytest

from app.core.database import db_manager
from app.core.exceptions import KeycloakException
from app.modules.authentication.keycloak import keycloak_client


@pytest.mark.asyncio
async def test_integration_signup_success(async_client: httpx.AsyncClient):
    """Test 1 & Test 8: Successful signup (201 Created) and verify tenant/membership isolation."""
    payload = {
        "tenant_name": "The Royal Spice",
        "owner": {
            "first_name": "Sneha",
            "last_name": "Roy",
            "email": "sneha.signup@example.com",
            "password": "StrongPassword123!",
        },
    }

    with patch.object(
        keycloak_client,
        "create_user",
        new_callable=AsyncMock,
        return_value="kc_mock_user_101",
    ):
        response = await async_client.post("/api/v1/tenants/signup", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["message"] == "Tenant registration successful"
    tenant_id = data["tenant_id"]
    user_id = data["user_id"]
    assert tenant_id.startswith("tenant_")
    assert user_id.startswith("user_")

    # Verify MongoDB: User created
    db = db_manager.get_database()
    user_doc = await db["users"].find_one({"_id": user_id})
    assert user_doc is not None
    assert user_doc["email"] == "sneha.signup@example.com"
    assert user_doc["keycloak_user_id"] == "kc_mock_user_101"
    assert user_doc["first_name"] == "Sneha"
    assert user_doc["last_name"] == "Roy"
    assert "password" not in user_doc

    # Verify MongoDB: Tenant created
    tenant_doc = await db["tenants"].find_one({"_id": tenant_id})
    assert tenant_doc is not None
    assert tenant_doc["name"] == "The Royal Spice"
    assert tenant_doc["status"] == "ACTIVE"

    # Verify MongoDB: Membership created linking user & tenant
    membership = await db["memberships"].find_one(
        {"user_id": user_id, "tenant_id": tenant_id}
    )
    assert membership is not None
    assert membership["role"] == "OWNER"
    assert membership["scope"] == "TENANT"
    assert membership["status"] == "ACTIVE"


@pytest.mark.asyncio
async def test_integration_signup_duplicate_email(async_client: httpx.AsyncClient):
    """Test 2: Duplicate email returns 409 Conflict."""
    payload = {
        "tenant_name": "The Royal Spice",
        "owner": {
            "first_name": "Sneha",
            "last_name": "Roy",
            "email": "existing@example.com",
            "password": "StrongPassword123!",
        },
    }

    # Pre-seed existing user in MongoDB
    db = db_manager.get_database()
    await db["users"].insert_one(
        {
            "_id": "user_existing_1",
            "email": "existing@example.com",
            "keycloak_user_id": "kc_existing_1",
            "first_name": "Old",
            "last_name": "User",
            "status": "ACTIVE",
        }
    )

    with patch.object(
        keycloak_client, "create_user", new_callable=AsyncMock
    ) as mock_kc:
        response = await async_client.post("/api/v1/tenants/signup", json=payload)
        mock_kc.assert_not_called()

    assert response.status_code == 409
    assert response.json() == {"detail": "A user with this email already exists."}


@pytest.mark.asyncio
async def test_integration_signup_invalid_email(async_client: httpx.AsyncClient):
    """Test 3: Invalid email returns 422 Unprocessable Entity."""
    payload = {
        "tenant_name": "The Royal Spice",
        "owner": {
            "first_name": "Sneha",
            "last_name": "Roy",
            "email": "not-valid-email-format",
            "password": "StrongPassword123!",
        },
    }
    response = await async_client.post("/api/v1/tenants/signup", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_integration_signup_invalid_password(async_client: httpx.AsyncClient):
    """Test 4: Password too short returns 422 Unprocessable Entity."""
    payload = {
        "tenant_name": "The Royal Spice",
        "owner": {
            "first_name": "Sneha",
            "last_name": "Roy",
            "email": "sneha@example.com",
            "password": "short",
        },
    }
    response = await async_client.post("/api/v1/tenants/signup", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_integration_signup_keycloak_unavailable(async_client: httpx.AsyncClient):
    """Test 5: Keycloak unavailable returns 502 Bad Gateway."""
    payload = {
        "tenant_name": "The Royal Spice",
        "owner": {
            "first_name": "Sneha",
            "last_name": "Roy",
            "email": "sneha@example.com",
            "password": "StrongPassword123!",
        },
    }

    with patch.object(
        keycloak_client,
        "create_user",
        new_callable=AsyncMock,
        side_effect=KeycloakException("Unable to connect to authentication server"),
    ):
        response = await async_client.post("/api/v1/tenants/signup", json=payload)

    assert response.status_code == 502
    assert "detail" in response.json()


@pytest.mark.asyncio
async def test_integration_signup_keycloak_permission_denied(
    async_client: httpx.AsyncClient,
):
    """Test 6: Keycloak service account lacks permission (returns 502)."""
    payload = {
        "tenant_name": "The Royal Spice",
        "owner": {
            "first_name": "Sneha",
            "last_name": "Roy",
            "email": "sneha@example.com",
            "password": "StrongPassword123!",
        },
    }

    with patch.object(
        keycloak_client,
        "create_user",
        new_callable=AsyncMock,
        side_effect=KeycloakException(
            "Insufficient permissions to manage users in Keycloak", status_code=502
        ),
    ):
        response = await async_client.post("/api/v1/tenants/signup", json=payload)

    assert response.status_code == 502
    assert "detail" in response.json()


@pytest.mark.asyncio
async def test_integration_signup_mongodb_failure_compensation(
    async_client: httpx.AsyncClient,
):
    """Test 7: MongoDB failure during workflow triggers rollback of Keycloak user."""
    payload = {
        "tenant_name": "The Royal Spice",
        "owner": {
            "first_name": "Sneha",
            "last_name": "Roy",
            "email": "sneha@example.com",
            "password": "StrongPassword123!",
        },
    }

    with (
        patch.object(
            keycloak_client,
            "create_user",
            new_callable=AsyncMock,
            return_value="kc_rollback_target",
        ),
        patch.object(
            keycloak_client, "delete_user", new_callable=AsyncMock
        ) as mock_kc_delete,
        patch(
            "app.modules.tenants.repository.TenantRepository.create_tenant",
            new_callable=AsyncMock,
            side_effect=Exception("Database write error"),
        ),
    ):
        response = await async_client.post("/api/v1/tenants/signup", json=payload)

    assert response.status_code == 500
    mock_kc_delete.assert_awaited_once_with("kc_rollback_target")
