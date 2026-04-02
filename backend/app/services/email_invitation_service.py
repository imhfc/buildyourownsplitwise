import secrets
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError, ValidationError
from app.models.email_invitation import EmailInvitation
from app.models.group import Group, GroupMember
from app.models.user import User
from app.schemas.email_invitation import EmailInvitationResponse, PendingInvitationResponse
from app.services.activity_log_service import log_activity
from app.services.group_service import check_membership


def _normalize_email(email: str) -> str:
    return email.lower().strip()


async def create_invitation(
    db: AsyncSession,
    group_id: uuid.UUID,
    inviter_id: uuid.UUID,
    email: str,
) -> dict:
    """Create an email invitation and return info needed for sending the email."""
    email = _normalize_email(email)
    if not email or "@" not in email:
        raise ValidationError("Invalid email address")

    await check_membership(db, group_id, inviter_id)

    # Check if this email is already a group member
    result = await db.execute(
        select(GroupMember)
        .join(User, GroupMember.user_id == User.id)
        .where(
            GroupMember.group_id == group_id,
            func.lower(User.email) == email,
        )
    )
    if result.scalar_one_or_none():
        raise ConflictError("This email is already a group member")

    # Check for existing pending invitation (same group + email)
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(EmailInvitation).where(
            EmailInvitation.group_id == group_id,
            EmailInvitation.email == email,
            EmailInvitation.status == "pending",
            EmailInvitation.expires_at > now,
        )
    )
    if result.scalar_one_or_none():
        raise ConflictError("A pending invitation already exists for this email")

    # Create invitation
    expires_at = now + timedelta(days=settings.EMAIL_INVITATION_EXPIRE_DAYS)
    token = secrets.token_urlsafe(32)
    invitation = EmailInvitation(
        group_id=group_id,
        inviter_id=inviter_id,
        email=email,
        token=token,
        status="pending",
        created_at=now,
        expires_at=expires_at,
    )
    db.add(invitation)
    await db.flush()

    # Get group name and inviter name for the email
    group_result = await db.execute(select(Group.name).where(Group.id == group_id))
    group_name = group_result.scalar_one()
    inviter_result = await db.execute(select(User.display_name).where(User.id == inviter_id))
    inviter_name = inviter_result.scalar_one()

    await log_activity(
        db, group_id=group_id, actor_id=inviter_id, action="email_invitation_sent",
        target_type="email_invitation", target_id=invitation.id, extra_name=email,
    )

    return {
        "id": invitation.id,
        "group_id": group_id,
        "email": email,
        "status": "pending",
        "inviter_name": inviter_name,
        "group_name": group_name,
        "token": token,
        "created_at": invitation.created_at,
        "expires_at": invitation.expires_at,
        "responded_at": None,
    }


async def list_group_invitations(
    db: AsyncSession,
    group_id: uuid.UUID,
    user_id: uuid.UUID,
) -> list[EmailInvitationResponse]:
    """List all email invitations for a group (visible to members)."""
    await check_membership(db, group_id, user_id)

    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(
            EmailInvitation,
            User.display_name.label("inviter_name"),
            Group.name.label("group_name"),
        )
        .join(User, EmailInvitation.inviter_id == User.id)
        .join(Group, EmailInvitation.group_id == Group.id)
        .where(
            EmailInvitation.group_id == group_id,
            Group.deleted_at.is_(None),
        )
        .order_by(EmailInvitation.created_at.desc())
    )
    rows = result.all()

    invitations = []
    for inv, inviter_name, group_name in rows:
        status = inv.status
        if status == "pending" and inv.expires_at <= now:
            status = "expired"
            inv.status = "expired"

        invitations.append(EmailInvitationResponse(
            id=inv.id,
            group_id=inv.group_id,
            email=inv.email,
            status=status,
            inviter_name=inviter_name,
            group_name=group_name,
            created_at=inv.created_at,
            expires_at=inv.expires_at,
            responded_at=inv.responded_at,
        ))

    return invitations


async def get_pending_for_user(
    db: AsyncSession,
    user_email: str,
) -> list[PendingInvitationResponse]:
    """Get pending invitations for a user by their email."""
    email = _normalize_email(user_email)
    now = datetime.now(timezone.utc)

    result = await db.execute(
        select(
            EmailInvitation,
            Group.name.label("group_name"),
            Group.description.label("group_description"),
            User.display_name.label("inviter_name"),
        )
        .join(Group, EmailInvitation.group_id == Group.id)
        .join(User, EmailInvitation.inviter_id == User.id)
        .where(
            EmailInvitation.email == email,
            EmailInvitation.status == "pending",
            EmailInvitation.expires_at > now,
            Group.deleted_at.is_(None),
        )
        .order_by(EmailInvitation.created_at.desc())
    )
    rows = result.all()

    invitations = []
    for inv, group_name, group_description, inviter_name in rows:
        # Get member count
        count_result = await db.execute(
            select(func.count(GroupMember.id)).where(GroupMember.group_id == inv.group_id)
        )
        member_count = count_result.scalar() or 0

        invitations.append(PendingInvitationResponse(
            id=inv.id,
            group_id=inv.group_id,
            group_name=group_name,
            group_description=group_description,
            inviter_name=inviter_name,
            member_count=member_count,
            created_at=inv.created_at,
            expires_at=inv.expires_at,
        ))

    return invitations


async def respond(
    db: AsyncSession,
    invitation_id: uuid.UUID,
    user_id: uuid.UUID,
    user_email: str,
    action: str,
) -> dict:
    """Accept or decline an email invitation."""
    email = _normalize_email(user_email)
    now = datetime.now(timezone.utc)

    result = await db.execute(
        select(EmailInvitation).where(EmailInvitation.id == invitation_id)
    )
    invitation = result.scalar_one_or_none()
    if not invitation:
        raise NotFoundError("Invitation not found")

    if invitation.email != email:
        raise ForbiddenError("This invitation is not for your email")

    if invitation.status != "pending":
        raise ConflictError(f"Invitation already {invitation.status}")

    if invitation.expires_at <= now:
        invitation.status = "expired"
        raise ConflictError("Invitation has expired")

    if action == "accept":
        # Check not already a member
        existing = await db.execute(
            select(GroupMember).where(
                GroupMember.group_id == invitation.group_id,
                GroupMember.user_id == user_id,
            )
        )
        if existing.scalar_one_or_none():
            invitation.status = "accepted"
            invitation.responded_at = now
            raise ConflictError("Already a member of this group")

        member = GroupMember(
            group_id=invitation.group_id,
            user_id=user_id,
            role="member",
        )
        db.add(member)
        invitation.status = "accepted"
        invitation.responded_at = now

        # Log activity
        user_result = await db.execute(select(User.display_name).where(User.id == user_id))
        user_name = user_result.scalar_one_or_none() or "Unknown"
        await log_activity(
            db, group_id=invitation.group_id, actor_id=user_id,
            action="member_added", target_type="member",
            target_id=user_id, extra_name=user_name,
        )

        return {"detail": "Joined group successfully", "group_id": str(invitation.group_id)}

    elif action == "decline":
        invitation.status = "declined"
        invitation.responded_at = now
        return {"detail": "Invitation declined"}

    raise ValidationError("Invalid action")


async def count_pending(db: AsyncSession, user_email: str) -> int:
    """Count pending invitations for an email address."""
    if not user_email:
        return 0
    email = _normalize_email(user_email)
    now = datetime.now(timezone.utc)

    result = await db.execute(
        select(func.count(EmailInvitation.id))
        .join(Group, EmailInvitation.group_id == Group.id)
        .where(
            EmailInvitation.email == email,
            EmailInvitation.status == "pending",
            EmailInvitation.expires_at > now,
            Group.deleted_at.is_(None),
        )
    )
    return result.scalar() or 0
