#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# ///

from __future__ import annotations

import sys

from _lib.claude_plugin import CLAUDE_PACKAGED_PLUGIN_MANIFEST, CLAUDE_PACKAGED_PLUGIN_SKILLS, inject_argument_hint
from _lib.repo import ROOT, collect_files


SOURCE_SKILLS = ROOT / "skills"


class SyncError(Exception):
    pass


def main() -> int:
    if not CLAUDE_PACKAGED_PLUGIN_MANIFEST.exists():
        raise SyncError(f"Missing required Claude plugin manifest: {CLAUDE_PACKAGED_PLUGIN_MANIFEST}")

    source_files = collect_files(SOURCE_SKILLS)
    packaged_files = collect_files(CLAUDE_PACKAGED_PLUGIN_SKILLS)

    source_paths = set(source_files)
    packaged_paths = set(packaged_files)

    missing_in_packaged = sorted(source_paths - packaged_paths)
    extra_in_packaged = sorted(packaged_paths - source_paths)
    content_mismatches: list[str] = []
    for relative_path in sorted(source_paths & packaged_paths):
        source_text = (SOURCE_SKILLS / relative_path).read_text()
        packaged_text = (CLAUDE_PACKAGED_PLUGIN_SKILLS / relative_path).read_text()
        expected_text = inject_argument_hint(relative_path.parent.name, source_text) if relative_path.name == "SKILL.md" else source_text
        if packaged_text != expected_text:
            content_mismatches.append(str(relative_path))

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
                "content mismatch: " + ", ".join(content_mismatches[:10])
            )
        raise SyncError(
            "Packaged Claude plugin skills are out of sync with /skills. "
            + " | ".join(details)
            + " | Run `uv run scripts/sync_claude_plugin.py`."
        )

    print(f"Claude plugin skills are in sync with source ({len(source_files)} files checked).")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SyncError as exc:
        print(f"Claude plugin sync check failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
