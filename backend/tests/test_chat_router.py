from unittest.mock import patch, AsyncMock, MagicMock
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.routers.chat import router, get_chatgpt_service
from app.services.chatgpt_service import ChatGPTService

# Create a fixture for the FastAPI app
@pytest.fixture
def app():
    app = FastAPI()
    app.include_router(router)
    return app

@pytest.fixture
def client(app):
    return TestClient(app)

@pytest.fixture
def mock_openai():
    mock_openai = AsyncMock()
    mock_openai.chat.completions.create = AsyncMock()
    return mock_openai

@pytest.fixture
def chat_service(mock_openai):
    with patch('app.services.chatgpt_service.AsyncOpenAI', return_value=mock_openai), \
         patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
        service = ChatGPTService()
        return service

@pytest.mark.asyncio
async def test_chat_endpoint_success(client, chat_service, mock_openai):
    """Test successful chat endpoint interaction"""
    # Configure the mock response
    response_obj = AsyncMock()
    response_obj.choices = [AsyncMock(message=AsyncMock(content="Test response"))]
    mock_openai.chat.completions.create.return_value = response_obj

    # Test with valid request
    with patch('app.routers.chat.ChatGPTService', return_value=chat_service):
        response = client.post("/chat", json={
            "message": "Test message",
            "context": ["Test context"]
        })
        
        assert response.status_code == 200
        assert response.json() == {"response": "Test response"}
        mock_openai.chat.completions.create.assert_called_once()

@pytest.mark.asyncio
async def test_chat_endpoint_no_message(client, chat_service):
    """Test chat endpoint with missing message field"""
    # Test with missing message
    with patch('app.routers.chat.ChatGPTService', return_value=chat_service):
        response = client.post("/chat", json={
            "context": ["Test context"]
        })
        
        assert response.status_code == 422

@pytest.mark.asyncio
async def test_chat_endpoint_empty_message(client, chat_service):
    """Test chat endpoint with empty message"""
    # Test with empty message
    with patch('app.routers.chat.ChatGPTService', return_value=chat_service):
        response = client.post("/chat", json={
            "message": "",
            "context": ["Test context"]
        })
        
        assert response.status_code == 400
        assert "Message cannot be empty" in response.json()["detail"]

@pytest.mark.asyncio
async def test_chat_endpoint_no_context(client, chat_service, mock_openai):
    """Test chat endpoint with missing context field"""
    # Configure the mock response
    response_obj = AsyncMock()
    response_obj.choices = [AsyncMock(message=AsyncMock(content="Test response"))]
    mock_openai.chat.completions.create.return_value = response_obj

    # Test with missing context (should default to empty list)
    with patch('app.routers.chat.ChatGPTService', return_value=chat_service):
        response = client.post("/chat", json={
            "message": "Test message"
        })
        
        assert response.status_code == 200
        assert response.json() == {"response": "Test response"}
        mock_openai.chat.completions.create.assert_called_once()

@pytest.mark.asyncio
async def test_chat_endpoint_service_error(client, chat_service, mock_openai):
    """Test chat endpoint when service raises an error"""
    # Configure the mock to raise an exception
    mock_openai.chat.completions.create.side_effect = Exception("Test error")

    # Test with valid request but service throws error
    with patch('app.routers.chat.ChatGPTService', return_value=chat_service):
        response = client.post("/chat", json={
            "message": "Test message",
            "context": ["Test context"]
        })
        
        assert response.status_code == 500
        assert "Test error" in response.json()["detail"]
        mock_openai.chat.completions.create.assert_called_once()

@pytest.mark.asyncio
async def test_chat_endpoint_invalid_request(client, chat_service):
    """Test chat endpoint with invalid request data"""
    # Test with invalid request data structure
    with patch('app.routers.chat.ChatGPTService', return_value=chat_service):
        response = client.post("/chat", json={
            "invalid_field": "should not be here"
        })
        
        assert response.status_code == 422  # Unprocessable Entity

@pytest.mark.asyncio
async def test_chat_endpoint_internal_error(client, chat_service, mock_openai):
    """Test chat endpoint when an internal error occurs"""
    # Configure the mock to raise an exception
    mock_openai.chat.completions.create.side_effect = Exception("Internal server error")

    # Test with valid request but service throws error
    with patch('app.routers.chat.ChatGPTService', return_value=chat_service):
        response = client.post("/chat", json={
            "message": "Test message",
            "context": ["Test context"]
        })
        
        assert response.status_code == 500
        assert "Internal server error" in response.json()["detail"]
