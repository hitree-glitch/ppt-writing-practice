const fs = require("fs");

const savPath =
  "C:/Users/user/OneDrive/D 대학원 박사/A 아주대/논문 작성/(작업 중) OATrauma_Natural Disaster Subset 7.7.25.sav";
const csvPath =
  "C:/Users/user/OneDrive/D 대학원 박사/A 아주대/논문 작성/(작업 중) OATrauma_Natural Disaster Subset 7.7.25.csv";

function text(buf, off, len) {
  return buf.subarray(off, off + len).toString("latin1").replace(/\0+$/g, "").trimEnd();
}

function i32(buf, off) {
  return buf.readInt32LE(off);
}

function readSavVariables(filePath) {
  const buf = fs.readFileSync(filePath);
  let off = 176;
  const physicalVars = [];
  const longVarNames = {};
  while (off < buf.length) {
    const type = i32(buf, off);
    off += 4;
    if (type === 2) {
      const varType = i32(buf, off);
      const hasLabel = i32(buf, off + 4);
      const nMissing = i32(buf, off + 8);
      const name = text(buf, off + 20, 8).trim();
      off += 28;
      let label = "";
      if (hasLabel) {
        const labelLength = i32(buf, off);
        off += 4;
        label = text(buf, off, labelLength);
        off += Math.ceil(labelLength / 4) * 4;
      }
      for (let k = 0; k < Math.abs(nMissing); k += 1) off += 8;
      physicalVars.push({ varType, shortName: name, label });
    } else if (type === 3) {
      const count = i32(buf, off);
      off += 4;
      for (let j = 0; j < count; j += 1) {
        off += 8;
        const labelLength = buf.readUInt8(off);
        off += 1;
        off += Math.ceil((labelLength + 1) / 8) * 8 - 1;
      }
    } else if (type === 4) {
      const count = i32(buf, off);
      off += 4 + count * 4;
    } else if (type === 6) {
      const lines = i32(buf, off);
      off += 4 + 80 * lines;
    } else if (type === 7) {
      const subtype = i32(buf, off);
      const size = i32(buf, off + 4);
      const count = i32(buf, off + 8);
      off += 12;
      const payload = buf.subarray(off, off + size * count).toString("latin1");
      if (subtype === 13) {
        for (const pair of payload.split("\t")) {
          const [shortName, longName] = pair.split("=");
          if (shortName && longName) longVarNames[shortName.trim()] = longName.trim();
        }
      }
      off += size * count;
    } else if (type === 999) {
      break;
    } else {
      break;
    }
  }
  return physicalVars
    .filter((v) => v.varType !== -1)
    .map((v) => ({ ...v, name: longVarNames[v.shortName] || v.shortName }));
}

function parseCsv(textValue) {
  const rows = [];
  let row = [];
  let field = "";
  let inQuotes = false;
  for (let i = 0; i < textValue.length; i += 1) {
    const ch = textValue[i];
    const next = textValue[i + 1];
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

function corr(rows, a, b) {
  const pairs = rows
    .map((row) => [num(row, a), num(row, b)])
    .filter(([x, y]) => x != null && y != null);
  const mx = mean(pairs.map((p) => p[0]));
  const my = mean(pairs.map((p) => p[1]));
  const sx = sd(pairs.map((p) => p[0]));
  const sy = sd(pairs.map((p) => p[1]));
  const r = pairs.reduce((acc, [x, y]) => acc + ((x - mx) / sx) * ((y - my) / sy), 0) / (pairs.length - 1);
  return { n: pairs.length, r };
}

const savVars = readSavVariables(savPath);
const targetVars = savVars.filter(
  (v) =>
    v.name === "MAH_1" ||
    v.shortName === "MAH_1" ||
    /MAH|mental|health|attitude|mean|center|cent/i.test(`${v.name} ${v.shortName} ${v.label}`)
);

const rows = parseCsv(fs.readFileSync(csvPath, "utf8"));
const headers = Object.keys(rows[0]);
const idx = headers.indexOf("MAH_1");
const around = headers.slice(Math.max(0, idx - 8), idx + 9);
const mahValues = rows.map((row) => num(row, "MAH_1")).filter((v) => v != null);
const unique = new Map();
for (const value of mahValues) unique.set(value, (unique.get(value) || 0) + 1);
const uniqueSorted = [...unique.entries()].sort((a, b) => a[0] - b[0]);
const correlations = ["PCLTot", "K10Tot", "OPQOLTot", "SBQTot", "LGS_Tot", "COGTot", "GriefTot"].map((name) => ({
  variable: name,
  ...corr(rows, "MAH_1", name),
}));

const result = {
  savMatches: targetVars,
  csvColumnIndex: idx,
  columnsAroundMAH_1: around,
  distribution: {
    n: mahValues.length,
    mean: mean(mahValues),
    sd: sd(mahValues),
    min: Math.min(...mahValues),
    max: Math.max(...mahValues),
    uniqueCount: uniqueSorted.length,
    firstValues: uniqueSorted.slice(0, 20).map(([value, count]) => ({ value, count })),
    lastValues: uniqueSorted.slice(-20).map(([value, count]) => ({ value, count })),
  },
  correlations,
};

fs.writeFileSync("inspect_mah1_results.json", JSON.stringify(result, null, 2));
console.log(JSON.stringify(result, null, 2));
