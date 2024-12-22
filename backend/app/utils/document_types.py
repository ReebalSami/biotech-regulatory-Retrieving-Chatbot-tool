from enum import Enum
from typing import List, Optional, Any
from pydantic import BaseModel
from datetime import datetime

class DocumentType(str, Enum):
    REFERENCE = "REFERENCE"
    USER_ATTACHMENT = "USER_ATTACHMENT"

class DocumentMetadata(BaseModel):
    id: str
    filename: str
    title: str
    description: Optional[str] = None
    categories: List[str] = []
    document_type: str
    chat_id: Optional[str] = None
    upload_date: str
    file_path: str

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "filename": self.filename,
            "title": self.title,
            "description": self.description,
            "categories": self.categories,
            "document_type": self.document_type,
            "chat_id": self.chat_id,
            "upload_date": self.upload_date,
            "file_path": self.file_path
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DocumentMetadata":
        return cls(**data)
