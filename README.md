# LMStudio-MCP

A Model Control Protocol (MCP) server that allows Claude to communicate with locally running LLM models via LM Studio.

<img width="1881" alt="Screenshot 2025-03-22 at 16 50 53" src="https://github.com/user-attachments/assets/c203513b-28db-4be5-8c61-ebb8a24404ce" />

## Overview

LMStudio-MCP creates a bridge between Claude (with MCP capabilities) and your locally running LM Studio instance. This allows Claude to:

- Check the health of your LM Studio API
- List available models
- Get the currently loaded model
- Generate completions using your local models

This enables you to leverage your own locally running models through Claude's interface, combining Claude's capabilities with your private models.

## ⚙️ Configuration

The bridge supports flexible configuration for different deployment scenarios:

- **Default**: Connects to `http://localhost:1234/v1`
- **Custom Host**: Set `LMSTUDIO_HOST` environment variable (e.g., `192.168.1.100`)
- **Custom Port**: Set `LMSTUDIO_PORT` environment variable (e.g., `5678`)

Example:
```bash
export LMSTUDIO_HOST=192.168.1.100
export LMSTUDIO_PORT=5678
python lmstudio_bridge.py
```

📖 **For detailed configuration options**, see [CONFIGURATION.md](CONFIGURATION.md)

## Prerequisites

- Python 3.7+
- [LM Studio](https://lmstudio.ai/) installed and running locally with a model loaded
- Claude with MCP access
- Required Python packages (see Installation)

## 🚀 Quick Installation

### One-Line Install (Recommended)
```bash
curl -fsSL https://raw.githubusercontent.com/infinitimeless/LMStudio-MCP/main/install.sh | bash
```

### Manual Installation Methods

#### 1. Local Python Installation
```bash
git clone https://github.com/infinitimeless/LMStudio-MCP.git
cd LMStudio-MCP
pip install requests "mcp[cli]" openai
```

#### 2. Docker Installation
```bash
# Using pre-built image
docker run -it --network host ghcr.io/infinitimeless/lmstudio-mcp:latest

# Or build locally
git clone https://github.com/infinitimeless/LMStudio-MCP.git
cd LMStudio-MCP
docker build -t lmstudio-mcp .
docker run -it --network host lmstudio-mcp
```

#### 3. Docker Compose
```bash
git clone https://github.com/infinitimeless/LMStudio-MCP.git
cd LMStudio-MCP
docker-compose up -d
```

For detailed deployment instructions, see [DOCKER.md](DOCKER.md).

## MCP Configuration

### Quick Setup

**Using GitHub directly (simplest)**:
```json
{
  "lmstudio-mcp": {
    "command": "uvx",
    "args": [
      "https://github.com/infinitimeless/LMStudio-MCP"
    ]
  }
}
```

**Using local installation**:
```json
{
  "lmstudio-mcp": {
    "command": "/bin/bash",
    "args": [
      "-c",
      "cd /path/to/LMStudio-MCP && source venv/bin/activate && python lmstudio_bridge.py"
    ]
  }
}
```

**Using Docker**:
```json
{
  "lmstudio-mcp-docker": {
    "command": "docker",
    "args": [
      "run",
      "-i",
      "--rm",
      "--network=host",
      "ghcr.io/infinitimeless/lmstudio-mcp:latest"
    ]
  }
}
```

For complete MCP configuration instructions, see [MCP_CONFIGURATION.md](MCP_CONFIGURATION.md).

## Usage

1. **Start LM Studio** and ensure it's running on port 1234 (the default)
2. **Load a model** in LM Studio
3. **Configure Claude MCP** with one of the configurations above
4. **Connect to the MCP server** in Claude when prompted

## Available Functions

The bridge provides the following functions:

- `health_check()`: Verify if LM Studio API is accessible
- `list_models()`: Get a list of all available models in LM Studio
- `get_current_model()`: Identify which model is currently loaded
- `chat_completion(prompt, system_prompt, temperature, max_tokens)`: Generate text from your local model

## Deployment Options

This project supports multiple deployment methods:

| Method | Use Case | Pros | Cons |
|--------|----------|------|------|
| **Local Python** | Development, simple setup | Fast, direct control | Requires Python setup |
| **Docker** | Isolated environments | Clean, portable | Requires Docker |
| **Docker Compose** | Production deployments | Easy management | More complex setup |
| **Kubernetes** | Enterprise/scale | Highly scalable | Complex configuration |
| **GitHub Direct** | Zero setup | No local install needed | Requires internet |

## Known Limitations

- Some models (e.g., phi-3.5-mini-instruct_uncensored) may have compatibility issues
- The bridge currently uses only the OpenAI-compatible API endpoints of LM Studio
- Model responses will be limited by the capabilities of your locally loaded model

## Troubleshooting

### API Connection Issues

If Claude reports 404 errors when trying to connect to LM Studio:
- Ensure LM Studio is running and has a model loaded
- Check that LM Studio's server is running on port 1234
- Verify your firewall isn't blocking the connection
- Try using "127.0.0.1" instead of "localhost" in the API URL if issues persist

### Model Compatibility

If certain models don't work correctly:
- Some models might not fully support the OpenAI chat completions API format
- Try different parameter values (temperature, max_tokens) for problematic models
- Consider switching to a more compatible model if problems persist

For detailed troubleshooting help, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

## 🐳 Docker & Containerization

This project includes comprehensive Docker support:

- **Multi-architecture images** (AMD64, ARM64/Apple Silicon)
- **Automated builds** via GitHub Actions
- **Pre-built images** available on GitHub Container Registry
- **Docker Compose** for easy deployment
- **Kubernetes manifests** for production deployments

See [DOCKER.md](DOCKER.md) for complete containerization documentation.

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT

## Acknowledgements

This project was originally developed as "Claude-LMStudio-Bridge_V2" and has been renamed and open-sourced as "LMStudio-MCP".

---

**🌟 If this project helps you, please consider giving it a star!**
