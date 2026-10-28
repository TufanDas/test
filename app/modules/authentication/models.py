from pydantic import BaseModel


class AuthenticatedUser(BaseModel):
    keycloak_user_id: str
    email: str | None = None
    username: str | None = None
