"""
configs/config.py
=================
Centralized configuration loader for IntentCompiler.

Loads environment variables from ``.env`` and reads configuration files
(like ``llm_config.yaml``) using ``infrakit.load``.

Exports:
  - APP_CONFIG: The merged configuration dictionary.
  - get_gemini_api_keys(): Function to parse API keys from the environment.
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from infrakit import load as infrakit_load

_ROOT = Path(__file__).resolve().parent.parent
_ENV_FILE = _ROOT / ".env"
_LLM_CONFIG_FILE = _ROOT / "configs" / "llm_config.yaml"

# 1. Load environment variables from .env
load_dotenv(_ENV_FILE)

# 2. Load YAML configs via infrakit
def _load_app_config() -> dict:
    if _LLM_CONFIG_FILE.exists():
        return infrakit_load(str(_LLM_CONFIG_FILE))
    return {}

# Export the config globally (loaded exactly once when imported)
APP_CONFIG = _load_app_config()


def get_gemini_api_keys() -> list[str]:
    """Retrieve and parse Gemini API keys from the environment."""
    env_keys_str = os.environ.get("GEMINI_API_KEYS", "")
    keys = [
        k.strip() for k in env_keys_str.split(",")
        if k.strip() and k.strip() != "YOUR_GEMINI_API_KEY_HERE"
    ]
    return keys
