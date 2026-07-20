#!/usr/bin/env python3
"""Expose every Peep skill to Claude Code, Codex, OpenCode and Agent Skills."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGINS = ROOT / "plugins"
HOST_DIRS = {
    "claude": Path.home() / ".claude" / "skills",
    "codex": Path.home() / ".codex" / "skills",
    "opencode": Path.home() / ".config" / "opencode" / "skills",
    "agents": Path.home() / ".agents" / "skills",
}


def source_root(plugin: Path, host: str) -> Path:
    variant = plugin / "variants" / host
    if variant.is_dir():
        return variant
    if host == "codex" and (plugin / "variants" / "agents").is_dir():
        return plugin / "variants" / "agents"
    return plugin / "skills"


def discover(host: str, selected_plugins: set[str] | None) -> list[tuple[str, Path]]:
    found: list[tuple[str, Path]] = []
    for plugin in sorted(path for path in PLUGINS.iterdir() if path.is_dir()):
        if selected_plugins is not None and plugin.name not in selected_plugins:
            continue
        root = source_root(plugin, host)
        if not root.is_dir():
            continue
        for skill in sorted(path for path in root.iterdir() if path.is_dir()):
            if (skill / "SKILL.md").is_file():
                found.append((skill.name, skill.resolve()))
    return found


def state(destination: Path, source: Path) -> str:
    if destination.is_symlink():
        resolved = destination.resolve()
        if resolved == source:
            return "installed"
        if resolved.is_relative_to(ROOT):
            return "managed-update"
        return "conflict"
    return "conflict" if destination.exists() else "missing"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Install Peep skills as symlinks without overwriting existing skills."
    )
    parser.add_argument(
        "--host",
        action="append",
        choices=sorted(HOST_DIRS),
        help="Target host; repeat as needed. Defaults to all hosts.",
    )
    parser.add_argument(
        "--plugin",
        action="append",
        help="Plugin to install; repeat as needed. Defaults to the complete catalog.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Report status without changing the filesystem.",
    )
    args = parser.parse_args()

    hosts = args.host or list(HOST_DIRS)
    selected_plugins = set(args.plugin) if args.plugin else None
    if selected_plugins is not None:
        available = {path.name for path in PLUGINS.iterdir() if path.is_dir()}
        unknown = sorted(selected_plugins - available)
        if unknown:
            parser.error(f"plugins desconhecidos: {', '.join(unknown)}")
    report: dict[str, list[dict[str, str]]] = {}
    conflicts = 0

    for host in hosts:
        destination_root = HOST_DIRS[host]
        if not args.check:
            destination_root.mkdir(parents=True, exist_ok=True)
        rows: list[dict[str, str]] = []
        for name, source in discover(host, selected_plugins):
            destination = destination_root / name
            status = state(destination, source)
            if status == "missing" and not args.check:
                os.symlink(source, destination, target_is_directory=True)
                status = "installed"
            elif status == "managed-update" and not args.check:
                destination.unlink()
                os.symlink(source, destination, target_is_directory=True)
                status = "updated"
            elif status == "conflict":
                conflicts += 1
            rows.append(
                {
                    "skill": name,
                    "status": status,
                    "source": str(source),
                    "destination": str(destination),
                }
            )
        report[host] = rows

    print(json.dumps(report, ensure_ascii=False, indent=2))
    if conflicts:
        print(
            "Conflitos não foram sobrescritos; remova ou mova os destinos listados e execute novamente.",
            file=__import__("sys").stderr,
        )
    return 1 if conflicts else 0


if __name__ == "__main__":
    raise SystemExit(main())
