import { COLORS, bg, kicker, title, body, metric, footer } from "./common.mjs";

export async function slide02(presentation, ctx) {
  const slide = presentation.slides.add();
  bg(slide, ctx, COLORS.white);
  kicker(slide, ctx, "업계 상황");
  title(slide, ctx, "상품 정보, 구매 확신, 반품 경험이 운영 경쟁력이 됩니다");
  body(slide, ctx, "여성용 가방은 크기·소재·수납·착용 장면을 직접 확인하기 어렵습니다. 온라인 쇼핑몰 운영자는 상세 정보 품질과 빠른 응대를 동시에 관리해야 합니다.", 60, 178, 920, 48, { size: 18, color: COLORS.text });
  metric(slide, ctx, "70.22%", "평균 장바구니 이탈률", "결제 전 불안과 마찰은 쇼핑몰 공통 손실 지점입니다.", 70, 250, 350, 230, { valueColor: COLORS.deep });
  metric(slide, ctx, "56%", "상품 이미지 먼저 탐색", "상품 상세 페이지에서 사용자의 첫 행동은 이미지 확인인 경우가 많습니다.", 465, 250, 350, 230, { valueColor: COLORS.green });
  metric(slide, ctx, "$890B", "2024년 미국 리테일 반품", "반품은 비용이자 고객 경험 관리 과제입니다.", 860, 250, 350, 230, { valueColor: COLORS.gold });
  ctx.addShape(slide, { x: 72, y: 530, w: 1138, h: 78, geometry: "roundRect", fill: COLORS.cream, line: ctx.line("#E4DDD1", 1) });
  body(slide, ctx, "따라서 제안의 출발점은 “AI 도구 구매”가 아니라 상품 정보·문의·반품 데이터를 매주 개선 흐름으로 연결하는 것입니다.", 100, 552, 1080, 34, { size: 20, color: COLORS.text, valign: "middle" });
  footer(slide, ctx, "Sources: Baymard cart abandonment stats; Baymard product image UX; NRF & Happy Returns 2024 retail returns.", 2);
  return slide;
}
