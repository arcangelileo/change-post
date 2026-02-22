from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.models.post import Post
from app.models.user import User
from app.services.project import get_projects_for_user

router = APIRouter(tags=["dashboard"])
templates = Jinja2Templates(directory="src/app/templates")


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    projects = await get_projects_for_user(db, user.id)
    project_ids = [p.id for p in projects]
    total_posts = 0
    if project_ids:
        result = await db.execute(
            select(func.count(Post.id)).where(Post.project_id.in_(project_ids))
        )
        total_posts = result.scalar_one()

    return templates.TemplateResponse(
        request,
        "pages/dashboard.html",
        {
            "user": user,
            "projects": projects,
            "total_posts": total_posts,
        },
    )
