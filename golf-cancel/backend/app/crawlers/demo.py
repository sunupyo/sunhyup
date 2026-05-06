"""
Demo crawler — produces randomized fake tee times for the next 14 days.
Use this to validate the full pipeline (DB → diff → Kakao alert) before
real platform crawlers are hooked up.

Toggle via ENABLE_DEMO_CRAWLER in .env.
"""
import random
from datetime import date, time, timedelta

from .base import BaseCrawler, CrawledTeeTime, CrawlerContext


# Hours that golf courses commonly open tee times.
HOURS = [6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
MINUTES = [0, 7, 14, 21, 28, 35, 42, 49, 56]


class DemoCrawler(BaseCrawler):
    name = "demo"

    async def fetch(self, ctx: CrawlerContext) -> list[CrawledTeeTime]:
        results: list[CrawledTeeTime] = []
        today = date.today()

        # Each call randomly produces 0~3 fake openings to simulate the
        # appearance/disappearance of cancellation slots.
        n = random.choices([0, 1, 2, 3], weights=[60, 25, 10, 5])[0]
        for _ in range(n):
            d = today + timedelta(days=random.randint(1, 14))
            h = random.choice(HOURS)
            m = random.choice(MINUTES)
            results.append(
                CrawledTeeTime(
                    course_id=ctx.course_id,
                    play_date=d,
                    tee_time=time(hour=h, minute=m),
                    holes=18,
                    green_fee=random.choice([180000, 220000, 250000, 280000, 320000]),
                    slots_open=random.choice([1, 2, 3, 4]),
                    raw_url=ctx.booking_url,
                )
            )
        return results
