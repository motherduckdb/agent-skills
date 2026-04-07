#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# ///

from __future__ import annotations

from _lib.claude_plugin import (
    CLAUDE_PACKAGED_PLUGIN_MANIFEST,
    CLAUDE_PACKAGED_PLUGIN_SKILLS,
    inject_argument_hint,
)
from _lib.repo import ROOT, replace_tree_from_source


SOURCE_SKILLS = ROOT / "skills"


def main() -> int:
    if not CLAUDE_PACKAGED_PLUGIN_MANIFEST.exists():
        raise FileNotFoundError(
            f"Missing required Claude plugin manifest: {CLAUDE_PACKAGED_PLUGIN_MANIFEST}"
        )

    replace_tree_from_source(SOURCE_SKILLS, CLAUDE_PACKAGED_PLUGIN_SKILLS)

    for skill_path in sorted(CLAUDE_PACKAGED_PLUGIN_SKILLS.glob("*/SKILL.md")):
        skill_name = skill_path.parent.name
        skill_path.write_text(inject_argument_hint(skill_name, skill_path.read_text()))

    print(f"Synced Claude plugin package to {CLAUDE_PACKAGED_PLUGIN_SKILLS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
