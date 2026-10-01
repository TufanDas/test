# Restaurant Management Backend

A multi-tenant Restaurant Management System (RMS) backend built with
**FastAPI, MongoDB, and Python**. The project follows a modular monolith
architecture, allowing multiple business domains to be developed and
maintained independently within a single repository.

## 1. Overview

The Restaurant Management System is designed to support restaurant
businesses, restaurant groups, and multiple branches through a
centralized platform.

The backend provides APIs for managing tenants, users, restaurants,
branches, menus, orders, billing, inventory, and other restaurant
operations.

### Key Features

-   **Multi-tenancy:** Support for multiple restaurant businesses on a
    single platform.
-   **Authentication:** Keycloak-based authentication and identity
    management.
-   **Role-Based Access Control (RBAC):** Role- and permission-based
    authorization.
-   **Restaurant Management:** Manage restaurants and their associated
    branches.
-   **User Management:** Manage users and their memberships across
    tenants.
-   **Modular Architecture:** Organize business domains into independent
    modules.
-   **REST API:** Versioned RESTful APIs built with FastAPI.
-   **MongoDB:** Flexible document-oriented data storage.
-   **Asynchronous Operations:** Async database access using PyMongo.

> **Note:** Features are implemented incrementally. The list describes
> the intended system capabilities, not necessarily the current
> implementation status.

## 2. Technology Stack

  Technology          Purpose
  ------------------- ------------------------------------------
  Python 3.12         Backend programming language
  FastAPI             REST API framework
  MongoDB             Primary database
  PyMongo             MongoDB driver with asynchronous support
  uv                  Python package and project management
  Pydantic            Data validation and serialization
  Pydantic Settings   Application configuration
  Keycloak            Authentication and identity management
  Pytest              Automated testing
  Ruff                Linting and code formatting
  Docker              Local development and deployment

## 3. Architecture

The project follows a **modular monolith architecture**.

All business modules reside in a single repository and run as one
application. Each module has its own API routes, business logic, data
access, and schemas.

This approach keeps initial development and deployment straightforward
while maintaining clear boundaries between business domains.

### Architecture Overview

``` text
                   Frontend
                 (Next.js)
                     |
                     v
              FastAPI Backend
                     |
          +----------+----------+
          |                     |
          v                     v
   Authentication          API Router
       Module                  |
          |          +---------+----------+
          v          |         |          |
      Keycloak       v         v          v
                  Tenants    Users    Restaurants
                     |         |          |
                     +---------+----------+
                               |
                               v
                            MongoDB
```

## 4. Project Structure

The backend is organized into modules based on business domains. Each
module is responsible for its own API endpoints, business logic, data
access, and schemas.

``` text
restaurant-management-backend/
├── app/
│   ├── main.py
│   ├── core/
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── security.py
│   │   └── exceptions.py
│   ├── api/
│   │   └── v1/
│   │       └── router.py
│   ├── modules/
│   │   ├── authentication/
│   │   ├── tenants/
│   │   ├── users/
│   │   ├── roles/
│   │   ├── permissions/
│   │   ├── restaurants/
│   │   ├── branches/
│   │   ├── menus/
│   │   ├── orders/
│   │   ├── billing/
│   │   ├── inventory/
│   │   ├── employees/
│   │   └── reports/
│   └── common/
│       ├── dependencies.py
│       ├── pagination.py
│       └── utils.py
├── tests/
│   ├── unit/
│   └── integration/
├── .env
├── .env.example
├── .gitignore
├── .python-version
├── pyproject.toml
├── uv.lock
├── docker-compose.yml
└── README.md
```

### Module Responsibilities

  Module             Responsibility
  ------------------ --------------------------------------------------
  `authentication`   Authentication integration and JWT validation
  `tenants`          Tenant registration and management
  `users`            Application user profiles and user management
  `roles`            Role creation and management
  `permissions`      Permission definitions and authorization
  `restaurants`      Restaurant creation and management
  `branches`         Branch management and configuration
  `menus`            Menu categories, items, and pricing
  `orders`           Order creation and order lifecycle
  `billing`          Invoices, payments, and billing operations
  `inventory`        Stock, ingredients, and inventory management
  `employees`        Employee records and restaurant staff management
  `reports`          Business reports and analytics

Each module should follow a consistent internal structure as it grows.

Example:

``` text
modules/
└── tenants/
    ├── __init__.py
    ├── router.py
    ├── service.py
    ├── repository.py
    ├── schemas.py
    ├── models.py
    └── dependencies.py
```

-   **Router:** Defines API endpoints and handles HTTP requests.
-   **Service:** Contains business logic and application rules.
-   **Repository:** Handles database operations.
-   **Schemas:** Defines request and response validation.
-   **Models:** Defines database document structures.
-   **Dependencies:** Provides module-specific dependencies when
    required.

## 5. Multi-Tenant Architecture

The system uses a hierarchical multi-tenant architecture to support
multiple restaurant businesses.

### Organizational Hierarchy

``` text
Platform
   |
   ├── Tenant A
   |      |
   |      ├── Restaurant A1
   |      |      ├── Branch A1-1
   |      |      └── Branch A1-2
   |      |
   |      └── Restaurant A2
   |             └── Branch A2-1
   |
   └── Tenant B
          |
          └── Restaurant B1
                 ├── Branch B1-1
                 └── Branch B1-2
```

### Hierarchy Definitions

  -----------------------------------------------------------------------
  Entity                              Description
  ----------------------------------- -----------------------------------
  Platform                            The central system that manages all
                                      tenants

  Tenant                              A business organization registered
                                      on the platform

  Restaurant                          A restaurant owned or managed by a
                                      tenant

  Branch                              A physical or operational location
                                      belonging to a restaurant

  User                                A person who can access one or more
                                      tenants

  Membership                          Defines a user's association with a
                                      tenant and their access
  -----------------------------------------------------------------------

### Tenant Isolation

Every tenant-owned resource must be associated with the appropriate
tenant.

Example restaurant document:

``` json
{
  "_id": "restaurant_001",
  "tenant_id": "tenant_001",
  "name": "The Food House",
  "status": "ACTIVE",
  "created_at": "2026-01-01T10:00:00Z",
  "updated_at": "2026-01-01T10:00:00Z"
}
```

The backend must enforce tenant isolation when retrieving, creating,
updating, or deleting tenant-owned resources.

Tenant IDs received from the frontend must never be treated as proof of
authorization. The backend must verify the authenticated user's
membership and permissions.

## 6. Authentication and Authorization

The system uses Keycloak for authentication and the backend for
application-level authorization.

### Authentication with Keycloak

Keycloak is responsible for:

-   User authentication
-   Password management
-   Single sign-on (SSO)
-   Multi-factor authentication (MFA)
-   Access token issuance
-   Refresh token management
-   Session management
-   Identity provider integration

The FastAPI backend validates access tokens issued by Keycloak before
allowing access to protected endpoints.

### Authorization in the Backend

The backend is responsible for:

-   User membership validation
-   Role assignment
-   Permission checking
-   Tenant isolation
-   Restaurant-level access control
-   Branch-level access control
-   Resource-level authorization

### Authentication Flow

``` text
Frontend
   |
   | 1. User initiates login
   v
Keycloak
   |
   | 2. Authenticate user
   | 3. Issue access token
   v
Frontend
   |
   | 4. Send API request with token
   v
FastAPI Backend
   |
   | 5. Validate JWT
   | 6. Identify authenticated user
   | 7. Verify membership and permissions
   v
Business Module
   |
   | 8. Execute authorized operation
   v
MongoDB
```

### Authorization Scopes

  Scope          Description
  -------------- -------------------------------------------
  `PLATFORM`     Access across the entire platform
  `TENANT`       Access to resources belonging to a tenant
  `RESTAURANT`   Access to a specific restaurant
  `BRANCH`       Access to a specific branch

A user's permissions may differ depending on the scope. For example, a
user may have administrative permissions for one restaurant but only
read permissions for another.

## 7. Prerequisites

Before setting up the project, ensure that the following tools are
installed.

  Requirement      Version
  ---------------- ----------------------------------
  Python           3.12
  MongoDB          7.0 or compatible
  uv               Latest stable version
  Git              Latest stable version
  Docker           Latest stable version (optional)
  Docker Compose   Latest stable version (optional)

Keycloak is required when implementing or testing the authentication
integration.

### Verify Installations

``` bash
python --version
uv --version
git --version
docker --version
```

## 8. Installation and Setup

### 8.1 Clone the Repository

``` bash
git clone <repository-url>
cd restaurant-management-backend
```

Replace `<repository-url>` with the actual repository URL.

### 8.2 Configure Python

The project uses Python 3.12.

``` bash
uv python install 3.12
uv python pin 3.12
```

### 8.3 Install Dependencies

``` bash
uv sync
```

This command creates the virtual environment if necessary and installs
the dependencies defined in `pyproject.toml` and `uv.lock`.

### 8.4 Activate the Virtual Environment

On Linux or macOS:

``` bash
source .venv/bin/activate
```

On Windows PowerShell:

``` powershell
.venv\Scripts\Activate.ps1
```

Alternatively, run project commands directly through `uv` without
activating the environment.

## 9. Environment Configuration

The application uses environment variables to manage configuration.

Create a `.env` file in the project root.

``` dotenv
APP_NAME=Restaurant Management Backend
APP_VERSION=1.0.0
APP_ENV=development
DEBUG=true

API_V1_PREFIX=/api/v1

MONGODB_URL=mongodb://localhost:27017
MONGODB_DATABASE=restaurant_management

CORS_ORIGINS=http://localhost:3000

KEYCLOAK_URL=http://localhost:8080
KEYCLOAK_REALM=restaurant-management
KEYCLOAK_CLIENT_ID=restaurant-management-backend
KEYCLOAK_CLIENT_SECRET=

JWT_ALGORITHM=RS256

LOG_LEVEL=INFO
```

### Environment Variable Descriptions

  Variable                   Description
  -------------------------- --------------------------------
  `APP_NAME`                 Application name
  `APP_VERSION`              Current application version
  `APP_ENV`                  Application environment
  `DEBUG`                    Enables or disables debug mode
  `API_V1_PREFIX`            Base path for version 1 APIs
  `MONGODB_URL`              MongoDB connection string
  `MONGODB_DATABASE`         MongoDB database name
  `CORS_ORIGINS`             Allowed frontend origins
  `KEYCLOAK_URL`             Keycloak server URL
  `KEYCLOAK_REALM`           Keycloak realm
  `KEYCLOAK_CLIENT_ID`       Backend Keycloak client ID
  `KEYCLOAK_CLIENT_SECRET`   Client secret, if applicable
  `JWT_ALGORITHM`            Expected JWT signing algorithm
  `LOG_LEVEL`                Application logging level

**Important:**

-   Never commit `.env` files containing secrets.
-   Use `.env.example` to document required environment variables.
-   Use separate configurations for development, testing, and
    production.
-   Do not enable debug mode in production.
-   Configure production secrets through a secure secrets management
    solution.

## 10. Running the Application

### 10.1 Start MongoDB

If MongoDB is installed locally, start the MongoDB service.

Alternatively, use Docker Compose:

``` bash
docker compose up -d mongodb
```

Ensure that MongoDB is accessible using the connection string configured
in `.env`.

### 10.2 Start the FastAPI Application

``` bash
uv run uvicorn app.main:app --reload
```

The application will be available at:

``` text
http://localhost:8000
```

The `--reload` option automatically restarts the application when source
files change. It should only be used during development.

### 10.3 API Documentation

FastAPI provides interactive API documentation.

  Documentation   URL
  --------------- --------------------------------------
  Swagger UI      `http://localhost:8000/docs`
  ReDoc           `http://localhost:8000/redoc`
  OpenAPI JSON    `http://localhost:8000/openapi.json`

These endpoints can be used to explore and test the API. For production,
configure documentation access according to the application's security
requirements.

## 11. API Versioning

All REST API endpoints are grouped under a versioned prefix.

The current API prefix is:

``` text
/api/v1
```

### Example Endpoints

  Method     Endpoint                        Description
  ---------- ------------------------------- -------------------------
  `POST`     `/api/v1/tenants`               Create a tenant
  `GET`      `/api/v1/tenants`               List accessible tenants
  `GET`      `/api/v1/tenants/{tenant_id}`   Get tenant details
  `PATCH`    `/api/v1/tenants/{tenant_id}`   Update tenant details
  `DELETE`   `/api/v1/tenants/{tenant_id}`   Deactivate a tenant

These endpoints represent the planned API structure. Their availability
depends on implementation status.

### Versioning Guidelines

-   Introduce a new API version when making breaking changes.
-   Maintain backward compatibility within the same major API version
    whenever possible.
-   Avoid changing the meaning of existing request or response fields.
-   Document deprecated endpoints and provide a migration path.
-   Keep API schemas consistent across modules.

For example:

``` text
/api/v1/tenants
/api/v2/tenants
```

Both versions may coexist during a migration period if backward
compatibility is required.

## 12. Database Design

MongoDB is the primary database for the application.

The system uses collections to store documents belonging to different
business domains.

### Planned Collections

  Collection          Description
  ------------------- -------------------------------
  `tenants`           Tenant information
  `users`             Application user profiles
  `memberships`       User-to-tenant associations
  `roles`             Role definitions
  `permissions`       Permission definitions
  `restaurants`       Restaurant information
  `branches`          Restaurant branch information
  `menus`             Menu definitions
  `menu_categories`   Menu categories
  `menu_items`        Individual menu items
  `orders`            Customer orders
  `invoices`          Billing documents
  `payments`          Payment transactions
  `inventory_items`   Inventory records
  `employees`         Employee information

The collection list may evolve as additional business requirements are
introduced.

### Document Structure

Tenant-owned documents should contain a tenant identifier.

Example:

``` json
{
  "_id": "menu_001",
  "tenant_id": "tenant_001",
  "restaurant_id": "restaurant_001",
  "branch_id": "branch_001",
  "name": "Chicken Burger",
  "price": 250,
  "currency": "INR",
  "status": "ACTIVE",
  "created_at": "2026-01-01T10:00:00Z",
  "updated_at": "2026-01-01T10:00:00Z"
}
```

### Database Guidelines

-   Use appropriate MongoDB indexes for frequently queried fields.
-   Create compound indexes for common tenant-scoped queries.
-   Store timestamps in UTC.
-   Use consistent document naming conventions.
-   Validate documents before database operations.
-   Apply tenant isolation to all relevant queries.
-   Use transactions when supported and necessary for operations that
    require atomicity.
-   Avoid storing unnecessary duplicated data.

### Example Tenant-Scoped Query

``` python
menu = await db.menu_items.find_one(
    {
        "_id": menu_id,
        "tenant_id": tenant_id
    }
)
```

The `tenant_id` must be derived from the authenticated and authorized
request context, not blindly accepted from the client.

## 13. Development Guidelines

The project follows a modular structure to keep business logic
maintainable and testable.

### Coding Standards

-   Follow Python naming conventions.
-   Use type hints wherever practical.
-   Use Pydantic models for request and response validation.
-   Keep business logic out of API route handlers.
-   Use asynchronous database operations.
-   Handle errors consistently.
-   Avoid unnecessary dependencies between modules.
-   Keep configuration centralized.
-   Write tests for important business logic.

### Module Responsibilities

Each module should own its business logic and data access.

For example, the `orders` module should not directly implement inventory
business rules. When an order affects inventory, the order module should
coordinate with the inventory module through a clearly defined
interface.

This helps reduce coupling and makes future changes easier.

### Dependency Management

Use `uv` to manage dependencies.

Add a production dependency:

``` bash
uv add <package-name>
```

Add a development dependency:

``` bash
uv add --dev <package-name>
```

Remove a dependency:

``` bash
uv remove <package-name>
```

Commit both `pyproject.toml` and `uv.lock` so that the project
dependencies remain reproducible.

### Code Formatting and Linting

Use Ruff for linting and formatting.

``` bash
uv run ruff check .
uv run ruff format .
```

Resolve linting issues before submitting changes.

## 14. Testing

The project uses Pytest for automated testing.

Tests are organized into unit and integration tests.

### Unit Tests

Unit tests validate individual functions and business logic
independently.

Examples include:

-   Tenant validation
-   Membership validation
-   Permission checking
-   Order calculations
-   Billing calculations
-   Inventory quantity calculations

### Integration Tests

Integration tests verify interactions between application components and
external dependencies.

Examples include:

-   MongoDB repository operations
-   API endpoint behavior
-   Authentication and authorization
-   Tenant isolation
-   Order and inventory workflows

### Test Structure

``` text
tests/
├── unit/
│   ├── test_tenants.py
│   ├── test_users.py
│   ├── test_permissions.py
│   └── test_orders.py
└── integration/
    ├── test_tenant_api.py
    ├── test_authentication.py
    ├── test_order_api.py
    └── test_database.py
```

### Running Tests

Run the complete test suite:

``` bash
uv run pytest
```

Run only unit tests:

``` bash
uv run pytest tests/unit
```

Run only integration tests:

``` bash
uv run pytest tests/integration
```

Run tests with coverage:

``` bash
uv run pytest --cov=app --cov-report=term-missing
```

Tests should be added whenever new business functionality or significant
changes are introduced.

## 15. Development Roadmap

The system will be developed incrementally, starting with the
application foundation and progressing toward complete restaurant
operations.

### Phase 1: Core Foundation

-   [ ] Initialize the FastAPI application.
-   [ ] Configure application settings.
-   [ ] Configure asynchronous MongoDB connectivity.
-   [ ] Implement centralized exception handling.
-   [ ] Configure logging.
-   [ ] Set up API versioning.
-   [ ] Configure development and testing environments.

### Phase 2: Authentication and Authorization

-   [ ] Integrate Keycloak.
-   [ ] Implement JWT validation.
-   [ ] Create application user management.
-   [ ] Implement tenant memberships.
-   [ ] Implement role management.
-   [ ] Implement permission management.
-   [ ] Implement scope-based authorization.
-   [ ] Enforce tenant isolation.

### Phase 3: Organization Management

-   [ ] Implement tenant management.
-   [ ] Implement restaurant management.
-   [ ] Implement branch management.
-   [ ] Associate restaurants and branches with tenants.
-   [ ] Implement organization-level access control.

### Phase 4: Restaurant Operations

-   [ ] Implement menu management.
-   [ ] Implement menu categories and items.
-   [ ] Implement order management.
-   [ ] Implement order status workflows.
-   [ ] Implement billing and invoicing.
-   [ ] Implement payment integration.

### Phase 5: Inventory and Employees

-   [ ] Implement inventory management.
-   [ ] Implement stock tracking.
-   [ ] Implement ingredient management.
-   [ ] Implement employee management.
-   [ ] Implement employee role assignments.
-   [ ] Integrate inventory operations with orders.

### Phase 6: Reporting and Deployment

-   [ ] Implement operational reports.
-   [ ] Implement sales reports.
-   [ ] Implement inventory reports.
-   [ ] Add automated tests for critical workflows.
-   [ ] Configure production deployment.
-   [ ] Configure CI/CD.
-   [ ] Set up monitoring and health checks.
-   [ ] Configure production logging and error tracking.

The roadmap is intended to guide development. Individual features may be
reprioritized as requirements evolve.


## License

Copyright © 2026 **Corpxcloud Technologies Private Limited**. All rights reserved.

This software and its source code are the exclusive property of **Corpxcloud Technologies Private Limited**.

### Permitted Use

Individuals may use this software for personal, educational, and non-commercial purposes, subject to the following conditions:

* The software may be downloaded and used for personal learning and experimentation.
* The software may be modified for personal, non-commercial use.
* The software may not be used for commercial purposes without prior written permission from Corpxcloud Technologies Private Limited.
* Any copies or modified versions must retain this copyright notice and license terms.

### Restrictions

Without prior written permission from Corpxcloud Technologies Private Limited, you may not:

* Use this software or any part of it for commercial purposes.
* Sell, sublicense, or distribute this software or modified versions.
* Use this software as part of a commercial product or service.
* Publish or redistribute the source code, in whole or in part.
* Claim ownership of the software or its original source code.

### Ownership

All intellectual property rights, including copyright, trademarks, and other proprietary rights in this software, remain with Corpxcloud Technologies Private Limited.

Permission to use the software does not transfer ownership or grant any rights beyond those explicitly stated in this license.

### Disclaimer

This software is provided "AS IS", without warranties of any kind, express or implied, including but not limited to warranties of merchantability, fitness for a particular purpose, and non-infringement.

Corpxcloud Technologies Private Limited shall not be liable for any damages or claims arising from the use of this software, to the maximum extent permitted by applicable law.

### Commercial Licensing

For commercial licensing, enterprise usage, redistribution permissions, or other licensing inquiries, please contact:

**Corpxcloud Technologies Private Limited**
Website: https://corpxcloud.com

### License Summary

| Use Case                     | Permission                            |
| ---------------------------- | ------------------------------------- |
| Personal use                 | Allowed                               |
| Educational use              | Allowed                               |
| Personal modifications       | Allowed                               |
| Commercial use               | Requires written permission           |
| Commercial redistribution    | Requires written permission           |
| Selling the software         | Prohibited without written permission |
| Publishing modified versions | Prohibited without written permission |
| Claiming ownership           | Prohibited                            |

By using this software, you agree to the terms and conditions of this license.
