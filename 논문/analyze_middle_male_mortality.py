from pathlib import Path
import warnings

import numpy as np
import pandas as pd


warnings.filterwarnings("ignore", category=RuntimeWarning)

BASE = Path("analysis_outputs_middle_male_mortality")
BASE.mkdir(exist_ok=True)

BIGDATA = Path(r"C:\Users\user\OneDrive\D 대학원 박사\A 아주대\2. 사회심리학과 빅데이터 (박현준)\데이터\(남보라) Bigdata_middle_male.csv")
MORTALITY = Path(r"C:\Users\user\OneDrive\D 대학원 박사\A 아주대\2. 사회심리학과 빅데이터 (박현준)\데이터\(남보라) 사망원인_104항목__성_연령_5세_별_사망자수__사망률_20260530004605.csv")


def age_band(age):
    bins = [(40, 44), (45, 49), (50, 54), (55, 59), (60, 64)]
    for lo, hi in bins:
        if lo <= age <= hi:
            return f"{lo} - {hi}세"
    return np.nan


def weighted_mean(x, w):
    mask = x.notna() & w.notna() & (w > 0)
    if mask.sum() == 0:
        return np.nan
    return np.average(x[mask], weights=w[mask])


def weighted_rate(x, w):
    return weighted_mean(x.astype(float), w)


def read_mortality():
    raw = pd.read_csv(MORTALITY, encoding="cp949")
    raw = raw.rename(columns={"사망원인별(104항목)": "cause", "성별": "sex", "연령": "age_band"})
    raw[["cause", "sex"]] = raw[["cause", "sex"]].ffill()
    raw = raw[raw["age_band"].notna()].copy()

    rows = []
    for _, row in raw.iterrows():
        for year in range(2010, 2025):
            count_col = str(year)
            rate_col = f"{year}.1"
            rows.append(
                {
                    "cause": row["cause"],
                    "sex": row["sex"],
                    "age_band": row["age_band"],
                    "survey_year": year,
                    "suicide_deaths": pd.to_numeric(row[count_col], errors="coerce"),
                    "suicide_rate": pd.to_numeric(row[rate_col], errors="coerce"),
                }
            )
    return pd.DataFrame(rows)


def read_bigdata():
    df = pd.read_csv(BIGDATA, encoding="utf-8-sig")
    df["age_band"] = df["age"].apply(age_band)
    df = df[df["age_band"].notna()].copy()
    df["low_income"] = df["income_group"].astype(str).str.contains("1구간", regex=False).astype(float)
    df["high_income"] = df["income_group"].astype(str).str.contains("5구간", regex=False).astype(float)
    df["depression_high"] = (df["CES_D"] >= 16).astype(float)
    df.loc[df["CES_D"].isna(), "depression_high"] = np.nan
    df["self_esteem_low"] = (df["SELF_ESTEEM"] <= 28).astype(float)
    df.loc[df["SELF_ESTEEM"].isna(), "self_esteem_low"] = np.nan
    df["problem_drinking"] = (df["AUDIT"] >= 8).astype(float)
    df.loc[df["AUDIT"].isna(), "problem_drinking"] = np.nan
    df["high_risk_drinking"] = (df["AUDIT"] >= 15).astype(float)
    df.loc[df["AUDIT"].isna(), "high_risk_drinking"] = np.nan
    for cols, out in [
        (["p03_5", "p03_6", "p03_7", "p03_9", "p03_10"], "p03_composite"),
        (["p05_aq1", "p05_aq2", "p05_aq3"], "p05_aq_composite"),
    ]:
        z = df[cols].apply(pd.to_numeric, errors="coerce")
        z = (z - z.mean()) / z.std(ddof=0)
        df[out] = z.mean(axis=1)
    return df


def aggregate_bigdata(df):
    numeric_means = [
        "age",
        "h_din",
        "CES_D",
        "SELF_ESTEEM",
        "AUDIT",
        "low_income",
        "high_income",
        "depression_high",
        "self_esteem_low",
        "problem_drinking",
        "high_risk_drinking",
        "p03_5",
        "p03_6",
        "p03_7",
        "p03_9",
        "p03_10",
        "p05_aq1",
        "p05_aq2",
        "p05_aq3",
        "p05_7aq1_mod",
        "p05_12aq1",
        "p03_composite",
        "p05_aq_composite",
    ]
    rows = []
    for (year, band), g in df.groupby(["survey_year", "age_band"], dropna=False):
        w = g["wgt_n"].fillna(g["combined_wgt"]).fillna(g["raw_wgt"])
        out = {
            "survey_year": year,
            "age_band": band,
            "n": len(g),
            "unique_people": g["h_pid"].nunique(),
            "weight_sum": w.sum(),
        }
        for col in numeric_means:
            out[f"{col}_wm"] = weighted_mean(pd.to_numeric(g[col], errors="coerce"), w)
        rows.append(out)
    return pd.DataFrame(rows)


def safe_corr(x, y):
    m = x.notna() & y.notna()
    if m.sum() < 4 or x[m].nunique() < 2 or y[m].nunique() < 2:
        return np.nan, int(m.sum())
    r = np.corrcoef(x[m].astype(float), y[m].astype(float))[0, 1]
    return r, int(m.sum())


def spearman_corr(x, y):
    d = pd.DataFrame({"x": x, "y": y}).dropna()
    if len(d) < 4 or d["x"].nunique() < 2 or d["y"].nunique() < 2:
        return np.nan
    return np.corrcoef(d["x"].rank(), d["y"].rank())[0, 1]


def permutation_p(x, y, n_perm=10000, seed=42):
    m = x.notna() & y.notna()
    xv = x[m].to_numpy()
    yv = y[m].to_numpy()
    if len(xv) < 4 or np.std(xv) == 0 or np.std(yv) == 0:
        return np.nan
    rng = np.random.default_rng(seed)
    obs = abs(np.corrcoef(xv, yv)[0, 1])
    hits = 0
    for _ in range(n_perm):
        yp = rng.permutation(yv)
        if abs(np.corrcoef(xv, yp)[0, 1]) >= obs:
            hits += 1
    return (hits + 1) / (n_perm + 1)


def residualize(series, groups):
    return series - series.groupby(groups).transform("mean")


def cronbach_alpha(df, cols):
    x = df[cols].apply(pd.to_numeric, errors="coerce").dropna()
    if len(x) < 10 or len(cols) < 2:
        return np.nan, len(x)
    item_var = x.var(axis=0, ddof=1).sum()
    total_var = x.sum(axis=1).var(ddof=1)
    if total_var <= 0:
        return np.nan, len(x)
    k = len(cols)
    return (k / (k - 1)) * (1 - item_var / total_var), len(x)


def ols_table(merged):
    candidates = {
        "depression_high_wm": "우울 고위험 비율",
        "self_esteem_low_wm": "낮은 자존감 비율",
        "problem_drinking_wm": "문제음주 비율",
        "AUDIT_wm": "AUDIT 평균",
        "low_income_wm": "저소득 비율",
        "h_din_wm": "가구소득 평균",
    }
    rows = []
    for col, label in candidates.items():
        d = merged[["suicide_rate", col, "survey_year", "age_band"]].dropna()
        if len(d) < 10:
            continue
        xraw = pd.concat(
            [
                d[[col]],
                pd.get_dummies(d["survey_year"].astype(str), prefix="year", drop_first=True),
                pd.get_dummies(d["age_band"].astype(str), prefix="age", drop_first=True),
            ],
            axis=1,
        )
        x = np.column_stack([np.ones(len(xraw)), xraw.astype(float).to_numpy()])
        y = d["suicide_rate"].astype(float).to_numpy()
        beta, *_ = np.linalg.lstsq(x, y, rcond=None)
        yhat = x @ beta
        ss_res = ((y - yhat) ** 2).sum()
        ss_tot = ((y - y.mean()) ** 2).sum()
        r2 = 1 - ss_res / ss_tot if ss_tot > 0 else np.nan
        rows.append(
            {
                "variable": col,
                "label_ko": label,
                "coef_with_year_age_FE": beta[1] if len(beta) > 1 else np.nan,
                "n_cells": len(d),
                "r2": r2,
            }
        )
    return pd.DataFrame(rows).sort_values("r2", ascending=False)


def lagged_correlations(merged, labels):
    d = merged.sort_values(["age_band", "survey_year"]).copy()
    d["next_suicide_rate"] = d.groupby("age_band")["suicide_rate"].shift(-1)
    rows = []
    for col, label in labels.items():
        r, n = safe_corr(d[col], d["next_suicide_rate"])
        rows.append(
            {
                "variable": col,
                "label_ko": label,
                "lag_pearson_r": r,
                "lag_spearman_r": spearman_corr(d[col], d["next_suicide_rate"]),
                "lag_permutation_p": permutation_p(d[col], d["next_suicide_rate"], n_perm=5000),
                "n_lag_cells": n,
            }
        )
    return pd.DataFrame(rows).sort_values("lag_pearson_r", key=lambda s: s.abs(), ascending=False)


def vulnerability_profiles(big):
    w = big["wgt_n"].fillna(big["combined_wgt"]).fillna(big["raw_wgt"])
    groups = {
        "우울 고위험": big["depression_high"] == 1,
        "우울 고위험 아님": big["depression_high"] == 0,
        "우울+문제음주": (big["depression_high"] == 1) & (big["problem_drinking"] == 1),
        "우울+저소득": (big["depression_high"] == 1) & (big["low_income"] == 1),
        "저자존감+문제음주": (big["self_esteem_low"] == 1) & (big["problem_drinking"] == 1),
    }
    rows = []
    for name, mask in groups.items():
        g = big[mask].copy()
        wg = w[mask]
        rows.append(
            {
                "profile": name,
                "n": len(g),
                "weighted_share": wg.sum() / w.sum(),
                "age_mean": weighted_mean(g["age"], wg),
                "income_mean": weighted_mean(g["h_din"], wg),
                "CES_D_mean": weighted_mean(g["CES_D"], wg),
                "SELF_ESTEEM_mean": weighted_mean(g["SELF_ESTEEM"], wg),
                "AUDIT_mean": weighted_mean(g["AUDIT"], wg),
                "problem_drinking_share": weighted_rate(g["problem_drinking"], wg),
                "low_income_share": weighted_rate(g["low_income"], wg),
            }
        )
    return pd.DataFrame(rows)


def svg_line_chart(merged):
    width, height, pad = 820, 390, 50
    years = sorted(merged["survey_year"].unique())
    rates = merged["suicide_rate"]
    ymin, ymax = rates.min() - 2, rates.max() + 2
    bands = list(merged["age_band"].drop_duplicates())
    colors = ["#2364aa", "#3da5d9", "#73bfb8", "#f4a261", "#d62828"]

    def sx(year):
        return pad + (year - min(years)) / (max(years) - min(years)) * (width - pad * 2)

    def sy(rate):
        return height - pad - (rate - ymin) / (ymax - ymin) * (height - pad * 2)

    parts = [f'<svg viewBox="0 0 {width} {height}" width="100%" height="{height}" role="img">']
    parts.append('<rect width="100%" height="100%" fill="#fff"/>')
    parts.append(f'<line x1="{pad}" y1="{height-pad}" x2="{width-pad}" y2="{height-pad}" stroke="#222"/>')
    parts.append(f'<line x1="{pad}" y1="{pad}" x2="{pad}" y2="{height-pad}" stroke="#222"/>')
    for year in years:
        x = sx(year)
        parts.append(f'<text x="{x}" y="{height-18}" text-anchor="middle" font-size="12">{year}</text>')
    for tick in np.linspace(np.ceil(ymin / 5) * 5, np.floor(ymax / 5) * 5, 5):
        y = sy(tick)
        parts.append(f'<line x1="{pad}" y1="{y}" x2="{width-pad}" y2="{y}" stroke="#e8e8e8"/>')
        parts.append(f'<text x="{pad-8}" y="{y+4}" text-anchor="end" font-size="12">{tick:.0f}</text>')
    for i, band in enumerate(bands):
        d = merged[merged["age_band"] == band].sort_values("survey_year")
        pts = " ".join(f"{sx(r.survey_year):.1f},{sy(r.suicide_rate):.1f}" for r in d.itertuples())
        parts.append(f'<polyline points="{pts}" fill="none" stroke="{colors[i % len(colors)]}" stroke-width="2.4"/>')
        for r in d.itertuples():
            parts.append(f'<circle cx="{sx(r.survey_year):.1f}" cy="{sy(r.suicide_rate):.1f}" r="3.8" fill="{colors[i % len(colors)]}"/>')
        parts.append(f'<text x="{width-pad+8}" y="{sy(d.iloc[-1].suicide_rate)+4:.1f}" font-size="12" fill="{colors[i % len(colors)]}">{band}</text>')
    parts.append('<text x="410" y="26" text-anchor="middle" font-size="17" font-weight="700">남성 40-64세 연령대별 자살 사망률</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def svg_bar_corr(corr):
    top = corr.sort_values("pearson_r", key=lambda s: s.abs(), ascending=False).head(12).iloc[::-1]
    width, height, pad_l, pad_r = 880, 440, 210, 35
    row_h = (height - 60) / len(top)
    zero = pad_l + (width - pad_l - pad_r) / 2
    scale = (width - pad_l - pad_r) / 2
    parts = [f'<svg viewBox="0 0 {width} {height}" width="100%" height="{height}" role="img">']
    parts.append('<rect width="100%" height="100%" fill="#fff"/>')
    parts.append(f'<line x1="{zero}" y1="35" x2="{zero}" y2="{height-25}" stroke="#222"/>')
    for i, r in enumerate(top.itertuples()):
        y = 45 + i * row_h
        x2 = zero + r.pearson_r * scale
        x = min(zero, x2)
        w = abs(x2 - zero)
        color = "#2364aa" if r.pearson_r >= 0 else "#d95f0e"
        parts.append(f'<text x="{pad_l-8}" y="{y+14}" text-anchor="end" font-size="12">{r.label_ko}</text>')
        parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{row_h*0.62}" fill="{color}"/>')
        parts.append(f'<text x="{x2 + (5 if r.pearson_r>=0 else -5)}" y="{y+14}" text-anchor="{"start" if r.pearson_r>=0 else "end"}" font-size="12">{r.pearson_r:.2f}</text>')
    parts.append('<text x="440" y="22" text-anchor="middle" font-size="17" font-weight="700">자살 사망률과의 탐색 상관</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def html_table(df):
    return df.to_html(index=False, border=0, classes="data", escape=False)


def md_table(df):
    d = df.copy()
    cols = list(d.columns)
    lines = ["| " + " | ".join(map(str, cols)) + " |"]
    lines.append("| " + " | ".join(["---"] * len(cols)) + " |")
    for _, row in d.iterrows():
        vals = []
        for col in cols:
            val = row[col]
            if isinstance(val, float):
                vals.append("" if pd.isna(val) else f"{val:.3f}")
            else:
                vals.append("" if pd.isna(val) else str(val))
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)


def main():
    big = read_bigdata()
    mort = read_mortality()
    agg = aggregate_bigdata(big)
    merged = agg.merge(mort, on=["survey_year", "age_band"], how="inner")
    merged = merged.sort_values(["survey_year", "age_band"])

    merged.to_csv(BASE / "merged_age_year_panel.csv", index=False, encoding="utf-8-sig")
    agg.to_csv(BASE / "bigdata_weighted_age_year_aggregates.csv", index=False, encoding="utf-8-sig")
    mort.to_csv(BASE / "mortality_suicide_long.csv", index=False, encoding="utf-8-sig")

    labels = {
        "h_din_wm": "가구소득 평균",
        "CES_D_wm": "우울 평균(CES-D)",
        "SELF_ESTEEM_wm": "자존감 평균",
        "AUDIT_wm": "AUDIT 평균",
        "low_income_wm": "저소득 비율",
        "high_income_wm": "고소득 비율",
        "depression_high_wm": "우울 고위험 비율",
        "self_esteem_low_wm": "낮은 자존감 비율",
        "problem_drinking_wm": "문제음주 비율",
        "high_risk_drinking_wm": "고위험 음주 비율",
        "p03_5_wm": "p03_5 평균",
        "p03_6_wm": "p03_6 평균",
        "p03_7_wm": "p03_7 평균",
        "p03_9_wm": "p03_9 평균",
        "p03_10_wm": "p03_10 평균",
        "p05_aq1_wm": "p05_aq1 평균",
        "p05_aq2_wm": "p05_aq2 평균",
        "p05_aq3_wm": "p05_aq3 평균",
        "p05_7aq1_mod_wm": "p05_7aq1_mod 비율",
        "p05_12aq1_wm": "p05_12aq1 평균",
        "p03_composite_wm": "p03 문항 합성점수",
        "p05_aq_composite_wm": "p05_aq 문항 합성점수",
    }
    rows = []
    for col, label in labels.items():
        r, n = safe_corr(merged[col], merged["suicide_rate"])
        sr = spearman_corr(merged[col], merged["suicide_rate"])
        age_resid_r, _ = safe_corr(residualize(merged[col], merged["age_band"]), residualize(merged["suicide_rate"], merged["age_band"]))
        year_resid_r, _ = safe_corr(residualize(merged[col], merged["survey_year"]), residualize(merged["suicide_rate"], merged["survey_year"]))
        rows.append(
            {
                "variable": col,
                "label_ko": label,
                "pearson_r": r,
                "spearman_r": sr,
                "age_demeaned_r": age_resid_r,
                "year_demeaned_r": year_resid_r,
                "permutation_p": permutation_p(merged[col], merged["suicide_rate"], n_perm=5000),
                "n_cells": n,
            }
        )
    corr = pd.DataFrame(rows).sort_values("pearson_r", key=lambda s: s.abs(), ascending=False)
    corr.to_csv(BASE / "exploratory_correlations.csv", index=False, encoding="utf-8-sig")

    ols = ols_table(merged)
    ols.to_csv(BASE / "ols_year_age_fixed_effects.csv", index=False, encoding="utf-8-sig")
    lag = lagged_correlations(merged, labels)
    lag.to_csv(BASE / "lagged_correlations_t_to_tplus1.csv", index=False, encoding="utf-8-sig")
    profiles = vulnerability_profiles(big)
    profiles.to_csv(BASE / "vulnerability_profiles.csv", index=False, encoding="utf-8-sig")
    alpha_p03, alpha_p03_n = cronbach_alpha(big, ["p03_5", "p03_6", "p03_7", "p03_9", "p03_10"])
    alpha_p05, alpha_p05_n = cronbach_alpha(big, ["p05_aq1", "p05_aq2", "p05_aq3"])

    cell_summary = merged.groupby("age_band").agg(
        suicide_rate_mean=("suicide_rate", "mean"),
        suicide_rate_min=("suicide_rate", "min"),
        suicide_rate_max=("suicide_rate", "max"),
        depression_high_mean=("depression_high_wm", "mean"),
        problem_drinking_mean=("problem_drinking_wm", "mean"),
        low_income_mean=("low_income_wm", "mean"),
        n_cell_mean=("n", "mean"),
    ).round(3)
    cell_summary.to_csv(BASE / "age_band_summary.csv", encoding="utf-8-sig")

    top_corr = corr.head(10).copy()
    top_corr[["pearson_r", "spearman_r", "age_demeaned_r", "year_demeaned_r", "permutation_p"]] = top_corr[
        ["pearson_r", "spearman_r", "age_demeaned_r", "year_demeaned_r", "permutation_p"]
    ].round(3)
    top_ols = ols.copy()
    if len(top_ols):
        top_ols[["coef_with_year_age_FE", "r2"]] = top_ols[["coef_with_year_age_FE", "r2"]].round(3)

    top_lag = lag.head(8).copy()
    top_lag[["lag_pearson_r", "lag_spearman_r", "lag_permutation_p"]] = top_lag[
        ["lag_pearson_r", "lag_spearman_r", "lag_permutation_p"]
    ].round(3)
    profiles_round = profiles.copy()
    for col in profiles_round.columns:
        if profiles_round[col].dtype.kind in "fc":
            profiles_round[col] = profiles_round[col].round(3)

    report = f"""# 중년 남성 개인자료와 자살 사망률 통합 탐색 분석

## 1. 자료 구조와 병합 방식

- 개인자료: `{BIGDATA.name}`, {len(big):,}행, 남성 40-64세, 조사연도 {int(big.survey_year.min())}-{int(big.survey_year.max())}.
- 사망자료: `{MORTALITY.name}`. 파일명은 104항목 사망원인이지만, 현재 CSV에 들어 있는 실제 원인은 `고의적 자해(자살) (X60-X84)` 남성 40-64세 5세 연령대별 사망자수와 사망률이다.
- 병합 단위: 개인자료를 `survey_year x age_band`로 가중 집계한 뒤, 같은 연도·연령대의 자살 사망률(십만 명당)과 결합했다.
- 최종 병합 셀: {len(merged)}개 = {merged['survey_year'].nunique()}개 연도 x {merged['age_band'].nunique()}개 5세 연령대.

주의: 이 분석은 동일 개인의 사망을 추적한 것이 아니다. 따라서 인과적 사망 예측이 아니라, 중년 남성의 심리사회적 조건이 동시대 연령대별 자살 사망률 구조와 어떻게 맞물리는지 보는 생태학적·탐색적 분석이다.

## 2. 핵심 기술 결과

연령대별 평균 자살 사망률과 개인자료 집계값:

{md_table(cell_summary.reset_index())}

## 3. 가장 큰 탐색 상관

{md_table(top_corr[['label_ko','pearson_r','spearman_r','age_demeaned_r','year_demeaned_r','permutation_p','n_cells']])}

해석법:
- `pearson_r`: 전체 30개 연도-연령 셀에서의 단순 상관.
- `spearman_r`: 순위 기반 상관.
- `age_demeaned_r`: 연령대 평균을 제거한 뒤, 같은 연령대 안에서 연도 변화가 함께 움직이는지 본 값.
- `year_demeaned_r`: 특정 연도 효과를 제거한 뒤, 같은 연도 안에서 연령대 차이가 함께 움직이는지 본 값.
- 표본 셀이 작기 때문에 p값보다 효과 크기와 방향의 일관성을 우선 해석해야 한다.

## 4. 연도·연령대 고정효과 회귀

연도와 5세 연령대 더미를 함께 넣어, 단순한 나이 차이나 특정 연도 충격을 통제한 매우 보수적인 모형이다. 패키지 제약상 p값 대신 계수와 설명력만 산출했다.

{md_table(top_ols) if len(top_ols) else '고정효과 회귀를 계산할 충분한 변동이 없었다.'}

## 5. 추가 탐색: 문항 묶음과 1년 지연

- p03 문항 5개 합성 신뢰도 Cronbach alpha: {alpha_p03:.3f} (완전응답 n={alpha_p03_n:,})
- p05_aq 문항 3개 합성 신뢰도 Cronbach alpha: {alpha_p05:.3f} (완전응답 n={alpha_p05_n:,})

동일 연령대에서 `t년`의 심리사회 지표가 `t+1년` 자살 사망률과 연결되는지 본 1년 지연 상관:

{md_table(top_lag[['label_ko','lag_pearson_r','lag_spearman_r','lag_permutation_p','n_lag_cells']])}

## 6. 개인자료 내부 취약 프로파일

{md_table(profiles_round)}

## 7. 사회심리학적 해석

가장 논문화하기 좋은 프레임은 “한국 중년 남성의 자살 위험은 개인의 우울만이 아니라 생계부양자 역할, 지위불안, 도움요청 회피, 음주를 통한 대처, 건강방치가 결합된 사회심리적 취약성의 결과”라는 것이다.

이 데이터에서는 특히 다음 세 가지를 중심 결과로 삼을 수 있다.

1. 연령 효과: 자살 사망률은 55-59세 및 60-64세에서 높게 나타나며, 중년 후반으로 갈수록 역할 상실, 건강 악화, 은퇴 불안이 누적되는 생애전환 가설과 맞물린다.
2. 심리·경제 취약성: 우울, 낮은 자존감, 저소득 집계 지표가 자살 사망률과 같은 방향으로 움직이는지 확인할 수 있다. 이는 개인 책임론이 아니라 사회경제적 압박이 심리적 취약성으로 번역되는 과정으로 해석해야 한다.
3. 음주 대처: AUDIT 및 문제음주 지표는 남성적 스트레스 대처양식의 간접 지표로 쓸 수 있다. 자살률과의 관련은 충동성, 우울 악화, 도움요청 지연이라는 경로로 논의할 수 있다.

## 8. 산출 파일

- `merged_age_year_panel.csv`: 병합된 최종 연도-연령대 패널.
- `bigdata_weighted_age_year_aggregates.csv`: 개인자료 가중 집계.
- `mortality_suicide_long.csv`: 사망자료 long format.
- `exploratory_correlations.csv`: 전체 탐색 상관.
- `ols_year_age_fixed_effects.csv`: 보수적 고정효과 회귀.
- `lagged_correlations_t_to_tplus1.csv`: 1년 지연 탐색 상관.
- `vulnerability_profiles.csv`: 개인자료 내부 취약집단 프로파일.
- `integrated_analysis_report.html`: 표와 SVG 시각화가 포함된 보고서.
"""
    (BASE / "integrated_analysis_report.md").write_text(report, encoding="utf-8")
    html = f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>중년 남성 개인자료와 자살 사망률 통합 탐색 분석</title>
<style>
body {{ font-family: "Malgun Gothic", Arial, sans-serif; margin: 36px; color: #222; line-height: 1.55; }}
h1, h2 {{ line-height: 1.25; }}
.note {{ background: #f5f7fa; border-left: 4px solid #2364aa; padding: 12px 14px; }}
.data {{ border-collapse: collapse; width: 100%; margin: 12px 0 26px; font-size: 13px; }}
.data th, .data td {{ border-bottom: 1px solid #ddd; padding: 7px 8px; text-align: right; }}
.data th:first-child, .data td:first-child, .data th:nth-child(2), .data td:nth-child(2) {{ text-align: left; }}
svg {{ margin: 14px 0 28px; border: 1px solid #eee; }}
</style>
</head>
<body>
<h1>중년 남성 개인자료와 자살 사망률 통합 탐색 분석</h1>
<p class="note">현재 사망자료 CSV에는 104개 사망원인이 모두 들어 있지 않고, 남성 40-64세의 고의적 자해(자살) 사망자수와 사망률만 포함되어 있다. 따라서 본 결과는 자살 사망률에 대한 생태학적 탐색 분석이다.</p>
<h2>병합 구조</h2>
<p>개인자료 {len(big):,}행을 조사연도와 5세 연령대로 가중 집계한 뒤, 같은 연도·연령대의 자살 사망률과 결합했다. 최종 분석 셀은 {len(merged)}개다.</p>
<h2>연령대별 자살 사망률</h2>
{svg_line_chart(merged)}
<h2>연령대 요약</h2>
{cell_summary.reset_index().to_html(index=False, border=0, classes="data")}
<h2>탐색 상관 상위 결과</h2>
{html_table(top_corr[['label_ko','pearson_r','spearman_r','age_demeaned_r','year_demeaned_r','permutation_p','n_cells']])}
{svg_bar_corr(corr)}
<h2>연도·연령대 고정효과 회귀</h2>
<p>셀 수가 30개뿐이므로 한 번에 한 변수만 투입했다. 계수는 연도와 연령대 차이를 제거한 뒤 해당 집계 지표가 1단위 증가할 때 자살 사망률이 얼마나 달라지는지의 탐색적 값이다.</p>
{html_table(top_ols) if len(top_ols) else '<p>고정효과 회귀를 계산할 충분한 변동이 없었다.</p>'}
<h2>문항 묶음과 1년 지연 분석</h2>
<p>p03 문항 합성 신뢰도 alpha={alpha_p03:.3f}, p05_aq 문항 합성 신뢰도 alpha={alpha_p05:.3f}. 아래 표는 같은 연령대에서 t년 지표와 t+1년 자살 사망률의 탐색 상관이다.</p>
{html_table(top_lag[['label_ko','lag_pearson_r','lag_spearman_r','lag_permutation_p','n_lag_cells']])}
<h2>개인자료 내부 취약 프로파일</h2>
{html_table(profiles_round)}
<h2>사회심리학적 결론</h2>
<p>가장 논문 가치가 있는 해석은 한국 중년 남성의 자살 사망률을 개인 심리 문제로 좁히지 않고, 생계부양자 역할 압박, 지위불안, 도움요청 회피, 음주를 통한 대처, 중년 후반의 역할 전환이 결합된 사회심리적 취약성으로 읽는 것이다.</p>
</body>
</html>
"""
    (BASE / "integrated_analysis_report.html").write_text(html, encoding="utf-8")
    print(f"done: {BASE.resolve()}")
    print(f"merged cells: {len(merged)}")
    print(top_corr[["label_ko", "pearson_r", "spearman_r", "age_demeaned_r", "year_demeaned_r"]].head(8).round(3).to_string(index=False))
    print("lagged")
    print(top_lag[["label_ko", "lag_pearson_r", "lag_spearman_r"]].head(5).to_string(index=False))


if __name__ == "__main__":
    main()
