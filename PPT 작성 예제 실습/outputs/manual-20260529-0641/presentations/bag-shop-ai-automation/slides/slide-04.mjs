import { COLORS, bg, kicker, title, body, checklist, card, text, footer } from "./common.mjs";

export async function slide04(presentation, ctx) {
  const slide = presentation.slides.add();
  bg(slide, ctx, COLORS.ceramic);
  kicker(slide, ctx, "솔루션 1");
  title(slide, ctx, "크기, 소재, 수납, 착용컷 누락을 자동으로 찾아 상품 페이지 품질을 높입니다", 74, COLORS.text, 1010);
  body(slide, ctx, "코덱스가 상품 설명, 이미지 목록, 운영 기준을 함께 확인해 신규 상품 등록 전 빠진 정보를 점검합니다.", 60, 184, 900, 34, { size: 18, color: COLORS.text });
  checklist(slide, ctx, [
    "가방 크기: 가로·세로·폭, 스트랩 길이",
    "소재와 관리법: 가죽/합성/패브릭, 보관 주의",
    "내부 수납: 포켓, 지퍼, 노트북/지갑 수납 여부",
    "착용 장면: 손잡이, 숄더, 크로스, 모델 착용 비율",
    "구매 전 안내: 배송, 교환, 반품, 색상 차이 안내",
  ], 68, 238, 570, 58);
  card(slide, ctx, 720, 238, 440, 280, { fill: COLORS.deep, stroke: COLORS.deep });
  text(slide, ctx, "왜 먼저 해야 하나요?", 752, 270, 360, 34, { size: 24, bold: true, color: COLORS.white });
  body(slide, ctx, "가방은 직접 들어보고 확인할 수 없기 때문에 상품 상세가 곧 판매 직원 역할을 합니다. 정보가 부족하면 고객 문의와 반품 가능성이 함께 올라갑니다.", 754, 326, 360, 100, { size: 17, color: "#EAF4F0" });
  text(slide, ctx, "56%", 754, 440, 110, 54, { size: 44, bold: true, color: COLORS.gold, valign: "middle" });
  body(slide, ctx, "상품 상세 페이지에서 첫 행동으로 이미지 탐색", 872, 452, 250, 40, { size: 15, color: "#EAF4F0" });
  footer(slide, ctx, "Source: Baymard product image UX research.", 4);
  return slide;
}
