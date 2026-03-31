#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# ///

from __future__ import annotations

import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_PLUGIN = ROOT / ".codex-plugin" / "plugin.json"
SOURCE_SKILLS = ROOT / "skills"
SOURCE_ASSETS = ROOT / "assets"
IGNORED_PARTS = {".venv", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", "target"}


def rebuild_directory(target: Path, source: Path) -> None:
    if target.exists() or target.is_symlink():
        if target.is_dir() and not target.is_symlink():
            shutil.rmtree(target)
        else:
            target.unlink()
    shutil.copytree(source, target, ignore=shutil.ignore_patterns(*IGNORED_PARTS, ".DS_Store", "*.pyc"))


def main() -> int:
    plugin_name = json.loads(SOURCE_PLUGIN.read_text())["name"]
    packaged_root = ROOT / "plugins" / plugin_name

    if packaged_root.exists() or packaged_root.is_symlink():
        if packaged_root.is_dir() and not packaged_root.is_symlink():
            shutil.rmtree(packaged_root)
        else:
            packaged_root.unlink()

    (packaged_root / ".codex-plugin").mkdir(parents=True, exist_ok=True)
    shutil.copy2(SOURCE_PLUGIN, packaged_root / ".codex-plugin" / "plugin.json")
    rebuild_directory(packaged_root / "skills", SOURCE_SKILLS)
    rebuild_directory(packaged_root / "assets", SOURCE_ASSETS)

    print(f"Synced Codex plugin package to {packaged_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
