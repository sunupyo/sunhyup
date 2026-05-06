"""
XGOLF 크롤러 (실 구현).

엔드포인트는 JSON API 가 아니라 EUC-KR 인코딩된 HTML 페이지를 반환하는
classic ASP 페이지입니다. 잔여 부킹 테이블을 BeautifulSoup 으로 파싱.

요청:
  GET https://www.xgolf.com/booking/booking_normal_list.asp
      ?club_code={CLUB_CODE}
      &book_date=YYYYMMDD
      &agent_code=77
  + Cookie 헤더 (로그인 세션, .env 의 XGOLF_COOKIE)

응답 행 구조 (관심 컬럼만):
  | 부킹일 | 코스(Hill/Rock) | 시간(td.Tee-off) | 1인 적용가(td.price > strong) |
  | 이벤트 아이콘 | 내용(td.subject; "[4인필수] 선결제 1인 186,000원" 식) | 예약 버튼 |

세션 쿠키가 만료되면 같은 URL이 로그인 페이지를 돌려줘서 잔여 테이블이
검색되지 않습니다. 이 경우 fetch 결과는 빈 리스트가 되고, 관리자가 .env 의
XGOLF_COOKIE 를 갱신해야 합니다.
"""
import logging
import re
from datetime import date, time, timedelta
from typing import List, Optional

import httpx
from bs4 import BeautifulSoup

from ..config import settings
from .base import BaseCrawler, CrawledTeeTime, CrawlerContext

logger = logging.getLogger(__name__)

_BASE = "https://www.xgolf.com"
_LIST_PATH = "/booking/booking_normal_list.asp"

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.7",
}

_PERSON_RE = re.compile(r"(\d)\s*인")
_DIGITS_RE = re.compile(r"[\d,]+")


def _persons_from_subject(text: str) -> int:
    """\"[4인필수] 선결제 1인 186,000원\" 같은 문구에서 잔여 인원 추출."""
    if not text:
        return 4
    # 첫 번째 숫자가 부킹 인원 ("1인 적용가" 의 1인은 가격기준이라 무시)
    bracket = re.search(r"\[\s*(\d)\s*인", text)
    if bracket:
        n = int(bracket.group(1))
        return n if 1 <= n <= 4 else 4
    m = _PERSON_RE.search(text)
    if m:
        n = int(m.group(1))
        return n if 1 <= n <= 4 else 4
    return 4


def _price_to_int(text: str) -> Optional[int]:
    if not text:
        return None
    m = _DIGITS_RE.search(text)
    if not m:
        return None
    try:
        return int(m.group(0).replace(",", ""))
    except ValueError:
        return None


def _build_list_url(club_code: str, target: date, agent: str) -> str:
    return (
        f"{_BASE}{_LIST_PATH}"
        f"?club_code={club_code}"
        f"&book_date={target.strftime('%Y%m%d')}"
        f"&agent_code={agent}"
    )


def _parse_html(html: str, ctx: CrawlerContext, target_date: date, list_url: str) -> List[CrawledTeeTime]:
    soup = BeautifulSoup(html, "lxml")

    # 잔여 부킹 테이블 식별: td.Tee-off 가 있는 첫 테이블
    target_table = None
    for t in soup.find_all("table"):
        if t.find("td", class_="Tee-off"):
            target_table = t
            break
    if target_table is None:
        return []

    rows = (target_table.find("tbody") or target_table).find_all("tr")
    out: List[CrawledTeeTime] = []
    for r in rows:
        tee_td = r.find("td", class_="Tee-off")
        if tee_td is None:
            continue
        try:
            hh, mm = tee_td.get_text(strip=True).split(":")
            tt = time(hour=int(hh), minute=int(mm))
        except Exception:
            continue

        price_td = r.find("td", class_="price")
        green_fee = _price_to_int(price_td.get_text(" ", strip=True) if price_td else "")

        subject_td = r.find("td", class_="subject")
        slots = _persons_from_subject(subject_td.get_text(" ", strip=True) if subject_td else "")

        out.append(
            CrawledTeeTime(
                course_id=ctx.course_id,
                play_date=target_date,
                tee_time=tt,
                holes=18,
                green_fee=green_fee,
                slots_open=slots,
                raw_url=list_url,
            )
        )
    return out


class XgolfCrawler(BaseCrawler):
    name = "xgolf"

    def __init__(self, lookahead_days: Optional[int] = None):
        self.lookahead_days = lookahead_days

    def _headers(self, club_code: str) -> dict:
        h = dict(_HEADERS)
        h["Referer"] = f"{_BASE}/booking/booking_calendar.asp?club_code={club_code}"
        if settings.XGOLF_COOKIE:
            h["Cookie"] = settings.XGOLF_COOKIE
        return h

    async def fetch(self, ctx: CrawlerContext) -> List[CrawledTeeTime]:
        if not ctx.platform_course_id:
            return []
        if not settings.XGOLF_COOKIE:
            logger.warning("XGOLF_COOKIE empty; xgolf crawler skipping %s", ctx.course_name)
            return []

        out: List[CrawledTeeTime] = []
        today = date.today()
        days = self.lookahead_days or settings.XGOLF_LOOKAHEAD_DAYS or 21
        agent = settings.XGOLF_AGENT_CODE or "77"
        headers = self._headers(ctx.platform_course_id)

        async with httpx.AsyncClient(timeout=15.0, headers=headers) as client:
            for offset in range(0, days):
                target = today + timedelta(days=offset)
                list_url = _build_list_url(ctx.platform_course_id, target, agent)
                try:
                    r = await client.get(list_url)
                    if r.status_code != 200:
                        continue
                    html = r.content.decode("euc-kr", errors="replace")
                    out.extend(_parse_html(html, ctx, target, list_url))
                except Exception:
                    logger.exception("xgolf fetch failed: %s on %s", ctx.course_name, target)
                    continue
        return out
