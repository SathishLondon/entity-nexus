from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.agent_service import AgentService
from app.core.config import settings

router = APIRouter()

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

@router.post("/chat", response_model=ChatResponse)
def chat_with_agent(request: ChatRequest, db: Session = Depends(get_db)):
    """
    Chat with the Entity Nexus Agent. 
    The agent has access to tools to search entities and view lineage.
    """
    # In a real app, we'd handle session/history here.
    # For now, it's a stateless single-turn chat.
    
    if not settings.OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OpenAI API Key not configured.")
        
    try:
        service = AgentService(db, settings.OPENAI_API_KEY)
        response_text = service.chat(request.message)
        return ChatResponse(response=response_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
