"""
Document retrieval module for searching through regulatory documents.
"""

from typing import List, Dict, Any, Union
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import json
import os
from pathlib import Path
from app.text_extraction import TextExtractor
from app.utils.logger import setup_logger
from app.utils.exceptions import DocumentNotFoundError, DocumentIndexingError, DocumentSearchError

logger = setup_logger(__name__)

class DocumentRetrieval:
    """Class for handling document retrieval and search."""
    
    def __init__(self, 
                 index_dir: str = None,
                 model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the document retrieval system.
        
        Args:
            index_dir: Directory to store FAISS index
            model_name: Name of the sentence transformer model to use
        """
        if index_dir is None:
            # Use absolute path from project root
            base_dir = Path(__file__).parent.parent
            index_dir = str(base_dir / "data/faiss_index")
            
        self.index_dir = Path(index_dir)
        print(f"Using index directory: {self.index_dir}")
        
        # Initialize text extractor
        self.text_extractor = TextExtractor()
        
        # Initialize sentence transformer
        try:
            self.model = SentenceTransformer(model_name)
            self.embedding_dim = self.model.get_sentence_embedding_dimension()
            logger.info(f"Initialized sentence transformer model: {model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize sentence transformer: {str(e)}")
            raise DocumentIndexingError("Failed to initialize embedding model")
        
        # Initialize or load FAISS index
        try:
            index_path = self.index_dir / "regulatory_index.faiss"
            mappings_path = self.index_dir / "document_mappings.json"
            
            if index_path.exists() and mappings_path.exists():
                # Load existing index
                self.index = faiss.read_index(str(index_path))
                with open(mappings_path, 'r') as f:
                    self.document_ids = json.load(f)
                logger.info("Loaded existing FAISS index")
            else:
                # Initialize new index
                self.index = faiss.IndexFlatIP(self.embedding_dim)  # Inner product index
                self.document_ids = []  # To map FAISS indices to document IDs
                logger.info("Initialized new FAISS index")
            
            self.chunks = []  # To store text chunks
        except Exception as e:
            logger.error(f"Failed to initialize FAISS index: {str(e)}")
            raise DocumentIndexingError("Failed to initialize search index")
        
        # Initialize TF-IDF vectorizer for keyword search
        self.vectorizer = TfidfVectorizer(stop_words='english')
        self.tfidf_matrix = None
    
    def _get_embeddings(self, texts: List[str]) -> np.ndarray:
        """Get embeddings for a list of texts."""
        try:
            embeddings = self.model.encode(texts, convert_to_numpy=True)
            return embeddings.astype('float32')  # FAISS requires float32
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            raise DocumentIndexingError(f"Failed to generate embeddings: {str(e)}")
    
    def _normalize_scores(self, scores: np.ndarray) -> np.ndarray:
        """Normalize scores to range [0, 1]."""
        if len(scores) == 0:
            return scores
        min_score = scores.min()
        max_score = scores.max()
        if max_score == min_score:
            return np.ones_like(scores)
        return (scores - min_score) / (max_score - min_score)
    
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
            extraction_result = self.text_extractor.extract_from_file(file_path)
            chunks = extraction_result["chunks"]
            
            # Get embeddings for chunks
            chunk_embeddings = self._get_embeddings(chunks)
            
            # Add to FAISS index
            self.index.add(chunk_embeddings)
            
            # Store mapping of indices to document info
            start_idx = len(self.document_ids)
            for i, chunk in enumerate(chunks):
                self.document_ids.append({
                    "doc_id": doc_id,
                    "chunk_index": i,
                    "chunk_text": chunk,
                    "metadata": metadata
                })
            
            # Update TF-IDF matrix
            if self.tfidf_matrix is None:
                self.tfidf_matrix = self.vectorizer.fit_transform(chunks)
            else:
                new_matrix = self.vectorizer.transform(chunks)
                self.tfidf_matrix = np.vstack([self.tfidf_matrix, new_matrix])
            
            logger.info(f"Document {doc_id} indexed successfully")
            
        except Exception as e:
            logger.error(f"Error indexing document: {str(e)}")
            raise DocumentIndexingError(f"Failed to index document: {str(e)}")
    
    async def search(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search for documents using hybrid search (semantic + keyword).
        
        Args:
            query: Search query
            n_results: Number of results to return
            
        Returns:
            List of search results with scores
        """
        try:
            # Get query embedding
            query_embedding = self._get_embeddings([query])[0].reshape(1, -1)
            
            # Semantic search with FAISS
            semantic_scores, semantic_indices = self.index.search(query_embedding, n_results * 2)
            semantic_scores = self._normalize_scores(semantic_scores[0])
            
            # Keyword search with TF-IDF
            chunks = [doc["chunk_text"] for doc in self.document_ids]
            if not chunks:
                logger.warning("No chunks available for search")
                return []
            
            # Fit or transform TF-IDF
            if self.tfidf_matrix is None:
                self.vectorizer.fit(chunks)
                self.tfidf_matrix = self.vectorizer.transform(chunks)
            
            query_tfidf = self.vectorizer.transform([query])
            keyword_scores = cosine_similarity(query_tfidf, self.tfidf_matrix)[0]
            keyword_scores = self._normalize_scores(keyword_scores)
            
            # Combine scores
            results = []
            seen_docs = set()
            
            for idx, (sem_score, idx) in enumerate(zip(semantic_scores, semantic_indices[0])):
                if idx >= len(self.document_ids):
                    continue
                    
                doc_info = self.document_ids[idx]
                doc_id = doc_info["doc_id"]
                
                # Skip if we already have a better chunk from this document
                if doc_id in seen_docs:
                    continue
                
                # Combine semantic and keyword scores
                keyword_score = keyword_scores[idx]
                combined_score = 0.7 * sem_score + 0.3 * keyword_score
                
                # Ensure metadata exists
                metadata = doc_info.get("metadata", {})
                if not isinstance(metadata, dict):
                    metadata = {}
                
                results.append({
                    "id": doc_id,
                    "content": doc_info["chunk_text"],
                    "metadata": metadata,
                    "score": float(combined_score),
                    "semantic_score": float(sem_score),
                    "keyword_score": float(keyword_score)
                })
                
                seen_docs.add(doc_id)
                
                if len(seen_docs) >= n_results:
                    break
            
            # Sort by combined score
            results.sort(key=lambda x: x["score"], reverse=True)
            logger.info(f"Search returned {len(results)} results")
            return results[:n_results]
            
        except Exception as e:
            logger.error(f"Error during search: {str(e)}")
            raise DocumentSearchError(f"Error during search: {str(e)}")
    
    def save_index(self):
        """Save the FAISS index and related data to disk."""
        try:
            # Save FAISS index
            index_path = self.index_dir / "regulatory_index.faiss"
            faiss.write_index(self.index, str(index_path))
            
            # Save document mappings
            mappings_path = self.index_dir / "document_mappings.json"
            with open(mappings_path, 'w') as f:
                json.dump(self.document_ids, f)
            
            logger.info("Search index saved successfully")
        except Exception as e:
            logger.error(f"Error saving search index: {str(e)}")
            raise DocumentIndexingError(f"Failed to save search index: {str(e)}")
    
    def load_index(self):
        """Load the FAISS index and related data from disk."""
        try:
            index_path = self.index_dir / "regulatory_index.faiss"
            mappings_path = self.index_dir / "document_mappings.json"
            
            if index_path.exists() and mappings_path.exists():
                # Load FAISS index
                self.index = faiss.read_index(str(index_path))
                
                # Load document mappings
                with open(mappings_path, 'r') as f:
                    self.document_ids = json.load(f)
                
                logger.info("Search index loaded successfully")
            else:
                logger.warning("No existing index found")
        except Exception as e:
            logger.error(f"Error loading search index: {str(e)}")
            raise DocumentIndexingError(f"Failed to load search index: {str(e)}")
