from encodings import undefined
from typing import Dict




def extract_task(text: str) -> Dict[str, object]:
    """
    Detect and extract an actionable task from a chat message.

    Args:
        text: Input message text.

    Returns:
        dict with keys {is_task: bool, task: str}
    """
    return {"is_task": False,  "task": ""}


__all__ = ["extract_task"]
