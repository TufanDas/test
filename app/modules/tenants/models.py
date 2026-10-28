from datetime import UTC, datetime

from pydantic import BaseModel, Field


def get_utc_now() -> datetime:
    return datetime.now(UTC)


class TenantModel(BaseModel):
    id: str = Field(alias="_id")
    name: str
    status: str = "ACTIVE"
    created_at: datetime = Field(default_factory=get_utc_now)
    updated_at: datetime = Field(default_factory=get_utc_now)

    class Config:
        populate_by_name = True


class MembershipModel(BaseModel):
    id: str = Field(alias="_id")
    user_id: str
    tenant_id: str
    role: str = "OWNER"
    scope: str = "TENANT"
    status: str = "ACTIVE"
    created_at: datetime = Field(default_factory=get_utc_now)
    updated_at: datetime = Field(default_factory=get_utc_now)

    class Config:
        populate_by_name = True
