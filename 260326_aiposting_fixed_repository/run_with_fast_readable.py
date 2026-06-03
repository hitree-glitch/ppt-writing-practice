#!/usr/bin/env python3
"""Run the extracted app and patch only naverblog text-entry functions."""

from __future__ import annotations

import importlib.abc
import importlib.machinery
import importlib.util
import importlib
import os
from pathlib import Path
import runpy
import sys


ROOT = Path(__file__).resolve().parent
EXTRACT = ROOT / "extracted_260326_aiposting"
PYZ_EXTRACTED = EXTRACT / "PYZ-00.pyz_extracted"
RUNTIME_SITE = ROOT / ".runtime_site"
MAIN_PYC = ROOT / "patched" / "AI글쓰기자동화봇_ChatGPT3.pyc"
PATCH_SOURCE = ROOT / "naverblog_runtime_patch.py"


class PyzPycFinder(importlib.abc.MetaPathFinder):
    """Resolve selected app/dependency pyc modules from the extracted PYZ folder."""

    def __init__(self, pyz_root: Path, native_root: Path, allowed_roots: set[str]) -> None:
        self.pyz_root = pyz_root
        self.native_root = native_root
        self.allowed_roots = allowed_roots

    def package_locations(self, parts: list[str], pyz_package_dir: Path) -> list[str]:
        locations = []
        if pyz_package_dir.is_dir():
            locations.append(str(pyz_package_dir))
        native_package_dir = self.native_root.joinpath(*parts)
        if native_package_dir.is_dir():
            locations.append(str(native_package_dir))
        return locations

    def find_spec(self, fullname: str, path=None, target=None):
        root_name = fullname.partition(".")[0]
        if root_name not in self.allowed_roots:
            return None

        parts = fullname.split(".")
        package_dir = self.pyz_root.joinpath(*parts)
        package_style_path = self.pyz_root.joinpath(*parts, "__init__.pyc")
        flat_package_path = self.pyz_root.joinpath(*parts).with_suffix(".pyc")
        module_path = package_style_path if package_style_path.exists() else flat_package_path
        if not module_path.exists():
            if package_dir.is_dir():
                spec = importlib.machinery.ModuleSpec(fullname, loader=None, is_package=True)
                spec.submodule_search_locations = self.package_locations(parts, package_dir)
                return spec
            return None

        is_package = package_dir.is_dir()
        loader = importlib.machinery.SourcelessFileLoader(fullname, str(module_path))
        spec = importlib.util.spec_from_loader(fullname, loader, is_package=is_package)
        if is_package and spec is not None:
            spec.submodule_search_locations = self.package_locations(parts, package_dir)
        return spec


def add_dll_dir(path: Path) -> None:
    if path.exists():
        os.add_dll_directory(str(path))


def discover_pyz_roots() -> set[str]:
    stdlib_names = getattr(sys, "stdlib_module_names", set())
    excluded_roots = {"PyQt5"}
    roots = set()
    for child in PYZ_EXTRACTED.iterdir():
        if child.name.startswith("__"):
            continue
        root_name = child.stem if child.suffix == ".pyc" else child.name
        if root_name in stdlib_names or root_name in excluded_roots:
            continue
        roots.add(root_name)
    return roots


def preload_runtime_patches() -> None:
    naver_module = importlib.import_module("naver")
    from naver_runtime_patch import apply_runtime_patch as apply_naver_runtime_patch

    apply_naver_runtime_patch(naver_module)

    naverblog_module = importlib.import_module("naverblog")
    from naverblog_runtime_patch import apply_runtime_patch as apply_naverblog_runtime_patch

    apply_naverblog_runtime_patch(naverblog_module)
    print(f"[runtime patch] loaded original naver: {getattr(naver_module, '__file__', '')}")
    print(f"[runtime patch] loaded original naverblog: {getattr(naverblog_module, '__file__', '')}")
    print(f"[runtime patch] patch source: {PATCH_SOURCE}")
    print("[runtime patch] get_top_post = current Naver blog-link extraction")
    print("[runtime patch] write_text = fast clipboard paste, write_quote = fast bold heading")


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
    cert_path = EXTRACT / "certifi" / "cacert.pem"
    if cert_path.exists():
        os.environ["REQUESTS_CA_BUNDLE"] = str(cert_path)
        os.environ["SSL_CERT_FILE"] = str(cert_path)

    sys.path.insert(0, str(EXTRACT))
    sys.path.insert(0, str(RUNTIME_SITE))
    sys.meta_path.insert(
        0,
        PyzPycFinder(PYZ_EXTRACTED, EXTRACT, discover_pyz_roots() | {"google"}),
    )

    preload_runtime_patches()
    os.chdir(ROOT)
    runpy.run_path(str(MAIN_PYC), run_name="__main__")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
