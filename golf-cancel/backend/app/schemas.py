from datetime import date, time, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class CourseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    region: str
    platform: str
    booking_url: Optional[str] = None
    is_active: bool


class TeeTimeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    course_id: int
    course_name: str
    region: str
    play_date: date
    tee_time: time
    holes: int
    green_fee: Optional[int]
    slots_open: int
    raw_url: Optional[str]
    status: str
    first_seen_at: datetime


class WatchIn(BaseModel):
    name: str
    regions: list[str] = []
    course_ids: list[int] = []
    weekdays: list[int] = []
    time_min: Optional[time] = None
    time_max: Optional[time] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    max_green_fee: Optional[int] = None
    min_slots: int = 1
    is_active: bool = True


class WatchOut(WatchIn):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    watch_id: int
    tee_time_id: int
    sent_at: datetime
    channel: str
    success: bool
    error_msg: Optional[str]


class KakaoStatus(BaseModel):
    connected: bool
    expires_at: Optional[datetime] = None
