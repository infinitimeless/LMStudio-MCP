"""
Tests for create_response() function in lmstudio_bridge.py

Tests the /v1/responses endpoint implementation including:
- Simple response creation
- Conversation continuity with previous_response_id
- Reasoning effort parameter (low/medium/high)
- Stream parameter handling
- Error handling (API errors, connection failures)
"""

import pytest
import json
from unittest.mock import patch, Mock
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestCreateResponse:
    """Test suite for create_response function"""

    @pytest.mark.asyncio
    @patch('requests.post')
    async def test_simple_response_success(self, mock_post):
        """Test basic response creation functionality"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = json.dumps({
            "id": "resp-test-123",
            "output": "This is a stateful response.",
            "usage": {"prompt_tokens": 10, "completion_tokens": 15, "total_tokens": 25}
        })
        mock_post.return_value = mock_response

        from lmstudio_bridge import create_response
        result = await create_response("test input")

        # Verify JSON response structure is preserved
        result_data = json.loads(result)
        assert "id" in result_data
        assert result_data["id"] == "resp-test-123"
        assert result_data["output"] == "This is a stateful response."
        mock_post.assert_called_once()
        # Verify the correct endpoint was called
        assert mock_post.call_args[0][0] == "http://localhost:1234/v1/responses"

    @pytest.mark.asyncio
    @patch('requests.post')
    async def test_response_with_previous_id(self, mock_post):
        """Test response creation with previous response ID"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = json.dumps({
            "id": "resp-test-456",
            "output": "Response with context.",
            "usage": {"prompt_tokens": 10, "completion_tokens": 15, "total_tokens": 25}
        })
        mock_post.return_value = mock_response

        from lmstudio_bridge import create_response
        result = await create_response("test input", previous_response_id="prev-123")

        # Verify previous response ID was passed
        call_args = mock_post.call_args
        assert call_args[1]["json"]["previous_response_id"] == "prev-123"

        # Verify response is valid
        result_data = json.loads(result)
        assert result_data["id"] == "resp-test-456"

    @pytest.mark.asyncio
    @patch('requests.post')
    async def test_response_with_reasoning_effort_low(self, mock_post):
        """Test response creation with low reasoning effort"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = json.dumps({
            "id": "resp-test-789",
            "output": "Low reasoning response.",
            "usage": {"prompt_tokens": 10, "completion_tokens": 15, "total_tokens": 25}
        })
        mock_post.return_value = mock_response

        from lmstudio_bridge import create_response
        result = await create_response("test input", reasoning_effort="low")

        call_args = mock_post.call_args
        assert call_args[1]["json"]["reasoning"]["effort"] == "low"

    @pytest.mark.asyncio
    @patch('requests.post')
    async def test_response_with_reasoning_effort_medium(self, mock_post):
        """Test response creation with medium reasoning effort"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = json.dumps({
            "id": "resp-test-medium",
            "output": "Medium reasoning response.",
            "usage": {"prompt_tokens": 10, "completion_tokens": 15, "total_tokens": 25}
        })
        mock_post.return_value = mock_response

        from lmstudio_bridge import create_response
        result = await create_response("test input", reasoning_effort="medium")

        call_args = mock_post.call_args
        assert call_args[1]["json"]["reasoning"]["effort"] == "medium"

    @pytest.mark.asyncio
    @patch('requests.post')
    async def test_response_with_reasoning_effort_high(self, mock_post):
        """Test response creation with high reasoning effort"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = json.dumps({
            "id": "resp-test-high",
            "output": "High reasoning response.",
            "usage": {"prompt_tokens": 10, "completion_tokens": 15, "total_tokens": 25}
        })
        mock_post.return_value = mock_response

        from lmstudio_bridge import create_response
        result = await create_response("test input", reasoning_effort="high")

        call_args = mock_post.call_args
        assert call_args[1]["json"]["reasoning"]["effort"] == "high"

    @pytest.mark.asyncio
    @patch('requests.post')
    async def test_response_with_stream_false(self, mock_post):
        """Test response creation with stream=False"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = json.dumps({
            "id": "resp-test-stream",
            "output": "Stream response.",
            "usage": {"prompt_tokens": 10, "completion_tokens": 15, "total_tokens": 25}
        })
        mock_post.return_value = mock_response

        from lmstudio_bridge import create_response
        result = await create_response("test input", stream=False)

        call_args = mock_post.call_args
        assert call_args[1]["json"]["stream"] is False

    @pytest.mark.asyncio
    @patch('requests.post')
    async def test_response_with_stream_true(self, mock_post):
        """Test response creation with stream=True"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = json.dumps({
            "id": "resp-test-stream-true",
            "output": "Streaming response.",
            "usage": {"prompt_tokens": 10, "completion_tokens": 15, "total_tokens": 25}
        })
        mock_post.return_value = mock_response

        from lmstudio_bridge import create_response
        result = await create_response("test input", stream=True)

        call_args = mock_post.call_args
        assert call_args[1]["json"]["stream"] is True

    @pytest.mark.asyncio
    @patch('requests.post')
    async def test_api_error_status_code(self, mock_post):
        """Test response creation with API error status codes"""
        # Test 500 error
        mock_response_500 = Mock()
        mock_response_500.status_code = 500
        mock_post.return_value = mock_response_500

        from lmstudio_bridge import create_response
        result = await create_response("test input")

        result_data = json.loads(result)
        assert "error" in result_data
        assert "500" in result_data["error"]

        # Test 404 error
        mock_response_404 = Mock()
        mock_response_404.status_code = 404
        mock_post.return_value = mock_response_404

        result = await create_response("test input")

        result_data = json.loads(result)
        assert "error" in result_data
        assert "404" in result_data["error"]

    @pytest.mark.asyncio
    @patch('requests.post')
    async def test_request_exception(self, mock_post):
        """Test response creation with request exceptions"""
        mock_post.side_effect = Exception("Connection failed")

        from lmstudio_bridge import create_response
        result = await create_response("test input")

        result_data = json.loads(result)
        assert "error" in result_data
        assert "Connection failed" in result_data["error"]

    @pytest.mark.asyncio
    @patch('requests.post')
    async def test_invalid_reasoning_effort(self, mock_post):
        """Test response creation with invalid reasoning effort"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = json.dumps({
            "id": "resp-test-invalid",
            "output": "Response with invalid reasoning.",
            "usage": {"prompt_tokens": 10, "completion_tokens": 15, "total_tokens": 25}
        })
        mock_post.return_value = mock_response

        from lmstudio_bridge import create_response
        result = await create_response("test input", reasoning_effort="invalid")

        # With invalid reasoning effort, should not include reasoning in payload
        call_args = mock_post.call_args
        # The implementation only adds reasoning if effort is in ["low", "medium", "high"]
        assert "reasoning" not in call_args[1]["json"]

    @pytest.mark.asyncio
    @patch('requests.post')
    async def test_timeout_configuration(self, mock_post):
        """Test that create_response uses proper timeout (60 seconds)"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = json.dumps({
            "id": "resp-test-timeout",
            "output": "Timeout test response.",
            "usage": {"prompt_tokens": 10, "completion_tokens": 15, "total_tokens": 25}
        })
        mock_post.return_value = mock_response

        from lmstudio_bridge import create_response
        await create_response("test input")

        # Verify timeout is set to 60 seconds (for reasoning tasks)
        call_args = mock_post.call_args
        assert call_args[1]["timeout"] == 60

    @pytest.mark.asyncio
    @patch('requests.post')
    async def test_complete_conversation_flow(self, mock_post):
        """Test a complete conversation flow with multiple turns"""
        # First response
        mock_response_1 = Mock()
        mock_response_1.status_code = 200
        mock_response_1.text = json.dumps({
            "id": "resp-turn-1",
            "output": "First response.",
            "usage": {"prompt_tokens": 5, "completion_tokens": 10, "total_tokens": 15}
        })
        mock_post.return_value = mock_response_1

        from lmstudio_bridge import create_response
        result_1 = await create_response("Hello")

        response_1_data = json.loads(result_1)
        first_id = response_1_data["id"]

        # Second response referencing first
        mock_response_2 = Mock()
        mock_response_2.status_code = 200
        mock_response_2.text = json.dumps({
            "id": "resp-turn-2",
            "output": "Second response with context.",
            "usage": {"prompt_tokens": 15, "completion_tokens": 12, "total_tokens": 27}
        })
        mock_post.return_value = mock_response_2

        result_2 = await create_response("Continue", previous_response_id=first_id)

        # Verify conversation continuity
        response_2_data = json.loads(result_2)
        assert response_2_data["id"] == "resp-turn-2"

        # Verify the second call included the previous response ID
        call_args = mock_post.call_args
        assert call_args[1]["json"]["previous_response_id"] == first_id


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
