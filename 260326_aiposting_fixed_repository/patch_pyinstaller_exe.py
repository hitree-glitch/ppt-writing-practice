#!/usr/bin/env python3
"""Rebuild the PyInstaller archive with the patched main bytecode."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import struct
import zlib


COOKIE_MAGIC = b"MEI\014\013\012\013\016"
SOURCE_EXE = Path(r"C:\Users\user\바탕화면\N 자동화\260326_aiposting.exe")
PATCHED_PYC = Path("patched/AI글쓰기자동화봇_ChatGPT3.pyc")
OUTPUT_EXE = Path("260326_aiposting_patched.exe")
TARGET_NAME = "AI글쓰기자동화봇_ChatGPT3"


@dataclass
class Cookie:
    pos: int
    pkg_len: int
    toc_pos: int
    toc_len: int
    py_ver: int
    pylib: bytes
    size: int


@dataclass
class TocEntry:
    name_bytes: bytes
    name: str
    pos: int
    comp_len: int
    uncomp_len: int
    comp_flag: int
    type_code: int


def find_cookie(blob: bytes) -> Cookie:
    pos = blob.rfind(COOKIE_MAGIC)
    if pos < 0:
        raise RuntimeError("PyInstaller cookie not found")
    if pos + 88 <= len(blob):
        magic, pkg_len, toc_pos, toc_len, py_ver, pylib = struct.unpack("!8sIIII64s", blob[pos : pos + 88])
        return Cookie(pos, pkg_len, toc_pos, toc_len, py_ver, pylib, 88)
    magic, pkg_len, toc_pos, toc_len, py_ver = struct.unpack("!8sIIII", blob[pos : pos + 24])
    return Cookie(pos, pkg_len, toc_pos, toc_len, py_ver, b"", 24)


def parse_toc(blob: bytes, pkg_start: int, cookie: Cookie) -> list[TocEntry]:
    entries: list[TocEntry] = []
    cursor = pkg_start + cookie.toc_pos
    end = cursor + cookie.toc_len
    while cursor < end:
        entry_size = struct.unpack("!I", blob[cursor : cursor + 4])[0]
        raw = blob[cursor : cursor + entry_size]
        pos, comp_len, uncomp_len, comp_flag, type_code = struct.unpack("!IIIbb", raw[4:18])
        name_bytes = raw[18:].split(b"\0", 1)[0]
        name = name_bytes.decode("utf-8", "replace")
        entries.append(TocEntry(name_bytes, name, pos, comp_len, uncomp_len, comp_flag, type_code))
        cursor += entry_size
    return entries


def pack_toc_entry(entry: TocEntry) -> bytes:
    name = entry.name_bytes + b"\0"
    entry_size = 18 + len(name)
    return (
        struct.pack("!I", entry_size)
        + struct.pack("!IIIbb", entry.pos, entry.comp_len, entry.uncomp_len, entry.comp_flag, entry.type_code)
        + name
    )


def main() -> int:
    blob = SOURCE_EXE.read_bytes()
    cookie = find_cookie(blob)
    pkg_start = len(blob) - cookie.pkg_len
    bootloader = blob[:pkg_start]
    entries = parse_toc(blob, pkg_start, cookie)
    replacement_with_header = PATCHED_PYC.read_bytes()
    replacement_payload = replacement_with_header[16:]

    data_section = bytearray()
    new_entries: list[TocEntry] = []
    patched = 0

    for entry in entries:
        raw = blob[pkg_start + entry.pos : pkg_start + entry.pos + entry.comp_len]
        payload = zlib.decompress(raw) if entry.comp_flag else raw
        if entry.name == TARGET_NAME and chr(entry.type_code) == "s":
            payload = replacement_payload
            patched += 1

        pos = len(data_section)
        packed_payload = zlib.compress(payload, 9) if entry.comp_flag else payload
        data_section.extend(packed_payload)
        new_entries.append(
            TocEntry(
                name_bytes=entry.name_bytes,
                name=entry.name,
                pos=pos,
                comp_len=len(packed_payload),
                uncomp_len=len(payload),
                comp_flag=entry.comp_flag,
                type_code=entry.type_code,
            )
        )

    if patched != 1:
        raise RuntimeError(f"Expected to patch exactly 1 entry, patched {patched}")

    toc = b"".join(pack_toc_entry(entry) for entry in new_entries)
    toc_pos = len(data_section)
    toc_len = len(toc)
    pkg_len = len(data_section) + toc_len + cookie.size

    if cookie.size == 88:
        new_cookie = struct.pack("!8sIIII64s", COOKIE_MAGIC, pkg_len, toc_pos, toc_len, cookie.py_ver, cookie.pylib)
    else:
        new_cookie = struct.pack("!8sIIII", COOKIE_MAGIC, pkg_len, toc_pos, toc_len, cookie.py_ver)

    OUTPUT_EXE.write_bytes(bootloader + data_section + toc + new_cookie)
    print(f"patched_exe: {OUTPUT_EXE.resolve()}")
    print(f"old_size: {len(blob)}")
    print(f"new_size: {OUTPUT_EXE.stat().st_size}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
