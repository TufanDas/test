from fastapi import Header


async def get_tenant_header(
    x_tenant_id: str | None = Header(None, alias="X-Tenant-ID"),
) -> str | None:
    """Optional tenant context extracted from request header for authenticated tenant-scoped endpoints."""
    return x_tenant_id
