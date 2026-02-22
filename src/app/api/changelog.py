from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.post import (
    CATEGORIES,
    get_published_posts_for_project,
    get_post_by_slug,
    increment_view_count,
)
from app.services.project import get_project_by_slug

router = APIRouter(prefix="/changelog", tags=["changelog"])
templates = Jinja2Templates(directory="src/app/templates")


@router.get("/{project_slug}", response_class=HTMLResponse)
async def public_changelog(
    project_slug: str,
    request: Request,
    category: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    project = await get_project_by_slug(db, project_slug)
    if not project:
        raise HTTPException(status_code=404, detail="Changelog not found")

    posts = await get_published_posts_for_project(db, project.id, category=category)

    return templates.TemplateResponse(
        request, "pages/changelog/public.html",
        {
            "project": project,
            "posts": posts,
            "categories": CATEGORIES,
            "active_category": category,
        },
    )


@router.get("/{project_slug}/{post_slug}", response_class=HTMLResponse)
async def public_post_detail(
    project_slug: str,
    post_slug: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    project = await get_project_by_slug(db, project_slug)
    if not project:
        raise HTTPException(status_code=404, detail="Changelog not found")

    post = await get_post_by_slug(db, project.id, post_slug)
    if not post or not post.is_published:
        raise HTTPException(status_code=404, detail="Post not found")

    await increment_view_count(db, post)

    return templates.TemplateResponse(
        request, "pages/changelog/post.html",
        {
            "project": project,
            "post": post,
            "categories": CATEGORIES,
        },
    )
