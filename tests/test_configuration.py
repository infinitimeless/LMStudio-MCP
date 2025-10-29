"""
Tests for LMStudio bridge configuration (host/port)

Verifies that the bridge can be configured via environment variables
to connect to LM Studio instances on different hosts/ports.
"""

import pytest
from unittest.mock import patch, Mock
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestConfiguration:
    """Test suite for configuration flexibility"""

    def test_default_configuration(self):
        """Test that default host and port are set correctly"""
        # Clear any existing env vars
        with patch.dict(os.environ, {}, clear=True):
            # Reload module to get fresh configuration
            if 'lmstudio_bridge' in sys.modules:
                del sys.modules['lmstudio_bridge']

            import lmstudio_bridge

            assert lmstudio_bridge.LMSTUDIO_HOST == "localhost"
            assert lmstudio_bridge.LMSTUDIO_PORT == "1234"
            assert lmstudio_bridge.LMSTUDIO_API_BASE == "http://localhost:1234/v1"

    def test_custom_host_configuration(self):
        """Test that custom host can be set via environment variable"""
        with patch.dict(os.environ, {"LMSTUDIO_HOST": "192.168.1.100", "LMSTUDIO_PORT": "1234"}):
            # Reload module to get fresh configuration
            if 'lmstudio_bridge' in sys.modules:
                del sys.modules['lmstudio_bridge']

            import lmstudio_bridge

            assert lmstudio_bridge.LMSTUDIO_HOST == "192.168.1.100"
            assert lmstudio_bridge.LMSTUDIO_API_BASE == "http://192.168.1.100:1234/v1"

    def test_custom_port_configuration(self):
        """Test that custom port can be set via environment variable"""
        with patch.dict(os.environ, {"LMSTUDIO_HOST": "localhost", "LMSTUDIO_PORT": "5678"}):
            # Reload module to get fresh configuration
            if 'lmstudio_bridge' in sys.modules:
                del sys.modules['lmstudio_bridge']

            import lmstudio_bridge

            assert lmstudio_bridge.LMSTUDIO_PORT == "5678"
            assert lmstudio_bridge.LMSTUDIO_API_BASE == "http://localhost:5678/v1"

    def test_custom_host_and_port_configuration(self):
        """Test that both host and port can be customized together"""
        with patch.dict(os.environ, {"LMSTUDIO_HOST": "10.0.0.50", "LMSTUDIO_PORT": "8080"}):
            # Reload module to get fresh configuration
            if 'lmstudio_bridge' in sys.modules:
                del sys.modules['lmstudio_bridge']

            import lmstudio_bridge

            assert lmstudio_bridge.LMSTUDIO_HOST == "10.0.0.50"
            assert lmstudio_bridge.LMSTUDIO_PORT == "8080"
            assert lmstudio_bridge.LMSTUDIO_API_BASE == "http://10.0.0.50:8080/v1"

    @pytest.mark.asyncio
    @patch('requests.get')
    async def test_health_check_uses_configured_base_url(self, mock_get):
        """Test that health_check uses the configured base URL"""
        with patch.dict(os.environ, {"LMSTUDIO_HOST": "192.168.1.50", "LMSTUDIO_PORT": "9999"}):
            # Reload module to get fresh configuration
            if 'lmstudio_bridge' in sys.modules:
                del sys.modules['lmstudio_bridge']

            from lmstudio_bridge import health_check, LMSTUDIO_API_BASE

            mock_response = Mock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            await health_check()

            # Verify it used the configured base URL
            expected_url = f"{LMSTUDIO_API_BASE}/models"
            assert expected_url == "http://192.168.1.50:9999/v1/models"
            mock_get.assert_called_once_with(expected_url)

    @pytest.mark.asyncio
    @patch('requests.post')
    async def test_chat_completion_uses_configured_base_url(self, mock_post):
        """Test that chat_completion uses the configured base URL"""
        with patch.dict(os.environ, {"LMSTUDIO_HOST": "remote-server", "LMSTUDIO_PORT": "7777"}):
            # Reload module to get fresh configuration
            if 'lmstudio_bridge' in sys.modules:
                del sys.modules['lmstudio_bridge']

            from lmstudio_bridge import chat_completion, LMSTUDIO_API_BASE

            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "choices": [{"message": {"content": "Response"}}]
            }
            mock_post.return_value = mock_response

            await chat_completion("test")

            # Verify it used the configured base URL
            expected_url = f"{LMSTUDIO_API_BASE}/chat/completions"
            assert expected_url == "http://remote-server:7777/v1/chat/completions"
            mock_post.assert_called_once()
            assert mock_post.call_args[0][0] == expected_url

        # Cleanup: Reset module to default configuration
        if 'lmstudio_bridge' in sys.modules:
            del sys.modules['lmstudio_bridge']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
