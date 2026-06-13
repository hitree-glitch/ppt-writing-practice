from math import erfc, sqrt
from pathlib import Path

import numpy as np
import pandas as pd
import pyreadstat


DATA_PATH = Path(
    r"C:\Users\user\OneDrive\D 대학원 박사\A 아주대\2. 사회심리학과 빅데이터 (박현준)\데이터\IAT -OSF자료\Korea.USA IAT.public.2006-2016.sav"
)
OUT_DIR = Path("analysis_outputs_korea_usa_iat_preliminary")


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


def reverse_1_to_7(s: pd.Series) -> pd.Series:
    return 8 - s


def main() -> None:
    OUT_DIR.mkdir(exist_ok=True)
    df, meta = pyreadstat.read_sav(str(DATA_PATH), apply_value_formats=False)

    for col in df.columns:
        if col not in ["sex", "politicalid_7c", "session_status", "study_name"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df["iat_korea_good"] = df["D_biep.Korea_Good_all"]
    df["explicit_korea_preference"] = df["att_7"]
    df["explicit_thermo_diff"] = df["tkorea"] - df["tusa"].fillna(df["tus"])
    df["political_liberal"] = df["politicalid_7"]
    df["sex_male"] = np.where(df["sex"] == "m", 1.0, np.where(df["sex"] == "f", 0.0, np.nan))
    df["year_centered"] = df["year"] - df["year"].mean()
    df["age_centered"] = df["age"] - df["age"].mean()
    df["political_centered"] = df["political_liberal"] - df["political_liberal"].mean()

    rwa_pro = ["rwaz1", "rwaz3", "rwaz5", "rwaz6", "rwaz7", "rwaz9", "rwaz11", "rwaz13", "rwaz15"]
    rwa_rev = ["rwaz2", "rwaz4", "rwaz8", "rwaz10", "rwaz12", "rwaz14"]
    sdo_pro = ["sdo1", "sdo2", "sdo3", "sdo4", "sdo5", "sdo6", "sdo7"]
    sdo_rev = ["sdo8", "sdo9", "sdo10", "sdo11", "sdo12"]

    if all(c in df.columns for c in rwa_pro + rwa_rev):
        df["rwa_mean"] = pd.concat([df[rwa_pro], df[rwa_rev].apply(reverse_1_to_7)], axis=1).mean(axis=1)
    if all(c in df.columns for c in sdo_pro + sdo_rev):
        df["sdo_mean"] = pd.concat([df[sdo_pro], df[sdo_rev].apply(reverse_1_to_7)], axis=1).mean(axis=1)

    summary_vars = [
        "iat_korea_good",
        "D_biep.Korea_Good_36",
        "D_biep.Korea_Good_47",
        "explicit_korea_preference",
        "explicit_thermo_diff",
        "tkorea",
        "tusa",
        "political_liberal",
        "rwa_mean",
        "sdo_mean",
        "age",
        "year",
        "PCT_error_3467",
        "pct_300",
    ]
    summary_vars = [c for c in summary_vars if c in df.columns]
    descriptives = df[summary_vars].describe().T
    descriptives["missing_rate"] = df[summary_vars].isna().mean()
    save_csv(descriptives, "01_descriptives.csv")

    yearly = (
        df.groupby("year")
        .agg(
            n_iat=("iat_korea_good", "count"),
            iat_mean=("iat_korea_good", "mean"),
            iat_sd=("iat_korea_good", "std"),
            explicit_pref_mean=("explicit_korea_preference", "mean"),
            explicit_thermo_mean=("explicit_thermo_diff", "mean"),
            political_mean=("political_liberal", "mean"),
            age_mean=("age", "mean"),
        )
        .reset_index()
    )
    yearly["iat_se"] = yearly["iat_sd"] / np.sqrt(yearly["n_iat"])
    save_csv(yearly.set_index("year"), "02_yearly_trends.csv")

    corr_vars = [
        "iat_korea_good",
        "explicit_korea_preference",
        "explicit_thermo_diff",
        "political_liberal",
        "rwa_mean",
        "sdo_mean",
        "age",
        "year",
    ]
    corr_vars = [c for c in corr_vars if c in df.columns]
    save_csv(df[corr_vars].corr(min_periods=100), "03_correlations.csv")

    models = []
    base_x = ["year_centered", "age_centered", "sex_male", "political_centered"]
    models.append(ols_table(df, "iat_korea_good", base_x, "IAT Korea-Good by year, demographics, politics"))
    models.append(
        ols_table(
            df,
            "iat_korea_good",
            base_x + ["explicit_korea_preference", "explicit_thermo_diff"],
            "IAT Korea-Good with explicit attitudes",
        )
    )
    if "rwa_mean" in df.columns and "sdo_mean" in df.columns:
        models.append(
            ols_table(
                df,
                "iat_korea_good",
                base_x + ["rwa_mean", "sdo_mean"],
                "IAT Korea-Good with RWA and SDO",
            )
        )
    save_csv(pd.concat(models, ignore_index=True), "04_regression_models.csv")

    quality = pd.DataFrame(
        {
            "n": [
                len(df),
                int(df["iat_korea_good"].notna().sum()),
                int((df["iat_korea_good"].notna() & (df["pct_300"] <= 10)).sum()),
                int((df["iat_korea_good"].notna() & (df["PCT_error_3467"] <= 30)).sum()),
                int((df["iat_korea_good"].notna() & (df["pct_300"] <= 10) & (df["PCT_error_3467"] <= 30)).sum()),
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

    key = {
        "n_total": len(df),
        "n_iat": int(df["iat_korea_good"].notna().sum()),
        "quality_n": int((df["iat_korea_good"].notna() & (df["pct_300"] <= 10) & (df["PCT_error_3467"] <= 30)).sum()),
        "iat_mean": float(df["iat_korea_good"].mean()),
        "iat_sd": float(df["iat_korea_good"].std()),
        "explicit_pref_mean": float(df["explicit_korea_preference"].mean()),
        "explicit_thermo_mean": float(df["explicit_thermo_diff"].mean()),
        "corr_iat_explicit_pref": float(df[["iat_korea_good", "explicit_korea_preference"]].corr().iloc[0, 1]),
        "corr_iat_thermo": float(df[["iat_korea_good", "explicit_thermo_diff"]].corr().iloc[0, 1]),
        "corr_iat_politics": float(df[["iat_korea_good", "political_liberal"]].corr().iloc[0, 1]),
    }

    report = f"""# Korea-USA IAT 예비 분석 메모

## 한 줄 결론

이 자료는 노인 IAT가 아니라 **한국-미국 국가집단 IAT**입니다. 사회심리 논문으로는 충분히 좋고,
특히 **국가정체성, 친한국/친미 태도, 정치성향, 권위주의(RWA), 사회지배성향(SDO)**을 함께 볼 수 있다는 장점이 큽니다.

## 자료 개요

- 전체 표본: {key["n_total"]:,}명
- IAT 점수 사용 가능: {key["n_iat"]:,}명
- 간단한 IAT 품질 기준 통과: {key["quality_n"]:,}명
- 연도 범위: {int(df["year"].min())}-{int(df["year"].max())}

## 핵심 결과

1. 평균 IAT Korea-Good 점수는 {key["iat_mean"]:.3f}(SD={key["iat_sd"]:.3f})입니다.
   - 양수는 `한국 + 좋음` 연합이 `미국 + 좋음` 연합보다 강하다는 뜻입니다.
   - 즉, 암묵 수준에서는 한국 선호가 꽤 뚜렷합니다.

2. 명시적 직접 선호(`att_7`) 평균은 {key["explicit_pref_mean"]:.3f}입니다.
   - 1=미국 매우 선호, 4=동일 선호, 7=한국 매우 선호이므로, 명시적으로도 한국 쪽 선호가 있습니다.

3. 명시적 온정 차이(`tkorea - 미국 온정`) 평균은 {key["explicit_thermo_mean"]:.3f}입니다.
   - 한국을 미국보다 더 따뜻하게 평가하는 경향입니다.

4. IAT와 명시적 직접 선호의 상관은 r={key["corr_iat_explicit_pref"]:.3f}, IAT와 온정 차이의 상관은 r={key["corr_iat_thermo"]:.3f}입니다.
   - 암묵 태도와 명시 태도는 관련은 있지만 완전히 같은 것은 아닙니다.

5. IAT와 정치성향(1=보수, 7=진보)의 단순상관은 r={key["corr_iat_politics"]:.3f}입니다.
   - 정치성향 효과는 단순상관만으로는 크지 않아 보입니다. 회귀와 상호작용으로 더 정교하게 봐야 합니다.

## 추천 논문 방향

제목 후보:
한국인의 국가집단 암묵태도와 정치심리적 예측요인:
2006-2017년 Korea-USA IAT 자료 분석

연구문제:
1. 한국 참가자는 한국-미국 중 어느 집단을 더 긍정적으로 암묵 연합하는가?
2. 이 암묵적 국가 선호는 시점에 따라 변화했는가?
3. 정치성향, 권위주의, 사회지배성향은 한국-미국 암묵 선호를 예측하는가?
4. 암묵적 국가 선호와 명시적 국가 선호는 얼마나 일치하는가?

## 주의할 점

- 파일명은 2006-2016이지만 실제 `year`에는 2017도 포함되어 있습니다. 분석에서 2017을 포함할지 제외할지 결정해야 합니다.
- `tus`는 사례 수가 적고, 대부분은 `tusa`에 미국 온정 점수가 있습니다. 분석에서는 `tusa`를 우선 사용하고 `tus`는 보조로 합쳤습니다.
- 정치성향은 `politicalid_7`을 쓰는 것이 안전합니다. 1=매우 보수, 7=매우 진보입니다.

## 생성된 파일

- `01_descriptives.csv`: 기술통계와 결측률
- `02_yearly_trends.csv`: 연도별 IAT/명시태도 평균
- `03_correlations.csv`: 핵심 변수 상관
- `04_regression_models.csv`: 예비 회귀분석
- `05_quality_counts.csv`: IAT 품질 기준별 표본 수
"""
    (OUT_DIR / "korean_paper_direction.md").write_text(report, encoding="utf-8-sig")
    print(report)


if __name__ == "__main__":
    main()
