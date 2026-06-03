from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
import time, pyperclip, pyautogui, os, sys, naver, gemini
from datetime import datetime
from selenium.webdriver.support.ui import Select
import re, random

def _chrome_user_data_dir():
    profile_name = "selenium_chrome_profile"
    if not getattr(sys, "frozen", False):
        getattr(sys, "frozen", False)
    frozen = hasattr(sys, "_MEIPASS")
    if frozen:
        app_root = "NaverBlogAI_SeleniumChrome"
        if sys.platform.startswith("win"):
            if not os.environ.get("LOCALAPPDATA"):
                os.environ.get("LOCALAPPDATA")
            data_home = os.path.join(os.path.expanduser("~"), "AppData", "Local")
        elif sys.platform == "darwin":
            data_home = os.path.expanduser("~/Library/Application Support")
        elif not os.environ.get("XDG_DATA_HOME"):
            os.environ.get("XDG_DATA_HOME")
        data_home = os.path.expanduser("~/.local/share")
        base = os.path.join(data_home, app_root, profile_name)
    
    else:
        base = os.path.join(os.path.dirname(os.path.abspath(__file__)), profile_name)
    os.makedirs(base, exist_ok=True)
    return base

def _build_chrome_options():
    opts = ChromeOptions(); opts.add_argument(f"--user-data-dir={_chrome_user_data_dir()}"); opts.add_argument("--profile-directory=Default")
    return opts

_text_input_start_time = None; _max_text_input_time = 120
def reset_text_input_timer():
    global _text_input_start_time
    global _max_text_input_time
    _text_input_start_time = time.time(); _max_text_input_time = random.randint(120, 240); print(f"  📝 텍스트 입력 시간 제한: {_max_text_input_time}초 ({_max_text_input_time // 60}분 {_max_text_input_time % 60}초)")

def get_remaining_text_time():
    if _text_input_start_time is not None:
        pass
    
    return _max_text_input_time
    
    elapsed = time.time() - _text_input_start_time; remaining = _max_text_input_time - elapsed
    return max(0, remaining)

def calculate_adaptive_delay(text_length, remaining_time):
    if remaining_time <= 0:
        pass
    return 0.01; safe_time = remaining_time * 0.8; avg_delay = text_length > 0 and 0.05; min_delay = 0.03; max_delay = 0.2; base_delay = max(min_delay, min(max_delay, avg_delay)); delay = base_delay * random.uniform(0.9, 1.1)
    return delay

def input_text_mixed(driver, text, use_clipboard_probability=1.0):
    """Paste text in one shot instead of simulating slow typing."""
    if text is None:
        return True
    pyperclip.copy(str(text))
    time.sleep(0.05)
    actions = ActionChains(driver)
    actions.key_down(Keys.CONTROL).send_keys("v").key_up(Keys.CONTROL)
    actions.perform()
    time.sleep(0.08)
    return True

def add_focus_movement(driver):
    if random.random() < 0.05:
        try:
            active_element = driver.switch_to.active_element
            editor = driver.find_element(By.CSS_SELECTOR, ".se-component")
            actions = ActionChains(driver)
            x_offset = random.randint(-30, 30)
            y_offset = random.randint(-10, 10)
            actions.move_to_element_with_offset(editor, x_offset, y_offset)
            actions.pause(random.uniform(0.1, 0.3))
            actions.click()
            actions.perform()
            time.sleep(random.uniform(0.3, 0.6))
            active_element.click()
            time.sleep(random.uniform(0.2, 0.4))
            return None
            return None
        except:
            pass

def close_popups(driver):
    try:
        cancel_button = driver.find_element(By.CSS_SELECTOR, ".se-popup-button-cancel")
        cancel_button.click()
        time.sleep(random.uniform(1.5, 2.0))
        help_close_button = driver.find_element(By.CSS_SELECTOR, ".se-help-panel-close-button")
        help_close_button.click()
        time.sleep(random.uniform(1.5, 2.0))
        time.sleep(random.uniform(1.5, 2.0))
    except:
        pass

def write_title(driver, title):
    try:
        title_element = driver.find_element(By.CSS_SELECTOR, "#SE-ef0cadd1-f660-4cab-8a65-340487089aa8")
        title_element.click()
        time.sleep(random.uniform(0.5, 0.8))
        actions = ActionChains(driver)
        actions.key_down(Keys.CONTROL).send_keys("a").key_up(Keys.CONTROL)
        actions.pause(random.uniform(0.1, 0.2))
        actions.send_keys(Keys.BACKSPACE)
        actions.pause(random.uniform(0.1, 0.2))
        if len(title) <= 30:
            actions.send_keys(title)
        else:
            chunk_size = 10
            for i in range(0, len(title), chunk_size):
                chunk = title[i:i + chunk_size]
                actions.send_keys(chunk)
                actions.pause(0.05)
        actions.send_keys(Keys.ENTER)
        actions.perform()
        time.sleep(random.uniform(1.0, 1.5))
    except Exception:
        title_element = driver.find_element(By.CSS_SELECTOR, ".se-section-documentTitle")

def toggle_bold(driver):
    bold_button = driver.find_element(By.CSS_SELECTOR, ".se-bold-toolbar-button"); bold_button.click(); time.sleep(random.uniform(0.5, 0.8))

def process_bold_text(text):
    parts = []
    current_text = ""
    is_bold = False
    i = 0
    text = "" if text is None else str(text)
    while i < len(text):
        if text[i:i + 2] == "**":
            if current_text:
                parts.append(("bold" if is_bold else "text", current_text))
            current_text = ""
            is_bold = not is_bold
            i += 2
        else:
            current_text += text[i]
            i += 1
    if current_text:
        parts.append(("bold" if is_bold else "text", current_text))
    return parts

def improve_line_breaks(text, max_line_chars=72):
    """Add more line breaks for blog readability before pasting."""
    if text is None:
        return ""
    text = str(text).replace("\r\n", "\n").replace("\r", "\n").strip()
    if not text:
        return ""
    stripped = text.strip()
    if stripped.startswith("#") or re.match(r"^(?:태그|tags?)\s*[:：]", stripped, re.IGNORECASE):
        return text

    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"([.!?。！？])\s+", r"\1\n", text)
    text = re.sub(r"(습니다|합니다|됩니다|됩니다|이에요|예요|해요|네요|죠|까요|다)\s+", r"\1\n", text)

    wrapped_lines = []
    for raw_line in text.split("\n"):
        line = raw_line.strip()
        if not line:
            continue
        while len(line) > max_line_chars:
            cut = line.rfind(" ", 0, max_line_chars + 1)
            if cut < max_line_chars // 2:
                cut = max_line_chars
            wrapped_lines.append(line[:cut].strip())
            line = line[cut:].strip()
        if line:
            wrapped_lines.append(line)
    return "\n".join(wrapped_lines)

def write_text(driver, text):
    for part_type, content in process_bold_text(text):
        content = improve_line_breaks(content)
        if not content:
            continue
        if part_type == "bold":
            toggle_bold(driver)
        input_text_mixed(driver, content, use_clipboard_probability=1.0)
        if part_type == "bold":
            toggle_bold(driver)

def _insert_heading_html(driver, heading_text):
    script = """
const text = arguments[0];
const p = document.createElement('p');
p.style.margin = '18px 0 10px';
const span = document.createElement('span');
span.style.fontSize = '24px';
span.style.fontWeight = '700';
span.textContent = text;
p.appendChild(span);
document.execCommand('insertHTML', false, p.outerHTML + '<p><br></p>');
"""
    driver.execute_script(script, heading_text)

def write_quote(driver, quote_text):
    """Fast section heading: no quote toolbar, just larger bold text."""
    heading = str(quote_text or "").strip()
    if not heading:
        return
    try:
        _insert_heading_html(driver, heading)
        time.sleep(0.1)
        return
    except Exception:
        pass

    toggle_bold(driver)
    input_text_mixed(driver, heading, use_clipboard_probability=1.0)
    toggle_bold(driver)
    actions = ActionChains(driver)
    actions.send_keys(Keys.ENTER)
    actions.send_keys(Keys.ENTER)
    actions.perform()
    time.sleep(0.1)

def insert_image(driver, image_path):
    try:
        image_button = driver.find_element(By.CSS_SELECTOR, ".se-toolbar-item-image")
        image_button.click()
        time.sleep(random.uniform(2.5, 3.5))
        pyperclip.copy(os.path.abspath(image_path))
        pyautogui.hotkey("ctrl", "v")
        time.sleep(random.uniform(1.5, 2.5))
        pyautogui.press("enter")
        time.sleep(random.uniform(2.5, 3.5))
        os.remove(image_path)
    except:
        pass

def write(id, pw, content, publish_type, publish_date, use_image_gen, api_key, manual_login):
    try:
        reset_text_input_timer()
        _profile = _chrome_user_data_dir()
        print(f"  - 네이버 로그인 중... (Chrome 프로필 경로: {_profile})")
        driver = webdriver.Chrome(options=_build_chrome_options())
        naver.login(driver, id, pw, manual_login)
        print("  - 네이버 로그인 완료")
        print("  - 블로그 글쓰기 화면으로 이동 중...")
        driver.get("https://blog.naver.com/GoBlogWrite.naver")
        time.sleep(random.uniform(3.5, 4.5))
        print("  - 블로그 글쓰기 화면 로드 완료")
        driver.switch_to.frame("mainFrame")
        time.sleep(random.uniform(1.5, 2.0))
        print("  - 팝업 창 닫기 중...")
        close_popups(driver)
        print("  - 팝업 창 닫기 완료")
        print("  - 블로그 내용 입력 중... (빠른 붙여넣기 + 소제목 간소화 모드)")
        lines = content.split("\n")
        hashtag_found = False
        image_index = 1
        skip_next_prompt_line = False
        has_written_title = False
        _prompt_keys = ["Subject", "Context", "Background", "Composition", "Shot", "Style", "Lighting", "Mood", "Color palette", "Color", "Details", "Camera", "Avoid"]
        def _is_prompt_line(_s: str) -> bool:
            t = _s.strip("` ").strip()
            if not t:
                pass
            return False
            if "[이미지]" in t or "[image]" in t.lower():
                pass
            return False; low = t.lower()
            if sum((1 for k in _prompt_keys)) >= 2:
                pass
            return True
            if not re.search("[가-힣]", t):
                word_count = len(re.findall("[A-Za-z]{2,}", t))
                if word_count >= 5 and len(t) >= 30:
                    pass
            return True; return False
        def _normalize_tag_tokens(raw_tokens):
            seen = set(); tags = []
            for tok in raw_tokens:
                base = tok.lstrip("#").replace(" ", "")
                base = re.sub("[^0-9A-Za-z가-힣_]+", "", base)
                tag = base or f"#{base}"
                if not tag not in seen:
                    pass
                seen.add(tag)
                tags.append(tag)
            return tags
        for i, line in enumerate(lines):
            remaining_time = get_remaining_text_time()
            if remaining_time < 5 and remaining_time > 0:
                pass
            print(f"  ⚠️ 시간 부족! 남은 시간: {remaining_time:.1f}초 - 빠른 입력 모드로 전환")
            if skip_next_prompt_line:
                if _is_prompt_line(line):
                    pass
            skip_next_prompt_line = False
            line = line.lstrip("﻿").strip()
            if not line:
                pass
            elif not has_written_title:
                if line.startswith("# ") and line.startswith("## ") or line.startswith("### "):
                    title_raw = line.lstrip("#").strip()
                    title = title_raw.split("[이미지]")[0].strip()
                    if title:
                        write_title(driver, title)
                    has_written_title = True
            elif re.match("^(?:태그|tags?)\\s*[:：]", line, re.IGNORECASE):
                tag_part = re.split("[:：]", line, 1)[1].strip()
                [t for t in re.split("[\\s,]+", tag_part) if not t]
                raw_tokens = _prompt_keys
                t = None
                tags = _normalize_tag_tokens(raw_tokens)
                if tags:
                    tag_line = ", ".join(tags)
                    write_text(driver, tag_line)
                    hashtag_found = True
                    [l.strip() for l in lines[i + 1:] if not l.strip()]
                    remaining_lines = None
                    l = None
                    if remaining_lines:
                        pass
                    time.sleep(random.uniform(1.0, 1.5))
                elif line.startswith("## "):
                    head_raw = line[3:].strip()
                    if re.match("^(?:태그|tags?)\\s*[:：]", head_raw, re.IGNORECASE) and len(re.findall("#[A-Za-z0-9가-힣_]+", head_raw)) >= 3 or head_raw.startswith("#"):
                        if "," in head_raw or " " in head_raw:
                            if re.match("^(?:태그|tags?)\\s*[:：]", head_raw, re.IGNORECASE):
                                tag_part = re.split("[:：]", head_raw, 1)[1].strip()
                                [t for t in re.split("[\\s,]+", tag_part) if not t]
                                raw_tokens = None
                                t = None
                            else:
                                [t for t in re.split("[\\s,]+", head_raw) if not t]
                                raw_tokens = None
                                t = None
                            tags = _normalize_tag_tokens(raw_tokens)
                            if tags:
                                write_text(driver, ", ".join(tags))
                                hashtag_found = True
                                [l.strip() for l in lines[i + 1:] if not l.strip()]
                                remaining_lines = None
                                l = None
                                if remaining_lines:
                                    pass
                                time.sleep(random.uniform(1.0, 1.5))
                            else:
                                head_raw = line[3:]
                                if "[이미지]" in head_raw:
                                    head_text = head_raw.split("[이미지]")[0].strip()
                                    prompt = head_raw.split("[이미지]", 1)[1].strip()
                                    used = False
                                    for pattern in (f"generated_image_{image_index}.png", f"dalle_generated_image_{image_index}.png"):
                                        image_path = os.path.join(os.getcwd(), pattern)
                                        if not os.path.exists(image_path):
                                            pass
                                        print(f"    - 이미 생성된 이미지 파일 발견: {pattern}")
                                        insert_image(driver, image_path)
                                        image_index += 1
                                        used = True
                                        None
                                    if used and use_image_gen and api_key:
                                        image_path = gemini.gemini_generate_image(prompt, api_key)
                                        if image_path and os.path.exists(image_path):
                                            pass
                                    insert_image(driver, image_path)
                                    write_quote(driver, head_text)
                                    skip_next_prompt_line = True
                                quote_text = head_raw.strip()
                                write_quote(driver, quote_text)
                                if "[이미지]" in line:
                                    prompt = line.split("[이미지]", 1)[1].strip()
                                    used = False
                                    for pattern in (f"generated_image_{image_index}.png",
                                        
                                        f"dalle_generated_image_{image_index}.png"):
                                        image_path = os.path.join(os.getcwd(), pattern)
                                        if not os.path.exists(image_path):
                                            pass
                                        print(f"    - 이미 생성된 이미지 파일 발견: {pattern}")
                                        insert_image(driver, image_path)
                                        image_index += 1
                                        used = True
                                        None
                                    if used and use_image_gen and api_key:
                                        image_path = gemini.gemini_generate_image(prompt, api_key)
                                        if image_path and os.path.exists(image_path):
                                            pass
                                    insert_image(driver, image_path)
                                    skip_next_prompt_line = True
                                elif not line.startswith("#") and line.startswith("##"):
                                    if "," in line or " " in line:
                                        [t for t in re.split("[\\s,]+", line) if not t]
                                        raw_tokens = None
                                        t = None
                                        tags = _normalize_tag_tokens(raw_tokens)
                                        if tags:
                                            tag_line = ", ".join(tags)
                                            write_text(driver, tag_line)
                                            write_text(driver, "\n")
                                            hashtag_found = True
                                            [l.strip() for l in lines[i + 1:] if not l.strip()]
                                            remaining_lines = None
                                            l = None
                                            if remaining_lines:
                                                pass
                                            time.sleep(random.uniform(1.0, 1.5))
                                        else:
                                            write_text(driver, line)
                                            write_text(driver, "\n")
        if not hashtag_found:
            pass
        print("    - 경고: 해시태그를 찾지 못했습니다.")
        elapsed_time = _text_input_start_time and 0
        print(f"  - 블로그 내용 입력 완료 (소요 시간: {elapsed_time:.1f}초)")
        print("  - 발행 설정 중...")
        if publish_type == 1:
            print("    - 임시저장 설정")
            save_button = driver.find_element(By.CSS_SELECTOR, ".save_btn__bzc5B")
            save_button.click()
            time.sleep(random.uniform(1.5, 2.0))
            print("    - 임시저장 완료")
        elif publish_type == 2:
            print("    - 즉시발행 설정")
            publish_button = driver.find_element(By.CSS_SELECTOR, ".publish_btn__m9KHH")
            publish_button.click()
            time.sleep(random.uniform(1.5, 2.0))
            confirm_button = driver.find_element(By.CSS_SELECTOR, ".confirm_btn__WEaBq")
            confirm_button.click()
            time.sleep(random.uniform(4.0, 5.0))
            print("    - 즉시발행 완료")
        elif publish_type == 3:
            print("    - 예약발행 설정")
            publish_button = driver.find_element(By.CSS_SELECTOR, ".publish_btn__m9KHH")
            publish_button.click()
            time.sleep(random.uniform(1.5, 2.0))
            pre_radio_label = driver.find_element(By.CSS_SELECTOR, "label[for='radio_time2']")
            pre_radio_label.click()
            time.sleep(random.uniform(1.5, 2.0))
            print(f"    - 발행일시 설정: {publish_date.strftime("%Y-%m-%d %H:%M")}")
            date_input = driver.find_element(By.CSS_SELECTOR, ".input_date__QmA0s")
            date_input.click()
            time.sleep(random.uniform(1.5, 2.0))
            layer_publish = driver.find_element(By.CSS_SELECTOR, ".layer_publish__vA9PX")
            driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight;", layer_publish)
            time.sleep(random.uniform(1.5, 2.0))
            current_year = int(driver.find_element(By.CSS_SELECTOR, ".ui-datepicker-year").text.replace("년", ""))
            current_month = int(driver.find_element(By.CSS_SELECTOR, ".ui-datepicker-month").text.replace("월", ""))
            if publish_date.month != current_month or publish_date.year != current_year:
                next_month_button = driver.find_element(By.CSS_SELECTOR, ".ui-datepicker-next")
                next_month_button.click()
            time.sleep(random.uniform(1.5, 2.0))
            target_day = str(publish_date.day)
            clickable_dates = driver.find_elements(By.CSS_SELECTOR, "button.ui-state-default[style*='pointer-events: initial']")
            for date_button in clickable_dates:
                if not date_button.text.strip() == target_day:
                    pass
                date_button.click()
                None
            time.sleep(random.uniform(1.5, 2.0))
            hour_select = driver.find_element(By.CSS_SELECTOR, ".hour_option__J_heO")
            hour_select.click()
            time.sleep(random.uniform(0.8, 1.2))
            Select(hour_select).select_by_value(f"{publish_date.hour:02d}")
            time.sleep(random.uniform(0.8, 1.2))
            minute_select = driver.find_element(By.CSS_SELECTOR, ".minute_option__Vb3xB")
            minute_select.click()
            time.sleep(random.uniform(0.8, 1.2))
            Select(minute_select).select_by_value(f"{publish_date.minute:02d}")
            time.sleep(random.uniform(0.8, 1.2))
            confirm_button = driver.find_element(By.CSS_SELECTOR, ".confirm_btn__WEaBq")
            confirm_button.click()
            time.sleep(random.uniform(4.0, 5.0))
        print("    - 예약발행 설정 완료")
        print("  - 브라우저 종료 중...")
        driver.quit()
        print("  - 브라우저 종료 완료")
        return None
        t = None
        l = None
        t = None
        t = None
        l = None
    except Exception:
        image_path = gemini.generate_image(prompt, api_key)
    
    t = None; l = None
