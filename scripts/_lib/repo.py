from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]

COMMON_IGNORED_PARTS = {
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
COMMON_IGNORED_NAMES = {".DS_Store"}
COMMON_IGNORED_SUFFIXES = {".pyc"}


def read_json_file(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text())
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def should_ignore(relative_path: Path) -> bool:
    if any(part in COMMON_IGNORED_PARTS for part in relative_path.parts):
        return True
    if relative_path.name in COMMON_IGNORED_NAMES:
        return True
    if relative_path.suffix in COMMON_IGNORED_SUFFIXES:
        return True
    return False


def iter_files(path: Path) -> list[Path]:
    if path.is_file():
        return [] if should_ignore(Path(path.name)) else [path]

    files: list[Path] = []
    for candidate in sorted(path.rglob("*")):
        if not candidate.is_file():
            continue
        relative_path = candidate.relative_to(path)
        if should_ignore(relative_path):
            continue
        files.append(candidate)
    return files


def file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def collect_files(root: Path) -> dict[Path, str]:
    if not root.exists():
        raise FileNotFoundError(f"Missing required directory: {root}")

    return {path.relative_to(root): file_digest(path) for path in iter_files(root)}


def remove_path(path: Path) -> None:
    if not path.exists() and not path.is_symlink():
        return
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
        return
    path.unlink()


def replace_tree_from_source(source: Path, target: Path) -> None:
    remove_path(target)
    target.mkdir(parents=True, exist_ok=True)

    for source_file in iter_files(source):
        relative_path = source_file.relative_to(source)
        destination = target / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_file, destination)
