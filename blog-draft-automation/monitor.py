"""구독 블로그의 새 글을 RSS/URL 기반으로 감시하는 모듈입니다."""

from __future__ import annotations

import re
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from threading import Event
from urllib.parse import urlparse

import requests

from config import DEFAULT_HEADERS
from crawler import Article, fetch_article
from post_db import is_processed


@dataclass
class FeedItem:
    source_url: str
    post_url: str
    title: str
    published_at: str = ""


def normalize_blog_source(raw: str) -> str:
    """블로그 ID 또는 URL을 RSS URL로 바꾸기 위한 원본 URL로 정리합니다."""
    value = raw.strip()
    if not value:
        return ""
    if value.startswith("http://") or value.startswith("https://"):
        return value
    return f"https://blog.naver.com/{value}"


def extract_blog_id(source: str) -> str:
    source = normalize_blog_source(source)
    parsed = urlparse(source)
    parts = [part for part in parsed.path.split("/") if part]
    if "blog.naver.com" in parsed.netloc and parts:
        return parts[0]
    return source.strip().strip("/")


def rss_url_for_source(source: str) -> str:
    blog_id = extract_blog_id(source)
    return f"https://rss.blog.naver.com/{blog_id}.xml"


def fetch_rss_items(source: str, limit: int = 10) -> list[FeedItem]:
    """네이버 블로그 RSS에서 최근 글 목록을 가져옵니다."""
    source_url = normalize_blog_source(source)
    rss_url = rss_url_for_source(source_url)
    response = requests.get(rss_url, headers=DEFAULT_HEADERS, timeout=15)
    response.raise_for_status()
    response.encoding = response.apparent_encoding or response.encoding

    root = ET.fromstring(response.text)
    items: list[FeedItem] = []
    for item in root.findall(".//item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        pub_date = (item.findtext("pubDate") or item.findtext("date") or "").strip()
        if link:
            items.append(FeedItem(source_url=source_url, post_url=link, title=title, published_at=pub_date))
        if len(items) >= limit:
            break
    return items


def fetch_new_articles(sources: list[str], per_source_limit: int = 5, log=None) -> list[tuple[FeedItem, Article]]:
    """구독 목록에서 아직 처리하지 않은 새 글 본문을 수집합니다."""
    results: list[tuple[FeedItem, Article]] = []
    for source in sources:
        clean_source = normalize_blog_source(source)
        if not clean_source:
            continue
        try:
            if log:
                log(f"[구독] RSS 확인 중: {clean_source}")
            items = fetch_rss_items(clean_source, limit=per_source_limit)
        except Exception as exc:
            if log:
                log(f"[경고] RSS 확인 실패: {clean_source} - {exc}")
            continue

        for item in items:
            if is_processed(item.post_url):
                continue
            try:
                if log:
                    log(f"[구독] 새 글 본문 수집: {item.title or item.post_url}")
                article = fetch_article(item.post_url)
                results.append((item, article))
            except Exception as exc:
                if log:
                    log(f"[경고] 새 글 본문 수집 실패: {item.post_url} - {exc}")
    return results


def run_monitor_loop(
    sources: list[str],
    interval_hours: float,
    callback,
    stop_event: Event,
    log=None,
) -> None:
    """앱이 켜져 있는 동안 주기적으로 새 글을 확인합니다."""
    interval_seconds = max(10, int(interval_hours * 3600))
    while not stop_event.is_set():
        try:
            new_items = fetch_new_articles(sources, log=log)
            callback(new_items)
        except Exception as exc:
            if log:
                log(f"[오류] 자동 감시 루프 오류: {exc}")
        if log:
            log(f"[대기] 다음 구독 확인까지 약 {interval_seconds // 60}분 대기합니다.")
        stop_event.wait(interval_seconds)


def extract_keywords_for_image(text: str, count: int = 4) -> list[str]:
    """이미지 검색용 키워드를 간단히 추출합니다."""
    preferred = []
    for keyword in ("semiconductor", "AI data center", "memory chip", "server", "finance", "business", "technology"):
        if keyword.lower() in text.lower():
            preferred.append(keyword)
    korean_map = {
        "반도체": "semiconductor",
        "오픈AI": "AI data center",
        "OpenAI": "AI data center",
        "HBM": "memory chip",
        "메모리": "memory chip",
        "투자": "business finance",
        "식당": "restaurant kitchen",
    }
    for src, dst in korean_map.items():
        if src in text and dst not in preferred:
            preferred.append(dst)
    if preferred:
        return preferred[:count]
    words = re.findall(r"[A-Za-z가-힣]{3,}", text)
    return words[:count]
