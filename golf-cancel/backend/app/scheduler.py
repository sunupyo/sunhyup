"""1분 주기로 모든 활성 코스를 크롤링 → diff → 카카오 알림."""
import logging
from datetime import datetime
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.orm import Session

from .config import settings
from .crawlers.base import CrawlerContext, CrawledTeeTime
from .crawlers.registry import get_crawler
from .db import SessionLocal
from .models import Course, Platform, TeeTime
from .notifier import evaluate_and_notify

logger = logging.getLogger("scheduler")
scheduler: Optional[AsyncIOScheduler] = None


def _key(t: CrawledTeeTime) -> tuple:
    return (t.course_id, t.play_date, t.tee_time, t.holes)


def _row_key(r: TeeTime) -> tuple:
    return (r.course_id, r.play_date, r.tee_time, r.holes)


async def _crawl_one(db: Session, course: Course) -> list[CrawledTeeTime]:
    if settings.ENABLE_DEMO_CRAWLER and course.platform != Platform.DEMO.value:
        # 데모 모드일 때는 모든 코스를 demo crawler 로 시뮬레이션
        crawler = get_crawler(Platform.DEMO.value)
    else:
        crawler = get_crawler(course.platform)

    if crawler is None:
        return []
    ctx = CrawlerContext(
        course_id=course.id,
        course_name=course.name,
        platform_course_id=course.platform_course_id,
        booking_url=course.booking_url,
    )
    try:
        return await crawler.fetch(ctx)
    except Exception as e:
        logger.exception("crawler error course=%s err=%s", course.name, e)
        return []


async def poll_once() -> None:
    db = SessionLocal()
    try:
        courses = db.query(Course).filter(Course.is_active.is_(True)).all()
        if not courses:
            return

        # 1) 모든 코스 크롤링 → 현재 열려있는 슬롯 set
        crawled: list[CrawledTeeTime] = []
        for c in courses:
            crawled.extend(await _crawl_one(db, c))

        crawled_keys = {_key(t): t for t in crawled}

        # 2) DB 의 현재 상태 (status=open) 조회
        course_ids = [c.id for c in courses]
        existing_open = (
            db.query(TeeTime)
            .filter(TeeTime.course_id.in_(course_ids), TeeTime.status == "open")
            .all()
        )
        existing_keys = {_row_key(r): r for r in existing_open}

        now = datetime.utcnow()
        newly_open_ids: list[int] = []

        # 3) crawled 에 있는 항목 처리
        for k, t in crawled_keys.items():
            row = existing_keys.get(k)
            if row is None:
                # 완전 새 슬롯이거나, 기존 status=taken 이었던 행이 다시 살아남
                row = (
                    db.query(TeeTime)
                    .filter(
                        TeeTime.course_id == t.course_id,
                        TeeTime.play_date == t.play_date,
                        TeeTime.tee_time == t.tee_time,
                        TeeTime.holes == t.holes,
                    )
                    .first()
                )
                if row is None:
                    row = TeeTime(
                        course_id=t.course_id,
                        play_date=t.play_date,
                        tee_time=t.tee_time,
                        holes=t.holes,
                        green_fee=t.green_fee,
                        slots_open=t.slots_open,
                        raw_url=t.raw_url,
                        status="open",
                        first_seen_at=now,
                        last_seen_at=now,
                    )
                    db.add(row)
                    db.flush()
                    newly_open_ids.append(row.id)
                else:
                    # taken → open 으로 부활
                    if row.status != "open":
                        row.status = "open"
                        row.first_seen_at = now
                        newly_open_ids.append(row.id)
                    row.green_fee = t.green_fee
                    row.slots_open = t.slots_open
                    row.raw_url = t.raw_url
                    row.last_seen_at = now
            else:
                # 이미 열려있던 슬롯 — 갱신만
                row.green_fee = t.green_fee
                row.slots_open = t.slots_open
                row.raw_url = t.raw_url
                row.last_seen_at = now

        # 4) 더 이상 안 보이는 기존 open 슬롯은 taken 처리
        for k, row in existing_keys.items():
            if k not in crawled_keys:
                row.status = "taken"

        db.commit()

        # 5) 새로 열린 슬롯에 대해 watch 매칭 + 카톡 발송
        await evaluate_and_notify(db, newly_open_ids)
    finally:
        db.close()


def start_scheduler() -> AsyncIOScheduler:
    global scheduler
    if scheduler is not None:
        return scheduler
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        poll_once,
        "interval",
        seconds=settings.POLL_INTERVAL_SECONDS,
        id="poll_courses",
        max_instances=1,
        coalesce=True,
        next_run_time=datetime.utcnow(),  # 부팅 즉시 1회
    )
    scheduler.start()
    return scheduler


def stop_scheduler() -> None:
    global scheduler
    if scheduler is not None:
        scheduler.shutdown(wait=False)
        scheduler = None
