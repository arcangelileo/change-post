import hashlib
import secrets
import uuid
from datetime import datetime, timezone

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.api_key import APIKey


def generate_api_key() -> tuple[str, str, str]:
    """Generate an API key. Returns (raw_key, key_hash, key_prefix)."""
    raw_key = f"cpk_{secrets.token_urlsafe(32)}"
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    key_prefix = raw_key[:12]
    return raw_key, key_hash, key_prefix


def hash_api_key(raw_key: str) -> str:
    """Hash an API key for storage."""
    return hashlib.sha256(raw_key.encode()).hexdigest()


async def create_api_key(
    db: AsyncSession, project_id: str, name: str
) -> tuple[APIKey, str]:
    """Create a new API key. Returns (api_key_obj, raw_key).
    The raw key is only available at creation time."""
    raw_key, key_hash, key_prefix = generate_api_key()
    api_key = APIKey(
        name=name,
        key_hash=key_hash,
        key_prefix=key_prefix,
        project_id=project_id,
    )
    db.add(api_key)
    await db.flush()
    return api_key, raw_key


async def get_api_keys_for_project(
    db: AsyncSession, project_id: str
) -> list[APIKey]:
    result = await db.execute(
        select(APIKey)
        .where(APIKey.project_id == project_id)
        .order_by(APIKey.created_at.desc())
    )
    return list(result.scalars().all())


async def get_api_key_by_id(
    db: AsyncSession, key_id: str
) -> APIKey | None:
    result = await db.execute(select(APIKey).where(APIKey.id == key_id))
    return result.scalar_one_or_none()


async def verify_api_key(
    db: AsyncSession, raw_key: str
) -> APIKey | None:
    """Verify an API key and return the APIKey object if valid."""
    key_hash = hash_api_key(raw_key)
    result = await db.execute(
        select(APIKey).where(APIKey.key_hash == key_hash)
    )
    api_key = result.scalar_one_or_none()
    if api_key:
        api_key.last_used_at = datetime.now(timezone.utc)
        await db.flush()
    return api_key


async def delete_api_key(
    db: AsyncSession, key_id: str, project_id: str
) -> bool:
    """Delete an API key by ID."""
    result = await db.execute(
        select(APIKey)
        .where(APIKey.id == key_id)
        .where(APIKey.project_id == project_id)
    )
    api_key = result.scalar_one_or_none()
    if not api_key:
        return False
    await db.delete(api_key)
    await db.flush()
    return True
