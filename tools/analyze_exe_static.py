import argparse
import hashlib
import os
import re
import struct
from collections import Counter


PYINSTALLER_MAGIC = b"MEI\014\013\012\013\016"


def read_at(f, offset, size):
    f.seek(offset)
    return f.read(size)


def cstr(data):
    return data.split(b"\0", 1)[0].decode("utf-8", "replace")


def parse_pe(path):
    with open(path, "rb") as f:
        size = os.path.getsize(path)
        mz = read_at(f, 0, 64)
        if mz[:2] != b"MZ":
            raise ValueError("Not an MZ executable")
        pe_off = struct.unpack_from("<I", mz, 0x3C)[0]
        sig = read_at(f, pe_off, 4)
        if sig != b"PE\0\0":
            raise ValueError("Missing PE signature")
        coff = read_at(f, pe_off + 4, 20)
        machine, sections, timestamp, ptrsym, numsym, opt_size, chars = struct.unpack("<HHIIIHH", coff)
        opt = read_at(f, pe_off + 24, opt_size)
        magic = struct.unpack_from("<H", opt, 0)[0]
        is64 = magic == 0x20B
        entry = struct.unpack_from("<I", opt, 16)[0]
        image_base = struct.unpack_from("<Q" if is64 else "<I", opt, 24)[0]
        subsystem = struct.unpack_from("<H", opt, 68 if is64 else 92)[0]
        dd_off = 112 if is64 else 96
        data_dirs = []
        if len(opt) >= dd_off + 16 * 8:
            for i in range(16):
                rva, sz = struct.unpack_from("<II", opt, dd_off + i * 8)
                data_dirs.append((rva, sz))
        section_table = pe_off + 24 + opt_size
        sec_rows = []
        for i in range(sections):
            row = read_at(f, section_table + i * 40, 40)
            name = cstr(row[:8])
            vsize, vaddr, raw_size, raw_ptr, rel_ptr, line_ptr, nrel, nline, schars = struct.unpack_from("<IIIIIIHHI", row, 8)
            sec_rows.append(
                {
                    "name": name,
                    "vaddr": vaddr,
                    "vsize": vsize,
                    "raw_ptr": raw_ptr,
                    "raw_size": raw_size,
                    "chars": schars,
                    "entropy": section_entropy(read_at(f, raw_ptr, min(raw_size, 2_000_000))) if raw_size else 0,
                }
            )

        def rva_to_off(rva):
            for s in sec_rows:
                span = max(s["vsize"], s["raw_size"])
                if s["vaddr"] <= rva < s["vaddr"] + span:
                    return s["raw_ptr"] + (rva - s["vaddr"])
            return None

        imports = []
        if len(data_dirs) > 1 and data_dirs[1][0]:
            imp_off = rva_to_off(data_dirs[1][0])
            if imp_off is not None:
                while True:
                    desc = read_at(f, imp_off, 20)
                    if len(desc) < 20 or desc == b"\0" * 20:
                        break
                    orig, tstamp, fwd, name_rva, thunk = struct.unpack("<IIIII", desc)
                    name_off = rva_to_off(name_rva)
                    dll = cstr(read_at(f, name_off, 256)) if name_off is not None else f"<rva:{name_rva:x}>"
                    imports.append(dll)
                    imp_off += 20

        overlay_start = max((s["raw_ptr"] + s["raw_size"] for s in sec_rows), default=0)
        overlay_size = max(0, size - overlay_start)
        return {
            "size": size,
            "sha256": sha256(path),
            "pe_offset": pe_off,
            "machine": machine,
            "architecture": "x64" if machine == 0x8664 else "x86" if machine == 0x14C else hex(machine),
            "sections": sections,
            "timestamp_raw": timestamp,
            "characteristics": chars,
            "optional_magic": hex(magic),
            "entry_rva": entry,
            "image_base": image_base,
            "subsystem": subsystem,
            "imports": imports,
            "section_rows": sec_rows,
            "overlay_start": overlay_start,
            "overlay_size": overlay_size,
        }


def section_entropy(data):
    if not data:
        return 0
    counts = Counter(data)
    n = len(data)
    import math

    return -sum((c / n) * math.log2(c / n) for c in counts.values())


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def extract_strings(path, min_len=5, limit=5000):
    ascii_re = re.compile(rb"[\x20-\x7e]{%d,}" % min_len)
    wide_re = re.compile((rb"(?:[\x20-\x7e]\x00){%d,}" % min_len))
    out = []
    with open(path, "rb") as f:
        data = f.read()
    for m in ascii_re.finditer(data):
        out.append((m.start(), m.group().decode("utf-8", "replace")))
    for m in wide_re.finditer(data):
        s = m.group().replace(b"\x00", b"").decode("utf-8", "replace")
        out.append((m.start(), s))
    out.sort(key=lambda x: x[0])
    return out[:limit], len(out)


def find_pyinstaller(path):
    with open(path, "rb") as f:
        data = f.read()
    pos = data.rfind(PYINSTALLER_MAGIC)
    if pos < 0:
        return None
    candidates = []
    for cookie_size, fmt in [(24, "!8siiii"), (88, "!8siiii64s")]:
        start = pos
        if start + cookie_size <= len(data):
            try:
                values = struct.unpack(fmt, data[start : start + cookie_size])
                item = {
                    "cookie_offset": start,
                    "cookie_size": cookie_size,
                    "pkg_len": values[1],
                    "toc_offset": values[2],
                    "toc_len": values[3],
                    "python_version": values[4],
                }
                if cookie_size == 88:
                    item["python_library"] = cstr(values[5])
                item["archive_start"] = len(data) - item["pkg_len"]
                candidates.append(item)
            except struct.error:
                pass
    return candidates


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    args = ap.parse_args()
    pe = parse_pe(args.path)
    strings, total_strings = extract_strings(args.path)
    pyi = find_pyinstaller(args.path)

    print("== FILE ==")
    for key in ["size", "sha256", "architecture", "pe_offset", "entry_rva", "image_base", "subsystem", "overlay_start", "overlay_size"]:
        print(f"{key}: {pe[key]}")
    print("\n== IMPORT DLLS ==")
    for dll in pe["imports"]:
        print(dll)
    print("\n== SECTIONS ==")
    for s in pe["section_rows"]:
        print(f"{s['name']:10} vaddr=0x{s['vaddr']:08x} vsize={s['vsize']:10} raw=0x{s['raw_ptr']:08x}+{s['raw_size']:10} entropy={s['entropy']:.3f}")
    print("\n== PYINSTALLER ==")
    print(pyi if pyi else "not detected")
    print(f"\n== STRINGS total={total_strings}, showing selected hits ==")
    keywords = re.compile(r"(pyinstaller|python|pyz|pyi_|selenium|chromedriver|webdriver|requests|urllib|openai|naver|keyword|aigold|google|api|token|password|secret|http://|https://|\.py|\.pyd|\.dll|\.exe)", re.I)
    shown = 0
    for off, s in strings:
        if keywords.search(s):
            print(f"0x{off:08x}: {s[:300]}")
            shown += 1
            if shown >= 300:
                break


if __name__ == "__main__":
    main()
