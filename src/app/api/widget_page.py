from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.config import settings
from app.database import get_db
from app.models.user import User
from app.services.project import get_project_by_id

router = APIRouter(tags=["widget_page"])
templates = Jinja2Templates(directory="src/app/templates")


@router.get("/projects/{project_id}/widget", response_class=HTMLResponse)
async def widget_embed_page(
    project_id: str,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    project = await get_project_by_id(db, project_id)
    if not project or project.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Project not found")

    return templates.TemplateResponse(
        request,
        "pages/widget/embed.html",
        {
            "user": user,
            "project": project,
            "base_url": settings.base_url.rstrip("/"),
        },
    )
