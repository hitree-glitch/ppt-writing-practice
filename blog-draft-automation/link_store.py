"""저장된 참고 링크와 구독 블로그 목록을 관리하는 모듈입니다."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, asdict
from datetime import datetime
from urllib.parse import urlparse

from config import BASE_DIR

LINK_STORE_FILE = BASE_DIR / "saved_links.json"


@dataclass
class SavedLink:
    id: str
    url: str
    name: str = ""
    kind: str = "reference"  # reference, blog
    memo: str = ""
    created_at: str = ""
    updated_at: str = ""


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def normalize_url(raw: str) -> str:
    """사용자가 입력한 URL/블로그 ID를 저장 가능한 URL로 정리합니다."""
    value = (raw or "").strip()
    if not value:
        return ""
    if value.startswith("http://") or value.startswith("https://"):
        return value
    if re.match(r"^[A-Za-z0-9_\-.]+$", value):
        return f"https://blog.naver.com/{value}"
    return value


def guess_name(url: str) -> str:
    """목록에 보여줄 짧은 이름을 자동으로 만듭니다."""
    parsed = urlparse(url)
    if "blog.naver.com" in parsed.netloc:
        parts = [part for part in parsed.path.split("/") if part]
        if parts:
            return parts[0]
    return parsed.netloc or url[:40]


def _read_raw() -> list[dict]:
    if not LINK_STORE_FILE.exists():
        return []
    try:
        data = json.loads(LINK_STORE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    return []


def load_links(kind: str | None = None) -> list[SavedLink]:
    links: list[SavedLink] = []
    for item in _read_raw():
        url = normalize_url(str(item.get("url", "")))
        if not url:
            continue
        saved = SavedLink(
            id=str(item.get("id") or _make_id(url)),
            url=url,
            name=str(item.get("name") or guess_name(url)),
            kind=str(item.get("kind") or "reference"),
            memo=str(item.get("memo") or ""),
            created_at=str(item.get("created_at") or ""),
            updated_at=str(item.get("updated_at") or ""),
        )
        if kind is None or saved.kind == kind:
            links.append(saved)
    return links


def save_links(links: list[SavedLink]) -> None:
    LINK_STORE_FILE.write_text(
        json.dumps([asdict(link) for link in links], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _make_id(url: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9]+", "-", url.lower()).strip("-")[:48]
    return safe or str(abs(hash(url)))


def upsert_link(url: str, name: str = "", kind: str = "reference", memo: str = "") -> SavedLink:
    clean_url = normalize_url(url)
    if not clean_url:
        raise ValueError("저장할 링크를 입력해 주세요.")

    links = load_links()
    now = _now()
    for link in links:
        if link.url == clean_url:
            link.name = name.strip() or link.name or guess_name(clean_url)
            link.kind = kind or link.kind
            link.memo = memo.strip() or link.memo
            link.updated_at = now
            save_links(links)
            return link

    link = SavedLink(
        id=_make_id(clean_url),
        url=clean_url,
        name=name.strip() or guess_name(clean_url),
        kind=kind or "reference",
        memo=memo.strip(),
        created_at=now,
        updated_at=now,
    )
    links.append(link)
    save_links(links)
    return link


def delete_link(link_id: str) -> None:
    links = [link for link in load_links() if link.id != link_id]
    save_links(links)


def links_to_text(links: list[SavedLink]) -> str:
    return "\n".join(link.url for link in links)
