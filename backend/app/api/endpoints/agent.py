from fastapi import APIRouter, Depends, HTTPException, Body
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

# ========== Phase 0: Basic AI Agent Endpoints ==========

@router.post("/parse-query")
def parse_query(query: str = Body(..., embed=True)):
    """
    Parse natural language query and extract intent.
    Returns prefill data for search form.
    
    Example queries:
    - "Show me the hierarchy for Apple Inc"
    - "Legal structure for DUNS 123456789"
    - "Ownership of Microsoft Corporation"
    """
    from app.services.basic_agent_service import BasicAgentService
    
    try:
        agent = BasicAgentService()
        intent = agent.parse_query(query)
        return intent.dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error parsing query: {str(e)}")

@router.get("/status")
def get_agent_status():
    """
    Check if Ollama is available and which models are installed.
    """
    from app.services.basic_agent_service import BasicAgentService
    
    try:
        agent = BasicAgentService()
        return agent.check_ollama_status()
    except Exception as e:
        return {
            'available': False,
            'reason': str(e),
            'models': []
        }
