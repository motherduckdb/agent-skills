#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import tarfile
from pathlib import Path

from gemini_extension_config import (
    GEMINI_EXTENSION,
    GEMINI_OPTIONAL_PACKAGING_ENTRIES,
    GEMINI_REQUIRED_PACKAGING_ENTRIES,
    ROOT,
)


DEFAULT_OUTPUT_DIR = ROOT / "release"

SKIP_NAMES = {
    ".DS_Store",
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "logs",
    "node_modules",
    "target",
}


def iter_files(path: Path) -> list[Path]:
    if path.is_file():
        return [path]

    files: list[Path] = []
    for candidate in sorted(path.rglob("*")):
        if candidate.is_dir():
            continue
        if any(part in SKIP_NAMES for part in candidate.parts):
            continue
        files.append(candidate)
    return files


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a self-contained Gemini CLI extension archive.")
    parser.add_argument(
        "--out-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Directory for the generated archive. Defaults to ./release.",
    )
    args = parser.parse_args()

    manifest = json.loads(GEMINI_EXTENSION.read_text())
    extension_name = manifest["name"]
    output_dir = Path(args.out_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    archive_path = output_dir / f"{extension_name}.tar.gz"

    include_paths: list[Path] = []
    for entry_path in GEMINI_REQUIRED_PACKAGING_ENTRIES + GEMINI_OPTIONAL_PACKAGING_ENTRIES:
        if entry_path in GEMINI_REQUIRED_PACKAGING_ENTRIES and not entry_path.exists():
            raise FileNotFoundError(f"Missing required packaging input: {entry_path}")
        if entry_path.exists():
            include_paths.append(entry_path)

    with tarfile.open(archive_path, "w:gz") as archive:
        for include_path in include_paths:
            for file_path in iter_files(include_path):
                archive.add(file_path, arcname=file_path.relative_to(ROOT))

    print(f"Packaged Gemini extension: {archive_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
