from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.post import CATEGORIES, get_published_posts_for_project
from app.services.project import get_project_by_slug

router = APIRouter(prefix="/api/widget", tags=["widget"])


@router.get("/{project_slug}/posts")
async def widget_posts(
    project_slug: str,
    limit: int = 5,
    db: AsyncSession = Depends(get_db),
):
    """Public API endpoint for the embeddable widget to fetch recent posts."""
    project = await get_project_by_slug(db, project_slug)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    limit = min(max(limit, 1), 20)
    posts = await get_published_posts_for_project(db, project.id)
    posts = posts[:limit]

    return JSONResponse(
        content={
            "project": {
                "name": project.name,
                "slug": project.slug,
                "accent_color": project.accent_color,
            },
            "posts": [
                {
                    "title": post.title,
                    "slug": post.slug,
                    "category": post.category,
                    "category_label": CATEGORIES.get(post.category, {}).get("label", post.category),
                    "published_at": post.published_at.isoformat() if post.published_at else None,
                    "excerpt": (post.body_markdown[:150] + "...") if len(post.body_markdown) > 150 else post.body_markdown,
                    "url": f"/changelog/{project.slug}/{post.slug}",
                }
                for post in posts
            ],
        },
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET",
            "Access-Control-Allow-Headers": "Content-Type",
            "Cache-Control": "public, max-age=60",
        },
    )


@router.get("/{project_slug}/embed.js")
async def widget_script(
    project_slug: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Serves the embeddable widget JavaScript snippet for a specific project."""
    project = await get_project_by_slug(db, project_slug)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    base_url = str(request.base_url).rstrip("/")

    js_code = f"""
(function() {{
  'use strict';

  var SLUG = '{project.slug}';
  var ACCENT = '{project.accent_color}';
  var BASE_URL = '{base_url}';
  var API_URL = BASE_URL + '/api/widget/' + SLUG + '/posts?limit=5';
  var CHANGELOG_URL = BASE_URL + '/changelog/' + SLUG;

  // Prevent double-init
  if (window.__changepost_loaded) return;
  window.__changepost_loaded = true;

  // Inject styles
  var style = document.createElement('style');
  style.textContent = `
    #cp-widget-trigger {{
      position: fixed;
      bottom: 24px;
      right: 24px;
      width: 52px;
      height: 52px;
      border-radius: 50%;
      background: ${{ACCENT}};
      color: #fff;
      border: none;
      cursor: pointer;
      box-shadow: 0 4px 12px rgba(0,0,0,0.15);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 99998;
      transition: transform 0.2s, box-shadow 0.2s;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }}
    #cp-widget-trigger:hover {{
      transform: scale(1.08);
      box-shadow: 0 6px 20px rgba(0,0,0,0.2);
    }}
    #cp-widget-trigger svg {{
      width: 24px;
      height: 24px;
    }}
    #cp-widget-badge {{
      position: absolute;
      top: -4px;
      right: -4px;
      width: 20px;
      height: 20px;
      border-radius: 50%;
      background: #ef4444;
      color: #fff;
      font-size: 11px;
      font-weight: 700;
      display: none;
      align-items: center;
      justify-content: center;
      border: 2px solid #fff;
    }}
    #cp-widget-panel {{
      position: fixed;
      bottom: 88px;
      right: 24px;
      width: 380px;
      max-height: 480px;
      background: #fff;
      border-radius: 16px;
      box-shadow: 0 20px 60px rgba(0,0,0,0.15), 0 0 0 1px rgba(0,0,0,0.05);
      z-index: 99999;
      display: none;
      flex-direction: column;
      overflow: hidden;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      animation: cpSlideUp 0.25s ease-out;
    }}
    @keyframes cpSlideUp {{
      from {{ opacity: 0; transform: translateY(12px); }}
      to {{ opacity: 1; transform: translateY(0); }}
    }}
    #cp-widget-header {{
      padding: 16px 20px;
      border-bottom: 1px solid #f3f4f6;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }}
    #cp-widget-header h3 {{
      margin: 0;
      font-size: 15px;
      font-weight: 700;
      color: #111827;
    }}
    #cp-widget-header a {{
      font-size: 12px;
      color: ${{ACCENT}};
      text-decoration: none;
      font-weight: 600;
    }}
    #cp-widget-header a:hover {{
      text-decoration: underline;
    }}
    #cp-widget-posts {{
      flex: 1;
      overflow-y: auto;
      padding: 4px 0;
    }}
    .cp-widget-post {{
      display: block;
      padding: 14px 20px;
      text-decoration: none;
      color: inherit;
      border-bottom: 1px solid #f9fafb;
      transition: background 0.15s;
    }}
    .cp-widget-post:hover {{
      background: #f9fafb;
    }}
    .cp-widget-post:last-child {{
      border-bottom: none;
    }}
    .cp-post-meta {{
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 4px;
    }}
    .cp-post-cat {{
      font-size: 10px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      padding: 2px 6px;
      border-radius: 4px;
      background: ${{ACCENT}}15;
      color: ${{ACCENT}};
    }}
    .cp-post-date {{
      font-size: 11px;
      color: #9ca3af;
    }}
    .cp-post-title {{
      font-size: 13px;
      font-weight: 600;
      color: #111827;
      margin: 0 0 3px 0;
      line-height: 1.4;
    }}
    .cp-post-excerpt {{
      font-size: 12px;
      color: #6b7280;
      margin: 0;
      line-height: 1.5;
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
      overflow: hidden;
    }}
    .cp-widget-empty {{
      padding: 40px 20px;
      text-align: center;
      color: #9ca3af;
      font-size: 13px;
    }}
    .cp-widget-footer {{
      padding: 10px 20px;
      border-top: 1px solid #f3f4f6;
      text-align: center;
    }}
    .cp-widget-footer a {{
      font-size: 11px;
      color: #9ca3af;
      text-decoration: none;
    }}
    .cp-widget-footer a:hover {{
      color: #6b7280;
    }}
    @media (max-width: 440px) {{
      #cp-widget-panel {{
        right: 12px;
        left: 12px;
        width: auto;
        bottom: 80px;
      }}
    }}
  `;
  document.head.appendChild(style);

  // Create trigger button
  var trigger = document.createElement('button');
  trigger.id = 'cp-widget-trigger';
  trigger.setAttribute('aria-label', "What's New");
  trigger.innerHTML = '<svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"/></svg><span id="cp-widget-badge"></span>';
  document.body.appendChild(trigger);

  // Create panel
  var panel = document.createElement('div');
  panel.id = 'cp-widget-panel';
  panel.innerHTML = '<div id="cp-widget-header"><h3>What\\'s New</h3><a href="' + CHANGELOG_URL + '" target="_blank">View all</a></div><div id="cp-widget-posts"><div class="cp-widget-empty">Loading...</div></div><div class="cp-widget-footer"><a href="' + CHANGELOG_URL + '" target="_blank">Powered by ChangePost</a></div>';
  document.body.appendChild(panel);

  var isOpen = false;

  trigger.addEventListener('click', function() {{
    isOpen = !isOpen;
    panel.style.display = isOpen ? 'flex' : 'none';
    if (isOpen) {{
      var badge = document.getElementById('cp-widget-badge');
      badge.style.display = 'none';
      try {{ localStorage.setItem('cp_last_seen_' + SLUG, new Date().toISOString()); }} catch(e) {{}}
    }}
  }});

  // Close on outside click
  document.addEventListener('click', function(e) {{
    if (isOpen && !panel.contains(e.target) && !trigger.contains(e.target)) {{
      isOpen = false;
      panel.style.display = 'none';
    }}
  }});

  // Fetch posts
  function loadPosts() {{
    fetch(API_URL)
      .then(function(r) {{ return r.json(); }})
      .then(function(data) {{
        var container = document.getElementById('cp-widget-posts');
        if (!data.posts || data.posts.length === 0) {{
          container.innerHTML = '<div class="cp-widget-empty">No updates yet. Check back soon!</div>';
          return;
        }}

        var html = '';
        data.posts.forEach(function(post) {{
          var date = post.published_at ? new Date(post.published_at).toLocaleDateString('en-US', {{month: 'short', day: 'numeric', year: 'numeric'}}) : '';
          html += '<a class="cp-widget-post" href="' + BASE_URL + post.url + '" target="_blank">';
          html += '<div class="cp-post-meta"><span class="cp-post-cat">' + (post.category_label || post.category) + '</span><span class="cp-post-date">' + date + '</span></div>';
          html += '<p class="cp-post-title">' + post.title + '</p>';
          html += '<p class="cp-post-excerpt">' + post.excerpt + '</p>';
          html += '</a>';
        }});
        container.innerHTML = html;

        // Show badge if there are new posts since last seen
        try {{
          var lastSeen = localStorage.getItem('cp_last_seen_' + SLUG);
          if (lastSeen && data.posts.length > 0) {{
            var lastSeenDate = new Date(lastSeen);
            var newCount = 0;
            data.posts.forEach(function(p) {{
              if (p.published_at && new Date(p.published_at) > lastSeenDate) newCount++;
            }});
            if (newCount > 0) {{
              var badge = document.getElementById('cp-widget-badge');
              badge.textContent = newCount > 9 ? '9+' : newCount;
              badge.style.display = 'flex';
            }}
          }} else if (!lastSeen && data.posts.length > 0) {{
            var badge = document.getElementById('cp-widget-badge');
            badge.textContent = data.posts.length > 9 ? '9+' : data.posts.length;
            badge.style.display = 'flex';
          }}
        }} catch(e) {{}}
      }})
      .catch(function() {{
        var container = document.getElementById('cp-widget-posts');
        container.innerHTML = '<div class="cp-widget-empty">Unable to load updates.</div>';
      }});
  }}

  loadPosts();
}})();
"""

    return Response(
        content=js_code,
        media_type="application/javascript",
        headers={
            "Access-Control-Allow-Origin": "*",
            "Cache-Control": "public, max-age=300",
        },
    )
