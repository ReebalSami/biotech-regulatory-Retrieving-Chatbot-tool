import os
import shutil
import json
from datetime import datetime, timedelta
from typing import List, Optional, Any
from fastapi import UploadFile
from pathlib import Path
import uuid
from app.utils.document_types import DocumentType, DocumentMetadata
from app.utils.exceptions import DocumentNotFoundError

class DocumentStorage:
    def __init__(self):
        self.base_dir = Path("data")
        self.reference_dir = self.base_dir / "reference_documents"
        self.user_dir = self.base_dir / "user_attachments"
        self.metadata_file = self.base_dir / "metadata.json"
        
        # Create directories if they don't exist
        self.reference_dir.mkdir(parents=True, exist_ok=True)
        self.user_dir.mkdir(parents=True, exist_ok=True)
        
        # Load or create metadata
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r') as f:
                self.metadata = json.load(f)
        else:
            self.metadata = {}
            self._save_metadata()
    
    def _save_metadata(self):
        """Save metadata to file"""
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2, default=str)
    
    def _get_storage_path(self, doc_type: DocumentType) -> Path:
        """Get the storage path for a document type"""
        return self.reference_dir if doc_type == DocumentType.REFERENCE else self.user_dir
    
    async def store_document(
        self,
        file: UploadFile,
        document_type: DocumentType,
        title: Optional[str] = None,
        description: Optional[str] = None,
        categories: Optional[List[str]] = None,
        chat_id: Optional[str] = None
    ) -> str:
        """Store a document and return its ID"""
        try:
            # Generate unique ID
            doc_id = str(uuid.uuid4())
            
            # Determine storage path
            storage_dir = self._get_storage_path(document_type)
            file_path = storage_dir / f"{doc_id}_{file.filename}"
            
            # Save file
            with open(file_path, 'wb') as f:
                shutil.copyfileobj(file.file, f)
            
            # Create metadata
            self.metadata[doc_id] = {
                "id": doc_id,
                "filename": file.filename,
                "title": title or file.filename,
                "description": description,
                "categories": categories or [],
                "document_type": document_type.value,
                "chat_id": chat_id,
                "upload_date": datetime.now().isoformat(),
                "file_path": str(file_path)
            }
            
            self._save_metadata()
            return doc_id
            
        except Exception as e:
            # Clean up if something goes wrong
            if 'file_path' in locals() and os.path.exists(file_path):
                os.remove(file_path)
            raise Exception(f"Failed to store document: {str(e)}")
    
    async def get_document(self, doc_id: str) -> DocumentMetadata:
        """Get document metadata"""
        if doc_id not in self.metadata:
            raise DocumentNotFoundError(f"Document {doc_id} not found")
        
        meta = self.metadata[doc_id]
        return DocumentMetadata(**meta)
    
    async def get_document_content(self, doc_id: str) -> str:
        """Get document content"""
        meta = await self.get_document(doc_id)
        with open(meta.file_path, 'r') as f:
            return f.read()
    
    async def list_documents(
        self,
        doc_type: Optional[DocumentType] = None,
        categories: Optional[List[str]] = None
    ) -> List[DocumentMetadata]:
        """List documents with optional filters"""
        docs = []
        for doc_id, meta in self.metadata.items():
            if doc_type and meta['document_type'] != doc_type.value:
                continue
                
            if categories and not any(cat in meta.get('categories', []) for cat in categories):
                continue
            
            docs.append(DocumentMetadata(**meta))
        
        return docs
    
    async def delete_document(self, doc_id: str):
        """Delete a document"""
        if doc_id not in self.metadata:
            raise DocumentNotFoundError(f"Document {doc_id} not found")
        
        # Remove file
        file_path = Path(self.metadata[doc_id]['file_path'])
        if file_path.exists():
            os.remove(file_path)
        
        # Remove metadata
        del self.metadata[doc_id]
        self._save_metadata()
    
    async def cleanup_expired_documents(self):
        """Clean up expired user attachments (older than 24 hours)"""
        now = datetime.now()
        to_delete = []
        
        for doc_id, meta in self.metadata.items():
            if meta['document_type'] != DocumentType.USER_ATTACHMENT.value:
                continue
                
            upload_date = datetime.fromisoformat(meta['upload_date'])
            if now - upload_date > timedelta(hours=24):
                to_delete.append(doc_id)
        
        for doc_id in to_delete:
            await self.delete_document(doc_id)
    
    def get_document_retrieval(self):
        """Get document retrieval instance"""
        try:
            from app.document_retrieval import DocumentRetrieval
            print("Creating DocumentRetrieval instance...")
            retrieval = DocumentRetrieval()
            print("DocumentRetrieval instance created successfully")
            return retrieval
        except Exception as e:
            print(f"Error creating DocumentRetrieval instance: {str(e)}")
            raise e

    async def search_documents(
        self,
        query: str,
        doc_type: Optional[DocumentType] = None,
        n_results: int = 5
    ) -> List[DocumentMetadata]:
        """
        Search documents using simple keyword matching.
        This should be replaced with a proper vector search in the future.
        """
        results = []
        for doc_id, meta in self.metadata.items():
            if doc_type and meta['document_type'] != doc_type.value:
                continue
            
            # Simple keyword matching in title and content
            score = 0
            query_lower = query.lower()
            
            # Check title
            if query_lower in meta.get('title', '').lower():
                score += 2
            
            # Check content
            try:
                with open(meta['file_path'], 'r') as f:
                    content = f.read().lower()
                    if query_lower in content:
                        score += 1
            except:
                continue
            
            if score > 0:
                results.append((score, DocumentMetadata(**meta)))
        
        # Sort by score and return top N results
        results.sort(key=lambda x: x[0], reverse=True)
        return [doc for score, doc in results[:n_results]]
