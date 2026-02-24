import pytest


@pytest.mark.asyncio
async def test_register_page_loads(client):
    response = await client.get("/register")
    assert response.status_code == 200
    assert "Create your account" in response.text


@pytest.mark.asyncio
async def test_login_page_loads(client):
    response = await client.get("/login")
    assert response.status_code == 200
    assert "Welcome back" in response.text


@pytest.mark.asyncio
async def test_register_success(client):
    response = await client.post(
        "/register",
        data={
            "email": "test@example.com",
            "username": "testuser",
            "password": "securepass123",
            "display_name": "Test User",
        },
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert response.headers["location"] == "/dashboard"
    assert "access_token" in response.cookies


@pytest.mark.asyncio
async def test_register_short_password(client):
    response = await client.post(
        "/register",
        data={
            "email": "test@example.com",
            "username": "testuser",
            "password": "short",
        },
        follow_redirects=False,
    )
    assert response.status_code == 422
    assert "at least 8 characters" in response.text


@pytest.mark.asyncio
async def test_register_short_username(client):
    response = await client.post(
        "/register",
        data={
            "email": "test@example.com",
            "username": "ab",
            "password": "securepass123",
        },
        follow_redirects=False,
    )
    assert response.status_code == 422
    assert "at least 3 characters" in response.text


@pytest.mark.asyncio
async def test_register_invalid_email(client):
    response = await client.post(
        "/register",
        data={
            "email": "invalid",
            "username": "testuser",
            "password": "securepass123",
        },
        follow_redirects=False,
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_duplicate_email(client):
    # Register first user
    await client.post(
        "/register",
        data={
            "email": "test@example.com",
            "username": "testuser1",
            "password": "securepass123",
        },
        follow_redirects=False,
    )
    # Try to register with same email
    response = await client.post(
        "/register",
        data={
            "email": "test@example.com",
            "username": "testuser2",
            "password": "securepass123",
        },
        follow_redirects=False,
    )
    assert response.status_code == 422
    assert "already exists" in response.text


@pytest.mark.asyncio
async def test_register_duplicate_username(client):
    await client.post(
        "/register",
        data={
            "email": "test1@example.com",
            "username": "testuser",
            "password": "securepass123",
        },
        follow_redirects=False,
    )
    response = await client.post(
        "/register",
        data={
            "email": "test2@example.com",
            "username": "testuser",
            "password": "securepass123",
        },
        follow_redirects=False,
    )
    assert response.status_code == 422
    assert "already taken" in response.text


@pytest.mark.asyncio
async def test_login_success(client):
    # Register first
    await client.post(
        "/register",
        data={
            "email": "test@example.com",
            "username": "testuser",
            "password": "securepass123",
        },
        follow_redirects=False,
    )
    # Login
    response = await client.post(
        "/login",
        data={
            "email": "test@example.com",
            "password": "securepass123",
        },
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert response.headers["location"] == "/dashboard"
    assert "access_token" in response.cookies


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    # Register first
    await client.post(
        "/register",
        data={
            "email": "test@example.com",
            "username": "testuser",
            "password": "securepass123",
        },
        follow_redirects=False,
    )
    # Login with wrong password
    response = await client.post(
        "/login",
        data={
            "email": "test@example.com",
            "password": "wrongpassword",
        },
        follow_redirects=False,
    )
    assert response.status_code == 401
    assert "Invalid email or password" in response.text


@pytest.mark.asyncio
async def test_login_nonexistent_email(client):
    response = await client.post(
        "/login",
        data={
            "email": "nobody@example.com",
            "password": "somepassword",
        },
        follow_redirects=False,
    )
    assert response.status_code == 401
    assert "Invalid email or password" in response.text


@pytest.mark.asyncio
async def test_login_empty_fields(client):
    response = await client.post(
        "/login",
        data={"email": "", "password": ""},
        follow_redirects=False,
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_logout(client):
    # Register and get auth cookie
    reg_response = await client.post(
        "/register",
        data={
            "email": "test@example.com",
            "username": "testuser",
            "password": "securepass123",
        },
        follow_redirects=False,
    )
    # Logout
    response = await client.get("/logout", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/login"


@pytest.mark.asyncio
async def test_dashboard_requires_auth(client):
    response = await client.get("/dashboard", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/login"


@pytest.mark.asyncio
async def test_dashboard_accessible_when_logged_in(client):
    # Register and get cookie
    reg_response = await client.post(
        "/register",
        data={
            "email": "test@example.com",
            "username": "testuser",
            "password": "securepass123",
        },
        follow_redirects=False,
    )
    # Set cookie and access dashboard
    client.cookies.set("access_token", reg_response.cookies.get("access_token"))
    response = await client.get("/dashboard")
    assert response.status_code == 200
    assert "testuser" in response.text


@pytest.mark.asyncio
async def test_register_page_redirects_when_logged_in(client):
    # Register
    reg_response = await client.post(
        "/register",
        data={
            "email": "test@example.com",
            "username": "testuser",
            "password": "securepass123",
        },
        follow_redirects=False,
    )
    client.cookies.set("access_token", reg_response.cookies.get("access_token"))
    # Visit register page while logged in
    response = await client.get("/register", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/dashboard"


@pytest.mark.asyncio
async def test_login_page_redirects_when_logged_in(client):
    reg_response = await client.post(
        "/register",
        data={
            "email": "test@example.com",
            "username": "testuser",
            "password": "securepass123",
        },
        follow_redirects=False,
    )
    client.cookies.set("access_token", reg_response.cookies.get("access_token"))
    response = await client.get("/login", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/dashboard"


@pytest.mark.asyncio
async def test_root_redirects_to_login(client):
    response = await client.get("/", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/login"


@pytest.mark.asyncio
async def test_root_redirects_to_dashboard_when_logged_in(client):
    """Root route redirects authenticated users to dashboard."""
    reg_response = await client.post(
        "/register",
        data={
            "email": "test@example.com",
            "username": "testuser",
            "password": "securepass123",
        },
        follow_redirects=False,
    )
    client.cookies.set("access_token", reg_response.cookies.get("access_token"))
    response = await client.get("/", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/dashboard"


@pytest.mark.asyncio
async def test_404_page_renders_html(client):
    """404 errors show a nice HTML error page, not JSON."""
    response = await client.get("/nonexistent-page")
    assert response.status_code == 404
    assert "Page not found" in response.text
    assert "Go to Dashboard" in response.text
