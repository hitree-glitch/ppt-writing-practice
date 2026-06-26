"""구독 글 수집부터 초안 생성, 이미지 검색, 선택적 네이버 저장까지 묶는 엔진입니다."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from crawler import Article
from image_searcher import ImageCandidate, attribution_block, download_image, search_free_images
from monitor import FeedItem, extract_keywords_for_image, fetch_new_articles
from naver_publisher import PublishRequest, publish_to_naver
from post_db import export_draft, mark_post
from writer import generate_blog_draft


@dataclass
class AutomationResult:
    item: FeedItem
    draft: str
    draft_path: Path
    images: list[ImageCandidate]
    downloaded_paths: list[Path]
    status: str


def build_image_query(article: Article, draft: str) -> str:
    keywords = extract_keywords_for_image(f"{article.title}\n{article.text}\n{draft}", count=3)
    return " ".join(keywords) if keywords else article.title


def process_new_posts_once(
    sources: list[str],
    api_key: str,
    style: str,
    target_length: str,
    article_prompt: str,
    publish_type: str,
    pexels_key: str = "",
    pixabay_key: str = "",
    auto_download_images: bool = True,
    auto_publish: bool = False,
    naver_blog_id: str = "",
    naver_id: str = "",
    naver_password: str = "",
    manual_login: bool = True,
    log=None,
) -> list[AutomationResult]:
    """새 글을 한 번 확인하고 자동화 파이프라인을 실행합니다."""
    collected = fetch_new_articles(sources, log=log)
    results: list[AutomationResult] = []
    for item, article in collected:
        try:
            if log:
                log(f"[자동화] 초안 생성: {article.title}")
            draft, _ = generate_blog_draft(
                articles=[article],
                api_key=api_key,
                style=style,
                target_length=target_length,
                keyword=article.title,
                mode_name="구독 블로그 새 글 기반 자동 작성",
                article_prompt=article_prompt,
                publish_type=publish_type,
                log=log,
            )

            image_query = build_image_query(article, draft)
            if log:
                log(f"[이미지] 무료 이미지 검색어: {image_query}")
            images = search_free_images(image_query, pexels_key=pexels_key, pixabay_key=pixabay_key, limit=6)
            downloaded_paths: list[Path] = []
            if auto_download_images:
                for candidate in images[:2]:
                    try:
                        downloaded_paths.append(download_image(candidate))
                    except Exception as exc:
                        if log:
                            log(f"[경고] 이미지 다운로드 실패: {candidate.image_url} - {exc}")

            if images:
                draft += "\n\n---\n" + attribution_block(images[:2]) + "\n"

            draft_path = export_draft(article.title or item.title or "automation_draft", draft)
            status = "draft_saved"

            if auto_publish and naver_blog_id:
                if log:
                    log("[네이버] 자동 예약/임시 저장을 시도합니다.")
                title, body = article.title or item.title, draft
                request = PublishRequest(
                    blog_id=naver_blog_id,
                    title=title[:90] or "자동 생성 초안",
                    body=body,
                    image_paths=[str(path) for path in downloaded_paths],
                    mode="scheduled" if publish_type == "예약 발행" else "draft",
                    naver_id=naver_id,
                    naver_password=naver_password,
                    manual_login=manual_login,
                )
                publish_to_naver(request, log=log)
                status = "naver_attempted"

            mark_post(
                source_url=item.source_url,
                post_url=item.post_url,
                title=article.title or item.title,
                published_at=item.published_at,
                text=article.text,
                status=status,
                draft_path=str(draft_path),
            )
            results.append(
                AutomationResult(
                    item=item,
                    draft=draft,
                    draft_path=draft_path,
                    images=images,
                    downloaded_paths=downloaded_paths,
                    status=status,
                )
            )
        except Exception as exc:
            mark_post(
                source_url=item.source_url,
                post_url=item.post_url,
                title=article.title or item.title,
                published_at=item.published_at,
                text=article.text,
                status=f"error: {exc}",
            )
            if log:
                log(f"[오류] 자동화 처리 실패: {item.post_url} - {exc}")
    return results
