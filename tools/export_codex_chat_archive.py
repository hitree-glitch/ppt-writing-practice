from __future__ import annotations

import json
import os
import re
from datetime import datetime
from pathlib import Path


SECRET_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key\s*[:=]\s*[\"']?)([^\"'\s]+)"),
    re.compile(r"(?i)(password\s*[:=]\s*[\"']?)([^\"'\s]+)"),
    re.compile(r"(?i)(token\s*[:=]\s*[\"']?)([^\"'\s]+)"),
    re.compile(r"(?i)(authorization\s*:\s*bearer\s+)(\S+)"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b"),
    re.compile(r"\bghp_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bAIza[0-9A-Za-z_-]{20,}\b"),
]


def mask_secrets(text: str) -> str:
    masked = text
    for pattern in SECRET_PATTERNS:
        if pattern.groups >= 2:
            masked = pattern.sub(r"\1[REDACTED]", masked)
        else:
            masked = pattern.sub("[REDACTED]", masked)
    return masked


def extract_text_parts(content: list[dict]) -> str:
    parts: list[str] = []
    for item in content:
        if not isinstance(item, dict):
            continue
        if item.get("type") in {"input_text", "output_text", "text"} and item.get("text"):
            parts.append(str(item["text"]))
    return "\n\n".join(parts).strip()


def parse_session(jsonl_path: Path) -> tuple[dict, list[dict]]:
    meta: dict = {"id": jsonl_path.stem, "source_file": jsonl_path.name}
    messages: list[dict] = []

    with jsonl_path.open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            entry_type = entry.get("type")
            payload = entry.get("payload", {})

            if entry_type == "session_meta":
                meta.update(
                    {
                        "id": payload.get("id", meta["id"]),
                        "started_at": payload.get("timestamp"),
                        "cwd": payload.get("cwd"),
                        "originator": payload.get("originator"),
                    }
                )
                continue

            if entry_type == "event_msg" and payload.get("type") == "user_message":
                message = payload.get("message", "").strip()
                if message:
                    messages.append(
                        {
                            "timestamp": entry.get("timestamp"),
                            "role": "user",
                            "text": mask_secrets(message),
                        }
                    )
                continue

            if entry_type == "response_item" and payload.get("type") == "message":
                role = payload.get("role")
                if role not in {"user", "assistant"}:
                    continue
                text = extract_text_parts(payload.get("content", []))
                if text:
                    messages.append(
                        {
                            "timestamp": entry.get("timestamp"),
                            "role": role,
                            "text": mask_secrets(text),
                        }
                    )

    return meta, messages


def render_markdown(meta: dict, messages: list[dict]) -> str:
    lines = [
        f"# Session {meta.get('id', 'unknown')}",
        "",
        f"- Source file: `{meta.get('source_file', '')}`",
        f"- Started at: `{meta.get('started_at', '')}`",
        f"- Originator: `{meta.get('originator', '')}`",
        f"- CWD: `{meta.get('cwd', '')}`",
        "",
    ]

    for message in messages:
        lines.extend(
            [
                f"## {str(message['role']).upper()}",
                "",
                f"`{message.get('timestamp', '')}`",
                "",
                message["text"],
                "",
            ]
        )

    return "\n".join(lines).rstrip() + "\n"


def collect_session_files(codex_home: Path) -> list[Path]:
    active = sorted((codex_home / "sessions").rglob("*.jsonl"))
    archived = sorted((codex_home / "archived_sessions").glob("*.jsonl"))
    return active + archived


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    codex_home = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
    archive_root = repo_root / "codex-chat-archive"
    sessions_root = archive_root / "sessions"
    sessions_root.mkdir(parents=True, exist_ok=True)

    exported = 0
    session_index: list[dict] = []

    for session_file in collect_session_files(codex_home):
        meta, messages = parse_session(session_file)
        if not messages:
            continue

        session_id = meta.get("id") or session_file.stem
        output_path = sessions_root / f"{session_id}.md"
        output_path.write_text(render_markdown(meta, messages), encoding="utf-8")
        exported += 1
        session_index.append(
            {
                "id": session_id,
                "source_file": session_file.name,
                "message_count": len(messages),
                "output_file": str(output_path.relative_to(archive_root)).replace("\\", "/"),
            }
        )

    manifest = {
        "synced_at": datetime.now().astimezone().isoformat(),
        "exported_sessions": exported,
        "codex_home": str(codex_home),
        "notes": "Exports user/assistant messages only and masks common secret patterns.",
    }
    (archive_root / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (archive_root / "index.json").write_text(
        json.dumps(session_index, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
