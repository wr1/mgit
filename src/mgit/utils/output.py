"""Shared output formatting for all commands."""

import json
from typing import Any


def emit(data: Any, fmt: str = "rich") -> str:
    """Serialize data to the requested format and print it. Returns the string."""
    if fmt == "json":
        out = json.dumps(data, indent=2, default=str)
        print(out)
        return out
    elif fmt in ("llm", "markdown"):
        out = _to_markdown(data, compact=(fmt == "llm"))
        print(out)
        return out
    # "rich" or anything else: caller handles its own rendering; just return JSON string
    return json.dumps(data, default=str)


def _to_markdown(data: Any, compact: bool = False) -> str:
    """Convert nested dicts/lists to compact markdown."""
    lines: list[str] = []
    if isinstance(data, dict):
        for k, v in data.items():
            if isinstance(v, list):
                lines.append(
                    f"**{k}**: {', '.join(str(i) for i in v)}" if compact else f"## {k}"
                )
                if not compact:
                    for item in v:
                        lines.append(f"- {item}")
            elif isinstance(v, dict):
                lines.append(f"**{k}**:" if compact else f"## {k}")
                for sk, sv in v.items():
                    lines.append(f"  - {sk}: {sv}")
            else:
                lines.append(f"**{k}**: {v}" if compact else f"**{k}**: {v}")
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                lines.append("- " + "  ".join(f"{k}={v}" for k, v in item.items()))
            else:
                lines.append(f"- {item}")
    else:
        lines.append(str(data))
    return "\n".join(lines)
