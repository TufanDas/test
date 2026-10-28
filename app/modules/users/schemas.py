from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserResponse(BaseModel):
    id: str
    keycloak_user_id: str
    email: EmailStr
    first_name: str
    last_name: str
    status: str
    created_at: datetime
    updated_at: datetime
