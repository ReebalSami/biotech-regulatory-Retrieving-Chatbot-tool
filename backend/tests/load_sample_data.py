"""Script to load sample data into the database"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.document_retrieval import DocumentRetrieval
from sample_data import sample_documents

def load_sample_data():
    doc_retrieval = DocumentRetrieval()
    
    print("Loading sample documents...")
    for doc in sample_documents:
        doc_id = doc_retrieval.index_document(doc)
        print(f"✓ Indexed document: {doc['metadata']['title']}")
    
    print("\nSample data loaded successfully!")

if __name__ == "__main__":
    load_sample_data()
