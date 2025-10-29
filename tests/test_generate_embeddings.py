"""
Tests for generate_embeddings() function in lmstudio_bridge.py

Tests the /v1/embeddings endpoint implementation including:
- Single text embedding
- Batch text embedding (list of strings)
- Model parameter handling
- Error handling (server down, invalid response)
- JSON response parsing
"""

import pytest
import json
from unittest.mock import patch, MagicMock, Mock
import sys
import os

# Add parent directory to path to import the module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# We need to test the function directly, but it's decorated with @mcp.tool()
# For now, we'll mock the requests calls


class TestGenerateEmbeddings:
    """Test suite for generate_embeddings function"""

    @pytest.mark.asyncio
    @patch('requests.post')
    async def test_single_text_embedding_success(self, mock_post):
        """Test embedding generation for a single text string"""
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = json.dumps({
            "object": "list",
            "data": [
                {
                    "object": "embedding",
                    "embedding": [0.1, 0.2, 0.3, -0.4, 0.5],
                    "index": 0
                }
            ],
            "model": "text-embedding-nomic-embed-text-v1.5",
            "usage": {
                "prompt_tokens": 5,
                "total_tokens": 5
            }
        })
        mock_post.return_value = mock_response

        # Import and test
        from lmstudio_bridge import generate_embeddings

        result = await generate_embeddings("Hello world")

        # Verify the result is valid JSON
        result_data = json.loads(result)
        assert "data" in result_data
        assert len(result_data["data"]) == 1
        assert "embedding" in result_data["data"][0]
        assert len(result_data["data"][0]["embedding"]) == 5

        # Verify API was called correctly
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0] == "http://localhost:1234/v1/embeddings"
        assert call_args[1]["json"]["input"] == "Hello world"
        assert call_args[1]["timeout"] == 30

    @pytest.mark.asyncio
    @patch('requests.post')
    async def test_batch_embedding_with_multiple_texts(self, mock_post):
        """Test embedding generation for multiple texts (batch processing)"""
        # Mock successful API response for batch
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = json.dumps({
            "object": "list",
            "data": [
                {
                    "object": "embedding",
                    "embedding": [0.1, 0.2, 0.3],
                    "index": 0
                },
                {
                    "object": "embedding",
                    "embedding": [0.4, 0.5, 0.6],
                    "index": 1
                }
            ],
            "model": "text-embedding-nomic-embed-text-v1.5",
            "usage": {
                "prompt_tokens": 10,
                "total_tokens": 10
            }
        })
        mock_post.return_value = mock_response

        from lmstudio_bridge import generate_embeddings

        texts = ["First text", "Second text"]
        result = await generate_embeddings(texts)

        # Verify the result structure
        result_data = json.loads(result)
        assert len(result_data["data"]) == 2
        assert result_data["data"][0]["index"] == 0
        assert result_data["data"][1]["index"] == 1

        # Verify response structure consistency
        assert result_data["object"] == "list"
        assert "usage" in result_data

        # Verify API was called with list and correct endpoint
        call_args = mock_post.call_args
        assert call_args[0][0] == "http://localhost:1234/v1/embeddings"
        assert call_args[1]["json"]["input"] == texts
        assert call_args[1]["timeout"] == 30

    @pytest.mark.asyncio
    @patch('requests.post')
    async def test_custom_model_parameter(self, mock_post):
        """Test that custom model parameter is passed correctly"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = json.dumps({
            "object": "list",
            "data": [{"object": "embedding", "embedding": [0.1], "index": 0}],
            "model": "custom-model",
            "usage": {"prompt_tokens": 5, "total_tokens": 5}
        })
        mock_post.return_value = mock_response

        from lmstudio_bridge import generate_embeddings

        await generate_embeddings("test", model="custom-model")

        # Verify model was passed in request
        call_args = mock_post.call_args
        assert call_args[1]["json"]["model"] == "custom-model"

    @pytest.mark.asyncio
    @patch('requests.post')
    async def test_default_model_not_sent(self, mock_post):
        """Test that 'default' model value is not sent to API"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = json.dumps({
            "object": "list",
            "data": [{"object": "embedding", "embedding": [0.1], "index": 0}],
            "usage": {"prompt_tokens": 5, "total_tokens": 5}
        })
        mock_post.return_value = mock_response

        from lmstudio_bridge import generate_embeddings

        await generate_embeddings("test", model="default")

        # Verify 'model' key is not in request when default
        call_args = mock_post.call_args
        assert "model" not in call_args[1]["json"]

    @pytest.mark.asyncio
    @patch('requests.post')
    async def test_api_error_status_code(self, mock_post):
        """Test error handling when API returns non-200 status"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_post.return_value = mock_response

        from lmstudio_bridge import generate_embeddings

        result = await generate_embeddings("test")

        # Verify error is returned as JSON
        result_data = json.loads(result)
        assert "error" in result_data
        assert "500" in result_data["error"]

    @pytest.mark.asyncio
    @patch('requests.post')
    async def test_request_exception_handling(self, mock_post):
        """Test error handling when request raises exception"""
        mock_post.side_effect = Exception("Connection refused")

        from lmstudio_bridge import generate_embeddings

        result = await generate_embeddings("test")

        # Verify error is returned as JSON
        result_data = json.loads(result)
        assert "error" in result_data
        assert "Connection refused" in result_data["error"]

    @pytest.mark.asyncio
    @patch('requests.post')
    async def test_timeout_configuration(self, mock_post):
        """Test that timeout is properly configured"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = json.dumps({
            "object": "list",
            "data": [{"object": "embedding", "embedding": [0.1], "index": 0}],
            "usage": {"prompt_tokens": 5, "total_tokens": 5}
        })
        mock_post.return_value = mock_response

        from lmstudio_bridge import generate_embeddings

        await generate_embeddings("test")

        # Verify timeout is set to 30 seconds
        call_args = mock_post.call_args
        assert call_args[1]["timeout"] == 30

    @pytest.mark.asyncio
    @patch('requests.post')
    async def test_empty_string_input(self, mock_post):
        """Test embedding generation with empty string input"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = json.dumps({
            "object": "list",
            "data": [{"object": "embedding", "embedding": [0.0], "index": 0}],
            "usage": {"prompt_tokens": 0, "total_tokens": 0}
        })
        mock_post.return_value = mock_response

        from lmstudio_bridge import generate_embeddings

        result = await generate_embeddings("")

        # Verify the API call was made with empty string
        call_args = mock_post.call_args
        assert call_args[1]["json"]["input"] == ""

        # Verify result is valid JSON
        result_data = json.loads(result)
        assert "data" in result_data

    @pytest.mark.asyncio
    @patch('requests.post')
    async def test_empty_list_input(self, mock_post):
        """Test embedding generation with empty list input"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = json.dumps({
            "object": "list",
            "data": [],
            "usage": {"prompt_tokens": 0, "total_tokens": 0}
        })
        mock_post.return_value = mock_response

        from lmstudio_bridge import generate_embeddings

        result = await generate_embeddings([])

        # Verify the API call was made with empty list
        call_args = mock_post.call_args
        assert call_args[1]["json"]["input"] == []

        # Verify result is valid JSON with empty data
        result_data = json.loads(result)
        assert "data" in result_data
        assert len(result_data["data"]) == 0

    @pytest.mark.asyncio
    @patch('requests.post')
    async def test_malformed_json_response(self, mock_post):
        """Test handling of malformed JSON response from API"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "This is not valid JSON {broken"
        mock_post.return_value = mock_response

        from lmstudio_bridge import generate_embeddings

        result = await generate_embeddings("test")

        # Should return the malformed response as-is since we return response.text
        # In a real scenario, the client would need to handle JSON parsing errors
        assert result == "This is not valid JSON {broken"

    @pytest.mark.asyncio
    @patch('requests.post')
    async def test_response_structure_validation(self, mock_post):
        """Test that response structure contains all expected fields"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = json.dumps({
            "object": "list",
            "data": [{"object": "embedding", "embedding": [0.1, 0.2], "index": 0}],
            "model": "test-model",
            "usage": {"prompt_tokens": 3, "total_tokens": 3}
        })
        mock_post.return_value = mock_response

        from lmstudio_bridge import generate_embeddings

        result = await generate_embeddings("test", model="test-model")

        # Verify all expected fields are present in response
        result_data = json.loads(result)
        assert "object" in result_data
        assert "data" in result_data
        assert "model" in result_data
        assert "usage" in result_data

        # Verify embedding structure
        assert "embedding" in result_data["data"][0]
        assert "index" in result_data["data"][0]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
