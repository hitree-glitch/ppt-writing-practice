"""Runtime-only text-entry patch for the extracted naverblog module."""

from __future__ import annotations

import re
import time


_naverblog = None


def _deps():
    if _naverblog is None:
        raise RuntimeError("naverblog runtime patch has not been applied")
    return _naverblog.ActionChains, _naverblog.Keys, _naverblog.pyperclip


def input_text_mixed(driver, text, use_clipboard_probability=1.0):
    """Paste the whole text at once instead of slow simulated typing."""
    if text is None:
        return True

    content = str(text)
    if not content:
        return True

    action_chains, keys, pyperclip = _deps()
    pyperclip.copy(content)
    actions = action_chains(driver)
    actions.key_down(keys.CONTROL).send_keys("v").key_up(keys.CONTROL).perform()
    time.sleep(0.05)
    return True


def _process_bold_text(text):
    parts = []
    pattern = r"\*\*(.*?)\*\*"
    last_end = 0

    for match in re.finditer(pattern, text):
        if match.start() > last_end:
            parts.append((False, text[last_end:match.start()]))
        parts.append((True, match.group(1)))
        last_end = match.end()

    if last_end < len(text):
        parts.append((False, text[last_end:]))

    return parts or [(False, text)]


def improve_line_breaks(text, max_line_chars=72):
    """Add readable line breaks without touching headings or tag lines."""
    if not text:
        return ""

    raw = str(text).replace("\r\n", "\n").replace("\r", "\n")
    lines = []
    for original_line in raw.split("\n"):
        line = re.sub(r"[ \t]+", " ", original_line).strip()
        if not line:
            lines.append("")
            continue

        lowered = line.lower()
        if line.startswith("#") or lowered.startswith(("태그", "tags")):
            lines.append(line)
            continue

        normalized = re.sub(r"([.!?。！？])\s+", r"\1\n", line)
        normalized = re.sub(
            r"(습니다|합니다|됩니다|입니다|했어요|해요|돼요|세요|죠|요)\s+",
            r"\1\n",
            normalized,
        )
        chunks = [chunk.strip() for chunk in normalized.split("\n") if chunk.strip()]
        for chunk in chunks or [line]:
            while len(chunk) > max_line_chars:
                split_at = chunk.rfind(" ", 0, max_line_chars + 1)
                if split_at < max_line_chars // 2:
                    split_at = max_line_chars
                lines.append(chunk[:split_at].strip())
                chunk = chunk[split_at:].strip()
            if chunk:
                lines.append(chunk)

    return "\n".join(lines)


def _toggle_bold(driver):
    action_chains, keys, _ = _deps()
    actions = action_chains(driver)
    actions.key_down(keys.CONTROL).send_keys("b").key_up(keys.CONTROL).perform()
    time.sleep(0.03)


def write_text(driver, text):
    if text is None:
        return None

    for is_bold, content in _process_bold_text(str(text)):
        content = improve_line_breaks(content)
        if not content:
            continue
        if is_bold:
            _toggle_bold(driver)
        input_text_mixed(driver, content, use_clipboard_probability=1.0)
        if is_bold:
            _toggle_bold(driver)

    return None


def _insert_heading_html(driver, heading_text):
    html_text = (
        str(heading_text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
    script = """
const text = arguments[0];
const p = document.createElement('p');
const span = document.createElement('span');
span.textContent = text;
span.style.fontSize = '24px';
span.style.fontWeight = '700';
p.appendChild(span);
document.execCommand('insertHTML', false, p.outerHTML + '<p><br></p>');
"""
    driver.execute_script(script, html_text)
    time.sleep(0.05)
    return True


def write_quote(driver, quote_text):
    heading = str(quote_text or "").strip()
    if not heading:
        return None

    try:
        if _insert_heading_html(driver, heading):
            return None
    except Exception:
        pass

    _toggle_bold(driver)
    input_text_mixed(driver, heading, use_clipboard_probability=1.0)
    _toggle_bold(driver)

    action_chains, keys, _ = _deps()
    actions = action_chains(driver)
    actions.send_keys(keys.ENTER).send_keys(keys.ENTER).perform()
    time.sleep(0.05)
    return None


def apply_runtime_patch(naverblog_module):
    """Patch only text-entry functions while keeping the original module logic."""
    global _naverblog
    _naverblog = naverblog_module
    naverblog_module.input_text_mixed = input_text_mixed
    naverblog_module.write_text = write_text
    naverblog_module.write_quote = write_quote
    return naverblog_module
