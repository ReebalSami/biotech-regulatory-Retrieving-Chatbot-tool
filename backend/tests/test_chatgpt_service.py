import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException
from openai import AsyncOpenAI
from app.services.chatgpt_service import ChatGPTService

@pytest.fixture
def mock_openai_response():
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(
            message=MagicMock(
                content="Test response"
            )
        )
    ]
    return mock_response

@pytest.fixture
def mock_openai_client():
    mock_client = MagicMock()
    mock_client.chat = MagicMock()
    mock_client.chat.completions = MagicMock()
    mock_client.chat.completions.create = AsyncMock()
    return mock_client

def test_init_without_api_key():
    with patch.dict('os.environ', clear=True):
        with pytest.raises(HTTPException) as exc_info:
            ChatGPTService()
        assert exc_info.value.status_code == 500
        assert "OpenAI API key not found" in str(exc_info.value.detail)

def test_init_with_api_key():
    with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
        with patch('openai.AsyncOpenAI') as mock_openai:
            service = ChatGPTService()
            assert isinstance(service.client, AsyncOpenAI)
            assert service.system_prompt is not None

@pytest.mark.asyncio
async def test_generate_response_success(mock_openai_client, mock_openai_response):
    # Configure the mock response
    mock_response = AsyncMock()
    mock_response.choices = [
        type('Choice', (), {'message': type('Message', (), {'content': 'Test response'})})()
    ]
    mock_openai_client.chat.completions.create.return_value = mock_response

    service = ChatGPTService()
    service.client = mock_openai_client  # Directly set the client

    response = await service.generate_response(
        user_message="Test message",
        context=["Test context"]
    )

    assert response == "Test response"
    mock_openai_client.chat.completions.create.assert_called_once()

@pytest.mark.asyncio
async def test_generate_response_with_empty_context(mock_openai_client, mock_openai_response):
    # Configure the mock response
    mock_response = AsyncMock()
    mock_response.choices = [
        type('Choice', (), {'message': type('Message', (), {'content': 'Test response'})})()
    ]
    mock_openai_client.chat.completions.create.return_value = mock_response

    service = ChatGPTService()
    service.client = mock_openai_client  # Directly set the client

    response = await service.generate_response(
        user_message="Test message",
        context=[]
    )

    assert response == "Test response"
    mock_openai_client.chat.completions.create.assert_called_once()

@pytest.mark.asyncio
async def test_generate_response_api_error(mock_openai_client):
    mock_openai_client.chat.completions.create.side_effect = Exception("API Error")
    
    with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
        with patch('openai.AsyncOpenAI', return_value=mock_openai_client):
            service = ChatGPTService()
            with pytest.raises(HTTPException) as exc_info:
                await service.generate_response("Test message", [])
            
            assert exc_info.value.status_code == 500
            assert "Error generating response" in str(exc_info.value.detail)

@pytest.mark.asyncio
async def test_generate_response_with_long_context(mock_openai_client, mock_openai_response):
    # Configure the mock response
    mock_response = AsyncMock()
    mock_response.choices = [
        type('Choice', (), {'message': type('Message', (), {'content': 'Test response'})})()
    ]
    mock_openai_client.chat.completions.create.return_value = mock_response

    service = ChatGPTService()
    service.client = mock_openai_client  # Directly set the client

    response = await service.generate_response(
        user_message="Test message",
        context=["Long context " * 100],  # Create a long context
        max_tokens=100,
        temperature=0.5
    )

    assert response == "Test response"
    mock_openai_client.chat.completions.create.assert_called_once()

@pytest.mark.asyncio
async def test_generate_response_unexpected_error():
    """Test handling of unexpected errors in generate_response"""
    mock_openai_client = AsyncMock()
    mock_openai_client.chat.completions.create.side_effect = Exception("Unexpected error")

    service = ChatGPTService()
    service.client = mock_openai_client

    with pytest.raises(HTTPException) as exc_info:
        await service.generate_response(
            user_message="Test message",
            context=["Test context"]
        )

    assert exc_info.value.status_code == 500
    assert "Unexpected error" in str(exc_info.value.detail)
