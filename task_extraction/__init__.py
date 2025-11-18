"""
Lightweight task extraction package.

Public API:
    extract_task(text: str) -> dict

Returns a dictionary with keys:
    - is_task: bool
    - confidence: float (0.0–1.0)
    - task: str (empty when no task detected)
"""

from .extractor import extract_task  # noqa: F401
