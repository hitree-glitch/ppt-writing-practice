export const COLORS = {
  cream: "#F2F0EB",
  ceramic: "#EDEBE9",
  white: "#FFFFFF",
  green: "#006241",
  bright: "#00754A",
  deep: "#1E3932",
  soft: "#D4E9E2",
  gold: "#CBA258",
  text: "#1F2933",
  muted: "#52606D",
  warn: "#F59E0B",
  line: "#CBD5D1",
};

export const ROOT = "C:/Users/user/Documents/코덱스 저장소/PPT 작성 예제 실습";
export const IMG = {
  hero: `${ROOT}/assets/imagegen/hero-bag-shop-automation.png`,
  workload: `${ROOT}/assets/imagegen/workload-before-automation.png`,
  inquiry: `${ROOT}/assets/imagegen/customer-inquiry-automation.png`,
};

export function bg(slide, ctx, color = COLORS.cream) {
  return ctx.addShape(slide, { x: 0, y: 0, w: ctx.W, h: ctx.H, fill: color, line: ctx.line(color, 0) });
}

export function text(slide, ctx, value, x, y, w, h, opts = {}) {
  return ctx.addText(slide, {
    text: value,
    x,
    y,
    w,
    h,
    fontSize: opts.size ?? 24,
    bold: opts.bold ?? false,
    color: opts.color ?? COLORS.text,
    typeface: opts.face ?? "Malgun Gothic",
    align: opts.align ?? "left",
    valign: opts.valign ?? "top",
    fill: opts.fill ?? "#00000000",
    line: opts.line ?? ctx.line("#00000000", 0),
    insets: opts.insets ?? { left: 0, right: 0, top: 0, bottom: 0 },
    name: opts.name,
  });
}

export function kicker(slide, ctx, label, dark = false) {
  ctx.addShape(slide, { x: 58, y: 42, w: 8, h: 8, fill: dark ? COLORS.gold : COLORS.bright, line: ctx.line("#00000000", 0), name: "kicker-marker" });
  return text(slide, ctx, label, 76, 34, 360, 24, {
    size: 13,
    bold: true,
    color: dark ? COLORS.soft : COLORS.bright,
    valign: "middle",
    name: "kicker-label",
  });
}

export function title(slide, ctx, value, y = 72, color = COLORS.text, w = 840) {
  return text(slide, ctx, value, 58, y, w, 100, { size: 34, bold: true, color, face: "Malgun Gothic" });
}

export function body(slide, ctx, value, x, y, w, h, opts = {}) {
  return text(slide, ctx, value, x, y, w, h, {
    size: opts.size ?? 18,
    color: opts.color ?? COLORS.muted,
    bold: opts.bold ?? false,
    valign: opts.valign ?? "top",
    insets: opts.insets ?? { left: 0, right: 0, top: 0, bottom: 0 },
  });
}

export function card(slide, ctx, x, y, w, h, opts = {}) {
  return ctx.addShape(slide, {
    x,
    y,
    w,
    h,
    geometry: opts.geometry ?? "roundRect",
    fill: opts.fill ?? COLORS.white,
    line: opts.line ?? ctx.line(opts.stroke ?? "#E1E7E3", opts.strokeWidth ?? 1),
    name: opts.name,
  });
}

export function pill(slide, ctx, label, x, y, w, opts = {}) {
  card(slide, ctx, x, y, w, opts.h ?? 34, {
    geometry: "roundRect",
    fill: opts.fill ?? COLORS.bright,
    line: ctx.line(opts.stroke ?? opts.fill ?? COLORS.bright, opts.strokeWidth ?? 1),
  });
  return text(slide, ctx, label, x + 16, y + 5, w - 32, (opts.h ?? 34) - 8, {
    size: opts.size ?? 13,
    bold: true,
    color: opts.color ?? COLORS.white,
    align: "center",
    valign: "middle",
  });
}

export function metric(slide, ctx, value, label, note, x, y, w, h, opts = {}) {
  card(slide, ctx, x, y, w, h, { fill: opts.fill ?? COLORS.white, stroke: opts.stroke ?? "#E1E7E3" });
  text(slide, ctx, value, x + 22, y + 22, w - 44, 46, { size: opts.valueSize ?? 37, bold: true, color: opts.valueColor ?? COLORS.green, valign: "middle" });
  text(slide, ctx, label, x + 22, y + 78, w - 44, 42, { size: 17, bold: true, color: COLORS.text });
  body(slide, ctx, note, x + 22, y + 124, w - 44, h - 142, { size: 13, color: COLORS.muted });
}

export function footer(slide, ctx, source, page, dark = false) {
  text(slide, ctx, source, 58, 680, 880, 18, { size: 9, color: dark ? "#BFD8D1" : COLORS.muted, valign: "middle" });
  text(slide, ctx, String(page).padStart(2, "0"), 1178, 676, 42, 24, { size: 11, bold: true, color: dark ? COLORS.soft : COLORS.green, align: "right", valign: "middle" });
}

export function smallArrow(slide, ctx, x, y, color = COLORS.bright) {
  return text(slide, ctx, "→", x, y, 34, 28, { size: 24, bold: true, color, align: "center", valign: "middle" });
}

export function checklist(slide, ctx, items, x, y, w, rowH = 46) {
  items.forEach((item, index) => {
    const yy = y + index * rowH;
    card(slide, ctx, x, yy, w, rowH - 8, { fill: index % 2 === 0 ? COLORS.white : "#FAFBFA", stroke: "#E2E8E4" });
    text(slide, ctx, "✓", x + 14, yy + 8, 24, 22, { size: 15, bold: true, color: COLORS.bright, valign: "middle", align: "center" });
    body(slide, ctx, item, x + 46, yy + 8, w - 58, 22, { size: 14, color: COLORS.text, valign: "middle" });
  });
}
