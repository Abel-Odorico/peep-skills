#!/usr/bin/env python3
"""Audita a consistência dos catálogos e manifestos do peep-skills."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PLUGINS_DIR = ROOT / "plugins"
CLAUDE_MARKETPLACE = ROOT / ".claude-plugin" / "marketplace.json"
CODEX_MARKETPLACE = ROOT / ".agents" / "plugins" / "marketplace.json"
README = ROOT / "README.md"


def load_json(path: Path, errors: list[str]) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        errors.append(f"arquivo ausente: {path.relative_to(ROOT)}")
        return {}
    except json.JSONDecodeError as exc:
        errors.append(f"JSON inválido em {path.relative_to(ROOT)}: {exc}")
        return {}
    if not isinstance(value, dict):
        errors.append(f"objeto JSON esperado em {path.relative_to(ROOT)}")
        return {}
    return value


def names_from_marketplace(data: dict, label: str, errors: list[str]) -> set[str]:
    entries = data.get("plugins", [])
    if not isinstance(entries, list):
        errors.append(f"{label}: `plugins` deve ser uma lista")
        return set()
    names = [entry.get("name") for entry in entries if isinstance(entry, dict)]
    duplicates = sorted({name for name in names if name and names.count(name) > 1})
    if duplicates:
        errors.append(f"{label}: nomes duplicados: {', '.join(duplicates)}")
    return {name for name in names if isinstance(name, str)}


def compare(label: str, expected: set[str], actual: set[str], errors: list[str]) -> None:
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    if missing:
        errors.append(f"{label}: ausentes: {', '.join(missing)}")
    if extra:
        errors.append(f"{label}: extras: {', '.join(extra)}")


def validate_manifests(plugin_names: set[str], errors: list[str]) -> None:
    required_interface = {
        "displayName",
        "shortDescription",
        "longDescription",
        "developerName",
        "category",
        "capabilities",
        "defaultPrompt",
    }
    for name in sorted(plugin_names):
        plugin_dir = PLUGINS_DIR / name
        for kind in ("claude", "codex"):
            manifest = plugin_dir / f".{kind}-plugin" / "plugin.json"
            data = load_json(manifest, errors)
            if not data:
                continue
            if data.get("name") != name:
                errors.append(f"{manifest.relative_to(ROOT)}: name diferente da pasta")
            if not data.get("version") or not data.get("description"):
                errors.append(f"{manifest.relative_to(ROOT)}: versão ou descrição ausente")
            skills_path = data.get("skills")
            if not isinstance(skills_path, str) or not (plugin_dir / skills_path).is_dir():
                errors.append(f"{manifest.relative_to(ROOT)}: caminho `skills` inválido")
            if kind == "codex":
                interface = data.get("interface")
                if not isinstance(interface, dict):
                    errors.append(f"{manifest.relative_to(ROOT)}: interface ausente")
                else:
                    missing = sorted(required_interface - set(interface))
                    if missing:
                        errors.append(
                            f"{manifest.relative_to(ROOT)}: interface incompleta: {', '.join(missing)}"
                        )


def validate_entries(data: dict, kind: str, errors: list[str]) -> None:
    for entry in data.get("plugins", []):
        if not isinstance(entry, dict) or not isinstance(entry.get("name"), str):
            errors.append(f"marketplace {kind}: entrada inválida")
            continue
        name = entry["name"]
        source = entry.get("source", {})
        if kind == "claude":
            if source.get("path") != f"plugins/{name}":
                errors.append(f"marketplace Claude: source.path inválido para {name}")
            if source.get("url") != "https://github.com/Abel-Odorico/peep-skills.git":
                errors.append(f"marketplace Claude: source.url inválido para {name}")
        else:
            if source != {"source": "local", "path": f"./plugins/{name}"}:
                errors.append(f"marketplace Codex: source inválido para {name}")
            policy = entry.get("policy")
            expected_policy = {"installation": "AVAILABLE", "authentication": "ON_INSTALL"}
            if policy != expected_policy:
                errors.append(f"marketplace Codex: policy inválida para {name}")
            if not entry.get("category"):
                errors.append(f"marketplace Codex: category ausente para {name}")


def main() -> int:
    errors: list[str] = []
    plugin_names = {path.name for path in PLUGINS_DIR.iterdir() if path.is_dir()}
    claude = load_json(CLAUDE_MARKETPLACE, errors)
    codex = load_json(CODEX_MARKETPLACE, errors)
    readme = README.read_text(encoding="utf-8")

    claude_names = names_from_marketplace(claude, "marketplace Claude", errors)
    codex_names = names_from_marketplace(codex, "marketplace Codex", errors)
    installs = set(re.findall(r"claude plugin install ([a-z0-9-]+)@peep-skills", readme))
    headings = set(re.findall(r"^### ([a-z0-9-]+)$", readme, re.MULTILINE))

    compare("marketplace Claude", plugin_names, claude_names, errors)
    compare("marketplace Codex", plugin_names, codex_names, errors)
    compare("README/install", plugin_names, installs, errors)
    compare("README/seções", plugin_names, headings, errors)
    validate_entries(claude, "claude", errors)
    validate_entries(codex, "codex", errors)
    validate_manifests(plugin_names, errors)

    result = {
        "plugins": len(plugin_names),
        "claude_marketplace": len(claude_names),
        "codex_marketplace": len(codex_names),
        "readme_installs": len(installs),
        "readme_sections": len(headings),
        "errors": errors,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
