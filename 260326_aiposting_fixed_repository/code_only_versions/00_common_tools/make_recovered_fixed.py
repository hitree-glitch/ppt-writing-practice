#!/usr/bin/env python3
"""Apply conservative mechanical fixes to depyo's Python 3.13 output."""

from __future__ import annotations

from pathlib import Path
import re


SRC = Path("recovered_depyo/decompiled/AI글쓰기자동화봇_ChatGPT3.py")
OUT = Path("recovered_fixed/AI글쓰기자동화봇_ChatGPT3.py")


def main() -> None:
    text = SRC.read_text(encoding="utf-8")

    # depyo 1.2.5 does not decode Python 3.13 LOAD_SUPER_ATTR flags correctly.
    text = re.sub(r"super\(\)\.##NAME_5##\(", "super().__init__(", text)
    text = re.sub(r"super\(\)\.##NAME_17##\(", "super().closeEvent(", text)
    text = re.sub(r"super\(\)\.(selected_tone|selected_preset|schedule_times)\(", "super().__init__(", text)
    text = text.replace("super().selected_publish_type()", "super().__init__()")
    text = text.replace("super().gemini_key()", "super().__init__()")

    # Most FREEVAR_0 artifacts are a mis-read self reference in methods.
    text = text.replace("##FREEVAR_0##", "self")

    # Reconstruct the small publish-mode helper name and branch.
    text = text.replace("def self(mode):", "def _set_mode(mode):")
    text = text.replace(
        'if mode == "single":\n'
        '                        self.stacked.setCurrentIndex(0); ##ERROR##(1)',
        'if mode == "single":\n'
        '                        self.stacked.setCurrentIndex(0)\n'
        '                    else:\n'
        '                        self.stacked.setCurrentIndex(1)',
    )

    # This placeholder comes from a cell-var/default-value sequence. Keep the
    # source syntactically valid and preserve the observable fallback.
    text = text.replace(
        'template = next((l.strip()[2:].strip() for l in lines), "")\n'
        '                    if not ##FREEVAR_2##:\n'
        '                        ##FREEVAR_2##',
        'title = next((l.strip()[2:].strip() for l in lines if l.strip().startswith("# ")), keyword or "")',
    )
    text = text.replace("##FREEVAR_2##", "keyword")
    text = text.replace("##ERROR##", "None")

    text = re.sub(
        r"any\(\(lambda \.0: try:\n"
        r"\s*for t in \.0:\n"
        r"\s*yield t is None\n"
        r"\s*None\n"
        r"\s*return None; except:\n"
        r"\s*pass\), self\.excel_schedule_times\(\)\)",
        "any(t is None for t in self.excel_schedule_times)",
        text,
    )
    text = re.sub(
        r"sum\(\(lambda \.0: try:\n"
        r"\s*for time in \.0:\n"
        r"\s*if time is not None:\n"
        r"\s*pass\n"
        r"\s*try:\n"
        r"\s*yield 1\n"
        r"\s*None\n"
        r"\s*return None\n"
        r"\s*except:\n"
        r"\s*pass; except:\n"
        r"\s*pass\), self\.excel_schedule_times\(\)\)",
        "sum(1 for time in self.excel_schedule_times if time is not None)",
        text,
    )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text, encoding="utf-8", newline="\n")
    print(OUT)


if __name__ == "__main__":
    main()
