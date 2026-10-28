from fastapi import APIRouter

from app.modules.authentication.router import router as auth_router
from app.modules.tenants.router import router as tenants_router

api_router = APIRouter()

# Register module routers
api_router.include_router(auth_router)
api_router.include_router(tenants_router)
