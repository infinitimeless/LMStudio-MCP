"""
Pytest configuration and shared fixtures for LMStudio-MCP tests
"""

import pytest
import sys
import os
from unittest.mock import patch

# Add parent directory to path so tests can import lmstudio_bridge
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def mock_lmstudio_api_base():
    """Fixture for LM Studio API base URL"""
    return "http://localhost:1234/v1"


@pytest.fixture(autouse=True)
def mock_lmstudio_env(monkeypatch):
    """Automatically set LM Studio environment variables for all tests"""
    import sys

    # Set environment variables
    monkeypatch.setenv("LMSTUDIO_HOST", "localhost")
    monkeypatch.setenv("LMSTUDIO_PORT", "1234")

    # Force module reload if it's already loaded to pick up new env vars
    if 'lmstudio_bridge' in sys.modules:
        del sys.modules['lmstudio_bridge']


@pytest.fixture
def sample_embedding_response():
    """Fixture for sample embedding API response"""
    return {
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
    }


@pytest.fixture
def sample_completion_response():
    """Fixture for sample completion API response"""
    return {
        "id": "cmpl-test",
        "object": "text_completion",
        "created": 1234567890,
        "model": "qwen/qwen3-coder-30b",
        "choices": [
            {
                "text": "This is a test completion.",
                "index": 0,
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 15,
            "total_tokens": 25
        }
    }


@pytest.fixture
def sample_response_api_response():
    """Fixture for sample /v1/responses API response"""
    return {
        "id": "resp-test-123",
        "object": "response",
        "created": 1234567890,
        "output": "This is a stateful response.",
        "model": "qwen/qwen3-coder-30b",
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 15,
            "total_tokens": 25
        }
    }
