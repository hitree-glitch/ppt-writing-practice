import argparse
import dis
import marshal
import sys
import types
from pathlib import Path


def load_code(path):
    data = Path(path).read_bytes()
    for off in (0, 16):
        try:
            obj = marshal.loads(data[off:])
            if isinstance(obj, types.CodeType):
                return obj
        except Exception:
            pass
    raise SystemExit(f"Could not load marshal code object: {path}")


def walk(code, prefix=""):
    yield prefix, code
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            name = f"{prefix}.{const.co_name}" if prefix else const.co_name
            yield from walk(const, name)


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("pyc")
    ap.add_argument("--dis", action="store_true")
    args = ap.parse_args()
    root = load_code(args.pyc)
    codes = list(walk(root))
    print(f"file={root.co_filename} name={root.co_name} codes={len(codes)}")
    print("\n== CODE OBJECTS ==")
    for name, c in codes:
        print(
            f"{name or '<module>'}: file={c.co_filename} firstlineno={c.co_firstlineno} "
            f"args={c.co_argcount} locals={c.co_nlocals} stack={c.co_stacksize}"
        )
    print("\n== NAMES ==")
    names = sorted(set().union(*(set(c.co_names) for _, c in codes)))
    for n in names:
        print(n)
    print("\n== STRING CONSTANTS ==")
    seen = set()
    for _, c in codes:
        for const in c.co_consts:
            if isinstance(const, str) and const not in seen:
                seen.add(const)
                text = const.replace("\r", "\\r").replace("\n", "\\n")
                print(text[:500])
    if args.dis:
        print("\n== DISASSEMBLY ==")
        for name, c in codes:
            print(f"\n--- {name or '<module>'} ---")
            dis.dis(c)


if __name__ == "__main__":
    main()
