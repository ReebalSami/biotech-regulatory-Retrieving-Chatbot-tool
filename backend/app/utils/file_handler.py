from typing import BinaryIO, Tuple
import magic
import os
from app.utils.exceptions import InvalidFileTypeError, FileSizeLimitError
from app.utils.logger import setup_logger
from app.config import get_settings

logger = setup_logger(__name__)
settings = get_settings()

def validate_file(file: BinaryIO, filename: str) -> Tuple[str, bytes]:
    """
    Validate file type and size, return content type and file content
    
    Args:
        file: File-like object
        filename: Original filename
    
    Returns:
        Tuple of (content_type, file_content)
        
    Raises:
        InvalidFileTypeError: If file type is not allowed
        FileSizeLimitError: If file size exceeds limit
    """
    # Read file content
    content = file.read()
    file_size = len(content)
    
    # Check file size
    if file_size > settings.MAX_UPLOAD_SIZE:
        logger.warning(f"File size {file_size} exceeds limit of {settings.MAX_UPLOAD_SIZE}")
        raise FileSizeLimitError(file_size, settings.MAX_UPLOAD_SIZE)
    
    # Detect file type using python-magic
    mime = magic.Magic(mime=True)
    content_type = mime.from_buffer(content)
    
    # Map MIME types to extensions
    mime_to_ext = {
        'application/pdf': 'pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
        'text/plain': 'txt'
    }
    
    # Get file extension from content type
    detected_ext = mime_to_ext.get(content_type)
    if not detected_ext or detected_ext not in settings.ALLOWED_EXTENSIONS:
        logger.warning(f"Invalid file type: {content_type} for file {filename}")
        raise InvalidFileTypeError(content_type)
    
    logger.info(f"File validation successful: {filename} ({content_type}, {file_size} bytes)")
    return content_type, content

def save_file(content: bytes, filename: str, directory: str = "uploads") -> str:
    """
    Save file content to disk
    
    Args:
        content: File content
        filename: Original filename
        directory: Target directory (relative to project root)
        
    Returns:
        Path to saved file
    """
    # Create directory if it doesn't exist
    os.makedirs(directory, exist_ok=True)
    
    # Generate unique filename
    base, ext = os.path.splitext(filename)
    unique_filename = f"{base}_{os.urandom(4).hex()}{ext}"
    file_path = os.path.join(directory, unique_filename)
    
    # Save file
    try:
        with open(file_path, 'wb') as f:
            f.write(content)
        logger.info(f"File saved successfully: {file_path}")
        return file_path
    except Exception as e:
        logger.error(f"Error saving file {filename}: {str(e)}")
        raise

def get_file_metadata(file_path: str) -> dict:
    """
    Get file metadata
    
    Args:
        file_path: Path to file
        
    Returns:
        Dictionary containing file metadata
    """
    try:
        stats = os.stat(file_path)
        return {
            'size': stats.st_size,
            'created': stats.st_ctime,
            'modified': stats.st_mtime,
            'path': file_path,
            'filename': os.path.basename(file_path)
        }
    except Exception as e:
        logger.error(f"Error getting metadata for {file_path}: {str(e)}")
        raise
