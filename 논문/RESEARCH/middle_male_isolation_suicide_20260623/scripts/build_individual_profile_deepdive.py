from pathlib import Path
import math
import re

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parents[1]
ARTIFACTS = ROOT / "artifacts"
OUTPUTS = ROOT / "outputs"
LOW_INCOME_TOKEN = "1\uad6c\uac04"


def find_bigdata() -> Path:
    candidates = list(Path.home().joinpath("OneDrive").rglob("*Bigdata*middle*male*.csv"))
    if not candidates:
        candidates = list(Path.home().joinpath("OneDrive").rglob("*Bigdata*.csv"))
    if not candidates:
        raise FileNotFoundError("Could not find Bigdata_middle_male.csv under OneDrive")
    return max(candidates, key=lambda p: p.stat().st_size)


def age_band(age):
    if pd.isna(age):
        return np.nan
    age = int(age)
    for lo, hi in [(40, 44), (45, 49), (50, 54), (55, 59), (60, 64)]:
        if lo <= age <= hi:
            return f"{lo} - {hi}\uc138"
    return np.nan


def age_start(label):
    m = re.search(r"\d+", str(label))
    return int(m.group(0)) if m else np.nan


def weighted_mean(x, w):
    x = pd.to_numeric(x, errors="coerce")
    w = pd.to_numeric(w, errors="coerce")
    mask = x.notna() & w.notna() & (w > 0)
    if mask.sum() == 0:
        return np.nan
    return float(np.average(x[mask], weights=w[mask]))


def weighted_sum(mask, w):
    m = mask.fillna(False).astype(bool)
    return float(w[m].sum())


def corr(x, y):
    d = pd.DataFrame({"x": x, "y": y}).dropna()
    if len(d) < 4 or d["x"].nunique() < 2 or d["y"].nunique() < 2:
        return np.nan, len(d)
    return float(np.corrcoef(d["x"], d["y"])[0, 1]), len(d)


def spearman(x, y):
    d = pd.DataFrame({"x": x, "y": y}).dropna()
    if len(d) < 4 or d["x"].nunique() < 2 or d["y"].nunique() < 2:
        return np.nan
    return float(np.corrcoef(d["x"].rank(), d["y"].rank())[0, 1])


def permutation_p(x, y, n_perm=5000, seed=7):
    d = pd.DataFrame({"x": x, "y": y}).dropna()
    if len(d) < 4 or d["x"].nunique() < 2 or d["y"].nunique() < 2:
        return np.nan
    rng = np.random.default_rng(seed)
    xv = d["x"].to_numpy(float)
    yv = d["y"].to_numpy(float)
    obs = abs(np.corrcoef(xv, yv)[0, 1])
    hits = 0
    for _ in range(n_perm):
        if abs(np.corrcoef(xv, rng.permutation(yv))[0, 1]) >= obs:
            hits += 1
    return float((hits + 1) / (n_perm + 1))


def add_flags(df):
    df = df.copy()
    df["age_band"] = df["age"].map(age_band)
    df = df[df["age_band"].notna()].copy()
    df["w"] = df["wgt_n"].fillna(df["combined_wgt"]).fillna(df["raw_wgt"])
    df["low_income"] = df["income_group"].astype(str).str.contains(LOW_INCOME_TOKEN, regex=False).astype(float)
    df["depression_high"] = np.where(df["CES_D"].notna(), (df["CES_D"] >= 16).astype(float), np.nan)
    df["self_esteem_low"] = np.where(df["SELF_ESTEEM"].notna(), (df["SELF_ESTEEM"] <= 28).astype(float), np.nan)
    df["problem_drinking"] = np.where(df["AUDIT"].notna(), (df["AUDIT"] >= 8).astype(float), np.nan)
    df["high_risk_drinking"] = np.where(df["AUDIT"].notna(), (df["AUDIT"] >= 15).astype(float), np.nan)
    df["psych_any"] = ((df["depression_high"].fillna(0) == 1) | (df["self_esteem_low"].fillna(0) == 1)).astype(float)
    df["compound_psych_alcohol"] = ((df["psych_any"] == 1) & (df["problem_drinking"].fillna(0) == 1)).astype(float)
    df["compound_psych_low_income"] = ((df["psych_any"] == 1) & (df["low_income"].fillna(0) == 1)).astype(float)
    df["triple_psych_alcohol_low_income"] = ((df["psych_any"] == 1) & (df["problem_drinking"].fillna(0) == 1) & (df["low_income"].fillna(0) == 1)).astype(float)
    df["profile"] = df.apply(classify_profile, axis=1)
    return df


def classify_profile(row):
    psych = row.get("psych_any", 0) == 1
    drink = row.get("problem_drinking", 0) == 1
    low = row.get("low_income", 0) == 1
    dep = row.get("depression_high", 0) == 1
    low_self = row.get("self_esteem_low", 0) == 1
    if psych and drink and low:
        return "compound_psych_alcohol_low_income"
    if dep and drink:
        return "depression_alcohol"
    if psych and low:
        return "psych_low_income"
    if low_self and drink:
        return "low_self_esteem_alcohol"
    if psych:
        return "psych_only"
    if drink:
        return "alcohol_only"
    if low:
        return "low_income_only"
    return "lower_observed_risk"


def flag_panel(df):
    flags = [
        "depression_high",
        "self_esteem_low",
        "problem_drinking",
        "high_risk_drinking",
        "low_income",
        "psych_any",
        "compound_psych_alcohol",
        "compound_psych_low_income",
        "triple_psych_alcohol_low_income",
    ]
    rows = []
    for (year, band), g in df.groupby(["survey_year", "age_band"]):
        w = g["w"]
        out = {"survey_year": year, "age_band": band, "n": len(g), "weight_sum": w.sum()}
        for flag in flags:
            out[f"{flag}_share"] = weighted_mean(g[flag], w)
        out["CES_D_mean"] = weighted_mean(g["CES_D"], w)
        out["SELF_ESTEEM_mean"] = weighted_mean(g["SELF_ESTEEM"], w)
        out["AUDIT_mean"] = weighted_mean(g["AUDIT"], w)
        out["income_mean"] = weighted_mean(g["h_din"], w)
        rows.append(out)
    out = pd.DataFrame(rows).sort_values(["survey_year", "age_band"])
    out.to_csv(ARTIFACTS / "individual_risk_flag_panel_by_age_year.csv", index=False, encoding="utf-8-sig")
    return out


def profile_shares(df):
    rows = []
    for (year, band), g in df.groupby(["survey_year", "age_band"]):
        w = g["w"]
        total = w.sum()
        for profile, gp in g.groupby("profile"):
            rows.append(
                {
                    "survey_year": year,
                    "age_band": band,
                    "profile": profile,
                    "n": len(gp),
                    "weighted_share": gp["w"].sum() / total if total > 0 else np.nan,
                }
            )
    long = pd.DataFrame(rows)
    long.to_csv(ARTIFACTS / "individual_profile_share_by_age_year_long.csv", index=False, encoding="utf-8-sig")
    wide = long.pivot_table(index=["survey_year", "age_band"], columns="profile", values="weighted_share", fill_value=0).reset_index()
    wide.to_csv(ARTIFACTS / "individual_profile_share_by_age_year_wide.csv", index=False, encoding="utf-8-sig")
    return long, wide


def overall_profiles(df):
    rows = []
    for band, g in df.groupby("age_band"):
        w = g["w"]
        total = w.sum()
        for profile, gp in g.groupby("profile"):
            rows.append({"age_band": band, "profile": profile, "weighted_share": gp["w"].sum() / total, "n": len(gp)})
    out = pd.DataFrame(rows)
    out["age_start"] = out["age_band"].map(age_start)
    out = out.sort_values(["age_start", "weighted_share"], ascending=[True, False]).drop(columns="age_start")
    out.to_csv(ARTIFACTS / "individual_profile_share_by_age_overall.csv", index=False, encoding="utf-8-sig")
    return out


def merge_with_suicide(flag_df, profile_wide):
    suicide = pd.read_csv(WORKSPACE / "analysis_outputs_middle_male_mortality" / "merged_age_year_panel.csv")
    keep = ["survey_year", "age_band", "suicide_deaths", "suicide_rate"]
    merged_flags = flag_df.merge(suicide[keep], on=["survey_year", "age_band"], how="left")
    merged_profiles = profile_wide.merge(suicide[keep], on=["survey_year", "age_band"], how="left")
    merged_flags.to_csv(ARTIFACTS / "individual_risk_flag_suicide_panel.csv", index=False, encoding="utf-8-sig")
    merged_profiles.to_csv(ARTIFACTS / "individual_profile_suicide_panel.csv", index=False, encoding="utf-8-sig")
    return merged_flags, merged_profiles


def correlations(merged_flags, merged_profiles):
    rows = []
    vars_flags = [c for c in merged_flags.columns if c.endswith("_share") or c in ["CES_D_mean", "SELF_ESTEEM_mean", "AUDIT_mean", "income_mean"]]
    for var in vars_flags:
        r, n = corr(merged_flags[var], merged_flags["suicide_rate"])
        rows.append({"type": "flag_or_mean", "variable": var, "pearson_r": r, "spearman_r": spearman(merged_flags[var], merged_flags["suicide_rate"]), "permutation_p": permutation_p(merged_flags[var], merged_flags["suicide_rate"]), "n_cells": n})
    profile_vars = [c for c in merged_profiles.columns if c not in ["survey_year", "age_band", "suicide_deaths", "suicide_rate"]]
    for var in profile_vars:
        r, n = corr(merged_profiles[var], merged_profiles["suicide_rate"])
        rows.append({"type": "profile_share", "variable": var, "pearson_r": r, "spearman_r": spearman(merged_profiles[var], merged_profiles["suicide_rate"]), "permutation_p": permutation_p(merged_profiles[var], merged_profiles["suicide_rate"]), "n_cells": n})
    out = pd.DataFrame(rows).sort_values("pearson_r", key=lambda s: s.abs(), ascending=False)
    out.to_csv(ARTIFACTS / "individual_profile_suicide_correlations.csv", index=False, encoding="utf-8-sig")
    return out


def recent_change(flag_panel_df, profile_wide):
    suicide = pd.read_csv(ARTIFACTS / "middle_male_suicide_2024_deterioration_by_age.csv")
    rows = []
    for band in sorted(flag_panel_df["age_band"].unique(), key=age_start):
        a = flag_panel_df[(flag_panel_df["age_band"] == band) & (flag_panel_df["survey_year"] == 2022)]
        b = flag_panel_df[(flag_panel_df["age_band"] == band) & (flag_panel_df["survey_year"] == 2024)]
        if a.empty or b.empty:
            continue
        out = {"age_band": band}
        for col in [c for c in flag_panel_df.columns if c.endswith("_share")]:
            out[f"{col}_change_2022_2024"] = float(b.iloc[0][col] - a.iloc[0][col])
        srow = suicide[suicide["age_band"] == band]
        if not srow.empty:
            out["suicide_rate_change_2022_2024"] = float(srow.iloc[0]["rate_change_2022_2024"])
            out["suicide_death_change_2022_2024"] = float(srow.iloc[0]["death_change_2022_2024"])
        rows.append(out)
    out = pd.DataFrame(rows)
    out.to_csv(ARTIFACTS / "risk_flag_recent_change_2022_2024_by_age.csv", index=False, encoding="utf-8-sig")
    return out


def transitions_2022_2024(df):
    d = df[df["survey_year"].isin([2022, 2024])].copy()
    pivot = d.pivot_table(index="h_pid", columns="survey_year", values="profile", aggfunc="first")
    pivot_age = d[d["survey_year"] == 2024].set_index("h_pid")[["age_band", "w"]]
    trans = pivot.join(pivot_age).dropna(subset=[2022, 2024])
    trans = trans.rename(columns={2022: "profile_2022", 2024: "profile_2024"})
    rows = []
    for band_key, g in [("all", trans)] + list(trans.groupby("age_band")):
        total = g["w"].sum()
        for (p0, p1), gp in g.groupby(["profile_2022", "profile_2024"]):
            rows.append({"age_band_2024": band_key, "profile_2022": p0, "profile_2024": p1, "n": len(gp), "weighted_share": gp["w"].sum() / total if total > 0 else np.nan})
    out = pd.DataFrame(rows).sort_values(["age_band_2024", "weighted_share"], ascending=[True, False])
    out.to_csv(ARTIFACTS / "profile_transition_2022_2024.csv", index=False, encoding="utf-8-sig")

    flags = ["depression_high", "problem_drinking", "psych_any", "low_income", "compound_psych_alcohol", "triple_psych_alcohol_low_income"]
    wide = d.pivot_table(index="h_pid", columns="survey_year", values=flags, aggfunc="first")
    # Flatten columns: flag_year.
    wide.columns = [f"{flag}_{year}" for flag, year in wide.columns]
    flag_trans = wide.join(pivot_age).dropna(subset=["age_band"])
    rows2 = []
    for band, g in flag_trans.groupby("age_band"):
        w = g["w"]
        row = {"age_band_2024": band, "n_linked": len(g), "weight_sum": w.sum()}
        for flag in flags:
            c2022 = f"{flag}_2022"
            c2024 = f"{flag}_2024"
            if c2022 not in g or c2024 not in g:
                continue
            old = g[c2022].fillna(0) == 1
            new = g[c2024].fillna(0) == 1
            row[f"persistent_{flag}_share"] = weighted_sum(old & new, w) / w.sum()
            row[f"new_{flag}_share"] = weighted_sum((~old) & new, w) / w.sum()
            row[f"remitted_{flag}_share"] = weighted_sum(old & (~new), w) / w.sum()
        rows2.append(row)
    out2 = pd.DataFrame(rows2).sort_values("age_band_2024", key=lambda s: s.map(age_start))
    out2.to_csv(ARTIFACTS / "persistent_risk_2022_2024_by_age.csv", index=False, encoding="utf-8-sig")
    return out, out2


def md_table(df, max_rows=12):
    d = df.head(max_rows).copy()
    for col in d.columns:
        if pd.api.types.is_float_dtype(d[col]):
            d[col] = d[col].map(lambda v: "" if pd.isna(v) else f"{v:.3f}")
    headers = [str(c) for c in d.columns]
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in d.to_numpy():
        lines.append("| " + " | ".join(str(v) for v in row) + " |")
    return "\n".join(lines)


def main():
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    big_path = find_bigdata()
    raw = pd.read_csv(big_path, encoding="utf-8-sig")
    df = add_flags(raw)
    flag_df = flag_panel(df)
    profile_long, profile_wide = profile_shares(df)
    overall = overall_profiles(df)
    merged_flags, merged_profiles = merge_with_suicide(flag_df, profile_wide)
    corr_df = correlations(merged_flags, merged_profiles)
    change = recent_change(flag_df, profile_wide)
    transition, persistent = transitions_2022_2024(df)

    top_corr = corr_df.head(12)
    top_overall = overall.sort_values("weighted_share", ascending=False).head(12)
    top_change_cols = ["age_band", "suicide_rate_change_2022_2024", "depression_high_share_change_2022_2024", "problem_drinking_share_change_2022_2024", "psych_any_share_change_2022_2024", "compound_psych_alcohol_share_change_2022_2024", "triple_psych_alcohol_low_income_share_change_2022_2024"]
    memo = f"""# Individual profile deep dive

Source person-year data: {big_path}
Rows used after age filtering: {len(df):,}; persons: {df['h_pid'].nunique():,}; years: {int(df['survey_year'].min())}-{int(df['survey_year'].max())}.

## Top profile shares by age, pooled years

{md_table(top_overall)}

## Correlations between profile/flag shares and male suicide rate

{md_table(top_corr[['type','variable','pearson_r','spearman_r','permutation_p','n_cells']])}

## 2022-2024 risk-share changes by age band

{md_table(change[top_change_cols], max_rows=10)}

## 2022-2024 persistence/new-entry risk by 2024 age band

{md_table(persistent, max_rows=10)}

## Most common profile transitions, 2022 to 2024

{md_table(transition[transition['age_band_2024'].eq('all')][['profile_2022','profile_2024','n','weighted_share']], max_rows=15)}
"""
    (OUTPUTS / "03_individual_profile_deepdive.md").write_text(memo, encoding="utf-8")
    print("done", ROOT)
    print("rows", len(df), "persons", df["h_pid"].nunique())
    print(top_corr[["type", "variable", "pearson_r", "spearman_r", "permutation_p", "n_cells"]].head(10).to_string(index=False))
    print(change[top_change_cols].to_string(index=False))
    print(persistent.to_string(index=False))


if __name__ == "__main__":
    main()
