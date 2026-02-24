# ChangePost

**Changelog and product update management for SaaS companies.**

ChangePost lets teams publish beautiful, organized product updates. Create posts categorized by type, publish them to a branded public changelog page, notify subscribers via email, and embed a "What's New" widget directly in your app. Think of it as a simpler, self-hostable alternative to Beamer or Changelogfy.

---

## Features

### Changelog Management
- **Rich Markdown Editor** — Write posts with a toolbar for bold, italic, headings, lists, code blocks, and links. Live preview toggle.
- **Categories** — Organize posts as New Feature, Improvement, Bug Fix, or Announcement — each with color-coded badges.
- **Draft/Publish Workflow** — Save drafts, publish when ready, or unpublish to pull posts back.

### Public Changelog Page
- **Branded Timeline** — Beautiful public page per project with your accent color, filterable by category.
- **SEO-Friendly** — Open Graph meta tags, semantic HTML, and clean URLs (`/changelog/{slug}`).
- **Subscriber Collection** — Email subscribe form built into the public page.

### Email Notifications
- **Automatic Alerts** — Subscribers receive an HTML email when a new post is published.
- **SMTP Integration** — Works with any SMTP provider (Gmail, SendGrid, Mailgun, Amazon SES).
- **Unsubscribe Links** — One-click unsubscribe via unique token in every email.

### Embeddable Widget
- **One-Line Install** — Add a `<script>` tag and get a floating bell button with a popup panel.
- **Unread Badge** — Red counter tracks new posts since last viewed using localStorage.
- **Mobile Responsive** — Works on desktop and mobile with touch-friendly UI.

### Analytics Dashboard
- **View Tracking** — Automatic view count per post on the public changelog.
- **Category Breakdown** — Visual bars showing post distribution by type.
- **Top Posts** — Ranked table of your most-viewed updates.

### Programmatic API
- **RESTful Endpoints** — Create and list posts from CI/CD pipelines or scripts.
- **API Key Auth** — Per-project Bearer tokens with SHA-256 hashed storage.
- **Full CRUD** — List, create, and retrieve posts programmatically.

### Multi-Project Support
- **Multiple Changelogs** — Manage separate changelogs from a single account.
- **Custom Branding** — Each project gets its own slug, description, and accent color.
- **Independent Subscribers** — Subscriber lists are per-project.

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3.12, FastAPI |
| **Database** | SQLite via async SQLAlchemy + aiosqlite |
| **Frontend** | Jinja2 templates, Tailwind CSS (CDN), HTMX |
| **Auth** | JWT tokens in httponly cookies, bcrypt |
| **Email** | SMTP with async support (aiosmtplib) |
| **Migrations** | Alembic (async-compatible) |
| **Testing** | pytest + pytest-asyncio + httpx (123 tests) |
| **Container** | Docker with multi-stage build |

---

## Quick Start

### Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/arcangelileo/change-post.git
cd change-post

# Configure environment
cp .env.example .env
# Edit .env — at minimum, set a strong SECRET_KEY

# Build and run
docker compose up --build -d

# Open http://localhost:8000
```

That's it. The app creates its SQLite database automatically on first run.

### Local Development

**Prerequisites:** Python 3.12+ and [uv](https://docs.astral.sh/uv/)

```bash
# Clone and install
git clone https://github.com/arcangelileo/change-post.git
cd change-post
uv sync

# Configure
cp .env.example .env

# Run the dev server
PYTHONPATH=src uv run uvicorn app.main:app --reload --port 8000

# Open http://localhost:8000
```

### Running Tests

```bash
uv run pytest tests/ -v
```

All 123 tests should pass. Tests use an in-memory SQLite database, so no setup needed.

---

## Configuration

All settings are configured via environment variables or a `.env` file.

### Core Settings

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | *(change in prod)* | JWT signing key. Generate with `python -c "import secrets; print(secrets.token_urlsafe(64))"` |
| `DATABASE_URL` | `sqlite+aiosqlite:///./changepost.db` | Database connection URL |
| `BASE_URL` | `http://localhost:8000` | Public URL for links in emails and the widget |
| `DEBUG` | `false` | Enable debug mode |
| `PORT` | `8000` | Host port mapping (Docker) |

### SMTP Settings (Optional)

Leave `SMTP_HOST` empty to disable email notifications. The app works fine without email — subscribers are still collected and can be notified once SMTP is configured.

| Variable | Default | Description |
|---|---|---|
| `SMTP_HOST` | *(empty)* | SMTP server hostname |
| `SMTP_PORT` | `587` | SMTP port (587 for STARTTLS, 465 for SSL) |
| `SMTP_USER` | *(empty)* | SMTP username |
| `SMTP_PASSWORD` | *(empty)* | SMTP password |
| `SMTP_FROM_EMAIL` | `noreply@changepost.app` | Sender address |
| `SMTP_USE_TLS` | `true` | Use STARTTLS encryption |

---

## API Reference

### Authentication

Create API keys from the dashboard under **Project → API Keys**. Use them as Bearer tokens:

```
Authorization: Bearer cpk_your_api_key_here
```

### Endpoints

#### List Posts

```http
GET /api/v1/posts
GET /api/v1/posts?published=true
```

**Response:**
```json
[
  {
    "id": 1,
    "title": "Dark Mode Support",
    "slug": "dark-mode-support",
    "body_markdown": "We just shipped dark mode!",
    "body_html": "<p>We just shipped dark mode!</p>",
    "category": "new_feature",
    "is_published": true,
    "published_at": "2026-02-24T10:00:00",
    "view_count": 42,
    "created_at": "2026-02-24T09:00:00"
  }
]
```

#### Create Post

```http
POST /api/v1/posts
Content-Type: application/json

{
  "title": "Dark Mode Support",
  "body_markdown": "We just shipped **dark mode** across the entire app!",
  "category": "new_feature",
  "is_published": true
}
```

**Categories:** `new_feature`, `improvement`, `bugfix`, `announcement`

When `is_published` is `true`, subscribers are automatically notified (if SMTP is configured).

#### Get Post

```http
GET /api/v1/posts/{post_id}
```

### Widget API (Public, No Auth Required)

```http
GET /api/widget/{project_slug}/posts?limit=5
GET /api/widget/{project_slug}/embed.js
```

### cURL Examples

```bash
# List published posts
curl -H "Authorization: Bearer cpk_your_key" \
  https://your-app.com/api/v1/posts?published=true

# Create a post from CI/CD
curl -X POST \
  -H "Authorization: Bearer cpk_your_key" \
  -H "Content-Type: application/json" \
  -d '{"title":"v2.1 Released","body_markdown":"Bug fixes and performance improvements.","category":"improvement","is_published":true}' \
  https://your-app.com/api/v1/posts
```

---

## Embedding the Widget

Add this script tag before the closing `</body>` tag of your website:

```html
<script src="https://your-changepost-url/api/widget/your-project-slug/embed.js" async></script>
```

This adds a floating bell button in the bottom-right corner. When clicked, it shows a popup panel with your latest changelog posts. A red badge indicates new updates since the user last checked.

The widget is:
- **Self-contained** — No dependencies, no CSS conflicts
- **Lightweight** — Single JS file, fetches data via JSON API
- **CORS-enabled** — Works from any domain
- **Mobile-friendly** — Responsive design with touch support

You can find your project's widget code and installation instructions in the dashboard under **Project → Widget**.

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                     Browser                          │
│  ┌──────────┐  ┌──────────┐  ┌───────────────────┐ │
│  │ Dashboard │  │  Public  │  │  Embedded Widget  │ │
│  │  (HTMX)  │  │ Changelog│  │   (Vanilla JS)    │ │
│  └────┬─────┘  └────┬─────┘  └────────┬──────────┘ │
└───────┼──────────────┼─────────────────┼────────────┘
        │              │                 │
        ▼              ▼                 ▼
┌─────────────────────────────────────────────────────┐
│                 FastAPI Application                   │
│                                                      │
│  ┌────────┐  ┌───────────┐  ┌──────────────────┐   │
│  │  Auth  │  │   HTML    │  │   REST API       │   │
│  │ (JWT)  │  │ Templates │  │ (Bearer Token)   │   │
│  └────┬───┘  └─────┬─────┘  └────────┬─────────┘   │
│       │            │                  │              │
│       ▼            ▼                  ▼              │
│  ┌──────────────────────────────────────────────┐   │
│  │              Service Layer                    │   │
│  │  auth · project · post · subscriber · email   │   │
│  └──────────────────┬───────────────────────────┘   │
│                     │                                │
│                     ▼                                │
│  ┌──────────────────────────────────────────────┐   │
│  │         SQLAlchemy ORM (async)                │   │
│  │  User · Project · Post · Subscriber · APIKey  │   │
│  └──────────────────┬───────────────────────────┘   │
│                     │                                │
│                     ▼                                │
│  ┌──────────────────────────────────────────────┐   │
│  │          SQLite (aiosqlite)                   │   │
│  └──────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

### Project Structure

```
src/app/
├── main.py          # FastAPI app, router registration, error handlers
├── config.py        # Pydantic Settings (all config via env vars)
├── database.py      # Async SQLAlchemy engine + session factory
├── api/             # Route handlers (one file per feature)
│   ├── auth.py      # Login, register, logout
│   ├── dashboard.py # Main dashboard with stats
│   ├── projects.py  # Project CRUD
│   ├── posts.py     # Post CRUD with markdown
│   ├── changelog.py # Public changelog pages
│   ├── subscribers.py # Subscriber management
│   ├── widget.py    # Widget JS + JSON API
│   ├── analytics.py # View stats dashboard
│   ├── api_keys.py  # API key management
│   └── programmatic.py # REST API for external access
├── models/          # SQLAlchemy ORM models
├── schemas/         # Pydantic request/response schemas
├── services/        # Business logic layer
├── templates/       # Jinja2 HTML templates (Tailwind CSS)
└── static/          # Static assets (CSS, JS, images)
```

### Key Design Decisions

- **Server-rendered HTML** with Jinja2 + Tailwind CSS CDN for fast page loads and zero build step
- **HTMX** for interactive elements without full client-side framework overhead
- **SQLite** for zero-config deployment; schema is Postgres-compatible for future migration
- **JWT in httponly cookies** for secure, stateless authentication
- **Alembic migrations** from the start for safe schema evolution
- **Markdown with sanitization** — python-markdown for rendering, bleach + regex for XSS prevention
- **Background email** — Notifications sent asynchronously so publishing is instant

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Make your changes
4. Run the tests (`uv run pytest tests/ -v`)
5. Commit and push (`git push origin feature/my-feature`)
6. Open a Pull Request

### Development Tips

- Use `PYTHONPATH=src uv run uvicorn app.main:app --reload` for auto-reload during development
- Tests use in-memory SQLite — no database setup needed
- The app auto-creates tables on startup via `init_db()`

---

## License

MIT
