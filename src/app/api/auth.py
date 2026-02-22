from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_optional_user
from app.database import get_db
from app.models.user import User
from app.services.auth import (
    authenticate_user,
    create_access_token,
    create_user,
    get_user_by_email,
    get_user_by_username,
)

router = APIRouter(tags=["auth"])
templates = Jinja2Templates(directory="src/app/templates")


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request, user: User | None = Depends(get_optional_user)):
    if user:
        return RedirectResponse(url="/dashboard", status_code=302)
    return templates.TemplateResponse(request, "pages/register.html")


@router.post("/register")
async def register(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    form = await request.form()
    email = form.get("email", "").strip().lower()
    username = form.get("username", "").strip().lower()
    password = form.get("password", "")
    display_name = form.get("display_name", "").strip() or None

    errors = []
    if not email or "@" not in email:
        errors.append("Valid email is required")
    if not username or len(username) < 3:
        errors.append("Username must be at least 3 characters")
    if not password or len(password) < 8:
        errors.append("Password must be at least 8 characters")

    if not errors:
        existing_email = await get_user_by_email(db, email)
        if existing_email:
            errors.append("An account with this email already exists")
        existing_username = await get_user_by_username(db, username)
        if existing_username:
            errors.append("This username is already taken")

    if errors:
        return templates.TemplateResponse(
            request,
            "pages/register.html",
            {
                "errors": errors,
                "email": email,
                "username": username,
                "display_name": display_name or "",
            },
            status_code=422,
        )

    user = await create_user(db, email, username, password, display_name)
    token = create_access_token(user.id)
    response = RedirectResponse(url="/dashboard", status_code=302)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=60 * 60 * 24,  # 24 hours
    )
    return response


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, user: User | None = Depends(get_optional_user)):
    if user:
        return RedirectResponse(url="/dashboard", status_code=302)
    return templates.TemplateResponse(request, "pages/login.html")


@router.post("/login")
async def login(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    form = await request.form()
    email = form.get("email", "").strip().lower()
    password = form.get("password", "")

    errors = []
    if not email:
        errors.append("Email is required")
    if not password:
        errors.append("Password is required")

    if errors:
        return templates.TemplateResponse(
            request,
            "pages/login.html",
            {"errors": errors, "email": email},
            status_code=422,
        )

    user = await authenticate_user(db, email, password)
    if not user:
        return templates.TemplateResponse(
            request,
            "pages/login.html",
            {
                "errors": ["Invalid email or password"],
                "email": email,
            },
            status_code=401,
        )

    token = create_access_token(user.id)
    response = RedirectResponse(url="/dashboard", status_code=302)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=60 * 60 * 24,
    )
    return response


@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie(key="access_token")
    return response
