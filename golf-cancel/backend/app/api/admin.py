from fastapi import APIRouter

from ..scheduler import poll_once

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.post("/poll-now")
async def poll_now():
    """수동으로 폴링 1회 실행 (디버그용)."""
    await poll_once()
    return {"ok": True}
