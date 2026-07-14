from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.agent.agent import run_agent
from app.database import get_db
from app.schemas import ChatRequest, ChatResponse

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/", response_model=ChatResponse)
def chat(payload: ChatRequest, db: Session = Depends(get_db)):
    history = [m.model_dump() for m in payload.messages]
    reply = run_agent(db, history)
    return ChatResponse(reply=reply)
