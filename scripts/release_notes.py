#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# ///

"""Print or publish customer-facing release notes from CHANGELOG.md.

  release_notes.py show 3.0.0      print the notes for one version
  release_notes.py check 3.0.0     exit 1 if CHANGELOG.md has no section for it
  release_notes.py sync            rewrite every published GitHub release from CHANGELOG.md (needs gh)
"""

from __future__ import annotations

import argparse
import sys

from _lib.release_notes import notes_for, sync_published_releases


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("show", "check"):
        sub.add_parser(name).add_argument("version", help="X.Y.Z, with or without a leading v")
    sync = sub.add_parser("sync")
    sync.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.command in {"show", "check"}:
        version = args.version.removeprefix("v")
        notes = notes_for(version)
        if notes is None:
            print(f"CHANGELOG.md has no '## {version}' section", file=sys.stderr)
            return 1
        if args.command == "show":
            print(notes, end="")
        return 0

    updated = sync_published_releases(dry_run=args.dry_run)
    print(f"{'Would update' if args.dry_run else 'Updated'} {len(updated)} release(s): {', '.join(updated) or 'none'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
