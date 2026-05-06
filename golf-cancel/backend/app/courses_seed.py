"""
초기 골프장 시드 데이터 (4개 권역).

더블이글(dbegl.com) 기준 국내 다수 골프장 중 다음 4개 권역만 포함:
  - 경기 남부 / 경기 북부 / 경기 동부+강원권 / 충청권

주의: platform_course_id 와 booking_url 은 자리표시자입니다.
실제 크롤링을 켜기 전에:
  1) 각 골프장이 실제로 사용하는 플랫폼(xgolf/kgolf/golfzon/own) 확인
  2) 플랫폼 사이트에서 해당 골프장의 내부 ID 확인 후 platform_course_id 채우기
  3) 모바일에서 자동 로그인되는 booking_url 입력
모르는 항목은 비워두면 됩니다 (데모 모드에서는 영향 없음).
"""
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session

from .models import Course, Region, Platform


# (이름, 권역, 플랫폼, platform_course_id, booking_url)
SEED: List[Tuple[str, Region, Platform, Optional[str], Optional[str]]] = [
    # ----- 경기 남부 -----
    ("포레스트힐CC", Region.GG_SOUTH, Platform.XGOLF, "809", "https://www.xgolf.com/booking/booking_calendar.asp?club_code=809"),
    ("안성베네스트GC", Region.GG_SOUTH, Platform.OWN, None, None),
    ("88CC", Region.GG_SOUTH, Platform.OWN, None, None),
    ("레이크사이드CC", Region.GG_SOUTH, Platform.OWN, None, None),
    ("이천중앙CC", Region.GG_SOUTH, Platform.XGOLF, None, None),
    ("페럼클럽", Region.GG_SOUTH, Platform.OWN, None, None),
    ("솔모로CC", Region.GG_SOUTH, Platform.XGOLF, None, None),
    ("양지파인CC", Region.GG_SOUTH, Platform.OWN, None, None),
    ("안성Q", Region.GG_SOUTH, Platform.XGOLF, None, None),
    ("캐슬렉스서울", Region.GG_SOUTH, Platform.OWN, None, None),
    ("글렌로스GC", Region.GG_SOUTH, Platform.XGOLF, None, None),
    ("발리오스CC", Region.GG_SOUTH, Platform.XGOLF, None, None),
    ("서서울CC", Region.GG_SOUTH, Platform.OWN, None, None),
    ("프라자CC", Region.GG_SOUTH, Platform.OWN, None, None),
    ("레인보우힐스CC", Region.GG_SOUTH, Platform.XGOLF, None, None),

    # ----- 경기 북부 -----
    ("베어크리크포천GC", Region.GG_NORTH, Platform.OWN, None, None),
    ("서원밸리CC", Region.GG_NORTH, Platform.OWN, None, None),
    ("한원CC", Region.GG_NORTH, Platform.XGOLF, None, None),
    ("일동레이크GC", Region.GG_NORTH, Platform.OWN, None, None),
    ("청평마이다스GC", Region.GG_NORTH, Platform.XGOLF, None, None),
    ("가평베네스트GC", Region.GG_NORTH, Platform.OWN, None, None),
    ("코스카CC", Region.GG_NORTH, Platform.XGOLF, None, None),
    ("더플레이어스CC", Region.GG_NORTH, Platform.XGOLF, None, None),

    # ----- 경기 동부 + 강원권 -----
    ("라데나CC", Region.GG_EAST_GW, Platform.OWN, None, None),
    ("비발디파크CC", Region.GG_EAST_GW, Platform.OWN, None, None),
    ("오크밸리CC", Region.GG_EAST_GW, Platform.OWN, None, None),
    ("휘슬링락CC", Region.GG_EAST_GW, Platform.OWN, None, None),
    ("여주CC", Region.GG_EAST_GW, Platform.XGOLF, None, None),
    ("곤지암CC", Region.GG_EAST_GW, Platform.OWN, None, None),
    ("신원CC", Region.GG_EAST_GW, Platform.XGOLF, None, None),
    ("이포CC", Region.GG_EAST_GW, Platform.XGOLF, None, None),
    ("자유CC", Region.GG_EAST_GW, Platform.XGOLF, None, None),
    ("양평TPC", Region.GG_EAST_GW, Platform.OWN, None, None),
    ("휘닉스평창CC", Region.GG_EAST_GW, Platform.OWN, None, None),
    ("강촌CC", Region.GG_EAST_GW, Platform.XGOLF, None, None),

    # ----- 충청권 -----
    ("사이프러스CC", Region.CHUNGCHEONG, Platform.OWN, None, None),
    ("골든베이CC", Region.CHUNGCHEONG, Platform.OWN, None, None),
    ("솔라고CC", Region.CHUNGCHEONG, Platform.XGOLF, None, None),
    ("스카이밸리CC", Region.CHUNGCHEONG, Platform.OWN, None, None),
    ("청주CC", Region.CHUNGCHEONG, Platform.XGOLF, None, None),
    ("천안상록CC", Region.CHUNGCHEONG, Platform.OWN, None, None),
    ("화산CC", Region.CHUNGCHEONG, Platform.XGOLF, None, None),
    ("캐슬파인즈", Region.CHUNGCHEONG, Platform.OWN, None, None),
    ("리베라CC", Region.CHUNGCHEONG, Platform.OWN, None, None),
]


def seed_if_empty(db: Session) -> int:
    """courses 테이블이 비어 있을 때만 시드 데이터 삽입. 삽입한 행 수를 반환."""
    if db.query(Course).first() is not None:
        return 0
    inserted = 0
    for name, region, platform, pcid, url in SEED:
        db.add(Course(
            name=name,
            region=region.value,
            platform=platform.value,
            platform_course_id=pcid,
            booking_url=url,
            is_active=True,
        ))
        inserted += 1
    db.commit()
    return inserted


def upsert_courses(db: Session) -> int:
    """이미 채워진 DB 에 누락된 시드 코스를 추가. 기존 행은 건드리지 않음.

    SEED 항목 중 platform_course_id 가 채워진 새 항목이 추가되었을 때 자동
    반영되도록 매 부팅마다 호출합니다.
    """
    inserted = 0
    for name, region, platform, pcid, url in SEED:
        existing = db.query(Course).filter(Course.name == name).first()
        if existing is None:
            db.add(Course(
                name=name,
                region=region.value,
                platform=platform.value,
                platform_course_id=pcid,
                booking_url=url,
                is_active=True,
            ))
            inserted += 1
    if inserted:
        db.commit()
    return inserted
