# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  config/__init__.py — Configuration Loader                                ║
# ║  ─────────────────────────────────────────────────────────────────────────  ║
# ║                                                                            ║
# ║  This module loads settings.yaml and exposes it as a Python dictionary.    ║
# ║  Any file in the project can import configuration values via:              ║
# ║  `from config import settings` or `from config import OPENROUTER_API_KEY`  ║
# ║                                                                            ║
# ║  STUDENT — THIS FILE:                                                      ║
# ║  - Reads settings.yaml (YAML → Python dict)                                ║
# ║  - Loads API keys from the .env file                                       ║
# ║  - Exports project-wide constants and paths                                ║
# ║                                                                            ║
# ║  How it works:                                                             ║
# ║  1. Uses pathlib.Path to locate the settings.yaml file                    ║
# ║  2. Uses yaml.safe_load() to parse YAML into a Python dictionary           ║
# ║  3. Uses python-dotenv to load environment variables from .env             ║
# ║  4. Exports structured constants for import across all application modules ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

from __future__ import annotations

import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

# ── Step 1: Load environment variables from .env ─────────────────────────────
# load_dotenv() searches for the .env file at the project root and loads
# key-value pairs into environment variables (e.g. OPENROUTER_API_KEY=sk-or-v1-...).
load_dotenv()

# ── Step 2: Determine file paths ─────────────────────────────────────────────
# __file__ = Path to this file (config/__init__.py)
# .parent = config/ directory
# .parent.parent = project root (de-mentor-demo/)
CONFIG_DIR = Path(__file__).parent
PROJECT_ROOT = CONFIG_DIR.parent
SETTINGS_PATH = CONFIG_DIR / "settings.yaml"

# ── Step 3: Parse settings.yaml into a Python dictionary ─────────────────────
# yaml.safe_load() is used for security to prevent execution of arbitrary objects.
with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
    settings: dict = yaml.safe_load(f)

# ── Step 4: Export convenience constants ─────────────────────────────────────
# These constants can be imported directly across the project:
#   from config import OPENROUTER_API_KEY, JEV_MODEL, ...

# API key retrieved from .env (using the variable name defined in settings.yaml)
_api_key_var = settings["openrouter"]["api_key_env_var"]
OPENROUTER_API_KEY: str = os.getenv(_api_key_var, "")

# Model identifiers sent to OpenRouter API
JEV_MODEL: str = settings["models"]["jev_model"]
CHAT_MODEL: str = settings["models"]["chat_model"]
CHAT_MAX_TOKENS: int = settings["models"]["chat_max_tokens"]

# API endpoints
DECISIONS_URL: str = settings["openrouter"]["decisions_url"]
CHAT_URL: str = settings["openrouter"]["chat_url"]
HTTP_REFERER: str = settings["openrouter"]["http_referer"]
APP_TITLE: str = settings["openrouter"]["app_title"]

# Server settings
SERVER_PORT: int = settings["server"]["port"]
SERVER_HOST: str = settings["server"]["host"]

# Mentor system prompt
MENTOR_SYSTEM_PROMPT: str = settings["mentor"]["system_prompt"]

# Presets for scenario default values (used by UI buttons)
PRESETS: dict = settings.get("presets", {})

# Static files directory for serving frontend HTML/CSS/JS files
STATIC_DIR = PROJECT_ROOT / "static"
