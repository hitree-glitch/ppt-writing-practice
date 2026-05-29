import { COLORS, bg, kicker, title, body, card, text, pill, footer } from "./common.mjs";

export async function slide10(presentation, ctx) {
  const slide = presentation.slides.add();
  bg(slide, ctx, COLORS.deep);
  kicker(slide, ctx, "다음 단계", true);
  title(slide, ctx, "가장 먼저 자동화할 업무 1개를 정하면 시작할 수 있습니다", 76, COLORS.white, 1020);
  body(slide, ctx, "아래 3개 중 하나를 첫 진단 대상으로 정하면 4주 컨설팅의 범위와 필요한 자료가 명확해집니다.", 62, 182, 980, 32, { size: 19, color: "#EAF4F0" });
  const options = [
    ["상품 상세 점검", "크기·소재·수납·착용컷 누락을 줄입니다."],
    ["고객 문의 자동화", "반복 문의 초안과 담당자 알림을 만듭니다."],
    ["리뷰/반품 분석", "반복 불만을 개선 액션으로 바꿉니다."],
  ];
  options.forEach((o, i) => {
    const x = 70 + i * 380;
    card(slide, ctx, x, 250, 320, 180, { fill: COLORS.white, stroke: COLORS.white });
    text(slide, ctx, `0${i + 1}`, x + 24, 274, 54, 30, { size: 19, bold: true, color: COLORS.gold });
    text(slide, ctx, o[0], x + 24, 326, 250, 30, { size: 24, bold: true, color: COLORS.green });
    body(slide, ctx, o[1], x + 24, 366, 260, 42, { size: 16, color: COLORS.text });
  });
  pill(slide, ctx, "확인할 자료: 상품 목록 · 최근 문의 · 리뷰/반품 사유 · 사용 중인 운영 도구", 218, 510, 844, { fill: COLORS.bright, h: 44, size: 15 });
  footer(slide, ctx, "Next decision: pick one workflow for the first diagnostic sprint.", 10, true);
  return slide;
}
