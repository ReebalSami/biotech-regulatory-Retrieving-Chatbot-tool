from typing import List, Optional, Dict
from datetime import datetime
from fastapi import UploadFile, HTTPException
import os
import shutil
from pathlib import Path
import json
import PyPDF2
from docx import Document as DocxDocument
import hashlib
from .document_retrieval import DocumentRetrieval

class DocumentManager:
    def __init__(self, base_dir: str = "documents"):
        self.base_dir = Path(base_dir)
        self.metadata_file = self.base_dir / "metadata.json"
        self.document_retrieval = DocumentRetrieval()
        self._ensure_directory_exists()
        self._load_metadata()

    def _ensure_directory_exists(self):
        """Ensure all necessary directories exist"""
        self.base_dir.mkdir(parents=True, exist_ok=True)
        (self.base_dir / "uploads").mkdir(exist_ok=True)
        (self.base_dir / "versions").mkdir(exist_ok=True)
        (self.base_dir / "previews").mkdir(exist_ok=True)
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
                    return file.read()
            else:
                raise ValueError(f"Unsupported file type: {file_path.suffix}")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error extracting text: {str(e)}")

    def _create_preview(self, file_path: Path, doc_id: str) -> str:
        """Create a preview of the document"""
        preview_path = self.base_dir / "previews" / f"{doc_id}.txt"
        try:
            content = self._extract_text_content(file_path)
            # Save first 1000 characters as preview
            with open(preview_path, 'w', encoding='utf-8') as f:
                f.write(content[:1000])
            return str(preview_path)
        except Exception as e:
            print(f"Error creating preview: {str(e)}")
            return ""

    async def upload_document(self, 
                            file: UploadFile, 
                            title: str,
                            document_type: str,
                            jurisdiction: str,
                            version: str,
                            effective_date: str,
                            categories: List[str] = None,
                            tags: List[str] = None) -> Dict:
        """Upload a new document with metadata and versioning"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_filename = f"{timestamp}_{file.filename.replace(' ', '_')}"
            file_path = self.base_dir / "uploads" / safe_filename

            # Save file
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            # Calculate file hash
            file_hash = self._calculate_file_hash(file_path)
            
            # Load existing metadata
            metadata = self._load_metadata()
            
            # Check if this is a new version of an existing document
            existing_doc_id = None
            for doc_id, doc in metadata.items():
                if doc["title"] == title and doc["document_type"] == document_type:
                    existing_doc_id = doc_id
                    break

            if existing_doc_id:
                # Move current version to versions directory
                current_file = Path(metadata[existing_doc_id]["file_path"])
                if current_file.exists():
                    version_dir = self.base_dir / "versions" / existing_doc_id
                    version_dir.mkdir(exist_ok=True)
                    shutil.move(
                        current_file,
                        version_dir / f"v{metadata[existing_doc_id]['version']}_{current_file.name}"
                    )
                doc_id = existing_doc_id
            else:
                doc_id = f"doc_{timestamp}"

            # Create preview
            preview_path = self._create_preview(file_path, doc_id)

            # Extract text content for search
            content = self._extract_text_content(file_path)

            # Update metadata
            metadata[doc_id] = {
                "title": title,
                "original_filename": file.filename,
                "stored_filename": safe_filename,
                "document_type": document_type,
                "jurisdiction": jurisdiction,
                "version": version,
                "effective_date": effective_date,
                "upload_date": datetime.now().isoformat(),
                "file_path": str(file_path),
                "preview_path": preview_path,
                "file_hash": file_hash,
                "categories": categories or [],
                "tags": tags or [],
                "versions": metadata.get(doc_id, {}).get("versions", []) + [{
                    "version": version,
                    "upload_date": datetime.now().isoformat(),
                    "file_hash": file_hash
                }]
            }
            self._save_metadata(metadata)

            # Index document for search
            self.document_retrieval.add_document(
                doc_id=doc_id,
                content=content,
                metadata={
                    "title": title,
                    "document_type": document_type,
                    "jurisdiction": jurisdiction,
                    "version": version,
                    "effective_date": effective_date,
                    "categories": categories or [],
                    "tags": tags or []
                }
            )

            return metadata[doc_id]

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error uploading document: {str(e)}")

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

    def _save_metadata(self, metadata: dict):
        """Save metadata to JSON file"""
        with open(self.metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)

    def _load_metadata(self) -> dict:
        """Load metadata from JSON file"""
        try:
            with open(self.metadata_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    # Existing methods remain unchanged
    def get_document_metadata(self, doc_id: str) -> Optional[Dict]:
        """Get metadata for a specific document"""
        metadata = self._load_metadata()
        return metadata.get(doc_id)

    def list_documents(self, 
                      document_type: Optional[str] = None,
                      jurisdiction: Optional[str] = None,
                      category: Optional[str] = None,
                      tag: Optional[str] = None) -> List[Dict]:
        """List all documents with optional filtering"""
        metadata = self._load_metadata()
        documents = []

        for doc_id, doc_metadata in metadata.items():
            if document_type and doc_metadata["document_type"] != document_type:
                continue
            if jurisdiction and doc_metadata["jurisdiction"] != jurisdiction:
                continue
            if category and category not in doc_metadata.get("categories", []):
                continue
            if tag and tag not in doc_metadata.get("tags", []):
                continue
            doc_metadata["id"] = doc_id
            documents.append(doc_metadata)

        return sorted(documents, key=lambda x: x["upload_date"], reverse=True)

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
        version_dir = self.base_dir / "versions" / doc_id
        if version_dir.exists():
            shutil.rmtree(version_dir)

        # Remove from metadata
        del metadata[doc_id]
        self._save_metadata(metadata)

        # Remove from search index
        self.document_retrieval.delete_document(doc_id)

    def update_document_metadata(self, doc_id: str, updates: Dict) -> Dict:
        """Update document metadata"""
        metadata = self._load_metadata()
        if doc_id not in metadata:
            raise HTTPException(status_code=404, detail="Document not found")

        # Update allowed fields
        allowed_fields = [
            "title", "document_type", "jurisdiction", 
            "version", "effective_date", "categories", "tags"
        ]
        for field in allowed_fields:
            if field in updates:
                metadata[doc_id][field] = updates[field]

        self._save_metadata(metadata)
        return metadata[doc_id]
