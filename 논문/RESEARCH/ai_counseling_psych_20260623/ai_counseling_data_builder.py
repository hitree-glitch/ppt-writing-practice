from __future__ import annotations

import csv
import io
import json
import math
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd


SESSION = Path(__file__).resolve().parent
RAW = SESSION / "data" / "raw"
PROCESSED = SESSION / "data" / "processed"
SOURCES = SESSION / "sources"
OUTPUTS = SESSION / "outputs"
ARTIFACTS = SESSION / "artifacts"

for directory in [RAW, PROCESSED, SOURCES, OUTPUTS, ARTIFACTS]:
    directory.mkdir(parents=True, exist_ok=True)


USER_AGENT = "CodexResearch/1.0 (+local reproducible research build)"
FETCHED_AT = datetime.now(timezone.utc).isoformat()


def log(message: str) -> None:
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}", flush=True)


def fetch_url(url: str, target: Path, timeout: int = 120, retries: int = 3) -> Path:
    if target.exists() and target.stat().st_size > 0:
        log(f"exists: {target.name} ({target.stat().st_size:,} bytes)")
        return target

    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            log(f"download {attempt}/{retries}: {url}")
            with urllib.request.urlopen(request, timeout=timeout) as response:
                target_tmp = target.with_suffix(target.suffix + ".part")
                with target_tmp.open("wb") as f:
                    while True:
                        chunk = response.read(1024 * 1024)
                        if not chunk:
                            break
                        f.write(chunk)
                target_tmp.replace(target)
            log(f"saved: {target} ({target.stat().st_size:,} bytes)")
            return target
        except Exception as exc:  # network retry path
            last_error = exc
            log(f"download failed: {exc}")
            time.sleep(2 * attempt)
    raise RuntimeError(f"Could not fetch {url}: {last_error}")


def read_first_dta_from_zip(zip_path: Path) -> tuple[pd.DataFrame, dict[str, str], str]:
    with zipfile.ZipFile(zip_path) as zf:
        dta_names = [n for n in zf.namelist() if n.lower().endswith(".dta")]
        if not dta_names:
            raise ValueError(f"No .dta file found in {zip_path}")
        dta_name = sorted(dta_names, key=len)[0]
        with zf.open(dta_name) as dta_file:
            reader = pd.io.stata.StataReader(dta_file, convert_categoricals=False)
            labels = reader.variable_labels()
            df = reader.read()
    return df, labels, dta_name


def normalize_text(value: object) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return ""
    return str(value).strip()


def clean_category(value: object) -> str:
    text = normalize_text(value)
    if not text:
        return ""
    lowered = text.lower()
    missing_tokens = {
        "nan",
        "na",
        "n/a",
        "missing",
        "prefer not to say",
        "i prefer not to say",
        "not applicable",
        "none",
    }
    if lowered in missing_tokens:
        return ""
    return text


def weighted_mean_boolean(series: pd.Series, weights: pd.Series | None = None) -> float:
    x = series.astype(float)
    mask = x.notna()
    if weights is None:
        return float(x[mask].mean()) if mask.any() else float("nan")
    w = pd.to_numeric(weights, errors="coerce")
    mask = mask & w.notna() & (w > 0)
    if not mask.any():
        return float("nan")
    return float(np.average(x[mask], weights=w[mask]))


def weighted_crosstab(
    df: pd.DataFrame,
    row: str,
    col: str,
    weight: str | None = None,
    min_n: int = 30,
) -> pd.DataFrame:
    temp = df[[row, col] + ([weight] if weight else [])].copy()
    temp[row] = temp[row].map(clean_category)
    temp[col] = temp[col].map(clean_category)
    temp = temp[(temp[row] != "") & (temp[col] != "")]
    if temp.empty:
        return pd.DataFrame()
    if weight and weight in temp:
        temp["_w"] = pd.to_numeric(temp[weight], errors="coerce").fillna(0)
    else:
        temp["_w"] = 1.0
    grouped = temp.groupby([row, col], dropna=False)["_w"].sum().reset_index()
    counts = temp.groupby([row, col], dropna=False).size().reset_index(name="raw_n")
    grouped = grouped.merge(counts, on=[row, col], how="left")
    totals = grouped.groupby(row)["_w"].transform("sum")
    raw_totals = grouped.groupby(row)["raw_n"].transform("sum")
    grouped["row_pct"] = np.where(totals > 0, grouped["_w"] / totals, np.nan)
    grouped["row_raw_n"] = raw_totals
    grouped = grouped[grouped["row_raw_n"] >= min_n].copy()
    grouped.rename(columns={"_w": "weighted_n"}, inplace=True)
    return grouped.sort_values([row, "row_pct"], ascending=[True, False])


def cramers_v(table: pd.DataFrame) -> float:
    if table.empty:
        return float("nan")
    observed = table.to_numpy(dtype=float)
    total = observed.sum()
    if total <= 0:
        return float("nan")
    row_sum = observed.sum(axis=1, keepdims=True)
    col_sum = observed.sum(axis=0, keepdims=True)
    expected = row_sum @ col_sum / total
    mask = expected > 0
    chi2 = ((observed - expected) ** 2 / np.where(mask, expected, np.nan))[mask].sum()
    r, k = observed.shape
    denom = total * max(min(k - 1, r - 1), 1)
    return float(math.sqrt(chi2 / denom))


def build_hints_analysis() -> dict:
    hints_base = "https://hints.cancer.gov"
    hints_downloads = {
        "HINTS7_2024": f"{hints_base}/dataset/HINTS7_STATA_20250731.zip",
        "HINTS6_2022": f"{hints_base}/dataset/HINTS6_STATA_20250731.zip",
    }

    source_rows = []
    variable_rows = []
    summary_rows = []
    crosstab_frames = []
    hints_details: dict[str, object] = {}

    search_terms = [
        "artificial",
        " ai ",
        "algorithm",
        "chatbot",
        "digital",
        "internet",
        "online",
        "portal",
        "app",
        "depress",
        "anxiety",
        "stress",
        "mental",
        "emotion",
        "psych",
        "counsel",
        "therapy",
        "doctor",
        "health care provider",
        "caregiver",
        "lonely",
        "social support",
        "trust",
        "confident",
    ]

    for dataset_id, url in hints_downloads.items():
        zip_path = fetch_url(url, RAW / f"{dataset_id}_STATA.zip")
        df, labels, dta_name = read_first_dta_from_zip(zip_path)
        log(f"{dataset_id}: loaded {dta_name}, rows={len(df):,}, cols={len(df.columns):,}")

        columns_lower = {c: c.lower() for c in df.columns}
        weight_candidates = [
            c
            for c in df.columns
            if re.search(r"(person|ruc|hh|final)?.*finw|weight|wt", c, flags=re.I)
        ]
        weight_col = ""
        for candidate in weight_candidates:
            if re.search(r"finwt0$|finalwgt|weight$", candidate, flags=re.I):
                weight_col = candidate
                break
        if not weight_col and weight_candidates:
            weight_col = weight_candidates[0]

        matched_cols: list[str] = []
        for col in df.columns:
            label = labels.get(col, "")
            haystack = f" {col} {label} ".lower()
            if any(term in haystack for term in search_terms):
                matched_cols.append(col)
                variable_rows.append(
                    {
                        "dataset": dataset_id,
                        "variable": col,
                        "label": label,
                        "nonmissing": int(df[col].notna().sum()),
                        "unique_values": int(df[col].nunique(dropna=True)),
                        "sample_values": " | ".join(
                            normalize_text(v) for v in df[col].dropna().head(6).tolist()
                        ),
                    }
                )

        ai_cols = [
            c
            for c in matched_cols
            if re.search(r"artificial|(^|_)ai($|_)|algorithm|chatbot|machine", f"{c} {labels.get(c, '')}", re.I)
        ]
        mental_cols = [
            c
            for c in matched_cols
            if re.search(r"depress|anxiety|stress|mental|emotion|psych|counsel|therapy|lonely|social support", f"{c} {labels.get(c, '')}", re.I)
        ]
        digital_cols = [
            c
            for c in matched_cols
            if re.search(r"digital|internet|online|portal|app|electronic|device|web", f"{c} {labels.get(c, '')}", re.I)
        ]

        for col in ai_cols + digital_cols[:8] + mental_cols[:8]:
            counts = df[col].value_counts(dropna=False).head(12)
            for value, count in counts.items():
                summary_rows.append(
                    {
                        "dataset": dataset_id,
                        "variable": col,
                        "label": labels.get(col, ""),
                        "value": normalize_text(value),
                        "raw_n": int(count),
                        "raw_pct": float(count / len(df)) if len(df) else np.nan,
                    }
                )

        # Build exploratory crosstabs if AI/digital and mental/professional-help variables coexist.
        exposure_cols = ai_cols[:5] + digital_cols[:5]
        outcome_cols = mental_cols[:6]
        for exposure in exposure_cols:
            for outcome in outcome_cols:
                if exposure == outcome:
                    continue
                tab = weighted_crosstab(df, exposure, outcome, weight_col or None)
                if tab.empty:
                    continue
                tab.insert(0, "dataset", dataset_id)
                tab.insert(1, "exposure", exposure)
                tab.insert(2, "exposure_label", labels.get(exposure, ""))
                tab.insert(3, "outcome", outcome)
                tab.insert(4, "outcome_label", labels.get(outcome, ""))
                crosstab_frames.append(tab.head(40))

        hints_details[dataset_id] = {
            "url": url,
            "rows": int(len(df)),
            "columns": int(len(df.columns)),
            "dta_member": dta_name,
            "weight_column": weight_col,
            "ai_candidate_columns": ai_cols,
            "digital_candidate_columns": digital_cols[:25],
            "mental_candidate_columns": mental_cols[:25],
        }
        source_rows.append(
            {
                "id": f"src_hints_{dataset_id.lower()}",
                "url": url,
                "title": f"{dataset_id} STATA data and supporting documents",
                "organization": "National Cancer Institute, Health Information National Trends Survey",
                "date": "2025-07-31 update",
                "type": "official public-use microdata",
                "quality_rating": "A",
                "fetched_at": FETCHED_AT,
                "claims": [
                    f"Public-use HINTS file used for individual-level AI/digital health and mental-health/help-seeking variable discovery; rows={len(df)}."
                ],
            }
        )

    pd.DataFrame(variable_rows).to_csv(PROCESSED / "hints_variable_candidates.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(summary_rows).to_csv(PROCESSED / "hints_candidate_value_counts.csv", index=False, encoding="utf-8-sig")
    if crosstab_frames:
        pd.concat(crosstab_frames, ignore_index=True).to_csv(
            PROCESSED / "hints_exploratory_crosstabs.csv", index=False, encoding="utf-8-sig"
        )
    else:
        pd.DataFrame().to_csv(PROCESSED / "hints_exploratory_crosstabs.csv", index=False, encoding="utf-8-sig")

    return {"sources": source_rows, "details": hints_details}


def build_stackoverflow_analysis() -> dict:
    base = "https://media.githubusercontent.com/media/StackExchange/Survey/main/packages/archive/2025"
    schema_url = f"{base}/schema.csv"
    results_url = f"{base}/results.csv"
    schema_path = fetch_url(schema_url, RAW / "stackoverflow_2025_schema.csv")
    results_path = fetch_url(results_url, RAW / "stackoverflow_2025_results.csv", timeout=240)

    schema = pd.read_csv(schema_path)
    df = pd.read_csv(results_path, low_memory=False)
    log(f"Stack Overflow 2025: rows={len(df):,}, cols={len(df.columns):,}")

    schema.to_csv(PROCESSED / "stackoverflow_2025_schema_copy.csv", index=False, encoding="utf-8-sig")

    schema_text_cols = [c for c in schema.columns if schema[c].dtype == object]
    schema["search_blob"] = schema[schema_text_cols].fillna("").agg(" ".join, axis=1).str.lower()
    so_var_candidates = schema[
        schema["search_blob"].str.contains(
            r"\bai\b|artificial|llm|agent|trust|accuracy|frustrat|satisfaction|job|happy|mental|stress|burnout",
            regex=True,
        )
    ].copy()
    so_var_candidates.to_csv(PROCESSED / "stackoverflow_ai_wellbeing_variable_candidates.csv", index=False, encoding="utf-8-sig")

    # Identify relevant columns from both schema and result columns.
    ai_cols = [c for c in df.columns if re.search(r"AI|LLM|Agent", c)]
    wellbeing_cols = [c for c in df.columns if re.search(r"JobSat|Satisfaction|Happy|Frustrat|Mental|Stress|Burnout", c, re.I)]
    profile_cols = [c for c in df.columns if c in {"Country", "Age", "EdLevel", "YearsCode", "YearsCodePro", "DevType", "Employment", "RemoteWork"}]
    selected_cols = profile_cols + ai_cols + wellbeing_cols
    pd.DataFrame({"column": selected_cols}).to_csv(PROCESSED / "stackoverflow_selected_columns.csv", index=False)

    summaries = []
    for col in selected_cols:
        counts = df[col].value_counts(dropna=False).head(30)
        for value, count in counts.items():
            summaries.append(
                {
                    "variable": col,
                    "value": normalize_text(value),
                    "raw_n": int(count),
                    "raw_pct": float(count / len(df)),
                }
            )
    pd.DataFrame(summaries).to_csv(PROCESSED / "stackoverflow_selected_value_counts.csv", index=False, encoding="utf-8-sig")

    # High-value crosstabs for paper ideation.
    key_pairs = []
    for exposure in ["AISelect", "AISent", "AIAcc", "AIBen", "AIComplex", "AIAgents"]:
        if exposure in df.columns:
            for outcome in ["JobSat", "AIFrustrations"]:
                if outcome in df.columns and exposure != outcome:
                    key_pairs.append((exposure, outcome))

    crosstab_frames = []
    association_rows = []
    for exposure, outcome in key_pairs:
        tab = weighted_crosstab(df, exposure, outcome, None, min_n=50)
        if tab.empty:
            continue
        tab.insert(0, "dataset", "StackOverflow_2025")
        tab.insert(1, "exposure", exposure)
        tab.insert(2, "outcome", outcome)
        crosstab_frames.append(tab.head(80))
        pivot = pd.crosstab(df[exposure].map(clean_category), df[outcome].map(clean_category))
        if pivot.shape[0] > 1 and pivot.shape[1] > 1:
            association_rows.append(
                {
                    "dataset": "StackOverflow_2025",
                    "exposure": exposure,
                    "outcome": outcome,
                    "raw_n": int(pivot.to_numpy().sum()),
                    "cramers_v": cramers_v(pivot),
                    "exposure_levels": int(pivot.shape[0]),
                    "outcome_levels": int(pivot.shape[1]),
                }
            )

    if crosstab_frames:
        pd.concat(crosstab_frames, ignore_index=True).to_csv(
            PROCESSED / "stackoverflow_ai_job_satisfaction_crosstabs.csv",
            index=False,
            encoding="utf-8-sig",
        )
    pd.DataFrame(association_rows).to_csv(
        PROCESSED / "stackoverflow_ai_job_satisfaction_associations.csv",
        index=False,
        encoding="utf-8-sig",
    )

    # One compact research-ready table: AI use frequency x job satisfaction.
    if "AISelect" in df.columns and "JobSat" in df.columns:
        compact = weighted_crosstab(df, "AISelect", "JobSat", None, min_n=50)
        compact.to_csv(
            PROCESSED / "stackoverflow_ai_use_by_job_satisfaction.csv",
            index=False,
            encoding="utf-8-sig",
        )

    return {
        "sources": [
            {
                "id": "src_stackoverflow_2025_results",
                "url": results_url,
                "title": "Stack Overflow Developer Survey 2025 public results CSV",
                "organization": "Stack Exchange",
                "date": "2025 survey, GitHub archive accessed 2026-06-23",
                "type": "official public-use microdata",
                "quality_rating": "B",
                "fetched_at": FETCHED_AT,
                "claims": [
                    f"Developer survey microdata includes AI use, AI trust/frustration, and job satisfaction variables; rows={len(df)}."
                ],
            },
            {
                "id": "src_stackoverflow_2025_schema",
                "url": schema_url,
                "title": "Stack Overflow Developer Survey 2025 public schema CSV",
                "organization": "Stack Exchange",
                "date": "2025 survey, GitHub archive accessed 2026-06-23",
                "type": "official metadata",
                "quality_rating": "B",
                "fetched_at": FETCHED_AT,
                "claims": ["Schema used to identify AI, trust, frustration, and job satisfaction fields."],
            },
        ],
        "details": {
            "rows": int(len(df)),
            "columns": int(len(df.columns)),
            "ai_columns": ai_cols,
            "wellbeing_columns": wellbeing_cols,
        },
    }


def worldbank_indicator(indicator: str, label: str) -> pd.DataFrame:
    url = (
        "https://api.worldbank.org/v2/country/all/indicator/"
        + urllib.parse.quote(indicator)
        + "?format=json&per_page=20000"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=120) as response:
        data = json.loads(response.read().decode("utf-8"))
    rows = []
    if isinstance(data, list) and len(data) > 1:
        for item in data[1]:
            rows.append(
                {
                    "country": item["country"]["value"],
                    "countryiso3code": item.get("countryiso3code"),
                    "date": int(item["date"]),
                    indicator: item.get("value"),
                }
            )
    frame = pd.DataFrame(rows)
    frame["indicator_label"] = label
    return frame


def build_macro_panel() -> dict:
    indicators = {
        "IT.NET.USER.ZS": "Individuals using the Internet (% of population)",
        "NY.GDP.PCAP.CD": "GDP per capita (current US$)",
        "SE.ADT.LITR.ZS": "Literacy rate, adult total (% of people ages 15 and above)",
        "SE.TER.ENRR": "School enrollment, tertiary (% gross)",
        "SH.XPD.CHEX.PC.CD": "Current health expenditure per capita (current US$)",
        "SP.POP.TOTL": "Population, total",
    }
    long_frames = []
    for code, label in indicators.items():
        try:
            frame = worldbank_indicator(code, label)
            long_frames.append(frame)
            log(f"World Bank {code}: {len(frame):,} rows")
        except Exception as exc:
            log(f"World Bank {code} failed: {exc}")

    if long_frames:
        wide = None
        for frame in long_frames:
            code_cols = [c for c in frame.columns if c not in {"country", "countryiso3code", "date", "indicator_label"}]
            code = code_cols[0]
            small = frame[["country", "countryiso3code", "date", code]].copy()
            wide = small if wide is None else wide.merge(small, on=["country", "countryiso3code", "date"], how="outer")
        wide.to_csv(PROCESSED / "worldbank_digital_literacy_health_macro_panel.csv", index=False, encoding="utf-8-sig")
    else:
        wide = pd.DataFrame()

    # WHO GHO indicator discovery: save candidate codes for mental health workforce and suicide.
    who_candidates = []
    try:
        request = urllib.request.Request("https://ghoapi.azureedge.net/api/Indicator", headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(request, timeout=120) as response:
            payload = json.loads(response.read().decode("utf-8"))
        rows = payload.get("value", payload if isinstance(payload, list) else [])
        for item in rows:
            name = item.get("IndicatorName", "")
            code = item.get("IndicatorCode", "")
            blob = f"{code} {name}".lower()
            if any(term in blob for term in ["suicide", "psychiatr", "psycholog", "mental health", "depress", "anxiety"]):
                who_candidates.append({"IndicatorCode": code, "IndicatorName": name})
        pd.DataFrame(who_candidates).drop_duplicates().to_csv(
            PROCESSED / "who_gho_mental_health_indicator_candidates.csv",
            index=False,
            encoding="utf-8-sig",
        )
        log(f"WHO GHO mental-health candidate indicators: {len(who_candidates):,}")
    except Exception as exc:
        log(f"WHO GHO discovery failed: {exc}")

    return {
        "sources": [
            {
                "id": "src_worldbank_api",
                "url": "https://api.worldbank.org/v2/",
                "title": "World Bank Indicators API",
                "organization": "World Bank",
                "date": "retrieved 2026-06-23",
                "type": "official API",
                "quality_rating": "A",
                "fetched_at": FETCHED_AT,
                "claims": [
                    "Used for country-year internet use, literacy, tertiary enrollment, health expenditure, GDP per capita, and population indicators."
                ],
            },
            {
                "id": "src_who_gho_indicator_api",
                "url": "https://ghoapi.azureedge.net/api/Indicator",
                "title": "WHO Global Health Observatory Indicator API",
                "organization": "World Health Organization",
                "date": "retrieved 2026-06-23",
                "type": "official API metadata",
                "quality_rating": "A",
                "fetched_at": FETCHED_AT,
                "claims": ["Used to discover suicide, psychiatrist, psychologist, and mental-health indicator codes."],
            },
        ],
        "details": {
            "worldbank_rows": int(len(wide)),
            "worldbank_indicators": indicators,
            "who_candidate_count": int(len(who_candidates)),
        },
    }


def write_sources_jsonl(sources: list[dict]) -> None:
    with (SOURCES / "sources.jsonl").open("w", encoding="utf-8") as f:
        for source in sources:
            f.write(json.dumps(source, ensure_ascii=False) + "\n")

    with (SOURCES / "bibliography.md").open("w", encoding="utf-8") as f:
        f.write("# Bibliography\n\n")
        for source in sources:
            f.write(
                f"- {source.get('organization')}. ({source.get('date')}). "
                f"{source.get('title')} [{source.get('type')}]. {source.get('url')}\n"
            )


def top_rows(path: Path, n: int = 8) -> pd.DataFrame:
    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame()
    try:
        return pd.read_csv(path).head(n)
    except Exception:
        return pd.DataFrame()


def md_table(df: pd.DataFrame, max_cols: int = 7) -> str:
    if df.empty:
        return "_No rows available._"
    df = df.copy()
    if len(df.columns) > max_cols:
        df = df[df.columns[:max_cols]]
    for col in df.columns:
        df[col] = df[col].map(lambda x: normalize_text(x)[:120])
    return df.to_markdown(index=False)


def write_reports(details: dict) -> None:
    catalog_rows = []
    for source in details["sources"]:
        catalog_rows.append(
            {
                "id": source["id"],
                "title": source["title"],
                "organization": source["organization"],
                "type": source["type"],
                "quality_rating": source["quality_rating"],
                "url": source["url"],
            }
        )
    pd.DataFrame(catalog_rows).to_csv(PROCESSED / "dataset_catalog.csv", index=False, encoding="utf-8-sig")

    so_assoc = top_rows(PROCESSED / "stackoverflow_ai_job_satisfaction_associations.csv", 10)
    so_use_job = top_rows(PROCESSED / "stackoverflow_ai_use_by_job_satisfaction.csv", 12)
    hints_vars = top_rows(PROCESSED / "hints_variable_candidates.csv", 20)
    who_candidates = top_rows(PROCESSED / "who_gho_mental_health_indicator_candidates.csv", 20)

    report = f"""# AI Experience, Literacy, and Psychological Counseling/Mental State: Data Build Report

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Working Paper Direction

**Recommended empirical title:**  
AI 리터러시와 심리적 도움추구의 이중효과: HINTS 건강정보 조사, 개발자 AI 사용 자료, 국가 단위 디지털 격차 지표를 결합한 탐색적 분석

**Core claim to test:**  
AI 사용 경험과 AI 신뢰는 심리상담/정신건강 도움추구를 단순히 대체하지 않는다. 오히려 디지털·건강정보 리터러시가 높은 집단에서는 전문적 도움 접근성이 커질 수 있지만, AI 정확도 불신·프라이버시 우려·AI가 “거의 맞지만 틀리는” 경험은 심리적 부담이나 인간 전문가 의존을 강화할 수 있다.

## Dataset Inventory

- **HINTS 7 (2024, updated 2025-07-31)**: U.S. adult public-use health information survey. Official page lists 7,278 total respondents and 7,208 complete responses.
- **HINTS 6 (2022, updated 2025-07-31)**: U.S. adult public-use health information survey. Official page lists 6,252 total respondents and 6,185 complete responses.
- **Stack Overflow Developer Survey 2025**: Official public results; page describes 49,000+ responses from 177 countries, including AI agent tools, LLMs, community platforms, and job satisfaction.
- **World Bank Indicators API**: Internet use, literacy, tertiary enrollment, GDP, health expenditure, and population country-year panel.
- **WHO GHO Indicator API**: Mental-health, suicide, psychiatrist, psychologist indicator discovery list.

## HINTS Candidate Variables

The file `data/processed/hints_variable_candidates.csv` lists AI/digital-health/mental-health/help-seeking variables found by variable names and labels.

{md_table(hints_vars)}

## Stack Overflow AI x Job Satisfaction Signals

Association strength is Cramer's V from raw contingency tables. Treat these as exploratory, not causal.

{md_table(so_assoc)}

AI use frequency by job satisfaction categories:

{md_table(so_use_job)}

## WHO Mental Health Indicator Candidates

{md_table(who_candidates)}

## Researchable Hypotheses

1. **AI-health trust hypothesis:** In HINTS, comfort/trust in AI or algorithmic health tools will be positively associated with online health information seeking and patient-portal use, but not necessarily with lower psychological distress.
2. **AI-friction hypothesis:** In Stack Overflow 2025, frequent AI users may report productivity gains, yet distrust/frustration variables will cluster with lower job satisfaction or neutral satisfaction rather than simple happiness.
3. **Digital readiness moderation hypothesis:** Country-level internet use, adult literacy, tertiary enrollment, and health expenditure will condition whether AI adoption becomes a support channel or a new inequality amplifier.
4. **Counselor-augmentation hypothesis:** A stronger paper can frame AI as a triage/psychoeducation layer that routes users toward licensed counselors, rather than as a replacement for counseling.

## Immediate Next Statistical Models

- HINTS: survey-weighted logistic models for `professional help / patient-provider communication / mental distress proxy` outcomes using AI trust, digital-health behaviors, demographics, and health status.
- Stack Overflow: multinomial or ordinal models predicting job satisfaction from AI use frequency, AI trust, AI frustrations, country, age, employment, years coding, and remote-work context.
- Macro panel: country-year descriptive and partial correlations between internet/literacy/health expenditure and WHO mental-health workforce/suicide indicators after exact indicator selection.

## Limitations

- HINTS is excellent for health-information behavior but may contain AI-health attitudes rather than direct generative-AI counseling use.
- Stack Overflow is not a general-population mental-health survey; job satisfaction is a psychological/work-wellbeing proxy.
- Macro country data are ecological and cannot prove individual-level AI effects.
- Korean nationally representative AI-literacy plus counseling microdata may require MDIS/KOSIS/KHIDI/NIA login or approval; those are catalog candidates, not included here unless accessible without credentials.
"""
    (OUTPUTS / "research_design_and_data_report.md").write_text(report, encoding="utf-8")

    summary = f"""# Executive Summary

I built a reproducible data package for a new paper on **AI use/literacy and psychological counseling or mental state**.

The strongest feasible paper design is a triangulated secondary-data study:

1. **HINTS 2024/2022** for individual-level health-information, AI/digital-health, mental-health/help-seeking candidate variables.
2. **Stack Overflow Developer Survey 2025** for high-resolution AI use, trust, frustration, agent use, and job-satisfaction patterns.
3. **World Bank + WHO GHO** for country-level digital readiness and mental-health system context.

Primary outputs are in `data/processed/` and the full design memo is `outputs/research_design_and_data_report.md`.
"""
    (OUTPUTS / "00_executive_summary.md").write_text(summary, encoding="utf-8")


def main() -> None:
    all_sources: list[dict] = []
    details: dict[str, object] = {"sources": all_sources}

    hints = build_hints_analysis()
    all_sources.extend(hints["sources"])
    details["hints"] = hints["details"]

    so = build_stackoverflow_analysis()
    all_sources.extend(so["sources"])
    details["stackoverflow"] = so["details"]

    macro = build_macro_panel()
    all_sources.extend(macro["sources"])
    details["macro"] = macro["details"]

    write_sources_jsonl(all_sources)
    write_reports({"sources": all_sources})

    state = {
        "topic": "AI use/literacy and psychological counseling or mental state",
        "session_id": "ai_counseling_psych_20260623",
        "status": "data_build_complete",
        "phase": "PHASE_7_OUTPUT",
        "fetched_at": FETCHED_AT,
        "details": details,
        "outputs": [
            "outputs/00_executive_summary.md",
            "outputs/research_design_and_data_report.md",
            "data/processed/dataset_catalog.csv",
            "data/processed/hints_variable_candidates.csv",
            "data/processed/stackoverflow_ai_job_satisfaction_associations.csv",
            "data/processed/worldbank_digital_literacy_health_macro_panel.csv",
            "data/processed/who_gho_mental_health_indicator_candidates.csv",
        ],
    }
    (SESSION / "state.json").write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    (SESSION / "README.md").write_text(
        "# AI Counseling Psychology Research Session\n\n"
        "This folder contains downloaded public datasets, processed variable catalogs, exploratory crosstabs, source metadata, and a research design memo.\n",
        encoding="utf-8",
    )
    log("complete")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        log(f"fatal: {exc}")
        raise
