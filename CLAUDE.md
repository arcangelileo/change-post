# ChangePost

Phase: DEVELOPMENT

## Project Spec
- **Repo**: https://github.com/arcangelileo/change-post
- **Idea**: ChangePost is a changelog and product update management platform that lets SaaS companies publish beautiful, organized product updates. Teams create posts categorized by type (new feature, improvement, bugfix, announcement), publish them to a branded public changelog page, and optionally notify subscribers via email. An embeddable JavaScript widget lets products surface updates directly inside their app. Think of it as "Beamer / Changelogfy but simpler and self-hostable."
- **Target users**: SaaS founders, product managers, and dev teams who need to communicate product changes to their users. Companies of 1-200 employees who don't want to build their own changelog infrastructure.
- **Revenue model**: Freemium SaaS. Free tier: 1 project, 50 posts, basic public page. Pro ($19/mo): unlimited posts, 3 projects, custom branding, email notifications, embeddable widget, analytics. Team ($49/mo): unlimited projects, team members, API access, custom domain support.
- **Tech stack**: Python 3.12, FastAPI, SQLite (via async SQLAlchemy + aiosqlite), Jinja2 + Tailwind CSS (CDN) + HTMX, APScheduler for background email jobs, Docker
- **MVP scope**:
  1. User auth (register, login, logout) with JWT httponly cookies
  2. Project management (create/edit projects, each with a unique slug)
  3. Changelog post CRUD (title, body with markdown, category/label, published/draft status, publish date)
  4. Public changelog page per project (beautiful, branded, filterable by category)
  5. Email subscriber collection (visitors can subscribe to a project's changelog)
  6. Email notifications on new published posts (via background job)
  7. Embeddable widget script (JS snippet that shows a "What's New" badge/popup)
  8. Dashboard with post analytics (view counts per post)
  9. API endpoints for programmatic post creation (API key auth)

## Architecture Decisions
- **Auth**: JWT tokens stored in httponly cookies, bcrypt password hashing, middleware-based auth
- **Database**: SQLite with async SQLAlchemy + aiosqlite for MVP; schema designed to be Postgres-compatible for future migration
- **Migrations**: Alembic from the start, async-compatible
- **Templates**: Jinja2 server-rendered with Tailwind CSS via CDN, Inter font, HTMX for interactive bits
- **Markdown**: python-markdown for rendering changelog post bodies
- **Background jobs**: APScheduler integrated into FastAPI lifespan for sending email notifications
- **Email**: SMTP-based email sending (configurable via env vars), with async support
- **Widget**: A lightweight vanilla JS snippet served as a static file, fetches recent posts from a public API endpoint
- **API keys**: Per-project API keys for programmatic access, stored as hashed values
- **Configuration**: Pydantic Settings, all config via environment variables
- **Project structure**: `src/app/` with `api/`, `models/`, `schemas/`, `services/`, `templates/`, `static/` subdirs
- **Testing**: pytest + pytest-asyncio + httpx async test client, in-memory SQLite
- **Docker**: Multi-stage build, non-root user, single Dockerfile + docker-compose.yml

## Task Backlog
- [x] Create project structure, pyproject.toml, and configuration
- [x] Set up FastAPI app skeleton with health check and database setup
- [x] Create SQLAlchemy models (User, Project, Post, Subscriber, APIKey) and Alembic migrations
- [x] Implement user authentication (register, login, logout, JWT middleware)
- [x] Build auth UI (register page, login page, protected dashboard shell)
- [x] Implement project CRUD (create, edit, list, delete) with dashboard UI
- [x] Implement changelog post CRUD (create, edit, list, delete, publish/draft toggle) with rich markdown editor UI
- [x] Build public changelog page (per-project, beautiful, filterable by category, SEO-friendly)
- [ ] Implement email subscriber system (subscribe form on public page, unsubscribe, manage subscribers in dashboard)
- [ ] Add email notification background job (notify subscribers on post publish)
- [ ] Build embeddable widget (JS snippet + API endpoint for recent posts)
- [ ] Add post view tracking and analytics dashboard
- [ ] Implement API key management and programmatic post creation API
- [ ] Write comprehensive tests (auth, posts, public pages, API, subscriptions)
- [ ] Write Dockerfile and docker-compose.yml
- [ ] Write README with setup and deploy instructions

## Progress Log
### Session 1 — IDEATION
- Chose idea: ChangePost (changelog & product update management SaaS)
- Created spec and backlog
- Rationale: Universal demand (every SaaS needs changelogs), proven market (Beamer charges $49+/mo), clear MVP scope, good fit for FastAPI + HTMX stack

### Session 2 — SCAFFOLDING
- Created GitHub repo and project structure
- Set up pyproject.toml with all dependencies (FastAPI, SQLAlchemy, Alembic, pytest, etc.)
- Created Pydantic Settings configuration (`src/app/config.py`)
- Set up async SQLAlchemy database layer (`src/app/database.py`)
- Created all SQLAlchemy models: User, Project, Post, Subscriber, APIKey
- Set up Alembic for async migrations
- Built FastAPI app with health check endpoint
- Created test infrastructure with in-memory SQLite (conftest.py)
- All tests passing (2/2)
- Using `uv` for package management (system has Python 3.13.5)

### Session 3 — AUTH & PROJECT CRUD
- Implemented full user authentication: register, login, logout with JWT httponly cookies
- Used bcrypt directly (passlib incompatible with bcrypt 5.x) for password hashing
- Created auth dependency system (`get_current_user`, `get_optional_user`)
- Built beautiful auth UI: split-screen login/register pages with branding panel (Tailwind CSS, Inter font)
- Built responsive dashboard shell with sidebar navigation (mobile hamburger menu)
- Implemented full project CRUD: create, edit, list, delete with slug auto-generation
- Project ownership enforcement — users can only access their own projects
- Dashboard shows stats cards (projects count, total posts, subscribers)
- All templates use modern Tailwind CSS: cards, forms, empty states, error alerts, transitions
- Wrote 34 tests covering auth flows, project CRUD, access control, and edge cases
- All 34 tests passing with zero warnings

### Session 4 — POST CRUD & PUBLIC CHANGELOG
- Implemented full changelog post CRUD: create, edit, list, delete with markdown rendering
- Rich markdown editor with toolbar (bold, italic, headings, lists, code, links) and live write/preview toggle
- Posts support 4 categories: New Feature, Improvement, Bug Fix, Announcement — each with color-coded badges
- Draft/publish workflow: save as draft or publish immediately, toggle publish/unpublish from detail page
- Auto-generated post slugs from titles with uniqueness guarantee
- Built beautiful public changelog page with timeline layout, per-project branding (accent color), and category filter
- Public post detail pages with SEO meta tags (og:title, og:description, article:published_time)
- View count tracking: each public post page visit increments the counter
- Project detail page now shows live post stats (total, published, views) and recent post list
- Markdown rendered server-side via python-markdown (fenced_code, tables, nl2br, sane_lists extensions)
- All templates fully styled with Tailwind CSS: monospace editor, markdown body styles, responsive layout
- 63 tests total (29 new): post CRUD, markdown rendering, publish toggle, public changelog, category filtering, view tracking, access control, SEO meta
- All 63 tests passing

## Known Issues
(none yet)

## Files Structure
```
change-post/
├── CLAUDE.md
├── .gitignore
├── .env.example
├── pyproject.toml
├── alembic.ini
├── alembic/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
├── src/
│   └── app/
│       ├── __init__.py
│       ├── main.py
│       ├── config.py
│       ├── database.py
│       ├── api/
│       │   ├── __init__.py
│       │   ├── health.py
│       │   ├── auth.py
│       │   ├── deps.py
│       │   ├── dashboard.py
│       │   ├── projects.py
│       │   ├── posts.py
│       │   └── changelog.py
│       ├── models/
│       │   ├── __init__.py
│       │   ├── user.py
│       │   ├── project.py
│       │   ├── post.py
│       │   ├── subscriber.py
│       │   └── api_key.py
│       ├── schemas/
│       │   ├── __init__.py
│       │   ├── auth.py
│       │   ├── project.py
│       │   └── post.py
│       ├── services/
│       │   ├── __init__.py
│       │   ├── auth.py
│       │   ├── project.py
│       │   └── post.py
│       ├── templates/
│       │   ├── layouts/
│       │   │   ├── base.html
│       │   │   ├── auth.html
│       │   │   └── dashboard.html
│       │   ├── pages/
│       │   │   ├── login.html
│       │   │   ├── register.html
│       │   │   ├── dashboard.html
│       │   │   ├── projects/
│       │   │   │   ├── list.html
│       │   │   │   ├── create.html
│       │   │   │   ├── detail.html
│       │   │   │   └── edit.html
│       │   │   ├── posts/
│       │   │   │   ├── list.html
│       │   │   │   ├── create.html
│       │   │   │   ├── detail.html
│       │   │   │   └── edit.html
│       │   │   └── changelog/
│       │   │       ├── public.html
│       │   │       └── post.html
│       │   └── components/
│       └── static/
│           ├── css/
│           ├── js/
│           └── images/
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── test_health.py
    ├── test_auth.py
    ├── test_projects.py
    ├── test_posts.py
    └── test_changelog.py
```
