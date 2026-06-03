import argparse
import os
import struct
import zlib
from pathlib import Path


MAGIC = b"MEI\014\013\012\013\016"


def cstr(b):
    return b.split(b"\0", 1)[0].decode("utf-8", "replace")


def cookie(data):
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
        "pylib": cstr(pylib),
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
            "type": chr(typ),
            "name": name,
        }
        p += entry_size


def sanitize(name):
    return "".join(ch if ch.isalnum() or ch in "._-+@()[]{} " else "_" for ch in name)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exe")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--extract-dir")
    ap.add_argument("--only", nargs="*", default=[])
    args = ap.parse_args()
    data = Path(args.exe).read_bytes()
    meta = cookie(data)
    entries = list(iter_toc(data, meta))
    print(f"pyver={meta['pyver']} pylib={meta['pylib']} entries={len(entries)} archive_start={meta['archive_start']}")
    counts = {}
    for e in entries:
        counts[e["type"]] = counts.get(e["type"], 0) + 1
    print("types:", " ".join(f"{k}:{v}" for k, v in sorted(counts.items())))
    if args.list:
        for e in entries:
            print(f"{e['type']} comp={e['compressed']} pos={e['pos']:9} clen={e['clen']:9} ulen={e['ulen']:9} {e['name']}")
    if args.extract_dir:
        outdir = Path(args.extract_dir)
        outdir.mkdir(parents=True, exist_ok=True)
        wanted = set(args.only)
        for e in entries:
            if wanted and e["name"] not in wanted and e["type"] not in wanted:
                continue
            blob = data[e["abs"] : e["abs"] + e["clen"]]
            if e["compressed"]:
                try:
                    blob = zlib.decompress(blob)
                except zlib.error as exc:
                    print(f"decompress failed {e['name']}: {exc}")
                    continue
            suffix = ".pyc" if e["type"] in {"m", "s"} and not e["name"].endswith(".pyc") else ""
            target = outdir / f"{e['type']}_{sanitize(e['name'])}{suffix}"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(blob)
            print(f"extracted {target} ({len(blob)} bytes)")


if __name__ == "__main__":
    main()
