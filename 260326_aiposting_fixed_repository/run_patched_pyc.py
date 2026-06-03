#!/usr/bin/env python3
"""Run the patched main pyc with extracted dependencies."""

from __future__ import annotations

import os
from pathlib import Path
import runpy
import sys


ROOT = Path(__file__).resolve().parent
EXTRACT = ROOT / "extracted_260326_aiposting"
RUNTIME_SITE = ROOT / ".runtime_site"
MAIN_PYC = ROOT / "patched" / "AI글쓰기자동화봇_ChatGPT3.pyc"


def add_dll_dir(path: Path) -> None:
    if path.exists():
        os.add_dll_directory(str(path))


def main() -> int:
    dll_dirs = [
        RUNTIME_SITE / "PyQt5" / "Qt5" / "bin",
        RUNTIME_SITE / "PyQt5" / "Qt5" / "plugins",
        EXTRACT,
        EXTRACT / "pywin32_system32",
    ]
    for path in dll_dirs:
        add_dll_dir(path)

    os.environ["QT_PLUGIN_PATH"] = str(RUNTIME_SITE / "PyQt5" / "Qt5" / "plugins")
    os.environ["PATH"] = ";".join(str(p) for p in dll_dirs if p.exists()) + ";" + os.environ.get("PATH", "")
    sys.path.insert(0, str(EXTRACT))
    sys.path.insert(0, str(RUNTIME_SITE))
    os.chdir(EXTRACT)
    runpy.run_path(str(MAIN_PYC), run_name="__main__")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
