import pytest
from httpx import AsyncClient


async def _setup_project_with_data(client: AsyncClient) -> dict:
    """Create a project with posts and views."""
    await client.post(
        "/register",
        data={
            "email": "analytics@test.com",
            "username": "analyticsuser",
            "password": "password123",
        },
    )
    await client.post(
        "/login",
        data={"email": "analytics@test.com", "password": "password123"},
    )
    resp = await client.post(
        "/projects/new",
        data={"name": "Analytics Test"},
        follow_redirects=False,
    )
    project_id = resp.headers["location"].split("/projects/")[1]
    slug = "analytics-test"

    # Create published posts
    for title, cat in [
        ("Feature One", "new_feature"),
        ("Bug Fix One", "bugfix"),
        ("Improvement One", "improvement"),
    ]:
        await client.post(
            f"/projects/{project_id}/posts/new",
            data={
                "title": title,
                "body_markdown": f"Content for {title}",
                "category": cat,
                "action": "publish",
            },
            follow_redirects=False,
        )

    # Generate some views by visiting public posts
    resp = await client.get(f"/changelog/{slug}")
    assert resp.status_code == 200

    return {"project_id": project_id, "slug": slug}


async def test_analytics_requires_auth(client: AsyncClient):
    """Analytics page requires authentication."""
    resp = await client.get("/projects/some-id/analytics")
    assert resp.status_code == 401 or resp.status_code == 403


async def test_analytics_page_loads(client: AsyncClient):
    """Analytics page loads for project owner."""
    info = await _setup_project_with_data(client)
    resp = await client.get(f"/projects/{info['project_id']}/analytics")
    assert resp.status_code == 200
    assert "Analytics" in resp.text


async def test_analytics_shows_stats(client: AsyncClient):
    """Analytics page shows key statistics."""
    info = await _setup_project_with_data(client)
    resp = await client.get(f"/projects/{info['project_id']}/analytics")
    assert resp.status_code == 200
    assert "Total Views" in resp.text
    assert "Published Posts" in resp.text
    assert "Subscribers" in resp.text
    assert "Avg Views/Post" in resp.text


async def test_analytics_shows_posts(client: AsyncClient):
    """Analytics page shows post titles in the top posts table."""
    info = await _setup_project_with_data(client)
    resp = await client.get(f"/projects/{info['project_id']}/analytics")
    assert resp.status_code == 200
    assert "Feature One" in resp.text


async def test_analytics_shows_categories(client: AsyncClient):
    """Analytics page shows category breakdown."""
    info = await _setup_project_with_data(client)
    resp = await client.get(f"/projects/{info['project_id']}/analytics")
    assert resp.status_code == 200
    assert "New Feature" in resp.text
    assert "Bug Fix" in resp.text
    assert "Improvement" in resp.text


async def test_analytics_other_user_denied(client: AsyncClient):
    """Another user cannot access analytics for a project they don't own."""
    info = await _setup_project_with_data(client)

    # Register and login as a different user
    await client.post(
        "/register",
        data={
            "email": "other@test.com",
            "username": "otheruser",
            "password": "password123",
        },
    )
    await client.post(
        "/login",
        data={"email": "other@test.com", "password": "password123"},
    )

    resp = await client.get(f"/projects/{info['project_id']}/analytics")
    assert resp.status_code == 404
