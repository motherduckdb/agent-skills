#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# ///

from __future__ import annotations

import shutil

from _lib.copilot_plugin import PACKAGED_SKILLS, SOURCE_SKILLS, iter_skill_files
from _lib.repo import remove_path


def main() -> int:
    remove_path(PACKAGED_SKILLS)
    for relative_path, source_file in iter_skill_files(SOURCE_SKILLS).items():
        destination = PACKAGED_SKILLS / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_file, destination)

    print(f"Synced Copilot plugin skills to {PACKAGED_SKILLS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
