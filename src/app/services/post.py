import re
import uuid
from datetime import datetime, timezone

import markdown
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.post import Post

CATEGORIES = {
    "new_feature": {"label": "New Feature", "color": "emerald"},
    "improvement": {"label": "Improvement", "color": "blue"},
    "bugfix": {"label": "Bug Fix", "color": "red"},
    "announcement": {"label": "Announcement", "color": "purple"},
}


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")


def render_markdown(text: str) -> str:
    return markdown.markdown(
        text,
        extensions=["fenced_code", "tables", "nl2br", "sane_lists"],
    )


async def get_posts_for_project(
    db: AsyncSession,
    project_id: str,
    published_only: bool = False,
) -> list[Post]:
    query = select(Post).where(Post.project_id == project_id)
    if published_only:
        query = query.where(Post.is_published == True)  # noqa: E712
        query = query.order_by(Post.published_at.desc())
    else:
        query = query.order_by(Post.created_at.desc())
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_published_posts_for_project(
    db: AsyncSession,
    project_id: str,
    category: str | None = None,
) -> list[Post]:
    query = (
        select(Post)
        .where(Post.project_id == project_id)
        .where(Post.is_published == True)  # noqa: E712
    )
    if category and category in CATEGORIES:
        query = query.where(Post.category == category)
    query = query.order_by(Post.published_at.desc())
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_post_by_id(db: AsyncSession, post_id: str) -> Post | None:
    result = await db.execute(select(Post).where(Post.id == post_id))
    return result.scalar_one_or_none()


async def get_post_by_slug(
    db: AsyncSession, project_id: str, slug: str
) -> Post | None:
    result = await db.execute(
        select(Post)
        .where(Post.project_id == project_id)
        .where(Post.slug == slug)
    )
    return result.scalar_one_or_none()


async def get_post_counts_for_project(db: AsyncSession, project_id: str) -> dict:
    total_result = await db.execute(
        select(func.count(Post.id)).where(Post.project_id == project_id)
    )
    published_result = await db.execute(
        select(func.count(Post.id))
        .where(Post.project_id == project_id)
        .where(Post.is_published == True)  # noqa: E712
    )
    views_result = await db.execute(
        select(func.coalesce(func.sum(Post.view_count), 0))
        .where(Post.project_id == project_id)
    )
    return {
        "total": total_result.scalar_one(),
        "published": published_result.scalar_one(),
        "total_views": views_result.scalar_one(),
    }


async def create_post(
    db: AsyncSession,
    project_id: str,
    title: str,
    body_markdown: str,
    category: str = "improvement",
    is_published: bool = False,
) -> Post:
    slug = slugify(title)
    existing = await get_post_by_slug(db, project_id, slug)
    if existing:
        slug = f"{slug}-{uuid.uuid4().hex[:6]}"

    body_html = render_markdown(body_markdown)

    post = Post(
        title=title,
        slug=slug,
        body_markdown=body_markdown,
        body_html=body_html,
        category=category if category in CATEGORIES else "improvement",
        is_published=is_published,
        published_at=datetime.now(timezone.utc) if is_published else None,
        project_id=project_id,
    )
    db.add(post)
    await db.flush()
    return post


async def update_post(
    db: AsyncSession,
    post: Post,
    title: str | None = None,
    body_markdown: str | None = None,
    category: str | None = None,
) -> Post:
    if title is not None:
        post.title = title
    if body_markdown is not None:
        post.body_markdown = body_markdown
        post.body_html = render_markdown(body_markdown)
    if category is not None and category in CATEGORIES:
        post.category = category
    await db.flush()
    return post


async def toggle_publish(db: AsyncSession, post: Post) -> Post:
    if post.is_published:
        post.is_published = False
        post.published_at = None
    else:
        post.is_published = True
        post.published_at = datetime.now(timezone.utc)
    await db.flush()
    return post


async def delete_post(db: AsyncSession, post: Post) -> None:
    await db.delete(post)
    await db.flush()


async def increment_view_count(db: AsyncSession, post: Post) -> None:
    post.view_count = post.view_count + 1
    await db.flush()
