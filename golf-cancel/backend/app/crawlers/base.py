from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date, time
from typing import Optional


@dataclass
class CrawledTeeTime:
    course_id: int
    play_date: date
    tee_time: time
    holes: int = 18
    green_fee: Optional[int] = None
    slots_open: int = 1
    raw_url: Optional[str] = None


@dataclass
class CrawlerContext:
    course_id: int
    course_name: str
    platform_course_id: Optional[str] = None
    booking_url: Optional[str] = None
    extra: dict = field(default_factory=dict)


class BaseCrawler(ABC):
    """Each platform implements one of these."""

    name: str = ""

    @abstractmethod
    async def fetch(self, ctx: CrawlerContext) -> list[CrawledTeeTime]:
        """Return current open tee times for the given course context."""
        ...
