from math import erfc, sqrt
from pathlib import Path

import numpy as np
import pandas as pd
import pyreadstat


BASE = Path(
    r"C:\Users\user\OneDrive\D 대학원 박사\A 아주대\2. 사회심리학과 빅데이터 (박현준)\데이터\IAT -OSF자료"
)
OUT_DIR = Path("analysis_outputs_iat_domain_comparison")


DATASETS = {
    "age": {
        "path": BASE / "Korea.Age IAT.public.2006-2017.sav",
        "format": "sav",
        "score": "D_biep.Young_Good_all",
        "explicit_pref": "att_7",
        "thermo_a": "tyoung",
        "thermo_b": "told",
        "label": "Age IAT: Young-Good over Old-Good",
    },
    "weight": {
        "path": BASE / "weight_iat_wide_2009-2019.csv",
        "format": "csv",
        "score": "D2.D.Thin_Good_all",
        "pct_300": "D2.pct_300",
        "pct_error": "D2.PCT_error_3467",
        "n_trials": "D2.N_3467",
        "explicit_pref": "att",
        "thermo_a": "Tthin",
        "thermo_b": "Tfat",
        "label": "Weight IAT: Thin-Good over Fat-Good",
    },
    "korea_usa": {
        "path": BASE / "Korea.USA IAT.public.2006-2016.sav",
        "format": "sav",
        "score": "D_biep.Korea_Good_all",
        "explicit_pref": "att_7",
        "thermo_a": "tkorea",
        "thermo_b": "tusa",
        "thermo_b_fallback": "tus",
        "label": "Korea-USA IAT: Korea-Good over USA-Good",
    },
}


def save_csv(df: pd.DataFrame, name: str) -> None:
    OUT_DIR.mkdir(exist_ok=True)
    df.to_csv(OUT_DIR / name, encoding="utf-8-sig", index=True)


def normal_p_from_t(t_values: np.ndarray) -> np.ndarray:
    return np.array([erfc(abs(float(t)) / sqrt(2)) for t in t_values])


def ols_table(data: pd.DataFrame, y_col: str, x_cols: list[str], name: str) -> pd.DataFrame:
    model_df = data[[y_col] + x_cols].replace([np.inf, -np.inf], np.nan).dropna().copy()
    if len(model_df) <= len(x_cols) + 2:
        return pd.DataFrame(
            {
                "term": ["INSUFFICIENT_DATA"],
                "estimate": [np.nan],
                "std_error": [np.nan],
                "t": [np.nan],
                "p": [np.nan],
                "ci_low": [np.nan],
                "ci_high": [np.nan],
                "n": [len(model_df)],
                "r_squared": [np.nan],
                "adj_r_squared": [np.nan],
                "model": [name],
            }
        )
    y = model_df[y_col].to_numpy(dtype=float)
    x = model_df[x_cols].to_numpy(dtype=float)
    x = np.column_stack([np.ones(len(model_df)), x])
    terms = ["Intercept"] + x_cols

    beta, *_ = np.linalg.lstsq(x, y, rcond=None)
    fitted = x @ beta
    resid = y - fitted
    n, k = x.shape
    df_resid = n - k
    sigma2 = float((resid @ resid) / df_resid)
    cov = sigma2 * np.linalg.pinv(x.T @ x)
    se = np.sqrt(np.diag(cov))
    t_values = beta / se
    p_values = normal_p_from_t(t_values)
    ci_delta = 1.96 * se
    ss_total = float(((y - y.mean()) @ (y - y.mean())))
    ss_resid = float(resid @ resid)
    r2 = np.nan if ss_total == 0 else 1 - ss_resid / ss_total
    adj_r2 = np.nan if np.isnan(r2) else 1 - (1 - r2) * (n - 1) / df_resid

    return pd.DataFrame(
        {
            "term": terms,
            "estimate": beta,
            "std_error": se,
            "t": t_values,
            "p": p_values,
            "ci_low": beta - ci_delta,
            "ci_high": beta + ci_delta,
            "n": n,
            "r_squared": r2,
            "adj_r_squared": adj_r2,
            "model": name,
        }
    )


def text_table(df: pd.DataFrame) -> str:
    return df.round(3).to_string()


def load_dataset(domain: str, spec: dict) -> pd.DataFrame:
    if spec["format"] == "sav":
        raw, _ = pyreadstat.read_sav(str(spec["path"]), apply_value_formats=False)
    else:
        raw = pd.read_csv(spec["path"], low_memory=False)

    common = pd.DataFrame(index=raw.index)
    common["domain"] = domain
    common["domain_label"] = spec["label"]
    common["iat_score"] = pd.to_numeric(raw[spec["score"]], errors="coerce")
    common["year"] = pd.to_numeric(raw.get("year"), errors="coerce")
    common["age"] = pd.to_numeric(raw.get("age"), errors="coerce")
    common["sex"] = raw.get("sex")
    common["sex_male"] = np.where(common["sex"] == "m", 1.0, np.where(common["sex"] == "f", 0.0, np.nan))
    common["political_raw"] = pd.to_numeric(raw.get("politicalid_7", raw.get("politicalid")), errors="coerce")
    common["explicit_pref"] = pd.to_numeric(raw.get(spec.get("explicit_pref")), errors="coerce")
    thermo_a = pd.to_numeric(raw.get(spec["thermo_a"]), errors="coerce")
    thermo_b = pd.to_numeric(raw.get(spec["thermo_b"]), errors="coerce")
    if "thermo_b_fallback" in spec:
        thermo_b = thermo_b.fillna(pd.to_numeric(raw.get(spec["thermo_b_fallback"]), errors="coerce"))
    common["explicit_thermo_diff"] = thermo_a - thermo_b

    common["pct_300"] = pd.to_numeric(raw.get(spec.get("pct_300", "pct_300")), errors="coerce")
    common["pct_error"] = pd.to_numeric(raw.get(spec.get("pct_error", "PCT_error_3467")), errors="coerce")
    common["n_trials"] = pd.to_numeric(raw.get(spec.get("n_trials", "N_3467")), errors="coerce")
    common["valid_iat"] = common["iat_score"].notna()
    pct_300_cutoff = 0.10 if common["pct_300"].max(skipna=True) <= 1 else 10
    error_cutoff = 0.30 if common["pct_error"].max(skipna=True) <= 1 else 30
    common["quality_flag"] = (
        common["valid_iat"]
        & (common["pct_300"] <= pct_300_cutoff)
        & (common["pct_error"] <= error_cutoff)
    )

    # Keep only records that have IAT scores for the comparative models.
    common = common[common["valid_iat"]].copy()
    common["iat_z_within_domain"] = common.groupby("domain")["iat_score"].transform(
        lambda s: (s - s.mean()) / s.std()
    )
    return common


def main() -> None:
    OUT_DIR.mkdir(exist_ok=True)
    parts = [load_dataset(domain, spec) for domain, spec in DATASETS.items()]
    long = pd.concat(parts, ignore_index=True)

    long["year_centered"] = long["year"] - long["year"].mean()
    long["age_centered"] = long["age"] - long["age"].mean()
    long["political_centered"] = long["political_raw"] - long["political_raw"].mean()

    for domain in DATASETS:
        long[f"domain_{domain}"] = (long["domain"] == domain).astype(float)
        long[f"year_x_{domain}"] = long["year_centered"] * long[f"domain_{domain}"]
        long[f"age_x_{domain}"] = long["age_centered"] * long[f"domain_{domain}"]
        long[f"male_x_{domain}"] = long["sex_male"] * long[f"domain_{domain}"]
        long[f"politics_x_{domain}"] = long["political_centered"] * long[f"domain_{domain}"]

    save_csv(long, "00_long_iat_domain_data.csv")

    domain_summary = (
        long.groupby("domain")
        .agg(
            label=("domain_label", "first"),
            n=("iat_score", "count"),
            quality_n=("quality_flag", "sum"),
            iat_mean=("iat_score", "mean"),
            iat_sd=("iat_score", "std"),
            iat_median=("iat_score", "median"),
            explicit_thermo_mean=("explicit_thermo_diff", "mean"),
            explicit_thermo_n=("explicit_thermo_diff", "count"),
            age_mean=("age", "mean"),
            political_mean=("political_raw", "mean"),
            first_year=("year", "min"),
            last_year=("year", "max"),
        )
        .sort_values("iat_mean", ascending=False)
    )
    save_csv(domain_summary, "01_domain_summary.csv")

    yearly = (
        long.groupby(["domain", "year"])
        .agg(
            n=("iat_score", "count"),
            iat_mean=("iat_score", "mean"),
            iat_sd=("iat_score", "std"),
            iat_z_mean=("iat_z_within_domain", "mean"),
            explicit_thermo_mean=("explicit_thermo_diff", "mean"),
            age_mean=("age", "mean"),
            political_mean=("political_raw", "mean"),
        )
        .reset_index()
    )
    yearly["iat_se"] = yearly["iat_sd"] / np.sqrt(yearly["n"])
    save_csv(yearly.set_index(["domain", "year"]), "02_yearly_by_domain.csv")

    demo = (
        long.assign(age_group=pd.cut(long["age"], bins=[0, 19, 29, 39, 49, 120], labels=["<=19", "20s", "30s", "40s", "50+"])),
        long
    )[0]
    demo_summary = (
        demo.groupby(["domain", "sex", "age_group"], observed=True)
        .agg(n=("iat_score", "count"), iat_mean=("iat_score", "mean"), iat_z_mean=("iat_z_within_domain", "mean"))
    )
    save_csv(demo_summary, "03_demographic_group_summary.csv")

    politics_summary = (
        long.groupby(["domain", "political_raw"])
        .agg(n=("iat_score", "count"), iat_mean=("iat_score", "mean"), iat_z_mean=("iat_z_within_domain", "mean"))
    )
    save_csv(politics_summary, "04_political_group_summary.csv")

    corr = (
        long.groupby("domain")[["iat_score", "iat_z_within_domain", "explicit_thermo_diff", "age", "year", "political_raw"]]
        .corr(min_periods=100)
    )
    save_csv(corr, "05_correlations_by_domain.csv")

    # Pooled comparison with age domain as the reference. Weight and Korea-USA
    # domain coefficients show mean differences relative to Age IAT.
    pooled = long.copy()
    pooled["is_weight"] = (pooled["domain"] == "weight").astype(float)
    pooled["is_korea_usa"] = (pooled["domain"] == "korea_usa").astype(float)
    model_tables = []
    model_tables.append(
        ols_table(
            pooled,
            "iat_score",
            ["is_weight", "is_korea_usa"],
            "Raw IAT mean difference by domain; reference=Age",
        )
    )
    model_tables.append(
        ols_table(
            pooled,
            "iat_z_within_domain",
            [
                "age_centered",
                "sex_male",
                "political_centered",
                "year_centered",
                "age_x_weight",
                "age_x_korea_usa",
                "male_x_weight",
                "male_x_korea_usa",
                "politics_x_weight",
                "politics_x_korea_usa",
                "year_x_weight",
                "year_x_korea_usa",
            ],
            "Standardized IAT predictors and domain interactions; reference=Age",
        )
    )
    for domain in DATASETS:
        d = long[long["domain"] == domain]
        model_tables.append(
            ols_table(
                d,
                "iat_score",
                ["age_centered", "sex_male", "political_centered", "year_centered", "explicit_thermo_diff"],
                f"Within-domain raw IAT predictors: {domain}",
            )
        )
    save_csv(pd.concat(model_tables, ignore_index=True), "06_regression_models.csv")

    top = domain_summary[["n", "quality_n", "iat_mean", "iat_sd", "explicit_thermo_mean", "first_year", "last_year"]]
    report = f"""# IAT Domain Comparison Preliminary Analysis

## What Was Combined

This analysis stacks three Korean IAT datasets into one long-format table:

- Age IAT: higher scores mean stronger Young-Good than Old-Good associations.
- Weight IAT: higher scores mean stronger Thin-Good than Fat-Good associations.
- Korea-USA IAT: higher scores mean stronger Korea-Good than USA-Good associations.

The datasets were not person-matched because usable user identifiers barely overlap.
This is a domain-comparison analysis, not a within-person multi-IAT analysis.

## Domain Means

{text_table(top)}

## Main Interpretation

Age IAT shows the largest average D score among the three domains, followed by
Korea-USA IAT, then Weight IAT. That means the strongest average automatic association
in these public Korean datasets is Young-Good over Old-Good.

This makes a useful paper frame:
not just whether ageism exists, but whether age-related implicit bias is unusually
strong compared with other socially meaningful IAT domains in the same Korean public
IAT archive.

## Suggested Paper Frame

Title candidate:
Comparing implicit biases in Korea: Age, body weight, and national-group IAT evidence

Core question:
Is implicit age bias stronger than other public IAT domains in Korean samples, and do
demographic/political predictors generalize across bias domains?

## Generated Files

- `00_long_iat_domain_data.csv`: stacked analytic data
- `01_domain_summary.csv`: domain-level means
- `02_yearly_by_domain.csv`: yearly trends by domain
- `03_demographic_group_summary.csv`: sex and age-group summaries
- `04_political_group_summary.csv`: political-orientation summaries
- `05_correlations_by_domain.csv`: within-domain correlations
- `06_regression_models.csv`: pooled and within-domain regressions
"""
    (OUT_DIR / "preliminary_report.md").write_text(report, encoding="utf-8")

    korean = f"""# 한국 IAT 영역 비교 예비 분석 메모

## 결론

Age IAT, Weight IAT, Korea-USA IAT를 개인 단위로 직접 매칭하기는 어렵습니다.
대신 세 자료를 같은 형식으로 세로로 붙여 **편향 영역 비교**를 할 수 있습니다.

## 핵심 결과

세 영역의 평균 IAT D점수는 다음과 같습니다.

{text_table(top)}

해석하면, 평균 D점수는 **Age IAT가 가장 큽니다**. 즉 이 자료들 안에서는
`젊은 사람-좋음 / 노인-나쁨` 자동 연합이 `날씬함-좋음`이나 `한국-좋음` 연합보다
평균적으로 더 강하게 나타납니다.

## 기존 노인 IAT 논문과 덜 겹치는 방향

기존 주제가 “Age IAT 안에서 시점, 인구통계, 정치성향 차이”라면,
새 주제는 이렇게 잡는 편이 좋습니다.

**한국 사회의 암묵편향은 대상 영역에 따라 다르게 나타나는가:
연령, 체중, 국가집단 IAT 비교**

이 주제는 Age IAT 하나만 보는 것이 아니라, 연령주의가 다른 암묵편향 영역과 비교해
얼마나 강한지 묻습니다. 그래서 기존 논문과 덜 겹칩니다.

## 연구문제

1. 한국 IAT 자료에서 가장 강한 평균 암묵연합은 어느 영역에서 나타나는가?
2. 연령주의 IAT는 체중 IAT와 국가집단 IAT보다 강한가?
3. 성별, 참가자 연령, 정치성향 효과는 모든 IAT 영역에 공통으로 나타나는가?
4. 명시 태도와 암묵 태도의 연결은 영역별로 다른가?

## 주의점

- 개인 단위 매칭 연구가 아닙니다. 같은 사람이 세 IAT를 모두 한 자료가 아니기 때문입니다.
- Korea-USA IAT는 “차별”보다는 국가집단 선호/내집단 선호로 표현하는 것이 안전합니다.
- D점수는 서로 비교 가능하지만, 각 IAT의 자극과 과제 맥락이 다르므로 효과 크기 비교는 조심스럽게 해석해야 합니다.

## 파일

- `00_long_iat_domain_data.csv`: 세 자료를 합친 분석용 long data
- `01_domain_summary.csv`: 영역별 평균
- `02_yearly_by_domain.csv`: 영역별 연도 추세
- `03_demographic_group_summary.csv`: 성별/연령대별 평균
- `04_political_group_summary.csv`: 정치성향별 평균
- `05_correlations_by_domain.csv`: 영역별 상관
- `06_regression_models.csv`: 통합 및 영역별 회귀분석
"""
    (OUT_DIR / "korean_paper_direction.md").write_text(korean, encoding="utf-8-sig")
    print(korean)


if __name__ == "__main__":
    main()
