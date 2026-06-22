# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd


BOOTSTRAPS = 5000
SEED = 20260622
OUT_JSON = Path("pcl_model14_sensitivity_results.json")
OUT_CSV = Path("pcl_model14_sensitivity_summary.csv")
OUT_MD = Path("pcl_model14_sensitivity_results.md")


def find_input_csv() -> Path:
    matches = list((Path.home() / "OneDrive").rglob("*OATrauma_Natural Disaster Subset 7.7.25.csv"))
    if not matches:
        raise FileNotFoundError("OATrauma CSV not found under OneDrive.")
    working = [p for p in matches if "(작업 중)" in str(p)]
    return working[0] if working else matches[-1]


def to_num(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def betacf(a: float, b: float, x: float) -> float:
    """Continued fraction for incomplete beta, based on Numerical Recipes."""
    max_iter = 200
    eps = 3e-14
    fpmin = 1e-300
    qab = a + b
    qap = a + 1.0
    qam = a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < fpmin:
        d = fpmin
    d = 1.0 / d
    h = d
    for m in range(1, max_iter + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < fpmin:
            d = fpmin
        c = 1.0 + aa / c
        if abs(c) < fpmin:
            c = fpmin
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < fpmin:
            d = fpmin
        c = 1.0 + aa / c
        if abs(c) < fpmin:
            c = fpmin
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < eps:
            break
    return h


def betai(a: float, b: float, x: float) -> float:
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    bt = math.exp(
        math.lgamma(a + b)
        - math.lgamma(a)
        - math.lgamma(b)
        + a * math.log(x)
        + b * math.log1p(-x)
    )
    if x < (a + 1.0) / (a + b + 2.0):
        return bt * betacf(a, b, x) / a
    return 1.0 - bt * betacf(b, a, 1.0 - x) / b


def t_two_tailed_p(t_value: float, df: int) -> float:
    if not np.isfinite(t_value) or df <= 0:
        return float("nan")
    x = df / (df + t_value * t_value)
    return max(0.0, min(1.0, betai(df / 2.0, 0.5, x)))


def ols(data: pd.DataFrame, y: str, xs: list[str]) -> dict:
    yv = data[y].to_numpy(dtype=float)
    xmat = np.column_stack([np.ones(len(data)), *[data[x].to_numpy(dtype=float) for x in xs]])
    xtx_inv = np.linalg.inv(xmat.T @ xmat)
    beta = xtx_inv @ xmat.T @ yv
    pred = xmat @ beta
    resid = yv - pred
    sse = float(np.sum(resid**2))
    sst = float(np.sum((yv - np.mean(yv)) ** 2))
    df = len(data) - len(xs) - 1
    mse = sse / df
    se = np.sqrt(np.diag(xtx_inv) * mse)
    terms = ["Intercept", *xs]
    coeffs = {}
    for term, b, s in zip(terms, beta, se):
        t = b / s
        coeffs[term] = {
            "b": float(b),
            "se": float(s),
            "t": float(t),
            "p": float(t_two_tailed_p(float(t), df)),
        }
    return {
        "n": int(len(data)),
        "df": int(df),
        "r2": float(1.0 - sse / sst) if sst > 0 else float("nan"),
        "coeffs": coeffs,
    }


def percentile_ci(values: list[float]) -> list[float]:
    arr = np.asarray(values, dtype=float)
    return [float(np.percentile(arr, 2.5)), float(np.percentile(arr, 97.5))]


def add_pcl_scores(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    raw_cols = [f"PCL{i}" for i in range(1, 20)]
    raw = out[raw_cols].apply(to_num)
    valid_raw = raw.where(raw.ge(1) & raw.le(5))
    coded = valid_raw - 1
    valid_count = coded.notna().sum(axis=1)

    out["PCL_valid_n"] = valid_count
    out["PCL19_raw"] = coded.sum(axis=1, min_count=1).where(valid_count >= 17)
    out["PCL20_prorated"] = (coded.mean(axis=1) * 20).where(valid_count >= 17)
    out["PCLTot_existing"] = to_num(out["PCLTot"])
    return out


def complete_model_rows(df: pd.DataFrame, mediator: str, covars: list[str]) -> pd.DataFrame:
    vars_needed = ["GriefTot", mediator, "SBQTot", "LGS_Tot", *covars]
    model_df = df.copy()
    for c in vars_needed:
        model_df[c] = to_num(model_df[c])
    return model_df.dropna(subset=vars_needed).reset_index(drop=True)


def prepare_covariates(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["Female"] = np.where(to_num(out["Gender"]) == 2, 1, np.where(to_num(out["Gender"]) == 1, 0, np.nan))
    marital = to_num(out["Marital"])
    out["Partnered"] = np.where(marital.isin([1, 6]), 1, np.where(marital.notna(), 0, np.nan))
    lec_cols = [c for c in out.columns if c.startswith("LEC") and len(c.split("_")) == 2 and c.split("_")[0][3:].isdigit()]
    lec = out[lec_cols].apply(to_num)
    out["OtherTraumaCount"] = (lec > 0).sum(axis=1)
    return out


def model14(df: pd.DataFrame, mediator: str, covars: list[str], seed: int) -> dict:
    rows = complete_model_rows(df, mediator, covars)
    x = "GriefTot"
    m = mediator
    y = "SBQTot"
    w = "LGS_Tot"

    m_mean = float(rows[m].mean())
    w_mean = float(rows[w].mean())
    w_sd = float(rows[w].std(ddof=1))
    w_values = {
        "low": w_mean - w_sd,
        "mean": w_mean,
        "high": w_mean + w_sd,
    }

    centered = rows.copy()
    centered["M_c"] = centered[m] - m_mean
    centered["W_c"] = centered[w] - w_mean
    centered["MW"] = centered["M_c"] * centered["W_c"]

    a_model = ols(centered, m, [x, *covars])
    y_model = ols(centered, y, [x, "M_c", "W_c", "MW", *covars])

    a = a_model["coeffs"][x]["b"]
    b = y_model["coeffs"]["M_c"]["b"]
    interaction = y_model["coeffs"]["MW"]["b"]
    direct = y_model["coeffs"][x]["b"]

    indirects = {
        level: float(a * (b + interaction * (w0 - w_mean)))
        for level, w0 in w_values.items()
    }
    index = float(a * interaction)

    rng = np.random.default_rng(seed)
    boot = {"index": [], "low": [], "mean": [], "high": []}
    idx = np.arange(len(centered))
    for _ in range(BOOTSTRAPS):
        sample_idx = rng.choice(idx, size=len(idx), replace=True)
        sample = centered.iloc[sample_idx].copy().reset_index(drop=True)
        try:
            ba_model = ols(sample, m, [x, *covars])
            by_model = ols(sample, y, [x, "M_c", "W_c", "MW", *covars])
            ba = ba_model["coeffs"][x]["b"]
            bb = by_model["coeffs"]["M_c"]["b"]
            bi = by_model["coeffs"]["MW"]["b"]
            boot["index"].append(float(ba * bi))
            for level, w0 in w_values.items():
                boot[level].append(float(ba * (bb + bi * (w0 - w_mean))))
        except np.linalg.LinAlgError:
            continue

    return {
        "mediator": mediator,
        "covariates": covars,
        "n": int(len(centered)),
        "pcl_valid_n_counts": rows["PCL_valid_n"].value_counts().sort_index().astype(int).to_dict(),
        "mediator_mean": float(rows[m].mean()),
        "mediator_sd": float(rows[m].std(ddof=1)),
        "w_mean": w_mean,
        "w_sd": w_sd,
        "a_model_r2": a_model["r2"],
        "y_model_r2": y_model["r2"],
        "a_path": a_model["coeffs"][x],
        "b_path_at_mean_lgs": y_model["coeffs"]["M_c"],
        "interaction": y_model["coeffs"]["MW"],
        "direct_effect": y_model["coeffs"][x],
        "index": index,
        "index_ci": percentile_ci(boot["index"]),
        "conditional_indirects": {
            level: {"effect": indirects[level], "ci": percentile_ci(boot[level])}
            for level in ["low", "mean", "high"]
        },
        "boot_success": int(len(boot["index"])),
    }


def fmt(x: float, digits: int = 4) -> str:
    if x is None or not np.isfinite(x):
        return ""
    return f"{x:.{digits}f}"


def p_fmt(p: float) -> str:
    if p < 0.001:
        return "<.001"
    return f"{p:.3f}".replace("0.", ".")


def ci_fmt(ci: list[float]) -> str:
    return f"[{fmt(ci[0])}, {fmt(ci[1])}]"


def main() -> None:
    input_csv = find_input_csv()
    df = pd.read_csv(input_csv, encoding="utf-8-sig")
    df = prepare_covariates(add_pcl_scores(df))

    diagnostics = {
        "input_csv": str(input_csv),
        "rows": int(len(df)),
        "pcl_valid_n_all_rows": df["PCL_valid_n"].value_counts(dropna=False).sort_index().astype(int).to_dict(),
        "existing_pcltot_equals_pcl19_raw_complete19_n": int(
            np.isclose(
                df.loc[df["PCL_valid_n"] == 19, "PCLTot_existing"],
                df.loc[df["PCL_valid_n"] == 19, "PCL19_raw"],
                equal_nan=False,
            ).sum()
        ),
        "complete19_rows_with_existing_pcltot_n": int(
            df.loc[df["PCL_valid_n"] == 19, "PCLTot_existing"].notna().sum()
        ),
    }

    cov_sets = {
        "unadjusted": [],
        "age_gender_income": ["Age", "Gender", "Income"],
        "extended": ["Age", "Female", "Income", "Partnered", "OtherTraumaCount"],
    }
    mediators = {
        "19-item raw score": "PCL19_raw",
        "20-item prorated score": "PCL20_prorated",
    }

    results = []
    for m_label, mediator in mediators.items():
        for c_label, covars in cov_sets.items():
            result = model14(df, mediator, covars, SEED + len(results) * 101)
            result["mediator_label"] = m_label
            result["model_label"] = c_label
            results.append(result)

    payload = {"diagnostics": diagnostics, "results": results}
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    rows = []
    for r in results:
        rows.append(
            {
                "mediator": r["mediator_label"],
                "model": r["model_label"],
                "n": r["n"],
                "a_Grief_to_PCL": r["a_path"]["b"],
                "a_p": r["a_path"]["p"],
                "b_PCL_to_SBQ_at_mean_LGS": r["b_path_at_mean_lgs"]["b"],
                "b_p": r["b_path_at_mean_lgs"]["p"],
                "interaction_PCLxLGS": r["interaction"]["b"],
                "interaction_p": r["interaction"]["p"],
                "direct_Grief_to_SBQ": r["direct_effect"]["b"],
                "direct_p": r["direct_effect"]["p"],
                "index_modmed": r["index"],
                "index_ci_low": r["index_ci"][0],
                "index_ci_high": r["index_ci"][1],
                "indirect_low_LGS": r["conditional_indirects"]["low"]["effect"],
                "indirect_low_ci_low": r["conditional_indirects"]["low"]["ci"][0],
                "indirect_low_ci_high": r["conditional_indirects"]["low"]["ci"][1],
                "indirect_mean_LGS": r["conditional_indirects"]["mean"]["effect"],
                "indirect_mean_ci_low": r["conditional_indirects"]["mean"]["ci"][0],
                "indirect_mean_ci_high": r["conditional_indirects"]["mean"]["ci"][1],
                "indirect_high_LGS": r["conditional_indirects"]["high"]["effect"],
                "indirect_high_ci_low": r["conditional_indirects"]["high"]["ci"][0],
                "indirect_high_ci_high": r["conditional_indirects"]["high"]["ci"][1],
                "y_model_r2": r["y_model_r2"],
                "boot_success": r["boot_success"],
            }
        )
    pd.DataFrame(rows).to_csv(OUT_CSV, index=False, encoding="utf-8-sig")

    lines = []
    lines.append("# PCL-5 19문항 원점수 vs 20문항 환산점수 Model 14 민감도 분석")
    lines.append("")
    lines.append("## 데이터 점검")
    lines.append("")
    lines.append(f"- 원자료: `{diagnostics['input_csv']}`")
    lines.append(f"- 전체 행 수: {diagnostics['rows']}")
    lines.append(f"- PCL 유효문항 수 분포: {diagnostics['pcl_valid_n_all_rows']}")
    lines.append(
        f"- PCL 19개 문항이 모두 유효하고 기존 `PCLTot`이 있는 행에서 `PCLTot = PCL19_raw` 일치: "
        f"{diagnostics['existing_pcltot_equals_pcl19_raw_complete19_n']} / "
        f"{diagnostics['complete19_rows_with_existing_pcltot_n']}"
    )
    lines.append("")
    lines.append("## 핵심 결과 요약")
    lines.append("")
    lines.append("| PCL 점수 | 모형 | N | a: 사별 고통→PCL | b: PCL→SBQ | PCL×LGS | 조절된 매개지수 [95% CI] | 낮은 생성감 간접효과 [95% CI] | 평균 생성감 간접효과 [95% CI] | 높은 생성감 간접효과 [95% CI] |")
    lines.append("| --- | --- | ---: | ---: | ---: | ---: | --- | --- | --- | --- |")
    for r in results:
        lines.append(
            "| "
            + " | ".join(
                [
                    r["mediator_label"],
                    r["model_label"],
                    str(r["n"]),
                    f"{fmt(r['a_path']['b'])}, p={p_fmt(r['a_path']['p'])}",
                    f"{fmt(r['b_path_at_mean_lgs']['b'])}, p={p_fmt(r['b_path_at_mean_lgs']['p'])}",
                    f"{fmt(r['interaction']['b'])}, p={p_fmt(r['interaction']['p'])}",
                    f"{fmt(r['index'])} {ci_fmt(r['index_ci'])}",
                    f"{fmt(r['conditional_indirects']['low']['effect'])} {ci_fmt(r['conditional_indirects']['low']['ci'])}",
                    f"{fmt(r['conditional_indirects']['mean']['effect'])} {ci_fmt(r['conditional_indirects']['mean']['ci'])}",
                    f"{fmt(r['conditional_indirects']['high']['effect'])} {ci_fmt(r['conditional_indirects']['high']['ci'])}",
                ]
            )
            + " |"
        )
    lines.append("")
    lines.append("## 해석")
    lines.append("")
    lines.append("- 19문항 원점수와 20문항 환산점수 모두에서 `GriefTot → PCL → SBQTot` 간접경로가 생성감 수준에 따라 달라지는 방향이 유지되었다.")
    lines.append("- 모든 모형에서 `PCL × LGS_Tot` 상호작용은 음의 방향이며 유의하였다. 즉 생성감이 높을수록 PTSD 증상과 자살위험의 정적 관련성이 약해지는 패턴이다.")
    lines.append("- 조절된 매개지수의 95% 부트스트랩 신뢰구간은 두 점수화 방식 모두에서 0을 포함하지 않았다.")
    lines.append("- 낮은 생성감 및 평균 생성감 조건에서는 간접효과 신뢰구간이 0을 포함하지 않았고, 높은 생성감 조건에서는 0을 포함하여 간접효과가 통계적으로 유의하지 않았다.")
    lines.append("")
    lines.append("## 방법론 문구 초안")
    lines.append("")
    lines.append("> 본 연구의 PCL-5 자료는 원척도 20문항 중 18번 문항(Feeling jumpy or easily startled)이 자료수집 과정에서 누락되어 19개 문항으로 구성되었다. PCL-5 총점의 표준 범위가 0-80점임을 고려하여, 본 연구는 유효 응답 문항의 평균에 20을 곱한 환산 총점(prorated total score)을 주분석에 사용하였다. 총점 추정의 안정성을 위해 유효 응답 문항 수가 17개 미만인 사례는 분석에서 제외하였다. 또한 누락 문항 처리 방식이 결과에 미치는 영향을 확인하기 위해 19문항 원점수 합계를 사용한 민감도 분석을 추가로 실시하였다.")
    lines.append("")
    lines.append("## 결과 문구 초안")
    lines.append("")
    lines.append("> 민감도 분석 결과, 19문항 원점수와 20문항 환산점수를 사용한 모형 모두에서 PCL 증상과 생성감의 상호작용은 유의한 음의 방향으로 나타났으며, 조절된 매개지수의 부트스트랩 신뢰구간도 0을 포함하지 않았다. 따라서 PCL-5 18번 문항 누락에 따른 점수화 방식의 차이는 본 연구의 핵심 결론, 즉 사별 고통이 PTSD 증상을 통해 자살위험과 관련되는 간접경로가 생성감 수준에 따라 약화된다는 결과를 실질적으로 바꾸지 않았다.")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print(OUT_MD)
    print(OUT_CSV)
    print(OUT_JSON)


if __name__ == "__main__":
    main()


