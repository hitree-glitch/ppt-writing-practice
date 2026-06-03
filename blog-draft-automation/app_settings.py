"""GUI 설정과 사용자 프롬프트를 저장/불러오는 모듈입니다."""

from __future__ import annotations

import json
from typing import Any

from config import DEFAULT_ARTICLE_PROMPT, DEFAULT_IMAGE_PROMPT, IMAGE_MODELS, IMAGE_MODES, SETTINGS_FILE


DEFAULT_SETTINGS: dict[str, Any] = {
    "api_key": "",
    "save_api_key": False,
    "naver_id": "",
    "naver_password": "",
    "remember_login": False,
    "manual_login": True,
    "article_prompt": DEFAULT_ARTICLE_PROMPT,
    "image_prompt": DEFAULT_IMAGE_PROMPT,
    "image_mode": IMAGE_MODES[0],
    "image_model": IMAGE_MODELS[0],
    "publish_type": "임시 저장",
    "subscription_sources": "",
    "monitor_interval_hours": 4.0,
    "pexels_api_key": "",
    "pixabay_api_key": "",
    "naver_blog_id": "",
    "auto_download_images": True,
    "auto_publish_enabled": False,
}


def load_settings() -> dict[str, Any]:
    """저장된 설정을 읽습니다. 파일이 없거나 깨졌으면 기본값을 사용합니다."""
    if not SETTINGS_FILE.exists():
        return DEFAULT_SETTINGS.copy()
    try:
        saved = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return DEFAULT_SETTINGS.copy()
    settings = DEFAULT_SETTINGS.copy()
    settings.update(saved)
    return settings


def save_settings(settings: dict[str, Any]) -> None:
    """체크박스 선택에 따라 민감 정보를 제외하고 설정을 저장합니다."""
    data = DEFAULT_SETTINGS.copy()
    data.update(settings)

    if not data.get("save_api_key"):
        data["api_key"] = ""
        data["pexels_api_key"] = ""
        data["pixabay_api_key"] = ""
    if not data.get("remember_login"):
        data["naver_id"] = ""
        data["naver_password"] = ""

    SETTINGS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
