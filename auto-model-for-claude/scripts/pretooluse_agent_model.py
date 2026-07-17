#!/usr/bin/env python3
"""PreToolUse hook: auto-inject Agent tool `model` when the caller omits it.

Fail-open by design — any error here must never block a real Agent call,
so exceptions fall through to "no output, exit 0" (tool runs unmodified).
"""

import importlib.util
import json
import re
import sys
from pathlib import Path

COMPLEX_HINTS = (
    "refactor", "migrate", "migration", "architecture", "redesign",
    "security", "audit", "debug", "investigat", "multi-file", "multi-step",
)


def slugify(text, limit=60):
    text = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    return text[:limit] or "general"


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return

    if data.get("tool_name") != "Agent":
        return

    tool_input = data.get("tool_input") or {}
    if tool_input.get("model"):
        return  # explicit choice already made — never override it

    description = tool_input.get("description", "")
    prompt = tool_input.get("prompt", "")
    task_type = slugify(description)
    complexity = "complex" if any(h in (description + prompt).lower() for h in COMPLEX_HINTS) else "easy"

    try:
        script_path = Path.home() / ".claude" / "skills" / "auto-model-for-claude" / "scripts" / "auto_model.py"
        spec = importlib.util.spec_from_file_location("auto_model", script_path)
        auto_model = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(auto_model)

        args = type("Args", (), {
            "task_type": task_type,
            "module": "hook-auto",
            "file": "",
            "complexity": complexity,
        })()
        recommendation = auto_model.recommend(args)
        model = recommendation.get("model")
    except Exception:
        return

    if not model:
        return

    merged_input = dict(tool_input)
    merged_input["model"] = model

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow",
            "updatedInput": merged_input,
        }
    }))


if __name__ == "__main__":
    main()
