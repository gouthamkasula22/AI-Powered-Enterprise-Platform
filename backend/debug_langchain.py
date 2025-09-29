#!/usr/bin/env python3
"""
Debug script to test LangChain service initialization
"""

import sys
import asyncio
import os
sys.path.append('src')

from src.infrastructure.database.database import get_db_session
from src.infrastructure.database.database import DatabaseManager
from src.infrastructure.langchain.simple_langchain_service import SimpleLangChainRAGService
from src.infrastructure.document.vector_store import VectorStore
from src.infrastructure.ai.llm_service import LLMService
from src.infrastructure.ai.context_manager import ContextManager
from src.infrastructure.document.document_processor import DocumentProcessor

async def test_langchain_service():
    """Test LangChain service initialization and methods"""
    try:
        print("🔧 Testing LangChain service initialization...")
        
        # Create database session
        db_manager = DatabaseManager()
        await db_manager.initialize()
        
        # Get database session generator
        db_session_gen = get_db_session()
        db_session = await db_session_gen.__anext__()
        
        # Initialize custom components
        print("1. Initializing custom components...")
        vector_store = VectorStore()
        print("   ✓ VectorStore initialized")
        
        llm_service = LLMService()
        print("   ✓ LLMService initialized")
        
        context_manager = ContextManager()
        print("   ✓ ContextManager initialized")
        
        document_processor = DocumentProcessor(db_session=db_session)
        print("   ✓ DocumentProcessor initialized")
        
        # Create LangChain service
        print("2. Creating LangChain service...")
        langchain_service = SimpleLangChainRAGService(
            vector_store=vector_store,
            llm_service=llm_service,
            context_manager=context_manager,
            document_processor=document_processor,
            memory_k=5,
            retriever_k=5
        )
        print("   ✓ SimpleLangChainRAGService initialized")
        
        # Test methods used by health check
        print("3. Testing health check methods...")
        chain_info = langchain_service.get_chain_info()
        print(f"   ✓ get_chain_info(): {chain_info}")
        
        custom_components = langchain_service.get_custom_components()
        print(f"   ✓ get_custom_components(): {list(custom_components.keys())}")
        
        print("✅ All tests passed! LangChain service is working correctly.")
        
        # Close database session
        await db_session.close()
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_langchain_service())