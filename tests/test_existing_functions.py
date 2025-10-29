"""
Tests for existing functions in lmstudio_bridge.py

Tests the original 4 endpoints to ensure they still work after our changes:
- health_check()
- list_models()
- get_current_model()
- chat_completion()
"""

import pytest
import json
from unittest.mock import patch, Mock
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestHealthCheck:
    """Test suite for health_check function"""

    @pytest.mark.asyncio
    @patch('requests.get')
    async def test_health_check_success(self, mock_get):
        """Test health check when API is accessible"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        from lmstudio_bridge import health_check

        result = await health_check()

        # Verify correct success message
        assert result == "LM Studio API is running and accessible."

        # Verify correct endpoint was called
        mock_get.assert_called_once_with("http://localhost:1234/v1/models")

    @pytest.mark.asyncio
    @patch('requests.get')
    async def test_health_check_non_200_status(self, mock_get):
        """Test health check when API returns non-200"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        from lmstudio_bridge import health_check

        result = await health_check()

        assert "status code 500" in result

    @pytest.mark.asyncio
    @patch('requests.get')
    async def test_health_check_connection_error(self, mock_get):
        """Test health check when connection fails"""
        mock_get.side_effect = Exception("Connection refused")

        from lmstudio_bridge import health_check

        result = await health_check()

        assert "Error connecting to LM Studio API" in result
        assert "Connection refused" in result


class TestListModels:
    """Test suite for list_models function"""

    @pytest.mark.asyncio
    @patch('requests.get')
    async def test_list_models_success(self, mock_get):
        """Test listing models when API returns models"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {"id": "qwen/qwen3-coder-30b"},
                {"id": "llama-3.2-3b-instruct"}
            ]
        }
        mock_get.return_value = mock_response

        from lmstudio_bridge import list_models

        result = await list_models()

        # Verify response contains expected content
        assert "Available models in LM Studio" in result
        assert "qwen/qwen3-coder-30b" in result
        assert "llama-3.2-3b-instruct" in result

        # Verify correct endpoint was called
        mock_get.assert_called_once_with("http://localhost:1234/v1/models")

    @pytest.mark.asyncio
    @patch('requests.get')
    async def test_list_models_empty(self, mock_get):
        """Test listing models when no models found"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": []}
        mock_get.return_value = mock_response

        from lmstudio_bridge import list_models

        result = await list_models()

        assert "No models found in LM Studio" in result

    @pytest.mark.asyncio
    @patch('requests.get')
    async def test_list_models_error(self, mock_get):
        """Test listing models when API call fails"""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        from lmstudio_bridge import list_models

        result = await list_models()

        assert "Failed to fetch models" in result
        assert "404" in result


class TestGetCurrentModel:
    """Test suite for get_current_model function"""

    @pytest.mark.asyncio
    @patch('requests.post')
    async def test_get_current_model_success(self, mock_post):
        """Test getting current model successfully"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "model": "qwen/qwen3-coder-30b"
        }
        mock_post.return_value = mock_response

        from lmstudio_bridge import get_current_model

        result = await get_current_model()

        assert "Currently loaded model: qwen/qwen3-coder-30b" in result

    @pytest.mark.asyncio
    @patch('requests.post')
    async def test_get_current_model_error(self, mock_post):
        """Test getting current model when API call fails"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_post.return_value = mock_response

        from lmstudio_bridge import get_current_model

        result = await get_current_model()

        assert "Failed to identify current model" in result


class TestChatCompletion:
    """Test suite for chat_completion function"""

    @pytest.mark.asyncio
    @patch('requests.post')
    async def test_chat_completion_simple(self, mock_post):
        """Test simple chat completion"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "Hello! How can I help you?"
                    }
                }
            ]
        }
        mock_post.return_value = mock_response

        from lmstudio_bridge import chat_completion

        result = await chat_completion("Hello")

        assert result == "Hello! How can I help you?"

        # Verify API call with correct endpoint
        call_args = mock_post.call_args
        assert call_args[0][0] == "http://localhost:1234/v1/chat/completions"

        # Verify request payload structure
        request_payload = call_args[1]["json"]
        assert "messages" in request_payload
        assert "temperature" in request_payload
        assert "max_tokens" in request_payload

        # Verify messages content
        messages = request_payload["messages"]
        assert len(messages) == 1
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "Hello"

    @pytest.mark.asyncio
    @patch('requests.post')
    async def test_chat_completion_with_system_prompt(self, mock_post):
        """Test chat completion with system prompt"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Response"}}]
        }
        mock_post.return_value = mock_response

        from lmstudio_bridge import chat_completion

        await chat_completion("Hello", system_prompt="You are a helpful assistant")

        # Verify system message included
        call_args = mock_post.call_args
        messages = call_args[1]["json"]["messages"]
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == "You are a helpful assistant"
        assert messages[1]["role"] == "user"

    @pytest.mark.asyncio
    @patch('requests.post')
    async def test_chat_completion_parameters(self, mock_post):
        """Test chat completion with custom parameters"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Response"}}]
        }
        mock_post.return_value = mock_response

        from lmstudio_bridge import chat_completion

        await chat_completion("Test", temperature=0.5, max_tokens=512)

        # Verify parameters passed correctly
        call_args = mock_post.call_args
        request_payload = call_args[1]["json"]

        # Verify all expected parameters are present
        assert request_payload["temperature"] == 0.5
        assert request_payload["max_tokens"] == 512
        assert "messages" in request_payload

        # Verify endpoint
        assert call_args[0][0] == "http://localhost:1234/v1/chat/completions"

    @pytest.mark.asyncio
    @patch('requests.post')
    async def test_chat_completion_no_choices(self, mock_post):
        """Test error when no choices returned"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"choices": []}
        mock_post.return_value = mock_response

        from lmstudio_bridge import chat_completion

        result = await chat_completion("Test")

        assert "Error: No response generated" in result

    @pytest.mark.asyncio
    @patch('requests.post')
    async def test_chat_completion_empty_content(self, mock_post):
        """Test error when empty content returned"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": ""}}]
        }
        mock_post.return_value = mock_response

        from lmstudio_bridge import chat_completion

        result = await chat_completion("Test")

        assert "Error: Empty response from model" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
