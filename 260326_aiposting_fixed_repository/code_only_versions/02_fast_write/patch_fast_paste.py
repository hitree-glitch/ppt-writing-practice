#!/usr/bin/env python3
"""Patch naverblog.write_text to paste each text block through the clipboard."""

from __future__ import annotations

from dataclasses import dataclass
import marshal
from pathlib import Path
import struct
import types
import zlib


COOKIE_MAGIC = b"MEI\014\013\012\013\016"
ROOT = Path(__file__).resolve().parent
SOURCE_EXE = Path(r"C:\Users\user\바탕화면\N 자동화\260326_aiposting.exe")
EXTRACT = ROOT / "extracted_260326_aiposting"
SOURCE_NAVERBLOG_PYC = EXTRACT / "PYZ-00.pyz_extracted" / "naverblog.pyc"
SOURCE_PYZ = EXTRACT / "PYZ.pyz"
PATCHED_MAIN_PYC = ROOT / "patched" / "AI글쓰기자동화봇_ChatGPT3.pyc"
PATCHED_NAVERBLOG_PYC = ROOT / "patched" / "naverblog.pyc"
PATCHED_PYZ = ROOT / "patched" / "PYZ.pyz"
OUTPUT_EXE = ROOT / "260326_aiposting_fastpaste.exe"
MAIN_ENTRY_NAME = "AI글쓰기자동화봇_ChatGPT3"


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


def replacement_write_text_code() -> types.CodeType:
    namespace: dict[str, object] = {}
    source = """
def write_text(driver, text):
    if text is None:
        return None
    content = str(text)
    if not content:
        return None
    input_text_mixed(driver, content, use_clipboard_probability=1.0)
    time.sleep(0.05)
    return None
"""
    compiled = compile(source, "naverblog.py", "exec")
    exec(compiled, namespace)
    return namespace["write_text"].__code__


def replace_code_object(code: types.CodeType, target_name: str, replacement: types.CodeType) -> tuple[types.CodeType, int]:
    new_consts = []
    replaced = 0
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            if const.co_name == target_name:
                new_consts.append(replacement)
                replaced += 1
            else:
                new_const, child_count = replace_code_object(const, target_name, replacement)
                new_consts.append(new_const)
                replaced += child_count
        else:
            new_consts.append(const)
    if replaced:
        code = code.replace(co_consts=tuple(new_consts))
    return code, replaced


def patch_naverblog_pyc() -> None:
    data = SOURCE_NAVERBLOG_PYC.read_bytes()
    header = data[:16]
    code = marshal.loads(data[16:])
    patched_code, count = replace_code_object(code, "write_text", replacement_write_text_code())
    if count != 1:
        raise RuntimeError(f"Expected one write_text code object, replaced {count}")
    PATCHED_NAVERBLOG_PYC.parent.mkdir(parents=True, exist_ok=True)
    PATCHED_NAVERBLOG_PYC.write_bytes(header + marshal.dumps(patched_code))
    print(f"patched_naverblog_pyc: {PATCHED_NAVERBLOG_PYC}")


def rebuild_pyz() -> None:
    pyz = SOURCE_PYZ.read_bytes()
    toc_offset = struct.unpack("!I", pyz[8:12])[0]
    toc = marshal.loads(pyz[toc_offset:])
    min_payload_pos = min(entry[1][1] for entry in toc if len(entry[1]) == 3 and entry[1][2] > 0)
    prefix = bytearray(pyz[:min_payload_pos])
    patched_payload = PATCHED_NAVERBLOG_PYC.read_bytes()[16:]

    body = bytearray()
    new_toc = []
    patched = 0
    for name, entry in toc:
        type_code, pos, length = entry
        if length <= 0:
            new_toc.append((name, (type_code, pos, length)))
            continue
        if name == "naverblog":
            raw = zlib.compress(patched_payload, 9)
            patched += 1
        else:
            raw = pyz[pos : pos + length]
        new_pos = len(prefix) + len(body)
        body.extend(raw)
        new_toc.append((name, (type_code, new_pos, len(raw))))

    if patched != 1:
        raise RuntimeError(f"Expected one naverblog PYZ entry, patched {patched}")

    new_toc_offset = len(prefix) + len(body)
    prefix[8:12] = struct.pack("!I", new_toc_offset)
    PATCHED_PYZ.write_bytes(bytes(prefix) + bytes(body) + marshal.dumps(new_toc))
    print(f"patched_pyz: {PATCHED_PYZ}")


def find_cookie(blob: bytes) -> Cookie:
    pos = blob.rfind(COOKIE_MAGIC)
    if pos < 0:
        raise RuntimeError("PyInstaller cookie not found")
    if pos + 88 <= len(blob):
        _magic, pkg_len, toc_pos, toc_len, py_ver, pylib = struct.unpack("!8sIIII64s", blob[pos : pos + 88])
        return Cookie(pos, pkg_len, toc_pos, toc_len, py_ver, pylib, 88)
    _magic, pkg_len, toc_pos, toc_len, py_ver = struct.unpack("!8sIIII", blob[pos : pos + 24])
    return Cookie(pos, pkg_len, toc_pos, toc_len, py_ver, b"", 24)


def parse_carchive_toc(blob: bytes, pkg_start: int, cookie: Cookie) -> list[TocEntry]:
    entries: list[TocEntry] = []
    cursor = pkg_start + cookie.toc_pos
    end = cursor + cookie.toc_len
    while cursor < end:
        entry_size = struct.unpack("!I", blob[cursor : cursor + 4])[0]
        raw = blob[cursor : cursor + entry_size]
        pos, comp_len, uncomp_len, comp_flag, type_code = struct.unpack("!IIIbb", raw[4:18])
        name_bytes = raw[18:].split(b"\0", 1)[0]
        entries.append(
            TocEntry(
                name_bytes=name_bytes,
                name=name_bytes.decode("utf-8", "replace"),
                pos=pos,
                comp_len=comp_len,
                uncomp_len=uncomp_len,
                comp_flag=comp_flag,
                type_code=type_code,
            )
        )
        cursor += entry_size
    return entries


def pack_carchive_toc_entry(entry: TocEntry) -> bytes:
    name = entry.name_bytes + b"\0"
    entry_size = 18 + len(name)
    return (
        struct.pack("!I", entry_size)
        + struct.pack("!IIIbb", entry.pos, entry.comp_len, entry.uncomp_len, entry.comp_flag, entry.type_code)
        + name
    )


def rebuild_exe() -> None:
    blob = SOURCE_EXE.read_bytes()
    cookie = find_cookie(blob)
    pkg_start = len(blob) - cookie.pkg_len
    bootloader = blob[:pkg_start]
    entries = parse_carchive_toc(blob, pkg_start, cookie)
    patched_main_payload = PATCHED_MAIN_PYC.read_bytes()[16:]
    patched_pyz_payload = PATCHED_PYZ.read_bytes()

    data_section = bytearray()
    new_entries: list[TocEntry] = []
    patched_main = 0
    patched_pyz = 0

    for entry in entries:
        raw = blob[pkg_start + entry.pos : pkg_start + entry.pos + entry.comp_len]
        payload = zlib.decompress(raw) if entry.comp_flag else raw

        if entry.name == MAIN_ENTRY_NAME and chr(entry.type_code) == "s":
            payload = patched_main_payload
            patched_main += 1
        elif entry.name == "PYZ.pyz" and chr(entry.type_code) == "z":
            payload = patched_pyz_payload
            patched_pyz += 1

        pos = len(data_section)
        packed = zlib.compress(payload, 9) if entry.comp_flag else payload
        data_section.extend(packed)
        new_entries.append(
            TocEntry(
                name_bytes=entry.name_bytes,
                name=entry.name,
                pos=pos,
                comp_len=len(packed),
                uncomp_len=len(payload),
                comp_flag=entry.comp_flag,
                type_code=entry.type_code,
            )
        )

    if patched_main != 1 or patched_pyz != 1:
        raise RuntimeError(f"Patch counts unexpected: main={patched_main}, pyz={patched_pyz}")

    toc = b"".join(pack_carchive_toc_entry(entry) for entry in new_entries)
    toc_pos = len(data_section)
    toc_len = len(toc)
    pkg_len = len(data_section) + toc_len + cookie.size
    if cookie.size == 88:
        new_cookie = struct.pack("!8sIIII64s", COOKIE_MAGIC, pkg_len, toc_pos, toc_len, cookie.py_ver, cookie.pylib)
    else:
        new_cookie = struct.pack("!8sIIII", COOKIE_MAGIC, pkg_len, toc_pos, toc_len, cookie.py_ver)

    OUTPUT_EXE.write_bytes(bootloader + data_section + toc + new_cookie)
    print(f"patched_exe: {OUTPUT_EXE}")
    print(f"new_size: {OUTPUT_EXE.stat().st_size}")


def main() -> int:
    if not PATCHED_MAIN_PYC.exists():
        raise FileNotFoundError(f"Missing patched main pyc: {PATCHED_MAIN_PYC}. Run patch_remove_date_check.py first.")
    patch_naverblog_pyc()
    rebuild_pyz()
    rebuild_exe()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
