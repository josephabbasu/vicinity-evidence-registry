from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import PIPELINE_STATES, Video
from ..security import get_current_user

router = APIRouter(prefix="/planner", tags=["planner"], dependencies=[Depends(get_current_user)])

# Anchor cadence from the content strategy: Tue & Sat 14:00 UTC
PUBLISH_WEEKDAYS = (1, 5)  # Monday=0
PUBLISH_HOUR_UTC = 14


@router.get("/calendar")
def calendar(db: Session = Depends(get_db)):
    """Scheduled/published videos plus the pipeline buffer status."""
    videos = db.scalars(select(Video)).all()
    scheduled = [
        {
            "id": v.id, "title": v.title, "status": v.status, "format": v.format,
            "scheduled_at": v.scheduled_at.isoformat() if v.scheduled_at else None,
            "published_at": v.published_at.isoformat() if v.published_at else None,
        }
        for v in videos
        if v.scheduled_at or v.published_at
    ]
    in_production = sum(
        1 for v in videos
        if PIPELINE_STATES.index(v.status) < PIPELINE_STATES.index("scheduled")
    )
    buffer_weeks = round(
        sum(1 for v in videos if v.status == "scheduled") / 2, 1
    )  # 2 long-form/week cadence
    return {
        "scheduled": sorted(scheduled, key=lambda x: x["scheduled_at"] or x["published_at"] or ""),
        "in_production": in_production,
        "buffer_weeks": buffer_weeks,
        "buffer_target_weeks": 3,
        "buffer_ok": buffer_weeks >= 3,
    }


@router.get("/next-slots")
def next_slots(count: int = 6):
    """The next publish slots on the Tue/Sat 14:00 UTC cadence."""
    now = datetime.now(timezone.utc)
    slots = []
    day = now
    while len(slots) < count:
        day = day + timedelta(days=1)
        if day.weekday() in PUBLISH_WEEKDAYS:
            slots.append(day.replace(hour=PUBLISH_HOUR_UTC, minute=0, second=0, microsecond=0).isoformat())
    return {"slots": slots}
