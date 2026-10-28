from pydantic import BaseModel, EmailStr, Field, field_validator


class OwnerSignupRequest(BaseModel):
    first_name: str = Field(
        ..., min_length=1, max_length=50, description="Owner first name"
    )
    last_name: str = Field(
        ..., min_length=1, max_length=50, description="Owner last name"
    )
    email: EmailStr = Field(..., description="Owner email address")
    password: str = Field(
        ..., min_length=8, max_length=128, description="Owner account password"
    )

    @field_validator("first_name", "last_name")
    @classmethod
    def strip_and_validate_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Name cannot be empty or whitespace only")
        return cleaned

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return value


class TenantSignupRequest(BaseModel):
    tenant_name: str = Field(
        ..., min_length=2, max_length=100, description="Restaurant business/tenant name"
    )
    owner: OwnerSignupRequest

    @field_validator("tenant_name")
    @classmethod
    def strip_and_validate_tenant_name(cls, value: str) -> str:
        cleaned = value.strip()
        if len(cleaned) < 2:
            raise ValueError(
                "Tenant name must have at least 2 non-whitespace characters"
            )
        return cleaned


class TenantSignupResponse(BaseModel):
    message: str = "Tenant registration successful"
    tenant_id: str
    user_id: str
