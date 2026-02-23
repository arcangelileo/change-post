import re

import pytest
from httpx import AsyncClient


async def _setup_project(client: AsyncClient) -> dict:
    """Create a user and project."""
    await client.post(
        "/register",
        data={
            "email": "apikey@test.com",
            "username": "apikeyuser",
            "password": "password123",
        },
    )
    await client.post(
        "/login",
        data={"email": "apikey@test.com", "password": "password123"},
    )
    resp = await client.post(
        "/projects/new",
        data={"name": "API Key Test"},
        follow_redirects=False,
    )
    project_id = resp.headers["location"].split("/projects/")[1]
    return {"project_id": project_id}


# --- API Key management ---

async def test_api_keys_requires_auth(client: AsyncClient):
    """API keys page requires authentication."""
    resp = await client.get("/projects/some-id/api-keys")
    assert resp.status_code == 401 or resp.status_code == 403


async def test_api_keys_page_loads(client: AsyncClient):
    """API keys page loads for project owner."""
    info = await _setup_project(client)
    resp = await client.get(f"/projects/{info['project_id']}/api-keys")
    assert resp.status_code == 200
    assert "API Keys" in resp.text
    assert "Create new API key" in resp.text


async def test_api_keys_empty(client: AsyncClient):
    """Empty API keys page shows appropriate message."""
    info = await _setup_project(client)
    resp = await client.get(f"/projects/{info['project_id']}/api-keys")
    assert resp.status_code == 200
    assert "No API keys yet" in resp.text


async def test_create_api_key(client: AsyncClient):
    """Creating an API key shows the raw key."""
    info = await _setup_project(client)
    resp = await client.post(
        f"/projects/{info['project_id']}/api-keys",
        data={"name": "Test Key"},
    )
    assert resp.status_code == 200
    assert "cpk_" in resp.text
    assert "API Key Created" in resp.text
    assert "Test Key" in resp.text


async def test_create_api_key_empty_name(client: AsyncClient):
    """Creating API key without name shows error."""
    info = await _setup_project(client)
    resp = await client.post(
        f"/projects/{info['project_id']}/api-keys",
        data={"name": ""},
    )
    assert resp.status_code == 422
    assert "required" in resp.text.lower()


async def test_delete_api_key(client: AsyncClient):
    """Can delete an API key."""
    info = await _setup_project(client)

    # Create a key
    resp = await client.post(
        f"/projects/{info['project_id']}/api-keys",
        data={"name": "Delete Me"},
    )
    assert resp.status_code == 200

    # Find key ID from the delete form
    match = re.search(r'/api-keys/([a-f0-9-]+)/delete', resp.text)
    assert match, "Could not find API key delete URL"
    key_id = match.group(1)

    # Delete the key
    resp = await client.post(
        f"/projects/{info['project_id']}/api-keys/{key_id}/delete",
        follow_redirects=False,
    )
    assert resp.status_code == 302

    # Verify it's gone
    resp = await client.get(f"/projects/{info['project_id']}/api-keys")
    assert "Delete Me" not in resp.text or "No API keys yet" in resp.text


async def test_api_key_shows_prefix(client: AsyncClient):
    """API key list shows key prefix."""
    info = await _setup_project(client)
    await client.post(
        f"/projects/{info['project_id']}/api-keys",
        data={"name": "Prefix Test"},
    )
    # Visit the list page (not the creation response)
    resp = await client.get(f"/projects/{info['project_id']}/api-keys")
    assert resp.status_code == 200
    assert "cpk_" in resp.text
    assert "Prefix Test" in resp.text


async def test_api_key_other_user_denied(client: AsyncClient):
    """Another user cannot access API keys for a project they don't own."""
    info = await _setup_project(client)

    # Register and login as another user
    await client.post(
        "/register",
        data={
            "email": "other-api@test.com",
            "username": "otherapi",
            "password": "password123",
        },
    )
    await client.post(
        "/login",
        data={"email": "other-api@test.com", "password": "password123"},
    )

    resp = await client.get(f"/projects/{info['project_id']}/api-keys")
    assert resp.status_code == 404
