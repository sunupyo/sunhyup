from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from ..config import settings
from ..db import get_db
from ..kakao import authorize_url, exchange_code, save_token, send_self_message
from ..models import KakaoToken
from ..schemas import KakaoStatus

router = APIRouter(prefix="/api/kakao", tags=["kakao"])


@router.get("/login")
def login():
    if not settings.KAKAO_REST_API_KEY:
        raise HTTPException(500, "KAKAO_REST_API_KEY not configured")
    return RedirectResponse(authorize_url())


@router.get("/callback")
async def callback(code: Optional[str] = None, error: Optional[str] = None, db: Session = Depends(get_db)):
    if error:
        return RedirectResponse(f"{settings.FRONTEND_BASE_URL}/settings?kakao=error&msg={error}")
    if not code:
        raise HTTPException(400, "missing code")
    try:
        token_resp = await exchange_code(code)
        save_token(db, token_resp)
    except Exception as e:
        return RedirectResponse(f"{settings.FRONTEND_BASE_URL}/settings?kakao=error&msg={str(e)[:120]}")
    return RedirectResponse(f"{settings.FRONTEND_BASE_URL}/settings?kakao=ok")


@router.get("/status", response_model=KakaoStatus)
def status(db: Session = Depends(get_db)):
    tok = db.get(KakaoToken, 1)
    if tok is None:
        return KakaoStatus(connected=False)
    return KakaoStatus(connected=True, expires_at=tok.expires_at)


@router.post("/test")
async def send_test(db: Session = Depends(get_db)):
    ok, err = await send_self_message(
        db,
        text="⛳ 골프 취소티 알림 - 테스트 메시지\n연결이 정상 작동합니다.",
        link_url=settings.FRONTEND_BASE_URL,
        button_title="대시보드 열기",
    )
    if not ok:
        raise HTTPException(400, err or "send failed")
    return {"ok": True}


@router.delete("/disconnect")
def disconnect(db: Session = Depends(get_db)):
    tok = db.get(KakaoToken, 1)
    if tok:
        db.delete(tok)
        db.commit()
    return {"ok": True}
