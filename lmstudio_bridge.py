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

def main():
    """Entry point for the package when installed via pip"""
    log_info("Starting LM Studio Bridge MCP Server")
    mcp.run(transport='stdio')

if __name__ == "__main__":
    # Initialize and run the server
    main()