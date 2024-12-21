import pytest
import os
from io import BytesIO
from app.utils.file_handler import validate_file, save_file, get_file_metadata
from app.utils.exceptions import InvalidFileTypeError, FileSizeLimitError
from app.config import get_settings

settings = get_settings()

def test_validate_file_pdf(sample_pdf):
    """Test PDF file validation"""
    with open(sample_pdf, 'rb') as f:
        content = f.read()
        file = BytesIO(content)
        content_type, file_content = validate_file(file, "test.pdf")
        assert content_type == "application/pdf"
        assert file_content == content

def test_validate_file_size_limit():
    """Test file size limit validation"""
    # Create a file larger than the limit
    content = b"x" * (settings.MAX_UPLOAD_SIZE + 1)
    file = BytesIO(content)
    
    with pytest.raises(FileSizeLimitError):
        validate_file(file, "test.txt")

def test_validate_file_invalid_type():
    """Test invalid file type validation"""
    # Create a Windows PE executable header
    content = (
        b"MZ"  # DOS header
        b"\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xFF\xFF\x00\x00"  # DOS stub
        b"\xB8\x00\x00\x00\x00\x00\x00\x00\x40\x00\x00\x00"  # PE header
        b"\x0E\x1F\xBA\x0E\x00\xB4\x09\xCD\x21\xB8\x01\x4C\xCD\x21"  # More DOS stub
    )
    file = BytesIO(content)
    
    with pytest.raises(InvalidFileTypeError):
        validate_file(file, "test.exe")

def test_save_file(temp_upload_dir):
    """Test file saving functionality"""
    content = b"test content"
    filename = "test.txt"
    
    file_path = save_file(content, filename, temp_upload_dir)
    
    assert os.path.exists(file_path)
    with open(file_path, 'rb') as f:
        saved_content = f.read()
        assert saved_content == content

def test_get_file_metadata(temp_upload_dir):
    """Test file metadata retrieval"""
    content = b"test content"
    filename = "test.txt"
    file_path = save_file(content, filename, temp_upload_dir)
    
    metadata = get_file_metadata(file_path)
    
    assert metadata['size'] == len(content)
    assert metadata['filename'] == os.path.basename(file_path)
    assert 'created' in metadata
    assert 'modified' in metadata
    assert 'path' in metadata

def test_save_file_creates_directory(temp_upload_dir):
    """Test directory creation when saving file"""
    nested_dir = os.path.join(temp_upload_dir, "nested", "dir")
    content = b"test content"
    filename = "test.txt"
    
    file_path = save_file(content, filename, nested_dir)
    
    assert os.path.exists(file_path)
    assert os.path.isdir(nested_dir)
