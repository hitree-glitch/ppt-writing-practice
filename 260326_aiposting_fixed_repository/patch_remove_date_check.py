#!/usr/bin/env python3
"""Create a patched pyc that removes the date-based license check."""

from __future__ import annotations

import marshal
from pathlib import Path
import types


ROOT = Path(__file__).resolve().parent
SOURCE_PYC = ROOT / "extracted_260326_aiposting" / "AI글쓰기자동화봇_ChatGPT3.pyc"
PATCHED_DIR = ROOT / "patched"
PATCHED_PYC = PATCHED_DIR / "AI글쓰기자동화봇_ChatGPT3.pyc"


def replacement_check_license_code() -> types.CodeType:
    namespace: dict[str, object] = {}
    source = """
def check_license(show_message, exit_on_fail, timeout):
    return True, 9999, ""
"""
    compiled = compile(source, "AI글쓰기자동화봇_ChatGPT3.py", "exec")
    exec(compiled, namespace)
    fn = namespace["check_license"]
    return fn.__code__


def replace_code_object(code: types.CodeType, target_name: str, replacement: types.CodeType) -> tuple[types.CodeType, int]:
    replaced = 0
    new_consts = []

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


def main() -> int:
    data = SOURCE_PYC.read_bytes()
    header = data[:16]
    code = marshal.loads(data[16:])
    patched_code, count = replace_code_object(code, "check_license", replacement_check_license_code())

    if count != 1:
        raise RuntimeError(f"Expected to replace exactly 1 check_license code object, replaced {count}")

    PATCHED_DIR.mkdir(parents=True, exist_ok=True)
    PATCHED_PYC.write_bytes(header + marshal.dumps(patched_code))
    print(f"patched: {PATCHED_PYC}")
    print("check_license now returns: (True, 9999, '')")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
