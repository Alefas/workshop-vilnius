Task Extraction Workshop
========================

This project provides a lightweight function to detect and extract actionable tasks from chat messages, and a simple CSV evaluation CLI.

API
---

Function: extract_task(text: str) -> {is_task: bool, task: str}

- is_task: whether the message contains an actionable task.
- task: a concise action phrase when a task is detected, otherwise an empty string.

Example
-------

Python usage:

    from task_extraction import extract_task

    print(extract_task("Can you prepare the release notes by Friday?"))
    # {'is_task': True, 'task': 'prepare the release notes by Friday'}

Evaluation
----------

Run evaluation on a CSV file with columns:
- text (message text)
- label (0/1 for task presence) — optional
- gold_task (reference task text) — optional

CLI:

    python eval.py --input data.csv \
        --text-col text \
        --label-col label \
        --gold-task-col gold_task \
        --output predictions.csv

Notes
-----
- The extractor is rule-based, dependency-free, and designed to be fast and robust for common chat phrasing.
- You can change column names using CLI flags.
- The evaluation reports precision/recall/F1 for task detection and an average token overlap F1 for task text when a reference is provided.
```
python3 -m venv venv
source venv/bin/activate
pip install openai
export OPENAI_API_KEY=<INSERT API KEY>
python -m eval --input data.v0.csv 
```
