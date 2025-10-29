#!/usr/bin/env python3
from mcp.server.fastmcp import FastMCP
import requests
import json
import sys
import os
from typing import List, Dict, Any, Optional, Union

# Initialize FastMCP server
mcp = FastMCP("lmstudio-bridge-enhanced")

# LM Studio settings - configurable via environment variables
LMSTUDIO_HOST = os.getenv("LMSTUDIO_HOST", "localhost")
LMSTUDIO_PORT = os.getenv("LMSTUDIO_PORT", "1234")
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
        # LM Studio doesn't have a direct endpoint for currently loaded model
        # We'll check which model responds to a simple completion request
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
        
        # Extract model info from response
        model_info = response.json().get("model", "Unknown")
        return f"Currently loaded model: {model_info}"
    except Exception as e:
        log_error(f"Error in get_current_model: {str(e)}")
        return f"Error identifying current model: {str(e)}"

@mcp.tool()
async def chat_completion(prompt: str, system_prompt: str = "", temperature: float = 0.7, max_tokens: int = 1024) -> str:
    """Generate a completion from the current LM Studio model.

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

        # Add system message if provided
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        # Add user message
        messages.append({"role": "user", "content": prompt})

        log_info(f"Sending request to LM Studio with {len(messages)} messages")

        response = requests.post(
            f"{LMSTUDIO_API_BASE}/chat/completions",
            json={
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
        )

        if response.status_code != 200:
            log_error(f"LM Studio API error: {response.status_code}")
            return f"Error: LM Studio returned status code {response.status_code}"

        response_json = response.json()
        log_info(f"Received response from LM Studio")

        # Extract the assistant's message
        choices = response_json.get("choices", [])
        if not choices:
            return "Error: No response generated"

        message = choices[0].get("message", {})
        content = message.get("content", "")

        if not content:
            return "Error: Empty response from model"

        return content
    except Exception as e:
        log_error(f"Error in chat_completion: {str(e)}")
        return f"Error generating completion: {str(e)}"

@mcp.tool()
async def text_completion(prompt: str, temperature: float = 0.7, max_tokens: int = 1024, stop_sequences: Optional[List[str]] = None) -> str:
    """Generate a raw text completion (non-chat format) from LM Studio.

    This endpoint is simpler and faster than chat completions for single-turn tasks
    like code completion, text continuation, or simple Q&A.

    Args:
        prompt: The text prompt to complete
        temperature: Controls randomness (0.0 to 2.0, default 0.7)
        max_tokens: Maximum number of tokens to generate (default 1024)
        stop_sequences: Optional list of sequences where generation will stop

    Returns:
        The completed text from the model
    """
    try:
        payload = {
            "prompt": prompt,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        # Add stop sequences if provided
        if stop_sequences:
            payload["stop"] = stop_sequences

        log_info(f"Sending text completion request to LM Studio")

        response = requests.post(
            f"{LMSTUDIO_API_BASE}/completions",
            json=payload,
            timeout=30
        )

        if response.status_code != 200:
            log_error(f"LM Studio API error: {response.status_code}")
            return f"Error: LM Studio returned status code {response.status_code}"

        response_json = response.json()
        log_info(f"Received text completion from LM Studio")

        # Extract the completion text
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
async def generate_embeddings(text: Union[str, List[str]], model: str = "default") -> str:
    """Generate vector embeddings for text using LM Studio.

    Supports both single text and batch processing. Useful for RAG systems,
    semantic search, text similarity, and clustering tasks.

    Args:
        text: Single text string or list of texts to embed
        model: Model to use for embeddings (default uses currently loaded model)

    Returns:
        JSON string with embeddings data including vectors and usage info
    """
    try:
        payload = {"input": text}

        # Only include model if it's not the default
        if model != "default":
            payload["model"] = model

        log_info(f"Sending embeddings request to LM Studio")

        response = requests.post(
            f"{LMSTUDIO_API_BASE}/embeddings",
            json=payload,
            timeout=30
        )

        if response.status_code != 200:
            log_error(f"LM Studio API error: {response.status_code}")
            error_response = {
                "error": f"LM Studio returned status code {response.status_code}"
            }
            return json.dumps(error_response)

        log_info(f"Received embeddings from LM Studio")

        # Return the JSON response as a string
        return response.text

    except requests.exceptions.RequestException as e:
        log_error(f"Error in generate_embeddings: {str(e)}")
        error_response = {
            "error": f"Failed to generate embeddings: {str(e)}"
        }
        return json.dumps(error_response)
    except Exception as e:
        log_error(f"Unexpected error in generate_embeddings: {str(e)}")
        error_response = {
            "error": f"Unexpected error during embedding generation: {str(e)}"
        }
        return json.dumps(error_response)

@mcp.tool()
async def create_response(input_text: str, previous_response_id: Optional[str] = None, reasoning_effort: str = "medium", stream: bool = False) -> str:
    """Create a response using LM Studio's stateful /v1/responses endpoint.

    This endpoint provides stateful conversations where you can reference previous
    responses without managing message history manually. Supports reasoning and streaming.

    Args:
        input_text: The user's input text
        previous_response_id: Optional ID from a previous response to continue conversation
        reasoning_effort: Level of reasoning effort - "low", "medium", or "high" (default "medium")
        stream: Whether to stream the response (default False)

    Returns:
        JSON string with response including ID for future reference
    """
    try:
        payload = {
            "input": input_text,
            "stream": stream
        }

        # Add previous response ID if provided (for conversation continuity)
        if previous_response_id:
            payload["previous_response_id"] = previous_response_id

        # Add reasoning configuration
        if reasoning_effort in ["low", "medium", "high"]:
            payload["reasoning"] = {"effort": reasoning_effort}

        log_info(f"Sending stateful response request to LM Studio")

        response = requests.post(
            f"{LMSTUDIO_API_BASE}/responses",
            json=payload,
            timeout=60  # Longer timeout for reasoning
        )

        if response.status_code != 200:
            log_error(f"LM Studio API error: {response.status_code}")
            error_response = {
                "error": f"LM Studio returned status code {response.status_code}"
            }
            return json.dumps(error_response)

        log_info(f"Received stateful response from LM Studio")

        # Return the JSON response as a string (includes response ID)
        return response.text

    except requests.exceptions.RequestException as e:
        log_error(f"Error in create_response: {str(e)}")
        error_response = {
            "error": f"Failed to create response: {str(e)}"
        }
        return json.dumps(error_response)
    except Exception as e:
        log_error(f"Unexpected error in create_response: {str(e)}")
        error_response = {
            "error": f"Unexpected error during response creation: {str(e)}"
        }
        return json.dumps(error_response)

def main():
    """Entry point for the package when installed via pip"""
    log_info("Starting LM Studio Bridge MCP Server")
    mcp.run(transport='stdio')

if __name__ == "__main__":
    # Initialize and run the server
    main()