import os
import shutil
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from app.main import app, get_document_manager
from app.document_retrieval import DocumentRetrieval
from app.document_management import DocumentManager

client = TestClient(app)

@pytest.fixture(scope="module")
def test_file():
    """Create a test document and clean up ChromaDB"""
    # Set up test directories
    test_dir = Path("backend/tests/test_documents")
    test_dir.mkdir(exist_ok=True)
    
    chroma_test_dir = Path("backend/tests/test_chroma")
    if chroma_test_dir.exists():
        shutil.rmtree(chroma_test_dir)
    chroma_test_dir.mkdir(exist_ok=True)
    
    # Create test document
    test_file = test_dir / "test_document.txt"
    with open(test_file, "w", encoding="utf-8") as f:
        f.write("This is a test document about FDA regulations")
    
    yield test_file
    
    # Cleanup
    if test_dir.exists():
        shutil.rmtree(test_dir)
    if chroma_test_dir.exists():
        shutil.rmtree(chroma_test_dir)

@pytest.fixture(scope="module")
def test_doc_retrieval():
    """Create a test DocumentRetrieval instance"""
    chroma_test_dir = Path("backend/tests/test_chroma")
    return DocumentRetrieval(persist_dir=str(chroma_test_dir))

@pytest.fixture(scope="module")
def test_doc_manager(test_doc_retrieval):
    """Create a test DocumentManager instance"""
    return DocumentManager(doc_retrieval=test_doc_retrieval)

@pytest.fixture(autouse=True)
def override_dependencies(test_doc_manager):
    """Override dependencies for testing"""
    app.dependency_overrides[get_document_manager] = lambda: test_doc_manager

def test_upload_and_search_workflow(test_file):
    """Test the complete document upload and search workflow"""
    # Step 1: Upload document
    with open(test_file, "rb") as f:
        response = client.post(
            "/documents/upload",
            files={"file": ("test_document.txt", f, "text/plain")},
            data={
                "title": "FDA Test Document",
                "document_type": "Regulatory",
                "jurisdiction": "US",
                "version": "1.0"
            }
        )
    assert response.status_code == 200
    doc_id = response.json()["id"]
    
    # Step 2: Verify document metadata
    response = client.get(f"/documents/{doc_id}")
    assert response.status_code == 200
    doc_data = response.json()
    assert doc_data["metadata"]["title"] == "FDA Test Document"
    assert doc_data["metadata"]["document_type"] == "Regulatory"
    
    # Step 3: Search for the document
    response = client.get("/documents/search", params={"query": "FDA regulations"})
    assert response.status_code == 200
    results = response.json()
    assert len(results) >= 1
    assert any("FDA" in result["content"] for result in results)
    
    # Step 4: Update document metadata
    new_metadata = {
        "title": "Updated FDA Document",
        "document_type": "Guidelines",
        "jurisdiction": "US",
        "version": "1.1"
    }
    response = client.put(
        f"/documents/{doc_id}/metadata",
        json=new_metadata
    )
    assert response.status_code == 200
    
    # Step 5: Verify updated metadata
    response = client.get(f"/documents/{doc_id}")
    assert response.status_code == 200
    updated_doc = response.json()
    assert updated_doc["metadata"]["title"] == "Updated FDA Document"
    assert updated_doc["metadata"]["version"] == "1.1"
    
    # Step 6: Delete document
    response = client.delete(f"/documents/{doc_id}")
    assert response.status_code == 200
    
    # Step 7: Verify deletion
    response = client.get(f"/documents/{doc_id}")
    assert response.status_code == 404

def test_document_list_and_filter():
    """Test document listing and filtering functionality"""
    # Upload multiple test documents
    test_docs = [
        {
            "content": "FDA guidelines for medical devices",
            "metadata": {
                "title": "FDA Guidelines",
                "document_type": "Regulatory",
                "jurisdiction": "US"
            }
        },
        {
            "content": "EMA requirements for biotech products",
            "metadata": {
                "title": "EMA Requirements",
                "document_type": "Requirements",
                "jurisdiction": "EU"
            }
        }
    ]
    
    doc_ids = []
    for doc in test_docs:
        test_file = Path("backend/tests/test_documents") / "temp.txt"
        test_file.parent.mkdir(exist_ok=True)
        with open(test_file, "w") as f:
            f.write(doc["content"])
            
        with open(test_file, "rb") as f:
            response = client.post(
                "/documents/upload",
                files={"file": ("temp.txt", f, "text/plain")},
                data=doc["metadata"]
            )
        assert response.status_code == 200
        doc_ids.append(response.json()["id"])
    
    # Test listing all documents
    response = client.get("/documents")
    assert response.status_code == 200
    docs = response.json()
    assert len(docs) >= 2
    
    # Test filtering by jurisdiction
    response = client.get("/documents", params={"jurisdiction": "US"})
    assert response.status_code == 200
    us_docs = response.json()
    assert all(doc["metadata"]["jurisdiction"] == "US" for doc in us_docs)
    
    # Test filtering by document type
    response = client.get("/documents", params={"document_type": "Regulatory"})
    assert response.status_code == 200
    reg_docs = response.json()
    assert all(doc["metadata"]["document_type"] == "Regulatory" for doc in reg_docs)
    
    # Cleanup
    for doc_id in doc_ids:
        client.delete(f"/documents/{doc_id}")

def test_error_handling():
    """Test API error handling"""
    # Test invalid document ID
    response = client.get("/documents/invalid_id")
    assert response.status_code == 404
    
    # Test invalid file type
    test_file = Path("backend/tests/test_documents") / "test.exe"
    test_file.parent.mkdir(exist_ok=True)
    with open(test_file, "wb") as f:
        f.write(b"invalid file content")
    
    with open(test_file, "rb") as f:
        response = client.post(
            "/documents/upload",
            files={"file": ("test.exe", f, "application/octet-stream")},
            data={
                "title": "Invalid File",
                "document_type": "Test",
                "jurisdiction": "US",
                "version": "1.0"
            }
        )
    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]
