"""
Anthropic Configuration for SRE Toolkit
"""

import os
from typing import Optional

def get_anthropic_config() -> dict:
    """Get Anthropic configuration from environment variables"""
    return {
        "api_key": os.getenv("ANTHROPIC_API_KEY"),
        "model": os.getenv("ANTHROPIC_MODEL", "claude-3-sonnet-20240229"),
        "temperature": float(os.getenv("ANTHROPIC_TEMPERATURE", "0.1")),
        "max_tokens": int(os.getenv("ANTHROPIC_MAX_TOKENS", "1000"))
    }

def validate_anthropic_config() -> tuple[bool, str]:
    """Validate Anthropic configuration"""
    config = get_anthropic_config()
    
    if not config["api_key"]:
        return False, "ANTHROPIC_API_KEY environment variable not set"
    
    if not config["api_key"] or len(config["api_key"]) < 20:
        return False, "Invalid Anthropic API key format (too short or empty)"
    
    return True, "Anthropic configuration is valid"

# Available Anthropic Claude models for SRE use
AVAILABLE_MODELS = [
    "claude-3-opus-20240229",      # Most capable, best for complex SRE analysis
    "claude-3-sonnet-20240229",    # Balanced performance and cost (recommended)
    "claude-3-haiku-20240307",     # Fastest and most cost-effective
    "claude-3-5-sonnet-20241022"   # Latest Claude 3.5 Sonnet
]

def get_recommended_model() -> str:
    """Get recommended model based on use case"""
    return "claude-3-sonnet-20240229"  # Good balance of capability and cost for SRE tasks

def get_model_info(model_name: str) -> dict:
    """Get information about a specific Claude model"""
    model_info = {
        "claude-3-opus-20240229": {
            "name": "Claude 3 Opus",
            "description": "Most capable model, best for complex SRE analysis and reasoning",
            "context_window": "200k tokens",
            "cost_per_1k_tokens": "$0.015 (input) / $0.075 (output)",
            "best_for": "Complex incident analysis, root cause analysis, detailed recommendations"
        },
        "claude-3-sonnet-20240229": {
            "name": "Claude 3 Sonnet", 
            "description": "Balanced performance and cost, recommended for most SRE tasks",
            "context_window": "200k tokens",
            "cost_per_1k_tokens": "$0.003 (input) / $0.015 (output)",
            "best_for": "General SRE analysis, event correlation, standard recommendations"
        },
        "claude-3-haiku-20240307": {
            "name": "Claude 3 Haiku",
            "description": "Fastest and most cost-effective, good for simple SRE tasks",
            "context_window": "200k tokens", 
            "cost_per_1k_tokens": "$0.00025 (input) / $0.00125 (output)",
            "best_for": "Quick summaries, simple analysis, high-volume processing"
        },
        "claude-3-5-sonnet-20241022": {
            "name": "Claude 3.5 Sonnet",
            "description": "Latest model with improved reasoning and code generation",
            "context_window": "200k tokens",
            "cost_per_1k_tokens": "$0.003 (input) / $0.015 (output)", 
            "best_for": "Advanced SRE analysis, complex troubleshooting, code generation"
        }
    }
    
    return model_info.get(model_name, {
        "name": "Unknown Model",
        "description": "Model information not available",
        "context_window": "Unknown",
        "cost_per_1k_tokens": "Unknown",
        "best_for": "Unknown"
    })
