from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from app.services.chatgpt_service import ChatGPTService
from app.document_storage import DocumentStorage
from app.text_extraction import extract_text_from_file

router = APIRouter(prefix="/chat", tags=["chat"])

class ChatRequest(BaseModel):
    message: str
    context: Optional[List[str]] = []
    attachment_ids: Optional[List[str]] = []

class ChatResponse(BaseModel):
    response: str
    processed_attachments: Optional[List[str]] = []

def get_chatgpt_service():
    """Dependency to get ChatGPT service instance"""
    return ChatGPTService()

def get_document_storage():
    """Dependency to get document storage instance"""
    return DocumentStorage()

@router.post("/upload", response_model=List[str])
async def upload_attachments(
    files: List[UploadFile] = File(...),
    document_storage: DocumentStorage = Depends(get_document_storage)
) -> List[str]:
    """
    Upload attachments for chat context
    
    Args:
        files: List of files to upload
        document_storage: Document storage service
        
    Returns:
        List of attachment IDs
    """
    attachment_ids = []
    
    for file in files:
        try:
            content = await file.read()
            doc_id = await document_storage.store_document_content(
                filename=file.filename,
                content=content,
                metadata={"source": "chat_attachment"}
            )
            attachment_ids.append(doc_id)
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Error processing file {file.filename}: {str(e)}"
            )
            
    return attachment_ids

@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    chatgpt_service: ChatGPTService = Depends(get_chatgpt_service),
    document_storage: DocumentStorage = Depends(get_document_storage)
) -> ChatResponse:
    """
    Chat endpoint to interact with the AI assistant.
    
    Args:
        request: ChatRequest containing the user's message and optional context
        chatgpt_service: Injected ChatGPT service
        document_storage: Document storage service
        
    Returns:
        ChatResponse containing the AI's response
        
    Raises:
        HTTPException: If the message is empty or if there's an error generating the response
    """
    if not request.message and not request.attachment_ids:
        raise HTTPException(
            status_code=400,
            detail="Either message or attachment must be provided"
        )
    
    try:
        # Process attachments if any
        attachment_context = []
        processed_attachments = []
        
        if request.attachment_ids:
            for doc_id in request.attachment_ids:
                try:
                    doc = await document_storage.get_document(doc_id)
                    if doc:
                        content = await document_storage.get_document_content(doc_id)
                        text = await extract_text_from_file(content, doc.filename)
                        attachment_context.append(
                            f"Document: {doc.filename}\n"
                            f"Content:\n{text}\n"
                            f"Please analyze this document's content, focusing on regulatory requirements, "
                            f"compliance guidelines, and key action items."
                        )
                        processed_attachments.append(doc.filename)
                except Exception as e:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Error processing attachment {doc_id}: {str(e)}"
                    )
        
        # Combine original context with attachment context
        full_context = request.context + attachment_context
        
        # If no message is provided but we have attachments, create a default message
        user_message = request.message
        if not user_message and attachment_context:
            user_message = "Please analyze the content of the attached document."
        
        response = await chatgpt_service.generate_response(
            user_message=user_message,
            context=full_context
        )
        
        return ChatResponse(
            response=response,
            processed_attachments=processed_attachments
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating response: {str(e)}"
        )
