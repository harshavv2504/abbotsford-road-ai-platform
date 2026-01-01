import faiss
import numpy as np
import json
import os
from typing import List, Tuple, Dict, Optional
from app.utils.logger import logger


class VectorStore:
    """FAISS flat index for vector storage (shared by both bots)"""
    
    def __init__(self, dimension: int = 384, index_path: str = None):
        self.dimension = dimension
        
        # Use absolute path relative to this file's location
        if index_path is None:
            # Get the backend/app directory
            app_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            index_path = os.path.join(app_dir, "data", "vector_db")
        
        self.index_path = index_path
        self.index_file = os.path.join(index_path, "faiss_index.bin")
        self.metadata_file = os.path.join(index_path, "metadata.json")
        
        self.index: Optional[faiss.IndexFlatIP] = None
        self.metadata: List[Dict] = []
        
        # Create directory if not exists
        os.makedirs(index_path, exist_ok=True)
    
    def initialize_index(self):
        """Create new FAISS flat index with Inner Product similarity"""
        logger.info(f"Initializing FAISS IndexFlatIP (dimension: {self.dimension})")
        self.index = faiss.IndexFlatIP(self.dimension)
        self.metadata = []
        logger.info("✅ FAISS index initialized")
    
    def add_documents(self, embeddings: np.ndarray, metadata: List[Dict]):
        """Add document embeddings to index (embeddings should already be normalized)"""
        if self.index is None:
            self.initialize_index()
        
        # Ensure embeddings are float32
        embeddings = embeddings.astype('float32')
        
        # Add to FAISS index (embeddings should already be normalized by embedding service)
        self.index.add(embeddings)
        
        # Add metadata
        self.metadata.extend(metadata)
        
        logger.info(f"Added {len(embeddings)} documents to index")
    
    def search(self, query_embedding: np.ndarray, k: int = 5) -> Tuple[np.ndarray, np.ndarray]:
        """
        Search for top-k similar documents using Inner Product similarity
        
        Returns:
            Tuple of (scores, indices) - higher scores are better for Inner Product
        """
        if self.index is None or self.index.ntotal == 0:
            logger.warning("Index is empty")
            return np.array([]), np.array([])
        
        # Ensure query is float32 and 2D (should already be normalized by embedding service)
        query_embedding = query_embedding.astype('float32').reshape(1, -1)
        
        # Search using Inner Product (higher scores = more similar)
        scores, indices = self.index.search(query_embedding, k)
        
        return scores[0], indices[0]
    
    def get_documents_by_indices(self, indices: np.ndarray) -> List[Dict]:
        """Get document metadata by indices"""
        results = []
        for idx in indices:
            if 0 <= idx < len(self.metadata):
                results.append(self.metadata[idx])
        return results
    
    def save_index(self):
        """Persist index and metadata to disk"""
        if self.index is None:
            logger.warning("No index to save")
            return
        
        # Save FAISS index
        faiss.write_index(self.index, self.index_file)
        
        # Save metadata
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2)
        
        logger.info(f"✅ Saved index to {self.index_file}")
    
    def load_index(self):
        """Load index and metadata from disk"""
        if not os.path.exists(self.index_file):
            logger.warning(f"Index file not found: {self.index_file}")
            self.initialize_index()
            return
        
        # Load FAISS index
        self.index = faiss.read_index(self.index_file)
        
        # Load metadata
        if os.path.exists(self.metadata_file):
            with open(self.metadata_file, 'r') as f:
                self.metadata = json.load(f)
        
        logger.info(f"✅ Loaded index from {self.index_file} ({self.index.ntotal} documents)")
    
    def get_index_size(self) -> int:
        """Get number of documents in index"""
        if self.index is None:
            return 0
        return self.index.ntotal
    
    def clear_index(self):
        """Clear all documents from index"""
        self.initialize_index()
        logger.info("Index cleared")


# Singleton instance (shared across application)
vector_store = VectorStore()
