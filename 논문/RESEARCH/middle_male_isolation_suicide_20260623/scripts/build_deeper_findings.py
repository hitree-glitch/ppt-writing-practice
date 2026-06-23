from pathlib import Path
import math
import re

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parents[1]
ARTIFACTS = ROOT / "artifacts"
OUTPUTS = ROOT / "outputs"


SEOUL = "\uc11c\uc6b8"
GYEONGGI = "\uacbd\uae30"
DAEGU = "\ub300\uad6c"


def zscore(series: pd.Series) -> pd.Series:
    std = series.std(ddof=0)
    if std == 0 or math.isnan(std):
        return series * 0
    return (series - series.mean()) / std


def pct(value: float) -> float:
    return round(float(value), 1)


def md_table(df: pd.DataFrame) -> str:
    rendered = df.copy()
    for col in rendered.columns:
        if pd.api.types.is_float_dtype(rendered[col]):
            rendered[col] = rendered[col].map(lambda v: "" if pd.isna(v) else f"{v:.1f}")
    headers = [str(col) for col in rendered.columns]
    rows = [[str(value) for value in row] for row in rendered.to_numpy()]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def age_start(age_band: str) -> int:
    match = re.search(r"\d+", str(age_band))
    if not match:
        raise ValueError(f"Cannot parse age band: {age_band!r}")
    return int(match.group(0))


def aggregate_rate(group: pd.DataFrame) -> float:
    # KOSIS rate is per 100,000. Recover denominators and aggregate.
    valid = group[(group["suicide_rate"] > 0) & group["suicide_deaths"].notna()]
    population = (valid["suicide_deaths"] / valid["suicide_rate"] * 100_000).sum()
    deaths = valid["suicide_deaths"].sum()
    if population <= 0:
        return np.nan
    return deaths / population * 100_000


def build_regional_concentration() -> tuple[pd.DataFrame, dict]:
    region = pd.read_csv(ARTIFACTS / "godoksa_region_year_2020_2024.csv")
    wide = (
        region.pivot(index="region", columns="year", values="count")
        .reset_index()
        .rename_axis(None, axis=1)
    )
    wide["change_2020_2024"] = wide[2024] - wide[2020]
    wide["pct_change_2020_2024"] = wide["change_2020_2024"] / wide[2020] * 100
    national_increase = int(wide["change_2020_2024"].sum())
    wide["share_of_national_increase_pct"] = (
        wide["change_2020_2024"] / national_increase * 100
    )
    wide["share_2024_pct"] = wide[2024] / wide[2024].sum() * 100
    wide["cumulative_increase_share_pct"] = (
        wide.sort_values("change_2020_2024", ascending=False)[
            "share_of_national_increase_pct"
        ].cumsum()
    )
    wide["core_growth_region"] = wide["region"].isin([SEOUL, GYEONGGI, DAEGU])
    wide["growth_type"] = np.select(
        [
            (wide[2024] >= 200) & (wide["pct_change_2020_2024"] >= 30),
            (wide[2024] < 250) & (wide["pct_change_2020_2024"] >= 70),
            wide["change_2020_2024"] < 0,
        ],
        ["large_and_fast", "small_base_fast_growth", "declining"],
        default="moderate",
    )
    wide = wide.sort_values("change_2020_2024", ascending=False)
    wide.to_csv(
        ARTIFACTS / "godoksa_regional_increase_concentration.csv",
        index=False,
        encoding="utf-8-sig",
    )

    seoul_gyeonggi = wide[wide["region"].isin([SEOUL, GYEONGGI])][
        "change_2020_2024"
    ].sum()
    core_three = wide[wide["region"].isin([SEOUL, GYEONGGI, DAEGU])][
        "change_2020_2024"
    ].sum()
    summary = {
        "national_increase": national_increase,
        "seoul_gyeonggi_increase": int(seoul_gyeonggi),
        "seoul_gyeonggi_share": seoul_gyeonggi / national_increase * 100,
        "core_three_increase": int(core_three),
        "core_three_share": core_three / national_increase * 100,
    }
    return wide, summary


def build_age_vulnerability() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    panel = pd.read_csv(WORKSPACE / "analysis_outputs_middle_male_mortality" / "merged_age_year_panel.csv")
    panel["age_start"] = panel["age_band"].map(age_start)

    age = (
        panel.groupby("age_band", as_index=False)
        .agg(
            suicide_rate=("suicide_rate", "mean"),
            suicide_deaths=("suicide_deaths", "mean"),
            depression_high_wm=("depression_high_wm", "mean"),
            low_income_wm=("low_income_wm", "mean"),
            problem_drinking_wm=("problem_drinking_wm", "mean"),
            self_esteem_low_wm=("self_esteem_low_wm", "mean"),
            AUDIT_wm=("AUDIT_wm", "mean"),
            SELF_ESTEEM_wm=("SELF_ESTEEM_wm", "mean"),
            age_start=("age_start", "first"),
        )
        .sort_values("age_start")
    )
    for col in [
        "depression_high_wm",
        "low_income_wm",
        "problem_drinking_wm",
        "self_esteem_low_wm",
    ]:
        age[f"{col}_z"] = zscore(age[col])
    age["psychosocial_vulnerability_zmean"] = age[
        [
            "depression_high_wm_z",
            "low_income_wm_z",
            "problem_drinking_wm_z",
            "self_esteem_low_wm_z",
        ]
    ].mean(axis=1)
    age["suicide_rate_z"] = zscore(age["suicide_rate"])
    age["mismatch_suicide_minus_psychosocial"] = (
        age["suicide_rate_z"] - age["psychosocial_vulnerability_zmean"]
    )
    age["paper_interpretation"] = np.select(
        [
            age["age_start"].eq(55),
            age["age_start"].eq(60),
            age["age_start"].isin([45, 50]),
        ],
        [
            "acute_mortality_excess",
            "latent_accumulated_vulnerability",
            "transition_and_drinking_risk",
        ],
        default="younger_middle_age_baseline",
    )
    age.drop(columns=["age_start"]).to_csv(
        ARTIFACTS / "middle_male_ageband_vulnerability_index.csv",
        index=False,
        encoding="utf-8-sig",
    )

    wide = panel.pivot(index="age_band", columns="survey_year", values=["suicide_rate", "suicide_deaths"])
    deterioration = pd.DataFrame(index=wide.index)
    deterioration["rate_change_2019_2024"] = wide[("suicide_rate", 2024)] - wide[("suicide_rate", 2019)]
    deterioration["death_change_2019_2024"] = wide[("suicide_deaths", 2024)] - wide[("suicide_deaths", 2019)]
    deterioration["rate_change_2022_2024"] = wide[("suicide_rate", 2024)] - wide[("suicide_rate", 2022)]
    deterioration["death_change_2022_2024"] = wide[("suicide_deaths", 2024)] - wide[("suicide_deaths", 2022)]
    deterioration["rate_2024"] = wide[("suicide_rate", 2024)]
    deterioration["deaths_2024"] = wide[("suicide_deaths", 2024)]
    deterioration = deterioration.reset_index()
    deterioration["age_start"] = deterioration["age_band"].map(age_start)
    deterioration = deterioration.sort_values("rate_change_2022_2024", ascending=False)
    deterioration["acceleration_rank_2022_2024"] = range(1, len(deterioration) + 1)
    deterioration.drop(columns=["age_start"]).to_csv(
        ARTIFACTS / "middle_male_suicide_2024_deterioration_by_age.csv",
        index=False,
        encoding="utf-8-sig",
    )

    panel.to_csv(
        ARTIFACTS / "middle_male_year_age_panel_enriched.csv",
        index=False,
        encoding="utf-8-sig",
    )
    return panel, age, deterioration


def build_age_bridge(panel: pd.DataFrame) -> pd.DataFrame:
    year = pd.read_csv(ARTIFACTS / "godoksa_year_summary_2020_2024.csv")
    g2024 = year[year["year"].eq(2024)].iloc[0]
    p2024 = panel[panel["survey_year"].eq(2024)].copy()
    p2024["age_start"] = p2024["age_band"].map(age_start)
    decade_map = {
        "40s": (40, 49, int(g2024["age_40s_count"])),
        "50s": (50, 59, int(g2024["age_50s_count"])),
        "60s": (60, 64, int(g2024["age_60s_count"])),
    }
    rows = []
    total_godoksa = int(g2024["total_godoksa"])
    total_suicide = p2024["suicide_deaths"].sum()
    for decade, (lo, hi, godoksa_count) in decade_map.items():
        group = p2024[p2024["age_start"].between(lo, hi)]
        rows.append(
            {
                "age_decade": decade,
                "godoksa_deaths_2024_allsex": godoksa_count,
                "share_of_total_godoksa_pct": godoksa_count / total_godoksa * 100,
                "male_suicide_deaths_2024": int(group["suicide_deaths"].sum()),
                "male_suicide_rate_aggregate_2024": aggregate_rate(group),
                "share_of_male_40_64_suicide_deaths_pct": group["suicide_deaths"].sum() / total_suicide * 100,
                "comparability_note": (
                    "godoksa all sex; suicide male only; 60s suicide covers 60-64 only"
                    if decade == "60s"
                    else "godoksa all sex; suicide male only"
                ),
            }
        )
    bridge = pd.DataFrame(rows)
    bridge.to_csv(
        ARTIFACTS / "godoksa_suicide_age_bridge_2024.csv",
        index=False,
        encoding="utf-8-sig",
    )
    return bridge


def build_priority_dataset(summary: dict, age: pd.DataFrame, deterioration: pd.DataFrame) -> pd.DataFrame:
    top_age_accel = deterioration.iloc[0]
    top_mismatch = age.sort_values("mismatch_suicide_minus_psychosocial", ascending=False).iloc[0]
    top_psych = age.sort_values("psychosocial_vulnerability_zmean", ascending=False).iloc[0]
    rows = [
        {
            "finding_id": "F1",
            "finding": "Spatial increase concentration",
            "core_number": f"{summary['core_three_share']:.1f}% of the 2020-2024 national increase is concentrated in Seoul, Gyeonggi, and Daegu.",
            "paper_use": "Turns godoksa from a general aging/isolation problem into an urban-regional concentration hypothesis.",
            "next_model": "province-year panel with single-person household, suicide, social-network, depression, welfare capacity variables",
        },
        {
            "finding_id": "F2",
            "finding": "Fastest recent suicide deterioration",
            "core_number": f"{top_age_accel['age_band']} male suicide rate rose {top_age_accel['rate_change_2022_2024']:.1f} per 100k from 2022 to 2024.",
            "paper_use": "Separates recent crisis acceleration from long-run vulnerability.",
            "next_model": "age-year crisis acceleration model",
        },
        {
            "finding_id": "F3",
            "finding": "Mortality-vulnerability mismatch",
            "core_number": f"{top_mismatch['age_band']} has the largest suicide-over-psychosocial mismatch; {top_psych['age_band']} has the largest accumulated psychosocial vulnerability.",
            "paper_use": "Argues that middle-aged men are not one homogeneous category.",
            "next_model": "two-outcome framework: suicide as acute expression, godoksa as accumulated isolation/discovery-delay expression",
        },
    ]
    findings = pd.DataFrame(rows)
    findings.to_csv(
        ARTIFACTS / "paper_ready_core_findings.csv",
        index=False,
        encoding="utf-8-sig",
    )
    return findings


def main() -> None:
    OUTPUTS.mkdir(exist_ok=True)
    ARTIFACTS.mkdir(exist_ok=True)
    regional, summary = build_regional_concentration()
    panel, age, deterioration = build_age_vulnerability()
    bridge = build_age_bridge(panel)
    findings = build_priority_dataset(summary, age, deterioration)

    memo = f"""# Deeper findings memo

This memo is generated from official godoksa summary tables, the local middle-male age-year suicide panel, and derived paper-ready indices.

## Core conclusion

The more novel claim is not that middle-aged men are vulnerable. The stronger claim is that the problem has two separable structures:

1. Godoksa growth is spatially concentrated.
2. Male midlife suicide risk is age-structured, not a single 40-64 pattern.
3. Suicide and godoksa should be modeled as related but different outcomes: acute crisis expression versus accumulated isolation and delayed discovery.

## Finding 1: regional concentration

National godoksa increased by {summary['national_increase']} cases from 2020 to 2024. Seoul and Gyeonggi account for {summary['seoul_gyeonggi_increase']} of those additional cases ({summary['seoul_gyeonggi_share']:.1f}%). Seoul, Gyeonggi, and Daegu together account for {summary['core_three_increase']} cases ({summary['core_three_share']:.1f}%).

Top increase regions:

{md_table(regional[['region', 2020, 2024, 'change_2020_2024', 'pct_change_2020_2024', 'share_of_national_increase_pct', 'share_2024_pct']].head(8))}

## Finding 2: middle-aged men are not one group

The age-band index shows a split between acute mortality excess and accumulated psychosocial vulnerability.

{md_table(age[['age_band', 'suicide_rate', 'depression_high_wm', 'low_income_wm', 'problem_drinking_wm', 'psychosocial_vulnerability_zmean', 'mismatch_suicide_minus_psychosocial', 'paper_interpretation']])}

## Finding 3: 2024 deterioration is strongest in the early 50s

From 2022 to 2024, the largest male suicide-rate acceleration is in {deterioration.iloc[0]['age_band']} (+{deterioration.iloc[0]['rate_change_2022_2024']:.1f} per 100,000).

{md_table(deterioration[['age_band', 'rate_change_2022_2024', 'death_change_2022_2024', 'rate_2024', 'deaths_2024', 'acceleration_rank_2022_2024']])}

## Finding 4: bridge table for the paper

{md_table(bridge)}

## Paper-ready framing

{md_table(findings)}
"""
    (OUTPUTS / "02_deeper_findings_memo.md").write_text(memo, encoding="utf-8")


if __name__ == "__main__":
    main()
