from __future__ import annotations

from _lib.repo import ROOT


GEMINI_EXTENSION = ROOT / "gemini-extension.json"
GEMINI_CONTEXT = ROOT / "GEMINI.md"
GEMINI_CONTEXT_FILE_NAME = GEMINI_CONTEXT.name
GEMINI_PLAN_DIRECTORY = ".gemini/plans"
GEMINI_COMMANDS = ROOT / "commands"
GEMINI_REQUIRED_COMMANDS = [
    GEMINI_COMMANDS / "motherduck" / "catalog.toml",
    GEMINI_COMMANDS / "motherduck" / "route.toml",
]
GEMINI_REQUIRED_PACKAGING_ENTRIES = [
    GEMINI_EXTENSION,
    GEMINI_CONTEXT,
    ROOT / "skills",
]
GEMINI_OPTIONAL_PACKAGING_ENTRIES = [
    GEMINI_COMMANDS,
    ROOT / "assets",
    ROOT / "LICENSE",
    ROOT / "README.md",
]
