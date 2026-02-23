from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.models.post import Post
from app.models.subscriber import Subscriber
from app.models.user import User
from app.services.post import CATEGORIES, get_posts_for_project
from app.services.project import get_project_by_id
from app.services.subscriber import get_subscriber_count_for_project

router = APIRouter(tags=["analytics"])
templates = Jinja2Templates(directory="src/app/templates")


@router.get("/projects/{project_id}/analytics", response_class=HTMLResponse)
async def project_analytics(
    project_id: str,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    project = await get_project_by_id(db, project_id)
    if not project or project.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get all posts with view counts
    posts = await get_posts_for_project(db, project_id)
    published_posts = [p for p in posts if p.is_published]

    # Overall stats
    total_views = sum(p.view_count for p in posts)
    total_posts = len(posts)
    published_count = len(published_posts)
    subscriber_count = await get_subscriber_count_for_project(db, project_id)

    # Top posts by views
    top_posts = sorted(published_posts, key=lambda p: p.view_count, reverse=True)[:10]

    # Category breakdown
    category_stats = {}
    for cat_key, cat_info in CATEGORIES.items():
        cat_posts = [p for p in published_posts if p.category == cat_key]
        category_stats[cat_key] = {
            "label": cat_info["label"],
            "color": cat_info["color"],
            "count": len(cat_posts),
            "views": sum(p.view_count for p in cat_posts),
        }

    # Recent posts with view data (for chart)
    chart_posts = sorted(published_posts, key=lambda p: p.published_at or p.created_at)[-12:]

    return templates.TemplateResponse(
        request,
        "pages/analytics/dashboard.html",
        {
            "user": user,
            "project": project,
            "total_views": total_views,
            "total_posts": total_posts,
            "published_count": published_count,
            "subscriber_count": subscriber_count,
            "top_posts": top_posts,
            "category_stats": category_stats,
            "chart_posts": chart_posts,
            "categories": CATEGORIES,
        },
    )
