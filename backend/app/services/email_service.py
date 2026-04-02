import logging

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


async def send_invitation_email(
    to_email: str,
    inviter_name: str,
    group_name: str,
    invite_token: str,
) -> None:
    """Send group invitation email via SendGrid API."""
    if not settings.SENDGRID_API_KEY:
        logger.info("SendGrid API key not configured, skipping email to %s", to_email)
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

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                "https://api.sendgrid.com/v3/mail/send",
                headers={
                    "Authorization": f"Bearer {settings.SENDGRID_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "personalizations": [{"to": [{"email": to_email}]}],
                    "from": {
                        "email": settings.SENDGRID_FROM_EMAIL,
                        "name": settings.APP_NAME,
                    },
                    "subject": f"{inviter_name} 邀請你加入「{group_name}」分帳群組",
                    "content": [{"type": "text/html", "value": html_content}],
                },
            )
            if resp.status_code >= 400:
                logger.error("SendGrid API error: %s %s", resp.status_code, resp.text)
            else:
                logger.info("Invitation email sent to %s", to_email)
    except httpx.HTTPError as e:
        logger.error("Failed to send invitation email to %s: %s", to_email, e)
