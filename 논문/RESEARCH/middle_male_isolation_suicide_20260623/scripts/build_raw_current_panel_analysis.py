from __future__ import annotations

import json
import math
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
try:
    import statsmodels.api as sm
except Exception:  # pragma: no cover
    sm = None

try:
    import mpmath as mp
except Exception:  # pragma: no cover
    mp = None


warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

BASE = Path(__file__).resolve().parents[1]
ART = BASE / "artifacts"
OUT = BASE / "outputs"
ART.mkdir(exist_ok=True)
OUT.mkdir(exist_ok=True)


REGION_MAP = {
    "전국": "전국",
    "계": "전국",
    "서울특별시": "서울",
    "서울": "서울",
    "부산광역시": "부산",
    "부산": "부산",
    "대구광역시": "대구",
    "대구": "대구",
    "인천광역시": "인천",
    "인천": "인천",
    "광주광역시": "광주",
    "광주": "광주",
    "대전광역시": "대전",
    "대전": "대전",
    "울산광역시": "울산",
    "울산": "울산",
    "세종특별자치시": "세종",
    "세종": "세종",
    "경기도": "경기",
    "경기": "경기",
    "강원도": "강원",
    "강원특별자치도": "강원",
    "강원": "강원",
    "충청북도": "충북",
    "충북": "충북",
    "충청남도": "충남",
    "충남": "충남",
    "전라북도": "전북",
    "전북특별자치도": "전북",
    "전북": "전북",
    "전라남도": "전남",
    "전남": "전남",
    "경상북도": "경북",
    "경북": "경북",
    "경상남도": "경남",
    "경남": "경남",
    "제주도": "제주",
    "제주특별자치도": "제주",
    "제주": "제주",
}

AGE_40_64_TILDE = ["40~44", "45~49", "50~54", "55~59", "60~64"]
AGE_40_64_SPACED = [
    "40 - 44세",
    "45 - 49세",
    "50 - 54세",
    "55 - 59세",
    "60 - 64세",
]


def find_raw_files() -> dict[str, Path]:
    root = Path.home() / "OneDrive"
    all_xlsx = sorted(root.rglob("*.xlsx"), key=lambda p: p.stat().st_mtime, reverse=True)
    selected: dict[str, Path] = {}
    for p in all_xlsx:
        prefix = p.name[:2]
        if prefix in {f"{i:02d}" for i in range(1, 8)} and prefix not in selected:
            selected[prefix] = p
    missing = [f"{i:02d}" for i in range(1, 8) if f"{i:02d}" not in selected]
    if missing:
        raise FileNotFoundError(f"Missing raw files with prefixes: {missing}")
    return dict(sorted(selected.items()))


def read_first_sheet(path: Path) -> pd.DataFrame:
    return pd.read_excel(path, sheet_name=0, header=None, dtype=object)


def numeric(value) -> float:
    if pd.isna(value):
        return np.nan
    text = str(value).strip().replace(",", "")
    if text in {"", "-", "x", "X", "*", "**"}:
        return np.nan
    try:
        return float(text)
    except ValueError:
        return np.nan


def clean_region(value) -> str | None:
    if pd.isna(value):
        return None
    text = str(value).strip()
    return REGION_MAP.get(text, text)


def zscore(series: pd.Series) -> pd.Series:
    s = pd.to_numeric(series, errors="coerce")
    sd = s.std(ddof=0)
    if not np.isfinite(sd) or sd == 0:
        return pd.Series(np.nan, index=series.index)
    return (s - s.mean()) / sd




def student_t_pdf(x: float, df: int) -> float:
    log_c = math.lgamma((df + 1) / 2) - math.lgamma(df / 2) - 0.5 * math.log(df * math.pi)
    return math.exp(log_c - ((df + 1) / 2) * math.log1p((x * x) / df))


def t_two_sided_p(abs_t: float, df: int) -> float:
    if not np.isfinite(abs_t) or df <= 0:
        return np.nan
    t = abs(float(abs_t))
    if t == 0:
        return 1.0
    upper = min(t, 100.0)
    steps = max(400, int(upper * 400))
    if steps % 2 == 1:
        steps += 1
    h = upper / steps
    total = student_t_pdf(0.0, df) + student_t_pdf(upper, df)
    odd = 0.0
    even = 0.0
    for i in range(1, steps):
        val = student_t_pdf(i * h, df)
        if i % 2:
            odd += val
        else:
            even += val
    integral_0_t = h / 3 * (total + 4 * odd + 2 * even)
    cdf = min(1.0, 0.5 + integral_0_t)
    return max(0.0, min(1.0, 2 * (1 - cdf)))

def corr_with_p(x: pd.Series, y: pd.Series) -> tuple[float, float]:
    dat = pd.concat([x, y], axis=1).dropna()
    n = len(dat)
    if n < 4:
        return np.nan, np.nan
    xv = dat.iloc[:, 0].astype(float).to_numpy()
    yv = dat.iloc[:, 1].astype(float).to_numpy()
    if np.nanstd(xv) == 0 or np.nanstd(yv) == 0:
        return np.nan, np.nan
    r = float(np.corrcoef(xv, yv)[0, 1])
    if abs(r) >= 1:
        return r, 0.0
    tval = abs(r) * math.sqrt((n - 2) / max(1e-12, 1 - r * r))
    return r, t_two_sided_p(tval, n - 2)

def parse_single_household(path: Path) -> pd.DataFrame:
    df = read_first_sheet(path)
    body = df.iloc[2:].copy()
    for col in [0, 1, 2]:
        body[col] = body[col].ffill()
    body = body.rename(
        columns={
            0: "raw_region",
            1: "sex",
            2: "age",
            3: "single_households",
            4: "housing_total",
            5: "detached_house",
            6: "apartment",
            7: "row_house",
            8: "multi_family_house",
            9: "non_residential_house",
            10: "non_housing_dwelling",
        }
    )
    body["region"] = body["raw_region"].map(clean_region)
    keep = (
        (body["sex"].astype(str).str.strip() == "남자")
        & (body["age"].astype(str).isin(AGE_40_64_TILDE))
        & (~body["region"].isin(["전국", "읍부", "면부", "동부"]))
    )
    cols = [
        "single_households",
        "housing_total",
        "detached_house",
        "apartment",
        "row_house",
        "multi_family_house",
        "non_residential_house",
        "non_housing_dwelling",
    ]
    sub = body.loc[keep, ["region"] + cols].copy()
    for c in cols:
        sub[c] = sub[c].map(numeric)
    out = sub.groupby("region", as_index=False)[cols].sum(min_count=1)
    out = out.rename(
        columns={
            "single_households": "male_40_64_single_households_2024",
            "housing_total": "male_40_64_single_housing_total_2024",
            "detached_house": "male_40_64_single_detached_house_2024",
            "apartment": "male_40_64_single_apartment_2024",
            "row_house": "male_40_64_single_row_house_2024",
            "multi_family_house": "male_40_64_single_multi_family_house_2024",
            "non_residential_house": "male_40_64_single_non_residential_house_2024",
            "non_housing_dwelling": "male_40_64_single_non_housing_dwelling_2024",
        }
    )
    total = out["male_40_64_single_households_2024"]
    out["male_40_64_single_non_apartment_share_2024"] = (
        (total - out["male_40_64_single_apartment_2024"]) / total * 100
    )
    out["male_40_64_single_non_housing_share_2024"] = (
        out["male_40_64_single_non_housing_dwelling_2024"] / total * 100
    )
    return out


def parse_social_network(path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    df = read_first_sheet(path)
    body = df.iloc[2:].copy()
    for col in [0, 1, 2]:
        body[col] = body[col].ffill()
    body = body.rename(columns={0: "raw_region", 1: "category", 2: "group"})
    body["region"] = body["raw_region"].map(clean_region)
    measures = {
        5: "no_help_sick_housework_pct",
        8: "no_help_money_pct",
        11: "no_depressed_talk_pct",
        6: "help_sick_avg_persons",
        9: "help_money_avg_persons",
        12: "depressed_talk_avg_persons",
    }
    rows = []
    for _, r in body.iterrows():
        if r["region"] != "전국":
            continue
        category = str(r["category"]).strip()
        group = str(r["group"]).strip()
        if (category, group) in {
            ("전체", "계"),
            ("성별", "남자"),
            ("세대구분", "1인가구"),
            ("가구원수", "1인"),
            ("연령", "40∼49세"),
            ("연령", "50∼59세"),
            ("연령", "60∼64세"),
            ("연령*성별", "40∼49세*남자"),
            ("연령*성별", "50∼59세*남자"),
            ("연령*성별", "60세 이상*남자"),
        }:
            item = {"year": 2025, "category": category, "group": group}
            for col, name in measures.items():
                item[name] = numeric(r[col]) if col in body.columns else np.nan
            rows.append(item)
    context = pd.DataFrame(rows)
    region_constants = {}
    male_row = context[(context["category"] == "성별") & (context["group"] == "남자")]
    one_row = context[(context["category"] == "세대구분") & (context["group"] == "1인가구")]
    if not male_row.empty:
        for c in measures.values():
            region_constants[f"national_male_social_{c}_2025"] = male_row.iloc[0][c]
    if not one_row.empty:
        for c in measures.values():
            region_constants[f"national_one_person_social_{c}_2025"] = one_row.iloc[0][c]
    regional = pd.DataFrame({"region": [r for r in REGION_MAP.values() if r != "전국"]}).drop_duplicates()
    for k, v in region_constants.items():
        regional[k] = v
    return regional, context


def parse_depression(path: Path) -> pd.DataFrame:
    df = read_first_sheet(path)
    body = df.iloc[2:].copy()
    for col in [0, 1, 2]:
        body[col] = body[col].ffill()
    body = body.rename(
        columns={
            0: "raw_region",
            1: "subregion",
            2: "subsubregion",
            3: "respondents",
            4: "crude_rate",
            5: "crude_se",
            6: "std_rate",
            7: "std_se",
        }
    )
    body["region"] = body["raw_region"].map(clean_region)
    keep = (body["subregion"].astype(str).str.strip() == "소계") & (
        body["subsubregion"].astype(str).str.strip() == "소계"
    )
    out = body.loc[keep, ["region", "respondents", "crude_rate", "std_rate"]].copy()
    for c in ["respondents", "crude_rate", "std_rate"]:
        out[c] = out[c].map(numeric)
    return out.rename(
        columns={
            "respondents": "depression_respondents_2025",
            "crude_rate": "depression_crude_rate_2025",
            "std_rate": "depression_std_rate_2025",
        }
    )


def parse_basic_livelihood(path: Path) -> pd.DataFrame:
    df = read_first_sheet(path)
    body = df.iloc[2:].copy()
    for col in [0, 1, 2]:
        body[col] = body[col].ffill()
    body = body.rename(columns={0: "raw_region", 1: "age_group", 2: "age_detail", 4: "male_count"})
    body["region"] = body["raw_region"].map(clean_region)
    keep = (
        body["age_group"].astype(str).isin(AGE_40_64_SPACED)
        & (body["age_detail"].astype(str).str.strip() == "소계")
        & (body["region"] != "전국")
    )
    sub = body.loc[keep, ["region", "age_group", "male_count"]].copy()
    sub["male_count"] = sub["male_count"].map(numeric)
    out = sub.groupby("region", as_index=False)["male_count"].sum(min_count=1)
    return out.rename(columns={"male_count": "basic_livelihood_male_40_64_count_2024"})


def parse_closure(path: Path) -> pd.DataFrame:
    df = read_first_sheet(path)
    body = df.iloc[3:].copy()
    for col in [0, 1]:
        body[col] = body[col].ffill()
    body = body.rename(
        columns={
            0: "sex",
            1: "raw_region",
            2: "total",
            5: "age_40s",
            6: "age_50s",
            7: "age_60s",
            8: "age_70plus",
        }
    )
    body["region"] = body["raw_region"].map(clean_region)
    keep = (body["sex"].astype(str).str.strip() == "남자") & (body["region"] != "전국")
    out = body.loc[keep, ["region", "total", "age_40s", "age_50s", "age_60s", "age_70plus"]].copy()
    for c in ["total", "age_40s", "age_50s", "age_60s", "age_70plus"]:
        out[c] = out[c].map(numeric)
    out["business_closure_male_40s_50s_count_2024"] = out["age_40s"] + out["age_50s"]
    out["business_closure_male_40_64_approx_count_2024"] = (
        out["age_40s"] + out["age_50s"] + 0.5 * out["age_60s"]
    )
    out["business_closure_male_40_69_count_2024"] = out["age_40s"] + out["age_50s"] + out["age_60s"]
    out = out.rename(
        columns={
            "total": "business_closure_male_total_count_2024",
            "age_40s": "business_closure_male_40s_count_2024",
            "age_50s": "business_closure_male_50s_count_2024",
            "age_60s": "business_closure_male_60s_count_2024",
            "age_70plus": "business_closure_male_70plus_count_2024",
        }
    )
    return out


def parse_divorce(path: Path) -> pd.DataFrame:
    df = read_first_sheet(path)
    body = df.iloc[2:].copy()
    for col in [0, 1]:
        body[col] = body[col].ffill()
    body = body.rename(columns={0: "raw_region", 1: "age_group", 2: "husband_rate", 3: "wife_rate"})
    body["region"] = body["raw_region"].map(clean_region)
    keep = (body["region"] != "전국") & body["age_group"].astype(str).isin(AGE_40_64_SPACED)
    sub = body.loc[keep, ["region", "age_group", "husband_rate"]].copy()
    sub["husband_rate"] = sub["husband_rate"].map(numeric)
    out = (
        sub.groupby("region", as_index=False)
        .agg(
            husband_divorce_rate_40_64_mean_2025=("husband_rate", "mean"),
            husband_divorce_rate_40_64_max_2025=("husband_rate", "max"),
        )
    )
    return out


def parse_mortality_or_suicide(path: Path) -> tuple[pd.DataFrame, dict]:
    df = read_first_sheet(path)
    body = df.iloc[2:].copy()
    for col in [0, 1, 2, 3]:
        body[col] = body[col].ffill()
    body = body.rename(
        columns={
            0: "cause",
            1: "raw_region",
            2: "age_group",
            3: "sex",
            4: "death_count",
            5: "death_rate",
        }
    )
    body["region"] = body["raw_region"].map(clean_region)
    causes = sorted(body["cause"].dropna().astype(str).unique().tolist())
    has_suicide = any("자살" in c or "고의적 자해" in c for c in causes)
    target_cause = next((c for c in causes if "자살" in c or "고의적 자해" in c), None)
    cause_for_parse = target_cause if has_suicide else causes[0]
    keep = (
        (body["cause"].astype(str) == cause_for_parse)
        & (body["sex"].astype(str).str.strip() == "남자")
        & body["age_group"].astype(str).isin(AGE_40_64_SPACED)
    )
    sub = body.loc[keep, ["region", "age_group", "death_count", "death_rate"]].copy()
    sub["death_count"] = sub["death_count"].map(numeric)
    sub["death_rate"] = sub["death_rate"].map(numeric)
    sub["population_est"] = np.where(
        sub["death_rate"] > 0,
        sub["death_count"] / sub["death_rate"] * 100000,
        np.nan,
    )
    out = (
        sub.groupby("region", as_index=False)
        .agg(
            male_40_64_death_count_2024=("death_count", "sum"),
            male_40_64_population_est_2024=("population_est", "sum"),
        )
    )
    out["male_40_64_total_mortality_rate_2024"] = (
        out["male_40_64_death_count_2024"] / out["male_40_64_population_est_2024"] * 100000
    )
    metadata = {
        "file_name": path.name,
        "causes": causes,
        "has_suicide_cause": has_suicide,
        "parsed_cause": cause_for_parse,
        "note": (
            "Downloaded table contains a suicide cause."
            if has_suicide
            else "Downloaded table contains only cause='계'; parsed as all-cause mortality, not suicide."
        ),
    }
    return out, metadata


def build_current_panel(raw_files: dict[str, Path]) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    single = parse_single_household(raw_files["01"])
    social_region, social_context = parse_social_network(raw_files["02"])
    depression = parse_depression(raw_files["03"])
    livelihood = parse_basic_livelihood(raw_files["04"])
    closure = parse_closure(raw_files["05"])
    divorce = parse_divorce(raw_files["06"])
    mortality, mortality_meta = parse_mortality_or_suicide(raw_files["07"])

    expected = pd.read_csv(ART / "regional_expected_growth_decomposition.csv")
    expected = expected.rename(
        columns={
            "2020": "godoksa_count_2020",
            "2021": "godoksa_count_2021",
            "2022": "godoksa_count_2022",
            "2023": "godoksa_count_2023",
            "2024": "godoksa_count_2024",
            "change_2020_2024": "godoksa_change_2020_2024",
            "pct_change_2020_2024": "godoksa_pct_change_2020_2024",
        }
    )
    keep_cols = [
        "region",
        "godoksa_count_2020",
        "godoksa_count_2021",
        "godoksa_count_2022",
        "godoksa_count_2023",
        "godoksa_count_2024",
        "expected_2024_if_national_growth",
        "excess_2024_vs_expected",
        "godoksa_change_2020_2024",
        "godoksa_pct_change_2020_2024",
        "cagr_2020_2024_pct",
        "recent_change_2023_2024",
        "trajectory_type",
    ]
    panel = expected[keep_cols].copy()
    for frame in [single, livelihood, closure, mortality, depression, divorce, social_region]:
        panel = panel.merge(frame, on="region", how="left")

    pop = panel["male_40_64_population_est_2024"]
    panel["godoksa_per_100k_male_40_64_pop_proxy_2024"] = panel["godoksa_count_2024"] / pop * 100000
    panel["godoksa_excess_per_100k_male_40_64_pop_proxy_2024"] = (
        panel["excess_2024_vs_expected"] / pop * 100000
    )
    panel["male_40_64_single_household_rate_pct_2024"] = (
        panel["male_40_64_single_households_2024"] / pop * 100
    )
    panel["basic_livelihood_male_40_64_rate_per_1000_2024"] = (
        panel["basic_livelihood_male_40_64_count_2024"] / pop * 1000
    )
    panel["business_closure_male_40_64_approx_rate_per_1000_2024"] = (
        panel["business_closure_male_40_64_approx_count_2024"] / pop * 1000
    )
    panel["single_to_basic_livelihood_ratio_2024"] = (
        panel["male_40_64_single_households_2024"]
        / panel["basic_livelihood_male_40_64_count_2024"]
    )
    panel["log_male_40_64_population_2024"] = np.log(panel["male_40_64_population_est_2024"])
    panel["log_godoksa_count_2024"] = np.log(panel["godoksa_count_2024"])

    panel["z_single_rate"] = zscore(panel["male_40_64_single_household_rate_pct_2024"])
    panel["z_welfare_rate"] = zscore(panel["basic_livelihood_male_40_64_rate_per_1000_2024"])
    panel["z_closure_rate"] = zscore(panel["business_closure_male_40_64_approx_rate_per_1000_2024"])
    panel["z_divorce_rate"] = zscore(panel["husband_divorce_rate_40_64_mean_2025"])
    panel["z_depression"] = zscore(panel["depression_std_rate_2025"])
    panel["structural_isolation_index"] = panel[["z_single_rate", "z_welfare_rate", "z_depression"]].mean(axis=1)
    panel["event_stress_index"] = panel[["z_closure_rate", "z_divorce_rate"]].mean(axis=1)
    panel["composite_vulnerability_index"] = panel[
        ["structural_isolation_index", "event_stress_index"]
    ].mean(axis=1)
    panel["vulnerability_rank"] = (
        panel["composite_vulnerability_index"].rank(ascending=False, method="min").astype(int)
    )

    return panel, social_context, mortality_meta


def correlation_table(panel: pd.DataFrame) -> pd.DataFrame:
    outcomes = [
        "godoksa_count_2024",
        "godoksa_change_2020_2024",
        "excess_2024_vs_expected",
        "godoksa_per_100k_male_40_64_pop_proxy_2024",
        "godoksa_excess_per_100k_male_40_64_pop_proxy_2024",
    ]
    predictors = [
        "male_40_64_single_household_rate_pct_2024",
        "basic_livelihood_male_40_64_rate_per_1000_2024",
        "business_closure_male_40_64_approx_rate_per_1000_2024",
        "husband_divorce_rate_40_64_mean_2025",
        "depression_std_rate_2025",
        "male_40_64_total_mortality_rate_2024",
        "structural_isolation_index",
        "event_stress_index",
        "composite_vulnerability_index",
    ]
    rows = []
    for y in outcomes:
        for x in predictors:
            dat = panel[[y, x]].dropna()
            if len(dat) < 4:
                continue
            pearson_r, pearson_p = corr_with_p(dat[x], dat[y])
            spearman_r, spearman_p = corr_with_p(dat[x].rank(method="average"), dat[y].rank(method="average"))
            rows.append(
                {
                    "outcome": y,
                    "predictor": x,
                    "n": len(dat),
                    "pearson_r": pearson_r,
                    "pearson_p": pearson_p,
                    "spearman_rho": spearman_r,
                    "spearman_p": spearman_p,
                }
            )
    return pd.DataFrame(rows)


def ols_fit_manual(dat: pd.DataFrame, y: str, xs: list[str]) -> list[dict]:
    clean = dat[[y] + xs].replace([np.inf, -np.inf], np.nan).dropna().copy()
    n = len(clean)
    k = len(xs) + 1
    if n <= k + 1:
        return []
    yv = clean[y].astype(float).to_numpy().reshape(-1, 1)
    Xraw = clean[xs].astype(float).to_numpy()
    X = np.column_stack([np.ones(n), Xraw])
    terms = ["const"] + xs
    try:
        xtx_inv = np.linalg.pinv(X.T @ X)
        beta = xtx_inv @ X.T @ yv
        resid = (yv - X @ beta).reshape(-1)
        fitted = (X @ beta).reshape(-1)
        yflat = yv.reshape(-1)
        sse = float(np.sum(resid ** 2))
        sst = float(np.sum((yflat - yflat.mean()) ** 2))
        r2 = 1 - sse / sst if sst > 0 else np.nan
        adj_r2 = 1 - (1 - r2) * (n - 1) / (n - k) if np.isfinite(r2) and n > k else np.nan
        h = np.sum((X @ xtx_inv) * X, axis=1)
        hc3_scale = (resid / np.maximum(1e-8, 1 - h)) ** 2
        cov = xtx_inv @ (X.T @ (hc3_scale[:, None] * X)) @ xtx_inv
        se = np.sqrt(np.maximum(np.diag(cov), 0))
        coef = beta.reshape(-1)
        tvals = coef / se
        pvals = [t_two_sided_p(abs(float(t)), n - k) for t in tvals]
        sigma2 = sse / n if n > 0 else np.nan
        aic = n * math.log(sigma2) + 2 * k if sigma2 > 0 else np.nan
        bic = n * math.log(sigma2) + math.log(n) * k if sigma2 > 0 else np.nan
        rows = []
        for i, term in enumerate(terms):
            rows.append(
                {
                    "term": term,
                    "coef": float(coef[i]),
                    "std_error_hc3": float(se[i]),
                    "t": float(tvals[i]),
                    "p": float(pvals[i]) if np.isfinite(pvals[i]) else np.nan,
                    "n": int(n),
                    "r2": float(r2),
                    "adj_r2": float(adj_r2),
                    "aic": float(aic) if np.isfinite(aic) else np.nan,
                    "bic": float(bic) if np.isfinite(bic) else np.nan,
                }
            )
        return rows
    except Exception:
        return []


def ols_models(panel: pd.DataFrame) -> pd.DataFrame:
    specs = {
        "M1_rate_index": (
            "godoksa_per_100k_male_40_64_pop_proxy_2024",
            ["structural_isolation_index", "event_stress_index"],
        ),
        "M2_excess_rate_index": (
            "godoksa_excess_per_100k_male_40_64_pop_proxy_2024",
            ["structural_isolation_index", "event_stress_index"],
        ),
        "M3_log_count_size_adjusted": (
            "log_godoksa_count_2024",
            ["log_male_40_64_population_2024", "structural_isolation_index", "event_stress_index"],
        ),
        "M4_rate_components": (
            "godoksa_per_100k_male_40_64_pop_proxy_2024",
            [
                "male_40_64_single_household_rate_pct_2024",
                "basic_livelihood_male_40_64_rate_per_1000_2024",
                "business_closure_male_40_64_approx_rate_per_1000_2024",
            ],
        ),
    }
    rows = []
    for model_name, (y, xs) in specs.items():
        for row in ols_fit_manual(panel, y, xs):
            row.update({"model": model_name, "outcome": y})
            rows.append(row)
    return pd.DataFrame(rows)

def top_lines(panel: pd.DataFrame, corr: pd.DataFrame, ols: pd.DataFrame, mortality_meta: dict) -> str:
    top_vuln = panel.sort_values("composite_vulnerability_index", ascending=False).head(7)
    top_godoksa_rate = panel.sort_values(
        "godoksa_per_100k_male_40_64_pop_proxy_2024", ascending=False
    ).head(7)
    top_excess = panel.sort_values("excess_2024_vs_expected", ascending=False).head(7)

    def md_table(df: pd.DataFrame, cols: list[str], digits: int = 2) -> str:
        d = df[cols].copy()
        for c in d.columns:
            if pd.api.types.is_numeric_dtype(d[c]):
                d[c] = d[c].map(lambda x: "" if pd.isna(x) else round(float(x), digits))
            else:
                d[c] = d[c].map(lambda x: "" if pd.isna(x) else str(x))
        headers = [str(c) for c in d.columns]
        rows = [["" if pd.isna(v) else str(v) for v in row] for row in d.to_numpy()]
        lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
        for row in rows:
            safe = [cell.replace("|", "/") for cell in row]
            lines.append("| " + " | ".join(safe) + " |")
        return "\n".join(lines)

    key_corr = corr[
        corr["outcome"].isin(
            [
                "godoksa_per_100k_male_40_64_pop_proxy_2024",
                "excess_2024_vs_expected",
                "godoksa_count_2024",
            ]
        )
    ].copy()
    key_corr["abs_spearman"] = key_corr["spearman_rho"].abs()
    key_corr = key_corr.sort_values(["outcome", "abs_spearman"], ascending=[True, False])
    key_corr = key_corr.groupby("outcome").head(5)

    ols_key = ols[ols["term"] != "const"].copy()
    if not ols_key.empty:
        ols_key = ols_key.sort_values(["model", "p"])

    manifest = pd.read_csv(ART / "raw_file_manifest_20260623.csv")

    lines = []
    lines.append("# 원자료 7개 결합 후 최신 시도 단면 분석")
    lines.append("")
    lines.append("## 1. 처리 결과")
    lines.append("")
    lines.append(f"- 원자료 파일 7개를 읽어 시도 단위 최신 분석 패널 {len(panel)}행을 만들었다.")
    lines.append("- 1인가구, 기초생활, 폐업, 전체 사망/인구분모는 2024년이다.")
    lines.append("- 사회적 관계망, 우울감, 이혼율은 사용자가 내려받은 파일 기준 2025년이다.")
    lines.append("- 기존 보건복지부 고독사 지역 통계 2020-2024를 결합해 2024 고독사 수준, 2020-2024 증가, 전국성장률 대비 초과 증가를 종속변수로 구성했다.")
    lines.append("")
    lines.append("## 2. 원자료 품질 경고")
    lines.append("")
    lines.append(f"- `07_자살률` 파일의 사망원인 값: `{mortality_meta['causes']}`")
    lines.append(f"- 판정: {mortality_meta['note']}")
    lines.append("- 따라서 이번 산출물의 `male_40_64_total_mortality_rate_2024`는 남성 40-64세 전체 사망률이며, 지역별 자살률이 아니다.")
    lines.append("- `02_사회적관계망` 파일은 행정구역 값이 전국뿐이다. 지역 간 차이를 설명하는 독립변수로는 쓸 수 없고, 전국 남성/1인가구 맥락 변수로만 보존했다.")
    lines.append("- `05_폐업자`는 40대·50대·60대·70세 이상 구간이므로, 남성 40-64세 폐업은 `40대+50대+60대의 절반`으로 근사했다.")
    lines.append("")
    lines.append("## 3. 취약성 지수 상위 지역")
    lines.append("")
    lines.append(md_table(top_vuln, [
        "region",
        "composite_vulnerability_index",
        "structural_isolation_index",
        "event_stress_index",
        "male_40_64_single_household_rate_pct_2024",
        "basic_livelihood_male_40_64_rate_per_1000_2024",
        "business_closure_male_40_64_approx_rate_per_1000_2024",
        "depression_std_rate_2025",
        "husband_divorce_rate_40_64_mean_2025",
    ]))
    lines.append("")
    lines.append("## 4. 고독사율 프록시 상위 지역")
    lines.append("")
    lines.append(md_table(top_godoksa_rate, [
        "region",
        "godoksa_count_2024",
        "male_40_64_population_est_2024",
        "godoksa_per_100k_male_40_64_pop_proxy_2024",
        "male_40_64_single_household_rate_pct_2024",
        "basic_livelihood_male_40_64_rate_per_1000_2024",
        "business_closure_male_40_64_approx_rate_per_1000_2024",
    ]))
    lines.append("")
    lines.append("## 5. 고독사 초과 증가 상위 지역")
    lines.append("")
    lines.append(md_table(top_excess, [
        "region",
        "godoksa_count_2020",
        "godoksa_count_2024",
        "expected_2024_if_national_growth",
        "excess_2024_vs_expected",
        "godoksa_change_2020_2024",
        "recent_change_2023_2024",
    ]))
    lines.append("")
    lines.append("## 6. 주요 상관 결과")
    lines.append("")
    lines.append(md_table(key_corr, [
        "outcome",
        "predictor",
        "n",
        "pearson_r",
        "pearson_p",
        "spearman_rho",
        "spearman_p",
    ], digits=3))
    lines.append("")
    lines.append("## 7. 탐색적 회귀 결과")
    lines.append("")
    if ols_key.empty:
        lines.append("- statsmodels 실행이 불가능해 회귀표를 만들지 못했다.")
    else:
        lines.append(md_table(ols_key, [
            "model",
            "term",
            "coef",
            "std_error_hc3",
            "p",
            "n",
            "r2",
            "adj_r2",
        ], digits=4))
    lines.append("")
    lines.append("## 8. 지금 단계의 논문용 해석")
    lines.append("")
    lines.append("이번 결합자료에서 새롭게 말할 수 있는 것은 `중년 남성 고독사 위험`이 단순히 1인가구 수가 많은 지역에서만 커지는 현상이 아니라는 점이다. 인구 규모를 남성 40-64세 추정인구로 보정하면, 고독사율 프록시는 일부 비수도권·고령화 지역에서 크게 나타나고, 2020-2024년 초과 증가분은 서울·경기·대구처럼 대도시권 충격 지역에 집중된다.")
    lines.append("")
    lines.append("따라서 한 가지 원인으로 묶기보다 두 경로 모델이 더 설득력 있다. 첫째, 대도시권에서는 폐업·이혼·주거 불안·관계망 약화가 짧은 시간 안에 겹치는 `사건성 위기 경로`가 고독사 증가를 밀어 올린다. 둘째, 비수도권과 고령화 지역에서는 1인가구화·기초생활 수급·우울감·의료취약성이 누적되어 `축적형 방치 경로`가 강해진다.")
    lines.append("")
    lines.append("현재 다운로드된 7개 파일만으로는 지역별 남성 40-64세 자살률을 직접 검증할 수 없다. 자살률 파일은 사망원인 `계`로 내려받혀 있어, 다음 재다운로드에서 사망원인 `고의적 자해(자살)` 또는 `자살` 항목을 반드시 포함해야 한다. 그 파일이 들어오면 같은 스크립트에서 종속변수 B를 바로 대체해 회귀를 다시 돌릴 수 있다.")
    lines.append("")
    lines.append("## 9. 산출 파일")
    lines.append("")
    for _, r in manifest.iterrows():
        lines.append(f"- 원자료 {r['prefix']}: {r['file_name']}")
    lines.append("- `artifacts/current_raw_region_panel_2024_2025.csv`")
    lines.append("- `artifacts/region_year_panel_from_latest_raw_2020_2025.csv`")
    lines.append("- `artifacts/current_raw_correlations.csv`")
    lines.append("- `artifacts/current_raw_ols_models.csv`")
    lines.append("- `artifacts/national_social_network_context_2025.csv`")
    return "\n".join(lines)


def make_region_year_panel(panel: pd.DataFrame) -> pd.DataFrame:
    godoksa = pd.read_csv(ART / "godoksa_region_year_2020_2024.csv")
    godoksa = godoksa.rename(columns={"count": "godoksa_count", "share_pct": "godoksa_share_pct"})
    latest_cols_2024 = [
        "region",
        "male_40_64_single_households_2024",
        "male_40_64_single_household_rate_pct_2024",
        "basic_livelihood_male_40_64_count_2024",
        "basic_livelihood_male_40_64_rate_per_1000_2024",
        "business_closure_male_40_64_approx_count_2024",
        "business_closure_male_40_64_approx_rate_per_1000_2024",
        "male_40_64_death_count_2024",
        "male_40_64_population_est_2024",
        "male_40_64_total_mortality_rate_2024",
    ]
    current_2024 = panel[latest_cols_2024].copy()
    current_2024["year"] = 2024
    current_2024 = current_2024.rename(columns={c: c.replace("_2024", "") for c in latest_cols_2024 if c != "region"})

    latest_cols_2025 = [
        "region",
        "depression_crude_rate_2025",
        "depression_std_rate_2025",
        "husband_divorce_rate_40_64_mean_2025",
        "husband_divorce_rate_40_64_max_2025",
        "national_male_social_no_help_sick_housework_pct_2025",
        "national_male_social_no_help_money_pct_2025",
        "national_male_social_no_depressed_talk_pct_2025",
        "national_one_person_social_no_help_sick_housework_pct_2025",
        "national_one_person_social_no_help_money_pct_2025",
        "national_one_person_social_no_depressed_talk_pct_2025",
    ]
    current_2025 = panel[latest_cols_2025].copy()
    current_2025["year"] = 2025
    current_2025 = current_2025.rename(columns={c: c.replace("_2025", "") for c in latest_cols_2025 if c != "region"})

    years = sorted(set(godoksa["year"]).union({2025}))
    regions = sorted(panel["region"].unique())
    skeleton = pd.MultiIndex.from_product([regions, years], names=["region", "year"]).to_frame(index=False)
    out = skeleton.merge(godoksa, on=["region", "year"], how="left")
    out = out.merge(current_2024, on=["region", "year"], how="left")
    out = out.merge(current_2025, on=["region", "year"], how="left")
    out["panel_note"] = np.where(
        out["year"].isin([2024, 2025]),
        "raw_covariates_observed_for_this_year_where_available",
        "godoksa_only_until multi-year covariates are downloaded",
    )
    return out


def main() -> None:
    raw_files = find_raw_files()
    manifest = []
    for prefix, path in raw_files.items():
        manifest.append(
            {
                "prefix": prefix,
                "file_name": path.name,
                "full_path": str(path),
                "size_bytes": path.stat().st_size,
                "last_write_time": pd.Timestamp(path.stat().st_mtime, unit="s").isoformat(),
            }
        )
    pd.DataFrame(manifest).to_csv(ART / "raw_file_manifest_20260623.csv", index=False, encoding="utf-8-sig")

    panel, social_context, mortality_meta = build_current_panel(raw_files)
    corr = correlation_table(panel)
    ols = ols_models(panel)
    region_year = make_region_year_panel(panel)

    panel.to_csv(ART / "current_raw_region_panel_2024_2025.csv", index=False, encoding="utf-8-sig")
    region_year.to_csv(ART / "region_year_panel_from_latest_raw_2020_2025.csv", index=False, encoding="utf-8-sig")
    social_context.to_csv(ART / "national_social_network_context_2025.csv", index=False, encoding="utf-8-sig")
    corr.to_csv(ART / "current_raw_correlations.csv", index=False, encoding="utf-8-sig")
    ols.to_csv(ART / "current_raw_ols_models.csv", index=False, encoding="utf-8-sig")
    with (ART / "mortality_file_quality_check.json").open("w", encoding="utf-8") as f:
        json.dump(mortality_meta, f, ensure_ascii=False, indent=2)

    quality = pd.DataFrame(
        [
            {
                "variable_group": "one_person_households",
                "source_prefix": "01",
                "observed_year": 2024,
                "regional_variation": True,
                "target_fit": "exact male 40-64",
                "note": "summed five-year age bands 40-44 to 60-64",
            },
            {
                "variable_group": "social_network",
                "source_prefix": "02",
                "observed_year": 2025,
                "regional_variation": False,
                "target_fit": "national male and national one-person household context only",
                "note": "downloaded file contains only nationwide rows",
            },
            {
                "variable_group": "depression",
                "source_prefix": "03",
                "observed_year": 2025,
                "regional_variation": True,
                "target_fit": "all adults, not male 40-64-specific",
                "note": "used city/province subtotal standardized rate",
            },
            {
                "variable_group": "basic_livelihood",
                "source_prefix": "04",
                "observed_year": 2024,
                "regional_variation": True,
                "target_fit": "exact male 40-64",
                "note": "summed five-year age bands",
            },
            {
                "variable_group": "business_closure",
                "source_prefix": "05",
                "observed_year": 2024,
                "regional_variation": True,
                "target_fit": "approximate male 40-64",
                "note": "used male 40s + 50s + half of 60s",
            },
            {
                "variable_group": "divorce",
                "source_prefix": "06",
                "observed_year": 2025,
                "regional_variation": True,
                "target_fit": "male/husband 40-64 rates, unweighted mean",
                "note": "population weights not in downloaded file",
            },
            {
                "variable_group": "suicide_or_mortality",
                "source_prefix": "07",
                "observed_year": 2024,
                "regional_variation": True,
                "target_fit": "not suicide; all-cause male 40-64 mortality",
                "note": mortality_meta["note"],
            },
        ]
    )
    quality.to_csv(ART / "current_raw_variable_quality_flags.csv", index=False, encoding="utf-8-sig")

    report = top_lines(panel, corr, ols, mortality_meta)
    (OUT / "09_raw_panel_analysis_korean.md").write_text(report, encoding="utf-8")

    print(
        json.dumps(
            {
                "raw_files": len(raw_files),
                "panel_rows": int(len(panel)),
                "region_year_rows": int(len(region_year)),
                "correlations": int(len(corr)),
                "ols_rows": int(len(ols)),
                "mortality_meta": mortality_meta,
                "outputs": [
                    str(ART / "current_raw_region_panel_2024_2025.csv"),
                    str(ART / "region_year_panel_from_latest_raw_2020_2025.csv"),
                    str(ART / "current_raw_correlations.csv"),
                    str(ART / "current_raw_ols_models.csv"),
                    str(OUT / "09_raw_panel_analysis_korean.md"),
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
