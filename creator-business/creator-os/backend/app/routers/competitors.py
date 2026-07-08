from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Competitor, CompetitorSnapshot
from ..schemas import CompetitorIn, CompetitorOut, SnapshotIn
from ..security import get_current_user

router = APIRouter(prefix="/competitors", tags=["competitors"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=list[dict])
def list_competitors(db: Session = Depends(get_db)):
    out = []
    for c in db.scalars(select(Competitor)).all():
        snaps = sorted(c.snapshots, key=lambda s: s.date)
        latest = snaps[-1] if snaps else None
        growth = None
        if len(snaps) >= 2 and snaps[0].subscribers > 0:
            growth = round((snaps[-1].subscribers - snaps[0].subscribers) / snaps[0].subscribers * 100, 1)
        out.append({
            "id": c.id,
            "name": c.name,
            "channel_url": c.channel_url,
            "niche_overlap": c.niche_overlap,
            "notes": c.notes,
            "subscribers": latest.subscribers if latest else None,
            "total_views": latest.total_views if latest else None,
            "videos": latest.videos if latest else None,
            "growth_pct": growth,
            "snapshots": [
                {"date": s.date.isoformat(), "subscribers": s.subscribers, "total_views": s.total_views}
                for s in snaps
            ],
        })
    return out


@router.post("", response_model=CompetitorOut, status_code=201)
def create_competitor(body: CompetitorIn, db: Session = Depends(get_db)):
    c = Competitor(**body.model_dump())
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


@router.post("/{competitor_id}/snapshots", status_code=201)
def add_snapshot(competitor_id: int, body: SnapshotIn, db: Session = Depends(get_db)):
    c = db.get(Competitor, competitor_id)
    if c is None:
        raise HTTPException(status_code=404, detail="Competitor not found")
    db.add(CompetitorSnapshot(
        competitor_id=competitor_id,
        subscribers=body.subscribers,
        total_views=body.total_views,
        videos=body.videos,
        date=body.date or datetime.now(timezone.utc),
    ))
    db.commit()
    return {"ok": True}


@router.delete("/{competitor_id}", status_code=204)
def delete_competitor(competitor_id: int, db: Session = Depends(get_db)):
    c = db.get(Competitor, competitor_id)
    if c is None:
        raise HTTPException(status_code=404, detail="Competitor not found")
    db.delete(c)
    db.commit()
