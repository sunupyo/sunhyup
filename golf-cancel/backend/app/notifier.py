"""Watch matching + Kakao 메시지 포맷."""
from __future__ import annotations
from datetime import datetime

from sqlalchemy.orm import Session

from .config import settings
from .kakao import send_self_message
from .models import Course, Notification, TeeTime, Watch


_WEEKDAY_KO = ["월", "화", "수", "목", "금", "토", "일"]


def _matches(watch: Watch, course: Course, tt: TeeTime) -> bool:
    if not watch.is_active:
        return False
    if watch.regions and course.region not in watch.regions:
        return False
    if watch.course_ids and course.id not in watch.course_ids:
        return False
    if watch.weekdays and tt.play_date.weekday() not in watch.weekdays:
        return False
    if watch.time_min and tt.tee_time < watch.time_min:
        return False
    if watch.time_max and tt.tee_time > watch.time_max:
        return False
    if watch.date_from and tt.play_date < watch.date_from:
        return False
    if watch.date_to and tt.play_date > watch.date_to:
        return False
    if watch.max_green_fee and tt.green_fee and tt.green_fee > watch.max_green_fee:
        return False
    if tt.slots_open < watch.min_slots:
        return False
    return True


def _format_message(course: Course, tt: TeeTime) -> str:
    weekday = _WEEKDAY_KO[tt.play_date.weekday()]
    fee = f"{tt.green_fee:,}원" if tt.green_fee else "그린피 미정"
    return (
        f"⛳ 취소티 발생\n"
        f"{course.name}\n"
        f"{tt.play_date.strftime('%Y-%m-%d')} ({weekday}) "
        f"{tt.tee_time.strftime('%H:%M')} · {tt.holes}홀\n"
        f"잔여 {tt.slots_open}자리 · {fee}"
    )


def _booking_link(course: Course, tt: TeeTime) -> str:
    if tt.raw_url:
        return tt.raw_url
    if course.booking_url:
        return course.booking_url
    return settings.FRONTEND_BASE_URL


async def evaluate_and_notify(db: Session, newly_open_tee_time_ids: list[int]) -> None:
    """주어진 tee_time id 들에 대해 활성 Watch 매칭하고 미발송이면 카카오 발송."""
    if not newly_open_tee_time_ids:
        return

    watches = db.query(Watch).filter(Watch.is_active.is_(True)).all()
    if not watches:
        return

    for tt_id in newly_open_tee_time_ids:
        tt = db.get(TeeTime, tt_id)
        if not tt:
            continue
        course = db.get(Course, tt.course_id)
        if not course:
            continue

        for w in watches:
            if not _matches(w, course, tt):
                continue
            # dedup: same (watch, tee_time) 이미 성공 발송했으면 skip
            already = (
                db.query(Notification)
                .filter(
                    Notification.watch_id == w.id,
                    Notification.tee_time_id == tt.id,
                    Notification.success.is_(True),
                )
                .first()
            )
            if already:
                continue

            text = _format_message(course, tt)
            link = _booking_link(course, tt)
            ok, err = await send_self_message(db, text=text, link_url=link)

            db.add(Notification(
                watch_id=w.id,
                tee_time_id=tt.id,
                channel="kakao",
                success=ok,
                error_msg=err,
                sent_at=datetime.utcnow(),
            ))
            db.commit()
