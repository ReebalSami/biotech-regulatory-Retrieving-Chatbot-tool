from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from pydantic import BaseModel
from app.services.chatgpt_service import ChatGPTService
from app.document_storage import DocumentStorage

router = APIRouter(prefix="/chat", tags=["chat"])

class ChatMessage(BaseModel):
    content: str
    context: Optional[List[str]] = None

class ChatResponse(BaseModel):
    response: str
    sources: Optional[List[dict]] = None

@router.post("/", response_model=ChatResponse)
async def chat(
    message: ChatMessage,
    chatgpt_service: ChatGPTService = Depends(ChatGPTService),
    document_storage: DocumentStorage = Depends(lambda: DocumentStorage())
):
    """
    Process a chat message using GPT-4 and return a response with relevant sources.
    """
    try:
        # Search for relevant documents if context is not provided
        if not message.context:
            try:
                results = await document_storage.search_documents(message.content, n_results=3)
                context_docs = [doc.content for doc, _ in results]
            except Exception as e:
                print(f"Error searching documents: {str(e)}")
                context_docs = []

        else:
            context_docs = message.context

        # Generate response using GPT-4
        try:
            response = await chatgpt_service.generate_response(
                user_message=message.content,
                context=context_docs
            )
        except HTTPException as e:
            # Re-raise HTTP exceptions (like missing API key) as is
            raise e
        except Exception as e:
            print(f"Error generating response: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Failed to generate response. Please check the server logs for more details."
            )

        return ChatResponse(
            response=response,
            sources=[{"content": doc[:200] + "..."} for doc in context_docs] if context_docs else None
        )

    except HTTPException as e:
        # Re-raise HTTP exceptions with their original status code and detail
        raise e
    except Exception as e:
        print(f"Unexpected error in chat endpoint: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred. Please check the server logs for more details."
        )
