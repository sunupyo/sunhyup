from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import courses, teetimes, watches, notifications, kakao_oauth, admin
from .config import settings
from .courses_seed import seed_if_empty, upsert_courses
from .db import Base, SessionLocal, engine
from .scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        n = seed_if_empty(db)
        if n:
            print(f"[seed] inserted {n} courses")
        added = upsert_courses(db)
        if added:
            print(f"[seed] upserted {added} additional courses")
    finally:
        db.close()
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(title="Golf Cancel Notifier", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_BASE_URL, "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(courses.router)
app.include_router(teetimes.router)
app.include_router(watches.router)
app.include_router(notifications.router)
app.include_router(kakao_oauth.router)
app.include_router(admin.router)


@app.get("/api/health")
def health():
    return {"ok": True, "demo": settings.ENABLE_DEMO_CRAWLER}
