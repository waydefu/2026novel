"""Minimal YAML-ish manifest loader. No PyYAML dependency."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def load_simple_mapping(path: Path) -> dict[str, Any]:
    data: dict[str, Any] = {}
    current_list: str | None = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        if line.startswith("  - ") or line.startswith("- "):
            if current_list is None:
                continue
            item = line.split("-", 1)[1].strip().strip('"').strip("'")
            data.setdefault(current_list, []).append(item)
            continue
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if value == "":
            current_list = key
            data[key] = []
            continue
        current_list = None
        low = value.lower()
        if low in {"true", "yes"}:
            data[key] = True
        elif low in {"false", "no"}:
            data[key] = False
        elif low in {"null", "none", "~"}:
            data[key] = None
        else:
            data[key] = value
    return data
