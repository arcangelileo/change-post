from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import settings
from app.database import init_db

# Import models so they register with Base.metadata
import app.models  # noqa: F401
from app.api.health import router as health_router


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
