from datetime import UTC, datetime

from pydantic import BaseModel, EmailStr, Field


def get_utc_now() -> datetime:
    return datetime.now(UTC)


class UserModel(BaseModel):
    id: str = Field(alias="_id")
    keycloak_user_id: str
    email: EmailStr
    first_name: str
    last_name: str
    status: str = "ACTIVE"
    created_at: datetime = Field(default_factory=get_utc_now)
    updated_at: datetime = Field(default_factory=get_utc_now)

    class Config:
        populate_by_name = True
