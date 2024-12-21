from typing import List, Dict, Any, Union
import chromadb
from chromadb.config import Settings
from app.database import db
import json
import os
from bson import ObjectId
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from app.utils.logger import setup_logger
from app.utils.exceptions import DocumentNotFoundError, DocumentIndexingError

logger = setup_logger(__name__)

class DocumentRetrieval:
    def __init__(self):
        # Create the persist directory if it doesn't exist
        persist_dir = "./data/chroma"
        os.makedirs(persist_dir, exist_ok=True)
        
        try:
            # Initialize ChromaDB with the new client configuration
            self.client = chromadb.PersistentClient(path=persist_dir)
            self.collection = self.client.get_or_create_collection(
                name="regulatory_documents",
                metadata={"hnsw:space": "cosine"}
            )
            logger.info("Successfully initialized ChromaDB client and collection")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {str(e)}")
            raise DocumentIndexingError("Failed to initialize document storage system")
        
        self.vectorizer = TfidfVectorizer(stop_words='english')
        self.document_vectors = None
        self.documents = []

    def _prepare_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Union[str, int, float, bool]]:
        """Convert metadata values to ChromaDB-compatible types"""
        try:
            prepared = {}
            for key, value in metadata.items():
                if isinstance(value, (str, int, float, bool)):
                    prepared[key] = value
                elif isinstance(value, list):
                    prepared[key] = ','.join(str(v) for v in value)
                elif value is None:
                    prepared[key] = ""
                else:
                    prepared[key] = str(value)
            return prepared
        except Exception as e:
            logger.error(f"Error preparing metadata: {str(e)}")
            raise DocumentIndexingError(f"Failed to prepare document metadata: {str(e)}")

    def index_document(self, document: Dict) -> str:
        """
        Index a new regulatory document in both ChromaDB and MongoDB
        """
        logger.info(f"Starting document indexing process for document: {document.get('title', 'Untitled')}")
        
        try:
            # Store in MongoDB
            doc_id = db.store_document(
                content=document["content"],
                metadata={
                    "title": document.get("title", ""),
                    "category": document.get("category", ""),
                    "source": document.get("source", ""),
                    "tags": document.get("tags", []),
                    "last_updated": document.get("last_updated", "")
                }
            )
            logger.debug(f"Document stored in MongoDB with ID: {doc_id}")

            # Prepare metadata for ChromaDB
            chroma_metadata = self._prepare_metadata({
                "source": doc_id,
                **document.get("metadata", {})
            })
            
            # Index in ChromaDB for semantic search
            self.collection.add(
                documents=[document["content"]],
                metadatas=[chroma_metadata],
                ids=[doc_id]
            )
            logger.info(f"Document successfully indexed in ChromaDB with ID: {doc_id}")
            
            return doc_id

        except Exception as e:
            logger.error(f"Error during document indexing: {str(e)}")
            # Clean up MongoDB document if ChromaDB indexing fails
            if 'doc_id' in locals():
                try:
                    if isinstance(doc_id, str):
                        doc_id = ObjectId(doc_id)
                    db.regulatory_documents.delete_one({'_id': doc_id})
                    logger.info(f"Cleaned up MongoDB document after failed ChromaDB indexing: {doc_id}")
                except Exception as cleanup_error:
                    logger.error(f"Error during cleanup: {str(cleanup_error)}")
            raise DocumentIndexingError(str(e))

    def search(self, query: str, n_results: int = 5) -> List[Dict]:
        """
        Search for relevant documents using semantic search
        """
        logger.info(f"Performing search with query: {query}")
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            documents = []
            for doc, meta, dist in zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0]
            ):
                documents.append({
                    "content": doc,
                    "metadata": meta,
                    "score": 1 - dist  # Convert distance to similarity score
                })
            
            logger.info(f"Search completed. Found {len(documents)} documents")
            return documents

        except Exception as e:
            logger.error(f"Error during document search: {str(e)}")
            raise DocumentIndexingError(f"Search operation failed: {str(e)}")

    def calculate_relevance(self, query: str, document_text: str) -> float:
        """Calculate relevance score between query and document text."""
        try:
            # Vectorize both texts
            vectors = self.vectorizer.fit_transform([query, document_text])
            
            # Calculate cosine similarity
            similarity = cosine_similarity(vectors[0:1], vectors[1:2])[0][0]
            
            return float(similarity)
        except Exception as e:
            logger.error(f"Error calculating relevance: {str(e)}")
            return 0.0

    def get_document_by_id(self, doc_id: str) -> Dict:
        """
        Retrieve a specific document by ID from MongoDB
        """
        try:
            return db.get_document(doc_id)
        except Exception as e:
            logger.error(f"Error retrieving document by ID: {str(e)}")
            raise DocumentNotFoundError(f"Document with ID {doc_id} not found")

    def delete_document(self, doc_id: str):
        """Delete a document from ChromaDB"""
        try:
            self.collection.delete(ids=[doc_id])
            logger.info(f"Document successfully deleted from ChromaDB: {doc_id}")
        except Exception as e:
            logger.error(f"Error deleting document from ChromaDB: {str(e)}")
            raise DocumentIndexingError(f"Failed to delete document: {str(e)}")

    def bulk_index_documents(self, directory_path: str):
        """
        Bulk index documents from a directory
        """
        try:
            for filename in os.listdir(directory_path):
                if filename.endswith('.json'):
                    with open(os.path.join(directory_path, filename), 'r') as f:
                        document = json.load(f)
                        self.index_document(document)
        except Exception as e:
            logger.error(f"Error in bulk indexing: {str(e)}")
            raise
