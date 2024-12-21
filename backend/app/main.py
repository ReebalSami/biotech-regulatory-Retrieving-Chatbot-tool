from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Dict
import io
import uvicorn
from app.document_retrieval import DocumentRetrieval
from app.chatbot import Chatbot
from app.document_management import DocumentManager
import os
import json
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
import PyPDF2
from docx import Document

app = FastAPI(title="Biotech Regulatory Compliance Tool")

# Initialize components
doc_retrieval = DocumentRetrieval()
chatbot = Chatbot(doc_retrieval)
doc_manager = DocumentManager()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

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
    return {"message": "Biotech Regulatory Compliance Tool API"}

@app.post("/chat", response_model=ChatResponse)
async def chat(message: ChatMessage):
    try:
        # Get chatbot response with questionnaire context
        response = await chatbot.get_response(
            message.message,
            questionnaire_data=message.questionnaire_data
        )
        
        # Get relevant documents used as sources
        sources = doc_retrieval.search(message.message)
        
        # Get user documents
        try:
            with open("user_documents.json", "r") as f:
                user_docs = json.load(f)
        except FileNotFoundError:
            user_docs = []
            
        # Process user documents
        user_sources = []
        for doc in user_docs:
            try:
                file_path = doc["file_path"]
                if os.path.exists(file_path):
                    # Extract text based on file type
                    file_extension = os.path.splitext(file_path)[1].lower()
                    doc_text = ""
                    
                    if file_extension == '.pdf':
                        with open(file_path, 'rb') as file:
                            pdf_reader = PyPDF2.PdfReader(file)
                            for page in pdf_reader.pages:
                                doc_text += page.extract_text() + "\n"
                    elif file_extension in ['.doc', '.docx']:
                        doc_obj = Document(file_path)
                        doc_text = "\n".join([paragraph.text for paragraph in doc_obj.paragraphs])
                    else:
                        with open(file_path, 'r') as file:
                            doc_text = file.read()
                            
                    # Add to sources if relevant
                    relevance_score = doc_retrieval.calculate_relevance(message.message, doc_text)
                    if relevance_score > 0.3:  # Adjust threshold as needed
                        user_sources.append({
                            "title": doc["title"],
                            "content": doc_text[:200] + "..." if len(doc_text) > 200 else doc_text,
                            "jurisdiction": "User Document"
                        })
            except Exception as e:
                print(f"Error processing user document {doc.get('title', 'Unknown')}: {str(e)}")
                continue
        
        # Combine sources
        all_sources = sources + user_sources
        
        # Update response to mention user documents if they were used
        if user_sources:
            response += "\n\nThis response also considers information from your uploaded documents."
        
        return ChatResponse(
            response=response,
            sources=[{
                "title": source.get("title", "Unknown"),
                "content": source.get("content", "")[:200] + "..." if len(source.get("content", "")) > 200 else source.get("content", ""),
                "jurisdiction": source.get("jurisdiction", "Unknown")
            } for source in all_sources]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/questionnaire")
async def process_questionnaire(input_data: QuestionnaireInput):
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
@app.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(...),
    document_type: str = Form(...),
    jurisdiction: str = Form(...),
    version: str = Form(...),
    effective_date: str = Form(...),
    categories: str = Form(""),
    tags: str = Form("")
):
    """Upload a new document with metadata"""
    try:
        categories_list = [c.strip() for c in categories.split(",")] if categories else []
        tags_list = [t.strip() for t in tags.split(",")] if tags else []
        
        result = await doc_manager.upload_document(
            file=file,
            title=title,
            document_type=document_type,
            jurisdiction=jurisdiction,
            version=version,
            effective_date=effective_date,
            categories=categories_list,
            tags=tags_list
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/documents/bulk-upload")
async def bulk_upload_documents(
    metadata: BulkUploadMetadata,
    files: List[UploadFile] = File([])
):
    """Upload multiple documents at once"""
    if len(files) != len(metadata.metadata_list):
        raise HTTPException(
            status_code=400,
            detail="Number of files must match number of metadata entries"
        )
    return await doc_manager.bulk_upload(files, metadata.metadata_list)

@app.post("/documents/bulk-delete")
async def bulk_delete_documents(request: BulkDeleteRequest):
    """Delete multiple documents at once"""
    return doc_manager.bulk_delete(request.doc_ids)

@app.get("/documents")
async def list_documents(
    document_type: Optional[str] = None,
    jurisdiction: Optional[str] = None,
    category: Optional[str] = None,
    tag: Optional[str] = None
):
    """List all documents with optional filtering"""
    return doc_manager.list_documents(
        document_type=document_type,
        jurisdiction=jurisdiction,
        category=category,
        tag=tag
    )

@app.get("/documents/{doc_id}")
async def get_document(doc_id: str):
    """Get metadata for a specific document"""
    result = doc_manager.get_document_metadata(doc_id)
    if not result:
        raise HTTPException(status_code=404, detail="Document not found")
    return result

@app.get("/documents/{doc_id}/preview")
async def get_document_preview(doc_id: str):
    """Get document preview content"""
    return doc_manager.get_document_preview(doc_id)

@app.get("/documents/{doc_id}/versions")
async def get_document_versions(doc_id: str):
    """Get version history for a document"""
    return doc_manager.get_document_versions(doc_id)

@app.get("/documents/categories")
async def get_categories():
    """Get all unique categories"""
    return doc_manager.get_categories()

@app.get("/documents/tags")
async def get_tags():
    """Get all unique tags"""
    return doc_manager.get_tags()

@app.get("/documents/export")
async def export_documents(format: str = Query("json", regex="^(json|csv)$")):
    """Export document list in various formats"""
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
    """Delete a document"""
    try:
        doc_manager.delete_document(doc_id)
        return {"message": "Document deleted successfully"}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.patch("/documents/{doc_id}")
async def update_document(doc_id: str, updates: Dict):
    """Update document metadata"""
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
    print(f"Starting upload process - Title: {title}, Description: {description}, File: {file.filename}")
    if title is None:
        title = file.filename
    
    try:
        # Create user documents directory if it doesn't exist
        user_docs_dir = "user_documents"
        print(f"Creating directory: {user_docs_dir}")
        os.makedirs(user_docs_dir, exist_ok=True)

        # Create or load user documents database
        user_docs_db_file = "user_documents.json"
        print(f"Loading database: {user_docs_db_file}")
        try:
            with open(user_docs_db_file, "r") as f:
                user_docs = json.load(f)
                print(f"Loaded {len(user_docs)} existing documents")
        except (FileNotFoundError, json.JSONDecodeError):
            print("No existing database, starting fresh")
            user_docs = []

        # Generate unique ID and filename
        doc_id = str(uuid.uuid4())
        file_extension = os.path.splitext(file.filename)[1]
        safe_filename = f"{doc_id}{file_extension}"
        file_path = os.path.join(user_docs_dir, safe_filename)
        print(f"Generated file path: {file_path}")

        # Save the file
        print("Reading file contents...")
        contents = await file.read()
        print(f"Received {len(contents)} bytes")
        
        print("Writing file to disk...")
        with open(file_path, "wb") as f:
            f.write(contents)
        print("File written successfully")

        # Create document metadata
        user_doc = {
            "id": doc_id,
            "title": title,
            "description": description,
            "filename": file.filename,
            "file_path": file_path,
            "upload_date": datetime.now().isoformat(),
            "file_type": file_extension.lstrip('.').lower()
        }
        print(f"Created metadata: {user_doc}")

        # Add to database
        user_docs.append(user_doc)
        print(f"Saving updated database with {len(user_docs)} documents")
        
        with open(user_docs_db_file, "w") as f:
            json.dump(user_docs, f, indent=2)
        print("Database updated successfully")

        return {"success": True, "document": user_doc}
    except Exception as e:
        error_msg = str(e)
        print(f"Error during upload: {error_msg}")
        # Clean up file if it was created
        if 'file_path' in locals() and os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"Cleaned up file: {file_path}")
            except Exception as cleanup_error:
                print(f"Failed to clean up file: {cleanup_error}")
        raise HTTPException(status_code=500, detail=error_msg)

@app.get("/user-documents")
async def get_user_documents():
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
