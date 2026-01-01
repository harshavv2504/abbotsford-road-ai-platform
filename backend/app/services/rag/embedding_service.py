from fastembed import TextEmbedding
from typing import List
import numpy as np
from app.utils.logger import logger


class EmbeddingService:
    """FastEmbed embedding service using ONNX Runtime (shared by both bots)"""
    
    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5"):
        self.model_name = model_name
        self.model = None
        self.dimension = 384  # Dimension for bge-small-en-v1.5
    
    def initialize_model(self):
        """Load FastEmbed model"""
        if self.model is None:
            logger.info(f"Loading embedding model: {self.model_name}")
            logger.info("💡 Using FastEmbed with ONNX Runtime - lightweight, no PyTorch needed!")
            self.model = TextEmbedding(model_name=self.model_name)
            
            # Verify dimensions with test embedding
            test_embedding = next(self.model.embed(["test"]))
            self.dimension = len(test_embedding)
            logger.info(f"✅ Embedding model loaded (dimension: {self.dimension})")
    
    def _add_passage_prefix(self, text: str) -> str:
        """Add passage prefix for better retrieval performance with BGE models"""
        if not text.strip().startswith("passage:"):
            return f"passage: {text}"
        return text
    
    def _add_query_prefix(self, text: str) -> str:
        """Add query prefix for better retrieval performance with BGE models"""
        if not text.strip().startswith("query:"):
            return f"query: {text}"
        return text
    
    def _normalize_embeddings(self, embeddings: np.ndarray) -> np.ndarray:
        """Normalize embeddings to unit length for Inner Product similarity"""
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1, norms)
        return embeddings / norms
    
    def encode_text(self, text: str, is_query: bool = False) -> np.ndarray:
        """
        Convert text to vector embedding
        
        Args:
            text: Text to embed
            is_query: If True, adds "query:" prefix (for search queries)
                     If False, adds "passage:" prefix (for documents)
        """
        if self.model is None:
            self.initialize_model()
        
        # Add appropriate prefix for better retrieval performance
        if is_query:
            prefixed_text = self._add_query_prefix(text)
        else:
            prefixed_text = self._add_passage_prefix(text)
        
        # FastEmbed's embed method returns an iterator
        embeddings = list(self.model.embed([prefixed_text]))
        embedding = np.array(embeddings[0])
        
        # Normalize for Inner Product similarity
        return self._normalize_embeddings(embedding.reshape(1, -1))[0]
    
    def encode_batch(self, texts: List[str], is_query: bool = False, batch_size: int = 64) -> np.ndarray:
        """
        Convert multiple texts to embeddings (batch processing)
        
        Args:
            texts: List of texts to embed
            is_query: If True, adds "query:" prefix to all texts
                     If False, adds "passage:" prefix to all texts
            batch_size: Batch size for processing
        """
        if self.model is None:
            self.initialize_model()
        
        # Add appropriate prefix for better retrieval performance
        if is_query:
            prefixed_texts = [self._add_query_prefix(text) for text in texts]
        else:
            prefixed_texts = [self._add_passage_prefix(text) for text in texts]
        
        logger.info(f"Generating embeddings for {len(texts)} texts using FastEmbed...")
        logger.info(f"📦 Batch size: {batch_size} | Prefix: {'query' if is_query else 'passage'}")
        
        # FastEmbed handles batching internally and returns an iterator
        embeddings_list = list(self.model.embed(prefixed_texts, batch_size=batch_size))
        embeddings = np.array(embeddings_list)
        
        # Normalize for Inner Product similarity
        embeddings_normalized = self._normalize_embeddings(embeddings)
        
        logger.info(f"✅ Generated {len(embeddings_normalized)} embeddings")
        return embeddings_normalized
    
    def get_embedding_dimension(self) -> int:
        """Get embedding dimension"""
        if self.dimension is None and self.model is not None:
            test_embedding = next(self.model.embed(["test"]))
            self.dimension = len(test_embedding)
        return self.dimension


# Singleton instance (shared across application)
embedding_service = EmbeddingService()
