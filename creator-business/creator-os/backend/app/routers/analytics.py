from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Idea, Task, Video, VideoMetric
from ..schemas import MetricIn
from ..security import get_current_user

router = APIRouter(prefix="/analytics", tags=["analytics"], dependencies=[Depends(get_current_user)])


@router.post("/metrics", status_code=201)
def add_metric(body: MetricIn, db: Session = Depends(get_db)):
    if db.get(Video, body.video_id) is None:
        raise HTTPException(status_code=404, detail="Video not found")
    data = body.model_dump()
    data["date"] = data["date"] or datetime.now(timezone.utc)
    db.add(VideoMetric(**data))
    db.commit()
    return {"ok": True}


@router.get("/videos/{video_id}")
def video_metrics(video_id: int, db: Session = Depends(get_db)):
    video = db.get(Video, video_id)
    if video is None:
        raise HTTPException(status_code=404, detail="Video not found")
    metrics = sorted(video.metrics, key=lambda m: m.date)
    return {
        "video_id": video_id,
        "title": video.title,
        "metrics": [
            {
                "date": m.date.isoformat(),
                "views": m.views,
                "ctr": m.ctr,
                "avg_percentage_viewed": m.avg_percentage_viewed,
                "watch_hours": m.watch_hours,
                "subscribers_gained": m.subscribers_gained,
                "revenue": m.revenue,
            }
            for m in metrics
        ],
    }


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db)):
    """Channel-level KPI rollup + pipeline health for the dashboard page."""
    totals = db.execute(
        select(
            func.coalesce(func.sum(VideoMetric.views), 0),
            func.coalesce(func.sum(VideoMetric.watch_hours), 0.0),
            func.coalesce(func.sum(VideoMetric.subscribers_gained), 0),
            func.coalesce(func.sum(VideoMetric.revenue), 0.0),
            func.coalesce(func.avg(VideoMetric.ctr), 0.0),
            func.coalesce(func.avg(VideoMetric.avg_percentage_viewed), 0.0),
        )
    ).one()

    pipeline = {
        status: count
        for status, count in db.execute(
            select(Video.status, func.count(Video.id)).group_by(Video.status)
        ).all()
    }

    # KPI health thresholds from the strategy's KPI table
    avg_ctr = round(totals[4], 2)
    avg_viewed = round(totals[5], 2)
    health = {
        "ctr": "healthy" if 4 <= avg_ctr <= 8 else ("low" if avg_ctr < 4 else "check thumbnails vs promise"),
        "retention": "healthy" if avg_viewed >= 50 else "below 50% target",
    }

    top = db.execute(
        select(Video.id, Video.title, func.sum(VideoMetric.views).label("v"))
        .join(VideoMetric, VideoMetric.video_id == Video.id)
        .group_by(Video.id)
        .order_by(func.sum(VideoMetric.views).desc())
        .limit(5)
    ).all()

    return {
        "totals": {
            "views": int(totals[0]),
            "watch_hours": round(totals[1], 1),
            "subscribers_gained": int(totals[2]),
            "revenue": round(totals[3], 2),
            "avg_ctr": avg_ctr,
            "avg_percentage_viewed": avg_viewed,
        },
        "health": health,
        "pipeline": pipeline,
        "top_videos": [{"id": t[0], "title": t[1], "views": int(t[2])} for t in top],
        "idea_backlog": db.scalar(select(func.count(Idea.id)).where(Idea.status == "backlog")) or 0,
        "open_tasks": db.scalar(select(func.count(Task.id)).where(Task.done.is_(False))) or 0,
    }
