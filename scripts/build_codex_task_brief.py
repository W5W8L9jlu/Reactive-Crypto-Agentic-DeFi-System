#!/usr/bin/env python3
from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docs" / "manifests" / "task_context_manifest.json"

def main() -> int:
    if len(sys.argv) < 3:
        print("Usage: build_codex_task_brief.py <module_id> <task...>")
        return 1

    module_id = sys.argv[1]
    task = " ".join(sys.argv[2:])

    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    module = next((m for m in data["modules"] if m["id"] == module_id), None)
    if module is None:
        print(f"Unknown module_id: {module_id}")
        return 2

    print(f"# Codex Task Brief: {module['title']}\n")
    print(f"Task: {task}\n")
    print("Read first:")
    print("- docs/knowledge/01_core/01_system_invariants.md")
    print("- docs/knowledge/01_core/02_domain_models.md")
    print(f"- {module['knowledge']}")
    print(f"- {module['contract']}")
    print(f"- {module['prompt']}\n")

    print("Only edit:")
    for f in module["files"]:
        print(f"- {f}")

    print("\nSuggested working directory:")
    print(f"- {module['workdir']}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
