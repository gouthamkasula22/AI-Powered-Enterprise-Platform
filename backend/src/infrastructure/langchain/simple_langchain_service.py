"""
Simplified LangChain service for testing

This provides basic LangChain compatibility without complex Pydantic issues.
"""

class SimpleLangChainRAGService:
    """Simplified LangChain service wrapper for testing"""
    
    def __init__(self, vector_store, llm_service, context_manager, document_processor, memory_k=5, retriever_k=5):
        # Store components directly without Pydantic complications
        self.vector_store = vector_store
        self.llm_service = llm_service
        self.context_manager = context_manager
        self.document_processor = document_processor
        self.memory_k = memory_k
        self.retriever_k = retriever_k
        
        # Simple wrapper components
        self.retriever = SimpleRetriever(vector_store, retriever_k)
        self.llm_wrapper = SimpleLLMWrapper(llm_service)
    
    def get_chain_info(self):
        """Return chain information"""
        return {
            "chain_type": "custom_rag_chain",
            "memory_k": self.memory_k,
            "retriever_k": self.retriever_k,
            "llm_type": "custom_wrapper",
            "vector_store_type": "custom_vector_store",
            "langchain_version": "wrapper_v1.0"
        }
    
    def get_custom_components(self):
        """Return custom components"""
        return {
            "vector_store": self.vector_store,
            "llm_service": self.llm_service,
            "context_manager": self.context_manager,
            "document_processor": self.document_processor,
            "retriever": self.retriever,
            "llm_wrapper": self.llm_wrapper
        }
    
    async def chat(self, message, conversation_history=None, **kwargs):
        """Simple chat method for testing"""
        try:
            # Simple implementation for testing
            documents = self.retriever.get_relevant_documents(message)
            
            return {
                "content": f"LangChain wrapper response to: {message[:100]}...",
                "processing_time_ms": 100,
                "model_used": "langchain_wrapper",
                "source": "langchain_service",
                "documents_found": len(documents)
            }
        except Exception as e:
            return {
                "content": f"LangChain service error: {str(e)}",
                "processing_time_ms": 0,
                "model_used": "langchain_wrapper",
                "source": "langchain_service"
            }

class SimpleRetriever:
    """Simple retriever wrapper"""
    
    def __init__(self, vector_store, k=5):
        self.vector_store = vector_store
        self.k = k
    
    def get_relevant_documents(self, query):
        """Get relevant documents"""
        try:
            return self.vector_store.similarity_search(query=query, k=self.k)
        except Exception as e:
            return []

class SimpleLLMWrapper:
    """Simple LLM wrapper"""
    
    def __init__(self, llm_service):
        self.llm_service = llm_service
    
    def generate(self, prompt):
        """Generate response"""
        return f"Simple LLM wrapper response to: {prompt[:50]}..."