#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# ///

from __future__ import annotations

import shutil

from _lib.repo import ROOT, read_json_file, remove_path, replace_tree_from_source

SOURCE_PLUGIN = ROOT / ".codex-plugin" / "plugin.json"
SOURCE_SKILLS = ROOT / "skills"
SOURCE_ASSETS = ROOT / "assets"


def main() -> int:
    plugin_name = str(read_json_file(SOURCE_PLUGIN)["name"])
    packaged_root = ROOT / "plugins" / plugin_name

    remove_path(packaged_root)

    (packaged_root / ".codex-plugin").mkdir(parents=True, exist_ok=True)
    shutil.copy2(SOURCE_PLUGIN, packaged_root / ".codex-plugin" / "plugin.json")
    replace_tree_from_source(SOURCE_SKILLS, packaged_root / "skills")
    replace_tree_from_source(SOURCE_ASSETS, packaged_root / "assets")

    print(f"Synced Codex plugin package to {packaged_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
