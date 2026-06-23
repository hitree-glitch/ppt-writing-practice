from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

ROOT = Path("RESEARCH/korea_ai_counseling_psych_20260623")
TEXT = ROOT / "artifacts" / "extracted_text"
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "processed"
DOCS = ROOT / "outputs"

OUT.mkdir(parents=True, exist_ok=True)
DOCS.mkdir(parents=True, exist_ok=True)

DIGITAL_DIVIDE_FILES = {
    2025: "digital_divide_2025_29168_file1.txt",
    2024: "digital_divide_2024_27832_file1.txt",
    2023: "digital_divide_2023_26517_file2.txt",
}


def page_map(path: Path) -> dict[int, str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    chunks = re.split(r"\n\n--- page (\d+) ---\n", text)
    return {int(chunks[i]): chunks[i + 1] for i in range(1, len(chunks), 2)}


def flat(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def quote(text: str, max_len: int = 260) -> str:
    text = flat(text)
    return text[:max_len]


def extract_ai_experience_panel() -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    pattern = re.compile(
        r"(?P<group>장애인|고령층|저소득층|농어민|북한이탈주민|결혼이민자)의 경험률은 "
        r"(?P<group_rate>\d+(?:\.\d+)?)%로 일반\s*국\s*민 (?P<general_rate>\d+(?:\.\d+)?)%"
        r"\s*보다 (?P<gap>\d+(?:\.\d+)?)%p (?P<direction>낮음|높음)"
    )
    for year, filename in DIGITAL_DIVIDE_FILES.items():
        pages = page_map(TEXT / filename)
        for page_no, text in pages.items():
            compact = flat(text)
            if "인공지능 서비스 경험률" not in compact and "인공지능(AI) 서비스 이용 경험" not in compact:
                continue
            for match in pattern.finditer(compact):
                group_rate = float(match.group("group_rate"))
                general_rate = float(match.group("general_rate"))
                signed_gap = group_rate - general_rate
                rows.append(
                    {
                        "year": year,
                        "dataset": "NIA 디지털정보격차실태조사",
                        "source_file": f"data/raw/{filename.replace('.txt', '.pdf')}",
                        "page": page_no,
                        "group": match.group("group"),
                        "ai_experience_rate": group_rate,
                        "general_public_rate": general_rate,
                        "gap_vs_general_pp": round(signed_gap, 1),
                        "reported_gap_abs_pp": float(match.group("gap")),
                        "reported_direction": match.group("direction"),
                        "unit": "%",
                        "extraction_status": "본문 문장 자동 추출",
                        "evidence_snippet": quote(compact),
                    }
                )
    df = pd.DataFrame(rows).drop_duplicates(["year", "group", "ai_experience_rate"])
    order = ["장애인", "고령층", "저소득층", "농어민", "북한이탈주민", "결혼이민자"]
    df["group_order"] = df["group"].map({g: i for i, g in enumerate(order)})
    return df.sort_values(["year", "group_order"]).drop(columns=["group_order"]).reset_index(drop=True)


def build_ai_service_summary() -> pd.DataFrame:
    rows = [
        # 2025 aggregate vulnerable-class AI service metrics.
        (2025, 322, "취약계층", "any_ai_service_awareness", "인공지능 서비스 8개 항목 중 하나라도 인지", None, 76.6),
        (2025, 322, "취약계층", "no_ai_service_awareness", "알고 있는 인공지능 서비스 없음", None, 23.4),
        (2025, 322, "취약계층", "service_awareness", "AI 서비스별 인지율", "주거 편의", 61.3),
        (2025, 322, "취약계층", "service_awareness", "AI 서비스별 인지율", "교통", 53.4),
        (2025, 322, "취약계층", "service_awareness", "AI 서비스별 인지율", "AI 기반 대화형 정보검색", 47.2),
        (2025, 322, "취약계층", "service_awareness", "AI 서비스별 인지율", "커뮤니케이션/친교", 39.6),
        (2025, 323, "취약계층", "service_experience_among_awared", "인지자 기준 최근 한 달 사용 경험률", "AI 기반 대화형 정보검색", 38.5),
        (2025, 323, "취약계층", "service_experience_among_awared", "인지자 기준 최근 한 달 사용 경험률", "교통", 25.0),
        (2025, 323, "취약계층", "service_experience_among_awared", "인지자 기준 최근 한 달 사용 경험률", "주거 편의", 23.8),
        (2025, 323, "취약계층", "service_experience_among_awared", "인지자 기준 최근 한 달 사용 경험률", "미디어", 23.5),
        (2025, 324, "취약계층", "service_helpfulness", "도움 정도 긍정 응답률", "주거 편의", 64.4),
        (2025, 324, "취약계층", "service_helpfulness", "도움 정도 긍정 응답률", "교통", 55.0),
        (2025, 324, "취약계층", "service_helpfulness", "도움 정도 긍정 응답률", "헬스케어", 48.9),
        (2025, 324, "취약계층", "service_helpfulness", "도움 정도 긍정 응답률", "커뮤니케이션/친교", 46.9),
        (2025, 324, "취약계층", "service_helpfulness", "도움 정도 긍정 응답률", "AI 기반 대화형 정보검색", 46.5),
        (2025, 325, "저소득층", "nonuse_reason", "AI 서비스 비이용 이유: 이용할 필요성이 없어서", None, 62.0),
        (2025, 325, "장애인", "nonuse_reason", "AI 서비스 비이용 이유: 신체적 제약으로 이용이 어려워서", None, 17.8),
        (2025, 325, "고령층", "nonuse_reason", "AI 서비스 비이용 이유: 아직 AI에 대해 잘 몰라서", None, 60.9),
        (2025, 325, "고령층", "nonuse_reason", "AI 서비스 비이용 이유: 이용 방법이 어려워서", None, 47.4),
        (2025, 325, "고령층", "nonuse_reason", "AI 서비스 비이용 이유: 기술에 대한 거부감이 있어서", None, 19.8),
        # 2024 aggregate vulnerable-class AI service metrics.
        (2024, 318, "취약계층", "any_ai_service_awareness", "인공지능 서비스 8개 항목 중 하나라도 인지", None, 74.9),
        (2024, 318, "취약계층", "no_ai_service_awareness", "알고 있는 인공지능 서비스 없음", None, 25.1),
        (2024, 318, "취약계층", "service_awareness", "AI 서비스별 인지율", "주거 편의", 64.5),
        (2024, 318, "취약계층", "service_awareness", "AI 서비스별 인지율", "교통", 54.4),
        (2024, 318, "취약계층", "service_awareness", "AI 서비스별 인지율", "AI 기반 대화형 정보검색", 38.9),
        (2024, 318, "취약계층", "service_awareness", "AI 서비스별 인지율", "커뮤니케이션/친교", 36.3),
        (2024, 319, "취약계층", "service_experience_among_awared", "인지자 기준 최근 한 달 사용 경험률", "미디어", 27.2),
        (2024, 319, "취약계층", "service_experience_among_awared", "인지자 기준 최근 한 달 사용 경험률", "주거 편의", 25.7),
        (2024, 319, "취약계층", "service_experience_among_awared", "인지자 기준 최근 한 달 사용 경험률", "교통", 25.2),
        (2024, 319, "취약계층", "service_experience_among_awared", "인지자 기준 최근 한 달 사용 경험률", "금융", 21.2),
        (2024, 320, "취약계층", "service_helpfulness", "도움 정도 긍정 응답률", "주거 편의", 63.9),
        (2024, 320, "취약계층", "service_helpfulness", "도움 정도 긍정 응답률", "교통", 55.2),
        (2024, 320, "취약계층", "service_helpfulness", "도움 정도 긍정 응답률", "커뮤니케이션/친교", 44.3),
        (2024, 320, "취약계층", "service_helpfulness", "도움 정도 긍정 응답률", "헬스케어", 43.8),
        (2024, 320, "취약계층", "service_helpfulness", "도움 정도 긍정 응답률", "미디어", 37.4),
    ]
    df = pd.DataFrame(
        rows,
        columns=["year", "page", "group", "metric", "metric_label", "service", "value"],
    )
    df["dataset"] = "NIA 디지털정보격차실태조사"
    df["unit"] = "%"
    df["extraction_status"] = "본문 서술 기반 구조화"
    return df


def build_smartphone_summary() -> pd.DataFrame:
    rows = [
        (2025, 50, "전체", 22.7, 4.1, 18.6),
        (2024, 48, "전체", 22.9, 4.2, 18.7),
        (2023, 50, "전체", 23.1, 4.2, 18.9),
    ]
    target_rows = [
        (2025, 50, "유아동", 26.0),
        (2025, 50, "청소년", 43.0),
        (2025, 50, "성인 청년층", 29.5),
        (2025, 50, "성인 중년층", 16.6),
        (2025, 50, "60대", 11.5),
        (2024, 48, "유아동", 25.9),
        (2024, 48, "청소년", 42.6),
        (2024, 48, "성인", 22.4),
        (2024, 48, "60대", 11.9),
        (2023, 50, "유아동", 25.0),
        (2023, 50, "청소년", 40.1),
        (2023, 50, "성인", 22.7),
        (2023, 50, "60대", 13.5),
    ]
    total = pd.DataFrame(rows, columns=["year", "page", "target_group", "overdependence_risk_rate", "high_risk_rate", "potential_risk_rate"])
    target = pd.DataFrame(target_rows, columns=["year", "page", "target_group", "overdependence_risk_rate"])
    for col in ["high_risk_rate", "potential_risk_rate"]:
        target[col] = None
    df = pd.concat([total, target], ignore_index=True)
    df["dataset"] = "NIA 스마트폰 과의존 실태조사"
    df["unit"] = "%"
    df["extraction_status"] = "본문 서술 기반 구조화"
    return df


def build_smartphone_psych_harm_2025() -> pd.DataFrame:
    factor_rows = [
        ("유아동", 73, "조절실패", 2.77, 2.43),
        ("유아동", 73, "현저성", 3.18, 2.46),
        ("유아동", 73, "문제적 결과", 2.71, 1.96),
        ("청소년", 73, "조절실패", 3.03, 2.10),
        ("청소년", 73, "현저성", 2.84, 1.87),
        ("청소년", 73, "문제적 결과", 2.44, 1.72),
        ("성인", 73, "조절실패", 2.90, 1.94),
        ("성인", 73, "현저성", 2.80, 1.73),
        ("성인", 73, "문제적 결과", 2.48, 1.59),
        ("60대", 73, "조절실패", 2.78, 1.67),
        ("60대", 73, "현저성", 2.67, 1.55),
        ("60대", 73, "문제적 결과", 2.56, 1.43),
    ]
    harm_rows = [
        ("유아동", 78, "스마트폰 이용 때문에 아이와 자주 싸운다", 61.8, 14.6, 2.69, 1.99),
        ("유아동", 78, "스마트폰을 하느라 다른 놀이나 학습에 지장이 있다", 62.2, 14.0, 2.67, 1.98),
        ("유아동", 78, "스마트폰 이용으로 인해 시력/자세가 안 좋아진다", 65.4, 12.8, 2.78, 1.93),
        ("청소년", 82, "스마트폰 이용 때문에 건강에 문제가 생긴 적이 있다", 42.5, 6.6, 2.44, 1.63),
        ("청소년", 82, "스마트폰 이용 때문에 가족과 심하게 다툰 적이 있다", 54.3, 12.6, 2.58, 1.74),
        ("청소년", 82, "스마트폰 이용 때문에 친구/동료/사회적 관계에서 심한 갈등을 경험한 적이 있다", 31.9, 8.3, 2.26, 1.71),
        ("청소년", 82, "스마트폰 때문에 업무/학업 수행에 어려움이 있다", 47.0, 10.4, 2.46, 1.80),
        ("성인", 86, "스마트폰 이용 때문에 건강에 문제가 생긴 적이 있다", 55.7, 9.3, 2.62, 1.66),
        ("성인", 86, "스마트폰 이용 때문에 가족과 심하게 다툰 적이 있다", 46.4, 5.2, 2.46, 1.57),
        ("성인", 86, "스마트폰 이용 때문에 친구/동료/사회적 관계에서 심한 갈등을 경험한 적이 있다", 39.2, 3.5, 2.37, 1.56),
        ("성인", 86, "스마트폰 때문에 업무/학업 수행에 어려움이 있다", 47.8, 3.5, 2.46, 1.57),
        ("60대", 90, "스마트폰 이용 때문에 건강에 문제가 생긴 적이 있다", 52.1, 4.4, 2.58, 1.50),
        ("60대", 90, "스마트폰 이용 때문에 가족과 심하게 다툰 적이 있다", 46.4, 1.8, 2.46, 1.41),
        ("60대", 90, "스마트폰 이용 때문에 친구/동료/사회적 관계에서 심한 갈등을 경험한 적이 있다", 53.9, 1.7, 2.70, 1.42),
        ("60대", 90, "스마트폰 때문에 업무/학업 수행에 어려움이 있다", 52.7, 1.1, 2.49, 1.41),
    ]
    factor_df = pd.DataFrame(factor_rows, columns=["target_group", "page", "indicator", "overdependence_risk_group_score", "general_user_score"])
    factor_df["indicator_type"] = "과의존 요인 점수"
    factor_df["positive_rate_overdependence"] = None
    factor_df["positive_rate_general_user"] = None
    harm_df = pd.DataFrame(
        harm_rows,
        columns=[
            "target_group",
            "page",
            "indicator",
            "positive_rate_overdependence",
            "positive_rate_general_user",
            "overdependence_risk_group_score",
            "general_user_score",
        ],
    )
    harm_df["indicator_type"] = "문제적 결과 문항"
    df = pd.concat([factor_df, harm_df], ignore_index=True)
    df["year"] = 2025
    df["dataset"] = "NIA 스마트폰 과의존 실태조사"
    df["rate_gap_pp"] = df.apply(
        lambda r: None
        if pd.isna(r["positive_rate_overdependence"]) or pd.isna(r["positive_rate_general_user"])
        else round(float(r["positive_rate_overdependence"]) - float(r["positive_rate_general_user"]), 1),
        axis=1,
    )
    df["score_gap"] = (df["overdependence_risk_group_score"].astype(float) - df["general_user_score"].astype(float)).round(2)
    df["unit"] = "% and 4-point score"
    df["extraction_status"] = "통계표 텍스트 기반 구조화"
    return df


def build_cyber_ai_violence_2025() -> pd.DataFrame:
    rows = [
        (2025, 9, "청소년", "victim_aftereffect_depression_anxiety_stress", "피해 후 우울·불안하거나 심한 스트레스를 받았다", 16.0, "%", "요약 페이지"),
        (2025, 9, "성인", "victim_aftereffect_depression_anxiety_stress", "피해 후 우울·불안하거나 심한 스트레스를 받았다", 27.7, "%", "요약 페이지"),
        (2025, 9, "청소년", "victim_aftereffect_no_particular_feeling", "피해 후 별다른 생각이 들지 않았다", 69.4, "%", "요약 페이지"),
        (2025, 9, "성인", "victim_aftereffect_no_particular_feeling", "피해 후 별다른 생각이 들지 않았다", 45.6, "%", "요약 페이지"),
        (2025, 9, "청소년", "victim_aftereffect_revenge_wish", "피해를 준 상대방에게 복수하고 싶었다", 26.2, "%", "요약 페이지"),
        (2025, 9, "성인", "victim_aftereffect_revenge_wish", "피해를 준 상대방에게 복수하고 싶었다", 25.3, "%", "요약 페이지"),
        (2025, 92, "청소년", "ai_assisted_perpetration_among_perpetrators", "AI 서비스를 활용한 사이버폭력 가해 경험", 2.2, "%", "가해 경험자 기준"),
        (2025, 189, "성인", "ai_assisted_perpetration_among_perpetrators", "AI 서비스를 활용한 사이버폭력 가해 경험", 2.6, "%", "가해 경험자 기준"),
        (2025, 105, "청소년", "ai_cyberviolence_serious_perception", "인공지능 활용 사이버폭력 심각성 인식", 89.4, "%", "심각함 응답"),
        (2025, 202, "성인", "ai_cyberviolence_serious_perception", "인공지능 활용 사이버폭력 심각성 인식", 87.6, "%", "심각함 응답"),
    ]
    df = pd.DataFrame(rows, columns=["year", "page", "target_group", "metric", "metric_label", "value", "unit", "base"])
    df["dataset"] = "NIA/방송미디어통신위원회 사이버폭력 실태조사"
    df["extraction_status"] = "본문·요약 페이지 기반 구조화"
    return df


def build_integrated_panel(ai_df: pd.DataFrame) -> pd.DataFrame:
    panel = ai_df.copy()
    panel["ai_gap_abs_pp"] = panel["gap_vs_general_pp"].abs()
    panel["analysis_unit"] = "year x vulnerable_group"
    panel["join_status"] = "AI 경험률 직접 관측; 심리위험 지표는 별도 브리지 테이블로 결합"
    panel["paper_use"] = "핵심 집단-연도 패널"
    return panel[
        [
            "analysis_unit",
            "year",
            "group",
            "ai_experience_rate",
            "general_public_rate",
            "gap_vs_general_pp",
            "ai_gap_abs_pp",
            "page",
            "dataset",
            "join_status",
            "paper_use",
            "evidence_snippet",
        ]
    ]


def markdown_table(df: pd.DataFrame, columns: list[str], max_rows: int = 20) -> str:
    sub = df.loc[:, [c for c in columns if c in df.columns]].head(max_rows).fillna("")
    header = [str(c) for c in sub.columns]
    lines = ["| " + " | ".join(header) + " |", "| " + " | ".join(["---"] * len(header)) + " |"]
    for _, row in sub.iterrows():
        lines.append("| " + " | ".join(str(row[c]).replace("\n", " ")[:180] for c in sub.columns) + " |")
    return "\n".join(lines)


def write_docs(
    ai_df: pd.DataFrame,
    service_df: pd.DataFrame,
    smartphone_df: pd.DataFrame,
    harm_df: pd.DataFrame,
    cyber_df: pd.DataFrame,
    panel_df: pd.DataFrame,
) -> None:
    growth = (
        ai_df.pivot(index="group", columns="year", values="ai_experience_rate")
        .assign(change_2023_2025=lambda x: (x[2025] - x[2023]).round(1))
        .reset_index()
        .sort_values("change_2023_2025", ascending=False)
    )
    gap_2025 = ai_df[ai_df["year"].eq(2025)].sort_values("gap_vs_general_pp")
    high_harm = harm_df[harm_df["indicator_type"].eq("문제적 결과 문항")].sort_values("rate_gap_pp", ascending=False)
    summary = {
        "ai_panel_rows": len(ai_df),
        "ai_service_metric_rows": len(service_df),
        "smartphone_summary_rows": len(smartphone_df),
        "smartphone_psych_harm_rows": len(harm_df),
        "cyber_ai_violence_rows": len(cyber_df),
        "integrated_panel_rows": len(panel_df),
    }
    (OUT / "paper_ready_dataset_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    memo = f"""# 논문용 수치 데이터셋 구축 메모

## 생성한 핵심 CSV

- `paper_ai_experience_panel.csv`: NIA 디지털정보격차실태조사의 2023-2025년 집단별 AI 서비스 경험률
- `paper_integrated_group_year_panel.csv`: 논문 1차 분석용 `연도 x 취약집단` 패널
- `paper_ai_service_summary_metrics.csv`: AI 서비스 인지율·경험률·도움 정도·비이용 이유 대표 수치
- `paper_smartphone_overdependence_summary.csv`: 스마트폰 과의존위험군 연도별·대상별 대표 수치
- `paper_smartphone_psych_harm_2025.csv`: 과의존위험군의 문제적 결과, 건강·가족·대인관계·학업/업무 어려움 지표
- `paper_cyber_ai_violence_2025.csv`: AI 활용 사이버폭력 심각성, AI 활용 가해 경험, 피해 후 심리상태 대표 수치

## AI 경험률 변화

{markdown_table(growth, ["group", 2023, 2024, 2025, "change_2023_2025"], 10)}

## 2025년 일반국민 대비 AI 경험률 격차

{markdown_table(gap_2025, ["group", "ai_experience_rate", "general_public_rate", "gap_vs_general_pp", "page"], 10)}

## 스마트폰 과의존 관련 심리·사회적 폐해 상위 격차

{markdown_table(high_harm, ["target_group", "indicator", "positive_rate_overdependence", "positive_rate_general_user", "rate_gap_pp", "page"], 12)}

## 해석

공개 PDF만으로도 논문용 1차 데이터셋은 만들 수 있습니다. 다만 이 데이터셋은 개인 단위가 아니라 `연도 x 집단`, `대상 x 지표` 수준의 결합자료입니다. 따라서 첫 논문은 인과효과보다는 **격차 구조, 위험군 프로파일링, 정책 타깃팅**을 중심으로 쓰는 것이 안전합니다.
"""
    (DOCS / "05_paper_ready_dataset_memo.md").write_text(memo, encoding="utf-8")

    findings = f"""# 예비 핵심 발견

## 1. AI 경험률은 전반적으로 상승했지만 집단 간 격차가 남아 있음

2023년에서 2025년 사이 일반국민의 AI 서비스 경험률은 49.7%에서 59.4%로 상승했습니다. 결혼이민자와 북한이탈주민은 2025년에 일반국민보다 높은 경험률을 보였지만, 고령층·농어민·장애인·저소득층은 여전히 낮았습니다.

## 2. 2025년 격차가 가장 큰 집단은 고령층과 농어민

2025년 일반국민 대비 AI 경험률 격차는 고령층 -29.2%p, 농어민 -28.3%p, 장애인 -23.8%p, 저소득층 -22.7%p입니다. 이는 AI 리터러시 논문에서 “디지털 취약성의 재생산”을 보여주는 핵심 근거가 됩니다.

## 3. AI 정보검색은 취약계층에서도 핵심 서비스지만 경험 격차가 큼

2025년 취약계층의 AI 기반 대화형 정보검색 인지율은 47.2%, 인지자 기준 경험률은 38.5%입니다. 같은 해 비이용 이유에서 고령층은 “AI를 잘 모름” 60.9%, “이용 방법이 어려움” 47.4%로 나타나, 심리상담·정보탐색 접근성에서 AI가 새 장벽이 될 수 있음을 시사합니다.

## 4. 스마트폰 과의존은 심리상태/상담 필요성과 연결할 수 있는 강한 브리지 지표

2025년 스마트폰 과의존위험군은 전체 22.7%, 청소년 43.0%, 성인 청년층 29.5%입니다. 과의존위험군은 일반사용자군보다 건강 문제, 가족 갈등, 대인관계 갈등, 학업/업무 어려움이 훨씬 높습니다. 예컨대 60대는 대인관계 갈등 긍정응답 격차가 52.2%p, 성인은 업무/학업 어려움 격차가 44.3%p입니다.

## 5. AI 활용 사이버폭력은 심리위험을 직접적으로 붙일 수 있는 최신 지점

2025년 사이버폭력 실태조사에서 AI 활용 사이버폭력이 심각하다고 보는 비율은 청소년 89.4%, 성인 87.6%입니다. 사이버폭력 피해 후 우울·불안 또는 심한 스트레스를 경험했다는 응답은 청소년 16.0%, 성인 27.7%입니다.

## 추천 논문 문장

“생성형 AI의 확산은 단순한 기술 채택의 문제가 아니라, 기존 디지털 취약집단의 정보접근·도움요청·심리위험 구조를 재배열하는 사회심리적 격차 문제로 분석될 필요가 있다.”
"""
    (DOCS / "06_preliminary_key_findings.md").write_text(findings, encoding="utf-8")


def main() -> None:
    ai_df = extract_ai_experience_panel()
    service_df = build_ai_service_summary()
    smartphone_df = build_smartphone_summary()
    harm_df = build_smartphone_psych_harm_2025()
    cyber_df = build_cyber_ai_violence_2025()
    panel_df = build_integrated_panel(ai_df)

    ai_df.to_csv(OUT / "paper_ai_experience_panel.csv", index=False, encoding="utf-8-sig")
    service_df.to_csv(OUT / "paper_ai_service_summary_metrics.csv", index=False, encoding="utf-8-sig")
    smartphone_df.to_csv(OUT / "paper_smartphone_overdependence_summary.csv", index=False, encoding="utf-8-sig")
    harm_df.to_csv(OUT / "paper_smartphone_psych_harm_2025.csv", index=False, encoding="utf-8-sig")
    cyber_df.to_csv(OUT / "paper_cyber_ai_violence_2025.csv", index=False, encoding="utf-8-sig")
    panel_df.to_csv(OUT / "paper_integrated_group_year_panel.csv", index=False, encoding="utf-8-sig")

    write_docs(ai_df, service_df, smartphone_df, harm_df, cyber_df, panel_df)
    print(
        json.dumps(
            {
                "paper_ai_experience_panel": len(ai_df),
                "paper_ai_service_summary_metrics": len(service_df),
                "paper_smartphone_overdependence_summary": len(smartphone_df),
                "paper_smartphone_psych_harm_2025": len(harm_df),
                "paper_cyber_ai_violence_2025": len(cyber_df),
                "paper_integrated_group_year_panel": len(panel_df),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
