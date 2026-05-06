from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Course
from ..schemas import CourseOut

router = APIRouter(prefix="/api/courses", tags=["courses"])


@router.get("", response_model=List[CourseOut])
def list_courses(
    region: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(Course)
    if region:
        q = q.filter(Course.region == region)
    return q.order_by(Course.region, Course.name).all()


@router.patch("/{course_id}/toggle", response_model=CourseOut)
def toggle_course(course_id: int, db: Session = Depends(get_db)):
    c = db.get(Course, course_id)
    if not c:
        from fastapi import HTTPException
        raise HTTPException(404)
    c.is_active = not c.is_active
    db.commit()
    db.refresh(c)
    return c
