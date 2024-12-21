from fastapi import HTTPException
from typing import Any, Dict, Optional

class DocumentError(HTTPException):
    def __init__(
        self,
        detail: str,
        status_code: int = 400,
        headers: Optional[Dict[str, Any]] = None
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)

class DocumentNotFoundError(DocumentError):
    def __init__(self, document_id: str):
        super().__init__(
            status_code=404,
            detail=f"Document with ID {document_id} not found"
        )

class DocumentIndexingError(DocumentError):
    def __init__(self, detail: str):
        super().__init__(
            status_code=500,
            detail=f"Error indexing document: {detail}"
        )

class InvalidFileTypeError(DocumentError):
    def __init__(self, file_type: str):
        super().__init__(
            status_code=400,
            detail=f"Invalid file type: {file_type}. Supported types are: pdf, docx, txt"
        )

class FileSizeLimitError(DocumentError):
    def __init__(self, file_size: int, max_size: int):
        super().__init__(
            status_code=400,
            detail=f"File size {file_size} bytes exceeds maximum size of {max_size} bytes"
        )
