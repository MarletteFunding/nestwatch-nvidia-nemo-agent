"""
OpenAI Configuration for SRE Toolkit
"""

import os
from typing import Optional

def get_openai_config() -> dict:
    """Get OpenAI configuration from environment variables"""
    return {
        "api_key": os.getenv("OPENAI_API_KEY"),
        "model": os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
        "temperature": float(os.getenv("OPENAI_TEMPERATURE", "0.7")),
        "max_tokens": int(os.getenv("OPENAI_MAX_TOKENS", "500"))
    }

def validate_openai_config() -> tuple[bool, str]:
    """Validate OpenAI configuration"""
    config = get_openai_config()
    
    if not config["api_key"]:
        return False, "OPENAI_API_KEY environment variable not set"
    
    if not config["api_key"].startswith("sk-"):
        return False, "Invalid OpenAI API key format"
    
    return True, "OpenAI configuration is valid"

# Available OpenAI models for SRE use
AVAILABLE_MODELS = [
    "gpt-4",
    "gpt-4-turbo-preview", 
    "gpt-3.5-turbo",
    "gpt-3.5-turbo-16k"
]

def get_recommended_model() -> str:
    """Get recommended model based on use case"""
    return "gpt-3.5-turbo"  # Good balance of cost and performance for SRE tasks
