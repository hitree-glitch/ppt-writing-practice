#!/usr/bin/env python3
"""Create lossless inspection reports for a Python .pyc file."""

from __future__ import annotations

from collections import Counter
import dis
import io
import marshal
from pathlib import Path
import types


PYC = Path("extracted_260326_aiposting/AI글쓰기자동화봇_ChatGPT3.pyc")
OUT_DIR = Path("bytecode_report")


def iter_code(code: types.CodeType):
    yield code
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            yield from iter_code(const)


def safe_repr(value):
    text = repr(value)
    if len(text) > 500:
        text = text[:497] + "..."
    return text


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    data = PYC.read_bytes()
    code = marshal.loads(data[16:])
    code_objects = list(iter_code(code))

    dis_out = io.StringIO()
    dis.dis(code, file=dis_out)
    (OUT_DIR / "AI글쓰기자동화봇_ChatGPT3.dis.txt").write_text(
        dis_out.getvalue(), encoding="utf-8", newline="\n"
    )

    with (OUT_DIR / "AI글쓰기자동화봇_ChatGPT3.code_map.txt").open(
        "w", encoding="utf-8", newline="\n"
    ) as f:
        f.write(f"pyc: {PYC}\n")
        f.write(f"code_objects: {len(code_objects)}\n\n")
        for idx, co in enumerate(code_objects):
            f.write(f"[{idx}] {co.co_qualname}\n")
            f.write(f"  name: {co.co_name}\n")
            f.write(f"  firstlineno: {co.co_firstlineno}\n")
            f.write(f"  filename: {co.co_filename}\n")
            f.write(f"  argcount: {co.co_argcount}\n")
            f.write(f"  posonlyargcount: {co.co_posonlyargcount}\n")
            f.write(f"  kwonlyargcount: {co.co_kwonlyargcount}\n")
            f.write(f"  stacksize: {co.co_stacksize}\n")
            f.write(f"  flags: {co.co_flags}\n")
            f.write(f"  varnames: {co.co_varnames!r}\n")
            f.write(f"  names: {co.co_names!r}\n")
            f.write(f"  freevars: {co.co_freevars!r}\n")
            f.write(f"  cellvars: {co.co_cellvars!r}\n")
            f.write(f"  consts: {len(co.co_consts)}\n\n")

    strings = []
    for co in code_objects:
        for const in co.co_consts:
            if isinstance(const, str):
                strings.append((co.co_qualname, co.co_firstlineno, const))

    with (OUT_DIR / "AI글쓰기자동화봇_ChatGPT3.strings.txt").open(
        "w", encoding="utf-8", newline="\n"
    ) as f:
        f.write(f"strings: {len(strings)}\n\n")
        for qualname, line, value in strings:
            f.write(f"[{line}] {qualname}: {safe_repr(value)}\n")

    import_names = Counter()
    for instr in dis.get_instructions(code):
        if instr.opname == "IMPORT_NAME":
            import_names[str(instr.argval)] += 1

    with (OUT_DIR / "AI글쓰기자동화봇_ChatGPT3.summary.txt").open(
        "w", encoding="utf-8", newline="\n"
    ) as f:
        f.write("Summary\n")
        f.write(f"code_objects: {len(code_objects)}\n")
        f.write(f"strings: {len(strings)}\n")
        f.write(f"top_level_imports: {dict(import_names)}\n")
        f.write("\nTop-level names:\n")
        f.write(", ".join(code.co_names))
        f.write("\n")

    print(OUT_DIR)
    print(f"code_objects={len(code_objects)} strings={len(strings)}")


if __name__ == "__main__":
    main()
