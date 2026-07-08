from fastapi import APIRouter, Depends

from ..config import settings
from ..schemas import ChatIn, ChatOut
from ..security import get_current_user
from ..services import ai

router = APIRouter(prefix="/assistant", tags=["assistant"], dependencies=[Depends(get_current_user)])


@router.post("/chat", response_model=ChatOut)
def chat(body: ChatIn):
    reply, mode = ai.chat(body.message, body.history)
    return ChatOut(reply=reply, model=settings.anthropic_model if mode == "claude" else "offline-fallback")
