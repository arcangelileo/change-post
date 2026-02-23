import asyncio
import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.models.user import User
from app.services.email import send_post_notification
from app.services.post import (
    CATEGORIES,
    create_post,
    delete_post,
    get_post_by_id,
    get_posts_for_project,
    get_post_counts_for_project,
    toggle_publish,
    update_post,
)
from app.services.project import get_project_by_id
from app.services.subscriber import get_subscribers_for_project

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projects/{project_id}/posts", tags=["posts"])
templates = Jinja2Templates(directory="src/app/templates")


async def _get_user_project(project_id: str, user: User, db: AsyncSession):
    project = await get_project_by_id(db, project_id)
    if not project or project.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.get("", response_class=HTMLResponse)
async def list_posts(
    project_id: str,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    project = await _get_user_project(project_id, user, db)
    posts = await get_posts_for_project(db, project_id)
    counts = await get_post_counts_for_project(db, project_id)
    return templates.TemplateResponse(
        request, "pages/posts/list.html",
        {
            "user": user,
            "project": project,
            "posts": posts,
            "counts": counts,
            "categories": CATEGORIES,
        },
    )


@router.get("/new", response_class=HTMLResponse)
async def create_post_page(
    project_id: str,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    project = await _get_user_project(project_id, user, db)
    return templates.TemplateResponse(
        request, "pages/posts/create.html",
        {
            "user": user,
            "project": project,
            "categories": CATEGORIES,
        },
    )


@router.post("/new")
async def create_post_handler(
    project_id: str,
    request: Request,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    project = await _get_user_project(project_id, user, db)
    form = await request.form()
    title = form.get("title", "").strip()
    body_markdown = form.get("body_markdown", "").strip()
    category = form.get("category", "improvement").strip()
    action = form.get("action", "draft")

    errors = []
    if not title:
        errors.append("Title is required")
    if len(title) > 300:
        errors.append("Title must be at most 300 characters")
    if not body_markdown:
        errors.append("Post body is required")

    if errors:
        return templates.TemplateResponse(
            request, "pages/posts/create.html",
            {
                "user": user,
                "project": project,
                "categories": CATEGORIES,
                "errors": errors,
                "title": title,
                "body_markdown": body_markdown,
                "category": category,
            },
            status_code=422,
        )

    is_published = action == "publish"
    post = await create_post(
        db, project_id=project_id, title=title,
        body_markdown=body_markdown, category=category,
        is_published=is_published,
    )

    # Send email notifications if published
    if is_published:
        subscribers = await get_subscribers_for_project(db, project_id)
        if subscribers:
            cat_label = CATEGORIES.get(category, {}).get("label", category)
            background_tasks.add_task(
                send_post_notification,
                subscribers=subscribers,
                project_name=project.name,
                project_slug=project.slug,
                post_title=post.title,
                post_slug=post.slug,
                post_body_html=post.body_html,
                post_category_label=cat_label,
                accent_color=project.accent_color,
            )

    return RedirectResponse(
        url=f"/projects/{project_id}/posts/{post.id}",
        status_code=302,
    )


@router.get("/{post_id}", response_class=HTMLResponse)
async def post_detail(
    project_id: str,
    post_id: str,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    project = await _get_user_project(project_id, user, db)
    post = await get_post_by_id(db, post_id)
    if not post or post.project_id != project_id:
        raise HTTPException(status_code=404, detail="Post not found")
    return templates.TemplateResponse(
        request, "pages/posts/detail.html",
        {
            "user": user,
            "project": project,
            "post": post,
            "categories": CATEGORIES,
        },
    )


@router.get("/{post_id}/edit", response_class=HTMLResponse)
async def edit_post_page(
    project_id: str,
    post_id: str,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    project = await _get_user_project(project_id, user, db)
    post = await get_post_by_id(db, post_id)
    if not post or post.project_id != project_id:
        raise HTTPException(status_code=404, detail="Post not found")
    return templates.TemplateResponse(
        request, "pages/posts/edit.html",
        {
            "user": user,
            "project": project,
            "post": post,
            "categories": CATEGORIES,
        },
    )


@router.post("/{post_id}/edit")
async def update_post_handler(
    project_id: str,
    post_id: str,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    project = await _get_user_project(project_id, user, db)
    post = await get_post_by_id(db, post_id)
    if not post or post.project_id != project_id:
        raise HTTPException(status_code=404, detail="Post not found")

    form = await request.form()
    title = form.get("title", "").strip()
    body_markdown = form.get("body_markdown", "").strip()
    category = form.get("category", post.category).strip()

    errors = []
    if not title:
        errors.append("Title is required")
    if not body_markdown:
        errors.append("Post body is required")

    if errors:
        return templates.TemplateResponse(
            request, "pages/posts/edit.html",
            {
                "user": user,
                "project": project,
                "post": post,
                "categories": CATEGORIES,
                "errors": errors,
            },
            status_code=422,
        )

    await update_post(db, post, title=title, body_markdown=body_markdown, category=category)
    return RedirectResponse(
        url=f"/projects/{project_id}/posts/{post.id}",
        status_code=302,
    )


@router.post("/{post_id}/toggle-publish")
async def toggle_publish_handler(
    project_id: str,
    post_id: str,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    project = await _get_user_project(project_id, user, db)
    post = await get_post_by_id(db, post_id)
    if not post or post.project_id != project_id:
        raise HTTPException(status_code=404, detail="Post not found")

    was_published = post.is_published
    await toggle_publish(db, post)

    # Send notifications only when going from draft -> published
    if not was_published and post.is_published:
        subscribers = await get_subscribers_for_project(db, project_id)
        if subscribers:
            cat_label = CATEGORIES.get(post.category, {}).get("label", post.category)
            background_tasks.add_task(
                send_post_notification,
                subscribers=subscribers,
                project_name=project.name,
                project_slug=project.slug,
                post_title=post.title,
                post_slug=post.slug,
                post_body_html=post.body_html,
                post_category_label=cat_label,
                accent_color=project.accent_color,
            )

    return RedirectResponse(
        url=f"/projects/{project_id}/posts/{post.id}",
        status_code=302,
    )


@router.post("/{post_id}/delete")
async def delete_post_handler(
    project_id: str,
    post_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_user_project(project_id, user, db)
    post = await get_post_by_id(db, post_id)
    if not post or post.project_id != project_id:
        raise HTTPException(status_code=404, detail="Post not found")
    await delete_post(db, post)
    return RedirectResponse(
        url=f"/projects/{project_id}/posts",
        status_code=302,
    )
