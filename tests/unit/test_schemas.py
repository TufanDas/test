import pytest
from pydantic import ValidationError

from app.modules.tenants.schemas import (
    TenantSignupRequest,
    TenantSignupResponse,
)


def test_valid_tenant_signup_request():
    data = {
        "tenant_name": "The Food House",
        "owner": {
            "first_name": "Sneha",
            "last_name": "Roy",
            "email": "sneha@example.com",
            "password": "StrongPassword123!",
        },
    }
    req = TenantSignupRequest(**data)
    assert req.tenant_name == "The Food House"
    assert req.owner.email == "sneha@example.com"
    assert req.owner.first_name == "Sneha"
    assert req.owner.last_name == "Roy"
    assert req.owner.password == "StrongPassword123!"


def test_invalid_email_raises_validation_error():
    with pytest.raises(ValidationError) as exc_info:
        TenantSignupRequest(
            tenant_name="The Food House",
            owner={
                "first_name": "Sneha",
                "last_name": "Roy",
                "email": "not-a-valid-email",
                "password": "StrongPassword123!",
            },
        )
    assert "email" in str(exc_info.value)


def test_invalid_password_too_short():
    with pytest.raises(ValidationError) as exc_info:
        TenantSignupRequest(
            tenant_name="The Food House",
            owner={
                "first_name": "Sneha",
                "last_name": "Roy",
                "email": "sneha@example.com",
                "password": "short",
            },
        )
    assert "password" in str(exc_info.value)


def test_blank_tenant_name_raises_error():
    with pytest.raises(ValidationError):
        TenantSignupRequest(
            tenant_name="   ",
            owner={
                "first_name": "Sneha",
                "last_name": "Roy",
                "email": "sneha@example.com",
                "password": "StrongPassword123!",
            },
        )


def test_blank_owner_name_raises_error():
    with pytest.raises(ValidationError):
        TenantSignupRequest(
            tenant_name="Valid Tenant",
            owner={
                "first_name": "   ",
                "last_name": "Roy",
                "email": "sneha@example.com",
                "password": "StrongPassword123!",
            },
        )


def test_tenant_signup_response_schema():
    resp = TenantSignupResponse(
        message="Tenant registration successful",
        tenant_id="tenant_001",
        user_id="user_001",
    )
    assert resp.tenant_id == "tenant_001"
    assert resp.user_id == "user_001"
    assert "password" not in resp.model_dump()
