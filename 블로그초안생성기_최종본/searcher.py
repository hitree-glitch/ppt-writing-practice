"""해외 자료 검색과 검색 결과 본문 수집을 담당하는 모듈입니다."""

from __future__ import annotations

from urllib.parse import parse_qs, quote_plus, urlparse

import requests
from bs4 import BeautifulSoup

from config import DEFAULT_HEADERS, DEFAULT_SEARCH_LIMIT
from crawler import Article, fetch_article


def search_duckduckgo(query: str, limit: int = DEFAULT_SEARCH_LIMIT) -> list[str]:
    """API 키 없이 DuckDuckGo HTML 검색을 사용해 영어권 자료 URL을 찾습니다."""
    search_query = f"{query} english article blog research"
    url = f"https://duckduckgo.com/html/?q={quote_plus(search_query)}&kl=us-en"
    response = requests.get(url, headers=DEFAULT_HEADERS, timeout=15)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    urls: list[str] = []
    for link in soup.select("a.result__a"):
        href = link.get("href")
        if not href:
            continue
        # DuckDuckGo HTML 결과는 /l/?uddg=... 형태의 리다이렉트 링크를 줄 때가 있습니다.
        if href.startswith("/l/"):
            parsed = urlparse(href)
            href = parse_qs(parsed.query).get("uddg", [""])[0]
        if href.startswith("http") and href not in urls:
            urls.append(href)
        if len(urls) >= limit:
            break
    return urls


def collect_overseas_sources(keyword: str, limit: int = DEFAULT_SEARCH_LIMIT, log=None) -> list[Article]:
    """검색 결과 중 본문 추출에 성공한 자료 3~5개를 모읍니다."""
    if log:
        log("[검색] DuckDuckGo에서 해외 자료를 찾는 중입니다.")
    urls = search_duckduckgo(keyword, limit=limit)

    articles: list[Article] = []
    for url in urls:
        try:
            if log:
                log(f"[검색] 자료 본문 추출 중: {url}")
            article = fetch_article(url)
            articles.append(article)
        except Exception as exc:
            if log:
                log(f"[경고] 해외 자료 추출 실패: {url} - {exc}")
        if len(articles) >= 5:
            break

    if not articles and log:
        log("[안내] 검색/추출에 실패했습니다. 참고 URL 방식으로 직접 URL을 입력해 주세요.")
    return articles
