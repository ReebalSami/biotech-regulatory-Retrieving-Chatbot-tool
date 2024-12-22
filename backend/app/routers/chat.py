from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.services.chatgpt_service import ChatGPTService

router = APIRouter(prefix="/chat", tags=["chat"])

class ChatRequest(BaseModel):
    message: str
    context: Optional[List[str]] = []

class ChatResponse(BaseModel):
    response: str

def get_chatgpt_service():
    """Dependency to get ChatGPT service instance"""
    return ChatGPTService()

@router.post("/", response_model=ChatResponse, name="chat_endpoint")
async def chat(
    request: ChatRequest,
    chatgpt_service: ChatGPTService = Depends(get_chatgpt_service)
) -> ChatResponse:
    """
    Chat endpoint to interact with the AI assistant.
    
    Args:
        request: ChatRequest containing the user's message and optional context
        chatgpt_service: Injected ChatGPT service
        
    Returns:
        ChatResponse containing the AI's response
        
    Raises:
        HTTPException: If the message is empty or if there's an error generating the response
    """
    if not request.message:
        raise HTTPException(
            status_code=400,
            detail="Message cannot be empty"
        )
    
    try:
        response = await chatgpt_service.generate_response(
            user_message=request.message,
            context=request.context or []
        )
        return ChatResponse(response=response)
        
    except Exception as e:
        # Convert all exceptions to HTTPException
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=500,
            detail=f"Error processing chat request: {str(e)}"
        )
