#!/usr/bin/env python3
from mcp.server.fastmcp import FastMCP
import requests
import json
import sys
import os
from typing import List, Dict, Any, Optional, Union

# Initialize FastMCP server
mcp = FastMCP("lmstudio-bridge")

# LM Studio settings - configurable via environment variables
# Inspired by @ahmedibrahim085 (https://github.com/ahmedibrahim085/LMStudio-MCP)
LMSTUDIO_HOST = os.getenv("LMSTUDIO_HOST", "localhost")
LMSTUDIO_PORT = os.getenv("LMSTUDIO_PORT", "1234")

# Validate port is a valid integer
try:
    _port = int(LMSTUDIO_PORT)
    if not (1 <= _port <= 65535):
        raise ValueError(f"Port {LMSTUDIO_PORT} out of range")
except ValueError:
    print(f"WARNING: Invalid LMSTUDIO_PORT '{LMSTUDIO_PORT}', falling back to 1234", file=sys.stderr)
    LMSTUDIO_PORT = "1234"

LMSTUDIO_API_BASE = f"http://{LMSTUDIO_HOST}:{LMSTUDIO_PORT}/v1"
DEFAULT_MODEL = "default"  # Will be replaced with whatever model is currently loaded


def log_error(message: str):
    """Log error messages to stderr for debugging"""
    print(f"ERROR: {message}", file=sys.stderr)


def log_info(message: str):
    """Log informational messages to stderr for debugging"""
    print(f"INFO: {message}", file=sys.stderr)


@mcp.tool()
async def health_check() -> str:
    """Check if LM Studio API is accessible.

    Returns:
        A message indicating whether the LM Studio API is running.
    """
    try:
        response = requests.get(f"{LMSTUDIO_API_BASE}/models")
        if response.status_code == 200:
            return "LM Studio API is running and accessible."
        else:
            return f"LM Studio API returned status code {response.status_code}."
    except Exception as e:
        return f"Error connecting to LM Studio API: {str(e)}"


@mcp.tool()
async def list_models() -> str:
    """List all available models in LM Studio.

    Returns:
        A formatted list of available models.
    """
    try:
        response = requests.get(f"{LMSTUDIO_API_BASE}/models")
        if response.status_code != 200:
            return f"Failed to fetch models. Status code: {response.status_code}"

        models = response.json().get("data", [])
        if not models:
            return "No models found in LM Studio."

        result = "Available models in LM Studio:\n\n"
        for model in models:
            result += f"- {model['id']}\n"

        return result
    except Exception as e:
        log_error(f"Error in list_models: {str(e)}")
        return f"Error listing models: {str(e)}"


@mcp.tool()
async def get_current_model() -> str:
    """Get the currently loaded model in LM Studio.

    Returns:
        The name of the currently loaded model.
    """
    try:
        response = requests.post(
            f"{LMSTUDIO_API_BASE}/chat/completions",
            json={
                "messages": [{"role": "system", "content": "What model are you?"}],
                "temperature": 0.7,
                "max_tokens": 10
            }
        )

        if response.status_code != 200:
            return f"Failed to identify current model. Status code: {response.status_code}"

        model_info = response.json().get("model", "Unknown")
        return f"Currently loaded model: {model_info}"
    except Exception as e:
        log_error(f"Error in get_current_model: {str(e)}")
        return f"Error identifying current model: {str(e)}"


@mcp.tool()
async def chat_completion(
    prompt: str,
    system_prompt: str = "",
    temperature: float = 0.7,
    max_tokens: int = 1024
) -> str:
    """Generate a chat completion from the current LM Studio model.

    Args:
        prompt: The user's prompt to send to the model
        system_prompt: Optional system instructions for the model
        temperature: Controls randomness (0.0 to 1.0)
        max_tokens: Maximum number of tokens to generate

    Returns:
        The model's response to the prompt
    """
    try:
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": prompt})

        log_info(f"Sending chat request to LM Studio with {len(messages)} messages")

        response = requests.post(
            f"{LMSTUDIO_API_BASE}/chat/completions",
            json={
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            },
            timeout=60
        )

        if response.status_code != 200:
            log_error(f"LM Studio API error: {response.status_code}")
            return f"Error: LM Studio returned status code {response.status_code}"

        response_json = response.json()
        log_info("Received response from LM Studio")

        choices = response_json.get("choices", [])
        if not choices:
            return "Error: No response generated"

        content = choices[0].get("message", {}).get("content", "")

        if not content:
            return "Error: Empty response from model"

        return content
    except Exception as e:
        log_error(f"Error in chat_completion: {str(e)}")
        return f"Error generating completion: {str(e)}"


@mcp.tool()
async def text_completion(
    prompt: str,
    temperature: float = 0.7,
    max_tokens: int = 1024,
    stop_sequences: Optional[List[str]] = None
) -> str:
    """Generate a raw text completion (non-chat format) from LM Studio.

    Simpler and faster than chat_completion for single-turn tasks like
    code completion or text continuation - no chat formatting overhead.

    Args:
        prompt: The text prompt to complete
        temperature: Controls randomness (0.0 to 2.0, default 0.7)
        max_tokens: Maximum number of tokens to generate (default 1024)
        stop_sequences: Optional list of sequences where generation will stop

    Returns:
        The completed text from the model

    Inspired by @ahmedibrahim085 (https://github.com/ahmedibrahim085/LMStudio-MCP)
    """
    try:
        payload: Dict[str, Any] = {
            "prompt": prompt,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        if stop_sequences:
            payload["stop"] = stop_sequences

        log_info("Sending text completion request to LM Studio")

        response = requests.post(
            f"{LMSTUDIO_API_BASE}/completions",
            json=payload,
            timeout=30
        )

        if response.status_code != 200:
            log_error(f"LM Studio API error: {response.status_code}")
            return f"Error: LM Studio returned status code {response.status_code}"

        response_json = response.json()
        log_info("Received text completion from LM Studio")

        choices = response_json.get("choices", [])
        if not choices:
            return "Error: No completion generated"

        text = choices[0].get("text", "")

        if not text:
            return "Error: Empty completion from model"

        return text
    except Exception as e:
        log_error(f"Error in text_completion: {str(e)}")
        return f"Error generating text completion: {str(e)}"


@mcp.tool()
async def generate_embeddings(
    text: Union[str, List[str]],
    model: str = "default"
) -> str:
    """Generate vector embeddings for text using LM Studio.

    Supports single text or batch processing. Useful for RAG systems,
    semantic search, and text similarity comparisons.

    Note: You must have an embedding model loaded in LM Studio (e.g.
    'text-embedding-nomic-embed-text-v1.5'). The default chat model
    will not work with this endpoint.

    Args:
        text: Single text string or list of texts to embed
        model: Embedding model to use. Omit to use the currently loaded
               model, but an embedding-specific model is recommended.

    Returns:
        JSON string with embeddings data including vectors and usage info

    Inspired by @ahmedibrahim085 (https://github.com/ahmedibrahim085/LMStudio-MCP)
    """
    try:
        payload: Dict[str, Any] = {"input": text}

        if model != "default":
            payload["model"] = model

        log_info("Sending embeddings request to LM Studio")

        response = requests.post(
            f"{LMSTUDIO_API_BASE}/embeddings",
            json=payload,
            timeout=30
        )

        if response.status_code != 200:
            log_error(f"LM Studio API error: {response.status_code}")
            return json.dumps({"error": f"LM Studio returned status code {response.status_code}"})

        log_info("Received embeddings from LM Studio")

        # Validate the response is well-formed JSON before returning
        try:
            json.loads(response.text)
        except json.JSONDecodeError:
            log_error("LM Studio returned malformed JSON for embeddings")
            return json.dumps({
                "error": "API returned malformed JSON",
                "raw_preview": response.text[:200]
            })

        return response.text

    except requests.exceptions.RequestException as e:
        log_error(f"Request error in generate_embeddings: {str(e)}")
        return json.dumps({"error": f"Failed to generate embeddings: {str(e)}"})
    except Exception as e:
        log_error(f"Unexpected error in generate_embeddings: {str(e)}")
        return json.dumps({"error": f"Unexpected error: {str(e)}"})


@mcp.tool()
async def create_response(
    input_text: str,
    previous_response_id: Optional[str] = None,
    reasoning_effort: str = "medium",
    stream: bool = False,
    model: Optional[str] = None
) -> str:
    """Create a stateful response using LM Studio's /v1/responses endpoint.

    Unlike chat_completion, this endpoint maintains conversation context
    automatically via response IDs - no manual message history needed.
    Pass the ID from a previous response to continue the conversation.

    Requires LM Studio v0.3.29 or later.

    Args:
        input_text: The user's input text
        previous_response_id: ID from a previous create_response call to
                              continue the conversation
        reasoning_effort: Reasoning depth - "low", "medium", or "high"
                          (default "medium")
        stream: Whether to stream the response (default False)
        model: Model to use. If omitted, the currently loaded model is
               detected automatically.

    Returns:
        JSON string with the response, including an 'id' field you can
        pass as previous_response_id in the next call.

    Inspired by @ahmedibrahim085 (https://github.com/ahmedibrahim085/LMStudio-MCP)
    """
    try:
        # Auto-detect current model if not specified
        if model is None:
            try:
                current = await get_current_model()
                detected = current.replace("Currently loaded model: ", "").strip()
                if not detected or detected == "Unknown":
                    raise ValueError("Model name could not be determined from response")
                model = detected
            except Exception as e:
                log_error(f"Model auto-detection failed: {str(e)}")
                return json.dumps({
                    "error": (
                        "Could not detect the currently loaded model. "
                        "Please specify a model explicitly via the 'model' parameter."
                    )
                })

        payload: Dict[str, Any] = {
            "input": input_text,
            "model": model,
            "stream": stream
        }

        if previous_response_id:
            payload["previous_response_id"] = previous_response_id

        if reasoning_effort in ("low", "medium", "high"):
            payload["reasoning"] = {"effort": reasoning_effort}

        log_info("Sending stateful response request to LM Studio")

        response = requests.post(
            f"{LMSTUDIO_API_BASE}/responses",
            json=payload,
            timeout=60
        )

        if response.status_code != 200:
            log_error(f"LM Studio API error: {response.status_code}")
            return json.dumps({"error": f"LM Studio returned status code {response.status_code}"})

        log_info("Received stateful response from LM Studio")
        return response.text

    except requests.exceptions.RequestException as e:
        log_error(f"Request error in create_response: {str(e)}")
        return json.dumps({"error": f"Failed to create response: {str(e)}"})
    except Exception as e:
        log_error(f"Unexpected error in create_response: {str(e)}")
        return json.dumps({"error": f"Unexpected error: {str(e)}"})


def main():
    """Entry point for the package when installed via pip"""
    log_info("Starting LM Studio Bridge MCP Server")
    mcp.run(transport='stdio')


if __name__ == "__main__":
    main()
