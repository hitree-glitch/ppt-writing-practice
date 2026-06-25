#!/usr/bin/env python3
"""Build a fixed PyInstaller exe by patching only selected bytecode functions."""

from __future__ import annotations

from dataclasses import dataclass
import marshal
from pathlib import Path
import struct
import types
import zlib


COOKIE_MAGIC = b"MEI\014\013\012\013\016"
ROOT = Path(__file__).resolve().parent
SOURCE_EXE = Path(r"C:\Users\user\바탕화면\N 자동화\260326_aiposting.exe")
EXTRACT = ROOT / "extracted_260326_aiposting"
PYZ_EXTRACTED = EXTRACT / "PYZ-00.pyz_extracted"
SOURCE_PYZ = EXTRACT / "PYZ.pyz"
PATCHED_DIR = ROOT / "patched"
PATCHED_MAIN_PYC = PATCHED_DIR / "AI글쓰기자동화봇_ChatGPT3.pyc"
PATCHED_NAVER_PYC = PATCHED_DIR / "naver_fixed.pyc"
PATCHED_NAVERBLOG_PYC = PATCHED_DIR / "naverblog_fixed.pyc"
PATCHED_PYZ = PATCHED_DIR / "PYZ_fixed.pyz"
OUTPUT_EXE = ROOT / "260326_aiposting_fixed.exe"


@dataclass
class Cookie:
    pos: int
    pkg_len: int
    toc_pos: int
    toc_len: int
    py_ver: int
    pylib: bytes
    size: int


@dataclass
class TocEntry:
    name_bytes: bytes
    name: str
    pos: int
    comp_len: int
    uncomp_len: int
    comp_flag: int
    type_code: int


def code_from_source(source: str, func_name: str, filename: str) -> types.CodeType:
    namespace: dict[str, object] = {}
    compiled = compile(source, filename, "exec")
    exec(compiled, namespace)
    return namespace[func_name].__code__


def replacement_input_text_mixed_code() -> types.CodeType:
    source = r'''

def input_text_mixed(driver, text, use_clipboard_probability=1.0):
    if text is None:
        return True
    content = str(text)
    if not content:
        return True

    def focus_body_editor():
        try:
            return bool(driver.execute_script("""
const selectors = [
  ".se-main-container .se-section-text [contenteditable='true']",
  ".se-main-container .se-section-text .se-text-paragraph",
  ".se-main-container .se-module-text [contenteditable='true']",
  ".se-main-container .se-component-content [contenteditable='true']",
  ".se-main-container .se-text-paragraph",
  ".se-main-container div[contenteditable='true']",
  "div[contenteditable='true']"
];
function isTitleArea(el) {
  if (!el || !el.closest) return false;
  return !!el.closest(".se-section-documentTitle, .se-documentTitle, .se-title-text, .se-title, [class*='documentTitle'], [class*='DocumentTitle'], [class*='document-title'], [class*='Document-title']");
}
function editableTarget(el) {
  if (!el) return null;
  if (el.isContentEditable || el.getAttribute("contenteditable") === "true") return el;
  return el.closest ? el.closest("[contenteditable='true']") : null;
}
function usable(el) {
  const target = editableTarget(el);
  if (!target || isTitleArea(target) || isTitleArea(el)) return false;
  const rect = target.getBoundingClientRect();
  return rect.width > 0 && rect.height > 0;
}
function placeCaretAtEnd(el) {
  const target = editableTarget(el);
  if (!target) return false;
  target.scrollIntoView({block: "center"});
  target.focus();
  const range = document.createRange();
  range.selectNodeContents(target);
  range.collapse(false);
  const sel = window.getSelection();
  sel.removeAllRanges();
  sel.addRange(range);
  return true;
}
if (usable(document.activeElement)) {
  return placeCaretAtEnd(document.activeElement);
}
for (const selector of selectors) {
  for (const el of document.querySelectorAll(selector)) {
    if (usable(el)) return placeCaretAtEnd(el);
  }
}
return false;
"""))
        except Exception:
            return False

    if not focus_body_editor():
        print("    - ??: ?? ?? ?? ?? ?? ?? ? ????? ??????.")
        return False

    pyperclip.copy(content)
    actions = ActionChains(driver)
    actions.key_down(Keys.CONTROL).send_keys("v").key_up(Keys.CONTROL).perform()
    time.sleep(0.08)
    return True
'''
    return code_from_source(source, "input_text_mixed", "naverblog.py")


def replacement_write_text_code() -> types.CodeType:
    source = r'''

def write_text(driver, text):
    if text is None:
        return None
    raw_text = str(text)
    if not raw_text:
        return None

    import html

    def focus_editor():
        try:
            return bool(driver.execute_script("""
const selectors = [
  ".se-main-container .se-section-text [contenteditable='true']",
  ".se-main-container .se-section-text .se-text-paragraph",
  ".se-main-container .se-module-text [contenteditable='true']",
  ".se-main-container .se-component-content [contenteditable='true']",
  ".se-main-container .se-text-paragraph",
  ".se-main-container div[contenteditable='true']",
  "div[contenteditable='true']"
];
function isTitleArea(el) {
  if (!el || !el.closest) return false;
  return !!el.closest(".se-section-documentTitle, .se-documentTitle, .se-title-text, .se-title, [class*='documentTitle'], [class*='DocumentTitle'], [class*='document-title'], [class*='Document-title']");
}
function editableTarget(el) {
  if (!el) return null;
  if (el.isContentEditable || el.getAttribute("contenteditable") === "true") return el;
  return el.closest ? el.closest("[contenteditable='true']") : null;
}
function usable(el) {
  const target = editableTarget(el);
  if (!target || isTitleArea(target) || isTitleArea(el)) return false;
  const rect = target.getBoundingClientRect();
  return rect.width > 0 && rect.height > 0;
}
function placeCaretAtEnd(el) {
  const target = editableTarget(el);
  if (!target) return false;
  target.scrollIntoView({block: "center"});
  target.focus();
  const range = document.createRange();
  range.selectNodeContents(target);
  range.collapse(false);
  const sel = window.getSelection();
  sel.removeAllRanges();
  sel.addRange(range);
  return true;
}
if (usable(document.activeElement)) {
  return placeCaretAtEnd(document.activeElement);
}
for (const selector of selectors) {
  for (const el of document.querySelectorAll(selector)) {
    if (usable(el)) return placeCaretAtEnd(el);
  }
}
return false;
"""))
        except Exception:
            return False

    def editor_text_length():
        try:
            value = driver.execute_script("""
function isTitleArea(el) {
  if (!el || !el.closest) return false;
  return !!el.closest(".se-section-documentTitle, .se-documentTitle, .se-title-text, .se-title, [class*='documentTitle'], [class*='DocumentTitle'], [class*='document-title'], [class*='Document-title']");
}
const roots = Array.from(document.querySelectorAll(
  ".se-main-container .se-section-text, .se-main-container .se-module-text, .se-main-container .se-component-content"
)).filter(el => !isTitleArea(el));
if (roots.length) return roots.map(el => el.innerText || "").join("\n").length;
const root = document.querySelector(".se-main-container") || document.body;
return root && root.innerText ? root.innerText.length : 0;
""")
            return int(value or 0)
        except Exception:
            return 0

    def insert_html(markup):
        before_len = editor_text_length()
        ok = driver.execute_script("""
const markup = arguments[0];
const selectors = [
  ".se-main-container .se-section-text [contenteditable='true']",
  ".se-main-container .se-section-text .se-text-paragraph",
  ".se-main-container .se-module-text [contenteditable='true']",
  ".se-main-container .se-component-content [contenteditable='true']",
  ".se-main-container .se-text-paragraph",
  ".se-main-container div[contenteditable='true']",
  "div[contenteditable='true']"
];
function isTitleArea(el) {
  if (!el || !el.closest) return false;
  return !!el.closest(".se-section-documentTitle, .se-documentTitle, .se-title-text, .se-title, [class*='documentTitle'], [class*='DocumentTitle'], [class*='document-title'], [class*='Document-title']");
}
function editableTarget(el) {
  if (!el) return null;
  if (el.isContentEditable || el.getAttribute("contenteditable") === "true") return el;
  return el.closest ? el.closest("[contenteditable='true']") : null;
}
function usable(el) {
  const target = editableTarget(el);
  if (!target || isTitleArea(target) || isTitleArea(el)) return false;
  const rect = target.getBoundingClientRect();
  return rect.width > 0 && rect.height > 0;
}
function focusBody() {
  if (usable(document.activeElement)) return editableTarget(document.activeElement);
  for (const selector of selectors) {
    for (const el of document.querySelectorAll(selector)) {
      if (usable(el)) return editableTarget(el);
    }
  }
  return null;
}
const active = focusBody();
if (!active) return false;
active.scrollIntoView({block: "center"});
active.focus();
const range = document.createRange();
range.selectNodeContents(active);
range.collapse(false);
const sel = window.getSelection();
sel.removeAllRanges();
sel.addRange(range);
try {
  return document.execCommand("insertHTML", false, markup);
} catch (error) {
  return false;
}
""", markup)
        time.sleep(0.08)
        after_len = editor_text_length()
        if not ok or after_len <= before_len:
            raise RuntimeError("Naver editor ignored fast HTML insert")
        return True

    def escape_inline(raw):
        escaped = html.escape(str(raw), quote=False)
        return re.sub(r"\*\*(.*?)\*\*", lambda m: "<strong>" + html.escape(m.group(1), quote=False) + "</strong>", escaped)

    def heading_html(raw):
        label = str(raw).strip().lstrip("#").strip()
        if not label:
            return ""
        return (
            '<p style="margin:30px 0 16px 0; line-height:1.55;">'
            '<strong><span style="font-size:26px; font-weight:700;">'
            + html.escape(label, quote=False)
            + '</span></strong></p><p><br></p>'
        )

    def body_html(raw):
        return (
            '<p style="margin:0 0 18px 0; line-height:1.95;">'
            '<span style="font-size:16px;">'
            + escape_inline(raw)
            + '</span></p><p><br></p>'
        )

    def normalize(raw):
        raw = str(raw).replace("\r\n", "\n").replace("\r", "\n")
        raw = raw.replace("\u200b", "")
        raw = re.sub(r"[ \t]+", " ", raw)
        raw = re.sub(r"\s*---\s*(?=#)", "\n\n", raw)
        raw = re.sub(r"([.!????])\s+", r"\1\n\n", raw)
        raw = re.sub(r"([.!????])(?=[\"')\]]?[\uac00-\ud7a3A-Za-z0-9#])", r"\1\n\n", raw)
        raw = re.sub(r"(?<!^)(?<!\n)(#[0-9A-Za-z_\uac00-\ud7a3]+)", r"\n\n\1", raw)
        return raw

    def split_blocks(raw, max_chars=92):
        blocks = []
        for part in normalize(raw).split("\n"):
            part = part.strip()
            if not part:
                continue
            if part.startswith("#"):
                blocks.append(part)
                continue
            while len(part) > max_chars:
                split_at = part.rfind(" ", 0, max_chars + 1)
                if split_at < max_chars // 2:
                    split_at = max_chars
                blocks.append(part[:split_at].strip())
                part = part[split_at:].strip()
            if part:
                blocks.append(part)
        return blocks

    def is_heading(raw):
        stripped = str(raw).strip()
        if stripped.startswith("#") and not stripped.startswith("## ??"):
            return True
        if re.match(r"^(??|??|??|??|???|?????|????|????)[,.:]?", stripped):
            return True
        return len(stripped) <= 34 and not re.search(r"[.!????]$", stripped) and not stripped.startswith("#")

    if not raw_text.strip():
        try:
            insert_html("<p><br></p>")
            return None
        except Exception:
            input_text_mixed(driver, "\n\n", use_clipboard_probability=1.0)
            return None

    markup = []
    for block in split_blocks(raw_text):
        if is_heading(block):
            markup.append(heading_html(block))
        else:
            markup.append(body_html(block))
    if not markup:
        return None

    try:
        insert_html("".join(markup))
    except Exception:
        fallback = "\n\n".join(block.strip().lstrip("#").strip() for block in split_blocks(raw_text) if block.strip())
        if fallback:
            input_text_mixed(driver, fallback + "\n\n", use_clipboard_probability=1.0)
    return None
'''
    return code_from_source(source, "write_text", "naverblog.py")


def replacement_write_quote_code() -> types.CodeType:
    source = r'''

def write_quote(driver, quote_text):
    heading = str(quote_text or "").strip()
    if not heading:
        return None

    import html

    def editor_text_length():
        try:
            value = driver.execute_script("""
function isTitleArea(el) {
  if (!el || !el.closest) return false;
  return !!el.closest(".se-section-documentTitle, .se-documentTitle, .se-title-text, .se-title, [class*='documentTitle'], [class*='DocumentTitle'], [class*='document-title'], [class*='Document-title']");
}
const roots = Array.from(document.querySelectorAll(
  ".se-main-container .se-section-text, .se-main-container .se-module-text, .se-main-container .se-component-content"
)).filter(el => !isTitleArea(el));
if (roots.length) return roots.map(el => el.innerText || "").join("\n").length;
const root = document.querySelector(".se-main-container") || document.body;
return root && root.innerText ? root.innerText.length : 0;
""")
            return int(value or 0)
        except Exception:
            return 0

    try:
        html_text = html.escape(heading, quote=False)
        before_len = editor_text_length()
        script = """
const text = arguments[0];
const selectors = [
  ".se-main-container .se-section-text [contenteditable='true']",
  ".se-main-container .se-section-text .se-text-paragraph",
  ".se-main-container .se-module-text [contenteditable='true']",
  ".se-main-container .se-component-content [contenteditable='true']",
  ".se-main-container .se-text-paragraph",
  ".se-main-container div[contenteditable='true']",
  "div[contenteditable='true']"
];
function isTitleArea(el) {
  if (!el || !el.closest) return false;
  return !!el.closest(".se-section-documentTitle, .se-documentTitle, .se-title-text, .se-title, [class*='documentTitle'], [class*='DocumentTitle'], [class*='document-title'], [class*='Document-title']");
}
function editableTarget(el) {
  if (!el) return null;
  if (el.isContentEditable || el.getAttribute("contenteditable") === "true") return el;
  return el.closest ? el.closest("[contenteditable='true']") : null;
}
function usable(el) {
  const target = editableTarget(el);
  if (!target || isTitleArea(target) || isTitleArea(el)) return false;
  const rect = target.getBoundingClientRect();
  return rect.width > 0 && rect.height > 0;
}
function focusBody() {
  if (usable(document.activeElement)) return editableTarget(document.activeElement);
  for (const selector of selectors) {
    for (const el of document.querySelectorAll(selector)) {
      if (usable(el)) return editableTarget(el);
    }
  }
  return null;
}
const active = focusBody();
if (!active) return false;
active.scrollIntoView({block: "center"});
active.focus();
const range = document.createRange();
range.selectNodeContents(active);
range.collapse(false);
const sel = window.getSelection();
sel.removeAllRanges();
sel.addRange(range);
const p = document.createElement('p');
const before = document.createElement('p');
before.innerHTML = '<br>';
const span = document.createElement('span');
span.innerHTML = text;
span.style.fontSize = '28px';
span.style.fontWeight = '700';
span.style.lineHeight = '1.55';
span.style.display = 'inline-block';
p.appendChild(span);
p.style.margin = '32px 0 18px 0';
return document.execCommand('insertHTML', false, before.outerHTML + p.outerHTML + '<p><br></p>');
"""
        ok = driver.execute_script(script, html_text)
        time.sleep(0.08)
        if not ok or editor_text_length() <= before_len:
            raise RuntimeError("Naver editor ignored fast heading insert")
        return None
    except Exception:
        pass

    actions = ActionChains(driver)
    actions.key_down(Keys.CONTROL).send_keys("b").key_up(Keys.CONTROL).perform()
    time.sleep(0.03)
    input_text_mixed(driver, heading, use_clipboard_probability=1.0)
    actions = ActionChains(driver)
    actions.key_down(Keys.CONTROL).send_keys("b").key_up(Keys.CONTROL).perform()
    actions.send_keys(Keys.ENTER).send_keys(Keys.ENTER).perform()
    time.sleep(0.05)
    return None
'''
    return code_from_source(source, "write_quote", "naverblog.py")


def replacement_get_top_post_code() -> types.CodeType:
    source = r'''
def get_top_post(keyword, post_count=3):
    import html
    import re
    from urllib.parse import parse_qs, urlparse

    def normalize_blog_url(raw_url):
        if not raw_url:
            return None
        raw = html.unescape(str(raw_url)).strip().strip("\"'<>")
        raw = raw.replace("\\/", "/")
        parsed = urlparse(raw)
        host = parsed.netloc.lower()
        if host not in {"blog.naver.com", "m.blog.naver.com"}:
            return None
        path_parts = [part for part in parsed.path.split("/") if part]
        if len(path_parts) >= 2:
            match = re.match(r"(\d+)", path_parts[1])
            if match:
                return f"https://blog.naver.com/{path_parts[0]}/{match.group(1)}"
        if path_parts and path_parts[0].lower() == "postview.naver":
            query = parse_qs(parsed.query)
            blog_id = (query.get("blogId") or query.get("blogid") or [""])[0]
            log_no = (query.get("logNo") or query.get("logno") or [""])[0]
            if blog_id and log_no:
                return f"https://blog.naver.com/{blog_id}/{log_no}"
        return None

    def add(url, urls, seen):
        if url and url not in seen:
            seen.add(url)
            urls.append(url)

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": "https://search.naver.com/",
    }
    params = {"where": "blog", "query": str(keyword)}

    try:
        response = requests.get(
            "https://search.naver.com/search.naver",
            headers=headers,
            params=params,
            timeout=15,
        )
        response.raise_for_status()
    except Exception:
        return []

    urls = []
    seen = set()

    try:
        soup = BeautifulSoup(response.text, "html.parser")
        selectors = [
            "a.title_link",
            "a.api_txt_lines",
            "a.total_tit",
            "a.name",
            "a[href*='blog.naver.com']",
        ]
        for selector in selectors:
            for anchor in soup.select(selector):
                add(normalize_blog_url(anchor.get("href")), urls, seen)
                if len(urls) >= int(post_count):
                    return urls[: int(post_count)]
    except Exception:
        pass

    pattern = re.compile(
        r"https?:\\?/\\?/(?:m\.)?blog\.naver\.com\\?/[^\s\"'<>]+",
        re.IGNORECASE,
    )
    for match in pattern.finditer(response.text or ""):
        add(normalize_blog_url(match.group(0)), urls, seen)
        if len(urls) >= int(post_count):
            break

    return urls[: int(post_count)]
'''
    return code_from_source(source, "get_top_post", "naver.py")


def replace_code_objects(
    code: types.CodeType, replacements: dict[str, types.CodeType], counts: dict[str, int]
) -> types.CodeType:
    new_consts = []
    changed = False
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            if const.co_name in replacements:
                new_consts.append(replacements[const.co_name])
                counts[const.co_name] = counts.get(const.co_name, 0) + 1
                changed = True
            else:
                new_const = replace_code_objects(const, replacements, counts)
                new_consts.append(new_const)
                changed = changed or new_const is not const
        else:
            new_consts.append(const)
    if changed:
        return code.replace(co_consts=tuple(new_consts))
    return code


def patch_pyc(source_pyc: Path, output_pyc: Path, replacements: dict[str, types.CodeType]) -> None:
    data = source_pyc.read_bytes()
    header = data[:16]
    code = marshal.loads(data[16:])
    counts: dict[str, int] = {}
    patched_code = replace_code_objects(code, replacements, counts)
    missing = [name for name in replacements if counts.get(name, 0) != 1]
    if missing:
        raise RuntimeError(f"{source_pyc.name}: expected one replacement for each, counts={counts}")
    output_pyc.parent.mkdir(parents=True, exist_ok=True)
    output_pyc.write_bytes(header + marshal.dumps(patched_code))
    print(f"patched_pyc: {output_pyc.name} counts={counts}")


def patch_module_pycs() -> None:
    patch_pyc(
        PYZ_EXTRACTED / "naverblog.pyc",
        PATCHED_NAVERBLOG_PYC,
        {
            "input_text_mixed": replacement_input_text_mixed_code(),
            "write_text": replacement_write_text_code(),
            "write_quote": replacement_write_quote_code(),
        },
    )
    patch_pyc(
        PYZ_EXTRACTED / "naver.pyc",
        PATCHED_NAVER_PYC,
        {"get_top_post": replacement_get_top_post_code()},
    )


def rebuild_pyz() -> None:
    pyz = SOURCE_PYZ.read_bytes()
    toc_offset = struct.unpack("!I", pyz[8:12])[0]
    toc = marshal.loads(pyz[toc_offset:])
    min_payload_pos = min(entry[1][1] for entry in toc if len(entry[1]) == 3 and entry[1][2] > 0)
    prefix = bytearray(pyz[:min_payload_pos])
    replacements = {
        "naver": PATCHED_NAVER_PYC.read_bytes()[16:],
        "naverblog": PATCHED_NAVERBLOG_PYC.read_bytes()[16:],
    }

    body = bytearray()
    new_toc = []
    patched: dict[str, int] = {name: 0 for name in replacements}
    for name, entry in toc:
        type_code, pos, length = entry
        if length <= 0:
            new_toc.append((name, (type_code, pos, length)))
            continue
        if name in replacements:
            raw = zlib.compress(replacements[name], 9)
            patched[name] += 1
        else:
            raw = pyz[pos : pos + length]
        new_pos = len(prefix) + len(body)
        body.extend(raw)
        new_toc.append((name, (type_code, new_pos, len(raw))))

    if any(count != 1 for count in patched.values()):
        raise RuntimeError(f"Unexpected PYZ patch counts: {patched}")

    new_toc_offset = len(prefix) + len(body)
    prefix[8:12] = struct.pack("!I", new_toc_offset)
    PATCHED_PYZ.write_bytes(bytes(prefix) + bytes(body) + marshal.dumps(new_toc))
    print(f"patched_pyz: {PATCHED_PYZ}")


def find_cookie(blob: bytes) -> Cookie:
    pos = blob.rfind(COOKIE_MAGIC)
    if pos < 0:
        raise RuntimeError("PyInstaller cookie not found")
    if pos + 88 <= len(blob):
        _magic, pkg_len, toc_pos, toc_len, py_ver, pylib = struct.unpack("!8sIIII64s", blob[pos : pos + 88])
        return Cookie(pos, pkg_len, toc_pos, toc_len, py_ver, pylib, 88)
    _magic, pkg_len, toc_pos, toc_len, py_ver = struct.unpack("!8sIIII", blob[pos : pos + 24])
    return Cookie(pos, pkg_len, toc_pos, toc_len, py_ver, b"", 24)


def parse_carchive_toc(blob: bytes, pkg_start: int, cookie: Cookie) -> list[TocEntry]:
    entries: list[TocEntry] = []
    cursor = pkg_start + cookie.toc_pos
    end = cursor + cookie.toc_len
    while cursor < end:
        entry_size = struct.unpack("!I", blob[cursor : cursor + 4])[0]
        raw = blob[cursor : cursor + entry_size]
        pos, comp_len, uncomp_len, comp_flag, type_code = struct.unpack("!IIIbb", raw[4:18])
        name_bytes = raw[18:].split(b"\0", 1)[0]
        entries.append(
            TocEntry(
                name_bytes=name_bytes,
                name=name_bytes.decode("utf-8", "replace"),
                pos=pos,
                comp_len=comp_len,
                uncomp_len=uncomp_len,
                comp_flag=comp_flag,
                type_code=type_code,
            )
        )
        cursor += entry_size
    return entries


def pack_carchive_toc_entry(entry: TocEntry) -> bytes:
    name = entry.name_bytes + b"\0"
    entry_size = 18 + len(name)
    return (
        struct.pack("!I", entry_size)
        + struct.pack("!IIIbb", entry.pos, entry.comp_len, entry.uncomp_len, entry.comp_flag, entry.type_code)
        + name
    )


def rebuild_exe() -> None:
    source_exe = SOURCE_EXE
    if not source_exe.exists():
        for candidate in (
            ROOT / "260326_aiposting_fixed.exe",
            ROOT / "260326_aiposting_no_expiry_original_speed.exe",
            ROOT / "260326_aiposting_patched.exe",
        ):
            if candidate.exists():
                source_exe = candidate
                print(f"source_exe_fallback: {source_exe}")
                break
    if not source_exe.exists():
        raise FileNotFoundError(f"Source exe not found: {SOURCE_EXE}")
    if not PATCHED_MAIN_PYC.exists():
        raise FileNotFoundError(f"Missing patched main pyc: {PATCHED_MAIN_PYC}")

    blob = source_exe.read_bytes()
    cookie = find_cookie(blob)
    pkg_start = len(blob) - cookie.pkg_len
    bootloader = blob[:pkg_start]
    entries = parse_carchive_toc(blob, pkg_start, cookie)
    patched_main_payload = PATCHED_MAIN_PYC.read_bytes()[16:]
    patched_pyz_payload = PATCHED_PYZ.read_bytes()

    data_section = bytearray()
    new_entries: list[TocEntry] = []
    patched_main = 0
    patched_pyz = 0

    for entry in entries:
        raw = blob[pkg_start + entry.pos : pkg_start + entry.pos + entry.comp_len]
        payload = zlib.decompress(raw) if entry.comp_flag else raw

        if chr(entry.type_code) == "s" and entry.name.endswith("_ChatGPT3"):
            payload = patched_main_payload
            patched_main += 1
        elif entry.name == "PYZ.pyz" and chr(entry.type_code) == "z":
            payload = patched_pyz_payload
            patched_pyz += 1

        pos = len(data_section)
        packed = zlib.compress(payload, 9) if entry.comp_flag else payload
        data_section.extend(packed)
        new_entries.append(
            TocEntry(
                name_bytes=entry.name_bytes,
                name=entry.name,
                pos=pos,
                comp_len=len(packed),
                uncomp_len=len(payload),
                comp_flag=entry.comp_flag,
                type_code=entry.type_code,
            )
        )

    if patched_main != 1 or patched_pyz != 1:
        raise RuntimeError(f"Patch counts unexpected: main={patched_main}, pyz={patched_pyz}")

    toc = b"".join(pack_carchive_toc_entry(entry) for entry in new_entries)
    toc_pos = len(data_section)
    toc_len = len(toc)
    pkg_len = len(data_section) + toc_len + cookie.size
    if cookie.size == 88:
        new_cookie = struct.pack("!8sIIII64s", COOKIE_MAGIC, pkg_len, toc_pos, toc_len, cookie.py_ver, cookie.pylib)
    else:
        new_cookie = struct.pack("!8sIIII", COOKIE_MAGIC, pkg_len, toc_pos, toc_len, cookie.py_ver)

    OUTPUT_EXE.write_bytes(bootloader + data_section + toc + new_cookie)
    print(f"patched_exe: {OUTPUT_EXE}")
    print(f"old_size: {len(blob)}")
    print(f"new_size: {OUTPUT_EXE.stat().st_size}")


def main() -> int:
    patch_module_pycs()
    rebuild_pyz()
    rebuild_exe()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
