import { COLORS, bg, kicker, title, body, card, text, footer } from "./common.mjs";

export async function slide06(presentation, ctx) {
  const slide = presentation.slides.add();
  bg(slide, ctx, COLORS.cream);
  kicker(slide, ctx, "솔루션 3");
  title(slide, ctx, "반복 불만을 상품 페이지 개선과 CS 기준으로 연결합니다", 74, COLORS.text, 980);
  body(slide, ctx, "반품과 리뷰는 비용이지만, 동시에 상세페이지와 고객응대를 개선하는 가장 직접적인 데이터입니다.", 60, 176, 860, 34, { size: 18, color: COLORS.text });
  const headers = ["반복 키워드", "자동 분류", "개선 액션"];
  const rows = [
    ["색상 차이", "사진/조명 이슈", "실내·자연광 컷 보강"],
    ["수납 부족", "상세 설명 부족", "내부 포켓/수납 예시 추가"],
    ["무게감", "체감 정보 부족", "무게 수치와 착용 설명 추가"],
    ["배송 손상", "포장/물류 이슈", "포장 기준과 검수 체크 강화"],
  ];
  const x = 70, y = 230, col = [210, 270, 320], rowH = 68;
  headers.forEach((h, i) => {
    const xx = x + col.slice(0, i).reduce((a, b) => a + b, 0);
    card(slide, ctx, xx, y, col[i], 48, { fill: COLORS.deep, stroke: COLORS.deep });
    text(slide, ctx, h, xx + 16, y + 12, col[i] - 32, 22, { size: 15, bold: true, color: COLORS.white, align: "center", valign: "middle" });
  });
  rows.forEach((r, ri) => {
    const yy = y + 48 + ri * rowH;
    r.forEach((cell, ci) => {
      const xx = x + col.slice(0, ci).reduce((a, b) => a + b, 0);
      card(slide, ctx, xx, yy, col[ci], rowH, { geometry: "rect", fill: ci === 2 ? COLORS.white : "#FAFBFA", stroke: "#D8E0DA" });
      text(slide, ctx, cell, xx + 18, yy + 20, col[ci] - 36, 26, { size: 15, bold: ci === 0, color: ci === 0 ? COLORS.green : COLORS.text, valign: "middle" });
    });
  });
  card(slide, ctx, 925, 246, 250, 230, { fill: COLORS.white, stroke: "#D8E0DA" });
  text(slide, ctx, "$890B", 960, 282, 180, 54, { size: 38, bold: true, color: COLORS.gold, align: "center", valign: "middle" });
  body(slide, ctx, "2024년 미국 리테일 반품 전망", 958, 348, 185, 34, { size: 15, bold: true, color: COLORS.text, align: "center" });
  body(slide, ctx, "반품 사유를 운영 개선으로 바꾸는 흐름이 필요합니다.", 958, 394, 185, 48, { size: 14, color: COLORS.muted, align: "center" });
  footer(slide, ctx, "Source: NRF & Happy Returns, 2024 retail returns.", 6);
  return slide;
}
