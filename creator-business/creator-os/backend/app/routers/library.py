"""Prompt library, knowledge base, and task manager — small CRUD surfaces."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import KnowledgeArticle, Prompt, Task
from ..schemas import ArticleIn, ArticleOut, PromptIn, PromptOut, TaskIn, TaskOut
from ..security import get_current_user

router = APIRouter(tags=["library"], dependencies=[Depends(get_current_user)])


# ---- prompt library ----

@router.get("/prompts", response_model=list[PromptOut])
def list_prompts(db: Session = Depends(get_db)):
    return db.scalars(select(Prompt).order_by(Prompt.name)).all()


@router.post("/prompts", response_model=PromptOut, status_code=201)
def create_prompt(body: PromptIn, db: Session = Depends(get_db)):
    if db.scalar(select(Prompt).where(Prompt.name == body.name)):
        raise HTTPException(status_code=409, detail="Prompt name already exists")
    p = Prompt(**body.model_dump())
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


@router.patch("/prompts/{prompt_id}", response_model=PromptOut)
def update_prompt(prompt_id: int, body: PromptIn, db: Session = Depends(get_db)):
    p = db.get(Prompt, prompt_id)
    if p is None:
        raise HTTPException(status_code=404, detail="Prompt not found")
    p.name, p.purpose, p.body = body.name, body.purpose, body.body
    p.version += 1  # prompts are versioned so output quality drift is traceable
    db.commit()
    db.refresh(p)
    return p


# ---- knowledge base ----

@router.get("/knowledge", response_model=list[ArticleOut])
def list_articles(category: str | None = None, db: Session = Depends(get_db)):
    q = select(KnowledgeArticle).order_by(KnowledgeArticle.category, KnowledgeArticle.title)
    if category:
        q = q.where(KnowledgeArticle.category == category)
    return db.scalars(q).all()


@router.post("/knowledge", response_model=ArticleOut, status_code=201)
def create_article(body: ArticleIn, db: Session = Depends(get_db)):
    a = KnowledgeArticle(**body.model_dump())
    db.add(a)
    db.commit()
    db.refresh(a)
    return a


@router.patch("/knowledge/{article_id}", response_model=ArticleOut)
def update_article(article_id: int, body: ArticleIn, db: Session = Depends(get_db)):
    a = db.get(KnowledgeArticle, article_id)
    if a is None:
        raise HTTPException(status_code=404, detail="Article not found")
    a.title, a.category, a.body = body.title, body.category, body.body
    db.commit()
    db.refresh(a)
    return a


# ---- task manager ----

@router.get("/tasks", response_model=list[TaskOut])
def list_tasks(done: bool | None = None, db: Session = Depends(get_db)):
    q = select(Task).order_by(Task.done, Task.due_at)
    if done is not None:
        q = q.where(Task.done.is_(done))
    return db.scalars(q).all()


@router.post("/tasks", response_model=TaskOut, status_code=201)
def create_task(body: TaskIn, db: Session = Depends(get_db)):
    t = Task(**body.model_dump())
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


@router.patch("/tasks/{task_id}", response_model=TaskOut)
def toggle_task(task_id: int, body: dict, db: Session = Depends(get_db)):
    t = db.get(Task, task_id)
    if t is None:
        raise HTTPException(status_code=404, detail="Task not found")
    if "done" in body:
        t.done = bool(body["done"])
    if "title" in body:
        t.title = body["title"]
    if "detail" in body:
        t.detail = body["detail"]
    db.commit()
    db.refresh(t)
    return t


@router.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    t = db.get(Task, task_id)
    if t is None:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(t)
    db.commit()
