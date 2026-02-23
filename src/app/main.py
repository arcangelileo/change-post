from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import settings
from app.database import init_db

# Import models so they register with Base.metadata
import app.models  # noqa: F401
from app.api.health import router as health_router
from app.api.auth import router as auth_router
from app.api.dashboard import router as dashboard_router
from app.api.projects import router as projects_router
from app.api.posts import router as posts_router
from app.api.changelog import router as changelog_router
from app.api.subscribers import router as subscribers_router
from app.api.widget import router as widget_router
from app.api.analytics import router as analytics_router
from app.api.api_keys import router as api_keys_router
from app.api.widget_page import router as widget_page_router
from app.api.programmatic import router as programmatic_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    yield
    # Shutdown


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

# Static files
app.mount("/static", StaticFiles(directory="src/app/static"), name="static")

# Templates
templates = Jinja2Templates(directory="src/app/templates")

# Routers
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(dashboard_router)
app.include_router(projects_router)
app.include_router(posts_router)
app.include_router(changelog_router)
app.include_router(subscribers_router)
app.include_router(widget_router)
app.include_router(analytics_router)
app.include_router(api_keys_router)
app.include_router(widget_page_router)
app.include_router(programmatic_router)


@app.get("/")
async def root(request: Request):
    return RedirectResponse(url="/login", status_code=302)
