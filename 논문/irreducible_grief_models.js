const fs = require("fs");

const inputPath =
  "C:/Users/user/OneDrive/D 대학원 박사/A 아주대/논문 작성/(작업 중) OATrauma_Natural Disaster Subset 7.7.25.csv";

function parseCsv(text) {
  const rows = [];
  let row = [];
  let field = "";
  let inQuotes = false;
  for (let i = 0; i < text.length; i += 1) {
    const ch = text[i];
    const next = text[i + 1];
    if (inQuotes) {
      if (ch === '"' && next === '"') {
        field += '"';
        i += 1;
      } else if (ch === '"') inQuotes = false;
      else field += ch;
    } else if (ch === '"') inQuotes = true;
    else if (ch === ",") {
      row.push(field);
      field = "";
    } else if (ch === "\n") {
      row.push(field);
      rows.push(row);
      row = [];
      field = "";
    } else if (ch !== "\r") field += ch;
  }
  if (field.length || row.length) {
    row.push(field);
    rows.push(row);
  }
  const headers = rows.shift().map((h) => h.replace(/^\uFEFF/, ""));
  return rows
    .map((values) => Object.fromEntries(headers.map((h, i) => [h, values[i] ?? ""])))
    .filter((rowObj) => String(rowObj.Consent ?? "").trim() !== "");
}

function num(row, key) {
  const raw = row[key];
  if (raw == null || String(raw).trim() === "") return null;
  const value = Number(String(raw).trim());
  return Number.isFinite(value) ? value : null;
}

function mean(xs) {
  return xs.reduce((a, b) => a + b, 0) / xs.length;
}

function sd(xs) {
  const m = mean(xs);
  return Math.sqrt(xs.reduce((a, b) => a + (b - m) ** 2, 0) / (xs.length - 1));
}

function transpose(a) {
  return a[0].map((_, i) => a.map((row) => row[i]));
}

function multiply(a, b) {
  const out = Array.from({ length: a.length }, () => Array(b[0].length).fill(0));
  for (let i = 0; i < a.length; i += 1) {
    for (let k = 0; k < b.length; k += 1) {
      for (let j = 0; j < b[0].length; j += 1) out[i][j] += a[i][k] * b[k][j];
    }
  }
  return out;
}

function invert(matrix) {
  const n = matrix.length;
  const aug = matrix.map((row, i) => [
    ...row,
    ...Array.from({ length: n }, (_, j) => (i === j ? 1 : 0)),
  ]);
  for (let col = 0; col < n; col += 1) {
    let pivot = col;
    for (let r = col + 1; r < n; r += 1) {
      if (Math.abs(aug[r][col]) > Math.abs(aug[pivot][col])) pivot = r;
    }
    if (Math.abs(aug[pivot][col]) < 1e-12) throw new Error("Singular matrix");
    [aug[col], aug[pivot]] = [aug[pivot], aug[col]];
    const divisor = aug[col][col];
    for (let j = 0; j < 2 * n; j += 1) aug[col][j] /= divisor;
    for (let r = 0; r < n; r += 1) {
      if (r === col) continue;
      const factor = aug[r][col];
      for (let j = 0; j < 2 * n; j += 1) aug[r][j] -= factor * aug[col][j];
    }
  }
  return aug.map((row) => row.slice(n));
}

function logGamma(z) {
  const p = [
    676.5203681218851,
    -1259.1392167224028,
    771.3234287776531,
    -176.6150291621406,
    12.507343278686905,
    -0.13857109526572012,
    9.984369578019572e-6,
    1.5056327351493116e-7,
  ];
  if (z < 0.5) return Math.log(Math.PI) - Math.log(Math.sin(Math.PI * z)) - logGamma(1 - z);
  let x = 0.9999999999998099;
  z -= 1;
  for (let i = 0; i < p.length; i += 1) x += p[i] / (z + i + 1);
  const t = z + p.length - 0.5;
  return 0.5 * Math.log(2 * Math.PI) + (z + 0.5) * Math.log(t) - t + Math.log(x);
}

function betaContinuedFraction(x, a, b) {
  const eps = 3e-12;
  const fpmin = 1e-30;
  let qab = a + b;
  let qap = a + 1;
  let qam = a - 1;
  let c = 1;
  let d = 1 - (qab * x) / qap;
  if (Math.abs(d) < fpmin) d = fpmin;
  d = 1 / d;
  let h = d;
  for (let m = 1; m <= 200; m += 1) {
    const m2 = 2 * m;
    let aa = (m * (b - m) * x) / ((qam + m2) * (a + m2));
    d = 1 + aa * d;
    if (Math.abs(d) < fpmin) d = fpmin;
    c = 1 + aa / c;
    if (Math.abs(c) < fpmin) c = fpmin;
    d = 1 / d;
    h *= d * c;
    aa = (-(a + m) * (qab + m) * x) / ((a + m2) * (qap + m2));
    d = 1 + aa * d;
    if (Math.abs(d) < fpmin) d = fpmin;
    c = 1 + aa / c;
    if (Math.abs(c) < fpmin) c = fpmin;
    d = 1 / d;
    const del = d * c;
    h *= del;
    if (Math.abs(del - 1) < eps) break;
  }
  return h;
}

function regularizedIncompleteBeta(x, a, b) {
  if (x <= 0) return 0;
  if (x >= 1) return 1;
  const bt = Math.exp(logGamma(a + b) - logGamma(a) - logGamma(b) + a * Math.log(x) + b * Math.log(1 - x));
  if (x < (a + 1) / (a + b + 2)) return (bt * betaContinuedFraction(x, a, b)) / a;
  return 1 - (bt * betaContinuedFraction(1 - x, b, a)) / b;
}

function studentTCdf(t, df) {
  const x = df / (df + t * t);
  const ib = regularizedIncompleteBeta(x, df / 2, 0.5);
  return t >= 0 ? 1 - ib / 2 : ib / 2;
}

function completeRows(rawRows, variables) {
  return rawRows
    .map((row) => Object.fromEntries(variables.map((name) => [name, num(row, name)])))
    .filter((row) => variables.every((name) => row[name] != null));
}

function ols(rows, yName, xNames) {
  const y = rows.map((row) => [row[yName]]);
  const x = rows.map((row) => [1, ...xNames.map((name) => row[name])]);
  const xt = transpose(x);
  const xtxInv = invert(multiply(xt, x));
  const beta = multiply(multiply(xtxInv, xt), y).map((row) => row[0]);
  const predicted = x.map((row) => row.reduce((acc, value, i) => acc + value * beta[i], 0));
  const residuals = y.map((value, i) => value[0] - predicted[i]);
  const yMean = mean(y.map((value) => value[0]));
  const sse = residuals.reduce((acc, value) => acc + value * value, 0);
  const sst = y.reduce((acc, value) => acc + (value[0] - yMean) ** 2, 0);
  const df = rows.length - xNames.length - 1;
  const mse = sse / df;
  const se = xtxInv.map((row, i) => Math.sqrt(row[i] * mse));
  const coeffs = ["Intercept", ...xNames].map((term, i) => {
    const t = beta[i] / se[i];
    return { term, b: beta[i], se: se[i], t, p: 2 * (1 - studentTCdf(Math.abs(t), df)) };
  });
  const r2 = 1 - sse / sst;
  return { n: rows.length, df, r2, adjR2: 1 - (1 - r2) * ((rows.length - 1) / df), coeffs };
}

function pFmt(value) {
  if (value < 0.001) return "< .001";
  return value.toFixed(3);
}

function fmt(value, digits = 3) {
  return Number.isFinite(value) ? value.toFixed(digits) : "";
}

function getCoeff(model, term) {
  return model.coeffs.find((c) => c.term === term);
}

function centerRows(rows, names) {
  const stats = Object.fromEntries(names.map((name) => [name, { mean: mean(rows.map((r) => r[name])), sd: sd(rows.map((r) => r[name])) }]));
  return rows.map((row) => {
    const out = { ...row };
    for (const name of names) out[`${name}_c`] = row[name] - stats[name].mean;
    return out;
  });
}

const rawRows = parseCsv(fs.readFileSync(inputPath, "utf8"));
const outcomes = ["PCLTot", "K10Tot", "SBQTot", "OPQOLTot", "LGS_Tot"];
const covars = ["Age", "Gender", "Income"];
const resourceSets = [
  { label: "Generativity", vars: ["LGS_Tot"] },
  { label: "Cognitive resources", vars: ["COGTot"] },
  { label: "Generativity + cognitive resources", vars: ["LGS_Tot", "COGTot"] },
];
const moderators = ["LGS_Tot", "COGTot"];
const x = "GriefTot";

const attenuation = [];
for (const y of outcomes) {
  if (y === x) continue;
  const baseRows = completeRows(rawRows, [y, x, ...covars]);
  const base = ols(baseRows, y, [x, ...covars]);
  const baseG = getCoeff(base, x);
  for (const set of resourceSets.filter((set) => !set.vars.includes(y))) {
    const rows = completeRows(rawRows, [y, x, ...covars, ...set.vars]);
    const model = ols(rows, y, [x, ...covars, ...set.vars]);
    const g = getCoeff(model, x);
    attenuation.push({
      outcome: y,
      resourceSet: set.label,
      n: rows.length,
      baseB: baseG.b,
      baseP: baseG.p,
      adjustedB: g.b,
      adjustedP: g.p,
      percentChange: ((g.b - baseG.b) / Math.abs(baseG.b)) * 100,
      adjR2: model.adjR2,
    });
  }
}

const moderation = [];
for (const y of outcomes) {
  if (y === x) continue;
  for (const w of moderators.filter((name) => name !== y)) {
    const rows = completeRows(rawRows, [y, x, w, ...covars]);
    const centered = centerRows(rows, [x, w]);
    for (const row of centered) row.XW = row[`${x}_c`] * row[`${w}_c`];
    const base = ols(centered, y, [`${x}_c`, `${w}_c`, ...covars]);
    const full = ols(centered, y, [`${x}_c`, `${w}_c`, "XW", ...covars]);
    const int = getCoeff(full, "XW");
    const grief = getCoeff(full, `${x}_c`);
    const wSd = sd(rows.map((row) => row[w]));
    const lowSlope = grief.b - int.b * wSd;
    const highSlope = grief.b + int.b * wSd;
    moderation.push({
      outcome: y,
      moderator: w,
      n: rows.length,
      interactionB: int.b,
      interactionSE: int.se,
      interactionP: int.p,
      deltaR2: full.r2 - base.r2,
      griefAtMeanB: grief.b,
      lowModeratorSlope: lowSlope,
      highModeratorSlope: highSlope,
      adjR2: full.adjR2,
    });
  }
}

attenuation.sort((a, b) => a.outcome.localeCompare(b.outcome) || a.resourceSet.localeCompare(b.resourceSet));
moderation.sort((a, b) => a.interactionP - b.interactionP);

const results = { inputPath, attenuation, moderation };
fs.writeFileSync("irreducible_grief_models.json", JSON.stringify(results, null, 2));

const lines = [];
lines.push("# Irreducible Grief Model Checks");
lines.push("");
lines.push("Question: does GriefTot remain associated with outcomes after resource variables are added, and do resources significantly buffer the grief-outcome link?");
lines.push("");
lines.push("Note: MAH_1 is excluded because the SAV label identifies it as Mahalanobis Distance, not a substantive psychological scale.");
lines.push("");
lines.push("## Attenuation Tests");
lines.push("| Outcome | Added resources | N | Grief b base | p base | Grief b adjusted | p adjusted | % change | Adj R2 |");
lines.push("| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |");
for (const r of attenuation) {
  lines.push(`| ${r.outcome} | ${r.resourceSet} | ${r.n} | ${fmt(r.baseB)} | ${pFmt(r.baseP)} | ${fmt(r.adjustedB)} | ${pFmt(r.adjustedP)} | ${fmt(r.percentChange, 1)} | ${fmt(r.adjR2)} |`);
}
lines.push("");
lines.push("## Moderation / Buffering Tests");
lines.push("| Outcome | Moderator | N | Interaction b | SE | p | Delta R2 | Slope at low W | Slope at high W |");
lines.push("| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |");
for (const r of moderation) {
  lines.push(`| ${r.outcome} | ${r.moderator} | ${r.n} | ${fmt(r.interactionB)} | ${fmt(r.interactionSE)} | ${pFmt(r.interactionP)} | ${fmt(r.deltaR2)} | ${fmt(r.lowModeratorSlope)} | ${fmt(r.highModeratorSlope)} |`);
}

fs.writeFileSync("irreducible_grief_models.md", `${lines.join("\n")}\n`);
console.log(lines.join("\n"));
