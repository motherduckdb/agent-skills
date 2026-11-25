#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# ///

from __future__ import annotations

import sys

from _lib.antigravity_plugin import PACKAGED_SKILLS, SOURCE_SKILLS, collect_skill_digests


class SyncError(Exception):
    pass


def main() -> int:
    source_files = collect_skill_digests(SOURCE_SKILLS)
    try:
        packaged_files = collect_skill_digests(PACKAGED_SKILLS)
    except FileNotFoundError as exc:
        raise SyncError(str(exc)) from exc

    source_paths = set(source_files)
    packaged_paths = set(packaged_files)

    details: list[str] = []
    missing = sorted(source_paths - packaged_paths)
    extra = sorted(packaged_paths - source_paths)
    mismatched = sorted(
        path for path in source_paths & packaged_paths if source_files[path] != packaged_files[path]
    )
    if missing:
        details.append("missing in packaged plugin: " + ", ".join(str(path) for path in missing[:10]))
    if extra:
        details.append("extra in packaged plugin: " + ", ".join(str(path) for path in extra[:10]))
    if mismatched:
        details.append("content mismatch: " + ", ".join(str(path) for path in mismatched[:10]))

    if details:
        raise SyncError(
            "Packaged Antigravity plugin skills are out of sync with /skills. "
            + " | ".join(details)
            + " | Run `uv run scripts/sync_antigravity_plugin.py`."
        )

    print(f"Antigravity plugin skills are in sync with source ({len(source_files)} files checked).")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SyncError as exc:
        print(f"Antigravity plugin sync check failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
