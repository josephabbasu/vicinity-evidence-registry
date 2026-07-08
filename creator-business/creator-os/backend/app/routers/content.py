from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import PIPELINE_STATES, Claim, Idea, Video
from ..schemas import ClaimIn, ClaimOut, ClaimUpdate, VideoIn, VideoOut, VideoUpdate
from ..security import get_current_user
from ..services import ai

router = APIRouter(prefix="/videos", tags=["content"], dependencies=[Depends(get_current_user)])


def _get_video(db: Session, video_id: int) -> Video:
    video = db.get(Video, video_id)
    if video is None:
        raise HTTPException(status_code=404, detail="Video not found")
    return video


@router.get("", response_model=list[VideoOut])
def list_videos(status: str | None = None, db: Session = Depends(get_db)):
    q = select(Video).order_by(Video.created_at.desc())
    if status:
        q = q.where(Video.status == status)
    return db.scalars(q).all()


@router.post("", response_model=VideoOut, status_code=201)
def create_video(body: VideoIn, db: Session = Depends(get_db)):
    video = Video(**body.model_dump())
    if body.idea_id:
        idea = db.get(Idea, body.idea_id)
        if idea:
            idea.status = "selected"
            if not video.pillar:
                video.pillar = idea.pillar
    db.add(video)
    db.commit()
    db.refresh(video)
    return video


@router.get("/{video_id}", response_model=VideoOut)
def get_video(video_id: int, db: Session = Depends(get_db)):
    return _get_video(db, video_id)


@router.patch("/{video_id}", response_model=VideoOut)
def update_video(video_id: int, body: VideoUpdate, db: Session = Depends(get_db)):
    video = _get_video(db, video_id)
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(video, k, v)
    db.commit()
    db.refresh(video)
    return video


@router.delete("/{video_id}", status_code=204)
def delete_video(video_id: int, db: Session = Depends(get_db)):
    video = _get_video(db, video_id)
    db.delete(video)
    db.commit()


# ---- pipeline state machine ----

@router.post("/{video_id}/advance", response_model=VideoOut)
def advance(video_id: int, db: Session = Depends(get_db)):
    """Move one step forward in the pipeline, enforcing the fact-check gate."""
    video = _get_video(db, video_id)
    idx = PIPELINE_STATES.index(video.status)
    if idx == len(PIPELINE_STATES) - 1:
        raise HTTPException(status_code=400, detail="Already at the final state")
    target = PIPELINE_STATES[idx + 1]

    # Trust gate: nothing moves past fact_checked with unverified claims,
    # and reaching fact_checked requires at least one claim to exist.
    if target == "fact_checked" and not video.claims:
        raise HTTPException(
            status_code=409,
            detail="Cannot mark fact_checked: no claims recorded. Extract [CLAIM] lines first.",
        )
    if PIPELINE_STATES.index(target) >= PIPELINE_STATES.index("voiced"):
        unverified = [c for c in video.claims if c.status == "unverified"]
        if unverified:
            raise HTTPException(
                status_code=409,
                detail=f"Blocked by the verification gate: {len(unverified)} unverified claim(s).",
            )
    if target == "scheduled" and video.scheduled_at is None:
        raise HTTPException(status_code=409, detail="Set scheduled_at before scheduling.")
    if target == "published":
        video.published_at = datetime.now(timezone.utc)

    video.status = target
    db.commit()
    db.refresh(video)
    return video


# ---- AI pipeline steps ----

@router.post("/{video_id}/research", response_model=dict)
def run_research(video_id: int, db: Session = Depends(get_db)):
    video = _get_video(db, video_id)
    brief, mode = ai.generate_research_brief(video.title, video.pillar)
    video.research_brief = brief
    db.commit()
    return {"mode": mode, "research_brief": brief}


@router.post("/{video_id}/script", response_model=dict)
def run_script(video_id: int, db: Session = Depends(get_db)):
    video = _get_video(db, video_id)
    if not video.research_brief:
        raise HTTPException(status_code=409, detail="Run research before scripting.")
    script, mode = ai.generate_script(video.title, video.pillar, video.research_brief)
    video.script = script
    db.commit()
    return {"mode": mode, "script": script}


@router.post("/{video_id}/factcheck", response_model=dict)
def run_factcheck(video_id: int, db: Session = Depends(get_db)):
    """Adversarial review pass + auto-extract [CLAIM] lines into the claims table."""
    video = _get_video(db, video_id)
    if not video.script:
        raise HTTPException(status_code=409, detail="No script to fact-check.")
    review, mode = ai.adversarial_fact_check(video.script)
    existing = {c.text for c in video.claims}
    added = 0
    for line in video.script.splitlines():
        if "[CLAIM]" in line:
            text = line.replace("[CLAIM]", "").replace("VO:", "").strip(" -#*")
            if text and text not in existing:
                db.add(Claim(video_id=video.id, text=text))
                existing.add(text)
                added += 1
    db.commit()
    return {"mode": mode, "review": review, "claims_extracted": added}


# ---- claims ----

@router.post("/{video_id}/claims", response_model=ClaimOut, status_code=201)
def add_claim(video_id: int, body: ClaimIn, db: Session = Depends(get_db)):
    _get_video(db, video_id)
    claim = Claim(video_id=video_id, **body.model_dump())
    db.add(claim)
    db.commit()
    db.refresh(claim)
    return claim


@router.patch("/{video_id}/claims/{claim_id}", response_model=ClaimOut)
def update_claim(video_id: int, claim_id: int, body: ClaimUpdate, db: Session = Depends(get_db)):
    claim = db.get(Claim, claim_id)
    if claim is None or claim.video_id != video_id:
        raise HTTPException(status_code=404, detail="Claim not found")
    data = body.model_dump(exclude_unset=True)
    if "status" in data:
        if data["status"] not in ("unverified", "verified", "corrected", "cut"):
            raise HTTPException(status_code=422, detail="Invalid claim status")
        if data["status"] in ("verified", "corrected") and not (
            data.get("source_url") or claim.source_url
        ):
            raise HTTPException(status_code=409, detail="A source URL is required to verify a claim.")
    for k, v in data.items():
        setattr(claim, k, v)
    db.commit()
    db.refresh(claim)
    return claim
