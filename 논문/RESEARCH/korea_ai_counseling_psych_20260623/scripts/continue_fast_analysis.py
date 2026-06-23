from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path("RESEARCH/korea_ai_counseling_psych_20260623")
PROCESSED = ROOT / "data" / "processed"
TEXT_DIR = ROOT / "artifacts" / "extracted_text"
SCRIPT = ROOT / "scripts" / "build_korea_ai_psych_dataset_v2.py"

spec = importlib.util.spec_from_file_location("builder", SCRIPT)
builder = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules['builder'] = builder
spec.loader.exec_module(builder)


def load_existing_pages(text_path: Path) -> list[tuple[int, str]]:
    text = text_path.read_text(encoding="utf-8", errors="replace")
    chunks = re.split(r"\n\n--- page (\d+) ---\n", text)
    if len(chunks) < 3:
        return [(0, text)]
    pages: list[tuple[int, str]] = []
    for idx in range(1, len(chunks), 2):
        pages.append((int(chunks[idx]), chunks[idx + 1]))
    return pages


def fast_pdf_pages(path: Path) -> list[tuple[int, str]]:
    import pypdf  # type: ignore

    reader = pypdf.PdfReader(str(path))
    return [(idx, page.extract_text() or "") for idx, page in enumerate(reader.pages, 1)]


def should_extract(row: pd.Series) -> bool:
    category = str(row.get("category", ""))
    return category in {"digital_divide", "smartphone_overdependence", "cyber_violence"}


def analyze() -> tuple[pd.DataFrame, pd.DataFrame]:
    files = pd.read_csv(PROCESSED / "nia_downloaded_files.csv")
    page_rows = []
    both_rows = []
    for _, row in files.iterrows():
        path = Path(str(row["path"]))
        if path.suffix.lower() != ".pdf" or not should_extract(row):
            continue
        text_path = TEXT_DIR / f"{path.stem}.txt"
        if text_path.exists() and text_path.stat().st_size > 1000:
            pages = load_existing_pages(text_path)
        else:
            try:
                pages = fast_pdf_pages(path)
            except Exception as exc:
                pages = [(0, f"PDF extraction failed: {exc!r}")]
            text_path.write_text("".join(f"\n\n--- page {p} ---\n{t}" for p, t in pages), encoding="utf-8", errors="replace")

        for page_no, text in pages:
            ai = builder.term_count(text, builder.AI_TERMS)
            psych = builder.term_count(text, builder.PSYCH_TERMS)
            terms = builder.present_terms(text, builder.AI_TERMS + builder.PSYCH_TERMS)
            base = {
                "category": row.get("category", ""),
                "label": row.get("label", ""),
                "year": row.get("year", ""),
                "title": row.get("title", ""),
                "filename": row.get("filename", ""),
                "page": page_no,
                "ai_term_count": ai,
                "psych_term_count": psych,
                "terms_present": terms,
                "detail_url": row.get("detail_url", ""),
            }
            if ai or psych:
                page_rows.append(base)
            if ai and psych:
                both_rows.append({**base, "snippet": builder.snippet(text, builder.AI_TERMS + builder.PSYCH_TERMS)})
    return pd.DataFrame(page_rows), pd.DataFrame(both_rows)


def main() -> None:
    nia_catalog = pd.read_csv(PROCESSED / "nia_report_catalog.csv")
    downloaded = pd.read_csv(PROCESSED / "nia_downloaded_files.csv")
    pages, both = analyze()
    pages.to_csv(PROCESSED / "nia_relevant_pages.csv", index=False, encoding="utf-8-sig")
    both.to_csv(PROCESSED / "nia_ai_psych_snippets.csv", index=False, encoding="utf-8-sig")

    kosis = builder.collect_kosis()
    kosis.to_csv(PROCESSED / "kosis_candidate_tables.csv", index=False, encoding="utf-8-sig")
    variables = builder.variable_map()
    variables.to_csv(PROCESSED / "korea_ai_psych_variable_map.csv", index=False, encoding="utf-8-sig")

    builder.write_docs(nia_catalog, downloaded, pages, both, kosis, variables)
    print(
        {
            "downloaded_files": len(downloaded),
            "relevant_pdf_pages": len(pages),
            "ai_psych_snippet_pages": len(both),
            "kosis_candidates": len(kosis),
        }
    )


if __name__ == "__main__":
    main()
