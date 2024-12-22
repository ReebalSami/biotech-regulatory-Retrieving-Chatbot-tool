"""Script to index existing documents in the system."""

import asyncio
import sys
import os
from pathlib import Path

# Add the parent directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from app.document_storage import DocumentStorage
from app.document_retrieval import DocumentRetrieval
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

async def index_all_documents():
    """Index all documents in the reference_documents directory."""
    try:
        # Initialize document storage and retrieval
        doc_storage = DocumentStorage()
        doc_retrieval = DocumentRetrieval()
        
        # Get list of all documents
        docs = await doc_storage.list_documents()
        logger.info(f"Found {len(docs)} documents to index")
        
        # Index each document
        for doc in docs:
            try:
                file_path = Path(doc.file_path)
                if not file_path.exists():
                    logger.warning(f"File not found: {file_path}")
                    continue
                    
                await doc_retrieval.index_document(
                    file_path=str(file_path),
                    doc_id=doc.id,
                    metadata={
                        "title": doc.title,
                        "document_type": doc.document_type,
                        "categories": doc.categories,
                        "description": doc.description
                    }
                )
                logger.info(f"Indexed document: {doc.title} ({doc.id})")
            except Exception as e:
                logger.error(f"Error indexing document {doc.id}: {str(e)}")
                continue
        
        # Save the index
        doc_retrieval.save_index()
        logger.info("Successfully saved search index")
        
    except Exception as e:
        logger.error(f"Error during indexing: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(index_all_documents())
