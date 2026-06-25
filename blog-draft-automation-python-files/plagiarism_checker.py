"""생성 글과 참고 원문 사이의 유사 표현을 점검하는 모듈입니다."""

from __future__ import annotations

import re
from difflib import SequenceMatcher

from config import PLAGIARISM_WORD_WINDOW
from crawler import Article


def _words(text: str) -> list[str]:
    return re.findall(r"[가-힣A-Za-z0-9]+", text.lower())


def _sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?。！？])\s+|\n+", text)
    ignored_prefixes = ("-", "#", "1.", "2.", "3.", "4.", "5.")
    sentences: list[str] = []
    for part in parts:
        cleaned = part.strip()
        if len(cleaned) < 30:
            continue
        # 제목 후보, 참고자료 목록, URL은 표절 판단 대상에서 제외합니다.
        if cleaned.startswith(ignored_prefixes) or cleaned.startswith("http"):
            continue
        sentences.append(cleaned)
    return sentences


def find_long_matches(source_text: str, generated_text: str, window: int = PLAGIARISM_WORD_WINDOW) -> list[str]:
    """12단어 이상 연속으로 같은 구간이 있는지 확인합니다."""
    source_words = _words(source_text)
    generated_words = _words(generated_text)
    source_windows = {" ".join(source_words[i : i + window]) for i in range(max(0, len(source_words) - window + 1))}

    matches: list[str] = []
    for i in range(max(0, len(generated_words) - window + 1)):
        chunk = " ".join(generated_words[i : i + window])
        if chunk in source_windows and chunk not in matches:
            matches.append(chunk)
    return matches[:10]


def find_similar_sentences(source_text: str, generated_text: str, threshold: float = 0.88) -> list[str]:
    """문장 단위로 지나치게 비슷한 표현을 찾습니다."""
    source_sentences = _sentences(source_text)
    generated_sentences = _sentences(generated_text)
    risky: list[str] = []

    for generated in generated_sentences:
        for source in source_sentences:
            ratio = SequenceMatcher(None, source[:500], generated[:500]).ratio()
            if ratio >= threshold:
                risky.append(generated)
                break
        if len(risky) >= 10:
            break
    return risky


def check_plagiarism(articles: list[Article], generated_text: str) -> dict:
    """최종 초안에 대한 표절 위험 점검 결과를 반환합니다."""
    source_text = "\n".join(article.text for article in articles)
    long_matches = find_long_matches(source_text, generated_text)
    similar_sentences = find_similar_sentences(source_text, generated_text)
    passed = not long_matches and not similar_sentences

    return {
        "passed": passed,
        "long_matches": long_matches,
        "similar_sentences": similar_sentences,
        "message": "위험 표현이 발견되지 않았습니다." if passed else "유사 표현이 발견되어 재작성 검토가 필요합니다.",
    }
