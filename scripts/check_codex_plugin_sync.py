#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# ///

from __future__ import annotations

import sys

from _lib.repo import ROOT, collect_files, read_json_file

SOURCE_PLUGIN = ROOT / ".codex-plugin" / "plugin.json"
SOURCE_SKILLS = ROOT / "skills"


class SyncError(Exception):
    pass


def main() -> int:
    if not SOURCE_PLUGIN.exists():
        raise SyncError(f"Missing required source plugin manifest: {SOURCE_PLUGIN}")

    packaged_root = ROOT / "plugins" / str(read_json_file(SOURCE_PLUGIN)["name"])
    packaged_plugin = packaged_root / ".codex-plugin" / "plugin.json"
    packaged_skills = packaged_root / "skills"
    if not packaged_plugin.exists():
        raise SyncError(f"Missing required packaged plugin manifest: {packaged_plugin}")

    source_manifest = SOURCE_PLUGIN.read_text()
    packaged_manifest = packaged_plugin.read_text()
    if source_manifest != packaged_manifest:
        raise SyncError(
            "Packaged Codex plugin manifest is out of sync with .codex-plugin/plugin.json. "
            "Run `uv run scripts/sync_codex_plugin.py`."
        )

    source_files = collect_files(SOURCE_SKILLS)
    packaged_files = collect_files(packaged_skills)

    source_paths = set(source_files)
    packaged_paths = set(packaged_files)

    missing_in_packaged = sorted(source_paths - packaged_paths)
    extra_in_packaged = sorted(packaged_paths - source_paths)
    content_mismatches = sorted(
        relative_path
        for relative_path in source_paths & packaged_paths
        if source_files[relative_path] != packaged_files[relative_path]
    )

    if missing_in_packaged or extra_in_packaged or content_mismatches:
        details: list[str] = []
        if missing_in_packaged:
            details.append(
                "missing in packaged plugin: " + ", ".join(str(path) for path in missing_in_packaged[:10])
            )
        if extra_in_packaged:
            details.append(
                "extra in packaged plugin: " + ", ".join(str(path) for path in extra_in_packaged[:10])
            )
        if content_mismatches:
            details.append(
                "content mismatch: " + ", ".join(str(path) for path in content_mismatches[:10])
            )
        raise SyncError(
            "Packaged Codex plugin skills are out of sync with /skills. "
            + " | ".join(details)
            + " | Run `uv run scripts/sync_codex_plugin.py`."
        )

    print(f"Codex plugin skills are in sync with source ({len(source_files)} files checked).")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SyncError as exc:
        print(f"Codex plugin sync check failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
