import argparse
import marshal
import struct
import types
import zlib
from pathlib import Path


MAGIC = b"MEI\014\013\012\013\016"


def cstr(b):
    return b.split(b"\0", 1)[0].decode("utf-8", "replace")


def parse_cookie(data):
    pos = data.rfind(MAGIC)
    if pos < 0:
        raise SystemExit("PyInstaller cookie not found")
    magic, pkg_len, toc_off, toc_len, pyver, pylib = struct.unpack("!8siiii64s", data[pos : pos + 88])
    archive_start = len(data) - pkg_len
    return {
        "cookie_offset": pos,
        "pkg_len": pkg_len,
        "toc_off": toc_off,
        "toc_len": toc_len,
        "pyver": pyver,
        "pylib": pylib,
        "archive_start": archive_start,
        "toc_abs": archive_start + toc_off,
    }


def iter_toc(data, meta):
    p = meta["toc_abs"]
    end = p + meta["toc_len"]
    while p < end:
        entry_size = struct.unpack("!i", data[p : p + 4])[0]
        raw = data[p : p + entry_size]
        pos, clen, ulen, flag, typ = struct.unpack("!IIIbb", raw[4:18])
        name = cstr(raw[18:])
        yield {
            "entry_size": entry_size,
            "pos": pos,
            "abs": meta["archive_start"] + pos,
            "clen": clen,
            "ulen": ulen,
            "compressed": flag,
            "type": typ,
            "type_chr": chr(typ),
            "name": name,
        }
        p += entry_size


def replacement_codes(filename):
    ns = {}
    src = """
def evaluate_license(current_time):
    return ("valid", 9999)

def check_license():
    return True
"""
    code = compile(src, filename, "exec")
    exec(code, ns)
    return {
        "evaluate_license": ns["evaluate_license"].__code__.replace(co_firstlineno=203),
        "check_license": ns["check_license"].__code__.replace(co_firstlineno=217),
    }


def patch_code_object(code, replacements):
    changed = False
    if code.co_name in replacements:
        return replacements[code.co_name], True
    new_consts = []
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            new_const, sub_changed = patch_code_object(const, replacements)
            new_consts.append(new_const)
            changed = changed or sub_changed
        else:
            new_consts.append(const)
    if changed:
        return code.replace(co_consts=tuple(new_consts)), True
    return code, False


def pad16(blob):
    pad = (-len(blob)) % 16
    return blob + (b"\0" * pad)


def build_toc_entry(e, pos, clen, ulen):
    name = e["name"].encode("utf-8") + b"\0"
    payload = struct.pack("!IIIbb", pos, clen, ulen, e["compressed"], e["type"]) + name
    payload = pad16(payload)
    return struct.pack("!i", len(payload) + 4) + payload


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input_exe")
    ap.add_argument("output_exe")
    args = ap.parse_args()

    data = Path(args.input_exe).read_bytes()
    meta = parse_cookie(data)
    entries = list(iter_toc(data, meta))
    main_entries = [e for e in entries if e["type_chr"] == "s" and e["ulen"] > 100_000]
    if len(main_entries) != 1:
        raise SystemExit(f"Expected one large script entry, found {len(main_entries)}")
    main_entry = main_entries[0]

    main_blob = data[main_entry["abs"] : main_entry["abs"] + main_entry["clen"]]
    if main_entry["compressed"]:
        main_blob = zlib.decompress(main_blob)
    root = marshal.loads(main_blob)
    replacements = replacement_codes(root.co_filename)
    patched_root, changed = patch_code_object(root, replacements)
    if not changed:
        raise SystemExit("No matching license functions were patched")
    patched_blob = marshal.dumps(patched_root)

    prefix = data[: meta["archive_start"]]
    archive_parts = []
    toc_parts = []
    pos = 0
    patched_info = None
    for e in entries:
        if e is main_entry:
            raw = zlib.compress(patched_blob, 9) if e["compressed"] else patched_blob
            ulen = len(patched_blob)
            patched_info = (e["name"], e["clen"], len(raw), e["ulen"], ulen)
        else:
            raw = data[e["abs"] : e["abs"] + e["clen"]]
            ulen = e["ulen"]
        archive_parts.append(raw)
        toc_parts.append(build_toc_entry(e, pos, len(raw), ulen))
        pos += len(raw)

    toc = b"".join(toc_parts)
    toc_off = pos
    archive = b"".join(archive_parts) + toc
    cookie = struct.pack(
        "!8siiii64s",
        MAGIC,
        len(archive) + 88,
        toc_off,
        len(toc),
        meta["pyver"],
        meta["pylib"],
    )
    out = prefix + archive + cookie
    Path(args.output_exe).write_bytes(out)
    print(f"patched_entry={patched_info}")
    print(f"old_size={len(data)} new_size={len(out)}")
    print(f"output={args.output_exe}")


if __name__ == "__main__":
    main()
