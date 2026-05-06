from datetime import datetime, date, time
from enum import Enum
from typing import Optional
from sqlalchemy import (
    String, Integer, Boolean, DateTime, Date, Time, ForeignKey, JSON, UniqueConstraint, Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


class Region(str, Enum):
    GG_SOUTH = "GG_SOUTH"           # 경기 남부
    GG_NORTH = "GG_NORTH"           # 경기 북부
    GG_EAST_GW = "GG_EAST_GW"       # 경기 동부 + 강원권
    CHUNGCHEONG = "CHUNGCHEONG"     # 충청권


class Platform(str, Enum):
    XGOLF = "xgolf"
    KGOLF = "kgolf"
    GOLFZON = "golfzon"
    OWN = "own"
    DEMO = "demo"


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    region: Mapped[str] = mapped_column(String(32), index=True)
    platform: Mapped[str] = mapped_column(String(32), index=True)
    platform_course_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    booking_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class TeeTime(Base):
    __tablename__ = "tee_times"
    __table_args__ = (
        UniqueConstraint("course_id", "play_date", "tee_time", "holes", name="uq_tee_slot"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), index=True)
    play_date: Mapped[date] = mapped_column(Date, index=True)
    tee_time: Mapped[time] = mapped_column(Time)
    holes: Mapped[int] = mapped_column(Integer, default=18)
    green_fee: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 원
    slots_open: Mapped[int] = mapped_column(Integer, default=1)            # 1~4
    raw_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="open")        # open / taken
    first_seen_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    course: Mapped[Course] = relationship()


class Watch(Base):
    """사용자가 등록한 알림 조건"""
    __tablename__ = "watches"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    regions: Mapped[list] = mapped_column(JSON, default=list)        # ["GG_SOUTH", ...] 빈배열 = 전체
    course_ids: Mapped[list] = mapped_column(JSON, default=list)     # [1, 5, 7] 빈배열 = 전체
    weekdays: Mapped[list] = mapped_column(JSON, default=list)       # [0..6] (월=0) 빈배열 = 전체
    time_min: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    time_max: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    date_from: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    date_to: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    max_green_fee: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    min_slots: Mapped[int] = mapped_column(Integer, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    watch_id: Mapped[int] = mapped_column(ForeignKey("watches.id"), index=True)
    tee_time_id: Mapped[int] = mapped_column(ForeignKey("tee_times.id"), index=True)
    sent_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    channel: Mapped[str] = mapped_column(String(16), default="kakao")
    success: Mapped[bool] = mapped_column(Boolean, default=False)
    error_msg: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class KakaoToken(Base):
    """싱글유저 OAuth 토큰 (id=1 고정)"""
    __tablename__ = "kakao_tokens"

    id: Mapped[int] = mapped_column(primary_key=True, default=1)
    access_token: Mapped[str] = mapped_column(Text)
    refresh_token: Mapped[str] = mapped_column(Text)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    refresh_expires_at: Mapped[datetime] = mapped_column(DateTime)
    scope: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
