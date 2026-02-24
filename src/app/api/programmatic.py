from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Header, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.api_key import verify_api_key
from app.services.email import send_post_notification
from app.services.post import (
    CATEGORIES,
    create_post,
    get_posts_for_project,
    get_post_by_id,
)
from app.services.project import get_project_by_id
from app.services.subscriber import get_subscribers_for_project

router = APIRouter(prefix="/api/v1", tags=["programmatic_api"])


async def get_api_key_project(
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """Dependency to validate API key and return the associated project."""
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Missing Authorization header. Use: Authorization: Bearer <api_key>",
        )

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Invalid Authorization format. Use: Authorization: Bearer <api_key>",
        )

    raw_key = authorization[7:].strip()
    if not raw_key:
        raise HTTPException(status_code=401, detail="API key is empty")

    api_key = await verify_api_key(db, raw_key)
    if not api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")

    return api_key


@router.get("/posts")
async def api_list_posts(
    api_key=Depends(get_api_key_project),
    published: bool | None = None,
    db: AsyncSession = Depends(get_db),
):
    """List posts for the project associated with the API key."""
    published_only = published if published is not None else False
    posts = await get_posts_for_project(db, api_key.project_id, published_only=published_only)

    return JSONResponse(content={
        "posts": [
            {
                "id": post.id,
                "title": post.title,
                "slug": post.slug,
                "body_markdown": post.body_markdown,
                "category": post.category,
                "category_label": CATEGORIES.get(post.category, {}).get("label", post.category),
                "is_published": post.is_published,
                "published_at": post.published_at.isoformat() if post.published_at else None,
                "view_count": post.view_count,
                "created_at": post.created_at.isoformat(),
            }
            for post in posts
        ],
        "total": len(posts),
    })


@router.post("/posts")
async def api_create_post(
    request: Request,
    background_tasks: BackgroundTasks,
    api_key=Depends(get_api_key_project),
    db: AsyncSession = Depends(get_db),
):
    """Create a new changelog post via API."""
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="Request body must be a JSON object")

    title = str(body.get("title", "")).strip()
    body_markdown = str(body.get("body_markdown", "")).strip()
    category = str(body.get("category", "improvement")).strip()
    is_published = bool(body.get("is_published", False))

    errors = []
    if not title:
        errors.append("title is required")
    elif len(title) > 300:
        errors.append("title must be at most 300 characters")
    if not body_markdown:
        errors.append("body_markdown is required")
    if category not in CATEGORIES:
        errors.append(f"category must be one of: {', '.join(CATEGORIES.keys())}")

    if errors:
        raise HTTPException(status_code=422, detail={"errors": errors})

    post = await create_post(
        db,
        project_id=api_key.project_id,
        title=title,
        body_markdown=body_markdown,
        category=category,
        is_published=is_published,
    )

    # Send email notifications if published
    if is_published:
        subscribers = await get_subscribers_for_project(db, api_key.project_id)
        if subscribers:
            project = await get_project_by_id(db, api_key.project_id)
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

    return JSONResponse(
        status_code=201,
        content={
            "post": {
                "id": post.id,
                "title": post.title,
                "slug": post.slug,
                "body_markdown": post.body_markdown,
                "category": post.category,
                "is_published": post.is_published,
                "published_at": post.published_at.isoformat() if post.published_at else None,
                "created_at": post.created_at.isoformat(),
            }
        },
    )


@router.get("/posts/{post_id}")
async def api_get_post(
    post_id: str,
    api_key=Depends(get_api_key_project),
    db: AsyncSession = Depends(get_db),
):
    """Get a single post by ID."""
    post = await get_post_by_id(db, post_id)
    if not post or post.project_id != api_key.project_id:
        raise HTTPException(status_code=404, detail="Post not found")

    return JSONResponse(content={
        "post": {
            "id": post.id,
            "title": post.title,
            "slug": post.slug,
            "body_markdown": post.body_markdown,
            "body_html": post.body_html,
            "category": post.category,
            "category_label": CATEGORIES.get(post.category, {}).get("label", post.category),
            "is_published": post.is_published,
            "published_at": post.published_at.isoformat() if post.published_at else None,
            "view_count": post.view_count,
            "created_at": post.created_at.isoformat(),
        }
    })
