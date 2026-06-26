"""무료 이미지 사이트에서 블로그 내용 관련 이미지를 검색/다운로드하는 모듈입니다."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote_plus

import requests

from config import BASE_DIR, DEFAULT_HEADERS


@dataclass
class ImageCandidate:
    provider: str
    title: str
    thumbnail_url: str
    image_url: str
    page_url: str
    author: str = ""
    license_name: str = ""

    def attribution(self) -> str:
        bits = [self.provider]
        if self.author:
            bits.append(f"Author: {self.author}")
        if self.license_name:
            bits.append(f"License: {self.license_name}")
        if self.page_url:
            bits.append(self.page_url)
        return " / ".join(bits)


def search_pexels(query: str, api_key: str, limit: int = 8) -> list[ImageCandidate]:
    if not api_key:
        return []
    response = requests.get(
        "https://api.pexels.com/v1/search",
        headers={"Authorization": api_key, **DEFAULT_HEADERS},
        params={"query": query, "per_page": limit, "orientation": "landscape"},
        timeout=20,
    )
    response.raise_for_status()
    data = response.json()
    results = []
    for photo in data.get("photos", []):
        src = photo.get("src", {})
        results.append(
            ImageCandidate(
                provider="Pexels",
                title=photo.get("alt") or query,
                thumbnail_url=src.get("medium") or src.get("small") or "",
                image_url=src.get("large2x") or src.get("large") or src.get("original") or "",
                page_url=photo.get("url") or "",
                author=photo.get("photographer") or "",
                license_name="Pexels License",
            )
        )
    return results


def search_pixabay(query: str, api_key: str, limit: int = 8) -> list[ImageCandidate]:
    if not api_key:
        return []
    response = requests.get(
        "https://pixabay.com/api/",
        headers=DEFAULT_HEADERS,
        params={
            "key": api_key,
            "q": query,
            "image_type": "photo",
            "orientation": "horizontal",
            "safesearch": "true",
            "per_page": limit,
        },
        timeout=20,
    )
    response.raise_for_status()
    data = response.json()
    results = []
    for item in data.get("hits", []):
        results.append(
            ImageCandidate(
                provider="Pixabay",
                title=item.get("tags") or query,
                thumbnail_url=item.get("webformatURL") or "",
                image_url=item.get("largeImageURL") or item.get("webformatURL") or "",
                page_url=item.get("pageURL") or "",
                author=item.get("user") or "",
                license_name="Pixabay Content License",
            )
        )
    return results


def search_wikimedia(query: str, limit: int = 8) -> list[ImageCandidate]:
    response = requests.get(
        "https://commons.wikimedia.org/w/api.php",
        headers=DEFAULT_HEADERS,
        params={
            "action": "query",
            "format": "json",
            "generator": "search",
            "gsrsearch": f"file:{query}",
            "gsrnamespace": 6,
            "gsrlimit": limit,
            "prop": "imageinfo",
            "iiprop": "url|extmetadata",
        },
        timeout=20,
    )
    response.raise_for_status()
    pages = response.json().get("query", {}).get("pages", {})
    results = []
    for page in pages.values():
        info = (page.get("imageinfo") or [{}])[0]
        meta = info.get("extmetadata") or {}
        image_url = info.get("url") or ""
        if not image_url.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
            continue
        author = (meta.get("Artist") or {}).get("value", "")
        license_name = (meta.get("LicenseShortName") or {}).get("value", "")
        page_url = (meta.get("ImageDescriptionUrl") or {}).get("value", "")
        results.append(
            ImageCandidate(
                provider="Wikimedia Commons",
                title=page.get("title", query),
                thumbnail_url=image_url,
                image_url=image_url,
                page_url=page_url,
                author=author,
                license_name=license_name,
            )
        )
    return results


def search_free_images(query: str, pexels_key: str = "", pixabay_key: str = "", limit: int = 8) -> list[ImageCandidate]:
    """Pexels/Pixabay/Wikimedia 순서로 무료 이미지 후보를 검색합니다."""
    candidates: list[ImageCandidate] = []
    errors: list[str] = []
    for fn in (
        lambda: search_pexels(query, pexels_key, limit),
        lambda: search_pixabay(query, pixabay_key, limit),
        lambda: search_wikimedia(query, limit),
    ):
        try:
            candidates.extend(fn())
        except Exception as exc:
            errors.append(str(exc))
    return candidates[:limit]


def download_image(candidate: ImageCandidate, folder: Path | None = None) -> Path:
    target_dir = folder or (BASE_DIR / "downloaded_images")
    target_dir.mkdir(parents=True, exist_ok=True)
    suffix = Path(candidate.image_url.split("?")[0]).suffix.lower()
    if suffix not in (".jpg", ".jpeg", ".png", ".webp"):
        suffix = ".jpg"
    safe_name = "".join(ch if ch.isalnum() else "_" for ch in f"{candidate.provider}_{candidate.title}")[:80]
    path = target_dir / f"{safe_name}{suffix}"
    response = requests.get(candidate.image_url, headers=DEFAULT_HEADERS, timeout=30)
    response.raise_for_status()
    path.write_bytes(response.content)
    return path


def attribution_block(candidates: list[ImageCandidate]) -> str:
    if not candidates:
        return ""
    lines = ["이미지 출처"]
    lines.extend(f"- {candidate.attribution()}" for candidate in candidates)
    return "\n".join(lines)
