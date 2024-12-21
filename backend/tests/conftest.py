import pytest
from fastapi.testclient import TestClient
from mongomock import MongoClient
import os
import tempfile
from app.main import app
from app.database import db
from app.document_retrieval import DocumentRetrieval

@pytest.fixture
def test_app():
    """
    Create a test client using the FastAPI app
    """
    client = TestClient(app)
    return client

@pytest.fixture
def mock_db(monkeypatch):
    """
    Replace MongoDB client with a mock for testing
    """
    mock_client = MongoClient()
    mock_db = mock_client.db
    monkeypatch.setattr(db, "client", mock_client)
    monkeypatch.setattr(db, "db", mock_db)
    return mock_db

@pytest.fixture
def temp_upload_dir():
    """
    Create a temporary directory for file uploads during tests
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        original_upload_dir = os.getenv("UPLOAD_DIR", "user_documents")
        os.environ["UPLOAD_DIR"] = temp_dir
        yield temp_dir
        os.environ["UPLOAD_DIR"] = original_upload_dir

@pytest.fixture
def sample_pdf():
    """
    Create a sample PDF file for testing
    """
    content = b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj 3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R>>endobj\nxref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000052 00000 n\n0000000101 00000 n\ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n178\n%%EOF\n"
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
        temp_file.write(content)
        temp_file.flush()
        yield temp_file.name
        os.unlink(temp_file.name)

@pytest.fixture
def sample_docx():
    """
    Create a sample DOCX file for testing
    """
    content = b"PK\x03\x04\x14\x00\x00\x00\x08\x00\x00\x00!\"Test Document\""
    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as temp_file:
        temp_file.write(content)
        temp_file.flush()
        yield temp_file.name
        os.unlink(temp_file.name)

@pytest.fixture
def mock_document_retrieval(monkeypatch):
    """
    Mock DocumentRetrieval for testing
    """
    class MockDocumentRetrieval:
        def __init__(self):
            self.documents = {}
        
        def index_document(self, document):
            doc_id = "test_doc_id"
            self.documents[doc_id] = document
            return doc_id
        
        def search(self, query, n_results=5):
            return list(self.documents.values())[:n_results]
    
    mock = MockDocumentRetrieval()
    monkeypatch.setattr("app.main.DocumentRetrieval", lambda: mock)
    return mock
