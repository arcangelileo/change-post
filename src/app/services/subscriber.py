import re
import uuid

from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.subscriber import Subscriber


def is_valid_email(email: str) -> bool:
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


async def get_subscribers_for_project(
    db: AsyncSession, project_id: str
) -> list[Subscriber]:
    result = await db.execute(
        select(Subscriber)
        .where(Subscriber.project_id == project_id)
        .order_by(Subscriber.created_at.desc())
    )
    return list(result.scalars().all())


async def get_subscriber_count_for_project(
    db: AsyncSession, project_id: str
) -> int:
    result = await db.execute(
        select(func.count(Subscriber.id))
        .where(Subscriber.project_id == project_id)
    )
    return result.scalar_one()


async def get_subscriber_by_email_and_project(
    db: AsyncSession, email: str, project_id: str
) -> Subscriber | None:
    result = await db.execute(
        select(Subscriber)
        .where(Subscriber.email == email)
        .where(Subscriber.project_id == project_id)
    )
    return result.scalar_one_or_none()


async def get_subscriber_by_token(
    db: AsyncSession, token: str
) -> Subscriber | None:
    result = await db.execute(
        select(Subscriber)
        .where(Subscriber.unsubscribe_token == token)
    )
    return result.scalar_one_or_none()


async def subscribe(
    db: AsyncSession, email: str, project_id: str
) -> Subscriber | None:
    """Subscribe an email to a project. Returns None if already subscribed."""
    existing = await get_subscriber_by_email_and_project(db, email, project_id)
    if existing:
        return None

    subscriber = Subscriber(
        email=email,
        project_id=project_id,
        unsubscribe_token=uuid.uuid4().hex,
    )
    db.add(subscriber)
    await db.flush()
    return subscriber


async def unsubscribe_by_token(db: AsyncSession, token: str) -> bool:
    """Unsubscribe using the unique token. Returns True if found and removed."""
    subscriber = await get_subscriber_by_token(db, token)
    if not subscriber:
        return False
    await db.delete(subscriber)
    await db.flush()
    return True


async def delete_subscriber(db: AsyncSession, subscriber_id: str, project_id: str) -> bool:
    """Delete a subscriber by ID (for dashboard management)."""
    result = await db.execute(
        select(Subscriber)
        .where(Subscriber.id == subscriber_id)
        .where(Subscriber.project_id == project_id)
    )
    subscriber = result.scalar_one_or_none()
    if not subscriber:
        return False
    await db.delete(subscriber)
    await db.flush()
    return True


async def get_total_subscribers_for_user(
    db: AsyncSession, project_ids: list[str]
) -> int:
    """Get total subscriber count across multiple projects."""
    if not project_ids:
        return 0
    result = await db.execute(
        select(func.count(Subscriber.id))
        .where(Subscriber.project_id.in_(project_ids))
    )
    return result.scalar_one()
