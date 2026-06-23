from pathlib import Path
import math

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts"
OUTPUTS = ROOT / "outputs"


def z(s):
    s = pd.to_numeric(s, errors="coerce")
    std = s.std(ddof=0)
    if std == 0 or pd.isna(std):
        return s * 0
    return (s - s.mean()) / std


def gini(values):
    x = np.array(values, dtype=float)
    if len(x) == 0 or np.all(x == 0):
        return np.nan
    x = np.sort(x)
    n = len(x)
    return float((2 * np.arange(1, n + 1) @ x) / (n * x.sum()) - (n + 1) / n)


def hhi(shares):
    s = np.array(shares, dtype=float)
    return float(np.sum(s ** 2))


def entropy(shares):
    s = np.array([v for v in shares if v > 0], dtype=float)
    return float(-np.sum(s * np.log(s)))


def age_start(label):
    return int(str(label).split("-")[0].strip())


def md_table(df, max_rows=20):
    d = df.head(max_rows).copy()
    for col in d.columns:
        if pd.api.types.is_float_dtype(d[col]):
            d[col] = d[col].map(lambda v: "" if pd.isna(v) else f"{v:.3f}")
    headers = [str(c) for c in d.columns]
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in d.to_numpy():
        lines.append("| " + " | ".join(str(v) for v in row) + " |")
    return "\n".join(lines)


def regional_decomposition():
    reg = pd.read_csv(ARTIFACTS / "godoksa_region_year_2020_2024.csv")
    wide = reg.pivot(index="region", columns="year", values="count").reset_index().rename_axis(None, axis=1)
    total_2020 = wide[2020].sum()
    total_2024 = wide[2024].sum()
    growth_factor = total_2024 / total_2020
    wide["expected_2024_if_national_growth"] = wide[2020] * growth_factor
    wide["excess_2024_vs_expected"] = wide[2024] - wide["expected_2024_if_national_growth"]
    wide["excess_share_of_total_excess_positive_pct"] = np.where(
        wide["excess_2024_vs_expected"] > 0,
        wide["excess_2024_vs_expected"] / wide.loc[wide["excess_2024_vs_expected"] > 0, "excess_2024_vs_expected"].sum() * 100,
        0,
    )
    wide["change_2020_2024"] = wide[2024] - wide[2020]
    wide["pct_change_2020_2024"] = wide["change_2020_2024"] / wide[2020] * 100
    wide["cagr_2020_2024_pct"] = ((wide[2024] / wide[2020]) ** (1 / 4) - 1) * 100
    years = [2020, 2021, 2022, 2023, 2024]
    slopes = []
    volatility = []
    recent_shock = []
    for _, row in wide.iterrows():
        y = row[years].to_numpy(dtype=float)
        x = np.arange(len(years))
        slopes.append(float(np.polyfit(x, y, 1)[0]))
        yoy = np.diff(y) / y[:-1]
        volatility.append(float(np.std(yoy, ddof=0)))
        recent_shock.append(float(y[-1] - y[-2]))
    wide["linear_slope_cases_per_year"] = slopes
    wide["yoy_volatility"] = volatility
    wide["recent_change_2023_2024"] = recent_shock
    national_increase = total_2024 - total_2020
    wide["share_of_national_increase_pct"] = wide["change_2020_2024"] / national_increase * 100
    conditions = [
        (wide["change_2020_2024"] < 0),
        (wide["excess_2024_vs_expected"] > 50) & (wide[2024] >= 500),
        (wide["excess_2024_vs_expected"] > 50) & (wide[2024] < 500),
        (wide["recent_change_2023_2024"] > 100),
        (wide["pct_change_2020_2024"] >= 70),
    ]
    labels = [
        "declining_or_reduced",
        "large_base_excess_growth",
        "small_base_excess_growth",
        "recent_spike",
        "fast_growth_from_small_base",
    ]
    wide["trajectory_type"] = np.select(conditions, labels, default="moderate_or_stable")
    wide = wide.sort_values("excess_2024_vs_expected", ascending=False)
    wide.to_csv(ARTIFACTS / "regional_expected_growth_decomposition.csv", index=False, encoding="utf-8-sig")

    concentration = []
    for year in years:
        counts = wide[year].to_numpy(dtype=float)
        shares = counts / counts.sum()
        ranked = np.sort(shares)[::-1]
        concentration.append(
            {
                "year": year,
                "total": int(counts.sum()),
                "gini_region_counts": gini(counts),
                "hhi_region_shares": hhi(shares),
                "effective_number_regions": 1 / hhi(shares),
                "entropy_region_shares": entropy(shares),
                "top1_share_pct": ranked[:1].sum() * 100,
                "top2_share_pct": ranked[:2].sum() * 100,
                "top3_share_pct": ranked[:3].sum() * 100,
                "top5_share_pct": ranked[:5].sum() * 100,
            }
        )
    conc = pd.DataFrame(concentration)
    conc.to_csv(ARTIFACTS / "spatial_concentration_indices_by_year.csv", index=False, encoding="utf-8-sig")
    return wide, conc


def age_mechanism():
    age = pd.read_csv(ARTIFACTS / "middle_male_ageband_vulnerability_index.csv")
    change = pd.read_csv(ARTIFACTS / "risk_flag_recent_change_2022_2024_by_age.csv")
    persistent = pd.read_csv(ARTIFACTS / "persistent_risk_2022_2024_by_age.csv").rename(columns={"age_band_2024": "age_band"})
    suicide = pd.read_csv(ARTIFACTS / "middle_male_suicide_2024_deterioration_by_age.csv")
    out = age.merge(change, on="age_band", how="left").merge(persistent, on="age_band", how="left").merge(suicide, on="age_band", how="left", suffixes=("", "_suicide"))
    observed_change_cols = [
        "depression_high_share_change_2022_2024",
        "self_esteem_low_share_change_2022_2024",
        "problem_drinking_share_change_2022_2024",
        "psych_any_share_change_2022_2024",
        "compound_psych_alcohol_share_change_2022_2024",
        "low_income_share_change_2022_2024",
    ]
    out["observed_risk_change_zmean"] = pd.concat([z(out[c]) for c in observed_change_cols], axis=1).mean(axis=1)
    out["suicide_acceleration_z"] = z(out["rate_change_2022_2024"])
    out["hidden_acute_crisis_index"] = out["suicide_acceleration_z"] - out["observed_risk_change_zmean"]
    accumulation_cols = [
        "persistent_depression_high_share",
        "persistent_psych_any_share",
        "persistent_low_income_share",
        "persistent_problem_drinking_share",
        "persistent_compound_psych_alcohol_share",
        "persistent_triple_psych_alcohol_low_income_share",
    ]
    out["persistent_accumulation_zmean"] = pd.concat([z(out[c]) for c in accumulation_cols], axis=1).mean(axis=1)
    out["new_risk_entry_zmean"] = pd.concat([
        z(out["new_depression_high_share"]),
        z(out["new_psych_any_share"]),
        z(out["new_problem_drinking_share"]),
        z(out["new_low_income_share"]),
    ], axis=1).mean(axis=1)
    types = []
    for _, r in out.iterrows():
        if r["hidden_acute_crisis_index"] >= out["hidden_acute_crisis_index"].quantile(0.75):
            types.append("hidden_acute_crisis")
        elif r["persistent_accumulation_zmean"] >= out["persistent_accumulation_zmean"].quantile(0.75):
            types.append("persistent_accumulation")
        elif r["mismatch_suicide_minus_psychosocial"] >= 0.5:
            types.append("mortality_excess")
        elif r["new_risk_entry_zmean"] >= out["new_risk_entry_zmean"].quantile(0.75):
            types.append("new_risk_entry")
        else:
            types.append("baseline_or_mixed")
    out["refined_mechanism_type"] = types
    keep = [
        "age_band",
        "rate_change_2022_2024",
        "suicide_rate",
        "psychosocial_vulnerability_zmean",
        "mismatch_suicide_minus_psychosocial",
        "observed_risk_change_zmean",
        "suicide_acceleration_z",
        "hidden_acute_crisis_index",
        "persistent_accumulation_zmean",
        "new_risk_entry_zmean",
        "refined_mechanism_type",
    ] + observed_change_cols + accumulation_cols
    out = out.sort_values("age_band", key=lambda s: s.map(age_start))
    out[keep].to_csv(ARTIFACTS / "age_mechanism_refined_indices.csv", index=False, encoding="utf-8-sig")
    return out[keep]


def build_hypothesis_matrix(regional, age_mech):
    rows = []
    top_excess = regional.head(5)
    rows.append({
        "hypothesis_id": "H1",
        "claim": "Godoksa growth is spatially concentrated beyond proportional national growth.",
        "evidence_now": "; ".join(f"{r.region}: excess {r.excess_2024_vs_expected:.1f}" for r in top_excess.itertuples()),
        "next_variable_needed": "male 40-64 one-person households by region/year; social-network absence; regional depression; welfare capacity",
        "model_target": "province-year godoksa count/rate panel",
    })
    hidden = age_mech.sort_values("hidden_acute_crisis_index", ascending=False).iloc[0]
    accum = age_mech.sort_values("persistent_accumulation_zmean", ascending=False).iloc[0]
    rows.append({
        "hypothesis_id": "H2",
        "claim": "Recent suicide acceleration among middle-aged men is not fully captured by standard survey risk indicators.",
        "evidence_now": f"{hidden.age_band}: rate +{hidden.rate_change_2022_2024:.1f}/100k, hidden acute crisis index {hidden.hidden_acute_crisis_index:.2f}",
        "next_variable_needed": "job loss, business closure, debt/arrears, health-shock, divorce/separation, emergency self-harm data",
        "model_target": "age-year suicide acceleration model",
    })
    rows.append({
        "hypothesis_id": "H3",
        "claim": "Early old-middle age shows accumulated vulnerability better suited to godoksa/discovery-delay interpretation than acute suicide alone.",
        "evidence_now": f"{accum.age_band}: persistent accumulation index {accum.persistent_accumulation_zmean:.2f}",
        "next_variable_needed": "alone-living duration, contact frequency, illness/disability, welfare contact, death discovery interval",
        "model_target": "two-outcome framework: suicide vs godoksa",
    })
    out = pd.DataFrame(rows)
    out.to_csv(ARTIFACTS / "refined_hypothesis_matrix.csv", index=False, encoding="utf-8-sig")
    return out


def main():
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    regional, conc = regional_decomposition()
    age_mech = age_mechanism()
    hyp = build_hypothesis_matrix(regional, age_mech)

    memo = f"""# Refined analysis memo

## 1. Regional decomposition: observed growth versus expected growth

If every region had grown at the national 2020-2024 godoksa growth rate, the expected 2024 count can be computed from each region's 2020 baseline. The residual identifies excess growth beyond simple proportional expansion.

{md_table(regional[['region', 2020, 2024, 'expected_2024_if_national_growth', 'excess_2024_vs_expected', 'pct_change_2020_2024', 'share_of_national_increase_pct', 'trajectory_type']].head(12))}

## 2. Spatial concentration indices

{md_table(conc)}

## 3. Refined age mechanism index

Hidden acute crisis index = standardized 2022-2024 suicide-rate acceleration minus standardized observed survey-risk change. A high value means mortality accelerated more than standard survey indicators would predict.

{md_table(age_mech[['age_band', 'rate_change_2022_2024', 'observed_risk_change_zmean', 'hidden_acute_crisis_index', 'persistent_accumulation_zmean', 'new_risk_entry_zmean', 'refined_mechanism_type']])}

## 4. Hypothesis matrix

{md_table(hyp)}
"""
    (OUTPUTS / "05_refined_analysis_memo.md").write_text(memo, encoding="utf-8")
    print("done")
    print(regional[['region', 2020, 2024, 'expected_2024_if_national_growth', 'excess_2024_vs_expected', 'trajectory_type']].head(10).to_string(index=False))
    print(age_mech[['age_band', 'rate_change_2022_2024', 'observed_risk_change_zmean', 'hidden_acute_crisis_index', 'persistent_accumulation_zmean', 'refined_mechanism_type']].to_string(index=False))


if __name__ == "__main__":
    main()
