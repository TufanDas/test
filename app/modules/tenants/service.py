import logging

from app.core.exceptions import (
    AppException,
    DatabaseException,
    DuplicateResourceException,
)
from app.modules.authentication.keycloak import KeycloakClient, keycloak_client
from app.modules.tenants.repository import TenantRepository, tenant_repository
from app.modules.tenants.schemas import TenantSignupRequest, TenantSignupResponse
from app.modules.users.repository import UserRepository, user_repository

logger = logging.getLogger(__name__)


class TenantService:
    """Main orchestration layer for Tenant business operations."""

    def __init__(
        self,
        tenant_repo: TenantRepository | None = None,
        user_repo: UserRepository | None = None,
        kc_client: KeycloakClient | None = None,
    ):
        self.tenant_repo = tenant_repo or tenant_repository
        self.user_repo = user_repo or user_repository
        self.keycloak_client = kc_client or keycloak_client

    async def signup_tenant(self, request: TenantSignupRequest) -> TenantSignupResponse:
        """Register a new restaurant business/tenant and its initial owner.

        Orchestration steps:
        1. Check existing application data (MongoDB email & tenant uniqueness)
        2. Create Keycloak user identity
        3. Create MongoDB application user
        4. Create MongoDB tenant
        5. Create MongoDB membership (Role: OWNER, Scope: TENANT)
        6. Return TenantSignupResponse

        Rollback strategy:
        If any step fails after Keycloak user creation, compensates by deleting
        any created MongoDB records and deleting the Keycloak user.
        """
        email = request.owner.email.strip().lower()
        tenant_name = request.tenant_name.strip()

        # Step 1: Pre-validation checks against MongoDB
        if await self.user_repo.check_user_exists_by_email(email):
            logger.warning(
                f"Registration rejected: user with email {email} already exists in database."
            )
            raise DuplicateResourceException("A user with this email already exists.")

        if await self.tenant_repo.check_tenant_name_exists(tenant_name):
            logger.warning(
                f"Registration rejected: tenant '{tenant_name}' already exists."
            )
            raise DuplicateResourceException("A tenant with this name already exists.")

        # Step 2: Create user in Keycloak (Identity Provider)
        # Passwords are never logged or stored in MongoDB
        keycloak_user_id = await self.keycloak_client.create_user(
            email=email,
            first_name=request.owner.first_name,
            last_name=request.owner.last_name,
            password=request.owner.password,
            enabled=True,
            email_verified=True,
        )

        created_user_id: str | None = None
        created_tenant_id: str | None = None
        created_membership_id: str | None = None

        try:
            # Step 3: Create Application User in MongoDB
            user_doc = await self.user_repo.create_user(
                keycloak_user_id=keycloak_user_id,
                email=email,
                first_name=request.owner.first_name,
                last_name=request.owner.last_name,
                status="ACTIVE",
            )
            created_user_id = user_doc["_id"]

            # Step 4: Create Tenant in MongoDB
            tenant_doc = await self.tenant_repo.create_tenant(
                name=tenant_name,
                status="ACTIVE",
            )
            created_tenant_id = tenant_doc["_id"]

            # Step 5: Create Membership linking User and Tenant with OWNER role & TENANT scope
            membership_doc = await self.tenant_repo.create_membership(
                user_id=created_user_id,
                tenant_id=created_tenant_id,
                role="OWNER",
                scope="TENANT",
                status="ACTIVE",
            )
            created_membership_id = membership_doc["_id"]

            logger.info(
                f"Successfully registered tenant {created_tenant_id} ('{tenant_name}') "
                f"with owner user {created_user_id} and membership {created_membership_id}"
            )

            return TenantSignupResponse(
                message="Tenant registration successful",
                tenant_id=created_tenant_id,
                user_id=created_user_id,
            )

        except Exception as exc:
            logger.error(
                f"Failure during tenant creation workflow after Keycloak user was created: {exc}. "
                f"Executing rollback compensation for Keycloak user {keycloak_user_id}..."
            )
            # Rollback any created MongoDB records
            if created_membership_id:
                try:
                    await self.tenant_repo.delete_membership(created_membership_id)
                except Exception as rollback_err:
                    logger.error(
                        f"Error rolling back membership {created_membership_id}: {rollback_err}"
                    )

            if created_tenant_id:
                try:
                    await self.tenant_repo.delete_tenant(created_tenant_id)
                except Exception as rollback_err:
                    logger.error(
                        f"Error rolling back tenant {created_tenant_id}: {rollback_err}"
                    )

            if created_user_id:
                try:
                    await self.user_repo.delete_user(created_user_id)
                except Exception as rollback_err:
                    logger.error(
                        f"Error rolling back user {created_user_id}: {rollback_err}"
                    )

            # Rollback Keycloak user identity
            try:
                await self.keycloak_client.delete_user(keycloak_user_id)
            except Exception as rollback_err:
                logger.error(
                    f"Error rolling back Keycloak user {keycloak_user_id}: {rollback_err}"
                )

            if isinstance(exc, AppException):
                raise
            raise DatabaseException(
                f"Failed to complete tenant registration: {exc!s}"
            ) from exc


tenant_service = TenantService()
