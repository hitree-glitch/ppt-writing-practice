"""구독 글 처리 이력과 자동화 작업 로그를 저장하는 SQLite 모듈입니다."""

from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path

from config import BASE_DIR

DB_PATH = BASE_DIR / "automation_state.sqlite3"


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS processed_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_url TEXT NOT NULL,
            post_url TEXT NOT NULL UNIQUE,
            title TEXT,
            published_at TEXT,
            content_hash TEXT,
            status TEXT NOT NULL DEFAULT 'seen',
            draft_path TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS automation_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            level TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    return conn


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()


def is_processed(post_url: str) -> bool:
    with _connect() as conn:
        row = conn.execute("SELECT 1 FROM processed_posts WHERE post_url = ?", (post_url,)).fetchone()
        return row is not None


def mark_post(
    source_url: str,
    post_url: str,
    title: str = "",
    published_at: str = "",
    text: str = "",
    status: str = "seen",
    draft_path: str = "",
) -> None:
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO processed_posts
                (source_url, post_url, title, published_at, content_hash, status, draft_path)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(post_url) DO UPDATE SET
                title = excluded.title,
                published_at = excluded.published_at,
                content_hash = excluded.content_hash,
                status = excluded.status,
                draft_path = excluded.draft_path
            """,
            (source_url, post_url, title, published_at, content_hash(text), status, draft_path),
        )


def add_log(level: str, message: str) -> None:
    with _connect() as conn:
        conn.execute("INSERT INTO automation_logs(level, message) VALUES (?, ?)", (level, message))


def recent_posts(limit: int = 50) -> list[dict]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM processed_posts ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(row) for row in rows]


def export_draft(title: str, content: str, folder: Path | None = None) -> Path:
    target_dir = folder or (BASE_DIR / "automation_drafts")
    target_dir.mkdir(parents=True, exist_ok=True)
    safe_title = "".join(ch if ch.isalnum() or ch in (" ", "_", "-") else "_" for ch in title).strip()[:80]
    if not safe_title:
        safe_title = "draft"
    path = target_dir / f"{safe_title}.txt"
    counter = 2
    while path.exists():
        path = target_dir / f"{safe_title}_{counter}.txt"
        counter += 1
    path.write_text(content, encoding="utf-8")
    return path
