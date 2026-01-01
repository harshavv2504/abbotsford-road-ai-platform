import os
from typing import List, Dict
from pathlib import Path
from app.services.rag.embedding_service import embedding_service
from app.services.rag.vector_store import vector_store
from app.utils.logger import logger


class DocumentLoader:
    """Load and index documents into FAISS vector store"""
    
    def __init__(self, chunk_size: int = 512):
        self.chunk_size = chunk_size
        self.embedding_service = embedding_service
        self.vector_store = vector_store
    
    def load_documents(self, directory: str) -> List[Dict]:
        """Load all documents from directory"""
        documents = []
        
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith(('.txt', '.md')):
                    file_path = os.path.join(root, file)
                    content = self._read_file(file_path)
                    
                    # Determine category from subdirectory
                    category = Path(root).name
                    
                    # Check if this is a Q&A format file
                    is_qa_format = self._is_qa_format(content)
                    
                    documents.append({
                        'file_path': file_path,
                        'content': content,
                        'category': category,
                        'is_qa_format': is_qa_format
                    })
        
        logger.info(f"Loaded {len(documents)} documents from {directory}")
        return documents
    
    def _is_qa_format(self, content: str) -> bool:
        """Check if document is in Q&A format (Q: ... A: ...)"""
        lines = content.strip().split('\n')
        # Check if file starts with Q: and has A: patterns
        has_q = any(line.strip().startswith('Q:') for line in lines[:10])
        has_a = any(line.strip().startswith('A:') for line in lines[:10])
        return has_q and has_a
    
    def _read_file(self, file_path: str) -> str:
        """Read file content"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading {file_path}: {e}")
            return ""
    
    def chunk_document(self, text: str, chunk_size: int = None, is_qa_format: bool = False) -> List[str]:
        """
        Split document into chunks
        
        For Q&A format: Each Q:A: pair becomes one chunk
        For regular text: Split by character size
        """
        if is_qa_format:
            return self._chunk_qa_document(text)
        
        # Regular chunking by characters
        chunk_size = chunk_size or self.chunk_size
        chunks = []
        for i in range(0, len(text), chunk_size):
            chunk = text[i:i + chunk_size]
            if chunk.strip():
                chunks.append(chunk.strip())
        
        return chunks
    
    def _chunk_qa_document(self, text: str) -> List[str]:
        """
        Split Q&A format document where each Q:A: pair is one chunk
        
        Format:
        Q: Question text here?
        A: Answer text here.
        
        Q: Next question?
        A: Next answer.
        """
        chunks = []
        lines = text.split('\n')
        
        current_chunk = []
        in_qa_pair = False
        
        for line in lines:
            line = line.strip()
            
            # Start of a new Q&A pair
            if line.startswith('Q:'):
                # Save previous chunk if exists
                if current_chunk:
                    chunk_text = '\n'.join(current_chunk).strip()
                    if chunk_text:
                        chunks.append(chunk_text)
                
                # Start new chunk
                current_chunk = [line]
                in_qa_pair = True
            
            # Answer part of the pair
            elif line.startswith('A:') and in_qa_pair:
                current_chunk.append(line)
            
            # Continuation of answer (multi-line)
            elif in_qa_pair and line and not line.startswith('Q:'):
                current_chunk.append(line)
            
            # Empty line - might be end of Q&A pair
            elif not line and in_qa_pair:
                # Keep the chunk going, just add spacing
                continue
        
        # Add the last chunk
        if current_chunk:
            chunk_text = '\n'.join(current_chunk).strip()
            if chunk_text:
                chunks.append(chunk_text)
        
        logger.info(f"Split Q&A document into {len(chunks)} Q&A pairs")
        return chunks
    
    def index_documents(self, documents: List[Dict]):
        """Process and add documents to FAISS index"""
        all_chunks = []
        all_metadata = []
        
        for doc in documents:
            content = doc['content']
            file_path = doc['file_path']
            category = doc['category']
            is_qa_format = doc.get('is_qa_format', False)
            
            # Split into chunks (Q&A pairs or regular chunks)
            chunks = self.chunk_document(content, is_qa_format=is_qa_format)
            
            for i, chunk in enumerate(chunks):
                all_chunks.append(chunk)
                
                # For Q&A format, extract question for better metadata
                doc_id_prefix = "qa" if is_qa_format else "chunk"
                
                all_metadata.append({
                    'doc_id': f"{Path(file_path).stem}_{doc_id_prefix}_{i}",
                    'source_file': file_path,
                    'category': category,
                    'chunk_index': i,
                    'chunk_text': chunk,
                    'is_qa': is_qa_format
                })
        
        if not all_chunks:
            logger.warning("No chunks to index")
            return
        
        # Generate embeddings with passage prefix (for documents)
        logger.info(f"Generating embeddings for {len(all_chunks)} chunks...")
        embeddings = self.embedding_service.encode_batch(all_chunks, is_query=False)
        
        # Add to vector store
        self.vector_store.add_documents(embeddings, all_metadata)
        
        # Save index
        self.vector_store.save_index()
        
        logger.info(f"✅ Indexed {len(all_chunks)} chunks from {len(documents)} documents")
    
    def rebuild_index(self, knowledge_base_dir: str = "app/data/knowledge_base"):
        """Rebuild index from scratch"""
        logger.info("Rebuilding index from scratch...")
        
        # Clear existing index
        self.vector_store.clear_index()
        
        # Load documents
        documents = self.load_documents(knowledge_base_dir)
        
        # Index documents
        if documents:
            self.index_documents(documents)
        else:
            logger.warning("No documents found to index")


# Singleton instance
document_loader = DocumentLoader()
