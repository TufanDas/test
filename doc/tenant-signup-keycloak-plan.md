# Tenant Sign-Up API — Keycloak Implementation Plan

## 1. Objective

Implement a **Tenant Sign-Up API** for the Restaurant Management Backend using:

- FastAPI
- MongoDB
- Keycloak
- Pydantic
- PyMongo
- Company's Keycloak server

The API will create:

1. A **Keycloak user**
2. An **application user** in MongoDB
3. A **tenant** in MongoDB
4. A **membership** connecting the user to the tenant
5. An initial **tenant-level role/membership**

The design follows the project's existing multi-tenant architecture where a tenant represents a business organization and a membership defines a user's association with that tenant.

---

# 2. Key Design Principle

The system will have a clear separation of responsibilities.

```text
                    Tenant Sign Up
                          |
                          v
                    FastAPI API
                          |
             +------------+-------------+
             |                          |
             v                          v
       Authentication                Tenants
          Module                     Module
             |                          |
             v                          v
         Keycloak                    MongoDB
             |                          |
             |                  +-------+-------+
             |                  |       |       |
             |                User   Tenant  Membership
             |
             v
       Keycloak User
```

### Keycloak owns

- User identity
- Password
- Authentication
- User credentials
- Email verification
- Access/refresh tokens

### MongoDB owns

- Application user profile
- Tenant
- Membership
- Application roles
- Permissions
- Restaurant/business data

This follows the README's architecture where Keycloak handles authentication and identity management while FastAPI handles application-level authorization, membership, permissions, and tenant isolation.

---

# 3. Keycloak Configuration

Use the company's Keycloak server:

```env
KEYCLOAK_URL=https://keycloak.fastteamdev.space/
KEYCLOAK_REALM=erp-realm
KEYCLOAK_CLIENT_ID=erp-backend-client
KEYCLOAK_CLIENT_SECRET=<configured-secret>
JWT_ALGORITHM=RS256
```

The secret must remain in `.env` and must **never be committed to Git**. The README explicitly requires secrets to stay out of committed `.env` files and recommends `.env.example` for documenting configuration.

## Keycloak Client

Use:

```text
erp-backend-client
```

This client is responsible for backend-to-Keycloak communication.

Required capability:

```text
Client authentication: ON
Service account roles: ON
```

The service account will be used by FastAPI to obtain a Keycloak access token for administrative user-management operations.

Keycloak's Admin REST API provides:

```http
POST /admin/realms/{realm}/users
```

for creating users. The operation requires appropriate administrative permissions and can return `201 Created`, `403 Forbidden`, or `409 Conflict`. 

---

# 4. Required Keycloak Permission

Before implementing the API, verify:

```text
erp-backend-client
        |
        v
Service account roles
        |
        v
realm-management
```

The service account should have the minimum required permissions.

Initially verify:

```text
manage-users
view-users
```

`manage-users` permits management/creation of users, while `view-users` permits user lookup. Keycloak documents these as realm-management roles for user administration. 

Do not grant unnecessary administrator permissions.

---

# 5. API Design

## Endpoint

```http
POST /api/v1/tenants/signup
```

### Purpose

Register a new restaurant business/tenant and its initial owner.

---

# 6. Request Schema

Suggested request:

```json
{
  "tenant_name": "The Food House",
  "owner": {
    "first_name": "Sneha",
    "last_name": "Roy",
    "email": "sneha@example.com",
    "password": "StrongPassword123!"
  }
}
```

### Important

The password is sent only for the registration operation.

It must:

- Never be logged
- Never be stored in MongoDB
- Never be returned in the API response

The password will be handled by Keycloak.

---

# 7. Response Schema

Successful registration:

```json
{
  "message": "Tenant registration successful",
  "tenant_id": "tenant_001",
  "user_id": "user_001"
}
```

Do not return:

```text
password
Keycloak client secret
Keycloak service-account token
```

---

# 8. Project Structure

Strictly follow the README structure.

```text
restaurant-management-backend/
│
├── app/
│   ├── main.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── security.py
│   │   └── exceptions.py
│   │
│   ├── api/
│   │   └── v1/
│   │       └── router.py
│   │
│   ├── modules/
│   │   │
│   │   ├── authentication/
│   │   │   ├── __init__.py
│   │   │   ├── router.py
│   │   │   ├── service.py
│   │   │   ├── repository.py
│   │   │   ├── schemas.py
│   │   │   ├── models.py
│   │   │   └── dependencies.py
│   │   │   └── keycloak.py
│   │   │
│   │   ├── tenants/
│   │   │   ├── __init__.py
│   │   │   ├── router.py
│   │   │   ├── service.py
│   │   │   ├── repository.py
│   │   │   ├── schemas.py
│   │   │   ├── models.py
│   │   │   └── dependencies.py
│   │   │
│   │   └── users/
│   │       ├── ...
│   │
│   └── common/
│       ├── dependencies.py
│       ├── pagination.py
│       └── utils.py
│
└── tests/
    ├── unit/
    └── integration/
```

This structure follows the README's defined modular-monolith organization and module responsibilities.

---

# 9. Responsibility of Each File

## `authentication/keycloak.py`

Responsible only for communication with Keycloak.

Responsibilities:

```text
Get service-account token
        ↓
Create Keycloak user
        ↓
Find Keycloak user
        ↓
Set user credentials if required
        ↓
Delete Keycloak user if rollback is required
```

It should NOT contain tenant business logic.

---

## `authentication/service.py`

Responsible for authentication-related business operations.

For this feature it will coordinate Keycloak operations when appropriate.

---

## `authentication/schemas.py`

Only authentication-related request/response schemas should be placed here.

Do not put tenant database schemas here.

---

## `tenants/router.py`

Responsible for:

```http
POST /api/v1/tenants/signup
```

The router should:

1. Receive request
2. Validate request through Pydantic
3. Call tenant service
4. Return response

Business logic should not be placed directly inside the route handler.

The README explicitly states that business logic should remain outside API route handlers.

---

## `tenants/service.py`

This is the **main orchestration layer**.

It coordinates:

```text
Validate registration
        ↓
Create Keycloak user
        ↓
Create MongoDB application user
        ↓
Create tenant
        ↓
Create membership
        ↓
Assign initial role
        ↓
Return registration result
```

---

## `tenants/repository.py`

Responsible only for MongoDB operations:

```text
create tenant
create membership
check existing tenant
```

It should not call Keycloak.

---

## `tenants/schemas.py`

Define:

```text
TenantSignupRequest
OwnerSignupRequest
TenantSignupResponse
```

Example conceptual structure:

```text
TenantSignupRequest
├── tenant_name
└── owner
    ├── first_name
    ├── last_name
    ├── email
    └── password
```

---

## `tenants/models.py`

Define the MongoDB document structures for the tenant domain.

For example:

```text
Tenant
Membership
```

The project already defines `tenants`, `users`, and `memberships` as planned MongoDB collections.

---

## `tenants/dependencies.py`

Keep tenant-specific dependencies here.

Examples:

```text
tenant context
tenant authorization
tenant-related dependencies
```

For public signup, authentication should not be required because the user does not have an access token yet.

---

# 10. Detailed Registration Flow

## Step 1 — Client sends signup request

```http
POST /api/v1/tenants/signup
```

```json
{
  "tenant_name": "The Food House",
  "owner": {
    "first_name": "Sneha",
    "last_name": "Roy",
    "email": "sneha@example.com",
    "password": "StrongPassword123!"
  }
}
```

---

## Step 2 — FastAPI validates request

Pydantic validates:

```text
tenant_name
first_name
last_name
email
password
```

Invalid request:

```text
422 Unprocessable Entity
```

---

# 11. Step 3 — Check Existing Application Data

Before creating anything:

```text
Check email
      ↓
Does application user already exist?
      |
      +---- YES → Conflict
      |
      +---- NO → Continue
```

Also check whether the requested tenant name/slug violates the project's tenant uniqueness rules once those rules are finalized.

---

# 12. Step 4 — Obtain Keycloak Service Token

FastAPI uses:

```text
erp-backend-client
```

to authenticate as its service account.

Conceptually:

```text
FastAPI
   |
   | client_id
   | client_secret
   v
Keycloak token endpoint
   |
   v
Service account access token
```

The service-account token is used internally by the backend to call Keycloak's Admin REST API.

---

# 13. Step 5 — Create Keycloak User

FastAPI calls:

```http
POST /admin/realms/erp-realm/users
```

with the appropriate Keycloak user representation.

Conceptually:

```json
{
  "username": "sneha@example.com",
  "email": "sneha@example.com",
  "firstName": "Sneha",
  "lastName": "Roy",
  "enabled": true
}
```

Keycloak's Admin REST API defines this endpoint for creating a new user. 

---

# 14. Step 6 — Configure Keycloak Credentials

After the user is created, obtain the newly created Keycloak user ID.

Then configure the initial credential according to the company's Keycloak policy.

Conceptually:

```text
Keycloak User
      |
      v
Set initial password
      |
      v
Password managed by Keycloak
```

Do not store the password in MongoDB.

The exact password/email-verification behavior should follow the company's Keycloak configuration rather than being invented by the backend.

---

# 15. Step 7 — Create MongoDB User

After successful Keycloak creation:

```text
users
```

should contain the application's user representation.

Example:

```json
{
  "_id": "user_001",
  "keycloak_user_id": "KEYCLOAK_USER_ID",
  "email": "sneha@example.com",
  "first_name": "Sneha",
  "last_name": "Roy",
  "status": "ACTIVE"
}
```

The most important relationship is:

```text
MongoDB users.keycloak_user_id
                |
                v
        Keycloak User ID
```

Do not use the email address as the permanent identity mapping.

---

# 16. Step 8 — Create Tenant

Create:

```text
tenants
```

Example:

```json
{
  "_id": "tenant_001",
  "name": "The Food House",
  "status": "ACTIVE"
}
```

The README defines a tenant as a business organization registered on the platform.

---

# 17. Step 9 — Create Membership

Create the relationship:

```text
User
  |
  | membership
  v
Tenant
```

Example:

```json
{
  "_id": "membership_001",
  "user_id": "user_001",
  "tenant_id": "tenant_001",
  "role": "OWNER",
  "scope": "TENANT"
}
```

This is important because the project does not treat a user and tenant as a direct one-to-one relationship. The README explicitly defines `Membership` as the entity that establishes a user's association with a tenant.

---

# 18. Step 10 — Assign Initial Role

For the person creating the tenant:

```text
Role = OWNER
Scope = TENANT
```

Conceptually:

```text
Sneha
  |
  +── Tenant: The Food House
           |
           +── OWNER
           +── TENANT scope
```

The exact role/permission model should use the project's existing `roles` and `permissions` design rather than introducing a separate authorization system.

---

# 19. Step 11 — Return Response

Successful result:

```http
201 Created
```

```json
{
  "message": "Tenant registration successful",
  "tenant_id": "tenant_001",
  "user_id": "user_001"
}
```

No password or Keycloak service token should be returned.

---

# 20. Error Handling

The API should explicitly handle:

### Duplicate email

```text
409 Conflict
```

Possible response:

```json
{
  "detail": "A user with this email already exists."
}
```

Keycloak's create-user API itself documents `409 Conflict` for conflicts such as an already-existing user. 

### Keycloak authentication failure

```text
502 Bad Gateway
```

or an appropriate service-integration error.

### Keycloak permission failure

```text
502/503
```

Internally log the actual Keycloak response, but do not expose sensitive Keycloak details to the client.

### MongoDB failure

Return an appropriate server error and execute the defined compensation strategy.

---

# 21. Rollback Strategy

This is critical because registration spans two systems:

```text
Keycloak
   +
MongoDB
```

Example:

```text
Create Keycloak user       ✓
        ↓
Create MongoDB user        ✓
        ↓
Create tenant              ✗
```

We must avoid leaving an unusable Keycloak account.

Recommended initial strategy:

```text
Start registration
       |
       v
Create Keycloak user
       |
       v
Create MongoDB user
       |
       v
Create tenant
       |
       v
Create membership
       |
       v
Success
```

If a later operation fails:

```text
Rollback / compensation
        |
        v
Delete Keycloak user
```

The Keycloak Admin API supports deleting a user through:

```http
DELETE /admin/realms/{realm}/users/{user-id}
```

 

The exact transaction/compensation mechanism should be finalized with the project's database requirements.

---

# 22. Authentication After Signup

Signup itself is:

```text
Public
```

because the user does not have a token yet.

After signup:

```text
User
  ↓
Keycloak Login
  ↓
Access Token
  ↓
FastAPI
  ↓
JWT Validation
  ↓
MongoDB User
  ↓
Membership
  ↓
Tenant
  ↓
Permissions
```

The README specifies that FastAPI validates Keycloak access tokens and then performs membership and permission checks.

---

# 23. JWT Validation

The existing configuration:

```env
JWT_ALGORITHM=RS256
```

will be used by the authentication/security layer for validating Keycloak-issued JWTs.

The backend should validate at minimum:

```text
Signature
Issuer
Audience
Expiration
Algorithm
Subject
```

Then:

```text
JWT.sub
   ↓
Keycloak user ID
   ↓
MongoDB users.keycloak_user_id
```

---

# 24. API Registration in Routers

The versioned API structure is:

```text
app/api/v1/router.py
```

The tenant router should be included there.

Conceptually:

```text
app/api/v1/router.py
        |
        +── authentication.router
        |
        +── tenants.router
        |
        +── users.router
        |
        +── ...
```

The README requires API versioning under:

```text
/api/v1
```

and defines tenant endpoints under this versioned structure.

---

# 25. Testing Plan

Create tests following the existing:

```text
tests/
├── unit/
└── integration/
```

structure.

## Unit Tests

Test:

```text
TenantSignupRequest validation
Email validation
Password validation
Tenant service logic
Membership creation logic
```

## Integration Tests

Test:

```text
POST /api/v1/tenants/signup
```

Scenarios:

### Test 1 — Successful signup

```text
201 Created
```

### Test 2 — Duplicate email

```text
409 Conflict
```

### Test 3 — Invalid email

```text
422
```

### Test 4 — Invalid password

```text
422
```

### Test 5 — Keycloak unavailable

```text
5xx
```

### Test 6 — Keycloak permission denied

```text
403/5xx
```

### Test 7 — MongoDB failure

Verify compensation behavior.

### Test 8 — Verify tenant isolation

Ensure the created membership connects the correct user and tenant.

---

# 26. Implementation Sequence

Implement in this exact order.

```text
PHASE 1
Configuration
    ↓
Verify Keycloak environment variables
    ↓
Verify erp-backend-client
    ↓
Verify service-account roles
```

```text
PHASE 2
Authentication Module
    ↓
Implement Keycloak client
    ↓
Get service-account token
    ↓
Test Keycloak connectivity
```

```text
PHASE 3
Tenant Schemas
    ↓
TenantSignupRequest
    ↓
TenantSignupResponse
```

```text
PHASE 4
Tenant Repository
    ↓
Create tenant
    ↓
Check existing user
    ↓
Create membership
```

```text
PHASE 5
Tenant Service
    ↓
Orchestrate Keycloak + MongoDB
```

```text
PHASE 6
Tenant Router
    ↓
POST /api/v1/tenants/signup
```

```text
PHASE 7
Error Handling
    ↓
Duplicate user
    ↓
Keycloak failure
    ↓
MongoDB failure
    ↓
Rollback
```

```text
PHASE 8
Testing
    ↓
Unit tests
    ↓
Integration tests
    ↓
Manual Swagger testing
```

---

# 27. Final Target Architecture

```text
                         FRONTEND
                            |
                            |
                    POST /api/v1/tenants/signup
                            |
                            v
                 ┌─────────────────────┐
                 │   tenants/router.py │
                 └──────────┬──────────┘
                            |
                            v
                 ┌─────────────────────┐
                 │  tenants/service.py │
                 └───────┬───────┬─────┘
                         |       |
              Keycloak   |       | MongoDB
                         |       |
                         v       v
               ┌────────────┐  ┌─────────────┐
               │authentication│  │  Tenant     │
               │  /keycloak   │  │ Repository  │
               └──────┬──────┘  └──────┬──────┘
                      |                 |
                      v                 v
                 Keycloak           MongoDB
                      |                 |
                      |          ┌──────┼──────┐
                      |          |      |      |
                      |        users tenants memberships
                      |
                      v
                Keycloak User
```

## Final ownership

| Component | Responsibility |
|---|---|
| `authentication/keycloak.py` | Keycloak communication |
| `authentication/service.py` | Authentication-related service logic |
| `tenants/router.py` | Tenant signup HTTP endpoint |
| `tenants/service.py` | Signup orchestration |
| `tenants/repository.py` | Tenant/Membership database operations |
| `tenants/schemas.py` | Signup request/response validation |
| `tenants/models.py` | Tenant-domain MongoDB models |
| `tenants/dependencies.py` | Tenant-specific dependencies |
| `core/config.py` | Environment configuration |
| `core/security.py` | JWT/security functionality |
| `api/v1/router.py` | API router registration |
| `tests/unit/` | Unit tests |
| `tests/integration/` | Keycloak/MongoDB/API integration tests |

---

# 28. Definition of Done

The Tenant Sign-Up feature will be considered complete when:

- [ ] `erp-backend-client` can authenticate as a service account
- [ ] Required Keycloak user-management permissions are verified
- [ ] FastAPI can obtain a Keycloak service token
- [ ] FastAPI can create a Keycloak user
- [ ] Keycloak user ID is obtained
- [ ] MongoDB application user is created
- [ ] MongoDB tenant is created
- [ ] MongoDB membership is created
- [ ] Initial tenant owner role is assigned
- [ ] Password is never stored in MongoDB
- [ ] Duplicate registration is handled
- [ ] Keycloak failures are handled
- [ ] MongoDB failures are handled
- [ ] Compensation/rollback is implemented
- [ ] API returns `201 Created` on success
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Swagger testing succeeds
- [ ] No secrets are committed to Git
- [ ] Existing project structure remains unchanged

## Expected final flow

```text
Tenant Owner
     |
     | Sign Up
     v
POST /api/v1/tenants/signup
     |
     v
FastAPI
     |
     +--------------------+
     |                    |
     v                    v
Keycloak              MongoDB
     |                    |
     |                    +── User
     |                    +── Tenant
     |                    +── Membership
     |
     +── Identity
     +── Password
     +── Authentication
     |
     v
Registration Complete
```
