from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.models.user import User
from app.services.post import get_posts_for_project, get_post_counts_for_project, CATEGORIES
from app.services.project import (
    create_project,
    delete_project,
    get_project_by_id,
    get_projects_for_user,
    update_project,
)

router = APIRouter(prefix="/projects", tags=["projects"])
templates = Jinja2Templates(directory="src/app/templates")


@router.get("", response_class=HTMLResponse)
async def list_projects(
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    projects = await get_projects_for_user(db, user.id)
    return templates.TemplateResponse(
        request, "pages/projects/list.html",
        {"user": user, "projects": projects},
    )


@router.get("/new", response_class=HTMLResponse)
async def create_project_page(
    request: Request,
    user: User = Depends(get_current_user),
):
    return templates.TemplateResponse(
        request, "pages/projects/create.html",
        {"user": user},
    )


@router.post("/new")
async def create_project_handler(
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    form = await request.form()
    name = form.get("name", "").strip()
    description = form.get("description", "").strip() or None
    website_url = form.get("website_url", "").strip() or None
    accent_color = form.get("accent_color", "#6366f1").strip()

    errors = []
    if not name:
        errors.append("Project name is required")
    if len(name) > 200:
        errors.append("Project name must be at most 200 characters")

    if errors:
        return templates.TemplateResponse(
            request, "pages/projects/create.html",
            {
                "user": user,
                "errors": errors,
                "name": name,
                "description": description or "",
                "website_url": website_url or "",
                "accent_color": accent_color,
            },
            status_code=422,
        )

    project = await create_project(
        db, name=name, owner_id=user.id,
        description=description, website_url=website_url,
        accent_color=accent_color,
    )
    return RedirectResponse(url=f"/projects/{project.id}", status_code=302)


@router.get("/{project_id}", response_class=HTMLResponse)
async def project_detail(
    project_id: str,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    project = await get_project_by_id(db, project_id)
    if not project or project.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Project not found")
    posts = await get_posts_for_project(db, project_id)
    counts = await get_post_counts_for_project(db, project_id)
    return templates.TemplateResponse(
        request, "pages/projects/detail.html",
        {
            "user": user,
            "project": project,
            "posts": posts,
            "counts": counts,
            "categories": CATEGORIES,
        },
    )


@router.get("/{project_id}/edit", response_class=HTMLResponse)
async def edit_project_page(
    project_id: str,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    project = await get_project_by_id(db, project_id)
    if not project or project.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Project not found")
    return templates.TemplateResponse(
        request, "pages/projects/edit.html",
        {"user": user, "project": project},
    )


@router.post("/{project_id}/edit")
async def update_project_handler(
    project_id: str,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    project = await get_project_by_id(db, project_id)
    if not project or project.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Project not found")

    form = await request.form()
    name = form.get("name", "").strip()
    description = form.get("description", "").strip() or None
    website_url = form.get("website_url", "").strip() or None
    accent_color = form.get("accent_color", project.accent_color).strip()

    errors = []
    if not name:
        errors.append("Project name is required")

    if errors:
        return templates.TemplateResponse(
            request, "pages/projects/edit.html",
            {
                "user": user,
                "project": project,
                "errors": errors,
            },
            status_code=422,
        )

    await update_project(
        db, project,
        name=name, description=description,
        website_url=website_url, accent_color=accent_color,
    )
    return RedirectResponse(url=f"/projects/{project.id}", status_code=302)


@router.post("/{project_id}/delete")
async def delete_project_handler(
    project_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    project = await get_project_by_id(db, project_id)
    if not project or project.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Project not found")
    await delete_project(db, project)
    return RedirectResponse(url="/projects", status_code=302)
