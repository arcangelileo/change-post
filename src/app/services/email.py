import asyncio
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import settings

logger = logging.getLogger(__name__)


def _build_html_email(
    project_name: str,
    project_slug: str,
    post_title: str,
    post_slug: str,
    post_body_html: str,
    post_category_label: str,
    accent_color: str,
    unsubscribe_token: str,
) -> str:
    """Build a beautiful HTML email for a new post notification."""
    base_url = settings.base_url.rstrip("/")
    post_url = f"{base_url}/changelog/{project_slug}/{post_slug}"
    unsubscribe_url = f"{base_url}/unsubscribe/{unsubscribe_token}"

    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin: 0; padding: 0; background-color: #f9fafb; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
    <div style="max-width: 600px; margin: 0 auto; padding: 40px 20px;">
        <div style="background: #ffffff; border-radius: 12px; border: 1px solid #e5e7eb; overflow: hidden;">
            <!-- Header -->
            <div style="padding: 24px 32px; border-bottom: 1px solid #f3f4f6;">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <div style="width: 36px; height: 36px; border-radius: 8px; background-color: {accent_color}15; display: flex; align-items: center; justify-content: center;">
                        <span style="font-size: 18px; font-weight: 700; color: {accent_color};">{project_name[0].upper()}</span>
                    </div>
                    <div>
                        <span style="font-size: 16px; font-weight: 700; color: #111827;">{project_name}</span>
                        <span style="display: block; font-size: 12px; color: #9ca3af;">New update published</span>
                    </div>
                </div>
            </div>

            <!-- Content -->
            <div style="padding: 32px;">
                <span style="display: inline-block; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; padding: 3px 8px; border-radius: 4px; background-color: {accent_color}15; color: {accent_color}; margin-bottom: 12px;">{post_category_label}</span>
                <h1 style="font-size: 22px; font-weight: 700; color: #111827; margin: 0 0 16px 0; line-height: 1.3;">{post_title}</h1>
                <div style="font-size: 14px; line-height: 1.7; color: #4b5563;">
                    {post_body_html}
                </div>
                <div style="margin-top: 24px;">
                    <a href="{post_url}" style="display: inline-block; padding: 10px 20px; background-color: {accent_color}; color: #ffffff; text-decoration: none; border-radius: 8px; font-size: 14px; font-weight: 600;">Read full post</a>
                </div>
            </div>
        </div>

        <!-- Footer -->
        <div style="text-align: center; padding: 24px 0;">
            <p style="font-size: 12px; color: #9ca3af; margin: 0;">
                You're receiving this because you subscribed to {project_name} updates.
            </p>
            <p style="font-size: 12px; margin: 8px 0 0 0;">
                <a href="{unsubscribe_url}" style="color: #9ca3af; text-decoration: underline;">Unsubscribe</a>
            </p>
        </div>
    </div>
</body>
</html>"""


async def send_email(to_email: str, subject: str, html_body: str) -> bool:
    """Send an email via SMTP. Returns True on success."""
    if not settings.smtp_host:
        logger.warning("SMTP not configured, skipping email to %s", to_email)
        return False

    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _send_email_sync, to_email, subject, html_body)
        logger.info("Email sent to %s", to_email)
        return True
    except Exception as e:
        logger.error("Failed to send email to %s: %s", to_email, str(e))
        return False


def _send_email_sync(to_email: str, subject: str, html_body: str) -> None:
    """Synchronous email sending via SMTP."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.smtp_from_email
    msg["To"] = to_email

    # Plain text fallback
    msg.attach(MIMEText("View this email in an HTML-capable email client.", "plain"))
    msg.attach(MIMEText(html_body, "html"))

    if settings.smtp_use_tls:
        server = smtplib.SMTP(settings.smtp_host, settings.smtp_port)
        server.starttls()
    else:
        server = smtplib.SMTP(settings.smtp_host, settings.smtp_port)

    if settings.smtp_user and settings.smtp_password:
        server.login(settings.smtp_user, settings.smtp_password)

    server.send_message(msg)
    server.quit()


async def send_post_notification(
    subscribers: list,
    project_name: str,
    project_slug: str,
    post_title: str,
    post_slug: str,
    post_body_html: str,
    post_category_label: str,
    accent_color: str,
) -> int:
    """Send notification emails to all subscribers for a new post.
    Returns the count of successfully sent emails."""
    if not settings.smtp_host:
        logger.warning("SMTP not configured, skipping notifications for %d subscribers", len(subscribers))
        return 0

    subject = f"New update: {post_title} — {project_name}"
    sent_count = 0

    for subscriber in subscribers:
        html_body = _build_html_email(
            project_name=project_name,
            project_slug=project_slug,
            post_title=post_title,
            post_slug=post_slug,
            post_body_html=post_body_html,
            post_category_label=post_category_label,
            accent_color=accent_color,
            unsubscribe_token=subscriber.unsubscribe_token,
        )
        success = await send_email(subscriber.email, subject, html_body)
        if success:
            sent_count += 1

    logger.info("Sent %d/%d notification emails for post '%s'", sent_count, len(subscribers), post_title)
    return sent_count
