"""Playwright 기반 네이버 블로그 글쓰기 자동화 모듈입니다.

네이버 화면 구조와 보안 정책은 자주 바뀔 수 있습니다. 이 모듈은 best-effort 방식이며,
캡차/2단계 인증/에디터 변경이 있으면 수동 개입이 필요합니다.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path

from config import BASE_DIR


@dataclass
class PublishRequest:
    blog_id: str
    title: str
    body: str
    image_paths: list[str]
    mode: str = "draft"  # draft, scheduled, publish
    schedule_time: str = ""
    naver_id: str = ""
    naver_password: str = ""
    manual_login: bool = True


class NaverPublishError(RuntimeError):
    pass


def _split_title_body(content: str) -> tuple[str, str]:
    lines = [line.rstrip() for line in content.splitlines()]
    title = ""
    body_start = 0
    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("2. 선택 제목"):
            for j in range(index + 1, min(index + 5, len(lines))):
                if lines[j].strip():
                    title = lines[j].strip()
                    break
        if stripped.startswith("3. 본문"):
            body_start = index + 1
            break
    if not title:
        for line in lines:
            if line.strip() and not line.strip().startswith(("1.", "-", "#")):
                title = line.strip()[:80]
                break
    body = "\n".join(lines[body_start:]).strip() if body_start else content.strip()
    return title or "블로그 초안", body


async def publish_to_naver_async(request: PublishRequest, log=None) -> None:
    try:
        from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
        import pyperclip
    except ImportError as exc:
        raise NaverPublishError("네이버 자동화를 사용하려면 playwright와 pyperclip 설치가 필요합니다.") from exc

    profile_dir = BASE_DIR / "naver_browser_profile"
    profile_dir.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(
            str(profile_dir),
            headless=False,
            viewport={"width": 1280, "height": 900},
        )
        page = browser.pages[0] if browser.pages else await browser.new_page()
        try:
            if log:
                log("[네이버] 로그인 페이지를 엽니다.")
            await page.goto("https://nid.naver.com/nidlogin.login", wait_until="domcontentloaded")

            if request.manual_login or not (request.naver_id and request.naver_password):
                if log:
                    log("[네이버] 수동 로그인 모드입니다. 브라우저에서 로그인 후 창을 그대로 두세요.")
                await page.wait_for_url(lambda url: "nid.naver.com" not in url, timeout=180000)
            else:
                await page.fill("#id", request.naver_id)
                await page.fill("#pw", request.naver_password)
                await page.click("#log\\.login")
                try:
                    await page.wait_for_url(lambda url: "nid.naver.com" not in url, timeout=120000)
                except PlaywrightTimeoutError:
                    if log:
                        log("[네이버] 자동 로그인 실패 또는 추가 인증이 필요합니다. 수동으로 완료해 주세요.")
                    await page.wait_for_url(lambda url: "nid.naver.com" not in url, timeout=180000)

            write_urls = [
                f"https://blog.naver.com/PostWriteForm.naver?blogId={request.blog_id}",
                f"https://blog.naver.com/{request.blog_id}?Redirect=Write",
            ]
            for url in write_urls:
                if log:
                    log(f"[네이버] 글쓰기 화면 이동 시도: {url}")
                await page.goto(url, wait_until="domcontentloaded")
                await page.wait_for_timeout(3000)
                if "PostWriteForm" in page.url or "blog.naver.com" in page.url:
                    break

            # 제목 입력 후보
            title_done = False
            for selector in [
                "textarea[placeholder*='제목']",
                "input[placeholder*='제목']",
                "[contenteditable='true'][data-placeholder*='제목']",
                ".se-title-text",
            ]:
                try:
                    await page.locator(selector).first.click(timeout=3000)
                    pyperclip.copy(request.title)
                    await page.keyboard.press("Control+V")
                    title_done = True
                    break
                except Exception:
                    continue
            if not title_done and log:
                log("[네이버] 제목 입력칸을 자동으로 찾지 못했습니다.")

            body_done = False
            for selector in [
                ".se-component-content [contenteditable='true']",
                ".se-section-text [contenteditable='true']",
                "[contenteditable='true']",
                "textarea",
            ]:
                try:
                    await page.locator(selector).last.click(timeout=5000)
                    pyperclip.copy(request.body)
                    await page.keyboard.press("Control+V")
                    body_done = True
                    break
                except Exception:
                    continue
            if not body_done:
                raise NaverPublishError("본문 입력 영역을 찾지 못했습니다. 네이버 에디터 구조가 바뀌었을 수 있습니다.")

            for image_path in request.image_paths:
                path = Path(image_path)
                if not path.exists():
                    continue
                try:
                    file_inputs = page.locator("input[type=file]")
                    if await file_inputs.count() > 0:
                        await file_inputs.first.set_input_files(str(path))
                        await page.wait_for_timeout(1500)
                except Exception as exc:
                    if log:
                        log(f"[네이버] 이미지 업로드 실패: {path} - {exc}")

            if request.mode == "draft":
                labels = ["임시저장", "저장"]
            elif request.mode == "scheduled":
                labels = ["발행", "예약", "예약 발행", "확인"]
            else:
                labels = ["발행", "확인"]

            for label in labels:
                try:
                    await page.get_by_text(label, exact=False).last.click(timeout=4000)
                    await page.wait_for_timeout(1500)
                except Exception:
                    continue

            if log:
                log("[네이버] 자동 입력 단계가 끝났습니다. 화면을 확인해 주세요.")
        finally:
            # 자동화 결과를 사용자가 확인할 수 있게 브라우저는 잠시 유지합니다.
            await page.wait_for_timeout(5000)
            await browser.close()


def publish_to_naver(request: PublishRequest, log=None) -> None:
    asyncio.run(publish_to_naver_async(request, log=log))
