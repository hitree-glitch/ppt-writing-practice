"""프로그램 전역 설정값을 모아두는 파일입니다."""

from pathlib import Path

APP_NAME = "참고 자료 기반 블로그 자동화 초안 생성기"
BASE_DIR = Path(__file__).resolve().parent
SETTINGS_FILE = BASE_DIR / "app_settings.json"

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0 Safari/537.36"
    )
}

DEFAULT_SEARCH_LIMIT = 5
GEMINI_MODEL = "gemini-1.5-flash"
GEMINI_API_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_MODEL}:generateContent"
)

PLAGIARISM_WORD_WINDOW = 12

DEFAULT_ARTICLE_PROMPT = """당신은 네이버 블로그 초안을 쓰는 한국어 콘텐츠 에디터입니다.
참고 자료의 문장을 복사하지 말고, 핵심 사실과 관점만 바탕으로 새 글을 작성하세요.
제목 후보 5개, 선택 제목, 소제목이 있는 본문, 참고자료 URL 목록을 포함하세요.
원문과 지나치게 유사한 표현은 피하고, 사람이 직접 쓴 듯 자연스럽게 재구성하세요."""

DEFAULT_IMAGE_PROMPT = """For each major section of the Korean blog draft, create one high-quality English image prompt.
Use editorial, realistic, clean blog-thumbnail style. Avoid logos, copyrighted characters, and text inside the image.
Return concise numbered prompts only."""

IMAGE_MODES = [
    "텍스트만 업로드(영문 프롬프트 생성)",
    "무료 이미지 사이트 검색",
    "이미지 자동 다운로드 후 첨부 후보",
]

IMAGE_MODELS = [
    "무료 이미지 검색(Pexels/Pixabay/Wikimedia)",
    "Gemini 1.5 Flash (프롬프트만)",
]
