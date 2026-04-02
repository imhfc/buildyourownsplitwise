import asyncio
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import settings

logger = logging.getLogger(__name__)


def _send_smtp(to_email: str, subject: str, html_content: str) -> None:
    """Blocking SMTP send — runs in a thread via asyncio.to_thread."""
    msg = MIMEMultipart("alternative")
    msg["From"] = f"{settings.APP_NAME} <{settings.SMTP_FROM_EMAIL}>"
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(html_content, "html", "utf-8"))

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
        server.starttls()
        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.send_message(msg)


async def send_invitation_email(
    to_email: str,
    inviter_name: str,
    group_name: str,
    invite_token: str,
) -> None:
    """Send group invitation email via Gmail SMTP."""
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        logger.info("SMTP not configured, skipping email to %s", to_email)
        return

    invite_url = f"{settings.FRONTEND_URL}/invite/email/{invite_token}"

    html_content = f"""
    <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto;">
      <h2>{inviter_name} 邀請你加入分帳群組</h2>
      <p>你收到一封來自 <strong>{inviter_name}</strong> 的邀請，
         加入「<strong>{group_name}</strong>」分帳群組。</p>
      <p>
        <a href="{invite_url}"
           style="display: inline-block; padding: 12px 24px;
                  background-color: #2563eb; color: #fff;
                  text-decoration: none; border-radius: 8px;">
          查看邀請
        </a>
      </p>
      <p style="color: #6b7280; font-size: 14px;">
        此邀請將在 {settings.EMAIL_INVITATION_EXPIRE_DAYS} 天後過期。
        如果你還沒有帳號，請先註冊後再接受邀請。
      </p>
      <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 24px 0;" />
      <p style="color: #9ca3af; font-size: 12px;">{settings.APP_NAME}</p>
    </div>
    """

    subject = f"{inviter_name} 邀請你加入「{group_name}」分帳群組"

    try:
        await asyncio.to_thread(_send_smtp, to_email, subject, html_content)
        logger.info("Invitation email sent to %s", to_email)
    except Exception as e:
        logger.error("Failed to send invitation email to %s: %s", to_email, e)
