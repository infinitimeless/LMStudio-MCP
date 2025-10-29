"""
Tests for text_completion() function in lmstudio_bridge.py

Tests the /v1/completions endpoint implementation including:
- Simple text completion
- Custom temperature parameter
- Stop sequences parameter
- Edge cases (empty prompt, empty response)
- Error handling (API errors, connection failures)
"""

import pytest
from unittest.mock import patch, Mock
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestTextCompletion:
    """Test suite for text_completion function"""

    @pytest.mark.asyncio
    @patch('requests.post')
    async def test_simple_completion_success(self, mock_post):
        """Test basic text completion functionality"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"text": "completed text", "index": 0, "finish_reason": "stop"}]
        }
        mock_post.return_value = mock_response

        from lmstudio_bridge import text_completion
        result = await text_completion("test prompt")

        assert result == "completed text"
        mock_post.assert_called_once()
        # Verify the correct endpoint was called
        assert mock_post.call_args[0][0] == "http://localhost:1234/v1/completions"

    @pytest.mark.asyncio
    @patch('requests.post')
    async def test_completion_with_custom_temperature(self, mock_post):
        """Test text completion with custom temperature parameter"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"text": "temperature test result", "index": 0}]
        }
        mock_post.return_value = mock_response

        from lmstudio_bridge import text_completion
        result = await text_completion("test prompt", temperature=0.5)

        assert result == "temperature test result"
        # Verify parameters were passed correctly
        call_args = mock_post.call_args
        assert call_args[1]["json"]["temperature"] == 0.5

    @pytest.mark.asyncio
    @patch('requests.post')
    async def test_completion_with_max_tokens(self, mock_post):
        """Test text completion with custom max_tokens parameter"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"text": "max tokens test", "index": 0}]
        }
        mock_post.return_value = mock_response

        from lmstudio_bridge import text_completion
        result = await text_completion("test prompt", max_tokens=512)

        assert result == "max tokens test"
        # Verify max_tokens was passed correctly
        call_args = mock_post.call_args
        assert call_args[1]["json"]["max_tokens"] == 512

    @pytest.mark.asyncio
    @patch('requests.post')
    async def test_completion_with_stop_sequences(self, mock_post):
        """Test text completion with stop sequences parameter"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"text": "stop sequence test", "index": 0}]
        }
        mock_post.return_value = mock_response

        from lmstudio_bridge import text_completion
        result = await text_completion("test prompt", stop_sequences=["\n", "END"])

        assert result == "stop sequence test"
        # Verify stop sequences were passed correctly
        call_args = mock_post.call_args
        assert call_args[1]["json"]["stop"] == ["\n", "END"]

    @pytest.mark.asyncio
    @patch('requests.post')
    async def test_empty_prompt(self, mock_post):
        """Test text completion with empty prompt"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"text": "", "index": 0}]
        }
        mock_post.return_value = mock_response

        from lmstudio_bridge import text_completion
        result = await text_completion("")

        # Empty completion should return error message
        assert result == "Error: Empty completion from model"

    @pytest.mark.asyncio
    @patch('requests.post')
    async def test_api_error_status_code(self, mock_post):
        """Test text completion with API error status codes"""
        # Test 500 error
        mock_response_500 = Mock()
        mock_response_500.status_code = 500
        mock_post.return_value = mock_response_500

        from lmstudio_bridge import text_completion
        result = await text_completion("test prompt")

        assert "Error: LM Studio returned status code 500" in result

        # Test 404 error
        mock_response_404 = Mock()
        mock_response_404.status_code = 404
        mock_post.return_value = mock_response_404

        result = await text_completion("test prompt")

        assert "Error: LM Studio returned status code 404" in result

    @pytest.mark.asyncio
    @patch('requests.post')
    async def test_request_exception(self, mock_post):
        """Test text completion with request exceptions"""
        mock_post.side_effect = Exception("Connection failed")

        from lmstudio_bridge import text_completion
        result = await text_completion("test prompt")

        assert "Error generating text completion" in result
        assert "Connection failed" in result

    @pytest.mark.asyncio
    @patch('requests.post')
    async def test_no_choices_returned(self, mock_post):
        """Test text completion when no choices are returned"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": []
        }
        mock_post.return_value = mock_response

        from lmstudio_bridge import text_completion
        result = await text_completion("test prompt")

        assert result == "Error: No completion generated"

    @pytest.mark.asyncio
    @patch('requests.post')
    async def test_empty_text_content(self, mock_post):
        """Test text completion with empty text content"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"text": "", "index": 0}]
        }
        mock_post.return_value = mock_response

        from lmstudio_bridge import text_completion
        result = await text_completion("test prompt")

        assert result == "Error: Empty completion from model"

    @pytest.mark.asyncio
    @patch('requests.post')
    async def test_timeout_configuration(self, mock_post):
        """Test that timeout is properly configured"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"text": "timeout test", "index": 0}]
        }
        mock_post.return_value = mock_response

        from lmstudio_bridge import text_completion
        await text_completion("test prompt")

        # Verify timeout is set to 30 seconds
        call_args = mock_post.call_args
        assert call_args[1]["timeout"] == 30


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
