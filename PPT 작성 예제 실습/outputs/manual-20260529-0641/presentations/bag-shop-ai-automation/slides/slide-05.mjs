import { COLORS, IMG, bg, kicker, title, body, card, text, smallArrow, footer } from "./common.mjs";

export async function slide05(presentation, ctx) {
  const slide = presentation.slides.add();
  bg(slide, ctx, COLORS.white);
  kicker(slide, ctx, "솔루션 2");
  title(slide, ctx, "반복 문의는 AI가 초안을 만들고, 민감한 답변은 사람이 확인합니다", 74, COLORS.text, 680);
  await ctx.addImage(slide, { path: IMG.inquiry, x: 760, y: 172, w: 430, h: 290, fit: "cover", alt: "non-branded customer inquiry automation flow" });
  const steps = [
    ["문의 접수", "배송·교환·소재·재입고"],
    ["n8n 분류", "유형 분류와 담당자 알림"],
    ["코덱스 초안", "상품 정보 기반 답변 작성"],
    ["사람 검수", "환불·불만·민감 이슈 확인"],
    ["발송/기록", "답변 발송 후 고객 기록"],
  ];
  steps.forEach((step, i) => {
    const x = 64 + i * 132;
    card(slide, ctx, x, 250, 112, 120, { fill: i === 2 ? COLORS.soft : COLORS.cream, stroke: "#D9E2DD" });
    text(slide, ctx, String(i + 1), x + 12, 266, 24, 24, { size: 13, bold: true, color: COLORS.bright, align: "center", valign: "middle" });
    text(slide, ctx, step[0], x + 14, 296, 88, 36, { size: 15, bold: true, color: COLORS.text, align: "center", valign: "middle" });
    body(slide, ctx, step[1], x + 12, 340, 88, 28, { size: 11, color: COLORS.muted, valign: "middle" });
    if (i < steps.length - 1) smallArrow(slide, ctx, x + 112, 295);
  });
  card(slide, ctx, 70, 476, 1060, 92, { fill: COLORS.deep, stroke: COLORS.deep });
  body(slide, ctx, "AI 고객응대는 속도를 높일 수 있지만, 고객이 민감하게 느끼는 교환·반품·불만 답변은 반드시 사람이 확인하는 구조로 설계합니다.", 104, 500, 990, 46, { size: 20, color: COLORS.white, valign: "middle" });
  footer(slide, ctx, "Sources: Qualtrics 2024 consumer experience trends; McKinsey generative AI in fashion.", 5);
  return slide;
}
