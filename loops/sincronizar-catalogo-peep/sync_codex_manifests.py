#!/usr/bin/env python3
"""Cria manifestos Codex ausentes a partir dos manifestos Claude existentes."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PLUGINS = ROOT / "plugins"


def display_name(name: str) -> str:
    words = {"ai": "AI", "pwa": "PWA", "api": "API", "fastapi": "FastAPI"}
    return " ".join(words.get(part, part.capitalize()) for part in name.split("-"))


def category(name: str) -> str:
    if name in {"ai-image-generation", "frontend-craft", "analytics-craft"}:
        return "Creative"
    if name in {"caveman", "find-skills", "skill-creator", "using-superpowers"}:
        return "Productivity"
    return "Developer Tools"


def shorten(text: str, limit: int = 96) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip(" ,.;:-") + "…"


def main() -> int:
    created: list[str] = []
    preserved: list[str] = []
    for plugin_dir in sorted(path for path in PLUGINS.iterdir() if path.is_dir()):
        claude_path = plugin_dir / ".claude-plugin" / "plugin.json"
        codex_path = plugin_dir / ".codex-plugin" / "plugin.json"
        if codex_path.exists():
            preserved.append(plugin_dir.name)
            continue
        claude = json.loads(claude_path.read_text(encoding="utf-8"))
        author = claude.get("author") or {"name": "Abel Odorico"}
        description = claude["description"]
        manifest = {
            "name": plugin_dir.name,
            "version": claude["version"],
            "description": description,
            "author": author,
            "skills": "./skills/",
            "interface": {
                "displayName": display_name(plugin_dir.name),
                "shortDescription": shorten(description),
                "longDescription": description,
                "developerName": author["name"],
                "category": category(plugin_dir.name),
                "capabilities": ["Interactive", "Write"],
                "defaultPrompt": [f"Use {display_name(plugin_dir.name)} neste projeto."],
            },
        }
        for field in ("homepage", "repository"):
            if claude.get(field):
                manifest[field] = claude[field]
        codex_path.parent.mkdir(parents=True, exist_ok=True)
        codex_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        created.append(plugin_dir.name)
    print(json.dumps({"created": created, "preserved": preserved}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
