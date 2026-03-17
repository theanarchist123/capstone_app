"""api/routes/notifications.py"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from api.deps import get_current_user
from models.user import User
from models.notification import Notification
from schemas import NotificationOut, SuccessResponse

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get("/", response_model=SuccessResponse)
async def list_notifications(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    q = select(Notification).where(
        Notification.user_id == current_user.id
    ).order_by(Notification.created_at.desc()).limit(50)
    notifs = (await db.execute(q)).scalars().all()
    return SuccessResponse(data=[NotificationOut.model_validate(n) for n in notifs])


@router.patch("/{notif_id}/read", response_model=SuccessResponse)
async def mark_read(
    notif_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    q = select(Notification).where(Notification.id == notif_id, Notification.user_id == current_user.id)
    notif = (await db.execute(q)).scalar_one_or_none()
    if not notif:
        raise HTTPException(404, "Notification not found")
    notif.read = True
    await db.commit()
    return SuccessResponse(message="Marked as read")


@router.post("/read-all", response_model=SuccessResponse)
async def mark_all_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import update
    stmt = (
        update(Notification)
        .where(Notification.user_id == current_user.id, Notification.read == False)
        .values(read=True)
    )
    await db.execute(stmt)
    await db.commit()
    return SuccessResponse(message="All notifications marked as read")
