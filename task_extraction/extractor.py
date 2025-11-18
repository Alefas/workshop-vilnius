from encodings import undefined
from typing import Dict


import os
from openai import OpenAI

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
)

def extract_task(text: str) -> Dict[str, object]:
    """
    Detect and extract an actionable task from a chat message.

    Args:
        text: Input message text.

    Returns:
        dict with keys {is_task: bool, task: str}
    """
    response = client.responses.create(
        model="gpt-4o",
        instructions="You are a coding assistant that talks like a pirate.",
        input=text,
    )

    print(response.output_text)
    return {"is_task": False,  "task": ""}


__all__ = ["extract_task"]
