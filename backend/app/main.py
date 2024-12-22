from fastapi import FastAPI, File, UploadFile, HTTPException, Query, Form, Body, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel
import json
from pathlib import Path
from app.document_storage import DocumentStorage
from app.utils.document_types import DocumentType, DocumentMetadata
from app.utils.exceptions import DocumentNotFoundError
from app.chatbot import process_query

app = FastAPI(
    title="Biotech Regulatory Document Management API",
    description="""
    This API provides comprehensive document management capabilities for biotech regulatory documents.
    Features include:
    - Document upload and management
    - Semantic search across documents
    - Document versioning
    - Metadata management
    - Regulatory compliance tracking
    """,
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize document storage
doc_storage = DocumentStorage()

async def get_document_storage():
    """Get document storage instance."""
    return doc_storage

class ChatAttachmentResponse(BaseModel):
    document_id: str
    filename: str
    upload_date: datetime

@app.post("/chat/attachments/upload", 
    response_model=ChatAttachmentResponse,
    tags=["Chat"],
    summary="Upload a chat attachment")
async def upload_chat_attachment(
    file: UploadFile,
    chat_id: str = Form(...),
    document_storage: DocumentStorage = Depends(get_document_storage)
):
    """
    Upload a document attachment for chat context.
    The attachment will be available for 24 hours.
    """
    doc_id = await document_storage.store_document(
        file=file,
        document_type=DocumentType.USER_ATTACHMENT,
        chat_id=chat_id
    )
    
    doc_meta = await document_storage.get_document(doc_id)
    return ChatAttachmentResponse(
        document_id=doc_id,
        filename=doc_meta.filename,
        upload_date=doc_meta.upload_date
    )

@app.get("/chat/attachments/{chat_id}",
    response_model=List[DocumentMetadata],
    tags=["Chat"],
    summary="List chat attachments")
async def list_chat_attachments(
    chat_id: str,
    document_storage: DocumentStorage = Depends(get_document_storage)
):
    """List all attachments for a specific chat session"""
    docs = await document_storage.list_documents(doc_type=DocumentType.USER_ATTACHMENT)
    return [doc for doc in docs if doc.chat_id == chat_id]

@app.delete("/chat/attachments/{doc_id}",
    tags=["Chat"],
    summary="Delete chat attachment")
async def delete_chat_attachment(
    doc_id: str,
    document_storage: DocumentStorage = Depends(get_document_storage)
):
    """Delete a chat attachment"""
    doc = await document_storage.get_document(doc_id)
    if doc.document_type != DocumentType.USER_ATTACHMENT:
        raise HTTPException(status_code=400, detail="Not a chat attachment")
    
    await document_storage.delete_document(doc_id)
    return {"message": "Attachment deleted successfully"}

@app.post("/documents/upload", 
    response_model=dict,
    tags=["Documents"],
    summary="Upload a new document",
    description="""
    Upload a new regulatory document with metadata.
    
    The following file types are supported:
    - PDF (.pdf)
    - Word Documents (.doc, .docx)
    - Text Files (.txt)
    
    Required metadata includes:
    - title: Document title
    - document_type: Type of document (e.g., 'Regulatory', 'Guidelines')
    - jurisdiction: Regulatory jurisdiction (e.g., 'US', 'EU')
    """
)
async def upload_document(
    file: UploadFile = File(..., description="The document file to upload"),
    title: str = Form(..., description="Document title"),
    document_type: str = Form(..., description="Type of document"),
    jurisdiction: str = Form(..., description="Regulatory jurisdiction"),
    version: Optional[str] = Form("1.0", description="Document version"),
    categories: Optional[List[str]] = Form(None, description="Document categories"),
    description: Optional[str] = Form(None, description="Document description"),
    document_storage: DocumentStorage = Depends(get_document_storage)
):
    try:
        doc_id = await document_storage.store_document(
            file=file,
            title=title,
            document_type=document_type,
            jurisdiction=jurisdiction,
            version=version,
            categories=categories,
            description=description
        )
        return {"id": doc_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents/{document_id}",
    tags=["Documents"],
    summary="Get document by ID",
    description="Retrieve a document and its metadata by ID"
)
async def get_document(document_id: str, document_storage: DocumentStorage = Depends(get_document_storage)):
    try:
        return await document_storage.get_document(document_id)
    except DocumentNotFoundError:
        raise HTTPException(status_code=404, detail="Document not found")

@app.get("/documents",
    tags=["Documents"],
    summary="List all documents",
    description="""
    List all documents with optional filtering by metadata.
    
    Filters can be applied for:
    - jurisdiction
    - document_type
    - categories
    """
)
async def list_documents(
    jurisdiction: Optional[str] = Query(None, description="Filter by jurisdiction"),
    document_type: Optional[str] = Query(None, description="Filter by document type"),
    category: Optional[str] = Query(None, description="Filter by category"),
    document_storage: DocumentStorage = Depends(get_document_storage)
):
    filters = {}
    if jurisdiction:
        filters["jurisdiction"] = jurisdiction
    if document_type:
        filters["document_type"] = document_type
    if category:
        filters["categories"] = category
    
    return await document_storage.list_documents(filters)

@app.post("/documents/search", 
    response_model=List[Dict[str, Any]],
    tags=["Documents"],
    summary="Search documents using semantic search")
async def search_documents(
    query: str = Query(..., description="Search query"),
    n_results: Optional[int] = Query(5, description="Number of results to return"),
    document_storage: DocumentStorage = Depends(get_document_storage)
):
    """Search for documents using semantic search."""
    try:
        # Get document retrieval instance
        doc_retrieval = document_storage.get_document_retrieval()
        
        # Perform search
        results = await doc_retrieval.search(query, n_results)
        return results
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error during search: {str(e)}"
        )

@app.put("/documents/{document_id}/metadata",
    tags=["Documents"],
    summary="Update document metadata",
    description="Update the metadata of an existing document"
)
async def update_document_metadata(
    document_id: str,
    metadata: dict = Body(..., description="Updated metadata fields"),
    document_storage: DocumentStorage = Depends(get_document_storage)
):
    try:
        return await document_storage.update_document_metadata(document_id, metadata)
    except DocumentNotFoundError:
        raise HTTPException(status_code=404, detail="Document not found")

@app.delete("/documents/{document_id}",
    tags=["Documents"],
    summary="Delete document",
    description="Delete a document and its associated metadata"
)
async def delete_document(document_id: str, document_storage: DocumentStorage = Depends(get_document_storage)):
    try:
        await document_storage.delete_document(document_id)
        return {"status": "success"}
    except DocumentNotFoundError:
        raise HTTPException(status_code=404, detail="Document not found")

@app.post("/chat", 
    response_model=dict,
    tags=["Chat"],
    summary="Process a chat message")
async def chat(
    query: str = Body(..., embed=True, description="User's question"),
    chat_id: str = Body(..., embed=True, description="Chat session ID"),
    context_size: int = Body(3, embed=True, description="Number of relevant documents to consider"),
    document_storage: DocumentStorage = Depends(get_document_storage)
):
    """Process a chat message and return a response with relevant sources."""
    try:
        # Get chat attachments
        attachments = await document_storage.list_documents(doc_type=DocumentType.USER_ATTACHMENT)
        chat_attachments = [doc for doc in attachments if doc.chat_id == chat_id]
        
        # Get reference documents
        ref_docs = await document_storage.list_documents(doc_type=DocumentType.REFERENCE)
        
        # Process query using both reference docs and chat attachments
        response, sources = await process_query(
            query=query,
            doc_storage=document_storage,
            reference_docs=ref_docs,
            chat_attachments=chat_attachments,
            context_size=context_size
        )
        
        return {
            "response": response,
            "sources": sources
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Admin endpoints for managing reference documents
@app.post("/admin/documents/upload",
    response_model=dict,
    tags=["Admin"],
    summary="Upload a reference document")
async def upload_reference_document(
    file: UploadFile,
    title: str = Form(...),
    description: str = Form(None),
    categories: List[str] = Form([]),
    document_storage: DocumentStorage = Depends(get_document_storage)
):
    """Upload a reference document with metadata"""
    try:
        doc_id = await document_storage.store_document(
            file=file,
            document_type=DocumentType.REFERENCE,
            title=title,
            description=description,
            categories=categories
        )
        return {"id": doc_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/admin/documents",
    response_model=List[dict],
    tags=["Admin"],
    summary="List all reference documents")
async def list_reference_documents(
    document_storage: DocumentStorage = Depends(get_document_storage)
):
    """List all reference documents"""
    try:
        docs = await document_storage.list_documents(doc_type=DocumentType.REFERENCE)
        return [
            {
                "id": doc.id,
                "filename": doc.filename,
                "title": doc.title,
                "description": doc.description,
                "categories": doc.categories,
                "upload_date": doc.upload_date
            }
            for doc in docs
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/admin/documents/{doc_id}",
    tags=["Admin"],
    summary="Delete a reference document")
async def delete_reference_document(
    doc_id: str,
    document_storage: DocumentStorage = Depends(get_document_storage)
):
    """Delete a reference document (admin only)"""
    try:
        doc = await document_storage.get_document(doc_id)
        if doc.document_type != DocumentType.REFERENCE:
            raise HTTPException(status_code=400, detail="Not a reference document")
        
        await document_storage.delete_document(doc_id)
        return {"message": "Document deleted successfully"}
    except DocumentNotFoundError:
        raise HTTPException(status_code=404, detail="Document not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Data models
class QuestionnaireInput(BaseModel):
    intended_purpose: str
    life_threatening: bool
    user_type: str
    requires_sterilization: bool
    body_contact_duration: str

class ChatMessage(BaseModel):
    message: str
    questionnaire_data: Optional[dict] = None

class ChatResponse(BaseModel):
    response: str
    sources: Optional[List[dict]] = None

class RegulatoryGuideline(BaseModel):
    title: str
    content: str
    reference: str
    relevance_score: float

class BulkUploadMetadata(BaseModel):
    metadata_list: List[dict]

class BulkDeleteRequest(BaseModel):
    doc_ids: List[str]

@app.get("/")
async def root():
    """
    API root endpoint.
    
    Returns:
    - A welcome message
    
    Raises:
    - None
    """
    return {"message": "Biotech Regulatory Compliance Tool API"}

@app.post("/questionnaire")
async def process_questionnaire(
    input_data: QuestionnaireInput,
    document_storage: DocumentStorage = Depends(get_document_storage)
):
    """
    Process a regulatory questionnaire and return relevant guidelines.
    """
    try:
        # Log input data
        print(f"Received questionnaire data: {input_data.dict()}")
        
        # Construct search query based on questionnaire input
        search_query = f"""
        medical device regulations for {input_data.intended_purpose} devices
        {"with life-threatening use" if input_data.life_threatening else ""}
        intended for {input_data.user_type}
        {"requiring sterilization" if input_data.requires_sterilization else ""}
        with {input_data.body_contact_duration} body contact duration
        """
        print(f"Generated search query: {search_query}")
        
        # Search for relevant documents
        doc_retrieval = document_storage.get_document_retrieval()
        results = await doc_retrieval.search(
            query=search_query,
            n_results=5
        )
        print(f"Search returned {len(results)} results")
        
        # Format results
        guidelines = []
        for result in results:
            print(f"Processing result: {result}")
            metadata = result.get('metadata', {})
            if not isinstance(metadata, dict):
                metadata = {}
                
            guideline = RegulatoryGuideline(
                title=metadata.get('title', 'Untitled'),
                content=result.get('content', ''),
                reference=metadata.get('document_type', 'Unknown'),
                relevance_score=result.get('score', 0.0)
            )
            guidelines.append(guideline)
        
        print(f"Returning {len(guidelines)} guidelines")
        return {
            "status": "success",
            "message": "Questionnaire processed successfully",
            "guidelines": guidelines
        }
    except Exception as e:
        print(f"Error processing questionnaire: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/guidelines")
async def get_guidelines(query: str):
    """
    Get regulatory guidelines based on a query.
    
    Parameters:
    - query: Search query for guidelines
    
    Returns:
    - List of relevant guidelines
    
    Raises:
    - 500: Server error during guideline retrieval
    """
    try:
        # TODO: Implement guideline retrieval logic
        sample_guideline = RegulatoryGuideline(
            title="Sample Guideline",
            content="This is a placeholder guideline content",
            reference="REF-001",
            relevance_score=0.95
        )
        return [sample_guideline]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/documents/bulk-upload")
async def bulk_upload_documents(
    metadata: BulkUploadMetadata,
    files: List[UploadFile] = File([]),
    document_storage: DocumentStorage = Depends(get_document_storage)
):
    """
    Upload multiple documents at once.
    
    Parameters:
    - metadata: List of document metadata
    - files: List of document files
    
    Returns:
    - Success message
    
    Raises:
    - 400: Number of files does not match number of metadata entries
    - 500: Server error during upload
    """
    if len(files) != len(metadata.metadata_list):
        raise HTTPException(
            status_code=400,
            detail="Number of files must match number of metadata entries"
        )
    return await document_storage.bulk_upload(files, metadata.metadata_list)

@app.post("/documents/bulk-delete")
async def bulk_delete_documents(request: BulkDeleteRequest, document_storage: DocumentStorage = Depends(get_document_storage)):
    """
    Delete multiple documents at once.
    
    Parameters:
    - request: List of document IDs to delete
    
    Returns:
    - Success message
    
    Raises:
    - 500: Server error during deletion
    """
    return await document_storage.bulk_delete(request.doc_ids)

@app.get("/documents/{doc_id}")
async def get_document(doc_id: str, document_storage: DocumentStorage = Depends(get_document_storage)):
    """
    Get metadata for a specific document.
    
    Parameters:
    - doc_id: ID of the document to retrieve
    
    Returns:
    - Document metadata
    
    Raises:
    - 404: Document not found
    - 500: Server error during document retrieval
    """
    result = await document_storage.get_document_metadata(doc_id)
    if not result:
        raise HTTPException(status_code=404, detail="Document not found")
    return result

@app.get("/documents/{doc_id}/preview")
async def get_document_preview(doc_id: str, document_storage: DocumentStorage = Depends(get_document_storage)):
    """
    Get document preview content.
    
    Parameters:
    - doc_id: ID of the document to retrieve
    
    Returns:
    - Document preview content
    
    Raises:
    - 404: Document not found
    - 500: Server error during document retrieval
    """
    return await document_storage.get_document_preview(doc_id)

@app.get("/documents/{doc_id}/versions")
async def get_document_versions(doc_id: str, document_storage: DocumentStorage = Depends(get_document_storage)):
    """
    Get version history for a document.
    
    Parameters:
    - doc_id: ID of the document to retrieve
    
    Returns:
    - List of document versions
    
    Raises:
    - 404: Document not found
    - 500: Server error during document retrieval
    """
    return await document_storage.get_document_versions(doc_id)

@app.get("/documents/categories")
async def get_categories(document_storage: DocumentStorage = Depends(get_document_storage)):
    """
    Get all unique categories.
    
    Returns:
    - List of categories
    
    Raises:
    - 500: Server error during category retrieval
    """
    return await document_storage.get_categories()

@app.get("/documents/tags")
async def get_tags(document_storage: DocumentStorage = Depends(get_document_storage)):
    """
    Get all unique tags.
    
    Returns:
    - List of tags
    
    Raises:
    - 500: Server error during tag retrieval
    """
    return await document_storage.get_tags()

@app.get("/documents/export")
async def export_documents(format: str = Query("json", regex="^(json|csv)$"), document_storage: DocumentStorage = Depends(get_document_storage)):
    """
    Export document list in various formats.
    
    Parameters:
    - format: Export format ("json" or "csv")
    
    Returns:
    - Exported document list
    
    Raises:
    - 400: Invalid export format
    - 500: Server error during export
    """
    try:
        content = await document_storage.export_document_list(format)
        
        if format == "json":
            media_type = "application/json"
            filename = "documents.json"
        else:  # csv
            media_type = "text/csv"
            filename = "documents.csv"
        
        return StreamingResponse(
            io.StringIO(content),
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/documents/{doc_id}")
async def delete_document(doc_id: str, document_storage: DocumentStorage = Depends(get_document_storage)):
    """
    Delete a document.
    
    Parameters:
    - doc_id: ID of the document to delete
    
    Returns:
    - Success message
    
    Raises:
    - 404: Document not found
    - 500: Server error during deletion
    """
    try:
        await document_storage.delete_document(doc_id)
        return {"message": "Document deleted successfully"}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.patch("/documents/{doc_id}")
async def update_document(doc_id: str, updates: dict, document_storage: DocumentStorage = Depends(get_document_storage)):
    """
    Update document metadata.
    
    Parameters:
    - doc_id: ID of the document to update
    - updates: Dictionary of metadata updates
    
    Returns:
    - Updated document metadata
    
    Raises:
    - 404: Document not found
    - 500: Server error during update
    """
    try:
        result = await document_storage.update_document_metadata(doc_id, updates)
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    print("Starting server...")
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="debug"
    )
