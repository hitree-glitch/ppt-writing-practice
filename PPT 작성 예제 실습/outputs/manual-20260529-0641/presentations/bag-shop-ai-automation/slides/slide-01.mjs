import { COLORS, IMG, bg, text, body, pill, footer } from "./common.mjs";

export async function slide01(presentation, ctx) {
  const slide = presentation.slides.add();
  bg(slide, ctx, COLORS.cream);
  await ctx.addImage(slide, { path: IMG.hero, x: 560, y: 0, w: 720, h: 720, fit: "cover", alt: "non-branded handbag ecommerce operator using laptop" });
  ctx.addShape(slide, { x: 0, y: 0, w: 560, h: 720, fill: COLORS.cream, line: ctx.line(COLORS.cream, 0) });
  pill(slide, ctx, "AI 자동화 제안", 58, 58, 180, { fill: COLORS.deep, h: 34 });
  text(slide, ctx, "여성용 가방\n쇼핑몰 AI 자동화\n컨설팅 제안", 58, 136, 470, 210, { size: 46, bold: true, color: COLORS.text });
  body(slide, ctx, "상품 상세, 고객 문의, 리뷰·반품, 운영 리포트를 반복 업무가 아니라 굴러가는 구조로 바꿉니다.", 62, 382, 410, 82, { size: 21, color: COLORS.text });
  pill(slide, ctx, "10장 제안서 · 4주 진단/설계", 62, 500, 245, { fill: COLORS.bright, h: 38 });
  text(slide, ctx, "대상: 내부 개발팀이 없는 여성용 가방 온라인 쇼핑몰", 62, 554, 420, 28, { size: 14, color: COLORS.muted });
  text(slide, ctx, "Image: generated with imagegen for this proposal; no logos or embedded text.", 58, 680, 420, 18, { size: 9, color: COLORS.muted, valign: "middle" });
  text(slide, ctx, "01", 498, 676, 42, 24, { size: 11, bold: true, color: COLORS.green, align: "right", valign: "middle" });
  return slide;
}
