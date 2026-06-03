#!/usr/bin/env python3
"""Extract a PyInstaller executable without executing it."""

from __future__ import annotations

import argparse
import importlib.util
import marshal
import os
from pathlib import Path
import struct
import sys
import zlib


COOKIE_MAGIC = b"MEI\014\013\012\013\016"
PYZ_MAGIC = b"PYZ\0"
PY_TYPES = {b"s", b"m", b"M"}


def sanitize(name: str) -> str:
    name = name.replace("\\", "/").strip("\0")
    while name.startswith("../") or name.startswith("/"):
        name = name.split("/", 1)[-1]
    return name or "unnamed"


def pyc_header(magic: bytes) -> bytes:
    return magic + b"\0" * 12


def find_cookie(blob: bytes) -> tuple[int, int, int, int, int, str]:
    end = blob.rfind(COOKIE_MAGIC)
    if end < 0:
        raise RuntimeError("PyInstaller cookie was not found")

    if end + 88 <= len(blob):
        magic, pkg_len, toc_pos, toc_len, py_ver, pylib = struct.unpack(
            "!8sIIII64s", blob[end : end + 88]
        )
        pylib_name = pylib.split(b"\0", 1)[0].decode("utf-8", "replace")
        return end, pkg_len, toc_pos, toc_len, py_ver, pylib_name

    magic, pkg_len, toc_pos, toc_len, py_ver = struct.unpack("!8sIIII", blob[end : end + 24])
    return end, pkg_len, toc_pos, toc_len, py_ver, ""


def parse_toc(blob: bytes, pkg_start: int, toc_pos: int, toc_len: int) -> list[dict]:
    entries: list[dict] = []
    cursor = pkg_start + toc_pos
    end = cursor + toc_len

    while cursor < end:
        entry_size = struct.unpack("!I", blob[cursor : cursor + 4])[0]
        raw = blob[cursor : cursor + entry_size]
        if len(raw) < 18:
            raise RuntimeError(f"Invalid TOC entry at {cursor}")

        entry_pos, comp_len, uncomp_len, comp_flag, type_code = struct.unpack("!IIIbb", raw[4:18])
        raw_name = raw[18:].split(b"\0", 1)[0]
        name = sanitize(raw_name.decode("utf-8", "replace"))
        entries.append(
            {
                "name": name,
                "pos": entry_pos,
                "comp_len": comp_len,
                "uncomp_len": uncomp_len,
                "comp_flag": comp_flag,
                "type": bytes([type_code]),
            }
        )
        cursor += entry_size

    return entries


def write_file(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def extract_pyz(pyz_path: Path, out_dir: Path, fallback_magic: bytes) -> int:
    blob = pyz_path.read_bytes()
    if not blob.startswith(PYZ_MAGIC):
        return 0

    pyc_magic = blob[4:8] or fallback_magic
    toc_offset = struct.unpack("!I", blob[8:12])[0]
    toc = marshal.loads(blob[toc_offset:])
    count = 0
    namespaces: list[str] = []

    if isinstance(toc, list):
        toc_items = toc
    elif isinstance(toc, dict):
        toc_items = toc.items()
    else:
        raise RuntimeError(f"Unsupported PYZ TOC type: {type(toc)!r}")

    for item in toc_items:
        if isinstance(item, tuple) and len(item) == 2 and isinstance(item[0], str):
            name, entry = item
        else:
            name, entry = item[0], item[1:]

        if len(entry) == 3:
            type_or_pkg, pos, length = entry
        elif len(entry) == 2:
            type_or_pkg = None
            pos, length = entry
        else:
            continue

        if length <= 0:
            namespaces.append(str(name))
            continue

        data = zlib.decompress(blob[pos : pos + length])
        mod_path = out_dir / "PYZ-00.pyz_extracted" / (sanitize(str(name)).replace(".", "/") + ".pyc")
        write_file(mod_path, pyc_header(pyc_magic) + data)
        count += 1

    if namespaces:
        write_file(
            out_dir / "PYZ-00.pyz_extracted" / "_namespace_packages.txt",
            ("\n".join(namespaces) + "\n").encode("utf-8"),
        )

    return count


def extract(exe_path: Path, out_dir: Path) -> None:
    blob = exe_path.read_bytes()
    cookie_pos, pkg_len, toc_pos, toc_len, py_ver, pylib_name = find_cookie(blob)
    pkg_start = len(blob) - pkg_len
    entries = parse_toc(blob, pkg_start, toc_pos, toc_len)

    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = out_dir / "manifest.tsv"
    pyc_magic = importlib.util.MAGIC_NUMBER

    with manifest.open("w", encoding="utf-8", newline="\n") as mf:
        mf.write("name\ttype\tcompressed\tcompressed_size\tuncompressed_size\n")
        for entry in entries:
            pos = pkg_start + int(entry["pos"])
            raw = blob[pos : pos + int(entry["comp_len"])]
            data = zlib.decompress(raw) if entry["comp_flag"] else raw

            type_code = entry["type"]
            rel_name = entry["name"]
            if type_code in PY_TYPES and not rel_name.endswith(".pyc"):
                rel_name += ".pyc"

            if type_code in PY_TYPES and not data.startswith(pyc_magic):
                data = pyc_header(pyc_magic) + data

            target = out_dir / rel_name
            write_file(target, data)
            mf.write(
                f"{entry['name']}\t{type_code.decode('latin1')}\t{entry['comp_flag']}\t"
                f"{entry['comp_len']}\t{entry['uncomp_len']}\n"
            )

    pyz_count = 0
    for pyz in out_dir.glob("*.pyz"):
        pyz_count += extract_pyz(pyz, out_dir, pyc_magic)

    print(f"exe: {exe_path}")
    print(f"output: {out_dir}")
    print(f"python_version_cookie: {py_ver}")
    print(f"python_library: {pylib_name or '(not recorded)'}")
    print(f"cookie_offset: {cookie_pos}")
    print(f"package_start: {pkg_start}")
    print(f"toc_entries: {len(entries)}")
    print(f"pyz_modules: {pyz_count}")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("exe", type=Path)
    parser.add_argument("-o", "--output", type=Path, required=True)
    args = parser.parse_args(argv)
    extract(args.exe, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
