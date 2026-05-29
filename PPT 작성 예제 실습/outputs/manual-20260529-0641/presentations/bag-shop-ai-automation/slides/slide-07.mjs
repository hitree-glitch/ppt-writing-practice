import { COLORS, bg, kicker, title, body, card, text, smallArrow, footer } from "./common.mjs";

export async function slide07(presentation, ctx) {
  const slide = presentation.slides.add();
  bg(slide, ctx, COLORS.white);
  kicker(slide, ctx, "코덱스 활용");
  title(slide, ctx, "코덱스는 매주 직접 정리하던 문서와 콘텐츠 초안을 도울 수 있습니다", 74, COLORS.text, 1040);
  const inputs = ["판매/재고 시트", "상품 정보", "리뷰/반품 사유", "고객 문의"];
  const outputs = ["주간 운영 리포트", "상품 설명 초안", "상세페이지 개선안", "SNS/이벤트 문구"];
  inputs.forEach((item, i) => {
    card(slide, ctx, 76, 220 + i * 72, 270, 48, { fill: COLORS.cream, stroke: "#E4DDD1" });
    text(slide, ctx, item, 98, 232 + i * 72, 230, 22, { size: 16, color: COLORS.text, bold: true, valign: "middle" });
  });
  card(slide, ctx, 474, 244, 250, 190, { fill: COLORS.deep, stroke: COLORS.deep });
  text(slide, ctx, "CODEX", 514, 286, 170, 42, { size: 32, bold: true, color: COLORS.gold, align: "center" });
  body(slide, ctx, "자료를 읽고\n초안과 점검표를 만드는\nAI 작업 도우미", 516, 344, 166, 72, { size: 17, color: COLORS.white, valign: "middle" });
  outputs.forEach((item, i) => {
    card(slide, ctx, 850, 220 + i * 72, 310, 48, { fill: i === 0 ? COLORS.soft : COLORS.white, stroke: "#D8E0DA" });
    text(slide, ctx, item, 872, 232 + i * 72, 270, 22, { size: 16, color: COLORS.text, bold: true, valign: "middle" });
  });
  smallArrow(slide, ctx, 385, 326);
  smallArrow(slide, ctx, 762, 326);
  body(slide, ctx, "핵심은 코덱스가 최종 판단을 대신하는 것이 아니라, 대표가 검토할 초안과 점검 기준을 빠르게 준비하는 것입니다.", 96, 560, 1040, 42, { size: 19, color: COLORS.text, valign: "middle" });
  footer(slide, ctx, "Source: solution design based on user-provided Codex automation requirement.", 7);
  return slide;
}
