from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import TrendKeyword, TrendPoint
from ..schemas import TrendKeywordIn, TrendOut, TrendPointIn
from ..security import get_current_user
from ..services.trends import analyze_points

router = APIRouter(prefix="/trends", tags=["trends"], dependencies=[Depends(get_current_user)])


def _serialize(kw: TrendKeyword) -> TrendOut:
    points = sorted(kw.points, key=lambda p: p.date)
    analysis = analyze_points([(p.date, p.interest) for p in points])
    return TrendOut(
        id=kw.id,
        keyword=kw.keyword,
        category=kw.category,
        latest=analysis["latest"],
        growth_pct=analysis["growth_pct"],
        momentum=analysis["momentum"],
        points=[{"date": p.date.isoformat(), "interest": p.interest} for p in points],
    )


@router.get("", response_model=list[TrendOut])
def list_trends(db: Session = Depends(get_db)):
    keywords = db.scalars(select(TrendKeyword)).all()
    out = [_serialize(k) for k in keywords]
    return sorted(out, key=lambda t: t.growth_pct, reverse=True)


@router.post("", response_model=TrendOut, status_code=201)
def create_keyword(body: TrendKeywordIn, db: Session = Depends(get_db)):
    if db.scalar(select(TrendKeyword).where(TrendKeyword.keyword == body.keyword)):
        raise HTTPException(status_code=409, detail="Keyword already tracked")
    kw = TrendKeyword(keyword=body.keyword, category=body.category)
    db.add(kw)
    db.commit()
    db.refresh(kw)
    return _serialize(kw)


@router.post("/{keyword_id}/points", response_model=TrendOut, status_code=201)
def add_point(keyword_id: int, body: TrendPointIn, db: Session = Depends(get_db)):
    kw = db.get(TrendKeyword, keyword_id)
    if kw is None:
        raise HTTPException(status_code=404, detail="Keyword not found")
    db.add(TrendPoint(
        keyword_id=keyword_id,
        interest=body.interest,
        date=body.date or datetime.now(timezone.utc),
    ))
    db.commit()
    db.refresh(kw)
    return _serialize(kw)


@router.delete("/{keyword_id}", status_code=204)
def delete_keyword(keyword_id: int, db: Session = Depends(get_db)):
    kw = db.get(TrendKeyword, keyword_id)
    if kw is None:
        raise HTTPException(status_code=404, detail="Keyword not found")
    db.delete(kw)
    db.commit()
