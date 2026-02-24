import pytest


async def register_and_login(client, email="test@example.com", username="testuser"):
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


async def create_test_project(client, name="Test Project"):
    response = await client.post(
        "/projects/new",
        data={"name": name, "accent_color": "#6366f1"},
        follow_redirects=False,
    )
    project_id = response.headers["location"].split("/projects/")[1]
    return project_id


async def create_test_post(client, project_id, title="Test Post", action="draft"):
    response = await client.post(
        f"/projects/{project_id}/posts/new",
        data={
            "title": title,
            "body_markdown": "## Changes\n\n- Added feature X\n- Fixed bug Y",
            "category": "new_feature",
            "action": action,
        },
        follow_redirects=False,
    )
    post_id = response.headers["location"].split("/posts/")[1]
    return post_id


# --- Post CRUD Tests ---


@pytest.mark.asyncio
async def test_posts_list_requires_auth(client):
    response = await client.get("/projects/fake-id/posts", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/login"


@pytest.mark.asyncio
async def test_posts_list_empty(client):
    await register_and_login(client)
    project_id = await create_test_project(client)
    response = await client.get(f"/projects/{project_id}/posts")
    assert response.status_code == 200
    assert "No posts yet" in response.text


@pytest.mark.asyncio
async def test_create_post_page(client):
    await register_and_login(client)
    project_id = await create_test_project(client)
    response = await client.get(f"/projects/{project_id}/posts/new")
    assert response.status_code == 200
    assert "New Post" in response.text
    assert "New Feature" in response.text  # category option


@pytest.mark.asyncio
async def test_create_post_as_draft(client):
    await register_and_login(client)
    project_id = await create_test_project(client)
    response = await client.post(
        f"/projects/{project_id}/posts/new",
        data={
            "title": "My First Update",
            "body_markdown": "Some great changes here.",
            "category": "improvement",
            "action": "draft",
        },
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert "/posts/" in response.headers["location"]


@pytest.mark.asyncio
async def test_create_post_and_publish(client):
    await register_and_login(client)
    project_id = await create_test_project(client)
    response = await client.post(
        f"/projects/{project_id}/posts/new",
        data={
            "title": "Published Update",
            "body_markdown": "This is live!",
            "category": "announcement",
            "action": "publish",
        },
        follow_redirects=False,
    )
    assert response.status_code == 302
    post_url = response.headers["location"]

    # Verify it's published
    detail = await client.get(post_url)
    assert detail.status_code == 200
    assert "Published" in detail.text
    assert "Published Update" in detail.text


@pytest.mark.asyncio
async def test_create_post_empty_title(client):
    await register_and_login(client)
    project_id = await create_test_project(client)
    response = await client.post(
        f"/projects/{project_id}/posts/new",
        data={
            "title": "",
            "body_markdown": "Some content",
            "category": "improvement",
            "action": "draft",
        },
        follow_redirects=False,
    )
    assert response.status_code == 422
    assert "required" in response.text.lower()


@pytest.mark.asyncio
async def test_create_post_empty_body(client):
    await register_and_login(client)
    project_id = await create_test_project(client)
    response = await client.post(
        f"/projects/{project_id}/posts/new",
        data={
            "title": "Good title",
            "body_markdown": "",
            "category": "improvement",
            "action": "draft",
        },
        follow_redirects=False,
    )
    assert response.status_code == 422
    assert "required" in response.text.lower()


@pytest.mark.asyncio
async def test_post_detail_page(client):
    await register_and_login(client)
    project_id = await create_test_project(client)
    post_id = await create_test_post(client, project_id)
    response = await client.get(f"/projects/{project_id}/posts/{post_id}")
    assert response.status_code == 200
    assert "Test Post" in response.text
    assert "Draft" in response.text


@pytest.mark.asyncio
async def test_post_markdown_rendering(client):
    await register_and_login(client)
    project_id = await create_test_project(client)
    response = await client.post(
        f"/projects/{project_id}/posts/new",
        data={
            "title": "Markdown Test",
            "body_markdown": "**bold text** and *italic*",
            "category": "improvement",
            "action": "draft",
        },
        follow_redirects=False,
    )
    post_url = response.headers["location"]
    detail = await client.get(post_url)
    assert "<strong>bold text</strong>" in detail.text
    assert "<em>italic</em>" in detail.text


@pytest.mark.asyncio
async def test_edit_post_page(client):
    await register_and_login(client)
    project_id = await create_test_project(client)
    post_id = await create_test_post(client, project_id)
    response = await client.get(f"/projects/{project_id}/posts/{post_id}/edit")
    assert response.status_code == 200
    assert "Edit Post" in response.text
    assert "Test Post" in response.text


@pytest.mark.asyncio
async def test_update_post(client):
    await register_and_login(client)
    project_id = await create_test_project(client)
    post_id = await create_test_post(client, project_id)

    response = await client.post(
        f"/projects/{project_id}/posts/{post_id}/edit",
        data={
            "title": "Updated Title",
            "body_markdown": "Updated content here.",
            "category": "bugfix",
        },
        follow_redirects=False,
    )
    assert response.status_code == 302

    detail = await client.get(f"/projects/{project_id}/posts/{post_id}")
    assert "Updated Title" in detail.text
    assert "Bug Fix" in detail.text


@pytest.mark.asyncio
async def test_toggle_publish(client):
    await register_and_login(client)
    project_id = await create_test_project(client)
    post_id = await create_test_post(client, project_id)

    # Publish
    response = await client.post(
        f"/projects/{project_id}/posts/{post_id}/toggle-publish",
        follow_redirects=False,
    )
    assert response.status_code == 302

    detail = await client.get(f"/projects/{project_id}/posts/{post_id}")
    assert "Published" in detail.text

    # Unpublish
    response = await client.post(
        f"/projects/{project_id}/posts/{post_id}/toggle-publish",
        follow_redirects=False,
    )
    assert response.status_code == 302

    detail = await client.get(f"/projects/{project_id}/posts/{post_id}")
    assert "Draft" in detail.text


@pytest.mark.asyncio
async def test_delete_post(client):
    await register_and_login(client)
    project_id = await create_test_project(client)
    post_id = await create_test_post(client, project_id)

    response = await client.post(
        f"/projects/{project_id}/posts/{post_id}/delete",
        follow_redirects=False,
    )
    assert response.status_code == 302

    # Verify deleted
    detail = await client.get(f"/projects/{project_id}/posts/{post_id}")
    assert detail.status_code == 404


@pytest.mark.asyncio
async def test_posts_listed_on_project_detail(client):
    await register_and_login(client)
    project_id = await create_test_project(client)
    await create_test_post(client, project_id, title="Feature Alpha")

    response = await client.get(f"/projects/{project_id}")
    assert response.status_code == 200
    assert "Feature Alpha" in response.text


@pytest.mark.asyncio
async def test_post_not_accessible_by_other_user(client):
    # User 1 creates project and post
    await register_and_login(client, email="user1@test.com", username="user1")
    project_id = await create_test_project(client)
    post_id = await create_test_post(client, project_id)

    # User 2 tries to access
    client.cookies.clear()
    await register_and_login(client, email="user2@test.com", username="user2")
    response = await client.get(f"/projects/{project_id}/posts/{post_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_post_slug_generated(client):
    await register_and_login(client)
    project_id = await create_test_project(client)
    await create_test_post(client, project_id, title="My Great Feature")

    detail = await client.get(f"/projects/{project_id}/posts")
    assert detail.status_code == 200
    assert "My Great Feature" in detail.text


@pytest.mark.asyncio
async def test_multiple_posts_listing(client):
    await register_and_login(client)
    project_id = await create_test_project(client)
    for i in range(3):
        await create_test_post(client, project_id, title=f"Update {i}")

    response = await client.get(f"/projects/{project_id}/posts")
    assert response.status_code == 200
    assert "Update 0" in response.text
    assert "Update 1" in response.text
    assert "Update 2" in response.text
    assert "3 total" in response.text
