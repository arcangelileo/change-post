import re

import pytest
from httpx import AsyncClient


async def _setup_project_with_api_key(client: AsyncClient) -> dict:
    """Create a user, project, and API key."""
    await client.post(
        "/register",
        data={
            "email": "progapi@test.com",
            "username": "progapiuser",
            "password": "password123",
        },
    )
    await client.post(
        "/login",
        data={"email": "progapi@test.com", "password": "password123"},
    )
    resp = await client.post(
        "/projects/new",
        data={"name": "API Project"},
        follow_redirects=False,
    )
    project_id = resp.headers["location"].split("/projects/")[1]

    # Create an API key
    resp = await client.post(
        f"/projects/{project_id}/api-keys",
        data={"name": "Test API Key"},
    )
    # Extract the raw key from the response
    match = re.search(r'(cpk_[A-Za-z0-9_-]+)', resp.text)
    assert match, "Could not find API key in response"
    raw_key = match.group(1)

    return {"project_id": project_id, "api_key": raw_key}


# --- Authentication ---

async def test_api_no_auth_header(client: AsyncClient):
    """API returns 401 without Authorization header."""
    resp = await client.get("/api/v1/posts")
    assert resp.status_code == 401


async def test_api_invalid_auth_format(client: AsyncClient):
    """API returns 401 with wrong Authorization format."""
    resp = await client.get(
        "/api/v1/posts",
        headers={"Authorization": "Basic abc123"},
    )
    assert resp.status_code == 401


async def test_api_invalid_key(client: AsyncClient):
    """API returns 401 with invalid API key."""
    resp = await client.get(
        "/api/v1/posts",
        headers={"Authorization": "Bearer cpk_invalid_key_here"},
    )
    assert resp.status_code == 401


# --- List posts ---

async def test_api_list_posts_empty(client: AsyncClient):
    """API returns empty list when no posts exist."""
    info = await _setup_project_with_api_key(client)
    resp = await client.get(
        "/api/v1/posts",
        headers={"Authorization": f"Bearer {info['api_key']}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["posts"] == []
    assert data["total"] == 0


async def test_api_list_posts(client: AsyncClient):
    """API returns posts after creating some."""
    info = await _setup_project_with_api_key(client)

    # Create a post via the web UI
    await client.post(
        f"/projects/{info['project_id']}/posts/new",
        data={
            "title": "API Listed Post",
            "body_markdown": "Body content",
            "category": "improvement",
            "action": "publish",
        },
        follow_redirects=False,
    )

    resp = await client.get(
        "/api/v1/posts",
        headers={"Authorization": f"Bearer {info['api_key']}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    assert any(p["title"] == "API Listed Post" for p in data["posts"])


async def test_api_list_posts_published_filter(client: AsyncClient):
    """API can filter to only published posts."""
    info = await _setup_project_with_api_key(client)

    # Create a published post
    await client.post(
        f"/projects/{info['project_id']}/posts/new",
        data={
            "title": "Published via UI",
            "body_markdown": "Body",
            "category": "improvement",
            "action": "publish",
        },
        follow_redirects=False,
    )

    # Create a draft post
    await client.post(
        f"/projects/{info['project_id']}/posts/new",
        data={
            "title": "Draft via UI",
            "body_markdown": "Body",
            "category": "bugfix",
            "action": "draft",
        },
        follow_redirects=False,
    )

    # Filter published only
    resp = await client.get(
        "/api/v1/posts?published=true",
        headers={"Authorization": f"Bearer {info['api_key']}"},
    )
    data = resp.json()
    for post in data["posts"]:
        assert post["is_published"] is True


# --- Create post via API ---

async def test_api_create_post(client: AsyncClient):
    """API can create a new post."""
    info = await _setup_project_with_api_key(client)
    resp = await client.post(
        "/api/v1/posts",
        headers={
            "Authorization": f"Bearer {info['api_key']}",
            "Content-Type": "application/json",
        },
        json={
            "title": "API Created Post",
            "body_markdown": "Created via the API!",
            "category": "new_feature",
            "is_published": True,
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["post"]["title"] == "API Created Post"
    assert data["post"]["category"] == "new_feature"
    assert data["post"]["is_published"] is True
    assert data["post"]["slug"] == "api-created-post"


async def test_api_create_post_draft(client: AsyncClient):
    """API can create a draft post."""
    info = await _setup_project_with_api_key(client)
    resp = await client.post(
        "/api/v1/posts",
        headers={
            "Authorization": f"Bearer {info['api_key']}",
            "Content-Type": "application/json",
        },
        json={
            "title": "Draft API Post",
            "body_markdown": "This is a draft",
            "category": "bugfix",
            "is_published": False,
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["post"]["is_published"] is False
    assert data["post"]["published_at"] is None


async def test_api_create_post_missing_title(client: AsyncClient):
    """API rejects post without title."""
    info = await _setup_project_with_api_key(client)
    resp = await client.post(
        "/api/v1/posts",
        headers={
            "Authorization": f"Bearer {info['api_key']}",
            "Content-Type": "application/json",
        },
        json={
            "body_markdown": "No title here",
            "category": "improvement",
        },
    )
    assert resp.status_code == 422


async def test_api_create_post_missing_body(client: AsyncClient):
    """API rejects post without body."""
    info = await _setup_project_with_api_key(client)
    resp = await client.post(
        "/api/v1/posts",
        headers={
            "Authorization": f"Bearer {info['api_key']}",
            "Content-Type": "application/json",
        },
        json={
            "title": "No Body Post",
            "category": "improvement",
        },
    )
    assert resp.status_code == 422


async def test_api_create_post_invalid_category(client: AsyncClient):
    """API rejects post with invalid category."""
    info = await _setup_project_with_api_key(client)
    resp = await client.post(
        "/api/v1/posts",
        headers={
            "Authorization": f"Bearer {info['api_key']}",
            "Content-Type": "application/json",
        },
        json={
            "title": "Bad Category",
            "body_markdown": "Body",
            "category": "not_a_real_category",
        },
    )
    assert resp.status_code == 422


# --- Get post by ID ---

async def test_api_get_post(client: AsyncClient):
    """API can retrieve a single post by ID."""
    info = await _setup_project_with_api_key(client)

    # Create a post
    resp = await client.post(
        "/api/v1/posts",
        headers={
            "Authorization": f"Bearer {info['api_key']}",
            "Content-Type": "application/json",
        },
        json={
            "title": "Fetch Me",
            "body_markdown": "Body to fetch",
            "category": "announcement",
        },
    )
    post_id = resp.json()["post"]["id"]

    # Fetch it
    resp = await client.get(
        f"/api/v1/posts/{post_id}",
        headers={"Authorization": f"Bearer {info['api_key']}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["post"]["title"] == "Fetch Me"
    assert data["post"]["body_html"]  # Should have rendered HTML


async def test_api_get_post_not_found(client: AsyncClient):
    """API returns 404 for nonexistent post."""
    info = await _setup_project_with_api_key(client)
    resp = await client.get(
        "/api/v1/posts/00000000-0000-0000-0000-000000000000",
        headers={"Authorization": f"Bearer {info['api_key']}"},
    )
    assert resp.status_code == 404


async def test_api_post_fields(client: AsyncClient):
    """API post response contains all expected fields."""
    info = await _setup_project_with_api_key(client)
    resp = await client.post(
        "/api/v1/posts",
        headers={
            "Authorization": f"Bearer {info['api_key']}",
            "Content-Type": "application/json",
        },
        json={
            "title": "Fields Test",
            "body_markdown": "Testing fields",
            "category": "improvement",
            "is_published": True,
        },
    )
    post = resp.json()["post"]
    assert "id" in post
    assert "title" in post
    assert "slug" in post
    assert "body_markdown" in post
    assert "category" in post
    assert "is_published" in post
    assert "published_at" in post
    assert "created_at" in post


async def test_api_create_published_post_with_subscribers(client: AsyncClient):
    """API can create a published post when subscribers exist (email send won't fail)."""
    info = await _setup_project_with_api_key(client)

    # Get project slug to subscribe
    resp = await client.get(f"/projects/{info['project_id']}")
    import re as _re
    slug_match = _re.search(r'/changelog/([\w-]+)', resp.text)
    slug = slug_match.group(1)

    # Add a subscriber
    await client.post(
        f"/changelog/{slug}/subscribe",
        data={"email": "api-notify@example.com"},
    )

    # Create published post via API — should succeed even with subscribers
    resp = await client.post(
        "/api/v1/posts",
        headers={
            "Authorization": f"Bearer {info['api_key']}",
            "Content-Type": "application/json",
        },
        json={
            "title": "Notification Test Post",
            "body_markdown": "Subscribers should be notified",
            "category": "new_feature",
            "is_published": True,
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["post"]["is_published"] is True
