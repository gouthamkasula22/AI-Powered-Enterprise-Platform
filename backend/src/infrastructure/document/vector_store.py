"""
ChromaDB Vector Store Integration
Handles document embeddings and semantic search
"""

import logging
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

from ...shared.exceptions import DocumentProcessingError

logger = logging.getLogger(__name__)


class VectorStore:
    """
    ChromaDB-based vector storage for document embeddings
    """
    
    def __init__(self, persist_directory: str = "./data/chroma_db"):
        self.persist_directory = persist_directory
        self.client = None
        self.collection = None
        self.embedding_model = None
        self.model_name = "all-MiniLM-L6-v2"  # Lightweight, fast model
        self.initialized = False
    
    async def initialize(self):
        """Initialize ChromaDB client and embedding model"""
        try:
            logger.info("Initializing ChromaDB vector store...")
            
            # Initialize ChromaDB client
            self.client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name="document_chunks",
                metadata={"description": "Document chunks for RAG system"}
            )
            
            # Initialize embedding model
            logger.info(f"Loading embedding model: {self.model_name}")
            self.embedding_model = SentenceTransformer(self.model_name)
            
            self.initialized = True
            logger.info("ChromaDB vector store initialized successfully")
            
            # Log collection info
            count = self.collection.count()
            logger.info(f"Collection 'document_chunks' has {count} existing embeddings")
            
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {str(e)}")
            raise DocumentProcessingError(f"Vector store initialization failed: {str(e)}")
    
    def _ensure_initialized(self):
        """Ensure vector store is initialized"""
        if not self.initialized or self.client is None or self.collection is None or self.embedding_model is None:
            raise DocumentProcessingError("Vector store not initialized. Call initialize() first.")
    
    async def add_document_chunks(
        self, 
        document_id: int, 
        chunks: List[Dict[str, Any]]
    ) -> int:
        """
        Add document chunks to vector store
        
        Args:
            document_id: Document ID
            chunks: List of chunk dictionaries with 'id', 'content', 'metadata'
            
        Returns:
            int: Number of chunks added
        """
        self._ensure_initialized()
        
        try:
            if not chunks:
                return 0
            
            logger.info(f"Adding {len(chunks)} chunks for document {document_id} to vector store")
            
            # Prepare data for ChromaDB
            ids = []
            embeddings = []
            documents = []
            metadatas = []
            
            for chunk in chunks:
                chunk_id = f"doc_{document_id}_chunk_{chunk['chunk_index']}"
                content = chunk['content']
                
                # Generate embedding
                if self.embedding_model is None:
                    raise DocumentProcessingError("Embedding model not initialized")
                embedding = self.embedding_model.encode(content).tolist()
                
                # Prepare metadata
                metadata = {
                    "document_id": document_id,
                    "chunk_index": chunk['chunk_index'],
                    "character_count": chunk.get('character_count', len(content)),
                    "word_count": chunk.get('word_count', len(content.split())),
                    "start_position": chunk.get('start_position', 0),
                    "end_position": chunk.get('end_position', len(content)),
                    "created_at": datetime.utcnow().isoformat()
                }
                
                ids.append(chunk_id)
                embeddings.append(embedding)
                documents.append(content)
                metadatas.append(metadata)
            
            # Add to ChromaDB collection
            if self.collection is None:
                raise DocumentProcessingError("Collection not initialized")
                
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas
            )
            
            logger.info(f"Successfully added {len(chunks)} embeddings to vector store")
            return len(chunks)
            
        except Exception as e:
            logger.error(f"Failed to add chunks to vector store: {str(e)}")
            raise DocumentProcessingError(f"Vector store addition failed: {str(e)}")
    
    async def search_similar_chunks(
        self, 
        query: str, 
        n_results: int = 5,
        document_ids: Optional[List[int]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar chunks using semantic similarity
        
        Args:
            query: Search query text
            n_results: Number of results to return
            document_ids: Optional list to filter by specific documents
            
        Returns:
            List of similar chunks with metadata
        """
        self._ensure_initialized()
        
        try:
            logger.info(f"Searching for similar chunks: '{query[:50]}...'")
            
            # Generate query embedding
            if self.embedding_model is None:
                raise DocumentProcessingError("Embedding model not initialized")
            query_embedding = self.embedding_model.encode(query).tolist()
            
            # Prepare search filter
            where_filter = None
            if document_ids:
                where_filter = {"document_id": {"$in": document_ids}}
            
            # Search in ChromaDB
            if self.collection is None:
                raise DocumentProcessingError("Collection not initialized")
                
            # Cast the where_filter to the expected type
            from typing import Dict, Union, List as TypedList
            from typing import cast
            from chromadb.api.types import Where
            
            # Convert the filter to the proper type
            typed_where_filter = cast(Where, where_filter) if where_filter is not None else None
            
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=typed_where_filter,
                include=["documents", "metadatas", "distances"]
            )
            
            # Format results
            formatted_results = []
            
            # Safety check for results
            if results is not None and 'ids' in results and results['ids'] and results['ids'][0]:
                for i in range(len(results['ids'][0])):
                    result = {
                        'id': results['ids'][0][i],
                        'content': results['documents'][0][i] if 'documents' in results and results['documents'] else '',
                        'metadata': results['metadatas'][0][i] if 'metadatas' in results and results['metadatas'] else {},
                        'similarity_score': 1 - results['distances'][0][i] if 'distances' in results and results['distances'] else 0.0,  # Convert distance to similarity
                        'distance': results['distances'][0][i] if 'distances' in results and results['distances'] else 1.0
                    }
                    formatted_results.append(result)
            
            logger.info(f"Found {len(formatted_results)} similar chunks")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Vector search failed: {str(e)}")
            raise DocumentProcessingError(f"Vector search failed: {str(e)}")
    
    async def delete_document_chunks(self, document_id: int) -> int:
        """
        Delete all chunks for a document from vector store
        
        Args:
            document_id: Document ID
            
        Returns:
            int: Number of chunks deleted
        """
        self._ensure_initialized()
        
        try:
            logger.info(f"Deleting chunks for document {document_id} from vector store")
            
            # Check if collection is initialized
            if self.collection is None:
                raise DocumentProcessingError("Collection not initialized")
                
            # Get all chunks for this document
            # Cast the where filter to the expected type
            from chromadb.api.types import Where
            from typing import cast
            
            where_condition = {"document_id": document_id}
            typed_where = cast(Where, where_condition)
            
            results = self.collection.get(
                where=typed_where,
                include=["metadatas"]
            )
            
            if results is not None and 'ids' in results and results['ids']:
                # Delete the chunks
                self.collection.delete(ids=results['ids'])
                deleted_count = len(results['ids'])
                logger.info(f"Deleted {deleted_count} chunks for document {document_id}")
                return deleted_count
            
            return 0
            
        except Exception as e:
            logger.error(f"Failed to delete document chunks: {str(e)}")
            raise DocumentProcessingError(f"Vector store deletion failed: {str(e)}")
    
    async def get_collection_stats(self) -> Dict[str, Any]:
        """Get vector store statistics"""
        self._ensure_initialized()
        
        try:
            if self.collection is None:
                return {
                    "error": "Collection not initialized",
                    "embedding_model": self.model_name,
                    "collection_name": "document_chunks",
                    "persist_directory": self.persist_directory,
                    "total_chunks": 0,
                    "sample_documents": 0
                }
                
            count = self.collection.count()
            
            # Get some sample data for analysis
            sample = self.collection.peek(limit=10)
            
            stats = {
                "total_chunks": count,
                "embedding_model": self.model_name,
                "collection_name": "document_chunks",
                "persist_directory": self.persist_directory,
                "sample_documents": len(sample['ids']) if sample is not None and 'ids' in sample and sample['ids'] else 0
            }
            
            if count > 0 and sample['metadatas']:
                # Get unique document count
                doc_ids = set()
                for metadata in sample['metadatas']:
                    if 'document_id' in metadata:
                        doc_ids.add(metadata['document_id'])
                
                stats["sample_document_count"] = len(doc_ids)
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get collection stats: {str(e)}")
            return {"error": str(e)}
    
    async def health_check(self) -> Dict[str, Any]:
        """Check vector store health"""
        try:
            if not self.initialized:
                return {
                    "status": "unhealthy",
                    "message": "Vector store not initialized"
                }
            
            # Check if collection and embedding model are available
            if self.collection is None:
                return {
                    "status": "unhealthy",
                    "message": "ChromaDB collection not initialized"
                }
            
            if self.embedding_model is None:
                return {
                    "status": "unhealthy",
                    "message": "Embedding model not initialized"
                }
            
            # Test basic operations
            count = self.collection.count()
            
            # Test embedding generation
            test_embedding = self.embedding_model.encode("test").tolist()
            
            return {
                "status": "healthy",
                "message": "Vector store operational",
                "chunk_count": count,
                "embedding_dimension": len(test_embedding),
                "model": self.model_name
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"Vector store error: {str(e)}"
            }


# Global vector store instance
vector_store = VectorStore()