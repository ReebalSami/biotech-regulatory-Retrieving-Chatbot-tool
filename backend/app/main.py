from fastapi import FastAPI, File, UploadFile, HTTPException, Query, Form, Body, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel
import json
from pathlib import Path
from app.document_management import DocumentManager
from app.utils.exceptions import DocumentNotFoundError, InvalidFileTypeError
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

doc_manager = DocumentManager()

async def get_document_manager():
    """Get document manager instance."""
    return doc_manager

@app.post("/documents/upload", 
    response_model=Dict[str, str],
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
    description: Optional[str] = Form(None, description="Document description")
):
    try:
        doc_id = await doc_manager.upload_document(
            file=file,
            title=title,
            document_type=document_type,
            jurisdiction=jurisdiction,
            version=version,
            categories=categories,
            description=description
        )
        return {"id": doc_id}
    except InvalidFileTypeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents/{document_id}",
    tags=["Documents"],
    summary="Get document by ID",
    description="Retrieve a document and its metadata by ID"
)
async def get_document(document_id: str):
    try:
        return doc_manager.get_document(document_id)
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
    category: Optional[str] = Query(None, description="Filter by category")
):
    filters = {}
    if jurisdiction:
        filters["jurisdiction"] = jurisdiction
    if document_type:
        filters["document_type"] = document_type
    if category:
        filters["categories"] = category
    
    return doc_manager.list_documents(filters)

@app.get("/documents/search", response_model=List[Dict[str, Any]], status_code=200)
async def search_documents(
    query: str = Query(..., description="Search query"),
    n_results: Optional[int] = Query(5, description="Number of results to return"),
    document_manager: DocumentManager = Depends(get_document_manager)
) -> List[Dict[str, Any]]:
    """Search for documents using semantic search."""
    try:
        results = await document_manager.search_documents(query, n_results)
        return results if results else []
    except Exception as e:
        logger.error(f"Error searching documents: {str(e)}")
        return []

@app.put("/documents/{document_id}/metadata",
    tags=["Documents"],
    summary="Update document metadata",
    description="Update the metadata of an existing document"
)
async def update_document_metadata(
    document_id: str,
    metadata: Dict[str, Any] = Body(..., description="Updated metadata fields")
):
    try:
        return doc_manager.update_document_metadata(document_id, metadata)
    except DocumentNotFoundError:
        raise HTTPException(status_code=404, detail="Document not found")

@app.delete("/documents/{document_id}",
    tags=["Documents"],
    summary="Delete document",
    description="Delete a document and its associated metadata"
)
async def delete_document(document_id: str):
    try:
        doc_manager.delete_document(document_id)
        return {"status": "success"}
    except DocumentNotFoundError:
        raise HTTPException(status_code=404, detail="Document not found")

@app.post("/chat",
    tags=["Chat"],
    summary="Chat with documents",
    description="""
    Ask questions about your regulatory documents.
    
    The chatbot will analyze your documents and provide relevant answers
    based on the content of your regulatory documents.
    """
)
async def chat(
    query: str = Body(..., embed=True, description="User's question"),
    context_size: int = Body(3, embed=True, description="Number of relevant documents to consider")
):
    try:
        return await process_query(query, context_size)
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
    metadata_list: List[Dict]

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
async def process_questionnaire(input_data: QuestionnaireInput):
    """
    Process a regulatory questionnaire.
    
    Parameters:
    - input_data: Questionnaire input data
    
    Returns:
    - Success message and processed data
    
    Raises:
    - 500: Server error during questionnaire processing
    """
    try:
        # TODO: Implement document retrieval based on questionnaire input
        return {
            "status": "success",
            "message": "Questionnaire processed successfully",
            "data": input_data.dict()
        }
    except Exception as e:
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

# Document Management Endpoints
@app.post("/documents/bulk-upload")
async def bulk_upload_documents(
    metadata: BulkUploadMetadata,
    files: List[UploadFile] = File([])
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
    return await doc_manager.bulk_upload(files, metadata.metadata_list)

@app.post("/documents/bulk-delete")
async def bulk_delete_documents(request: BulkDeleteRequest):
    """
    Delete multiple documents at once.
    
    Parameters:
    - request: List of document IDs to delete
    
    Returns:
    - Success message
    
    Raises:
    - 500: Server error during deletion
    """
    return doc_manager.bulk_delete(request.doc_ids)

@app.get("/documents/{doc_id}")
async def get_document(doc_id: str):
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
    result = doc_manager.get_document_metadata(doc_id)
    if not result:
        raise HTTPException(status_code=404, detail="Document not found")
    return result

@app.get("/documents/{doc_id}/preview")
async def get_document_preview(doc_id: str):
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
    return doc_manager.get_document_preview(doc_id)

@app.get("/documents/{doc_id}/versions")
async def get_document_versions(doc_id: str):
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
    return doc_manager.get_document_versions(doc_id)

@app.get("/documents/categories")
async def get_categories():
    """
    Get all unique categories.
    
    Returns:
    - List of categories
    
    Raises:
    - 500: Server error during category retrieval
    """
    return doc_manager.get_categories()

@app.get("/documents/tags")
async def get_tags():
    """
    Get all unique tags.
    
    Returns:
    - List of tags
    
    Raises:
    - 500: Server error during tag retrieval
    """
    return doc_manager.get_tags()

@app.get("/documents/export")
async def export_documents(format: str = Query("json", regex="^(json|csv)$")):
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
        content = doc_manager.export_document_list(format)
        
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
async def delete_document(doc_id: str):
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
        doc_manager.delete_document(doc_id)
        return {"message": "Document deleted successfully"}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.patch("/documents/{doc_id}")
async def update_document(doc_id: str, updates: Dict):
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
        result = doc_manager.update_document_metadata(doc_id, updates)
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# User Document Management
@app.post("/user-documents/upload")
async def upload_user_document(
    file: UploadFile,
    title: str = Form(None),
    description: str = Form("")
):
    """
    Upload a user document.
    
    Parameters:
    - file: The document file (PDF, DOCX, or TXT)
    - title: Document title
    - description: Document description
    
    Returns:
    - Success message and document ID
    
    Raises:
    - 400: Invalid file type or size
    - 500: Server error during upload
    """
    try:
        # Validate file
        content_type, content = validate_file(file.file, file.filename)
        
        # Save file
        file_path = save_file(content, file.filename, "user_documents")
        
        # Get file metadata
        metadata = get_file_metadata(file_path)
        
        # Process document content
        doc_retrieval = DocumentRetrieval()
        doc_id = doc_retrieval.index_document({
            "content": content.decode('utf-8'),
            "metadata": {
                "filename": file.filename,
                "content_type": content_type,
                **metadata
            }
        })
        
        logger.info(f"Document uploaded and processed successfully: {doc_id}")
        return {"message": "File uploaded successfully", "document_id": doc_id}
        
    except Exception as e:
        logger.error(f"Error processing upload: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/user-documents")
async def get_user_documents():
    """
    Get all user documents.
    
    Returns:
    - List of user documents
    
    Raises:
    - 500: Server error during document retrieval
    """
    try:
        with open("user_documents.json", "r") as f:
            user_docs = json.load(f)
        return user_docs
    except FileNotFoundError:
        return []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/user-documents/{doc_id}/preview")
async def get_user_document_preview(doc_id: str):
    """
    Get user document preview content.
    
    Parameters:
    - doc_id: ID of the document to retrieve
    
    Returns:
    - Document preview content
    
    Raises:
    - 404: Document not found
    - 500: Server error during document retrieval
    """
    try:
        # Get document metadata
        with open("user_documents.json", "r") as f:
            user_docs = json.load(f)
        
        doc = next((d for d in user_docs if d["id"] == doc_id), None)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        # Read file content
        file_path = doc["file_path"]
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")

        # Extract text based on file type
        file_extension = os.path.splitext(file_path)[1].lower()
        
        if file_extension == '.pdf':
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
        elif file_extension in ['.doc', '.docx']:
            doc = Document(file_path)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        elif file_extension == '.txt':
            with open(file_path, 'r', encoding='utf-8') as file:
                text = file.read()
        else:
            text = "Preview not available for this file type"

        return text
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/user-documents/{doc_id}")
async def delete_user_document(doc_id: str):
    """
    Delete a user document.
    
    Parameters:
    - doc_id: ID of the document to delete
    
    Returns:
    - Success message
    
    Raises:
    - 404: Document not found
    - 500: Server error during deletion
    """
    try:
        # Read current documents
        with open("user_documents.json", "r") as f:
            user_docs = json.load(f)
        
        # Find document
        doc = next((d for d in user_docs if d["id"] == doc_id), None)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        # Delete file
        file_path = doc["file_path"]
        if os.path.exists(file_path):
            os.remove(file_path)

        # Update database
        user_docs = [d for d in user_docs if d["id"] != doc_id]
        with open("user_documents.json", "w") as f:
            json.dump(user_docs, f, indent=2)

        return {"success": True}
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
