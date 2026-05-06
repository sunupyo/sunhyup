from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Course, TeeTime
from ..schemas import TeeTimeOut

router = APIRouter(prefix="/api/teetimes", tags=["teetimes"])


@router.get("", response_model=List[TeeTimeOut])
def list_open_teetimes(
    region: Optional[str] = Query(None),
    course_id: Optional[int] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    db: Session = Depends(get_db),
):
    q = (
        db.query(TeeTime, Course)
        .join(Course, Course.id == TeeTime.course_id)
        .filter(TeeTime.status == "open")
    )
    if region:
        q = q.filter(Course.region == region)
    if course_id:
        q = q.filter(Course.id == course_id)
    if date_from:
        q = q.filter(TeeTime.play_date >= date_from)
    if date_to:
        q = q.filter(TeeTime.play_date <= date_to)

    rows = q.order_by(TeeTime.play_date, TeeTime.tee_time).limit(500).all()
    return [
        TeeTimeOut(
            id=tt.id,
            course_id=c.id,
            course_name=c.name,
            region=c.region,
            play_date=tt.play_date,
            tee_time=tt.tee_time,
            holes=tt.holes,
            green_fee=tt.green_fee,
            slots_open=tt.slots_open,
            raw_url=tt.raw_url,
            status=tt.status,
            first_seen_at=tt.first_seen_at,
        )
        for tt, c in rows
    ]
