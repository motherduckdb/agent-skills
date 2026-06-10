#!/usr/bin/env python3
"""Bump or verify the repo-wide skills version.

Usage:
    uv run scripts/bump_version.py 2.3.0          # bump all version surfaces
    uv run scripts/bump_version.py --check 2.3.0  # verify all surfaces match

Bumps the manifests, INTEGRATION_VERSION, and every agent-skills/<version>
watermark in one pass. Run the standard validation suite afterwards.
"""

from __future__ import annotations

import argparse
import sys

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))

from _lib.release import ReleaseError, bump, check


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("version", help="target version (X.Y.Z)")
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify all version surfaces match instead of bumping",
    )
    args = parser.parse_args()

    try:
        if args.check:
            problems = check(args.version)
            if problems:
                print(f"Version check failed for {args.version}:")
                for problem in problems:
                    print(f"  - {problem}")
                return 1
            print(f"All version surfaces match {args.version}.")
            return 0

        changes = bump(args.version)
        print(f"Bumped to {args.version}:")
        for change in changes:
            print(f"  - {change}")
        print("Next: run the validation suite and commit.")
        return 0
    except ReleaseError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    return_code = main()
    raise SystemExit(return_code)
