from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path("RESEARCH/korea_ai_counseling_psych_20260623")
DATA = ROOT / "data" / "processed"
CHARTS = ROOT / "outputs" / "charts"
CHARTS.mkdir(parents=True, exist_ok=True)

FONT = "'Malgun Gothic', 'Apple SD Gothic Neo', Arial, sans-serif"
COLORS = {
    "장애인": "#2563eb",
    "고령층": "#dc2626",
    "저소득층": "#16a34a",
    "농어민": "#9333ea",
    "북한이탈주민": "#ea580c",
    "결혼이민자": "#0891b2",
}


def line_chart_ai_trends() -> None:
    df = pd.read_csv(DATA / "paper_ai_experience_panel.csv")
    width, height = 980, 620
    left, right, top, bottom = 88, 220, 72, 82
    plot_w = width - left - right
    plot_h = height - top - bottom
    years = [2023, 2024, 2025]
    ymin, ymax = 20, 70

    def x(year: int) -> float:
        return left + (year - min(years)) / (max(years) - min(years)) * plot_w

    def y(value: float) -> float:
        return top + (ymax - value) / (ymax - ymin) * plot_h

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        f'<rect width="{width}" height="{height}" fill="#ffffff"/>',
        f'<text x="{left}" y="36" font-family="{FONT}" font-size="24" font-weight="700" fill="#111827">AI 서비스 경험률 추이: 디지털 취약집단 vs 일반국민</text>',
        f'<text x="{left}" y="60" font-family="{FONT}" font-size="13" fill="#4b5563">NIA 디지털정보격차실태조사, 단위: %</text>',
    ]
    for tick in range(20, 71, 10):
        yy = y(tick)
        parts.append(f'<line x1="{left}" y1="{yy:.1f}" x2="{width-right}" y2="{yy:.1f}" stroke="#e5e7eb"/>')
        parts.append(f'<text x="{left-12}" y="{yy+4:.1f}" text-anchor="end" font-family="{FONT}" font-size="12" fill="#6b7280">{tick}</text>')
    for year in years:
        xx = x(year)
        parts.append(f'<text x="{xx:.1f}" y="{height-bottom+30}" text-anchor="middle" font-family="{FONT}" font-size="13" fill="#374151">{year}</text>')
    parts.append(f'<line x1="{left}" y1="{height-bottom}" x2="{width-right}" y2="{height-bottom}" stroke="#9ca3af"/>')
    parts.append(f'<line x1="{left}" y1="{top}" x2="{left}" y2="{height-bottom}" stroke="#9ca3af"/>')

    # General-public reference line.
    general = df.groupby("year")["general_public_rate"].first().reindex(years)
    pts = " ".join(f"{x(int(year)):.1f},{y(float(val)):.1f}" for year, val in general.items())
    parts.append(f'<polyline points="{pts}" fill="none" stroke="#111827" stroke-width="3" stroke-dasharray="8 5"/>')
    for year, val in general.items():
        parts.append(f'<circle cx="{x(int(year)):.1f}" cy="{y(float(val)):.1f}" r="4" fill="#111827"/>')
    legend_y = top
    parts.append(f'<line x1="{width-right+36}" y1="{legend_y}" x2="{width-right+70}" y2="{legend_y}" stroke="#111827" stroke-width="3" stroke-dasharray="8 5"/>')
    parts.append(f'<text x="{width-right+78}" y="{legend_y+5}" font-family="{FONT}" font-size="13" fill="#111827">일반국민</text>')

    for idx, group in enumerate(["장애인", "고령층", "저소득층", "농어민", "북한이탈주민", "결혼이민자"], start=1):
        sub = df[df["group"].eq(group)].set_index("year").reindex(years)
        pts = " ".join(f"{x(year):.1f},{y(float(row['ai_experience_rate'])):.1f}" for year, row in sub.iterrows())
        color = COLORS[group]
        parts.append(f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="2.4"/>')
        for year, row in sub.iterrows():
            val = float(row["ai_experience_rate"])
            parts.append(f'<circle cx="{x(year):.1f}" cy="{y(val):.1f}" r="4" fill="{color}"/>')
            if year == 2025:
                parts.append(f'<text x="{x(year)+8:.1f}" y="{y(val)+4:.1f}" font-family="{FONT}" font-size="12" fill="{color}">{val:.1f}</text>')
        ly = legend_y + idx * 26
        parts.append(f'<line x1="{width-right+36}" y1="{ly}" x2="{width-right+70}" y2="{ly}" stroke="{color}" stroke-width="2.4"/>')
        parts.append(f'<text x="{width-right+78}" y="{ly+5}" font-family="{FONT}" font-size="13" fill="#111827">{group}</text>')

    parts.append("</svg>")
    (CHARTS / "ai_experience_trends.svg").write_text("\n".join(parts), encoding="utf-8")


def bar_chart_gap_2025() -> None:
    df = pd.read_csv(DATA / "paper_ai_experience_panel.csv")
    sub = df[df["year"].eq(2025)].sort_values("gap_vs_general_pp")
    width, height = 900, 460
    left, top, bar_h, gap = 180, 72, 34, 18
    zero_x = 580
    scale = 11
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="40" y="36" font-family="{FONT}" font-size="23" font-weight="700" fill="#111827">2025년 일반국민 대비 AI 경험률 격차</text>',
        f'<text x="40" y="58" font-family="{FONT}" font-size="13" fill="#4b5563">NIA 디지털정보격차실태조사, 단위: %p</text>',
        f'<line x1="{zero_x}" y1="{top-18}" x2="{zero_x}" y2="{height-50}" stroke="#9ca3af"/>',
        f'<text x="{zero_x}" y="{height-26}" text-anchor="middle" font-family="{FONT}" font-size="12" fill="#6b7280">일반국민 기준선</text>',
    ]
    for idx, row in enumerate(sub.itertuples(index=False)):
        y = top + idx * (bar_h + gap)
        value = float(row.gap_vs_general_pp)
        color = "#dc2626" if value < 0 else "#0891b2"
        if value < 0:
            x = zero_x + value * scale
            w = abs(value * scale)
        else:
            x = zero_x
            w = value * scale
        parts.append(f'<text x="{left-18}" y="{y+23}" text-anchor="end" font-family="{FONT}" font-size="15" fill="#111827">{row.group}</text>')
        parts.append(f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="{bar_h}" rx="3" fill="{color}"/>')
        tx = x - 8 if value < 0 else x + w + 8
        anchor = "end" if value < 0 else "start"
        parts.append(f'<text x="{tx:.1f}" y="{y+22}" text-anchor="{anchor}" font-family="{FONT}" font-size="14" font-weight="700" fill="{color}">{value:+.1f}</text>')
    parts.append("</svg>")
    (CHARTS / "ai_gap_2025.svg").write_text("\n".join(parts), encoding="utf-8")


def bar_chart_harm_gap() -> None:
    df = pd.read_csv(DATA / "paper_smartphone_psych_harm_2025.csv")
    sub = df[df["indicator_type"].eq("문제적 결과 문항")].sort_values("rate_gap_pp", ascending=False).head(10)
    width, height = 1160, 640
    left, top, bar_h, gap = 430, 80, 32, 20
    scale = 10
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="38" y="38" font-family="{FONT}" font-size="23" font-weight="700" fill="#111827">스마트폰 과의존위험군의 심리·사회적 폐해 격차</text>',
        f'<text x="38" y="60" font-family="{FONT}" font-size="13" fill="#4b5563">2025 스마트폰 과의존 실태조사, 과의존위험군 긍정응답률 - 일반사용자군 긍정응답률, 단위: %p</text>',
    ]
    for idx, row in enumerate(sub.itertuples(index=False)):
        y = top + idx * (bar_h + gap)
        label = f"{row.target_group}: {row.indicator}"
        value = float(row.rate_gap_pp)
        color = "#7c3aed" if row.target_group in ["유아동", "청소년"] else "#2563eb"
        parts.append(f'<text x="{left-18}" y="{y+22}" text-anchor="end" font-family="{FONT}" font-size="13" fill="#111827">{label[:42]}</text>')
        parts.append(f'<rect x="{left}" y="{y}" width="{value*scale:.1f}" height="{bar_h}" rx="3" fill="{color}"/>')
        parts.append(f'<text x="{left+value*scale+8:.1f}" y="{y+22}" font-family="{FONT}" font-size="14" font-weight="700" fill="{color}">{value:.1f}</text>')
    parts.append("</svg>")
    (CHARTS / "smartphone_psych_harm_gap_2025.svg").write_text("\n".join(parts), encoding="utf-8")


def main() -> None:
    line_chart_ai_trends()
    bar_chart_gap_2025()
    bar_chart_harm_gap()
    print("charts written", CHARTS)


if __name__ == "__main__":
    main()
