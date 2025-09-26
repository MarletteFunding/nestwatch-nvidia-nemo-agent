"""
Prompt registry for SRE Dashboard LLM integration.
Contains all prompts and schemas for deterministic AI responses.
"""

import os
from pathlib import Path

# Base directory for prompts
PROMPTS_DIR = Path(__file__).parent.parent / "prompts"
SCHEMAS_DIR = Path(__file__).parent.parent / "schemas"

def _read_file(path: Path) -> str:
    """Read file content safely."""
    try:
        return path.read_text(encoding='utf-8')
    except FileNotFoundError:
        return ""

# System prompts
SYSTEM_SRE = _read_file(PROMPTS_DIR / "system" / "sre_core_v3.md")

# Task cards
CARD_EVENT_ANALYSIS = _read_file(PROMPTS_DIR / "cards" / "event_analysis_v1.md")
CARD_INCIDENT = _read_file(PROMPTS_DIR / "cards" / "incident_v2.md")
CARD_OPTIM = _read_file(PROMPTS_DIR / "cards" / "optimization_v1.md")

# JSON schemas
SCHEMA_EVENT_ANALYSIS = _read_file(SCHEMAS_DIR / "event_analysis_v1.json")
SCHEMA_INCIDENT = _read_file(SCHEMAS_DIR / "incident_v2.json")
SCHEMA_OPTIM = _read_file(SCHEMAS_DIR / "optimization_v1.json")

# Router
ROUTER_V1 = _read_file(PROMPTS_DIR / "router_v1.md")
