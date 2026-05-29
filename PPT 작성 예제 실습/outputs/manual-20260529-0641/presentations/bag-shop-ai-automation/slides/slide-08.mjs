import { COLORS, bg, kicker, title, body, card, text, footer } from "./common.mjs";

export async function slide08(presentation, ctx) {
  const slide = presentation.slides.add();
  bg(slide, ctx, COLORS.ceramic);
  kicker(slide, ctx, "4주 실행 로드맵");
  title(slide, ctx, "4주 안에 진단에서 자동화 운영 기준까지 정리합니다", 74, COLORS.text, 920);
  const weeks = [
    ["1주차", "업무 진단", "상품 등록, 문의, 리뷰/반품, 리포트 흐름 확인"],
    ["2주차", "후보 선정", "효과가 크고 위험이 낮은 자동화 1~2개 선택"],
    ["3주차", "흐름 설계", "코덱스 초안 생성과 n8n 연결 구조 설계"],
    ["4주차", "운영 기준", "검수 기준, 담당자 역할, 다음 구축 계획 정리"],
  ];
  weeks.forEach((w, i) => {
    const x = 70 + i * 292;
    card(slide, ctx, x, 248, 250, 230, { fill: COLORS.white, stroke: "#D8E0DA" });
    card(slide, ctx, x + 18, 270, 70, 34, { fill: i === 2 ? COLORS.bright : COLORS.deep, stroke: i === 2 ? COLORS.bright : COLORS.deep });
    text(slide, ctx, w[0], x + 24, 278, 58, 18, { size: 13, bold: true, color: COLORS.white, align: "center", valign: "middle" });
    text(slide, ctx, w[1], x + 24, 328, 200, 30, { size: 23, bold: true, color: COLORS.green, align: "center" });
    body(slide, ctx, w[2], x + 28, 378, 194, 64, { size: 15, color: COLORS.text, align: "center" });
    if (i < weeks.length - 1) {
      text(slide, ctx, "→", x + 256, 342, 38, 32, { size: 26, bold: true, color: COLORS.bright, align: "center", valign: "middle" });
    }
  });
  body(slide, ctx, "첫 구축은 보통 상품 상세 점검, 고객 문의 분류, 리뷰/반품 분석 중 하나부터 시작합니다.", 114, 560, 1030, 34, { size: 20, color: COLORS.text, align: "center" });
  footer(slide, ctx, "Source: proposed 4-week consulting scope.", 8);
  return slide;
}
