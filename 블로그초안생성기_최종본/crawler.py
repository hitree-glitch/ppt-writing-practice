"""URL에서 제목과 본문을 수집하는 모듈입니다."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import parse_qs, urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from config import DEFAULT_HEADERS


@dataclass
class Article:
    """수집한 글 하나를 담는 간단한 자료 구조입니다."""

    url: str
    title: str
    text: str


def _clean_text(text: str) -> str:
    """본문 텍스트의 빈 줄과 과한 공백을 정리합니다."""
    lines = [line.strip() for line in text.splitlines()]
    noise_words = (
        "공감",
        "댓글",
        "안부",
        "블로그",
        "카테고리",
        "이웃",
        "메뉴",
        "본문 기타 기능",
        "공유하기",
        "URL 복사",
        "프로필",
    )
    cleaned: list[str] = []
    for line in lines:
        if not line:
            continue
        # 네이버 블로그 UI에서 자주 섞이는 짧은 메뉴 문구를 제거합니다.
        if len(line) <= 12 and any(word in line for word in noise_words):
            continue
        if line.lower() in {"true", "false", "none", "null"}:
            continue
        cleaned.append(line)
    return "\n".join(cleaned)


def _remove_noise(soup: BeautifulSoup) -> None:
    """광고, 댓글, 메뉴처럼 본문이 아닌 요소를 최대한 제거합니다."""
    selectors = [
        "script",
        "style",
        "noscript",
        "iframe",
        "nav",
        "aside",
        "footer",
        "header",
        ".comment",
        ".comments",
        ".reply",
        ".recommend",
        ".related",
        ".ad",
        ".ads",
        ".banner",
        "#comment",
        "#comments",
    ]
    for selector in selectors:
        for tag in soup.select(selector):
            tag.decompose()


def _resolve_naver_iframe_url(url: str, html: str) -> str | None:
    """네이버 블로그의 iframe 본문 주소를 찾아 실제 글 URL로 변환합니다."""
    soup = BeautifulSoup(html, "html.parser")
    frame = soup.select_one("iframe#mainFrame") or soup.select_one("iframe[name=mainFrame]")
    if frame and frame.get("src"):
        return urljoin(url, frame["src"])

    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    blog_id = query.get("blogId", [None])[0]
    log_no = query.get("logNo", [None])[0]
    if blog_id and log_no:
        return f"https://blog.naver.com/PostView.naver?blogId={blog_id}&logNo={log_no}"
    return None


def _extract_from_html(url: str, html: str) -> Article:
    """HTML에서 제목과 본문 후보를 추출합니다."""
    soup = BeautifulSoup(html, "html.parser")
    _remove_noise(soup)

    title = ""
    title_tag = soup.select_one(".se-title-text, .pcol1, h1, title")
    if title_tag:
        title = title_tag.get_text(" ", strip=True)

    # 네이버는 본문 컨테이너만 우선 추출해야 메뉴/댓글/이웃 문구가 덜 섞입니다.
    if "blog.naver.com" in url:
        body_selectors = [
            ".se-main-container",
            "#postViewArea",
            ".post-view",
            ".se_component_wrap",
        ]
    else:
        body_selectors = [
            "article",
            "main",
            ".post-view",
            ".entry-content",
            ".article-body",
            "body",
        ]
    text = ""
    for selector in body_selectors:
        node = soup.select_one(selector)
        if node:
            for bad in node.select(".se-oglink, .se-module-map, .se-module-sticker, .u_likeit_list_module"):
                bad.decompose()
            candidate = _clean_text(node.get_text("\n", strip=True))
            if len(candidate) > len(text):
                text = candidate

    # 일반 웹페이지는 trafilatura가 본문을 더 잘 잡는 경우가 있어 선택적으로 사용합니다.
    if "blog.naver.com" not in url:
        try:
            import trafilatura

            extracted = trafilatura.extract(html, url=url, include_comments=False, include_tables=False)
            if extracted and len(extracted) > len(text):
                text = _clean_text(extracted)
        except Exception:
            pass

    return Article(url=url, title=title or "제목 없음", text=text)


def fetch_article(url: str, timeout: int = 15) -> Article:
    """URL 하나에서 글을 수집합니다. 실패하면 예외를 호출한 쪽으로 전달합니다."""
    response = requests.get(url, headers=DEFAULT_HEADERS, timeout=timeout)
    response.raise_for_status()
    response.encoding = response.apparent_encoding or response.encoding

    iframe_url = None
    if "blog.naver.com" in url:
        iframe_url = _resolve_naver_iframe_url(url, response.text)

    if iframe_url and iframe_url != url:
        response = requests.get(iframe_url, headers=DEFAULT_HEADERS, timeout=timeout)
        response.raise_for_status()
        response.encoding = response.apparent_encoding or response.encoding
        url = iframe_url

    article = _extract_from_html(url, response.text)
    if len(article.text) < 100:
        raise ValueError("본문을 충분히 추출하지 못했습니다.")
    return article


def fetch_articles(urls: list[str], log=None) -> list[Article]:
    """여러 URL을 순서대로 수집합니다. 일부 실패해도 나머지는 계속 진행합니다."""
    articles: list[Article] = []
    for index, url in enumerate(urls, start=1):
        try:
            if log:
                log(f"[수집] {index}/{len(urls)} URL 처리 중: {url}")
            articles.append(fetch_article(url))
        except Exception as exc:  # GUI가 종료되지 않도록 오류를 로그로만 남깁니다.
            if log:
                log(f"[경고] 수집 실패: {url} - {exc}")
    return articles
