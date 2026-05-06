from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Watch
from ..schemas import WatchIn, WatchOut

router = APIRouter(prefix="/api/watches", tags=["watches"])


@router.get("", response_model=List[WatchOut])
def list_watches(db: Session = Depends(get_db)):
    return db.query(Watch).order_by(Watch.created_at.desc()).all()


@router.post("", response_model=WatchOut)
def create_watch(payload: WatchIn, db: Session = Depends(get_db)):
    w = Watch(**payload.model_dump())
    db.add(w)
    db.commit()
    db.refresh(w)
    return w


@router.put("/{watch_id}", response_model=WatchOut)
def update_watch(watch_id: int, payload: WatchIn, db: Session = Depends(get_db)):
    w = db.get(Watch, watch_id)
    if not w:
        raise HTTPException(404)
    for k, v in payload.model_dump().items():
        setattr(w, k, v)
    db.commit()
    db.refresh(w)
    return w


@router.delete("/{watch_id}")
def delete_watch(watch_id: int, db: Session = Depends(get_db)):
    w = db.get(Watch, watch_id)
    if not w:
        raise HTTPException(404)
    db.delete(w)
    db.commit()
    return {"ok": True}
