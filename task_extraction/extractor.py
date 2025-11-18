from encodings import undefined
from typing import Dict

import json
import re

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
        instructions=f"""
        Parse the following message to assess if the message contains a task. If so, summarize the task. Return the results in a json format e.g. '{{"is_task": 0, "task": "summary of task"}}',
        Example input: "Remember to buy milk!"
        Example response: {{"is_task":0, "task":"Buy milk"}}
        """,
        input=text,
    )

    response_text = response.output_text
    parsed_text = re.findall(r"(\{.*?\})", response_text)[0]
    print(parsed_text)
    res = json.loads(parsed_text)
    assert "is_task" in res, print("Malformed response, missing is_task key")

    return res


__all__ = ["extract_task"]
