from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.models.user import User
from app.services.project import get_project_by_id, get_project_by_slug
from app.services.subscriber import (
    delete_subscriber,
    get_subscriber_count_for_project,
    get_subscribers_for_project,
    is_valid_email,
    subscribe,
    unsubscribe_by_token,
)

router = APIRouter(tags=["subscribers"])
templates = Jinja2Templates(directory="src/app/templates")


# --- Dashboard subscriber management ---


@router.get("/projects/{project_id}/subscribers", response_class=HTMLResponse)
async def list_subscribers(
    project_id: str,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    project = await get_project_by_id(db, project_id)
    if not project or project.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Project not found")

    subscribers = await get_subscribers_for_project(db, project_id)
    count = len(subscribers)

    return templates.TemplateResponse(
        request,
        "pages/subscribers/list.html",
        {
            "user": user,
            "project": project,
            "subscribers": subscribers,
            "count": count,
        },
    )


@router.post("/projects/{project_id}/subscribers/{subscriber_id}/delete")
async def delete_subscriber_handler(
    project_id: str,
    subscriber_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    project = await get_project_by_id(db, project_id)
    if not project or project.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Project not found")

    deleted = await delete_subscriber(db, subscriber_id, project_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Subscriber not found")

    return RedirectResponse(
        url=f"/projects/{project_id}/subscribers", status_code=302
    )


# --- Public subscribe/unsubscribe ---


@router.post("/changelog/{project_slug}/subscribe")
async def subscribe_handler(
    project_slug: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    project = await get_project_by_slug(db, project_slug)
    if not project:
        raise HTTPException(status_code=404, detail="Changelog not found")

    form = await request.form()
    email = form.get("email", "").strip().lower()

    if not email or not is_valid_email(email):
        return templates.TemplateResponse(
            request,
            "pages/changelog/subscribe_result.html",
            {
                "project": project,
                "success": False,
                "message": "Please enter a valid email address.",
            },
            status_code=422,
        )

    subscriber = await subscribe(db, email, project.id)

    if subscriber is None:
        # Already subscribed — still show success to prevent email enumeration
        return templates.TemplateResponse(
            request,
            "pages/changelog/subscribe_result.html",
            {
                "project": project,
                "success": True,
                "message": "You're subscribed! You'll receive notifications for new updates.",
            },
        )

    return templates.TemplateResponse(
        request,
        "pages/changelog/subscribe_result.html",
        {
            "project": project,
            "success": True,
            "message": "You're subscribed! You'll receive notifications for new updates.",
        },
    )


@router.get("/unsubscribe/{token}", response_class=HTMLResponse)
async def unsubscribe_page(
    token: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    removed = await unsubscribe_by_token(db, token)
    return templates.TemplateResponse(
        request,
        "pages/changelog/unsubscribe.html",
        {
            "success": removed,
        },
    )
