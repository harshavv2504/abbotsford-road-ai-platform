"""
Initialize RAG system by loading and indexing documents
Run this script after setting up the backend for the first time
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.rag.document_loader import document_loader
from app.services.rag.embedding_service import embedding_service
from app.services.rag.vector_store import vector_store


def main():
    print("🚀 Initializing RAG system...")
    print()
    
    # Initialize embedding model
    print("Step 1: Loading embedding model...")
    embedding_service.initialize_model()
    print()
    
    # Initialize vector store
    print("Step 2: Initializing vector store...")
    vector_store.initialize_index()
    print()
    
    # Load and index documents
    print("Step 3: Loading and indexing documents...")
    
    # Try different paths depending on where script is run from
    possible_paths = [
        "app/data/knowledge_base",
        "backend/app/data/knowledge_base",
        os.path.join(os.path.dirname(__file__), "..", "app", "data", "knowledge_base")
    ]
    
    knowledge_base_dir = None
    for path in possible_paths:
        if os.path.exists(path):
            knowledge_base_dir = path
            break
    
    if not knowledge_base_dir:
        print(f"❌ Knowledge base directory not found in any of these locations:")
        for path in possible_paths:
            print(f"  - {path}")
        print("Please create the directory and add documents first.")
        return
    
    print(f"Using knowledge base: {knowledge_base_dir}")
    document_loader.rebuild_index(knowledge_base_dir)
    print()
    
    # Verify
    print("Step 4: Verifying...")
    index_size = vector_store.get_index_size()
    print(f"✅ RAG system initialized successfully!")
    print(f"📊 Indexed {index_size} document chunks")
    print()
    
    # Test retrieval
    print("Step 5: Testing retrieval...")
    from app.services.rag.retriever import retriever
    
    test_query = "What are your pricing plans?"
    results = retriever.retrieve(test_query, k=3)
    
    print(f"Query: '{test_query}'")
    print(f"Found {len(results)} relevant documents:")
    for i, doc in enumerate(results, 1):
        print(f"  {i}. {doc.get('source_file')} (score: {doc.get('similarity_score', 0):.3f})")
    print()
    
    print("✅ RAG system is ready to use!")


if __name__ == "__main__":
    main()
