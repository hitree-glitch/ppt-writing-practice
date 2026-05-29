import { COLORS, bg, kicker, title, body, card, text, footer } from "./common.mjs";

export async function slide09(presentation, ctx) {
  const slide = presentation.slides.add();
  bg(slide, ctx, COLORS.white);
  kicker(slide, ctx, "기대 효과");
  title(slide, ctx, "반복 처리 시간을 줄이고, 대표가 상품 기획과 매출 개선에 집중하게 만듭니다", 74, COLORS.text, 1030);
  card(slide, ctx, 70, 220, 500, 300, { fill: COLORS.cream, stroke: "#E4DDD1" });
  card(slide, ctx, 710, 220, 500, 300, { fill: COLORS.deep, stroke: COLORS.deep });
  text(slide, ctx, "BEFORE", 104, 248, 120, 28, { size: 18, bold: true, color: COLORS.warn });
  text(slide, ctx, "AFTER", 744, 248, 120, 28, { size: 18, bold: true, color: COLORS.gold });
  const before = ["상품 설명을 매번 새로 작성", "반복 문의를 사람이 하나씩 응대", "반품 사유가 쌓여도 개선으로 연결 어려움", "주간 리포트가 대표에게 몰림"];
  const after = ["상품 상세 점검 기준 표준화", "AI 초안 + 사람 검수로 응답 속도 개선", "리뷰/반품 키워드가 개선 액션으로 전환", "운영 리포트 초안 자동 준비"];
  before.forEach((b, i) => body(slide, ctx, `• ${b}`, 106, 306 + i * 44, 400, 26, { size: 18, color: COLORS.text }));
  after.forEach((a, i) => body(slide, ctx, `• ${a}`, 746, 306 + i * 44, 400, 26, { size: 18, color: COLORS.white }));
  text(slide, ctx, "→", 610, 340, 60, 56, { size: 42, bold: true, color: COLORS.bright, align: "center", valign: "middle" });
  body(slide, ctx, "정량 효과는 실제 문의량, 상품 수, 반품 데이터 확인 후 산정합니다. 첫 단계에서는 반복 업무 1개를 줄이는 구조부터 검증합니다.", 110, 570, 1040, 42, { size: 17, color: COLORS.text, align: "center" });
  footer(slide, ctx, "Source: solution logic; exact savings require client data validation.", 9);
  return slide;
}
