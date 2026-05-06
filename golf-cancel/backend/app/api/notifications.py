from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Notification
from ..schemas import NotificationOut

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get("", response_model=List[NotificationOut])
def list_notifications(
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db),
):
    return (
        db.query(Notification)
        .order_by(Notification.sent_at.desc())
        .limit(limit)
        .all()
    )
