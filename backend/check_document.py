#!/usr/bin/env python3
"""
Test script to check if document ID 5 exists in the database
"""
import asyncio
import sys
import os

# Add the backend source to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def check_document():
    try:
        from infrastructure.database.database import get_db_session
        from sqlalchemy import text
        
        session_gen = get_db_session()
        session = await session_gen.__anext__()
        
        try:
            # Check if document 5 exists
            query = text("""
                SELECT id, filename, extracted_text, word_count, processing_status, thread_id, created_at
                FROM chat_documents 
                WHERE id = :doc_id
            """)
            result = await session.execute(query, {"doc_id": 5})
            document = result.fetchone()
            
            if document:
                print(f"✅ Document 5 found:")
                print(f"   ID: {document.id}")
                print(f"   Filename: {document.filename}")
                print(f"   Thread ID: {document.thread_id}")
                print(f"   Processing Status: {document.processing_status}")
                print(f"   Word Count: {document.word_count}")
                print(f"   Created: {document.created_at}")
                print(f"   Has Content: {'Yes' if document.extracted_text else 'No'}")
                if document.extracted_text:
                    print(f"   Content Preview: {document.extracted_text[:200]}...")
            else:
                print("❌ Document 5 not found in database")
                
            # Also check all documents in the database
            query_all = text("SELECT id, filename, thread_id, processing_status FROM chat_documents ORDER BY id")
            result_all = await session.execute(query_all)
            all_docs = result_all.fetchall()
            
            print(f"\n📋 All documents in database ({len(all_docs)} total):")
            for doc in all_docs:
                print(f"   ID {doc.id}: {doc.filename} (Thread: {doc.thread_id}, Status: {doc.processing_status})")
                
        finally:
            await session.close()
            
    except Exception as e:
        print(f"❌ Error checking document: {e}")

if __name__ == "__main__":
    asyncio.run(check_document())