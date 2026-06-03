import argparse
import marshal
import struct
import zlib
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pyz")
    ap.add_argument("--filter", default="")
    args = ap.parse_args()
    data = Path(args.pyz).read_bytes()
    if not data.startswith(b"PYZ\0"):
        raise SystemExit("not a PYZ archive")
    magic = data[4:8]
    toc_pos = struct.unpack("!I", data[8:12])[0]
    toc_blob = data[toc_pos:]
    try:
        toc = marshal.loads(toc_blob)
    except Exception:
        toc = marshal.loads(zlib.decompress(toc_blob))
    print(f"magic={magic.hex()} toc_pos={toc_pos} entries={len(toc)}")
    filt = args.filter.lower()
    items = toc.items() if isinstance(toc, dict) else toc
    for name, meta in sorted(items, key=lambda kv: str(kv[0])):
        if filt and filt not in str(name).lower():
            continue
        print(f"{name}: {meta}")


if __name__ == "__main__":
    main()
