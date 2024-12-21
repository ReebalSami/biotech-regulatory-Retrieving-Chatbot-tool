import os
import json
import uuid
import shutil
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from fastapi import UploadFile
from app.utils.exceptions import DocumentNotFoundError, InvalidFileTypeError
from app.document_retrieval import DocumentRetrieval
from app.config import get_settings
from app.utils.logger import setup_logger

class DocumentManager:
    def __init__(self, doc_retrieval: Optional[DocumentRetrieval] = None):
        # Initialize directories
        self.documents_dir = Path("user_documents")
        self.documents_dir.mkdir(exist_ok=True)
        
        self.metadata_file = Path("documents/metadata.json")
        self.metadata_file.parent.mkdir(exist_ok=True)
        
        # Initialize document retrieval
        self.doc_retrieval = doc_retrieval if doc_retrieval else DocumentRetrieval()
        
        # Initialize logger
        self.logger = setup_logger(__name__)
        
        # Load metadata
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, "r") as f:
                    self.metadata = json.load(f)
            except json.JSONDecodeError:
                self.logger.error("Failed to load metadata file. Creating new one.")
                self.metadata = {}
        else:
            self.metadata = {}
            self._save_metadata()

    def _save_metadata(self):
        """Save metadata to file"""
        try:
            with open(self.metadata_file, "w") as f:
                json.dump(self.metadata, f, indent=4)
        except Exception as e:
            self.logger.error(f"Failed to save metadata: {str(e)}")

    def _ensure_directory_exists(self):
        """Ensure all necessary directories exist"""
        self.documents_dir.mkdir(exist_ok=True)
        self.metadata_file.parent.mkdir(exist_ok=True)
        (self.documents_dir / "uploads").mkdir(exist_ok=True)
        (self.documents_dir / "versions").mkdir(exist_ok=True)
        (self.documents_dir / "previews").mkdir(exist_ok=True)
        if not self.metadata_file.exists():
            self._save_metadata({})

    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file content"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def _extract_text_content(self, file_path: Path) -> str:
        """Extract text content from various file types"""
        try:
            if file_path.suffix.lower() == '.pdf':
                with open(file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    text = ""
                    for page in pdf_reader.pages:
                        text += page.extract_text() + "\n"
                    return text
            elif file_path.suffix.lower() in ['.doc', '.docx']:
                doc = DocxDocument(file_path)
                return "\n".join([paragraph.text for paragraph in doc.paragraphs])
            elif file_path.suffix.lower() == '.txt':
                with open(file_path, 'r', encoding='utf-8') as file:
                    return file.read().strip()
            else:
                raise ValueError(f"Unsupported file type: {file_path.suffix}")
        except Exception as e:
            self.logger.error(f"Error extracting text content: {str(e)}")
            raise HTTPException(
                status_code=400,
                detail=f"Failed to extract text content: {str(e)}"
            )

    def _create_preview(self, file_path: Path, doc_id: str) -> str:
        """Create a preview of the document"""
        preview_path = self.documents_dir / "previews" / f"{doc_id}.txt"
        try:
            content = self._extract_text_content(file_path)
            # Save first 1000 characters as preview
            with open(preview_path, 'w', encoding='utf-8') as f:
                f.write(content[:1000])
            return str(preview_path)
        except Exception as e:
            print(f"Error creating preview: {str(e)}")
            return ""

    def _validate_file_size(self, file_path: Path, max_size_mb: int = 10) -> None:
        """Validate file size"""
        file_size = file_path.stat().st_size
        max_size = max_size_mb * 1024 * 1024  # Convert MB to bytes
        if file_size > max_size:
            raise HTTPException(
                status_code=400,
                detail=f"File size exceeds limit of {max_size_mb}MB"
            )

    def _validate_file_type(self, file_path: Path) -> None:
        """Validate file type"""
        allowed_extensions = {'.pdf', '.doc', '.docx', '.txt'}
        if file_path.suffix.lower() not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type: {file_path.suffix}"
            )

    async def upload_document(
        self,
        file: UploadFile,
        title: str,
        document_type: str,
        jurisdiction: str,
        version: str = "1.0",
        categories: Optional[List[str]] = None,
        description: Optional[str] = None
    ) -> str:
        """
        Upload a document with metadata.
        
        Args:
            file: The uploaded file
            title: Document title
            document_type: Type of document
            jurisdiction: Regulatory jurisdiction
            version: Document version
            categories: List of categories
            description: Document description
            
        Returns:
            Document ID
            
        Raises:
            InvalidFileTypeError: If file type is not supported
        """
        try:
            # Validate file type
            file_ext = os.path.splitext(file.filename)[1].lower()
            if file_ext not in [".pdf", ".doc", ".docx", ".txt"]:
                raise InvalidFileTypeError(f"Unsupported file type: {file_ext}")
            
            # Generate unique ID and save file
            doc_id = str(uuid.uuid4())
            file_path = self.documents_dir / f"{doc_id}{file_ext}"
            
            # Save file
            contents = await file.read()
            with open(file_path, "wb") as f:
                f.write(contents)
            
            # Extract text content
            content = contents.decode("utf-8", errors="ignore") if file_ext == ".txt" else await self.doc_retrieval.extract_text(file_path)
            
            # Save metadata
            metadata = {
                "id": doc_id,
                "title": title,
                "document_type": document_type,
                "jurisdiction": jurisdiction,
                "version": version,
                "categories": categories or [],
                "description": description,
                "file_path": str(file_path),
                "file_type": file_ext,
                "upload_date": datetime.now().isoformat(),
                "content": content
            }
            
            self.metadata[doc_id] = metadata
            self._save_metadata()
            
            # Index document for search
            await self.doc_retrieval.index_document(str(file_path), doc_id, metadata)
            
            return doc_id
        except Exception as e:
            self.logger.error(f"Error uploading document: {str(e)}")
            if "file_path" in locals() and os.path.exists(file_path):
                os.unlink(file_path)
            raise

    def get_document_preview(self, doc_id: str) -> str:
        """Get document preview content"""
        metadata = self._load_metadata()
        if doc_id not in metadata:
            raise HTTPException(status_code=404, detail="Document not found")
        
        preview_path = metadata[doc_id].get("preview_path")
        if not preview_path or not Path(preview_path).exists():
            return ""
        
        with open(preview_path, 'r', encoding='utf-8') as f:
            return f.read()

    def get_document_versions(self, doc_id: str) -> List[Dict]:
        """Get version history for a document"""
        metadata = self._load_metadata()
        if doc_id not in metadata:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return metadata[doc_id].get("versions", [])

    async def bulk_upload(self, files: List[UploadFile], metadata_list: List[Dict]) -> List[Dict]:
        """Upload multiple documents at once"""
        results = []
        for file, metadata in zip(files, metadata_list):
            try:
                result = await self.upload_document(
                    file=file,
                    **metadata
                )
                results.append({"success": True, "data": result})
            except Exception as e:
                results.append({"success": False, "error": str(e)})
        return results

    def bulk_delete(self, doc_ids: List[str]) -> Dict:
        """Delete multiple documents at once"""
        results = {
            "successful": [],
            "failed": []
        }
        for doc_id in doc_ids:
            try:
                self.delete_document(doc_id)
                results["successful"].append(doc_id)
            except Exception as e:
                results["failed"].append({"id": doc_id, "error": str(e)})
        return results

    def get_categories(self) -> List[str]:
        """Get all unique categories"""
        metadata = self._load_metadata()
        categories = set()
        for doc in metadata.values():
            categories.update(doc.get("categories", []))
        return sorted(list(categories))

    def get_tags(self) -> List[str]:
        """Get all unique tags"""
        metadata = self._load_metadata()
        tags = set()
        for doc in metadata.values():
            tags.update(doc.get("tags", []))
        return sorted(list(tags))

    def export_document_list(self, format: str = "json") -> str:
        """Export document list in various formats"""
        metadata = self._load_metadata()
        if format == "json":
            return json.dumps(metadata, indent=2)
        elif format == "csv":
            import csv
            import io
            output = io.StringIO()
            writer = csv.writer(output)
            headers = ["ID", "Title", "Type", "Jurisdiction", "Version", "Effective Date", "Categories", "Tags"]
            writer.writerow(headers)
            for doc_id, doc in metadata.items():
                writer.writerow([
                    doc_id,
                    doc["title"],
                    doc["document_type"],
                    doc["jurisdiction"],
                    doc["version"],
                    doc["effective_date"],
                    ",".join(doc.get("categories", [])),
                    ",".join(doc.get("tags", []))
                ])
            return output.getvalue()
        else:
            raise ValueError(f"Unsupported export format: {format}")

    def _load_metadata(self) -> dict:
        """Load metadata from JSON file"""
        try:
            with open(self.metadata_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def get_document_metadata(self, doc_id: str) -> Optional[Dict]:
        """Get metadata for a specific document"""
        metadata = self._load_metadata()
        return metadata.get(doc_id)

    def list_documents(self, filters: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
        """
        List all documents with optional filtering.
        
        Args:
            filters: Optional filters to apply
            
        Returns:
            List of document metadata
        """
        documents = []
        for doc_id, metadata in self.metadata.items():
            # Apply filters if any
            if filters:
                match = True
                for key, value in filters.items():
                    if key not in metadata or metadata[key] != value:
                        match = False
                        break
                if not match:
                    continue
            
            # Format document data
            doc_data = {
                "id": doc_id,
                "metadata": {
                    "title": metadata["title"],
                    "document_type": metadata["document_type"],
                    "jurisdiction": metadata["jurisdiction"],
                    "version": metadata["version"],
                    "categories": metadata.get("categories", []),
                    "description": metadata.get("description", ""),
                    "upload_date": metadata["upload_date"],
                    "file_type": metadata["file_type"]
                }
            }
            documents.append(doc_data)
        
        return documents

    def delete_document(self, doc_id: str):
        """Delete a document and all its versions"""
        metadata = self._load_metadata()
        if doc_id not in metadata:
            raise HTTPException(status_code=404, detail="Document not found")

        # Delete main file
        file_path = Path(metadata[doc_id]["file_path"])
        if file_path.exists():
            file_path.unlink()

        # Delete preview
        preview_path = metadata[doc_id].get("preview_path")
        if preview_path and Path(preview_path).exists():
            Path(preview_path).unlink()

        # Delete versions
        version_dir = self.documents_dir / "versions" / doc_id
        if version_dir.exists():
            shutil.rmtree(version_dir)

        # Remove from metadata
        del metadata[doc_id]
        self._save_metadata(metadata)

        # Remove from search index
        self.doc_retrieval.delete_document(doc_id)

    def update_document_metadata(self, doc_id: str, **updates) -> Dict:
        """Update document metadata"""
        metadata = self._load_metadata()
        if doc_id not in metadata:
            raise HTTPException(status_code=404, detail="Document not found")

        # Update allowed fields
        allowed_fields = [
            "title", "document_type", "jurisdiction", 
            "version", "effective_date", "categories", "tags"
        ]
        for field, value in updates.items():
            if field in allowed_fields:
                metadata[doc_id][field] = value

        self._save_metadata(metadata)
        return metadata[doc_id]

    async def search_documents(
        self,
        query: str,
        n_results: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Search for documents using semantic search.
        
        Args:
            query: Search query
            n_results: Number of results to return
            
        Returns:
            List of search results with scores
        """
        try:
            # Perform search using document retrieval
            results = await self.doc_retrieval.search(query, n_results)
            return results
        except Exception as e:
            self.logger.error(f"Error searching documents: {str(e)}")
            return []

    def get_document(self, doc_id: str) -> Dict[str, Any]:
        """
        Get document metadata by ID.
        
        Args:
            doc_id: Document ID
            
        Returns:
            Document metadata
            
        Raises:
            DocumentNotFoundError: If document not found
        """
        if doc_id not in self.metadata:
            raise DocumentNotFoundError(f"Document not found: {doc_id}")
        
        metadata = self.metadata[doc_id]
        return {
            "id": doc_id,
            "metadata": {
                "title": metadata["title"],
                "document_type": metadata["document_type"],
                "jurisdiction": metadata["jurisdiction"],
                "version": metadata["version"],
                "categories": metadata.get("categories", []),
                "description": metadata.get("description", ""),
                "upload_date": metadata["upload_date"],
                "file_type": metadata["file_type"]
            },
            "content": metadata["content"]
        }

    def update_document_metadata(self, doc_id: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update document metadata.
        
        Args:
            doc_id: Document ID
            metadata: Updated metadata fields
            
        Returns:
            Updated document metadata
            
        Raises:
            DocumentNotFoundError: If document not found
        """
        if doc_id not in self.metadata:
            raise DocumentNotFoundError(f"Document not found: {doc_id}")
        
        # Update metadata
        self.metadata[doc_id].update(metadata)
        self._save_metadata()
        
        # Update search index
        self.doc_retrieval.update_document_metadata(doc_id, metadata)
        
        return self.metadata[doc_id]

    def delete_document(self, doc_id: str):
        """
        Delete a document and its metadata.
        
        Args:
            doc_id: Document ID
            
        Raises:
            DocumentNotFoundError: If document not found
        """
        if doc_id not in self.metadata:
            raise DocumentNotFoundError(f"Document not found: {doc_id}")
        
        # Delete file
        file_path = Path(self.metadata[doc_id]["file_path"])
        if file_path.exists():
            file_path.unlink()
        
        # Delete metadata
        del self.metadata[doc_id]
        self._save_metadata()
        
        # Remove from search index
        self.doc_retrieval.delete_document(doc_id)
