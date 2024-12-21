import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import db
from app.document_retrieval import DocumentRetrieval
from app.chatbot import Chatbot
import openai
from dotenv import load_dotenv
import json
from bson import ObjectId

def test_mongodb_connection():
    """Test MongoDB connection and basic operations"""
    try:
        # Test connection
        db.client.server_info()
        print("✅ MongoDB connection successful")
        
        # Test document insertion
        test_doc = {
            "content": "Test document",
            "metadata": {
                "title": "Test",
                "category": "Test Category",
                "jurisdiction": "Test Jurisdiction"
            }
        }
        doc_id = db.store_document(test_doc["content"], test_doc["metadata"])
        print("✅ Document insertion successful")
        
        # Test document retrieval
        retrieved_doc = db.get_document(ObjectId(doc_id))
        if not retrieved_doc:
            raise Exception("Failed to retrieve document")
        print("✅ Document retrieval successful")
        
        # Cleanup
        db.regulatory_documents.delete_one({'_id': ObjectId(doc_id)})
        print("✅ Test cleanup successful")
        
    except Exception as e:
        print(f"❌ MongoDB test failed: {str(e)}")
        raise

def test_openai_connection():
    """Test OpenAI API connection"""
    try:
        openai.api_key = os.getenv('OPENAI_API_KEY')
        # Test with a simple completion
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hello, this is a test!"}],
            max_tokens=10
        )
        print("✅ OpenAI API connection successful")
    except Exception as e:
        print(f"❌ OpenAI API test failed: {str(e)}")
        raise

def test_document_retrieval():
    """Test document retrieval system"""
    try:
        doc_retrieval = DocumentRetrieval()
        
        # Test document with properly formatted metadata
        test_doc = {
            "title": "Test Regulation",
            "content": "This is a test regulatory document about medical devices.",
            "metadata": {
                "category": "Medical Devices",
                "jurisdiction": "Test",
                "tags": "test,medical_devices",  # Convert list to string
                "last_updated": "2023-12-21"
            }
        }
        
        # Test indexing
        doc_id = doc_retrieval.index_document(test_doc)
        print("✅ Document indexing successful")
        
        # Test search
        search_results = doc_retrieval.search("medical devices")
        assert len(search_results) > 0
        print("✅ Document search successful")
        
        # Cleanup
        if isinstance(doc_id, str):
            doc_id = ObjectId(doc_id)
        db.regulatory_documents.delete_one({'_id': doc_id})
        print("✅ Test cleanup successful")
        
    except Exception as e:
        print(f"❌ Document retrieval test failed: {str(e)}")
        raise

def test_chatbot():
    """Test chatbot functionality"""
    try:
        doc_retrieval = DocumentRetrieval()
        chatbot = Chatbot(doc_retrieval)
        
        # Test simple query
        response = chatbot.chain.invoke("What are the basic requirements for medical devices?")
        assert response is not None and isinstance(response, str)
        print("✅ Chatbot response successful")
        
    except Exception as e:
        print(f"❌ Chatbot test failed: {str(e)}")
        raise

def main():
    """Run all tests"""
    print("\n🔍 Starting configuration and connection tests...\n")
    
    try:
        print("\n📊 Testing MongoDB connection...")
        test_mongodb_connection()
        
        print("\n🤖 Testing OpenAI API connection...")
        test_openai_connection()
        
        print("\n📚 Testing document retrieval system...")
        test_document_retrieval()
        
        print("\n💬 Testing chatbot functionality...")
        test_chatbot()
        
        print("\n✨ All tests passed successfully!")
        
    except Exception as e:
        print(f"\n❌ Tests failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    main()
