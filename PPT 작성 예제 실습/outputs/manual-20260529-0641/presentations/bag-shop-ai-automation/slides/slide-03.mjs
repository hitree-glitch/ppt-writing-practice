import { COLORS, IMG, bg, kicker, title, body, card, text, footer } from "./common.mjs";

export async function slide03(presentation, ctx) {
  const slide = presentation.slides.add();
  bg(slide, ctx, COLORS.cream);
  await ctx.addImage(slide, { path: IMG.workload, x: 560, y: 0, w: 720, h: 720, fit: "cover", alt: "non-branded ecommerce workload scene" });
  ctx.addShape(slide, { x: 0, y: 0, w: 560, h: 720, fill: COLORS.cream, line: ctx.line(COLORS.cream, 0) });
  kicker(slide, ctx, "운영 페인포인트");
  title(slide, ctx, "대표와 운영자는 상품 등록, 문의, 콘텐츠, 반품 대응을 동시에 처리합니다", 76, COLORS.text, 470);
  const tasks = [
    ["상품 상세", "크기·소재·수납·착용컷 누락 점검"],
    ["고객 문의", "배송·교환·소재·재입고 반복 답변"],
    ["리뷰/반품", "불만 키워드와 개선 액션 정리"],
    ["콘텐츠", "신상품 설명, SNS, 이벤트 문구 작성"],
    ["리포트", "판매·재고·문의 현황 주간 정리"],
  ];
  tasks.forEach((task, i) => {
    const y = 258 + i * 70;
    card(slide, ctx, 62, y, 420, 54, { fill: COLORS.white, stroke: "#E2E5DF" });
    text(slide, ctx, task[0], 82, y + 14, 98, 24, { size: 16, bold: true, color: COLORS.green, valign: "middle" });
    body(slide, ctx, task[1], 184, y + 14, 280, 24, { size: 14, color: COLORS.text, valign: "middle" });
  });
  text(slide, ctx, "Source: SMB operating model inference based on user-provided context; image generated with imagegen.", 58, 680, 420, 18, { size: 9, color: COLORS.muted, valign: "middle" });
  text(slide, ctx, "03", 498, 676, 42, 24, { size: 11, bold: true, color: COLORS.green, align: "right", valign: "middle" });
  return slide;
}
