from __future__ import annotations

import html
import json
import re
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlencode, urljoin, urlparse
from urllib.request import Request, urlopen

import pandas as pd

ROOT = Path("RESEARCH/korea_ai_counseling_psych_20260623")
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
SOURCES = ROOT / "sources"
OUTPUTS = ROOT / "outputs"
ARTIFACTS = ROOT / "artifacts"
TEXT_DIR = ARTIFACTS / "extracted_text"

for folder in [RAW, PROCESSED, SOURCES, OUTPUTS, ARTIFACTS, TEXT_DIR]:
    folder.mkdir(parents=True, exist_ok=True)

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Codex-Korea-Research"

NIA_CATEGORIES = [
    ("digital_divide", "디지털정보격차실태조사", "81623", 3, "핵심 AI·디지털 격차 지표"),
    ("smartphone_overdependence", "스마트폰 과의존 실태조사", "65914", 3, "디지털 과의존·심리위험 지표"),
    ("cyber_violence", "사이버폭력 실태조사", "68302", 3, "온라인 피해·정서위험 지표"),
    ("internet_use", "인터넷이용실태조사", "99870", 6, "기본 인터넷·디지털 이용 맥락 지표"),
]

KOSIS_KEYWORDS = [
    "스트레스 인지율",
    "우울감 경험률",
    "자살생각률",
    "정신건강상담",
    "심리상담",
    "상담 경험",
    "정신건강복지센터",
    "정신건강서비스",
    "스마트폰 과의존",
    "인터넷 과의존",
    "디지털정보격차",
    "인공지능 이용",
    "인공지능 서비스 이용",
    "챗GPT 이용",
    "AI 리터러시",
]

AI_TERMS = ["인공지능", "AI", "생성형", "챗GPT", "ChatGPT", "알고리즘", "지능정보", "AI 서비스", "AI서비스"]
PSYCH_TERMS = ["심리", "상담", "스트레스", "우울", "정신건강", "자살", "고립", "외로움", "불안", "중독", "과의존", "피해", "폭력", "도움"]


@dataclass
class NiaFile:
    category: str
    label: str
    role: str
    year: str
    title: str
    posted_date: str
    cb_idx: str
    bc_idx: str
    detail_url: str
    download_url: str
    file_no: str
    filename: str
    path: str
    content_type: str
    size_bytes: int


def fetch(url: str, data: bytes | None = None, timeout: int = 60) -> tuple[bytes, dict[str, str], str]:
    req = Request(url, data=data, headers={"User-Agent": USER_AGENT, "Accept": "*/*"})
    with urlopen(req, timeout=timeout) as resp:
        return resp.read(), {k.lower(): v for k, v in resp.headers.items()}, resp.url


def fetch_text(url: str, data: bytes | None = None, timeout: int = 60) -> str:
    body, headers, _ = fetch(url, data=data, timeout=timeout)
    charset = "utf-8"
    match = re.search(r"charset=([^;\s]+)", headers.get("content-type", ""), re.I)
    if match:
        charset = match.group(1)
    return body.decode(charset, "replace")


def clean(value: Any) -> str:
    text = html.unescape("" if value is None else str(value))
    text = re.sub(r"<script\b[^>]*>.*?</script>", " ", text, flags=re.S | re.I)
    text = re.sub(r"<style\b[^>]*>.*?</style>", " ", text, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def safe_name(value: str) -> str:
    text = re.sub(r"[\\/:*?\"<>|]+", "_", clean(value))
    text = re.sub(r"\s+", "_", text).strip("_")
    return text[:90] or "file"


def year_from(text: str) -> str:
    match = re.search(r"(20\d{2})", text)
    return match.group(1) if match else ""


def ext_from(body: bytes, headers: dict[str, str], url: str) -> str:
    ctype = headers.get("content-type", "").lower()
    if body.startswith(b"%PDF") or "pdf" in ctype:
        return ".pdf"
    if body.startswith(b"PK\x03\x04"):
        # NIA xlsx/hwp sometimes arrive as zip containers. Keep zip to avoid false claims.
        return ".zip"
    if "excel" in ctype or "spreadsheet" in ctype:
        return ".xlsx"
    if "csv" in ctype:
        return ".csv"
    suffix = Path(urlparse(url).path).suffix
    return suffix if suffix else ".bin"


def is_probably_file(body: bytes, headers: dict[str, str]) -> bool:
    ctype = headers.get("content-type", "").lower()
    if body.startswith(b"%PDF") or body.startswith(b"PK\x03\x04"):
        return True
    if "application/" in ctype and "html" not in ctype:
        return True
    if len(body) > 50_000 and b"<html" not in body[:500].lower():
        return True
    return False


def parse_nia_list(category: str, label: str, cb_idx: str, role: str) -> list[dict[str, str]]:
    list_url = f"https://www.nia.or.kr/site/nia_kor/ex/bbs/List.do?cbIdx={cb_idx}"
    text = fetch_text(list_url)
    rows: list[dict[str, str]] = []
    for block in re.findall(r"<li\b.*?</li>", text, flags=re.S | re.I):
        match = re.search(r"doBbsFView\('([^']+)','([^']+)','([^']*)','([^']*)'\)", block)
        if not match:
            continue
        cb, bc, _menu, parent = match.groups()
        title_match = re.search(r'title="([^"]+)"', block)
        title = clean(title_match.group(1) if title_match else block).replace("-첨부파일 있음", "").strip()
        dates = re.findall(r"20\d{2}\.\d{2}\.\d{2}", clean(block))
        rows.append(
            {
                "source": "NIA",
                "category": category,
                "label": label,
                "role": role,
                "year": year_from(title),
                "title": title,
                "posted_date": dates[0] if dates else "",
                "cb_idx": cb,
                "bc_idx": bc,
                "parent_seq": parent or bc,
                "list_url": list_url,
                "detail_url": f"https://www.nia.or.kr/site/nia_kor/ex/bbs/View.do?cbIdx={cb}&bcIdx={bc}&parentSeq={parent or bc}",
            }
        )
    return rows


def download_links(detail_url: str, cb_idx: str, bc_idx: str) -> list[tuple[str, str]]:
    try:
        text = fetch_text(detail_url)
    except Exception:
        text = ""
    found: list[tuple[str, str]] = []
    for pattern in [r'href="([^"]*Download\.do[^"]+)"', r"(/common/board/Download\.do\?[^'\"\s<>]+)"]:
        for raw in re.findall(pattern, text, flags=re.I):
            url = urljoin(detail_url, html.unescape(raw))
            qs = parse_qs(urlparse(url).query)
            file_no = (qs.get("fileNo") or [""])[0]
            if url not in [x[0] for x in found]:
                found.append((url, file_no))
    if found:
        return found
    return [
        (f"https://www.nia.or.kr/common/board/Download.do?bcIdx={bc_idx}&cbIdx={cb_idx}&fileNo={n}", str(n))
        for n in range(1, 4)
    ]


def download_nia(rows: list[dict[str, str]]) -> list[NiaFile]:
    files: list[NiaFile] = []
    for row in rows:
        for url, file_no in download_links(row["detail_url"], row["cb_idx"], row["bc_idx"]):
            try:
                body, headers, final_url = fetch(url, timeout=90)
            except Exception as exc:
                print("download error", row["title"], url, repr(exc))
                continue
            if not is_probably_file(body, headers):
                continue
            ext = ext_from(body, headers, final_url)
            filename = f"{safe_name(row['category'])}_{row['year']}_{row['bc_idx']}_file{file_no or 'x'}{ext}"
            path = RAW / filename
            if not path.exists() or path.stat().st_size != len(body):
                path.write_bytes(body)
            files.append(
                NiaFile(
                    category=row["category"],
                    label=row["label"],
                    role=row["role"],
                    year=row["year"],
                    title=row["title"],
                    posted_date=row["posted_date"],
                    cb_idx=row["cb_idx"],
                    bc_idx=row["bc_idx"],
                    detail_url=row["detail_url"],
                    download_url=final_url,
                    file_no=file_no,
                    filename=path.name,
                    path=str(path),
                    content_type=headers.get("content-type", ""),
                    size_bytes=len(body),
                )
            )
            time.sleep(0.15)
    return files


def term_count(text: str, terms: list[str]) -> int:
    lower = text.lower()
    total = 0
    for term in terms:
        if re.fullmatch(r"[A-Za-z]+", term):
            total += len(re.findall(rf"\b{re.escape(term.lower())}\b", lower))
        else:
            total += text.count(term)
    return total


def present_terms(text: str, terms: list[str]) -> str:
    lower = text.lower()
    found = []
    for term in terms:
        if re.fullmatch(r"[A-Za-z]+", term):
            ok = re.search(rf"\b{re.escape(term.lower())}\b", lower) is not None
        else:
            ok = term in text
        if ok:
            found.append(term)
    return "; ".join(found)


def snippet(text: str, terms: list[str], window: int = 220) -> str:
    compact = re.sub(r"\s+", " ", text).strip()
    if not compact:
        return ""
    positions = []
    lower = compact.lower()
    for term in terms:
        pos = lower.find(term.lower()) if re.fullmatch(r"[A-Za-z]+", term) else compact.find(term)
        if pos >= 0:
            positions.append(pos)
    start = max(0, min(positions) - window) if positions else 0
    return compact[start : start + window * 2]


def pdf_pages(path: Path) -> list[tuple[int, str]]:
    try:
        import pdfplumber  # type: ignore

        with pdfplumber.open(str(path)) as pdf:
            return [(idx, page.extract_text(x_tolerance=1, y_tolerance=3) or "") for idx, page in enumerate(pdf.pages, 1)]
    except Exception:
        try:
            import pypdf  # type: ignore

            reader = pypdf.PdfReader(str(path))
            return [(idx, page.extract_text() or "") for idx, page in enumerate(reader.pages, 1)]
        except Exception as exc:
            return [(0, f"PDF extraction failed: {exc!r}")]


def analyze_pdfs(files: list[NiaFile]) -> tuple[pd.DataFrame, pd.DataFrame]:
    page_rows: list[dict[str, Any]] = []
    both_rows: list[dict[str, Any]] = []
    for item in files:
        path = Path(item.path)
        if path.suffix.lower() != ".pdf":
            continue
        full = []
        for page_no, text in pdf_pages(path):
            full.append(f"\n\n--- page {page_no} ---\n{text}")
            ai = term_count(text, AI_TERMS)
            psych = term_count(text, PSYCH_TERMS)
            terms = present_terms(text, AI_TERMS + PSYCH_TERMS)
            base = {
                "category": item.category,
                "label": item.label,
                "year": item.year,
                "title": item.title,
                "filename": item.filename,
                "page": page_no,
                "ai_term_count": ai,
                "psych_term_count": psych,
                "terms_present": terms,
                "detail_url": item.detail_url,
            }
            if ai or psych:
                page_rows.append(base)
            if ai and psych:
                both_rows.append({**base, "snippet": snippet(text, AI_TERMS + PSYCH_TERMS)})
        (TEXT_DIR / f"{path.stem}.txt").write_text("".join(full), encoding="utf-8")
    return pd.DataFrame(page_rows), pd.DataFrame(both_rows)


def kosis_search(keyword: str) -> dict[str, Any]:
    params = {
        "query": keyword,
        "collection": "statDB",
        "startCount": "0",
        "resultCount": "20",
        "sort": "RANK",
        "reQuery": "",
        "realQuery": keyword,
        "range": "ALL",
        "startDate": "",
        "endDate": "",
        "searchField": "ALL",
        "detailViewStatus": "N",
        "detailQuery": keyword,
        "gbn": "L",
        "categoryPath": "",
        "categoryIdxField": "",
        "categorySort": "kosis",
    }
    body, _, _ = fetch(
        "https://kosis.kr/search/searchStatDBAjax.do",
        data=urlencode(params).encode("utf-8"),
        timeout=45,
    )
    return json.loads(body.decode("utf-8", "replace"))


def collect_kosis() -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    raw: dict[str, Any] = {}
    for keyword in KOSIS_KEYWORDS:
        try:
            data = kosis_search(keyword)
            raw[keyword] = data
            for rank, item in enumerate(data.get("resultList", []), 1):
                org_id = item.get("ORG_ID") or ""
                tbl_id = item.get("TBL_ID") or ""
                rows.append(
                    {
                        "keyword": keyword,
                        "rank": rank,
                        "org_id": org_id,
                        "tbl_id": tbl_id,
                        "table_name": clean(item.get("TBL_NM")),
                        "stat_name": clean(item.get("STAT_NM_KMA") or item.get("STAT_NM")),
                        "org_name": clean(item.get("ORG_NM")),
                        "start_period": item.get("STRT_PRD_DE") or "",
                        "end_period": item.get("END_PRD_DE") or "",
                        "item01": clean(item.get("ITEM01")),
                        "item02": clean(item.get("ITEM02")),
                        "item03": clean(item.get("ITEM03")),
                        "path": clean(item.get("MT_ATITLE")),
                        "official_url": f"https://kosis.kr/statHtml/statHtml.do?orgId={org_id}&tblId={tbl_id}&conn_path=I2"
                        if org_id and tbl_id
                        else "",
                    }
                )
        except Exception as exc:
            rows.append({"keyword": keyword, "rank": "", "error": repr(exc)})
        time.sleep(0.15)
    (ARTIFACTS / "kosis_search_raw.json").write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")
    return pd.DataFrame(rows)


def variable_map() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "construct": "AI exposure / AI literacy",
                "korean_label": "AI 서비스 인지·이용·태도",
                "candidate_source": "NIA 디지털정보격차실태조사 2024-2025 부록/통계표",
                "candidate_variables": "AI 서비스 인지, 이용 경험, 이용 의향, 활용 능력, 도움 필요",
                "paper_role": "핵심 독립변수 또는 매개변수",
                "unit": "개인 원자료 신청 시 개인; 공개 PDF 기준 집단·연도·취약계층 셀",
            },
            {
                "construct": "Digital inclusion",
                "korean_label": "디지털 접근·역량·활용 수준",
                "candidate_source": "NIA 디지털정보격차실태조사",
                "candidate_variables": "디지털정보화 수준, 접근 수준, 역량 수준, 활용 수준, 취약계층 구분",
                "paper_role": "AI 이용 격차의 구조적 원인",
                "unit": "집단·연도 또는 개인",
            },
            {
                "construct": "Digital overdependence",
                "korean_label": "스마트폰/인터넷 과의존 위험",
                "candidate_source": "NIA 스마트폰 과의존 실태조사",
                "candidate_variables": "과의존위험군, 고위험군, 잠재적위험군, 조절실패, 현저성, 문제적 결과",
                "paper_role": "심리상태 결과변수 또는 조절변수",
                "unit": "연령·성별·집단·연도 셀",
            },
            {
                "construct": "Online harm",
                "korean_label": "사이버폭력 피해·가해·목격 경험",
                "candidate_source": "NIA 사이버폭력 실태조사",
                "candidate_variables": "피해 경험률, 유형별 피해, 대응·상담 경험",
                "paper_role": "디지털 환경 위험요인",
                "unit": "연령·성별·학교급·연도 셀",
            },
            {
                "construct": "Mental state",
                "korean_label": "스트레스·우울·자살생각",
                "candidate_source": "KOSIS/KDCA 국민건강영양조사, 지역사회건강조사 등",
                "candidate_variables": "스트레스 인지율, 우울감 경험률, 자살생각률",
                "paper_role": "주요 심리상태 결과변수",
                "unit": "개인 원자료 가능; 공개 KOSIS 기준 연도·성·연령·지역 셀",
            },
            {
                "construct": "Help-seeking / counseling access",
                "korean_label": "심리상담·정신건강서비스 접근",
                "candidate_source": "KOSIS/보건복지부/정신건강복지센터 관련 통계",
                "candidate_variables": "정신건강상담, 정신건강복지센터 이용, 도움 요청 경험",
                "paper_role": "종속변수 또는 정책성과 지표",
                "unit": "지역·연도 기관/이용 지표 또는 개인 원자료",
            },
        ]
    )


def md_table(df: pd.DataFrame, cols: list[str], max_rows: int = 20) -> str:
    if df.empty:
        return "_자료 없음_"
    sub = df[[c for c in cols if c in df.columns]].head(max_rows).fillna("")
    lines = ["| " + " | ".join(sub.columns) + " |", "| " + " | ".join("---" for _ in sub.columns) + " |"]
    for _, row in sub.iterrows():
        lines.append("| " + " | ".join(str(row[c]).replace("\n", " ")[:220] for c in sub.columns) + " |")
    return "\n".join(lines)


def write_docs(
    nia_catalog: pd.DataFrame,
    downloaded: pd.DataFrame,
    pages: pd.DataFrame,
    both: pd.DataFrame,
    kosis: pd.DataFrame,
    variables: pd.DataFrame,
) -> None:
    sources = []
    for category, label, cb_idx, _limit, role in NIA_CATEGORIES:
        sources.append(
            {
                "source": "NIA",
                "title": label,
                "url": f"https://www.nia.or.kr/site/nia_kor/ex/bbs/List.do?cbIdx={cb_idx}",
                "use": role,
                "access_date": "2026-06-23",
            }
        )
    sources.append(
        {
            "source": "KOSIS",
            "title": "국가통계포털 통계DB 검색",
            "url": "https://kosis.kr/search/search.do",
            "use": "정신건강·상담·디지털 이용 후보 테이블 탐색",
            "access_date": "2026-06-23",
        }
    )
    (SOURCES / "sources.jsonl").write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in sources) + "\n",
        encoding="utf-8",
    )

    mental = kosis[
        kosis.get("keyword", pd.Series(dtype=str)).astype(str).str.contains("스트레스|우울|자살|정신건강|상담|심리", regex=True, na=False)
    ] if not kosis.empty else pd.DataFrame()

    summary = f"""# 한국 자료 기반 AI·심리상담/심리상태 논문 데이터 패키지

## 결론 먼저

가장 논문화 가능성이 높은 주제는 **"AI 서비스 이용 격차가 심리상담·정신건강 위험과 어떻게 맞물리는가: 한국 디지털 취약계층의 집단-연도 결합자료 분석"**입니다.

핵심 축은 세 가지입니다.

1. **AI/디지털 리터러시 축**: NIA 디지털정보격차실태조사. 2024년 보고서에는 `인공지능(AI) 서비스 관련` 부록이 확인되어 AI 인지·이용·태도를 직접 다룰 수 있습니다.
2. **디지털 위험 축**: NIA 스마트폰 과의존 실태조사와 사이버폭력 실태조사. 과의존, 온라인 피해, 상담·도움 요청 가능성을 연결할 수 있습니다.
3. **심리상태/상담 축**: KOSIS의 스트레스 인지율, 우울감 경험률, 자살생각률, 정신건강상담·정신건강복지센터 후보 테이블.

## 이번 수집 결과

- NIA 공식 목록에서 수집한 보고서 후보: **{len(nia_catalog):,}건**
- 실제 다운로드한 최신 보고서/통계표 파일: **{len(downloaded):,}개**
- PDF에서 AI 또는 심리 관련어가 발견된 페이지: **{len(pages):,}개**
- AI 관련어와 심리 관련어가 같은 페이지에 함께 나온 핵심 후보 페이지: **{len(both):,}개**
- KOSIS 검색으로 확보한 후보 통계 테이블: **{len(kosis):,}건**

## 1순위 연구질문

**디지털 취약계층에서 AI 서비스 인지·이용 격차는 스마트폰 과의존, 온라인 피해, 스트레스·우울 같은 심리상태 지표와 어떤 방식으로 결합되는가?**

공개자료만으로는 `연도 x 집단` 또는 `연도 x 성별 x 연령` 집계 셀 분석부터 시작하는 것이 안전합니다. 이후 NIA/MDIS/질병관리청 원자료를 확보하면 개인 수준 로지스틱 회귀, 다층모형, 매개·조절모형으로 확장할 수 있습니다.
"""
    (OUTPUTS / "00_executive_summary.md").write_text(summary, encoding="utf-8")

    catalog = f"""# 데이터 카탈로그

## NIA 보고서 후보

{md_table(nia_catalog, ["category", "year", "title", "posted_date", "detail_url"], 30)}

## 다운로드된 파일

{md_table(downloaded, ["category", "year", "title", "filename", "size_bytes"], 40)}

## KOSIS 정신건강·상담 후보

{md_table(mental, ["keyword", "rank", "org_id", "tbl_id", "table_name", "stat_name", "end_period", "official_url"], 40)}
"""
    (OUTPUTS / "01_data_catalog.md").write_text(catalog, encoding="utf-8")

    relevant = both.sort_values(["year", "category", "page"], ascending=[False, True, True]) if not both.empty else both
    (OUTPUTS / "02_ai_psych_relevant_pages.md").write_text(
        "# AI·심리 관련 핵심 페이지 후보\n\n"
        + "공개 PDF에서 AI 관련어와 심리·상담 관련어가 같은 페이지에 함께 나온 후보입니다. 수치 인용 전에는 원 PDF 표 번호와 주석을 다시 확인해야 합니다.\n\n"
        + md_table(relevant, ["category", "year", "title", "page", "terms_present", "snippet"], 50),
        encoding="utf-8",
    )

    design = """# 연구설계 초안

## 추천 제목

AI 리터러시 격차와 심리상담 접근성: 한국 디지털 취약계층의 디지털정보격차·과의존·정신건강 지표 결합 분석

## 가설

H1. 디지털정보화 역량이 낮은 집단일수록 AI 서비스 인지·이용 수준이 낮다.

H2. AI 서비스 이용 격차는 연령, 장애, 소득, 농어민, 이주 배경 등 기존 디지털 취약성에 따라 확대된다.

H3. 스마트폰 과의존 또는 사이버폭력 피해가 높은 집단·연령대에서는 스트레스·우울·상담 필요 지표가 높게 나타난다.

H4. AI 이용 경험은 심리상담 접근성에 양면적으로 작동할 수 있다. 정보탐색·상담 접근을 높일 수 있지만, 낮은 AI 리터러시 집단에서는 오정보·비이용 격차가 더 커질 수 있다.

## 분석 단위

1차 공개자료 분석은 `연도 x 집단` 또는 `연도 x 성별 x 연령` 집계 셀을 권장합니다. NIA 디지털 취약계층 구분과 KOSIS 정신건강 지표의 연령·성별·지역 구분이 완전히 일치하지 않을 수 있으므로, 논문에서는 생태학적 결합자료라는 한계를 명확히 두는 것이 안전합니다.

## 모델

- 기술통계: AI 인지·이용, 디지털 역량, 과의존 위험, 스트레스/우울 지표의 연도별 변화
- 집단 비교: 고령층·장애인·저소득층·농어민·결혼이민자·북한이탈주민 간 격차
- 결합 패널: 집단 또는 연령대별 AI/디지털 지표와 심리상태 지표의 상관·고정효과 탐색
- 원자료 확보 시: 개인 수준 로지스틱 회귀, 다층모형, 매개·조절모형

## 차별점

기존 연구가 디지털 격차, 스마트폰 과의존, 정신건강을 따로 보는 경우가 많다면, 이 설계는 **생성형 AI 시대의 새 디지털 격차가 심리상담 접근성과 정신건강 위험을 동시에 재배열하는지**를 한국 공식자료로 묻습니다.
"""
    (OUTPUTS / "03_research_design.md").write_text(design, encoding="utf-8")

    limits = """# 자료 접근성과 다음 단계

## 현재 확보 가능한 것

NIA 공식 홈페이지에서 PDF 보고서와 일부 통계표 파일을 직접 내려받을 수 있습니다. KOSIS는 정신건강·상담 관련 통계DB 후보 테이블 ID와 공식 열람 URL을 확보할 수 있습니다.

## 제한

공개 보고서 PDF만으로는 개인 단위의 AI 이용 경험과 상담 행동을 같은 사람에게서 연결하기 어렵습니다. 따라서 현재 산출물은 논문 기획과 집계자료 분석용입니다. 강한 개인 수준 인과모형을 쓰려면 NIA 원자료, 지역사회건강조사, 국민건강영양조사, 청소년건강행태조사 등 원자료 신청이 필요합니다.

## 권장 확장

1. NIA 디지털정보격차실태조사 원자료 또는 통계표 확보
2. KOSIS 후보 테이블 중 스트레스·우울·자살생각·정신건강상담 지표를 연령/성/지역 단위로 다운로드
3. 집단 정의가 맞는 수준으로 셀을 맞춘 뒤 패널 데이터 구성
4. 원자료 확보 전에는 `관련성/격차/정책 타깃팅` 논문으로 쓰고, 원자료 확보 후 `개인 수준 예측/매개` 논문으로 확장
"""
    (OUTPUTS / "04_access_limitations_and_next_steps.md").write_text(limits, encoding="utf-8")


def main() -> None:
    all_rows: list[dict[str, str]] = []
    to_download: list[dict[str, str]] = []
    for category, label, cb_idx, limit, role in NIA_CATEGORIES:
        rows = parse_nia_list(category, label, cb_idx, role)
        all_rows.extend(rows)
        to_download.extend(rows[:limit])

    nia_catalog = pd.DataFrame(all_rows)
    nia_catalog.to_csv(PROCESSED / "nia_report_catalog.csv", index=False, encoding="utf-8-sig")

    files = download_nia(to_download)
    downloaded = pd.DataFrame([asdict(item) for item in files])
    downloaded.to_csv(PROCESSED / "nia_downloaded_files.csv", index=False, encoding="utf-8-sig")

    pages, both = analyze_pdfs(files)
    pages.to_csv(PROCESSED / "nia_relevant_pages.csv", index=False, encoding="utf-8-sig")
    both.to_csv(PROCESSED / "nia_ai_psych_snippets.csv", index=False, encoding="utf-8-sig")

    kosis = collect_kosis()
    kosis.to_csv(PROCESSED / "kosis_candidate_tables.csv", index=False, encoding="utf-8-sig")

    variables = variable_map()
    variables.to_csv(PROCESSED / "korea_ai_psych_variable_map.csv", index=False, encoding="utf-8-sig")

    write_docs(nia_catalog, downloaded, pages, both, kosis, variables)
    print(
        json.dumps(
            {
                "nia_catalog_rows": len(nia_catalog),
                "downloaded_files": len(downloaded),
                "relevant_pdf_pages": len(pages),
                "ai_psych_snippet_pages": len(both),
                "kosis_candidates": len(kosis),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
