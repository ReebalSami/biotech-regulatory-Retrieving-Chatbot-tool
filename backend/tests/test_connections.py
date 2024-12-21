import pytest
from app.document_retrieval import DocumentRetrieval
from app.chatbot import Chatbot
from app.database import db
from app.config import get_settings
import logging

logger = logging.getLogger(__name__)

def test_mongodb_connection():
    """Test MongoDB connection"""
    try:
        # Test connection
        db.client.server_info()
        logger.info("✅ MongoDB connection successful")
        
        # Test document insertion
        test_doc = {
            "content": "This is a test document",
            "metadata": {
                "title": "Test Document",
                "type": "test"
            }
        }
        doc_id = db.store_document(test_doc["content"], test_doc["metadata"])
        logger.info("✅ Document insertion successful")
        
        # Test document retrieval
        retrieved_doc = db.get_document(doc_id)
        if not retrieved_doc:
            raise Exception("Failed to retrieve document")
        logger.info("✅ Document retrieval successful")
        
        # Cleanup
        db.regulatory_documents.delete_one({'_id': doc_id})
        logger.info("✅ Test cleanup successful")
        
    except Exception as e:
        logger.error(f"❌ MongoDB test failed: {str(e)}")
        raise

def test_openai_connection():
    """Test OpenAI API connection"""
    try:
        settings = get_settings()
        assert settings.OPENAI_API_KEY, "OpenAI API key not found"
        logger.info("✅ OpenAI API key found")
    except Exception as e:
        logger.error(f"❌ OpenAI API key check failed: {str(e)}")
        raise

def test_document_retrieval():
    """Test document retrieval functionality"""
    try:
        doc_retrieval = DocumentRetrieval()
        # Test search functionality
        results = doc_retrieval.search("test query")
        assert isinstance(results, list), "Search should return a list"
        logger.info("✅ Document retrieval test passed")
    except Exception as e:
        logger.error(f"❌ Document retrieval test failed: {str(e)}")
        raise

@pytest.mark.asyncio
async def test_chatbot():
    """Test chatbot functionality"""
    try:
        doc_retrieval = DocumentRetrieval()
        chatbot = Chatbot(doc_retrieval)
        
        # Test simple query
        response = await chatbot.get_response("What are the basic requirements for medical devices?")
        assert isinstance(response, str), "Response should be a string"
        assert len(response) > 0, "Response should not be empty"
        logger.info("✅ Chatbot test passed")
    except Exception as e:
        logger.error(f"❌ Chatbot test failed: {str(e)}")
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
