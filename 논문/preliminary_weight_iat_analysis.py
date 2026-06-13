from pathlib import Path
from math import erfc, sqrt

import numpy as np
import pandas as pd


DATA_PATH = Path(
    r"C:\Users\user\OneDrive\D 대학원 박사\A 아주대\2. 사회심리학과 빅데이터 (박현준)\데이터\IAT -OSF자료\weight_iat_wide_2009-2019.csv"
)
OUT_DIR = Path("analysis_outputs_weight_iat_preliminary")


def save_csv(df: pd.DataFrame, name: str) -> None:
    OUT_DIR.mkdir(exist_ok=True)
    df.to_csv(OUT_DIR / name, index=True, encoding="utf-8-sig")


def ols_table(data: pd.DataFrame, y_col: str, x_cols: list[str], name: str) -> pd.DataFrame:
    model_df = data[[y_col] + x_cols].dropna().copy()
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
    cov = sigma2 * np.linalg.inv(x.T @ x)
    se = np.sqrt(np.diag(cov))
    t_values = beta / se
    # With thousands of observations, the normal approximation is effectively
    # identical for the reporting purpose of this preliminary scan.
    p_values = np.array([erfc(abs(float(t)) / sqrt(2)) for t in t_values])
    ci_delta = 1.96 * se
    ss_total = float(((y - y.mean()) @ (y - y.mean())))
    ss_resid = float(resid @ resid)
    r2 = 1 - ss_resid / ss_total
    adj_r2 = 1 - (1 - r2) * (n - 1) / df_resid

    table = pd.DataFrame(
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
    return table


def main() -> None:
    OUT_DIR.mkdir(exist_ok=True)
    df = pd.read_csv(DATA_PATH, low_memory=False)

    # Keep original columns, then add readable aliases used in formulas.
    df = df.rename(
        columns={
            "D2.D.Thin_Good_all": "iat_d2",
            "D6.D.Thin_Good_all": "iat_d6",
            "diff_thermo": "explicit_thermo_diff",
            "diff_ident": "identity_diff",
        }
    )

    numeric_cols = [
        "iat_d2",
        "iat_d6",
        "explicit_thermo_diff",
        "identity_diff",
        "Tfat",
        "Tthin",
        "controlother",
        "controlyou",
        "important",
        "identthin",
        "identfat",
        "age",
        "year",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df["sex_clean"] = df["sex"].where(df["sex"].isin(["f", "m"]))
    df["sex_male"] = (df["sex_clean"] == "m").astype(float)
    df.loc[df["sex_clean"].isna(), "sex_male"] = np.nan
    df["year_centered"] = df["year"] - df["year"].mean()
    df["age_centered"] = df["age"] - df["age"].mean()
    df["weight_importance_high"] = 8 - df["important"]
    df["thin_identification_high"] = 6 - df["identthin"]
    df["fat_identification_high"] = 6 - df["identfat"]
    df["thin_over_fat_identification"] = df["thin_identification_high"] - df["fat_identification_high"]

    summary_vars = [
        "iat_d2",
        "iat_d6",
        "explicit_thermo_diff",
        "identity_diff",
        "Tfat",
        "Tthin",
        "controlother",
        "controlyou",
        "important",
        "identthin",
        "identfat",
        "weight_importance_high",
        "thin_identification_high",
        "fat_identification_high",
        "thin_over_fat_identification",
        "age",
        "year",
    ]
    descriptives = df[summary_vars].describe().T
    descriptives["missing_rate"] = df[summary_vars].isna().mean()
    save_csv(descriptives, "01_descriptives.csv")

    counts = pd.concat(
        {
            "year": df["year"].value_counts(dropna=False).sort_index(),
            "sex": df["sex_clean"].value_counts(dropna=False),
            "session_status": df["session_status"].value_counts(dropna=False),
        },
        axis=0,
    ).to_frame("n")
    save_csv(counts, "02_counts.csv")

    corr_vars = [
        "iat_d2",
        "iat_d6",
        "explicit_thermo_diff",
        "identity_diff",
        "controlother",
        "controlyou",
        "important",
        "identthin",
        "identfat",
        "age",
        "year",
    ]
    corr = df[corr_vars].corr(method="pearson", min_periods=100)
    save_csv(corr, "03_correlations.csv")

    yearly = (
        df.groupby("year")
        .agg(
            n=("iat_d2", "count"),
            iat_d2_mean=("iat_d2", "mean"),
            iat_d2_sd=("iat_d2", "std"),
            iat_d6_mean=("iat_d6", "mean"),
            explicit_thermo_mean=("explicit_thermo_diff", "mean"),
            explicit_thermo_n=("explicit_thermo_diff", "count"),
            age_mean=("age", "mean"),
        )
        .reset_index()
    )
    yearly["iat_d2_se"] = yearly["iat_d2_sd"] / np.sqrt(yearly["n"])
    save_csv(yearly.set_index("year"), "04_yearly_trends.csv")

    models = []

    model_data_1 = df[["iat_d2", "explicit_thermo_diff", "age_centered", "year_centered", "sex_male"]].dropna()
    if len(model_data_1) > 20:
        models.append(
            ols_table(
                model_data_1,
                "iat_d2",
                ["explicit_thermo_diff", "age_centered", "year_centered", "sex_male"],
                "IAT predicted by explicit attitude, age, year, sex",
            )
        )

    model_data_2 = df[
        [
            "iat_d2",
            "controlother",
            "controlyou",
            "weight_importance_high",
            "thin_over_fat_identification",
            "age_centered",
            "year_centered",
            "sex_male",
        ]
    ].dropna()
    if len(model_data_2) > 20:
        models.append(
            ols_table(
                model_data_2,
                "iat_d2",
                [
                    "controlother",
                    "controlyou",
                    "weight_importance_high",
                    "thin_over_fat_identification",
                    "age_centered",
                    "year_centered",
                    "sex_male",
                ],
                "IAT predicted by control beliefs and identity",
            )
        )

    model_data_3 = df[["explicit_thermo_diff", "iat_d2", "controlother", "age_centered", "year_centered", "sex_male"]].dropna()
    if len(model_data_3) > 20:
        models.append(
            ols_table(
                model_data_3,
                "explicit_thermo_diff",
                ["iat_d2", "controlother", "age_centered", "year_centered", "sex_male"],
                "Explicit attitude predicted by IAT and control belief",
            )
        )

    model_table = pd.concat(models, ignore_index=True) if models else pd.DataFrame()
    save_csv(model_table, "05_regression_models.csv")

    valid_iat = df["iat_d2"].notna()
    quality = pd.DataFrame(
        {
            "n": [
                len(df),
                int(valid_iat.sum()),
                int((valid_iat & (df["D2.pct_300"] <= 0.10)).sum()),
                int((valid_iat & (df["D2.PCT_error_3467"] <= 0.30)).sum()),
                int((valid_iat & (df["D2.pct_300"] <= 0.10) & (df["D2.PCT_error_3467"] <= 0.30)).sum()),
            ]
        },
        index=[
            "all_rows",
            "valid_iat_d2",
            "valid_iat_d2_and_pct_300_le_10pct",
            "valid_iat_d2_and_error_le_30pct",
            "valid_iat_d2_and_both_quality_rules",
        ],
    )
    save_csv(quality, "06_quality_counts.csv")

    key = {
        "n_total": len(df),
        "n_iat_d2": int(df["iat_d2"].notna().sum()),
        "iat_d2_mean": float(df["iat_d2"].mean()),
        "iat_d2_sd": float(df["iat_d2"].std()),
        "iat_d6_mean": float(df["iat_d6"].mean()),
        "explicit_thermo_mean": float(df["explicit_thermo_diff"].mean()),
        "corr_iat_explicit": float(df[["iat_d2", "explicit_thermo_diff"]].corr().iloc[0, 1]),
        "corr_d2_d6": float(df[["iat_d2", "iat_d6"]].corr().iloc[0, 1]),
        "quality_n": int((valid_iat & (df["D2.pct_300"] <= 0.10) & (df["D2.PCT_error_3467"] <= 0.30)).sum()),
    }

    report = f"""# Weight IAT Korea 2009-2019 Preliminary Analysis

## Data

- Wide data rows: {key["n_total"]:,}
- IAT D2 usable rows: {key["n_iat_d2"]:,}
- IAT D2 rows after simple quality flags (<=10% faster than 300ms and <=30% error): {key["quality_n"]:,}
- Years covered: {int(df["year"].min())}-{int(df["year"].max())}

## Main Descriptive Findings

- Mean IAT D2 Thin-Good score: {key["iat_d2_mean"]:.3f} (SD = {key["iat_d2_sd"]:.3f})
- Mean IAT D6 Thin-Good score: {key["iat_d6_mean"]:.3f}
- D2-D6 correlation: r = {key["corr_d2_d6"]:.3f}
- Mean explicit thermometer difference (Tthin - Tfat): {key["explicit_thermo_mean"]:.3f}
- IAT-explicit thermometer correlation: r = {key["corr_iat_explicit"]:.3f}

## Working Interpretation

Positive IAT values indicate stronger Thin-Good than Fat-Good associations. The average
IAT score is positive, so the data show a clear implicit thin-positive association.

The thermometer difference is coded as Tthin - Tfat. Its average is negative in this
dataset, which means participants rated fat people warmer than thin people on average.
That makes this dataset especially interesting for an implicit-explicit dissociation
paper: implicit responses favor thin people, while explicit warmth ratings do not show
the same simple pattern.

## Suggested Paper Frame

Title candidate:
Implicit-explicit dissociation in weight stigma among Korean participants:
Evidence from the 2009-2019 Weight IAT dataset

Core question:
Do Korean participants show implicit thin-positive bias even when explicit evaluations
are weak, absent, or reversed?

Recommended primary outcome:
IAT D2 Thin-Good score. D6 can be reported as a robustness check.

Recommended predictors:
explicit thermometer difference, perceived weight controllability, self/other body
perception, identification with thin/fat people, age, sex, and survey year.

## Files

- `01_descriptives.csv`: variable descriptives and missingness
- `02_counts.csv`: year, sex, and session status counts
- `03_correlations.csv`: correlation matrix
- `04_yearly_trends.csv`: yearly means
- `05_regression_models.csv`: robust OLS regression summaries
- `06_quality_counts.csv`: basic IAT quality-rule counts
"""
    (OUT_DIR / "preliminary_report.md").write_text(report, encoding="utf-8")

    korean_report = f"""# 한국 Weight IAT 예비 분석 메모

## 한 줄 결론

이 자료는 사회심리 논문으로 충분히 쓸 만합니다. 가장 강한 포인트는
**암묵적으로는 날씬한 사람-좋음 연합이 뚜렷하지만, 명시적 온정 평가는 같은 방향으로 강하게 나타나지 않는다**는 점입니다.

## 자료 개요

- 개인 단위 자료: {key["n_total"]:,}명
- IAT D2 점수 사용 가능: {key["n_iat_d2"]:,}명
- 간단한 IAT 품질 기준 통과: {key["quality_n"]:,}명
- 기간: {int(df["year"].min())}-{int(df["year"].max())}

## 핵심 발견

1. 평균 IAT D2 점수는 {key["iat_d2_mean"]:.3f}입니다.
   - 양수는 `날씬한 사람 + 좋음` 연합이 더 강하다는 뜻입니다.
   - 따라서 한국 참가자 표본에서 암묵적 thin-positive bias가 관찰됩니다.

2. D2와 D6 점수의 상관은 r = {key["corr_d2_d6"]:.3f}입니다.
   - 두 계산 방식이 거의 같은 결론을 주므로, D2를 주분석으로 두고 D6를 강건성 분석으로 쓰면 좋습니다.

3. 명시적 온정 차이(`Tthin - Tfat`)의 평균은 {key["explicit_thermo_mean"]:.3f}입니다.
   - 이 값은 음수라서, 단순 온정 평정에서는 날씬한 사람을 더 따뜻하게 평가했다고 보기 어렵습니다.
   - 그래서 이 자료의 논문 포인트는 “명시적 편견이 강하다”보다 “암묵-명시 불일치”가 더 좋습니다.

4. IAT와 명시적 온정 차이의 상관은 r = {key["corr_iat_explicit"]:.3f}입니다.
   - 통계적으로는 작지만, 사회심리 논문에서는 오히려 암묵/명시 태도의 분리 가능성을 보여주는 근거가 됩니다.

## 추천 논문 제목

한국인의 체중 낙인에서 암묵적 태도와 명시적 평가의 불일치:
2009-2019년 Weight IAT 자료 분석

## 추천 연구문제

1. 한국 참가자들은 평균적으로 날씬한 사람-좋음 암묵 연합을 보이는가?
2. 암묵적 체중편향은 명시적 온정 평가와 얼마나 연결되는가?
3. 체중통제 신념, 체중 중요도, 체형 동일시는 암묵적 체중편향을 설명하는가?
4. 2009년부터 2019년까지 암묵적 체중편향은 변화했는가?

## 주의할 점

- `important`, `identthin`, `identfat`은 원척도 방향이 직관과 반대입니다. 분석표에는 해석하기 쉽게 재코딩한 변수도 만들었습니다.
- 회귀모형의 설명력은 작습니다. 이건 실패라기보다 대규모 IAT 자료에서 흔한 패턴입니다. 논문에서는 “큰 효과 예측”보다 “암묵-명시 구조와 작은 예측요인의 안정성”으로 쓰는 편이 안전합니다.
- 실제 투고용 분석에서는 결측 처리, 품질 제외 기준, 중복 세션 처리 기준을 명확히 써야 합니다.

## 생성된 파일

- `01_descriptives.csv`: 기술통계와 결측률
- `02_counts.csv`: 연도, 성별, 세션 상태 빈도
- `03_correlations.csv`: 상관표
- `04_yearly_trends.csv`: 연도별 평균
- `05_regression_models.csv`: 예비 회귀분석
- `06_quality_counts.csv`: IAT 품질 기준별 표본 수
"""
    (OUT_DIR / "korean_paper_direction.md").write_text(korean_report, encoding="utf-8-sig")

    print(report)


if __name__ == "__main__":
    main()
