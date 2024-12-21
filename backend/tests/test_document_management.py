import pytest
from datetime import datetime
import os
import shutil
from pathlib import Path
from fastapi import HTTPException, UploadFile
from app.document_management import DocumentManager
import json

@pytest.fixture
def doc_manager():
    """Create a test document manager with a temporary directory"""
    test_dir = Path("test_documents")
    if test_dir.exists():
        shutil.rmtree(test_dir)
    test_dir.mkdir(parents=True)
    manager = DocumentManager(base_dir=str(test_dir))
    manager._ensure_directory_exists()  # Ensure all subdirectories exist
    yield manager
    # Cleanup after tests
    if test_dir.exists():
        shutil.rmtree(test_dir)

@pytest.fixture
def sample_document():
    return {
        "content": "This is a test regulatory document about medical devices.",
        "metadata": {
            "title": "Test Regulation",
            "description": "Test description",
            "document_type": "Regulatory Guideline",
            "jurisdiction": "EU",
            "version": "1.0",
            "effective_date": datetime.utcnow().isoformat(),
            "categories": ["Medical Devices"],
            "tags": ["test", "medical_devices"]
        }
    }

@pytest.fixture
def sample_txt(doc_manager):
    """Create a sample text file for testing"""
    file_path = doc_manager.base_dir / "test.txt"
    with open(file_path, "w") as f:
        f.write("Test content for text extraction")
    return file_path

def test_init(doc_manager):
    """Test document manager initialization"""
    assert doc_manager.base_dir.exists()
    assert (doc_manager.base_dir / "uploads").exists()
    assert (doc_manager.base_dir / "versions").exists()
    assert (doc_manager.base_dir / "previews").exists()
    assert doc_manager.metadata_file.exists()

@pytest.mark.asyncio
async def test_upload_document(doc_manager, sample_document):
    """Test uploading a document"""
    # Create a test file
    test_file = doc_manager.base_dir / "test.txt"
    with open(test_file, "w") as f:
        f.write(sample_document["content"])
    
    # Create UploadFile object
    with open(test_file, "rb") as f:
        upload_file = UploadFile(
            filename="test.txt",
            file=f
        )
        
        # Upload document
        doc_id = await doc_manager.upload_document(
            file=upload_file,
            title=sample_document["metadata"]["title"],
            document_type=sample_document["metadata"]["document_type"],
            jurisdiction=sample_document["metadata"]["jurisdiction"],
            version=sample_document["metadata"]["version"],
            effective_date=sample_document["metadata"]["effective_date"],
            categories=sample_document["metadata"]["categories"],
            tags=sample_document["metadata"]["tags"]
        )
        assert doc_id is not None
    
    # Verify storage
    metadata = doc_manager._load_metadata()
    assert doc_id in metadata
    assert metadata[doc_id]["title"] == sample_document["metadata"]["title"]

@pytest.mark.asyncio
async def test_get_document(doc_manager, sample_document):
    """Test retrieving a document"""
    # Upload a document first
    test_file = doc_manager.base_dir / "test.txt"
    with open(test_file, "w") as f:
        f.write(sample_document["content"])
    
    with open(test_file, "rb") as f:
        upload_file = UploadFile(
            filename="test.txt",
            file=f
        )
        doc_id = await doc_manager.upload_document(
            file=upload_file,
            title=sample_document["metadata"]["title"],
            document_type=sample_document["metadata"]["document_type"],
            jurisdiction=sample_document["metadata"]["jurisdiction"],
            version=sample_document["metadata"]["version"],
            effective_date=sample_document["metadata"]["effective_date"],
            categories=sample_document["metadata"]["categories"],
            tags=sample_document["metadata"]["tags"]
        )
    
    # Get document
    doc = doc_manager.get_document_metadata(doc_id)
    assert doc is not None
    assert doc["title"] == sample_document["metadata"]["title"]
    assert doc["document_type"] == sample_document["metadata"]["document_type"]

@pytest.mark.asyncio
async def test_list_documents(doc_manager, sample_document):
    """Test listing documents with filters"""
    # Upload multiple documents
    doc_ids = []
    for i in range(3):
        test_file = doc_manager.base_dir / f"test_{i}.txt"
        with open(test_file, "w") as f:
            f.write(sample_document["content"])
        
        with open(test_file, "rb") as f:
            upload_file = UploadFile(
                filename=f"test_{i}.txt",
                file=f
            )
            metadata = sample_document["metadata"].copy()
            metadata["title"] = f"Test Document {i}"
            doc_id = await doc_manager.upload_document(
                file=upload_file,
                title=metadata["title"],
                document_type=metadata["document_type"],
                jurisdiction=metadata["jurisdiction"],
                version=metadata["version"],
                effective_date=metadata["effective_date"],
                categories=metadata["categories"],
                tags=metadata["tags"]
            )
            doc_ids.append(doc_id)
    
    # Test listing with filters
    docs = doc_manager.list_documents(
        document_type="Regulatory Guideline",
        jurisdiction="EU"
    )
    assert len(docs) >= 3
    
    # Test listing with category filter
    docs = doc_manager.list_documents(category="Medical Devices")
    assert len(docs) >= 3

@pytest.mark.asyncio
async def test_delete_document(doc_manager, sample_document):
    """Test deleting a document"""
    # Upload a document first
    test_file = doc_manager.base_dir / "test.txt"
    with open(test_file, "w") as f:
        f.write(sample_document["content"])
    
    with open(test_file, "rb") as f:
        upload_file = UploadFile(
            filename="test.txt",
            file=f
        )
        doc_id = await doc_manager.upload_document(
            file=upload_file,
            title=sample_document["metadata"]["title"],
            document_type=sample_document["metadata"]["document_type"],
            jurisdiction=sample_document["metadata"]["jurisdiction"],
            version=sample_document["metadata"]["version"],
            effective_date=sample_document["metadata"]["effective_date"],
            categories=sample_document["metadata"]["categories"],
            tags=sample_document["metadata"]["tags"]
        )
    
    # Delete document
    doc_manager.delete_document(doc_id)
    
    # Verify deletion
    metadata = doc_manager._load_metadata()
    assert doc_id not in metadata

def test_extract_text_content(doc_manager, sample_txt):
    """Test text extraction from different file types"""
    # Test TXT extraction
    text = doc_manager._extract_text_content(sample_txt)
    assert "Test content" in text

def test_invalid_document_id(doc_manager):
    """Test operations with invalid document ID"""
    invalid_id = "nonexistent_id"
    
    # Test get_document with invalid ID
    doc = doc_manager.get_document_metadata(invalid_id)
    assert doc is None
    
    # Test delete_document with invalid ID
    with pytest.raises(HTTPException) as exc_info:
        doc_manager.delete_document(invalid_id)
    assert exc_info.value.status_code == 404

@pytest.mark.asyncio
async def test_upload_invalid_file_type(doc_manager):
    """Test uploading a file with invalid extension"""
    test_file = doc_manager.base_dir / "test.invalid"
    with open(test_file, "w") as f:
        f.write("Invalid file content")
    
    with open(test_file, "rb") as f:
        upload_file = UploadFile(
            filename="test.invalid",
            file=f
        )
        with pytest.raises(HTTPException) as exc_info:
            await doc_manager.upload_document(
                file=upload_file,
                title="Invalid File",
                document_type="Test",
                jurisdiction="EU",
                version="1.0",
                effective_date=datetime.utcnow().isoformat()
            )
        assert exc_info.value.status_code == 400
        assert "Invalid file type" in str(exc_info.value.detail)

@pytest.mark.asyncio
async def test_upload_large_file(doc_manager):
    """Test uploading a file exceeding size limit"""
    # Create a large file (11MB)
    test_file = doc_manager.base_dir / "large.txt"
    with open(test_file, "wb") as f:
        f.write(b"0" * (11 * 1024 * 1024))
    
    with open(test_file, "rb") as f:
        upload_file = UploadFile(
            filename="large.txt",
            file=f
        )
        with pytest.raises(HTTPException) as exc_info:
            await doc_manager.upload_document(
                file=upload_file,
                title="Large File",
                document_type="Test",
                jurisdiction="EU",
                version="1.0",
                effective_date=datetime.utcnow().isoformat()
            )
        assert exc_info.value.status_code == 400
        assert "File size exceeds limit" in str(exc_info.value.detail)

@pytest.mark.asyncio
async def test_document_versioning(doc_manager, sample_document):
    """Test document versioning functionality"""
    # Upload initial version
    test_file = doc_manager.base_dir / "test.txt"
    with open(test_file, "w") as f:
        f.write(sample_document["content"])
    
    with open(test_file, "rb") as f:
        upload_file = UploadFile(
            filename="test.txt",
            file=f
        )
        doc_id = await doc_manager.upload_document(
            file=upload_file,
            title=sample_document["metadata"]["title"],
            document_type=sample_document["metadata"]["document_type"],
            jurisdiction=sample_document["metadata"]["jurisdiction"],
            version="1.0",
            effective_date=datetime.utcnow().isoformat()
        )
    
    # Upload new version
    with open(test_file, "w") as f:
        f.write(sample_document["content"] + "\nUpdated content")
    
    with open(test_file, "rb") as f:
        upload_file = UploadFile(
            filename="test.txt",
            file=f
        )
        new_doc_id = await doc_manager.upload_document(
            file=upload_file,
            title=sample_document["metadata"]["title"],
            document_type=sample_document["metadata"]["document_type"],
            jurisdiction=sample_document["metadata"]["jurisdiction"],
            version="2.0",
            effective_date=datetime.utcnow().isoformat(),
            previous_version=doc_id
        )
    
    # Verify versioning
    metadata = doc_manager._load_metadata()
    assert metadata[new_doc_id]["previous_version"] == doc_id
    assert metadata[new_doc_id]["version"] == "2.0"

@pytest.mark.asyncio
async def test_concurrent_uploads(doc_manager, sample_document):
    """Test handling concurrent document uploads"""
    import asyncio
    
    async def upload_doc(index):
        test_file = doc_manager.base_dir / f"test_{index}.txt"
        with open(test_file, "w") as f:
            f.write(f"{sample_document['content']} {index}")
        
        with open(test_file, "rb") as f:
            upload_file = UploadFile(
                filename=f"test_{index}.txt",
                file=f
            )
            return await doc_manager.upload_document(
                file=upload_file,
                title=f"Test Document {index}",
                document_type=sample_document["metadata"]["document_type"],
                jurisdiction=sample_document["metadata"]["jurisdiction"],
                version=f"1.{index}",
                effective_date=datetime.utcnow().isoformat()
            )
    
    # Upload 5 documents concurrently
    doc_ids = await asyncio.gather(*[upload_doc(i) for i in range(5)])
    
    # Verify all uploads succeeded
    assert len(doc_ids) == 5
    assert len(set(doc_ids)) == 5  # All IDs should be unique
    
    # Verify all documents are in metadata
    metadata = doc_manager._load_metadata()
    for doc_id in doc_ids:
        assert doc_id in metadata

@pytest.mark.asyncio
async def test_update_document_metadata(doc_manager, sample_document):
    """Test updating document metadata"""
    # Upload initial document
    test_file = doc_manager.base_dir / "test.txt"
    with open(test_file, "w") as f:
        f.write(sample_document["content"])
    
    with open(test_file, "rb") as f:
        upload_file = UploadFile(
            filename="test.txt",
            file=f
        )
        doc_id = await doc_manager.upload_document(
            file=upload_file,
            title=sample_document["metadata"]["title"],
            document_type=sample_document["metadata"]["document_type"],
            jurisdiction=sample_document["metadata"]["jurisdiction"],
            version="1.0",
            effective_date=datetime.utcnow().isoformat()
        )
    
    # Update metadata
    new_title = "Updated Title"
    new_tags = ["updated", "test"]
    doc_manager.update_document_metadata(
        doc_id,
        title=new_title,
        tags=new_tags
    )
    
    # Verify update
    metadata = doc_manager._load_metadata()
    assert metadata[doc_id]["title"] == new_title
    assert metadata[doc_id]["tags"] == new_tags

@pytest.mark.asyncio
async def test_document_search(doc_manager, sample_document):
    """Test document search functionality"""
    # Upload documents with different content
    docs_content = [
        "Medical device regulation in the EU",
        "FDA guidelines for biotech products",
        "ISO standards for medical equipment"
    ]

    for content in docs_content:
        test_file = doc_manager.base_dir / f"test_{content[:10]}.txt"
        with open(test_file, "w") as f:
            f.write(content)

        with open(test_file, "rb") as f:
            upload_file = UploadFile(
                filename=test_file.name,
                file=f
            )
            await doc_manager.upload_document(
                file=upload_file,
                title=content,  # Use full content as title
                document_type="Regulatory",
                jurisdiction="Global",
                version="1.0",
                effective_date=datetime.utcnow().isoformat()
            )

    # Search for documents
    results = doc_manager.search_documents("medical device regulation")
    assert len(results) >= 1
    assert any("medical device" in result["content"].lower() for result in results)

    # Search for FDA documents
    results = doc_manager.search_documents("FDA guidelines")
    assert len(results) >= 1
    
    # Debug print
    print("\nSearch Results Structure:")
    print(json.dumps(results, indent=2))
    
    # Check if any result contains the FDA document
    assert any("FDA guidelines for biotech products" == result["content"] for result in results), \
        f"Expected to find FDA guidelines document in results"

def test_cleanup_on_upload_failure(doc_manager):
    """Test that temporary files are cleaned up on upload failure"""
    test_file = doc_manager.base_dir / "test.txt"
    with open(test_file, "w") as f:
        f.write("Test content")
    
    initial_files = set(os.listdir(doc_manager.base_dir))
    
    # Simulate upload failure
    with pytest.raises(Exception):
        with open(test_file, "rb") as f:
            upload_file = UploadFile(
                filename="test.txt",
                file=f
            )
            doc_manager._save_file(upload_file, raise_error=True)
    
    # Verify no temporary files were left
    current_files = set(os.listdir(doc_manager.base_dir))
    assert current_files == initial_files
