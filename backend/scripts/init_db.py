import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.document_retrieval import DocumentRetrieval
from app.database import Database
import json

def init_database():
    """Initialize the database and index sample documents"""
    print("Initializing document retrieval system...")
    doc_retrieval = DocumentRetrieval()
    
    # Create data directories if they don't exist
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
    docs_dir = os.path.join(data_dir, 'documents')
    os.makedirs(docs_dir, exist_ok=True)
    
    # Index all documents in the documents directory
    print("Indexing documents...")
    doc_retrieval.bulk_index_documents(docs_dir)
    print("Document indexing complete!")

if __name__ == "__main__":
    init_database()
