#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///

from __future__ import annotations

import argparse
import json
from pathlib import Path

from _lib.product_drift import DEFAULT_RELEASE_NOTES_RSS, audit_product_drift
from _lib.repo import ROOT


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compare MotherDuck release-note links with the skill catalog's product sources."
    )
    parser.add_argument("--since", required=True, help="Include entries on or after YYYY-MM-DD.")
    parser.add_argument("--rss-url", default=DEFAULT_RELEASE_NOTES_RSS)
    parser.add_argument("--catalog", type=Path, default=ROOT / "skills" / "catalog.json")
    parser.add_argument(
        "--check-sources",
        action="store_true",
        help="Fetch catalog source URLs and report redirects or failures. Intended for manual drift review, not the default CI gate.",
    )
    parser.add_argument("--json", action="store_true", help="Emit a machine-readable report.")
    args = parser.parse_args()

    report = audit_product_drift(
        since=args.since,
        rss_url=args.rss_url,
        catalog_path=args.catalog,
        check_sources=args.check_sources,
    )
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0

    print(f"Release-note entries since {args.since}: {len(report['entries'])}")
    for entry in report["entries"]:
        print(f"\n{entry['published']} — {entry['title']}")
        print(f"  {entry['url']}")
        for linked in entry["linked_docs"]:
            owners = ", ".join(linked["skills"]) or "UNMAPPED"
            print(f"  [{owners}] {linked['url']}")

    unmatched = report["unmatched_links"]
    print(f"\nUnmapped release-note documentation links: {len(unmatched)}")
    for url in unmatched:
        print(f"  {url}")

    if args.check_sources:
        failures = [item for item in report["source_checks"] if item["status"] != "ok"]
        print(f"\nCatalog source checks requiring review: {len(failures)}")
        for item in failures:
            detail = item.get("error") or item.get("final_url") or "unknown"
            print(f"  [{item['status']}] {item['url']} -> {detail}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
