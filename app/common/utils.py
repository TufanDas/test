import uuid
from datetime import UTC, datetime


def utc_now() -> datetime:
    return datetime.now(UTC)


def generate_prefixed_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"
