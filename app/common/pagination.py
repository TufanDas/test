from pydantic import BaseModel, Field


class PaginationParams(BaseModel):
    page: int = Field(1, ge=1, description="Page number")
    limit: int = Field(20, ge=1, le=100, description="Items per page")

    @property
    def skip(self) -> int:
        return (self.page - 1) * self.limit


class PaginatedResponse[T](BaseModel):
    items: list[T]
    total: int
    page: int
    limit: int
    total_pages: int
