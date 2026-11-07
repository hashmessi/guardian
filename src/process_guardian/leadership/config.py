"""Configuration for Process Guardian Leadership AI services."""

import os

# Store GEMINI_API_KEY only on the backend environment; never in React or Git.
# Configure via GEMINI_API_KEY environment variable.
DEFAULT_GEMINI_KEY = ""
GEMINI_API_KEY: str = os.environ.get("GEMINI_API_KEY", DEFAULT_GEMINI_KEY)
GEMINI_MODEL: str = os.environ.get("GEMINI_MODEL", "gemini-3.8-flash")
GEMINI_TIMEOUT_SECONDS: float = float(os.environ.get("GEMINI_TIMEOUT_SECONDS", "6.0"))
