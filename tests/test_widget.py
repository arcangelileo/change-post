import json

import pytest
from httpx import AsyncClient


async def _setup_project_with_posts(client: AsyncClient) -> dict:
    """Create a project with some published posts."""
    await client.post(
        "/register",
        data={
            "email": "widget@test.com",
            "username": "widgetuser",
            "password": "password123",
        },
    )
    await client.post(
        "/login",
        data={"email": "widget@test.com", "password": "password123"},
    )
    resp = await client.post(
        "/projects/new",
        data={"name": "Widget Test"},
        follow_redirects=False,
    )
    project_id = resp.headers["location"].split("/projects/")[1]

    # Create a published post
    await client.post(
        f"/projects/{project_id}/posts/new",
        data={
            "title": "Widget Feature Post",
            "body_markdown": "This is a test post for the widget.",
            "category": "new_feature",
            "action": "publish",
        },
        follow_redirects=False,
    )

    # Create a draft post (should not appear in widget)
    await client.post(
        f"/projects/{project_id}/posts/new",
        data={
            "title": "Draft Post",
            "body_markdown": "This is a draft.",
            "category": "bugfix",
            "action": "draft",
        },
        follow_redirects=False,
    )

    return {"project_id": project_id, "slug": "widget-test"}


# --- Widget JSON API ---

async def test_widget_posts_api(client: AsyncClient):
    """Widget API returns JSON with published posts."""
    info = await _setup_project_with_posts(client)
    resp = await client.get(f"/api/widget/{info['slug']}/posts")
    assert resp.status_code == 200
    data = resp.json()
    assert "posts" in data
    assert "project" in data
    assert data["project"]["slug"] == info["slug"]
    assert len(data["posts"]) >= 1


async def test_widget_posts_only_published(client: AsyncClient):
    """Widget API only shows published posts."""
    info = await _setup_project_with_posts(client)
    resp = await client.get(f"/api/widget/{info['slug']}/posts")
    data = resp.json()
    for post in data["posts"]:
        assert "Draft Post" not in post["title"]


async def test_widget_posts_has_required_fields(client: AsyncClient):
    """Widget API posts contain all required fields."""
    info = await _setup_project_with_posts(client)
    resp = await client.get(f"/api/widget/{info['slug']}/posts")
    data = resp.json()
    post = data["posts"][0]
    assert "title" in post
    assert "slug" in post
    assert "category" in post
    assert "category_label" in post
    assert "published_at" in post
    assert "excerpt" in post
    assert "url" in post


async def test_widget_posts_limit(client: AsyncClient):
    """Widget API respects limit parameter."""
    info = await _setup_project_with_posts(client)
    resp = await client.get(f"/api/widget/{info['slug']}/posts?limit=1")
    data = resp.json()
    assert len(data["posts"]) <= 1


async def test_widget_posts_cors_headers(client: AsyncClient):
    """Widget API returns CORS headers for cross-origin embedding."""
    info = await _setup_project_with_posts(client)
    resp = await client.get(f"/api/widget/{info['slug']}/posts")
    assert resp.headers.get("access-control-allow-origin") == "*"


async def test_widget_posts_nonexistent_project(client: AsyncClient):
    """Widget API returns 404 for nonexistent project."""
    resp = await client.get("/api/widget/no-such-project/posts")
    assert resp.status_code == 404


# --- Widget JS embed ---

async def test_widget_embed_js(client: AsyncClient):
    """Widget embed.js endpoint returns JavaScript."""
    info = await _setup_project_with_posts(client)
    resp = await client.get(f"/api/widget/{info['slug']}/embed.js")
    assert resp.status_code == 200
    assert "javascript" in resp.headers.get("content-type", "")
    assert "cp-widget-trigger" in resp.text
    assert info["slug"] in resp.text


async def test_widget_embed_js_nonexistent_project(client: AsyncClient):
    """Widget embed.js returns 404 for nonexistent project."""
    resp = await client.get("/api/widget/no-such-project/embed.js")
    assert resp.status_code == 404


async def test_widget_embed_js_cors_headers(client: AsyncClient):
    """Widget embed.js has CORS headers."""
    info = await _setup_project_with_posts(client)
    resp = await client.get(f"/api/widget/{info['slug']}/embed.js")
    assert resp.headers.get("access-control-allow-origin") == "*"


# --- Widget embed page (dashboard) ---

async def test_widget_embed_page_requires_auth(client: AsyncClient):
    """Widget embed page requires authentication — redirects to login."""
    resp = await client.get("/projects/some-id/widget", follow_redirects=False)
    assert resp.status_code == 302
    assert resp.headers["location"] == "/login"


async def test_widget_embed_page(client: AsyncClient):
    """Widget embed page shows embed code snippet."""
    info = await _setup_project_with_posts(client)
    resp = await client.get(f"/projects/{info['project_id']}/widget")
    assert resp.status_code == 200
    assert "embed.js" in resp.text
    assert "Embeddable Widget" in resp.text
    assert info["slug"] in resp.text


async def test_widget_embed_js_has_html_escape(client: AsyncClient):
    """Widget JS includes HTML escaping function to prevent XSS."""
    info = await _setup_project_with_posts(client)
    resp = await client.get(f"/api/widget/{info['slug']}/embed.js")
    assert resp.status_code == 200
    # Verify the esc() function is included for XSS prevention
    assert "function esc(" in resp.text
    # Verify esc() is used for post content rendering
    assert "esc(post.title)" in resp.text
    assert "esc(post.excerpt)" in resp.text
