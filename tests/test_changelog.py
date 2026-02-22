import pytest


async def register_and_login(client, email="test@example.com", username="testuser"):
    reg_response = await client.post(
        "/register",
        data={
            "email": email,
            "username": username,
            "password": "securepass123",
        },
        follow_redirects=False,
    )
    client.cookies.set("access_token", reg_response.cookies.get("access_token"))
    return reg_response


async def create_project_with_slug(client, name="Test Project"):
    response = await client.post(
        "/projects/new",
        data={"name": name, "accent_color": "#6366f1", "description": "A test project"},
        follow_redirects=False,
    )
    project_id = response.headers["location"].split("/projects/")[1]
    # Get the slug from project detail
    detail = await client.get(f"/projects/{project_id}")
    # Extract slug from detail page
    import re
    slug_match = re.search(r'/changelog/([\w-]+)', detail.text)
    slug = slug_match.group(1) if slug_match else "test-project"
    return project_id, slug


async def create_published_post(client, project_id, title="Test Post", category="improvement"):
    response = await client.post(
        f"/projects/{project_id}/posts/new",
        data={
            "title": title,
            "body_markdown": "## What's new\n\n- Added feature X\n- Fixed bug Y",
            "category": category,
            "action": "publish",
        },
        follow_redirects=False,
    )
    post_id = response.headers["location"].split("/posts/")[1]
    return post_id


async def create_draft_post(client, project_id, title="Draft Post"):
    response = await client.post(
        f"/projects/{project_id}/posts/new",
        data={
            "title": title,
            "body_markdown": "Draft content",
            "category": "improvement",
            "action": "draft",
        },
        follow_redirects=False,
    )
    post_id = response.headers["location"].split("/posts/")[1]
    return post_id


# --- Public changelog page tests ---


@pytest.mark.asyncio
async def test_public_changelog_page(client):
    await register_and_login(client)
    project_id, slug = await create_project_with_slug(client)
    await create_published_post(client, project_id, "First Update")

    # Public page should be accessible without auth
    client.cookies.clear()
    response = await client.get(f"/changelog/{slug}")
    assert response.status_code == 200
    assert "First Update" in response.text
    assert "Changelog" in response.text


@pytest.mark.asyncio
async def test_public_changelog_shows_project_name(client):
    await register_and_login(client)
    project_id, slug = await create_project_with_slug(client, name="Awesome App")

    client.cookies.clear()
    response = await client.get(f"/changelog/{slug}")
    assert response.status_code == 200
    assert "Awesome App" in response.text


@pytest.mark.asyncio
async def test_public_changelog_only_shows_published(client):
    await register_and_login(client)
    project_id, slug = await create_project_with_slug(client)
    await create_published_post(client, project_id, "Published Post")
    await create_draft_post(client, project_id, "Secret Draft")

    client.cookies.clear()
    response = await client.get(f"/changelog/{slug}")
    assert response.status_code == 200
    assert "Published Post" in response.text
    assert "Secret Draft" not in response.text


@pytest.mark.asyncio
async def test_public_changelog_filter_by_category(client):
    await register_and_login(client)
    project_id, slug = await create_project_with_slug(client)
    await create_published_post(client, project_id, "New Feature A", category="new_feature")
    await create_published_post(client, project_id, "Bug Fix B", category="bugfix")

    client.cookies.clear()

    # All posts
    response = await client.get(f"/changelog/{slug}")
    assert "New Feature A" in response.text
    assert "Bug Fix B" in response.text

    # Filter by new_feature
    response = await client.get(f"/changelog/{slug}?category=new_feature")
    assert "New Feature A" in response.text
    assert "Bug Fix B" not in response.text

    # Filter by bugfix
    response = await client.get(f"/changelog/{slug}?category=bugfix")
    assert "Bug Fix B" in response.text
    assert "New Feature A" not in response.text


@pytest.mark.asyncio
async def test_public_changelog_empty(client):
    await register_and_login(client)
    project_id, slug = await create_project_with_slug(client)

    client.cookies.clear()
    response = await client.get(f"/changelog/{slug}")
    assert response.status_code == 200
    assert "No updates yet" in response.text


@pytest.mark.asyncio
async def test_public_changelog_nonexistent_project(client):
    response = await client.get("/changelog/nonexistent-slug")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_public_post_detail(client):
    await register_and_login(client)
    project_id, slug = await create_project_with_slug(client)
    await create_published_post(client, project_id, "Detailed Update")

    client.cookies.clear()
    # Get the post slug from the changelog page
    changelog = await client.get(f"/changelog/{slug}")
    import re
    post_slug_match = re.search(rf'/changelog/{slug}/([\w-]+)', changelog.text)
    assert post_slug_match, "Post link not found on changelog page"
    post_slug = post_slug_match.group(1)

    response = await client.get(f"/changelog/{slug}/{post_slug}")
    assert response.status_code == 200
    assert "Detailed Update" in response.text
    assert "What&#" in response.text or "What's new" in response.text.lower() or "Added feature" in response.text


@pytest.mark.asyncio
async def test_public_post_detail_increments_views(client):
    await register_and_login(client)
    project_id, slug = await create_project_with_slug(client)
    post_id = await create_published_post(client, project_id, "View Test")

    # Get post slug
    post_detail = await client.get(f"/projects/{project_id}/posts/{post_id}")
    import re
    slug_match = re.search(rf'/changelog/{slug}/([\w-]+)', post_detail.text)
    post_slug = slug_match.group(1) if slug_match else "view-test"

    client.cookies.clear()

    # Visit public post page twice
    await client.get(f"/changelog/{slug}/{post_slug}")
    await client.get(f"/changelog/{slug}/{post_slug}")

    # Re-login and check view count
    login_resp = await client.post(
        "/login",
        data={"email": "test@example.com", "password": "securepass123"},
        follow_redirects=False,
    )
    client.cookies.set("access_token", login_resp.cookies.get("access_token"))
    detail = await client.get(f"/projects/{project_id}/posts/{post_id}")
    assert "2 views" in detail.text


@pytest.mark.asyncio
async def test_public_post_draft_not_accessible(client):
    await register_and_login(client)
    project_id, slug = await create_project_with_slug(client)
    await create_draft_post(client, project_id, "Hidden Draft")

    client.cookies.clear()
    response = await client.get(f"/changelog/{slug}/hidden-draft")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_public_changelog_markdown_rendered(client):
    await register_and_login(client)
    project_id, slug = await create_project_with_slug(client)
    await client.post(
        f"/projects/{project_id}/posts/new",
        data={
            "title": "Markdown Rendering",
            "body_markdown": "**Important** change and `code_example`",
            "category": "improvement",
            "action": "publish",
        },
        follow_redirects=False,
    )

    client.cookies.clear()
    response = await client.get(f"/changelog/{slug}")
    assert response.status_code == 200
    assert "<strong>Important</strong>" in response.text
    assert "<code>code_example</code>" in response.text


@pytest.mark.asyncio
async def test_public_changelog_seo_meta(client):
    await register_and_login(client)
    project_id, slug = await create_project_with_slug(client)
    post_id = await create_published_post(client, project_id, "SEO Test Post")

    # Get post slug
    detail = await client.get(f"/projects/{project_id}/posts/{post_id}")
    import re
    match = re.search(rf'/changelog/{slug}/([\w-]+)', detail.text)
    post_slug = match.group(1)

    client.cookies.clear()
    response = await client.get(f"/changelog/{slug}/{post_slug}")
    assert response.status_code == 200
    assert 'og:title' in response.text
    assert "SEO Test Post" in response.text


@pytest.mark.asyncio
async def test_category_labels_displayed(client):
    await register_and_login(client)
    project_id, slug = await create_project_with_slug(client)
    await create_published_post(client, project_id, "Feature X", category="new_feature")

    client.cookies.clear()
    response = await client.get(f"/changelog/{slug}")
    assert "New Feature" in response.text
