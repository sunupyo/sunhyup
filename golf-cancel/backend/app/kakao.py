"""
Kakao OAuth + "나에게 보내기" 메시지 발송.

전제: 본인만 사용. 카카오 디벨로퍼스에서 발급받은 REST API 키 1개로
본인 계정에 OAuth 로그인 → access/refresh 토큰 저장 → 백엔드가 토큰으로
본인 카톡에 메시지 전송. 사업자/심사 불필요.

필수 동의항목 (Kakao 디벨로퍼스 → 카카오 로그인 → 동의항목):
  - "카카오톡 메시지 전송"  scope: talk_message  (필수동의)
"""
import json
from datetime import datetime, timedelta
from typing import Optional

import httpx
from sqlalchemy.orm import Session

from .config import settings
from .models import KakaoToken


_AUTH = "https://kauth.kakao.com"
_API = "https://kapi.kakao.com"


def authorize_url() -> str:
    return (
        f"{_AUTH}/oauth/authorize"
        f"?response_type=code"
        f"&client_id={settings.KAKAO_REST_API_KEY}"
        f"&redirect_uri={settings.KAKAO_REDIRECT_URI}"
        f"&scope=talk_message"
    )


def _token_form(extra: dict) -> dict:
    form = {"client_id": settings.KAKAO_REST_API_KEY, **extra}
    if settings.KAKAO_CLIENT_SECRET:
        form["client_secret"] = settings.KAKAO_CLIENT_SECRET
    return form


async def exchange_code(code: str) -> dict:
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.post(
            f"{_AUTH}/oauth/token",
            data=_token_form({
                "grant_type": "authorization_code",
                "redirect_uri": settings.KAKAO_REDIRECT_URI,
                "code": code,
            }),
        )
        r.raise_for_status()
        return r.json()


async def refresh_token(refresh: str) -> dict:
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.post(
            f"{_AUTH}/oauth/token",
            data=_token_form({
                "grant_type": "refresh_token",
                "refresh_token": refresh,
            }),
        )
        r.raise_for_status()
        return r.json()


def save_token(db: Session, token_resp: dict) -> KakaoToken:
    now = datetime.utcnow()
    expires_at = now + timedelta(seconds=int(token_resp["expires_in"]))
    refresh_expires_at = now + timedelta(seconds=int(token_resp.get("refresh_token_expires_in", 60 * 60 * 24 * 60)))

    existing = db.get(KakaoToken, 1)
    if existing is None:
        existing = KakaoToken(
            id=1,
            access_token=token_resp["access_token"],
            refresh_token=token_resp.get("refresh_token") or "",
            expires_at=expires_at,
            refresh_expires_at=refresh_expires_at,
            scope=token_resp.get("scope"),
            updated_at=now,
        )
        db.add(existing)
    else:
        existing.access_token = token_resp["access_token"]
        # 카카오는 refresh_token 만료 1개월 미만일 때만 새 refresh_token 을 내려줌
        if token_resp.get("refresh_token"):
            existing.refresh_token = token_resp["refresh_token"]
            existing.refresh_expires_at = refresh_expires_at
        existing.expires_at = expires_at
        existing.scope = token_resp.get("scope") or existing.scope
        existing.updated_at = now
    db.commit()
    db.refresh(existing)
    return existing


async def get_valid_access_token(db: Session) -> Optional[str]:
    tok = db.get(KakaoToken, 1)
    if tok is None:
        return None
    if tok.expires_at <= datetime.utcnow() + timedelta(minutes=1):
        # 만료 1분 전이면 갱신
        try:
            new = await refresh_token(tok.refresh_token)
            tok = save_token(db, new)
        except Exception:
            return None
    return tok.access_token


async def send_self_message(
    db: Session,
    text: str,
    link_url: str,
    button_title: str = "예약하러 가기",
) -> tuple[bool, Optional[str]]:
    """카카오톡 '나에게 보내기' 로 텍스트+링크 메시지 전송.

    text 는 카카오 정책상 200자 제한.
    """
    access = await get_valid_access_token(db)
    if not access:
        return False, "kakao_not_connected"

    # text 200자 제한
    if len(text) > 199:
        text = text[:196] + "..."

    template_object = {
        "object_type": "text",
        "text": text,
        "link": {"web_url": link_url, "mobile_web_url": link_url},
        "button_title": button_title,
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.post(
            f"{_API}/v2/api/talk/memo/default/send",
            headers={"Authorization": f"Bearer {access}"},
            data={"template_object": json.dumps(template_object, ensure_ascii=False)},
        )
        if r.status_code == 200 and r.json().get("result_code") == 0:
            return True, None
        return False, f"{r.status_code}:{r.text[:200]}"
