"""
LangChain wrapper around our custom VectorStore

This wrapper makes our custom vector store compatible with LangChain
while preserving all the performance optimizations.
"""

from typing import List, Optional, Dict, Any
from langchain.schema import BaseRetriever, Document
from langchain.callbacks.manager import CallbackManagerForRetrieverRun, AsyncCallbackManagerForRetrieverRun
from pydantic import Field

class CustomVectorStoreRetriever(BaseRetriever):
    """
    LangChain retriever wrapper around our custom VectorStore
    
    This allows us to use our optimized vector store within LangChain chains
    while maintaining full performance and functionality.
    """
    
    def __init__(self, custom_vector_store, k: int = 5):
        # Initialize BaseRetriever without passing custom fields to parent
        super().__init__()
        # Set custom fields manually after initialization using object.__setattr__ for Pydantic
        object.__setattr__(self, 'custom_store', custom_vector_store)
        object.__setattr__(self, 'k', k)
    
    class Config:
        arbitrary_types_allowed = True
    
    def _get_relevant_documents(
        self, 
        query: str, 
        *, 
        run_manager: CallbackManagerForRetrieverRun
    ) -> List[Document]:
        """
        Retrieve relevant documents using our custom vector store
        
        Args:
            query: The search query
            run_manager: LangChain callback manager
            
        Returns:
            List of LangChain Document objects
        """
        try:
            # Use our existing vector search method
            custom_store = getattr(self, 'custom_store')
            k = getattr(self, 'k', 5)
            custom_results = custom_store.similarity_search(
                query=query, 
                k=k
            )
            
            # Convert our custom results to LangChain Document format
            langchain_docs = []
            for result in custom_results:
                # Handle different result formats from our custom store
                if hasattr(result, 'content') and hasattr(result, 'metadata'):
                    # DocumentChunk format
                    content = result.content
                    metadata = result.metadata or {}
                    
                    # Add our custom metadata
                    if hasattr(result, 'chunk_id'):
                        metadata['chunk_id'] = result.chunk_id
                    if hasattr(result, 'similarity_score'):
                        metadata['similarity_score'] = result.similarity_score
                        
                elif isinstance(result, dict):
                    # Dictionary format
                    content = result.get('content', result.get('text', ''))
                    metadata = result.get('metadata', {})
                else:
                    # String format fallback
                    content = str(result)
                    metadata = {}
                
                # Create LangChain document
                langchain_doc = Document(
                    page_content=content,
                    metadata={
                        **metadata,
                        'retriever': 'custom_vector_store',
                        'framework': 'langchain_wrapper'
                    }
                )
                langchain_docs.append(langchain_doc)
            
            # Log retrieval for debugging
            if run_manager:
                run_manager.on_text(
                    f"Retrieved {len(langchain_docs)} documents from custom vector store"
                )
            
            return langchain_docs
            
        except Exception as e:
            # Log error but don't break the chain
            if run_manager:
                run_manager.on_text(f"Error in custom vector retrieval: {str(e)}")
            
            # Return empty list to prevent chain failure
            return []
    
    async def _aget_relevant_documents(
        self, 
        query: str, 
        *, 
        run_manager: AsyncCallbackManagerForRetrieverRun
    ) -> List[Document]:
        """Async version of document retrieval"""
        try:
            # Check if our custom store supports async
            custom_store = getattr(self, 'custom_store')
            k = getattr(self, 'k', 5)
            if hasattr(custom_store, 'asimilarity_search'):
                custom_results = await custom_store.asimilarity_search(
                    query=query, 
                    k=k
                )
            else:
                # Fallback to sync method
                custom_results = custom_store.similarity_search(
                    query=query, 
                    k=k
                )
            
            # Convert results same as sync method
            langchain_docs = []
            for result in custom_results:
                if hasattr(result, 'content') and hasattr(result, 'metadata'):
                    content = result.content
                    metadata = result.metadata or {}
                    
                    if hasattr(result, 'chunk_id'):
                        metadata['chunk_id'] = result.chunk_id
                    if hasattr(result, 'similarity_score'):
                        metadata['similarity_score'] = result.similarity_score
                        
                elif isinstance(result, dict):
                    content = result.get('content', result.get('text', ''))
                    metadata = result.get('metadata', {})
                else:
                    content = str(result)
                    metadata = {}
                
                langchain_doc = Document(
                    page_content=content,
                    metadata={
                        **metadata,
                        'retriever': 'custom_vector_store_async',
                        'framework': 'langchain_wrapper'
                    }
                )
                langchain_docs.append(langchain_doc)
            
            return langchain_docs
            
        except Exception as e:
            if run_manager:
                await run_manager.on_text(f"Error in async custom vector retrieval: {str(e)}")
            return []
    
    def add_documents(self, documents: List[Document]) -> None:
        """Add documents to the custom vector store"""
        try:
            # Convert LangChain documents to our format if needed
            custom_store = getattr(self, 'custom_store')
            if hasattr(custom_store, 'add_documents'):
                custom_store.add_documents(documents)
            elif hasattr(custom_store, 'add_texts'):
                texts = [doc.page_content for doc in documents]
                metadatas = [doc.metadata for doc in documents]
                custom_store.add_texts(texts, metadatas)
        except Exception as e:
            print(f"Error adding documents to custom store: {e}")
    
    def get_custom_store(self):
        """Access to the underlying custom vector store"""
        return getattr(self, 'custom_store')