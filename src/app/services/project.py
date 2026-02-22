import re
import uuid

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")


async def get_projects_for_user(db: AsyncSession, user_id: str) -> list[Project]:
    result = await db.execute(
        select(Project).where(Project.owner_id == user_id).order_by(Project.created_at.desc())
    )
    return list(result.scalars().all())


async def get_project_by_id(db: AsyncSession, project_id: str) -> Project | None:
    result = await db.execute(select(Project).where(Project.id == project_id))
    return result.scalar_one_or_none()


async def get_project_by_slug(db: AsyncSession, slug: str) -> Project | None:
    result = await db.execute(select(Project).where(Project.slug == slug))
    return result.scalar_one_or_none()


async def get_project_count_for_user(db: AsyncSession, user_id: str) -> int:
    result = await db.execute(
        select(func.count(Project.id)).where(Project.owner_id == user_id)
    )
    return result.scalar_one()


async def create_project(
    db: AsyncSession,
    name: str,
    owner_id: str,
    description: str | None = None,
    website_url: str | None = None,
    accent_color: str = "#6366f1",
) -> Project:
    slug = slugify(name)
    # Ensure slug uniqueness
    existing = await get_project_by_slug(db, slug)
    if existing:
        slug = f"{slug}-{uuid.uuid4().hex[:6]}"

    project = Project(
        name=name,
        slug=slug,
        description=description,
        website_url=website_url,
        accent_color=accent_color,
        owner_id=owner_id,
    )
    db.add(project)
    await db.flush()
    return project


async def update_project(
    db: AsyncSession,
    project: Project,
    name: str | None = None,
    description: str | None = None,
    website_url: str | None = None,
    accent_color: str | None = None,
) -> Project:
    if name is not None:
        project.name = name
    if description is not None:
        project.description = description
    if website_url is not None:
        project.website_url = website_url
    if accent_color is not None:
        project.accent_color = accent_color
    await db.flush()
    return project


async def delete_project(db: AsyncSession, project: Project) -> None:
    await db.delete(project)
    await db.flush()
