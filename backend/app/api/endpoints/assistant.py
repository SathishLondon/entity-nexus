from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from typing import List, Dict, Any

router = APIRouter()

class AskRequest(BaseModel):
    question: str

class AskResponse(BaseModel):
    answer: str
    relevant_modules: List[Dict]
    relevant_fields: List[Dict]
    sample_json: Any = None
    try_it_actions: List[Dict]
    related_questions: List[str]

@router.post("/ask", response_model=AskResponse)
def ask_assistant(request: AskRequest):
    """
    Ask the D&B Reference Data Assistant a question.
    
    Example questions:
    - "Where can I find ownership information?"
    - "What's the difference between DUNS and registration number?"
    - "How do I get financial data?"
    - "Show me all hierarchy-related endpoints"
    """
    from app.services.reference_data_assistant import ReferenceDataAssistant
    from app.services.reference_service import ReferenceService
    
    try:
        reference_service = ReferenceService()
        assistant = ReferenceDataAssistant(reference_service)
        
        response = assistant.ask(request.question)
        
        return AskResponse(**response)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing question: {str(e)}")

@router.get("/suggest-questions")
def get_suggested_questions():
    """
    Get a list of suggested questions to ask the assistant.
    """
    from app.services.reference_data_assistant import ReferenceDataAssistant
    from app.services.reference_service import ReferenceService
    
    try:
        reference_service = ReferenceService()
        assistant = ReferenceDataAssistant(reference_service)
        
        return {
            "questions": assistant.get_suggested_questions()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting suggestions: {str(e)}")

@router.post("/render-example")
def render_example(module_id: str = Body(...), field: str = Body(None)):
    """
    Render an example from actual data.
    Returns sample JSON or specific field value if available.
    """
    from app.services.reference_service import ReferenceService
    
    try:
        reference_service = ReferenceService()
        sample = reference_service.get_sample(module_id)
        
        if not sample:
            raise HTTPException(status_code=404, detail=f"No sample data for {module_id}")
        
        if field:
            # Try to extract specific field
            # Simple dot notation support
            value = sample
            for part in field.split('.'):
                if isinstance(value, dict):
                    value = value.get(part)
                else:
                    value = None
                    break
            
            return {
                "module_id": module_id,
                "field": field,
                "value": value
            }
        else:
            return {
                "module_id": module_id,
                "sample": sample
            }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error rendering example: {str(e)}")
