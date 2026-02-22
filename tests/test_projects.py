import pytest


async def register_and_login(client, email="test@example.com", username="testuser"):
    """Helper to register a user and set the auth cookie."""
    reg_response = await client.post(
        "/register",
        data={
            "email": email,
            "username": username,
            "password": "securepass123",
            "display_name": "Test User",
        },
        follow_redirects=False,
    )
    client.cookies.set("access_token", reg_response.cookies.get("access_token"))
    return reg_response


@pytest.mark.asyncio
async def test_projects_list_requires_auth(client):
    response = await client.get("/projects", follow_redirects=False)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_projects_list_empty(client):
    await register_and_login(client)
    response = await client.get("/projects")
    assert response.status_code == 200
    assert "No projects yet" in response.text


@pytest.mark.asyncio
async def test_create_project_page(client):
    await register_and_login(client)
    response = await client.get("/projects/new")
    assert response.status_code == 200
    assert "Create a new project" in response.text


@pytest.mark.asyncio
async def test_create_project_success(client):
    await register_and_login(client)
    response = await client.post(
        "/projects/new",
        data={
            "name": "My App",
            "description": "A great app",
            "website_url": "https://myapp.com",
            "accent_color": "#6366f1",
        },
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert "/projects/" in response.headers["location"]


@pytest.mark.asyncio
async def test_create_project_empty_name(client):
    await register_and_login(client)
    response = await client.post(
        "/projects/new",
        data={
            "name": "",
            "description": "",
            "accent_color": "#6366f1",
        },
        follow_redirects=False,
    )
    assert response.status_code == 422
    assert "required" in response.text


@pytest.mark.asyncio
async def test_project_detail_page(client):
    await register_and_login(client)
    # Create project
    create_response = await client.post(
        "/projects/new",
        data={
            "name": "My App",
            "description": "A great app",
            "accent_color": "#6366f1",
        },
        follow_redirects=False,
    )
    project_url = create_response.headers["location"]
    # View detail
    response = await client.get(project_url)
    assert response.status_code == 200
    assert "My App" in response.text
    assert "A great app" in response.text


@pytest.mark.asyncio
async def test_project_edit_page(client):
    await register_and_login(client)
    create_response = await client.post(
        "/projects/new",
        data={"name": "My App", "accent_color": "#6366f1"},
        follow_redirects=False,
    )
    project_url = create_response.headers["location"]
    response = await client.get(f"{project_url}/edit")
    assert response.status_code == 200
    assert "Edit Project" in response.text
    assert "My App" in response.text


@pytest.mark.asyncio
async def test_project_update(client):
    await register_and_login(client)
    create_response = await client.post(
        "/projects/new",
        data={"name": "My App", "accent_color": "#6366f1"},
        follow_redirects=False,
    )
    project_url = create_response.headers["location"]

    response = await client.post(
        f"{project_url}/edit",
        data={
            "name": "Updated App",
            "description": "Updated description",
            "accent_color": "#10b981",
        },
        follow_redirects=False,
    )
    assert response.status_code == 302

    # Verify update
    detail_response = await client.get(project_url)
    assert "Updated App" in detail_response.text
    assert "Updated description" in detail_response.text


@pytest.mark.asyncio
async def test_project_delete(client):
    await register_and_login(client)
    create_response = await client.post(
        "/projects/new",
        data={"name": "To Delete", "accent_color": "#6366f1"},
        follow_redirects=False,
    )
    project_url = create_response.headers["location"]

    response = await client.post(
        f"{project_url}/delete",
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert response.headers["location"] == "/projects"

    # Verify deleted
    detail_response = await client.get(project_url)
    assert detail_response.status_code == 404


@pytest.mark.asyncio
async def test_project_not_found(client):
    await register_and_login(client)
    response = await client.get("/projects/nonexistent-id")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_project_owned_by_other_user(client):
    # User 1 creates project
    await register_and_login(client, email="user1@test.com", username="user1")
    create_response = await client.post(
        "/projects/new",
        data={"name": "User1 Project", "accent_color": "#6366f1"},
        follow_redirects=False,
    )
    project_url = create_response.headers["location"]

    # User 2 tries to access
    client.cookies.clear()
    await register_and_login(client, email="user2@test.com", username="user2")
    response = await client.get(project_url)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_project_slug_generated(client):
    await register_and_login(client)
    create_response = await client.post(
        "/projects/new",
        data={"name": "My Great App", "accent_color": "#6366f1"},
        follow_redirects=False,
    )
    project_url = create_response.headers["location"]
    detail_response = await client.get(project_url)
    assert "my-great-app" in detail_response.text


@pytest.mark.asyncio
async def test_projects_listed_on_dashboard(client):
    await register_and_login(client)
    await client.post(
        "/projects/new",
        data={"name": "Dashboard Project", "accent_color": "#6366f1"},
        follow_redirects=False,
    )
    response = await client.get("/dashboard")
    assert response.status_code == 200
    assert "Dashboard Project" in response.text


@pytest.mark.asyncio
async def test_multiple_projects(client):
    await register_and_login(client)
    for i in range(3):
        await client.post(
            "/projects/new",
            data={"name": f"Project {i}", "accent_color": "#6366f1"},
            follow_redirects=False,
        )
    response = await client.get("/projects")
    assert response.status_code == 200
    assert "Project 0" in response.text
    assert "Project 1" in response.text
    assert "Project 2" in response.text
