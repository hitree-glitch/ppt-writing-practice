from math import erfc, sqrt
from pathlib import Path

import numpy as np
import pandas as pd
import pyreadstat


DATA_PATH = Path(
    r"C:\Users\user\OneDrive\D 대학원 박사\A 아주대\2. 사회심리학과 빅데이터 (박현준)\데이터\IAT -OSF자료\Korea.Age IAT.public.2006-2017.sav"
)
OUT_DIR = Path("analysis_outputs_korea_age_iat_preliminary")


def save_csv(df: pd.DataFrame, name: str) -> None:
    OUT_DIR.mkdir(exist_ok=True)
    df.to_csv(OUT_DIR / name, encoding="utf-8-sig")


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
    p_values = np.array([erfc(abs(float(t)) / sqrt(2)) for t in t_values])
    ci_delta = 1.96 * se
    ss_total = float(((y - y.mean()) @ (y - y.mean())))
    ss_resid = float(resid @ resid)
    r2 = 1 - ss_resid / ss_total
    adj_r2 = 1 - (1 - r2) * (n - 1) / df_resid

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


def main() -> None:
    OUT_DIR.mkdir(exist_ok=True)
    df, meta = pyreadstat.read_sav(str(DATA_PATH), apply_value_formats=False)

    for col in df.columns:
        if col not in ["sex", "session_status", "study_name", "politicalid_7c"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df["iat_young_good"] = df["D_biep.Young_Good_all"]
    df["explicit_young_preference"] = df["att_7"]
    df["explicit_thermo_diff"] = df["tyoung"] - df["told"]
    df["political_liberal"] = df["politicalid_7"]
    df["sex_male"] = np.where(df["sex"] == "m", 1.0, np.where(df["sex"] == "f", 0.0, np.nan))
    df["year_centered"] = df["year"] - df["year"].mean()
    df["age_centered"] = df["age"] - df["age"].mean()
    df["political_centered"] = df["political_liberal"] - df["political_liberal"].mean()
    df["year_x_politics"] = df["year_centered"] * df["political_centered"]

    summary_vars = [
        "iat_young_good",
        "D_biep.Young_Good_36",
        "D_biep.Young_Good_47",
        "explicit_young_preference",
        "explicit_thermo_diff",
        "tyoung",
        "told",
        "political_liberal",
        "age",
        "year",
        "PCT_error_3467",
        "pct_300",
        "ctoya",
        "atoma",
        "yatoa",
        "matoo",
        "choosetobe",
        "feel",
        "hopetolive",
        "othersthink",
    ]
    descriptives = df[summary_vars].describe().T
    descriptives["missing_rate"] = df[summary_vars].isna().mean()
    save_csv(descriptives, "01_descriptives.csv")

    yearly = (
        df.groupby("year")
        .agg(
            n_iat=("iat_young_good", "count"),
            iat_mean=("iat_young_good", "mean"),
            iat_sd=("iat_young_good", "std"),
            explicit_pref_mean=("explicit_young_preference", "mean"),
            explicit_thermo_mean=("explicit_thermo_diff", "mean"),
            political_mean=("political_liberal", "mean"),
            age_mean=("age", "mean"),
        )
        .reset_index()
    )
    yearly["iat_se"] = yearly["iat_sd"] / np.sqrt(yearly["n_iat"])
    save_csv(yearly.set_index("year"), "02_yearly_trends.csv")

    corr_vars = [
        "iat_young_good",
        "explicit_young_preference",
        "explicit_thermo_diff",
        "political_liberal",
        "age",
        "year",
        "feel",
        "choosetobe",
        "matoo",
    ]
    save_csv(df[corr_vars].corr(min_periods=100), "03_correlations.csv")

    models = [
        ols_table(
            df,
            "iat_young_good",
            ["year_centered", "age_centered", "sex_male", "political_centered"],
            "IAT Young-Good by year, demographics, politics",
        ),
        ols_table(
            df,
            "iat_young_good",
            [
                "year_centered",
                "age_centered",
                "sex_male",
                "political_centered",
                "explicit_young_preference",
                "explicit_thermo_diff",
            ],
            "IAT Young-Good with explicit attitudes",
        ),
        ols_table(
            df,
            "iat_young_good",
            ["year_centered", "age_centered", "sex_male", "political_centered", "year_x_politics"],
            "IAT Young-Good year by politics interaction",
        ),
    ]
    save_csv(pd.concat(models, ignore_index=True), "04_regression_models.csv")

    quality = pd.DataFrame(
        {
            "n": [
                len(df),
                int(df["iat_young_good"].notna().sum()),
                int((df["iat_young_good"].notna() & (df["pct_300"] <= 10)).sum()),
                int((df["iat_young_good"].notna() & (df["PCT_error_3467"] <= 30)).sum()),
                int((df["iat_young_good"].notna() & (df["pct_300"] <= 10) & (df["PCT_error_3467"] <= 30)).sum()),
            ]
        },
        index=[
            "all_rows",
            "valid_iat",
            "valid_iat_and_pct_300_le_10pct",
            "valid_iat_and_error_le_30pct",
            "valid_iat_and_both_quality_rules",
        ],
    )
    save_csv(quality, "05_quality_counts.csv")

    by_politics = (
        df.groupby("political_liberal")
        .agg(n_iat=("iat_young_good", "count"), iat_mean=("iat_young_good", "mean"), explicit_thermo_mean=("explicit_thermo_diff", "mean"))
    )
    save_csv(by_politics, "06_by_political_orientation.csv")

    key = {
        "n_total": len(df),
        "n_iat": int(df["iat_young_good"].notna().sum()),
        "quality_n": int((df["iat_young_good"].notna() & (df["pct_300"] <= 10) & (df["PCT_error_3467"] <= 30)).sum()),
        "iat_mean": float(df["iat_young_good"].mean()),
        "iat_sd": float(df["iat_young_good"].std()),
        "explicit_pref_mean": float(df["explicit_young_preference"].mean()),
        "explicit_thermo_mean": float(df["explicit_thermo_diff"].mean()),
        "corr_iat_explicit_pref": float(df[["iat_young_good", "explicit_young_preference"]].corr().iloc[0, 1]),
        "corr_iat_thermo": float(df[["iat_young_good", "explicit_thermo_diff"]].corr().iloc[0, 1]),
        "corr_iat_politics": float(df[["iat_young_good", "political_liberal"]].corr().iloc[0, 1]),
        "corr_iat_year": float(df[["iat_young_good", "year"]].corr().iloc[0, 1]),
        "corr_iat_age": float(df[["iat_young_good", "age"]].corr().iloc[0, 1]),
    }

    report = f"""# Korea Age IAT 예비 분석 메모

## 한 줄 결론

이 자료는 사용자가 말한 주제, 즉 **한국에서 노인에 대한 IAT가 시점에 따라 달라지는지,
인구통계학적으로 다른지, 정치성향에 따라 차이가 있는지**를 분석하기에 적합합니다.

## 자료 개요

- 전체 표본: {key["n_total"]:,}명
- IAT 점수 사용 가능: {key["n_iat"]:,}명
- 간단한 IAT 품질 기준 통과: {key["quality_n"]:,}명
- 연도 범위: {int(df["year"].min())}-{int(df["year"].max())}

## 핵심 결과

1. 평균 IAT Young-Good 점수는 {key["iat_mean"]:.3f}(SD={key["iat_sd"]:.3f})입니다.
   - 양수는 `젊은 사람 + 좋음` 연합이 `노인 + 좋음` 연합보다 강하다는 뜻입니다.
   - 따라서 평균적으로 **암묵적 친젊음/반노인 편향**이 관찰됩니다.

2. 명시적 직접 선호(`att_7`) 평균은 {key["explicit_pref_mean"]:.3f}입니다.
   - 값의 방향은 코드북 라벨 확인 후 본문에 정확히 적어야 하지만, IAT와 함께 명시 태도 비교가 가능합니다.

3. 명시적 온정 차이(`tyoung - told`) 평균은 {key["explicit_thermo_mean"]:.3f}입니다.
   - 양수라면 젊은 사람을 노인보다 더 따뜻하게 평가한 것입니다.

4. IAT와 명시적 직접 선호의 상관은 r={key["corr_iat_explicit_pref"]:.3f}, IAT와 온정 차이의 상관은 r={key["corr_iat_thermo"]:.3f}입니다.
   - 암묵적 연령주의와 명시적 연령 태도의 일치 정도를 논문 핵심 결과로 쓸 수 있습니다.

5. IAT와 연도의 단순상관은 r={key["corr_iat_year"]:.3f}, IAT와 참가자 연령의 단순상관은 r={key["corr_iat_age"]:.3f}입니다.
   - 연도 변화와 인구통계 차이는 회귀모형에서 더 정교하게 확인하는 것이 좋습니다.

6. IAT와 정치성향(1=보수, 7=진보)의 단순상관은 r={key["corr_iat_politics"]:.3f}입니다.
   - 정치성향에 따른 차이는 단순상관뿐 아니라 연도와의 상호작용까지 보는 설계가 좋습니다.

## 추천 논문 방향

제목 후보:
한국인의 암묵적 연령주의 변화와 정치사회적 예측요인:
2006-2017년 Korea Age IAT 자료 분석

연구문제:
1. 한국 참가자는 평균적으로 젊은 사람을 노인보다 더 긍정적으로 암묵 연합하는가?
2. 암묵적 연령주의는 2006-2017년 동안 변화했는가?
3. 참가자 연령, 성별, 교육수준에 따라 암묵적 연령주의가 다른가?
4. 정치성향에 따라 노인에 대한 암묵적 차별이 다른가?
5. 정치성향과 시점의 상호작용이 있는가?

## 생성된 파일

- `01_descriptives.csv`: 기술통계와 결측률
- `02_yearly_trends.csv`: 연도별 IAT/명시태도 평균
- `03_correlations.csv`: 핵심 변수 상관
- `04_regression_models.csv`: 예비 회귀분석
- `05_quality_counts.csv`: IAT 품질 기준별 표본 수
- `06_by_political_orientation.csv`: 정치성향별 평균
"""
    (OUT_DIR / "korean_paper_direction.md").write_text(report, encoding="utf-8-sig")
    print(report)


if __name__ == "__main__":
    main()
