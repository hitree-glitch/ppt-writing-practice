"""참고 자료를 분석해 새 글 작성 방향을 만드는 모듈입니다."""

from __future__ import annotations

import re
from collections import Counter

from crawler import Article


STOPWORDS = {
    "그리고",
    "하지만",
    "또한",
    "있는",
    "없는",
    "합니다",
    "대한",
    "위해",
    "하면",
    "것은",
    "것이다",
    "있다",
    "된다",
    "했다",
    "한다",
    "정도",
    "수준",
    "예상",
    "블로그",
    "네이버",
    "경우",
    "공감",
    "댓글",
    "안부글",
    "출처",
    "기능",
    "본문",
    "true",
    "false",
    "this",
    "that",
    "with",
    "from",
    "have",
    "will",
    "about",
    "their",
}


def clean_title(title: str) -> str:
    """네이버 블로그 접미사와 불필요한 공백을 정리합니다."""
    cleaned = re.sub(r"\s*[:\-]\s*네이버\s*블로그\s*$", "", title.strip())
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned or "제목 없음"


def _tokens(text: str) -> list[str]:
    return re.findall(r"[가-힣A-Za-z0-9]{2,}", text.lower())


def _top_keywords(text: str, count: int = 12) -> list[str]:
    words = [word for word in _tokens(text) if word not in STOPWORDS and len(word) >= 2]
    return [word for word, _ in Counter(words).most_common(count)]


def _guess_topic(articles: list[Article], keywords: list[str], user_keyword: str) -> str:
    if user_keyword:
        return clean_title(user_keyword)

    titles = [clean_title(article.title) for article in articles if article.title and article.title != "제목 없음"]
    if titles and 2 <= len(titles[0]) <= 80:
        return titles[0]
    if keywords:
        return " · ".join(keywords[:3])
    return "참고 자료의 핵심 주제"


def analyze_articles(articles: list[Article], user_keyword: str = "") -> dict:
    """수집 자료를 규칙 기반으로 분석합니다."""
    combined = "\n\n".join(f"{clean_title(a.title)}\n{a.text}" for a in articles)
    keywords = _top_keywords(combined)
    core_topic = _guess_topic(articles, keywords, user_keyword)

    return {
        "core_topic": core_topic,
        "repeated_keywords": keywords,
        "reader_questions": [
            f"{core_topic}에서 가장 먼저 확인해야 할 점은 무엇일까?",
            "실제로 따라 할 때 주의해야 할 점은 무엇일까?",
            "과장 없이 독자에게 도움이 되는 기준은 무엇일까?",
        ],
        "article_flow": [
            "독자의 문제 상황 제시",
            "핵심 개념 정리",
            "실천 방법 또는 판단 기준 설명",
            "주의사항과 예외 상황 안내",
            "검토를 권하는 마무리",
        ],
        "weak_points": [
            "원문 흐름을 그대로 따라가면 새 글의 독자성이 약해질 수 있습니다.",
            "숫자와 사례는 맥락을 설명해야 설득력이 생깁니다.",
        ],
        "improvement_direction": [
            "원문 문장을 복사하지 않고 새 문장으로 재구성합니다.",
            "독자가 바로 이해할 수 있게 소제목을 명확히 나눕니다.",
            "주의사항과 사실 확인 필요성을 함께 넣습니다.",
        ],
        "source_titles": [clean_title(article.title) for article in articles],
    }
