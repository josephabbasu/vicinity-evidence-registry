from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Idea, User
from ..schemas import IdeaGenIn, IdeaIn, IdeaOut
from ..security import get_current_user
from ..services import ai

router = APIRouter(prefix="/ideas", tags=["ideas"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=list[IdeaOut])
def list_ideas(status: str | None = None, pillar: str | None = None, db: Session = Depends(get_db)):
    q = select(Idea)
    if status:
        q = q.where(Idea.status == status)
    if pillar:
        q = q.where(Idea.pillar == pillar)
    ideas = db.scalars(q).all()
    return sorted(ideas, key=lambda i: i.score, reverse=True)


@router.post("", response_model=IdeaOut, status_code=201)
def create_idea(body: IdeaIn, db: Session = Depends(get_db)):
    idea = Idea(**body.model_dump())
    db.add(idea)
    db.commit()
    db.refresh(idea)
    return idea


@router.patch("/{idea_id}", response_model=IdeaOut)
def update_idea(idea_id: int, body: dict, db: Session = Depends(get_db)):
    idea = db.get(Idea, idea_id)
    if idea is None:
        raise HTTPException(status_code=404, detail="Idea not found")
    allowed = {"title", "pillar", "format", "notes", "demand", "evergreen",
               "competition_gap", "monetization", "production_ease", "status"}
    for k, v in body.items():
        if k in allowed:
            setattr(idea, k, v)
    db.commit()
    db.refresh(idea)
    return idea


@router.delete("/{idea_id}", status_code=204)
def delete_idea(idea_id: int, db: Session = Depends(get_db)):
    idea = db.get(Idea, idea_id)
    if idea is None:
        raise HTTPException(status_code=404, detail="Idea not found")
    db.delete(idea)
    db.commit()


@router.post("/generate", response_model=dict)
def generate(body: IdeaGenIn, db: Session = Depends(get_db)):
    """AI idea generator: proposes ideas and stores them in the backlog."""
    proposals, mode = ai.generate_ideas(body.pillar, body.topic_hint, body.count)
    created = []
    for p in proposals:
        idea = Idea(title=p["title"], notes=p.get("notes", ""), pillar=body.pillar)
        db.add(idea)
        created.append(idea)
    db.commit()
    return {"mode": mode, "created": [{"id": i.id, "title": i.title} for i in created]}
