from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.models.user import User
from app.services.api_key import (
    create_api_key,
    delete_api_key,
    get_api_keys_for_project,
)
from app.services.project import get_project_by_id

router = APIRouter(tags=["api_keys"])
templates = Jinja2Templates(directory="src/app/templates")


@router.get("/projects/{project_id}/api-keys", response_class=HTMLResponse)
async def list_api_keys(
    project_id: str,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    project = await get_project_by_id(db, project_id)
    if not project or project.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Project not found")

    api_keys = await get_api_keys_for_project(db, project_id)

    return templates.TemplateResponse(
        request,
        "pages/api_keys/list.html",
        {
            "user": user,
            "project": project,
            "api_keys": api_keys,
            "new_key": None,
        },
    )


@router.post("/projects/{project_id}/api-keys")
async def create_api_key_handler(
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

    if not name:
        api_keys = await get_api_keys_for_project(db, project_id)
        return templates.TemplateResponse(
            request,
            "pages/api_keys/list.html",
            {
                "user": user,
                "project": project,
                "api_keys": api_keys,
                "new_key": None,
                "errors": ["API key name is required"],
            },
            status_code=422,
        )

    if len(name) > 200:
        api_keys = await get_api_keys_for_project(db, project_id)
        return templates.TemplateResponse(
            request,
            "pages/api_keys/list.html",
            {
                "user": user,
                "project": project,
                "api_keys": api_keys,
                "new_key": None,
                "errors": ["Name must be at most 200 characters"],
            },
            status_code=422,
        )

    api_key, raw_key = await create_api_key(db, project_id, name)
    api_keys = await get_api_keys_for_project(db, project_id)

    return templates.TemplateResponse(
        request,
        "pages/api_keys/list.html",
        {
            "user": user,
            "project": project,
            "api_keys": api_keys,
            "new_key": raw_key,
        },
    )


@router.post("/projects/{project_id}/api-keys/{key_id}/delete")
async def delete_api_key_handler(
    project_id: str,
    key_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    project = await get_project_by_id(db, project_id)
    if not project or project.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Project not found")

    deleted = await delete_api_key(db, key_id, project_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="API key not found")

    return RedirectResponse(
        url=f"/projects/{project_id}/api-keys", status_code=302
    )
