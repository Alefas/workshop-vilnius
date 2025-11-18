from typing import Dict

import json
import re
import os

try:
    from openai import OpenAI  # type: ignore
except Exception:  # pragma: no cover - optional dependency handling
    OpenAI = None  # type: ignore


def _coerce_is_task(val) -> int:
    if isinstance(val, bool):
        return 1 if val else 0
    if isinstance(val, (int, float)):
        return 1 if int(val) != 0 else 0
    if isinstance(val, str):
        v = val.strip().lower()
        return 1 if v in {"1", "true", "yes", "y", "t"} else 0
    return 0


def _parse_json_loose(text: str) -> Dict[str, object]:
    """Try a few strategies to extract a JSON object from arbitrary text.
    Falls back to default structure if parsing fails.
    """
    default = {"is_task": 0, "task": ""}
    if not text:
        return default
    # Strip code fences if present
    fenced = re.match(r"```(?:json)?\s*(.*)\s*```\s*$", text, flags=re.DOTALL)
    core = fenced.group(1) if fenced else text
    # 1) Direct parse
    try:
        obj = json.loads(core)
        if isinstance(obj, dict):
            return obj
    except Exception:
        pass
    # 2) Find first JSON-looking object and try to parse
    for m in re.finditer(r"\{[^{}]*?(?:\{[^{}]*\}[^{}]*?)*\}", core, flags=re.DOTALL):
        frag = m.group(0)
        try:
            obj = json.loads(frag)
            if isinstance(obj, dict):
                return obj
        except Exception:
            continue
    # 3) Nothing worked
    return default


def extract_task(text: str) -> Dict[str, object]:
    """
    Detect and extract an actionable task from a chat message.

    Args:
        text: Input message text.

    Returns:
        dict with keys {is_task: bool, task: str}
    """
    response_text = ""
    # Call API if available; otherwise skip and use default parser which returns non-crashing defaults
    if OpenAI is not None and os.environ.get("OPENAI_API_KEY"):
        try:
            client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
            response = client.responses.create(
                model="gpt-4o",
                instructions=(
                    """
                    Parse the following message to assess if the message contains a task. If so, summarize the task.
                    Return the results strictly in JSON format like {"is_task": 0 or 1, "task": "summary"} with no extra text.
                    Example input: "Remember to buy milk!"
                    Example response: {"is_task":1, "task":"Buy milk"}
                    """
                ),
                input=text,
            )
            response_text = getattr(response, "output_text", "") or ""
        except Exception:
            # On any API error, fall back to default downstream
            response_text = ""

    # Robust parsing (avoids IndexError when no JSON is found)
    res = _parse_json_loose(response_text)

    # Normalize fields
    is_task = _coerce_is_task(res.get("is_task", 0))
    task = res.get("task", "")
    if task is None:
        task = ""
    task = str(task)

    return {"is_task": is_task, "task": task}


__all__ = ["extract_task"]
