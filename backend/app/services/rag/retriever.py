from typing import List, Dict, Optional
import numpy as np
from app.services.rag.embedding_service import embedding_service
from app.services.rag.vector_store import vector_store
from app.utils.logger import logger


class Retriever:
    """Query and retrieve relevant documents from vector store"""
    
    def __init__(self):
        self.embedding_service = embedding_service
        self.vector_store = vector_store
    
    def retrieve(self, query: str, k: int = 5, category_filter: Optional[str] = None) -> List[Dict]:
        """
        Retrieve top-k relevant documents for query
        
        Args:
            query: User query text
            k: Number of documents to retrieve
            category_filter: Filter by document category (optional)
        
        Returns:
            List of relevant documents with metadata
        """
        # Generate query embedding with query prefix (for search)
        query_embedding = self.embedding_service.encode_text(query, is_query=True)
        
        # Search vector store
        distances, indices = self.vector_store.search(query_embedding, k=k * 2)  # Get more for filtering
        
        # Get documents
        documents = self.vector_store.get_documents_by_indices(indices)
        
        # Add similarity scores
        for i, doc in enumerate(documents):
            doc['similarity_score'] = float(1 / (1 + distances[i]))  # Convert distance to similarity
        
        # Filter by category if specified
        if category_filter:
            documents = [doc for doc in documents if doc.get('category') == category_filter]
        
        # Return top-k after filtering
        return documents[:k]
    
    def retrieve_with_scores(self, query: str, k: int = 5) -> List[Dict]:
        """Retrieve documents with similarity scores"""
        return self.retrieve(query, k=k)
    
    def filter_by_relevance(self, documents: List[Dict], min_score: float = 0.5) -> List[Dict]:
        """Filter documents by minimum relevance score"""
        return [doc for doc in documents if doc.get('similarity_score', 0) >= min_score]
    
    def format_context_for_llm(self, documents: List[Dict]) -> str:
        """
        Format retrieved documents as context for LLM prompt
        
        Returns:
            Formatted context string
        """
        if not documents:
            return ""
        
        context_parts = []
        for i, doc in enumerate(documents, 1):
            chunk_text = doc.get('chunk_text', '')
            source = doc.get('source_file', 'Unknown')
            context_parts.append(f"[Document {i} - {source}]\n{chunk_text}")
        
        context = "\n\n".join(context_parts)
        return context


# Singleton instance
retriever = Retriever()
