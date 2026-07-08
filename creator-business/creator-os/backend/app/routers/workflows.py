"""Workflow automation: one-call orchestration of the production pipeline."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Claim, Idea, Task, Video
from ..security import get_current_user
from ..services import ai

router = APIRouter(prefix="/workflows", tags=["workflows"], dependencies=[Depends(get_current_user)])


@router.post("/produce/{idea_id}")
def produce_from_idea(idea_id: int, db: Session = Depends(get_db)):
    """Idea -> video record -> research brief -> script draft -> claim extraction,
    plus the human-gate task checklist. One call runs the AI-assisted half of the
    pipeline; humans then verify claims, record VO, and edit."""
    idea = db.get(Idea, idea_id)
    if idea is None:
        raise HTTPException(status_code=404, detail="Idea not found")

    video = Video(title=idea.title, pillar=idea.pillar, format=idea.format, idea_id=idea.id)
    db.add(video)
    idea.status = "selected"
    db.flush()

    brief, brief_mode = ai.generate_research_brief(video.title, video.pillar)
    video.research_brief = brief
    video.status = "researched"

    script, script_mode = ai.generate_script(video.title, video.pillar, brief)
    video.script = script
    video.status = "scripted"

    claims = 0
    seen: set[str] = set()
    for line in script.splitlines():
        if "[CLAIM]" in line:
            text = line.replace("[CLAIM]", "").replace("VO:", "").strip(" -#*")
            if text and text not in seen:
                db.add(Claim(video_id=video.id, text=text))
                seen.add(text)
                claims += 1

    for title in (
        "Approve research brief",
        "Verify every claim (source URL required)",
        "Editor voice pass on script",
        "Record VO",
        "Edit + Shorts cutdowns",
        "Thumbnail variants (check 160x90 legibility)",
        "SEO metadata + schedule",
    ):
        db.add(Task(title=title, video_id=video.id))

    db.commit()
    return {
        "video_id": video.id,
        "status": video.status,
        "modes": {"research": brief_mode, "script": script_mode},
        "claims_extracted": claims,
        "tasks_created": 7,
        "note": "Human gates remain: claims must be verified before the pipeline can advance past fact_checked.",
    }


@router.post("/weekly-ideation")
def weekly_ideation(db: Session = Depends(get_db)):
    """The Monday batch job: top up the idea backlog for any pillar running low."""
    pillars = [
        "Money Foundations", "Debt & Credit", "Saving & Budgeting", "Investing From Zero",
        "Scams & Traps", "Earning & Career", "The Economy Explained", "Money Psychology",
        "Big Life Purchases", "Money Around the World",
    ]
    created = []
    for pillar in pillars:
        backlog = db.scalars(
            select(Idea).where(Idea.pillar == pillar, Idea.status == "backlog")
        ).all()
        if len(backlog) < 3:
            proposals, _mode = ai.generate_ideas(pillar, "", 3 - len(backlog))
            for p in proposals:
                idea = Idea(title=p["title"], notes=p.get("notes", ""), pillar=pillar)
                db.add(idea)
                created.append(p["title"])
    db.commit()
    return {"created": created, "count": len(created)}
