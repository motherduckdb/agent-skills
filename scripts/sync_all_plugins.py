#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# ///

"""Sync or verify all packaged harness plugins (Claude, Codex, Copilot, Antigravity).

Usage:
    uv run scripts/sync_all_plugins.py          # rebuild all 4 packaged plugins
    uv run scripts/sync_all_plugins.py --check  # verify all 4 are in sync with /skills
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent

SYNC_SCRIPTS = [
    "sync_claude_plugin.py",
    "sync_codex_plugin.py",
    "sync_copilot_plugin.py",
    "sync_antigravity_plugin.py",
]

CHECK_SCRIPTS = [
    "check_claude_plugin_sync.py",
    "check_codex_plugin_sync.py",
    "check_copilot_plugin_sync.py",
    "check_antigravity_plugin_sync.py",
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify all packaged plugins match source /skills instead of syncing.",
    )
    args = parser.parse_args()

    targets = CHECK_SCRIPTS if args.check else SYNC_SCRIPTS
    for script_name in targets:
        script_path = SCRIPTS_DIR / script_name
        result = subprocess.run([sys.executable, str(script_path)], check=False)
        if result.returncode != 0:
            return result.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
