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
    """Class for handling document retrieval and search."""
    
    def __init__(self, persist_dir: str = "./data/chroma"):
        """
        Initialize the document retrieval system.
        
        Args:
            persist_dir: Directory to store ChromaDB data
        """
        # Create the persist directory if it doesn't exist
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

    async def index_document(self, file_path: str, doc_id: str, metadata: Dict[str, Any]) -> None:
        """
        Index a document for search.
        
        Args:
            file_path: Path to the document file
            doc_id: Document ID
            metadata: Document metadata
        """
        try:
            # Extract text content
            content = await self._extract_text_content(file_path)
            
            # Clean metadata (convert all values to strings)
            clean_metadata = {}
            for key, value in metadata.items():
                if isinstance(value, (list, tuple)):
                    clean_metadata[key] = ", ".join(map(str, value))
                elif isinstance(value, (str, int, float, bool)):
                    clean_metadata[key] = str(value)
                else:
                    clean_metadata[key] = str(value)
            
            # Delete if exists
            try:
                self.collection.delete(ids=[doc_id])
            except:
                pass
            
            # Add to ChromaDB
            self.collection.add(
                documents=[content],
                metadatas=[clean_metadata],
                ids=[doc_id]
            )
            
            logger.info(f"Document {doc_id} indexed successfully")
        except Exception as e:
            logger.error(f"Error indexing document: {str(e)}")
            raise DocumentIndexingError(f"Failed to index document: {str(e)}")

    async def search(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search for documents using semantic search.
        
        Args:
            query: Search query
            n_results: Number of results to return
            
        Returns:
            List of search results with scores
        """
        try:
            # Search in ChromaDB
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                include=["documents", "metadatas", "distances"]
            )
            
            # Format results
            search_results = []
            if results and results.get("ids") and len(results["ids"][0]) > 0:
                for i in range(len(results["ids"][0])):
                    result = {
                        "id": results["ids"][0][i],
                        "content": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i],
                        "score": 1.0 - float(results["distances"][0][i])  # Convert distance to similarity score
                    }
                    search_results.append(result)
            
                # Sort results by score in descending order
                search_results.sort(key=lambda x: x['score'], reverse=True)
            
            return search_results
        except Exception as e:
            logger.error(f"Error during search: {str(e)}")
            return []

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

    def _get_embeddings(self, text: str) -> List[float]:
        """
        Get embeddings for text.
        
        Args:
            text: Text to get embeddings for
            
        Returns:
            List of embeddings
        """
        try:
            # Use a simple bag-of-words approach for now
            # In a real application, you would use a proper embedding model
            words = text.lower().split()
            embeddings = [0.0] * 384  # Use 384 dimensions for ChromaDB
            for i, word in enumerate(words):
                if i < len(embeddings):
                    embeddings[i] = hash(word) / 1e10  # Simple hash-based embedding
            return embeddings
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            raise DocumentIndexingError(f"Failed to generate embeddings: {str(e)}")

    async def _extract_text_content(self, file_path: str) -> str:
        """Extract text content from a file."""
        try:
            # Read text file
            with open(file_path, "rb") as f:
                content = f.read().decode("utf-8", errors="ignore")
            return content
        except Exception as e:
            logger.error(f"Error extracting text content: {str(e)}")
            raise DocumentIndexingError(f"Failed to extract text content: {str(e)}")
