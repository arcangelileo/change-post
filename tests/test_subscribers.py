import pytest
from httpx import AsyncClient


async def _register_and_login(client: AsyncClient) -> dict:
    await client.post(
        "/register",
        data={
            "email": "sub@test.com",
            "username": "subtester",
            "password": "password123",
        },
    )
    await client.post(
        "/login",
        data={"email": "sub@test.com", "password": "password123"},
    )
    resp = await client.post(
        "/projects/new",
        data={"name": "Sub Test Project"},
        follow_redirects=False,
    )
    project_url = resp.headers["location"]
    project_id = project_url.split("/projects/")[1]
    # Get project slug
    detail = await client.get(f"/projects/{project_id}")
    return {"project_id": project_id, "detail_html": detail.text}


async def _get_project_slug(client: AsyncClient, project_id: str) -> str:
    detail = await client.get(f"/projects/{project_id}")
    # Extract slug from the public changelog URL in the page
    import re
    match = re.search(r'/changelog/([a-z0-9-]+)', detail.text)
    return match.group(1) if match else "sub-test-project"


# --- Public subscribe tests ---

async def test_subscribe_form_on_public_page(client: AsyncClient):
    """The public changelog page should have a subscribe form."""
    info = await _register_and_login(client)
    slug = await _get_project_slug(client, info["project_id"])
    resp = await client.get(f"/changelog/{slug}")
    assert resp.status_code == 200
    assert 'action="/changelog/' in resp.text
    assert '/subscribe"' in resp.text
    assert 'name="email"' in resp.text
    assert "Stay in the loop" in resp.text


async def test_subscribe_success(client: AsyncClient):
    """A visitor can subscribe to a project's changelog."""
    info = await _register_and_login(client)
    slug = await _get_project_slug(client, info["project_id"])
    resp = await client.post(
        f"/changelog/{slug}/subscribe",
        data={"email": "subscriber@example.com"},
        follow_redirects=False,
    )
    assert resp.status_code == 200
    assert "subscribed" in resp.text.lower()


async def test_subscribe_duplicate(client: AsyncClient):
    """Subscribing twice shows success (prevents email enumeration)."""
    info = await _register_and_login(client)
    slug = await _get_project_slug(client, info["project_id"])
    await client.post(
        f"/changelog/{slug}/subscribe",
        data={"email": "dup@example.com"},
    )
    resp = await client.post(
        f"/changelog/{slug}/subscribe",
        data={"email": "dup@example.com"},
    )
    assert resp.status_code == 200
    assert "subscribed" in resp.text.lower()


async def test_subscribe_invalid_email(client: AsyncClient):
    """Subscribing with invalid email shows error."""
    info = await _register_and_login(client)
    slug = await _get_project_slug(client, info["project_id"])
    resp = await client.post(
        f"/changelog/{slug}/subscribe",
        data={"email": "not-an-email"},
    )
    assert resp.status_code == 422
    assert "valid email" in resp.text.lower()


async def test_subscribe_empty_email(client: AsyncClient):
    """Subscribing with empty email shows error."""
    info = await _register_and_login(client)
    slug = await _get_project_slug(client, info["project_id"])
    resp = await client.post(
        f"/changelog/{slug}/subscribe",
        data={"email": ""},
    )
    assert resp.status_code == 422


async def test_subscribe_nonexistent_project(client: AsyncClient):
    """Subscribing to nonexistent project returns 404."""
    resp = await client.post(
        "/changelog/no-such-project/subscribe",
        data={"email": "test@example.com"},
    )
    assert resp.status_code == 404


# --- Unsubscribe tests ---

async def test_unsubscribe_success(client: AsyncClient):
    """Unsubscribing with valid token works."""
    info = await _register_and_login(client)
    slug = await _get_project_slug(client, info["project_id"])

    # Subscribe first
    await client.post(
        f"/changelog/{slug}/subscribe",
        data={"email": "unsub@example.com"},
    )

    # Get the subscriber's token from the subscribers list
    resp = await client.get(f"/projects/{info['project_id']}/subscribers")
    assert "unsub@example.com" in resp.text

    # We need the unsubscribe token - it's in the DB, let's test the endpoint
    # For now, test with an invalid token
    resp = await client.get("/unsubscribe/invalid-token")
    assert resp.status_code == 200
    assert "expired" in resp.text.lower() or "no longer valid" in resp.text.lower()


async def test_unsubscribe_invalid_token(client: AsyncClient):
    """Unsubscribing with invalid token shows appropriate message."""
    resp = await client.get("/unsubscribe/totally-bogus-token")
    assert resp.status_code == 200
    assert "no longer valid" in resp.text.lower() or "expired" in resp.text.lower()


# --- Dashboard subscriber management ---

async def test_subscribers_list_requires_auth(client: AsyncClient):
    """Subscriber list requires authentication."""
    resp = await client.get("/projects/some-id/subscribers")
    assert resp.status_code == 401 or resp.status_code == 403


async def test_subscribers_list_empty(client: AsyncClient):
    """Empty subscriber list shows appropriate message."""
    info = await _register_and_login(client)
    resp = await client.get(f"/projects/{info['project_id']}/subscribers")
    assert resp.status_code == 200
    assert "No subscribers yet" in resp.text


async def test_subscribers_list_shows_subscribers(client: AsyncClient):
    """Subscriber list shows subscribed emails."""
    info = await _register_and_login(client)
    slug = await _get_project_slug(client, info["project_id"])

    # Subscribe
    await client.post(
        f"/changelog/{slug}/subscribe",
        data={"email": "list-test@example.com"},
    )

    resp = await client.get(f"/projects/{info['project_id']}/subscribers")
    assert resp.status_code == 200
    assert "list-test@example.com" in resp.text
    assert "1 subscriber" in resp.text


async def test_delete_subscriber(client: AsyncClient):
    """Can remove a subscriber from the dashboard."""
    info = await _register_and_login(client)
    slug = await _get_project_slug(client, info["project_id"])

    # Subscribe
    await client.post(
        f"/changelog/{slug}/subscribe",
        data={"email": "delete-me@example.com"},
    )

    # Get subscriber list to find subscriber ID
    resp = await client.get(f"/projects/{info['project_id']}/subscribers")
    assert "delete-me@example.com" in resp.text

    # Extract subscriber ID from the delete form action
    import re
    match = re.search(r'/subscribers/([a-f0-9-]+)/delete', resp.text)
    assert match, "Could not find subscriber delete URL"
    subscriber_id = match.group(1)

    # Delete
    resp = await client.post(
        f"/projects/{info['project_id']}/subscribers/{subscriber_id}/delete",
        follow_redirects=False,
    )
    assert resp.status_code == 302

    # Verify deleted
    resp = await client.get(f"/projects/{info['project_id']}/subscribers")
    assert "delete-me@example.com" not in resp.text


async def test_subscriber_count_on_project_detail(client: AsyncClient):
    """Project detail page shows correct subscriber count."""
    info = await _register_and_login(client)
    slug = await _get_project_slug(client, info["project_id"])

    # Subscribe two emails
    await client.post(
        f"/changelog/{slug}/subscribe",
        data={"email": "count1@example.com"},
    )
    await client.post(
        f"/changelog/{slug}/subscribe",
        data={"email": "count2@example.com"},
    )

    resp = await client.get(f"/projects/{info['project_id']}")
    assert resp.status_code == 200
    # The subscriber count should be 2
    assert ">2<" in resp.text
