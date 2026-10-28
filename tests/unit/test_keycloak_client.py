from unittest.mock import AsyncMock, patch

import httpx
import pytest

from app.core.exceptions import (
    KeycloakAuthException,
    KeycloakConflictException,
    KeycloakException,
)
from app.modules.authentication.keycloak import KeycloakClient


@pytest.fixture
def client():
    return KeycloakClient(
        base_url="https://keycloak.example.com",
        realm="test-realm",
        client_id="test-client",
        client_secret="test-secret",
    )


@pytest.mark.asyncio
async def test_get_service_account_token_success(client):
    mock_response = httpx.Response(
        200,
        json={"access_token": "mock-token-123", "expires_in": 300},
        request=httpx.Request("POST", client.token_url),
    )
    with patch(
        "httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response
    ):
        token = await client.get_service_account_token()
        assert token == "mock-token-123"


@pytest.mark.asyncio
async def test_get_service_account_token_unauthorized(client):
    mock_response = httpx.Response(
        401,
        json={"error": "unauthorized_client"},
        request=httpx.Request("POST", client.token_url),
    )
    with (
        patch(
            "httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response
        ),
        pytest.raises(KeycloakAuthException),
    ):
        await client.get_service_account_token(force_refresh=True)


@pytest.mark.asyncio
async def test_create_user_success_with_location_header(client):
    with patch.object(
        client,
        "get_service_account_token",
        new_callable=AsyncMock,
        return_value="mock-token",
    ):
        mock_response = httpx.Response(
            201,
            headers={
                "Location": "https://keycloak.example.com/admin/realms/test-realm/users/kc-user-uuid-999"
            },
            request=httpx.Request("POST", client.admin_users_url),
        )
        with patch(
            "httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response
        ):
            user_id = await client.create_user(
                email="test@example.com",
                first_name="Test",
                last_name="User",
                password="Password123!",
            )
            assert user_id == "kc-user-uuid-999"


@pytest.mark.asyncio
async def test_create_user_conflict(client):
    with patch.object(
        client,
        "get_service_account_token",
        new_callable=AsyncMock,
        return_value="mock-token",
    ):
        mock_response = httpx.Response(
            409,
            json={"errorMessage": "User exists with same email"},
            request=httpx.Request("POST", client.admin_users_url),
        )
        with (
            patch(
                "httpx.AsyncClient.post",
                new_callable=AsyncMock,
                return_value=mock_response,
            ),
            pytest.raises(KeycloakConflictException),
        ):
            await client.create_user(
                email="duplicate@example.com",
                first_name="Dup",
                last_name="User",
                password="Password123!",
            )


@pytest.mark.asyncio
async def test_create_user_forbidden(client):
    with patch.object(
        client,
        "get_service_account_token",
        new_callable=AsyncMock,
        return_value="mock-token",
    ):
        mock_response = httpx.Response(
            403,
            text="Forbidden",
            request=httpx.Request("POST", client.admin_users_url),
        )
        with patch(
            "httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response
        ):
            with pytest.raises(KeycloakException) as exc_info:
                await client.create_user(
                    email="test@example.com",
                    first_name="Test",
                    last_name="User",
                    password="Password123!",
                )
            assert exc_info.value.status_code == 502


@pytest.mark.asyncio
async def test_delete_user_for_rollback(client):
    with patch.object(
        client,
        "get_service_account_token",
        new_callable=AsyncMock,
        return_value="mock-token",
    ):
        mock_response = httpx.Response(
            204,
            request=httpx.Request("DELETE", f"{client.admin_users_url}/kc-123"),
        )
        with patch(
            "httpx.AsyncClient.delete",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            success = await client.delete_user("kc-123")
            assert success is True
