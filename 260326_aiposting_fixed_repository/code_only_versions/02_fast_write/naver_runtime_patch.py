"""Runtime-only search-result patch for the extracted naver module."""

from __future__ import annotations

import html
import re
from urllib.parse import parse_qs, urlencode, urlparse
import urllib.request


_naver = None


def _normalize_blog_url(raw_url):
    if not raw_url:
        return None

    raw = html.unescape(str(raw_url)).strip().strip("\"'<>")
    raw = raw.replace("\\/", "/")
    parsed = urlparse(raw)
    host = parsed.netloc.lower()

    if host in {"blog.naver.com", "m.blog.naver.com"}:
        path_parts = [part for part in parsed.path.split("/") if part]
        if len(path_parts) >= 2 and path_parts[1].isdigit():
            return f"https://blog.naver.com/{path_parts[0]}/{path_parts[1]}"
        if path_parts and path_parts[0].lower() == "postview.naver":
            query = parse_qs(parsed.query)
            blog_id = (query.get("blogId") or query.get("blogid") or [""])[0]
            log_no = (query.get("logNo") or query.get("logno") or [""])[0]
            if blog_id and log_no:
                return f"https://blog.naver.com/{blog_id}/{log_no}"

    return None


def _iter_blog_urls_from_html(text):
    pattern = re.compile(
        r"https?:\\?/\\?/(?:m\.)?blog\.naver\.com\\?/[^\s\"'<>]+",
        re.IGNORECASE,
    )
    for match in pattern.finditer(text or ""):
        normalized = _normalize_blog_url(match.group(0))
        if normalized:
            yield normalized


def get_top_post(keyword, post_count=3):
    """Collect top Naver blog post URLs with selectors plus a regex fallback."""
    if _naver is None:
        raise RuntimeError("naver runtime patch has not been applied")

    beautiful_soup = _naver.BeautifulSoup

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
        request = urllib.request.Request(
            "https://search.naver.com/search.naver?" + urlencode(params),
            headers=headers,
        )
        with urllib.request.urlopen(request, timeout=15) as response:
            data = response.read()
            encoding = response.headers.get_content_charset() or "utf-8"
            response_text = data.decode(encoding, "replace")
    except Exception:
        return []

    urls = []
    seen = set()

    def add(url):
        if url and url not in seen:
            seen.add(url)
            urls.append(url)

    soup = beautiful_soup(response_text, "html.parser")
    selectors = [
        "a.title_link",
        "a.api_txt_lines",
        "a.total_tit",
        "a.name",
        "a[href*='blog.naver.com']",
    ]
    for selector in selectors:
        for anchor in soup.select(selector):
            add(_normalize_blog_url(anchor.get("href")))
            if len(urls) >= int(post_count):
                return urls[: int(post_count)]

    for url in _iter_blog_urls_from_html(response_text):
        add(url)
        if len(urls) >= int(post_count):
            break

    return urls[: int(post_count)]


def apply_runtime_patch(naver_module):
    global _naver
    _naver = naver_module
    naver_module.get_top_post = get_top_post
    return naver_module
