# ChangePost

A changelog and product update management platform for SaaS companies. Publish beautiful, organized product updates, notify subscribers via email, and embed a "What's New" widget directly in your app.

## Features

- **Changelog posts** — Create, edit, and publish posts with Markdown support. Categorize as New Feature, Improvement, Bug Fix, or Announcement.
- **Public changelog page** — Branded, filterable timeline view with SEO meta tags. Shareable URL per project.
- **Email subscribers** — Visitors subscribe from the public page. Automatic notifications on new published posts via SMTP.
- **Embeddable widget** — A lightweight JS snippet adds a "What's New" bell button to any website. Tracks unread updates with localStorage.
- **Analytics dashboard** — View counts per post, category breakdown, and top posts ranking.
- **Programmatic API** — RESTful API with Bearer token auth for creating and listing posts from CI/CD pipelines.
- **Multi-project** — Manage multiple changelogs from a single account, each with its own slug, branding color, and subscribers.

## Tech Stack

- **Backend**: Python 3.12, FastAPI, SQLAlchemy (async) + aiosqlite
- **Frontend**: Jinja2 templates, Tailwind CSS (CDN), HTMX
- **Auth**: JWT tokens in httponly cookies, bcrypt password hashing
- **Database**: SQLite (Postgres-compatible schema for future migration)
- **Email**: SMTP with async support, configurable via env vars
- **Testing**: pytest + pytest-asyncio + httpx (115 tests)

## Quick Start

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

### Local Development

```bash
# Clone the repository
git clone https://github.com/arcangelileo/change-post.git
cd change-post

# Install dependencies
uv sync

# Copy environment config
cp .env.example .env
# Edit .env with your settings (SECRET_KEY, SMTP, etc.)

# Run the development server
uv run uvicorn app.main:app --reload --port 8000

# Open http://localhost:8000
```

### Run Tests

```bash
uv run pytest tests/ -v
```

### Docker

```bash
# Build and run
docker compose up --build

# Or build the image directly
docker build -t changepost .
docker run -p 8000:8000 --env-file .env changepost
```

The app will be available at `http://localhost:8000`.

## Configuration

All settings are configured via environment variables (or a `.env` file):

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | *(required)* | JWT signing key — use a long random string |
| `DATABASE_URL` | `sqlite+aiosqlite:///./changepost.db` | Database connection URL |
| `BASE_URL` | `http://localhost:8000` | Public base URL for links in emails and widget |
| `DEBUG` | `false` | Enable debug mode |
| `SMTP_HOST` | *(empty)* | SMTP server hostname (leave empty to disable email) |
| `SMTP_PORT` | `587` | SMTP server port |
| `SMTP_USER` | *(empty)* | SMTP username |
| `SMTP_PASSWORD` | *(empty)* | SMTP password |
| `SMTP_FROM_EMAIL` | `noreply@changepost.app` | Sender email address |
| `SMTP_USE_TLS` | `true` | Use STARTTLS for SMTP |

## API Reference

### Authentication

All API endpoints require a Bearer token in the `Authorization` header:

```
Authorization: Bearer cpk_your_api_key_here
```

API keys are created from the dashboard under **Project > API Keys**.

### Endpoints

#### List Posts

```
GET /api/v1/posts
GET /api/v1/posts?published=true
```

#### Create Post

```
POST /api/v1/posts
Content-Type: application/json

{
  "title": "New Feature: Dark Mode",
  "body_markdown": "We just shipped dark mode support!",
  "category": "new_feature",
  "is_published": true
}
```

Categories: `new_feature`, `improvement`, `bugfix`, `announcement`

#### Get Post

```
GET /api/v1/posts/{post_id}
```

### Widget API (Public)

```
GET /api/widget/{project_slug}/posts?limit=5
GET /api/widget/{project_slug}/embed.js
```

## Embedding the Widget

Add this script tag before the closing `</body>` tag of your website:

```html
<script src="https://your-changepost-url/api/widget/your-project-slug/embed.js" async></script>
```

This adds a floating bell button that shows your latest changelog posts in a popup panel.

## Project Structure

```
src/app/
├── main.py          # FastAPI app, router registration
├── config.py        # Pydantic Settings
├── database.py      # Async SQLAlchemy engine
├── api/             # Route handlers
├── models/          # SQLAlchemy ORM models
├── schemas/         # Pydantic request/response schemas
├── services/        # Business logic layer
├── templates/       # Jinja2 HTML templates
└── static/          # CSS, JS, images
```

## License

MIT
