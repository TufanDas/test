from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Application
    APP_NAME: str = "Restaurant Management Backend"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"
    DEBUG: bool = True

    # API
    API_V1_PREFIX: str = "/api/v1"

    # Database - MongoDB
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DATABASE: str = "restaurant_management"

    # CORS
    CORS_ORIGINS: str | list[str] = "http://localhost:3000"

    # Keycloak Configuration
    KEYCLOAK_URL: str = "https://keycloak.fastteamdev.space/"
    KEYCLOAK_REALM: str = "erp-realm"
    KEYCLOAK_CLIENT_ID: str = "erp-backend-client"
    KEYCLOAK_CLIENT_SECRET: str = ""

    # Security
    JWT_ALGORITHM: str = "RS256"

    # Logging
    LOG_LEVEL: str = "INFO"

    @property
    def cors_origins_list(self) -> list[str]:
        if isinstance(self.CORS_ORIGINS, list):
            return self.CORS_ORIGINS
        return [
            origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()
        ]

    @property
    def keycloak_token_url(self) -> str:
        base = self.KEYCLOAK_URL.rstrip("/")
        return f"{base}/realms/{self.KEYCLOAK_REALM}/protocol/openid-connect/token"

    @property
    def keycloak_admin_users_url(self) -> str:
        base = self.KEYCLOAK_URL.rstrip("/")
        return f"{base}/admin/realms/{self.KEYCLOAK_REALM}/users"

    @property
    def keycloak_issuer_url(self) -> str:
        base = self.KEYCLOAK_URL.rstrip("/")
        return f"{base}/realms/{self.KEYCLOAK_REALM}"

    @property
    def keycloak_certs_url(self) -> str:
        base = self.KEYCLOAK_URL.rstrip("/")
        return f"{base}/realms/{self.KEYCLOAK_REALM}/protocol/openid-connect/certs"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
