from fastapi import APIRouter, Depends

from ..schemas import SeoScoreIn, SeoScoreOut
from ..security import get_current_user
from ..services import ai
from ..services.seo import score_metadata

router = APIRouter(prefix="/seo", tags=["seo"], dependencies=[Depends(get_current_user)])


@router.post("/score", response_model=SeoScoreOut)
def score(body: SeoScoreIn):
    return score_metadata(body.title, body.description, body.tags)


@router.post("/suggest", response_model=dict)
def suggest(body: SeoScoreIn):
    text, mode = ai.seo_suggestions(body.title, body.description, body.tags)
    return {"mode": mode, "suggestions": text}
