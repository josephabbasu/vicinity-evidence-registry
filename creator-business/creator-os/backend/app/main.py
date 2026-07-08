from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import Base, SessionLocal, engine
from .routers import analytics, assistant, auth, competitors, content, ideas, library, planner, seo, trends, workflows
from .seed import seed


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    if settings.seed_demo_data:
        with SessionLocal() as db:
            seed(db)
    yield


app = FastAPI(
    title="CreatorOS",
    description="Production system for the Plain Money YouTube business: "
    "idea bank, research/script pipeline with a claim-verification gate, SEO, "
    "trends, competitors, analytics, planner, prompt library, and AI assistant.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for r in (auth, ideas, content, seo, trends, competitors, analytics, planner, assistant, library, workflows):
    app.include_router(r.router)


@app.get("/health")
def health():
    return {"status": "ok", "ai": "configured" if settings.anthropic_api_key else "offline-fallback"}
