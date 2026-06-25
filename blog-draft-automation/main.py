"""블로그 초안 생성기 GUI 실행 파일입니다.

여러 참고 링크를 저장해두고, 저장된 링크를 자동 감시/수동 초안 생성에 재사용할 수 있습니다.
"""

from __future__ import annotations

import threading
import tkinter as tk
import webbrowser
from tkinter import filedialog, messagebox, ttk

from app_settings import load_settings, save_settings
from automation_engine import process_new_posts_once
from config import APP_NAME, DEFAULT_ARTICLE_PROMPT, DEFAULT_IMAGE_PROMPT
from crawler import Article, fetch_articles
from file_saver import save_docx, save_txt
from image_searcher import attribution_block, download_image, search_free_images
from link_store import delete_link, links_to_text, load_links, upsert_link
from monitor import fetch_latest_articles, fetch_new_articles
from naver_publisher import PublishRequest, publish_to_naver
from post_db import export_draft, mark_post, recent_posts
from searcher import collect_overseas_sources
from writer import generate_blog_draft


class BlogDraftApp(tk.Tk):
    """수집, 재작성, 이미지 검색, 네이버 보내기를 한 화면에서 다루는 GUI입니다."""

    def __init__(self) -> None:
        super().__init__()
        self.title(APP_NAME)
        self.geometry("1380x860")
        self.minsize(1120, 720)

        self.settings = load_settings()
        self.pending_items: list[tuple[object, Article]] = []
        self.generated_text = ""
        self.downloaded_image_paths: list[str] = []
        self.monitor_stop = threading.Event()
        self.monitor_thread: threading.Thread | None = None

        self._build_ui()
        self._load_settings_to_ui()
        self.refresh_saved_links()
        self.log("[시스템] 프로그램을 시작했습니다.")

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.tabs = ttk.Notebook(self)
        self.tabs.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        self.work_tab = ttk.Frame(self.tabs, padding=10)
        self.manual_tab = ttk.Frame(self.tabs, padding=10)
        self.settings_tab = ttk.Frame(self.tabs, padding=10)
        self.logs_tab = ttk.Frame(self.tabs, padding=10)

        self.tabs.add(self.work_tab, text="자동 작업")
        self.tabs.add(self.manual_tab, text="수동 초안")
        self.tabs.add(self.settings_tab, text="설정")
        self.tabs.add(self.logs_tab, text="로그/이력")

        self._build_work_tab()
        self._build_manual_tab()
        self._build_settings_tab()
        self._build_logs_tab()

    def _build_work_tab(self) -> None:
        self.work_tab.columnconfigure(0, weight=0, minsize=430)
        self.work_tab.columnconfigure(1, weight=1)
        self.work_tab.rowconfigure(0, weight=1)

        left = ttk.Frame(self.work_tab)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        left.columnconfigure(0, weight=1)

        source_box = ttk.LabelFrame(left, text="1. 저장 링크/구독 블로그", padding=10)
        source_box.grid(row=0, column=0, sticky="ew")
        source_box.columnconfigure(0, weight=1)

        self.subscription_text = tk.Text(source_box, height=5, wrap="word")
        self.subscription_text.grid(row=0, column=0, sticky="ew")
        ttk.Label(source_box, text="블로그 ID 또는 URL을 여러 줄로 입력할 수 있습니다.").grid(row=1, column=0, sticky="w", pady=(4, 0))

        link_form = ttk.Frame(source_box)
        link_form.grid(row=2, column=0, sticky="ew", pady=(8, 0))
        link_form.columnconfigure(0, weight=1)
        self.link_url_entry = ttk.Entry(link_form)
        self.link_url_entry.grid(row=0, column=0, sticky="ew", padx=(0, 4))
        self.link_kind_var = tk.StringVar(value="blog")
        ttk.Combobox(link_form, textvariable=self.link_kind_var, values=["blog", "reference"], width=10, state="readonly").grid(row=0, column=1, padx=(0, 4))
        ttk.Button(link_form, text="링크 저장", command=self.add_saved_link_from_entry).grid(row=0, column=2)

        self.saved_link_tree = ttk.Treeview(source_box, columns=("kind", "url"), show="tree headings", height=5, selectmode="extended")
        self.saved_link_tree.heading("#0", text="이름")
        self.saved_link_tree.heading("kind", text="구분")
        self.saved_link_tree.heading("url", text="URL")
        self.saved_link_tree.column("#0", width=90)
        self.saved_link_tree.column("kind", width=70, anchor="center")
        self.saved_link_tree.column("url", width=250)
        self.saved_link_tree.grid(row=3, column=0, sticky="ew", pady=(8, 0))

        link_buttons = ttk.Frame(source_box)
        link_buttons.grid(row=4, column=0, sticky="ew", pady=(6, 0))
        ttk.Button(link_buttons, text="선택 링크를 감시 목록에 넣기", command=self.use_selected_links).pack(side="left")
        ttk.Button(link_buttons, text="선택 삭제", command=self.delete_selected_saved_links).pack(side="left", padx=6)
        ttk.Button(link_buttons, text="목록 새로고침", command=self.refresh_saved_links).pack(side="left")

        button_box = ttk.LabelFrame(left, text="2. 실행", padding=10)
        button_box.grid(row=1, column=0, sticky="ew", pady=10)
        button_box.columnconfigure((0, 1), weight=1)
        ttk.Button(button_box, text="지금 새 글 확인", command=self.start_check_new_posts).grid(row=0, column=0, sticky="ew", padx=(0, 4))
        ttk.Button(button_box, text="선택 링크 최신 3개", command=self.start_fetch_selected_latest3).grid(row=2, column=0, sticky="ew", padx=(0, 4), pady=(8, 0))
        ttk.Button(button_box, text="4시간 자동 감시 시작", command=self.start_monitor).grid(row=0, column=1, sticky="ew", padx=(4, 0))
        ttk.Button(button_box, text="감시 중지", command=self.stop_monitor).grid(row=1, column=0, columnspan=2, sticky="ew", pady=(8, 0))

        action_box = ttk.LabelFrame(left, text="3. 선택 글 처리", padding=10)
        action_box.grid(row=2, column=0, sticky="ew")
        action_box.columnconfigure(0, weight=1)
        ttk.Button(action_box, text="선택 글로 초안 만들기", command=self.start_generate_selected).grid(row=0, column=0, sticky="ew")
        ttk.Button(action_box, text="목록 전체로 초안 만들기", command=self.start_generate_all_pending).grid(row=1, column=0, sticky="ew", pady=(8, 0))
        ttk.Button(action_box, text="무료 이미지 찾기", command=self.start_image_search).grid(row=2, column=0, sticky="ew", pady=(8, 0))
        ttk.Button(action_box, text="네이버 임시저장으로 보내기", command=lambda: self.start_naver_send("draft")).grid(row=3, column=0, sticky="ew", pady=(8, 0))
        ttk.Button(action_box, text="네이버 예약설정 화면까지 보내기", command=lambda: self.start_naver_send("scheduled")).grid(row=4, column=0, sticky="ew", pady=(8, 0))

        status_box = ttk.LabelFrame(left, text="상태", padding=10)
        status_box.grid(row=3, column=0, sticky="nsew", pady=10)
        left.rowconfigure(3, weight=1)
        status_box.columnconfigure(0, weight=1)
        status_box.rowconfigure(0, weight=1)
        self.status_text = tk.Text(status_box, height=8, wrap="word", state="disabled")
        self.status_text.grid(row=0, column=0, sticky="nsew")

        right = ttk.Frame(self.work_tab)
        right.grid(row=0, column=1, sticky="nsew")
        right.columnconfigure(0, weight=1)
        right.rowconfigure(1, weight=1)

        list_box = ttk.LabelFrame(right, text="새 글 목록", padding=8)
        list_box.grid(row=0, column=0, sticky="ew")
        list_box.columnconfigure(0, weight=1)
        self.post_tree = ttk.Treeview(list_box, columns=("source", "date"), show="tree headings", height=7)
        self.post_tree.heading("#0", text="제목")
        self.post_tree.heading("source", text="출처")
        self.post_tree.heading("date", text="발행일")
        self.post_tree.column("#0", width=420)
        self.post_tree.column("source", width=180)
        self.post_tree.column("date", width=160)
        self.post_tree.grid(row=0, column=0, sticky="ew")

        preview = ttk.PanedWindow(right, orient="horizontal")
        preview.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
        draft_frame = ttk.LabelFrame(preview, text="초안 미리보기", padding=8)
        draft_frame.columnconfigure(0, weight=1)
        draft_frame.rowconfigure(0, weight=1)
        self.draft_text = self._text_area(draft_frame)
        preview.add(draft_frame, weight=3)
        image_frame = ttk.LabelFrame(preview, text="이미지 후보/출처", padding=8)
        image_frame.columnconfigure(0, weight=1)
        image_frame.rowconfigure(0, weight=1)
        self.image_text = self._text_area(image_frame)
        preview.add(image_frame, weight=2)

    def _build_manual_tab(self) -> None:
        self.manual_tab.columnconfigure(0, weight=1)
        self.manual_tab.rowconfigure(1, weight=1)
        form = ttk.LabelFrame(self.manual_tab, text="수동 초안 생성", padding=10)
        form.grid(row=0, column=0, sticky="ew")
        form.columnconfigure(1, weight=1)

        self.mode_var = tk.StringVar(value="url")
        ttk.Radiobutton(form, text="URL 참고", variable=self.mode_var, value="url").grid(row=0, column=0, sticky="w")
        ttk.Radiobutton(form, text="키워드 해외 검색", variable=self.mode_var, value="search").grid(row=0, column=1, sticky="w")
        ttk.Label(form, text="참고 URL").grid(row=1, column=0, sticky="nw", pady=(8, 0))
        self.url_text = tk.Text(form, height=4, wrap="word")
        self.url_text.grid(row=1, column=1, sticky="ew", pady=(8, 0))
        ttk.Label(form, text="키워드/주제").grid(row=2, column=0, sticky="w", pady=(8, 0))
        self.keyword_entry = ttk.Entry(form)
        self.keyword_entry.grid(row=2, column=1, sticky="ew", pady=(8, 0))

        buttons = ttk.Frame(form)
        buttons.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        ttk.Button(buttons, text="크롤링 확인", command=self.start_manual_crawl).pack(side="left")
        ttk.Button(buttons, text="글 생성", command=self.start_manual_generate).pack(side="left", padx=8)
        ttk.Button(buttons, text="입력 URL 여러 개 저장", command=self.save_manual_urls_to_links).pack(side="left")
        ttk.Button(buttons, text="선택 저장 링크 불러오기", command=self.append_selected_links_to_manual).pack(side="left", padx=8)
        ttk.Button(buttons, text="txt 저장", command=self.save_as_txt).pack(side="left")
        ttk.Button(buttons, text="docx 저장", command=self.save_as_docx).pack(side="left", padx=8)

        result_frame = ttk.LabelFrame(self.manual_tab, text="수동 결과/크롤링 확인", padding=8)
        result_frame.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
        result_frame.columnconfigure(0, weight=1)
        result_frame.rowconfigure(0, weight=1)
        self.manual_result_text = self._text_area(result_frame)

    def _build_settings_tab(self) -> None:
        self.settings_tab.columnconfigure(1, weight=1)
        row = 0
        for label, attr, hidden in [
            ("Gemini API 키", "api_key_entry", True),
            ("Pexels API 키", "pexels_key_entry", True),
            ("Pixabay API 키", "pixabay_key_entry", True),
            ("네이버 ID", "naver_id_entry", False),
            ("네이버 비밀번호", "naver_pw_entry", True),
            ("내 블로그 ID", "naver_blog_id_entry", False),
        ]:
            ttk.Label(self.settings_tab, text=label).grid(row=row, column=0, sticky="w", pady=4)
            entry = ttk.Entry(self.settings_tab, show="*" if hidden else "")
            entry.grid(row=row, column=1, sticky="ew", pady=4)
            setattr(self, attr, entry)
            row += 1

        ttk.Button(self.settings_tab, text="Gemini 키 발급", command=lambda: webbrowser.open("https://aistudio.google.com/app/apikey")).grid(row=0, column=2, padx=6)
        ttk.Button(self.settings_tab, text="Pexels", command=lambda: webbrowser.open("https://www.pexels.com/api/")).grid(row=1, column=2, padx=6)
        ttk.Button(self.settings_tab, text="Pixabay", command=lambda: webbrowser.open("https://pixabay.com/api/docs/")).grid(row=2, column=2, padx=6)

        ttk.Label(self.settings_tab, text="확인 주기(시간)").grid(row=row, column=0, sticky="w", pady=4)
        self.monitor_interval_entry = ttk.Entry(self.settings_tab, width=10)
        self.monitor_interval_entry.grid(row=row, column=1, sticky="w", pady=4)
        row += 1
        ttk.Label(self.settings_tab, text="기본 글자 수").grid(row=row, column=0, sticky="w", pady=4)
        self.length_entry = ttk.Entry(self.settings_tab, width=10)
        self.length_entry.grid(row=row, column=1, sticky="w", pady=4)
        row += 1
        ttk.Label(self.settings_tab, text="기본 문체").grid(row=row, column=0, sticky="w", pady=4)
        self.style_var = tk.StringVar(value="정보형")
        ttk.Combobox(self.settings_tab, textvariable=self.style_var, values=["정보형", "후기형", "상담형", "홍보형", "전문가형"], state="readonly").grid(row=row, column=1, sticky="w", pady=4)
        row += 1

        self.save_api_key_var = tk.BooleanVar(value=False)
        self.remember_login_var = tk.BooleanVar(value=False)
        self.manual_login_var = tk.BooleanVar(value=True)
        self.auto_download_images_var = tk.BooleanVar(value=True)
        self.auto_publish_var = tk.BooleanVar(value=False)
        for text, var in [
            ("API 키 저장", self.save_api_key_var),
            ("네이버 로그인 정보 저장", self.remember_login_var),
            ("수동 로그인 모드 권장", self.manual_login_var),
            ("무료 이미지 상위 2개 자동 다운로드", self.auto_download_images_var),
            ("자동 감시 중 네이버 임시/예약 저장까지 시도", self.auto_publish_var),
        ]:
            ttk.Checkbutton(self.settings_tab, text=text, variable=var).grid(row=row, column=1, sticky="w")
            row += 1

        button_row = ttk.Frame(self.settings_tab)
        button_row.grid(row=row, column=0, columnspan=3, sticky="ew", pady=12)
        ttk.Button(button_row, text="글쓰기 프롬프트 수정", command=lambda: self.open_prompt_editor("article")).pack(side="left")
        ttk.Button(button_row, text="이미지 프롬프트 수정", command=lambda: self.open_prompt_editor("image")).pack(side="left", padx=8)
        ttk.Button(button_row, text="설정 저장", command=self.save_current_settings).pack(side="left")

    def _build_logs_tab(self) -> None:
        self.logs_tab.columnconfigure(0, weight=1)
        self.logs_tab.rowconfigure(0, weight=1)
        pane = ttk.PanedWindow(self.logs_tab, orient="horizontal")
        pane.grid(row=0, column=0, sticky="nsew")
        log_frame = ttk.LabelFrame(pane, text="실행 로그", padding=8)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        self.log_text = self._text_area(log_frame, state="disabled")
        pane.add(log_frame, weight=1)
        history_frame = ttk.LabelFrame(pane, text="처리 이력", padding=8)
        history_frame.columnconfigure(0, weight=1)
        history_frame.rowconfigure(0, weight=1)
        self.history_text = self._text_area(history_frame)
        pane.add(history_frame, weight=1)
        ttk.Button(self.logs_tab, text="처리 이력 새로고침", command=self.refresh_history).grid(row=1, column=0, sticky="ew", pady=(8, 0))

    def _text_area(self, parent: ttk.Frame, state: str = "normal") -> tk.Text:
        text = tk.Text(parent, wrap="word", undo=True, state=state)
        text.grid(row=0, column=0, sticky="nsew")
        scroll = ttk.Scrollbar(parent, command=text.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        text.configure(yscrollcommand=scroll.set)
        return text

    def _load_settings_to_ui(self) -> None:
        self.api_key_entry.insert(0, self.settings.get("api_key", ""))
        self.pexels_key_entry.insert(0, self.settings.get("pexels_api_key", ""))
        self.pixabay_key_entry.insert(0, self.settings.get("pixabay_api_key", ""))
        self.naver_id_entry.insert(0, self.settings.get("naver_id", ""))
        self.naver_pw_entry.insert(0, self.settings.get("naver_password", ""))
        self.naver_blog_id_entry.insert(0, self.settings.get("naver_blog_id", ""))
        self.subscription_text.insert("1.0", self.settings.get("subscription_sources", ""))
        self.monitor_interval_entry.insert(0, str(self.settings.get("monitor_interval_hours", 4)))
        self.length_entry.insert(0, str(self.settings.get("target_length", "2000")))
        self.style_var.set(self.settings.get("style", "정보형"))
        self.save_api_key_var.set(bool(self.settings.get("save_api_key", False)))
        self.remember_login_var.set(bool(self.settings.get("remember_login", False)))
        self.manual_login_var.set(bool(self.settings.get("manual_login", True)))
        self.auto_download_images_var.set(bool(self.settings.get("auto_download_images", True)))
        self.auto_publish_var.set(bool(self.settings.get("auto_publish_enabled", False)))

    def _settings_from_ui(self) -> dict:
        return {
            "api_key": self.api_key_entry.get().strip(),
            "pexels_api_key": self.pexels_key_entry.get().strip(),
            "pixabay_api_key": self.pixabay_key_entry.get().strip(),
            "save_api_key": self.save_api_key_var.get(),
            "naver_id": self.naver_id_entry.get().strip(),
            "naver_password": self.naver_pw_entry.get().strip(),
            "naver_blog_id": self.naver_blog_id_entry.get().strip(),
            "remember_login": self.remember_login_var.get(),
            "manual_login": self.manual_login_var.get(),
            "article_prompt": self.settings.get("article_prompt", DEFAULT_ARTICLE_PROMPT),
            "image_prompt": self.settings.get("image_prompt", DEFAULT_IMAGE_PROMPT),
            "subscription_sources": self.subscription_text.get("1.0", "end").strip(),
            "monitor_interval_hours": self._monitor_interval(),
            "target_length": self.length_entry.get().strip() or "2000",
            "auto_download_images": self.auto_download_images_var.get(),
            "auto_publish_enabled": self.auto_publish_var.get(),
            "style": self.style_var.get(),
        }

    def save_current_settings(self) -> None:
        self.settings.update(self._settings_from_ui())
        save_settings(self.settings)
        self.log("[설정] 저장했습니다.")

    def open_prompt_editor(self, kind: str) -> None:
        title = "글쓰기 프롬프트" if kind == "article" else "이미지 프롬프트"
        key = "article_prompt" if kind == "article" else "image_prompt"
        default = DEFAULT_ARTICLE_PROMPT if kind == "article" else DEFAULT_IMAGE_PROMPT
        win = tk.Toplevel(self)
        win.title(title)
        win.geometry("760x520")
        win.columnconfigure(0, weight=1)
        win.rowconfigure(0, weight=1)
        text = tk.Text(win, wrap="word", undo=True)
        text.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        text.insert("1.0", self.settings.get(key, default))

        def save_prompt() -> None:
            self.settings[key] = text.get("1.0", "end").strip() or default
            self.save_current_settings()
            win.destroy()

        ttk.Button(win, text="저장", command=save_prompt).grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))

    def log(self, message: str) -> None:
        self.after(0, self._append_log, message)

    def _append_log(self, message: str) -> None:
        for widget in (self.log_text, self.status_text):
            widget.configure(state="normal")
            widget.insert("end", message + "\n")
            widget.see("end")
            widget.configure(state="disabled")

    def refresh_saved_links(self) -> None:
        if not hasattr(self, "saved_link_tree"):
            return
        for item in self.saved_link_tree.get_children():
            self.saved_link_tree.delete(item)
        for link in load_links():
            self.saved_link_tree.insert("", "end", iid=link.id, text=link.name, values=(link.kind, link.url))

    def _selected_saved_links(self):
        selected_ids = list(self.saved_link_tree.selection()) if hasattr(self, "saved_link_tree") else []
        by_id = {link.id: link for link in load_links()}
        return [by_id[item_id] for item_id in selected_ids if item_id in by_id]

    def add_saved_link_from_entry(self) -> None:
        try:
            link = upsert_link(self.link_url_entry.get(), kind=self.link_kind_var.get())
            self.link_url_entry.delete(0, "end")
            self.refresh_saved_links()
            self.log(f"[링크] 저장 완료: {link.url}")
        except Exception as exc:
            messagebox.showwarning("링크 저장 실패", str(exc))

    def delete_selected_saved_links(self) -> None:
        selected = self._selected_saved_links()
        if not selected:
            messagebox.showwarning("선택 필요", "삭제할 링크를 선택해 주세요.")
            return
        for link in selected:
            delete_link(link.id)
        self.refresh_saved_links()
        self.log(f"[링크] {len(selected)}개 삭제 완료")

    def use_selected_links(self) -> None:
        selected = self._selected_saved_links()
        if not selected:
            messagebox.showwarning("선택 필요", "사용할 링크를 선택해 주세요.")
            return
        current = self.subscription_text.get("1.0", "end").strip()
        urls = links_to_text(selected)
        merged = "\n".join(part for part in [current, urls] if part).strip()
        self.subscription_text.delete("1.0", "end")
        self.subscription_text.insert("1.0", merged)
        self.log(f"[링크] 선택 링크 {len(selected)}개를 감시 목록에 넣었습니다.")

    def append_selected_links_to_manual(self) -> None:
        selected = self._selected_saved_links()
        if not selected:
            messagebox.showwarning("선택 필요", "불러올 링크를 자동 작업 탭 목록에서 선택해 주세요.")
            return
        current = self.url_text.get("1.0", "end").strip()
        urls = links_to_text(selected)
        merged = "\n".join(part for part in [current, urls] if part).strip()
        self.url_text.delete("1.0", "end")
        self.url_text.insert("1.0", merged)
        self.tabs.select(self.manual_tab)
        self.log(f"[링크] 선택 링크 {len(selected)}개를 수동 URL 입력칸에 불러왔습니다.")

    def save_manual_urls_to_links(self) -> None:
        urls = [line.strip() for line in self.url_text.get("1.0", "end").splitlines() if line.strip()]
        if not urls:
            messagebox.showwarning("입력 필요", "저장할 URL을 한 줄에 하나씩 입력해 주세요.")
            return
        saved = 0
        for url in urls:
            try:
                upsert_link(url, kind="reference")
                saved += 1
            except Exception as exc:
                self.log(f"[경고] 링크 저장 실패: {url} - {exc}")
        self.refresh_saved_links()
        self.log(f"[링크] 수동 입력 URL {saved}개 저장 완료")

    def _subscription_sources(self) -> list[str]:
        raw = self.subscription_text.get("1.0", "end").strip()
        return [line.strip() for line in raw.splitlines() if line.strip()]

    def _monitor_interval(self) -> float:
        try:
            return max(0.05, float(self.monitor_interval_entry.get().strip() or 4))
        except ValueError:
            return 4.0

    def start_fetch_selected_latest3(self) -> None:
        selected = self._selected_saved_links()
        if not selected:
            messagebox.showwarning("선택 필요", "최신 글을 가져올 저장 링크를 선택해 주세요.")
            return
        sources = [link.url for link in selected]
        self.log(f"[구독] 선택 링크 {len(sources)}개의 최신 글 3개 확인을 시작합니다.")
        threading.Thread(target=self._fetch_selected_latest3_worker, args=(sources,), daemon=True).start()

    def _fetch_selected_latest3_worker(self, sources: list[str]) -> None:
        try:
            self.pending_items = fetch_latest_articles(sources, per_source_limit=3, log=self.log)
            self.after(0, self._refresh_post_tree)
            self.log(f"[구독] 최신 글 후보 {len(self.pending_items)}개를 가져왔습니다.")
        except Exception as exc:
            self.log(f"[오류] 최신 글 3개 가져오기 실패: {exc}")

    def start_generate_all_pending(self) -> None:
        if not self.pending_items:
            messagebox.showwarning("목록 없음", "먼저 최신 글을 가져오거나 새 글을 확인해 주세요.")
            return
        self.save_current_settings()
        self.log(f"[생성] 목록의 글 {len(self.pending_items)}개를 묶어 초안 생성을 시작합니다.")
        threading.Thread(target=self._generate_all_pending_worker, daemon=True).start()

    def _generate_all_pending_worker(self) -> None:
        try:
            articles = [article for _, article in self.pending_items]
            keyword = self.keyword_entry.get().strip() or (articles[0].title if articles else "")
            draft, _ = generate_blog_draft(
                articles=articles,
                api_key=self.api_key_entry.get().strip(),
                style=self.style_var.get(),
                target_length=self.length_entry.get().strip(),
                keyword=keyword,
                mode_name="저장 링크 최신 글 묶음 기반 작성",
                article_prompt=self.settings.get("article_prompt", DEFAULT_ARTICLE_PROMPT),
                publish_type="임시 저장",
                log=self.log,
            )
            self.generated_text = draft
            title = keyword or "latest_posts_draft"
            path = export_draft(title, draft)
            for feed_item, article in self.pending_items:
                mark_post(feed_item.source_url, feed_item.post_url, article.title, feed_item.published_at, article.text, "draft_saved_bundle", str(path))
            self.after(0, self._show_draft, draft)
            self.log(f"[생성] 묶음 초안 저장 완료: {path}")
            self.refresh_history()
        except Exception as exc:
            self.log(f"[오류] 묶음 초안 생성 실패: {exc}")

    def start_check_new_posts(self) -> None:
        if not self._subscription_sources():
            messagebox.showwarning("입력 필요", "구독 블로그 ID/URL을 입력하거나 저장 링크를 선택해 주세요.")
            return
        self.save_current_settings()
        self.log("[구독] 새 글 확인을 시작합니다.")
        threading.Thread(target=self._check_new_posts_worker, daemon=True).start()

    def _check_new_posts_worker(self) -> None:
        try:
            self.pending_items = fetch_new_articles(self._subscription_sources(), log=self.log)
            self.after(0, self._refresh_post_tree)
            self.log(f"[구독] 새 글 후보 {len(self.pending_items)}개를 찾았습니다.")
        except Exception as exc:
            self.log(f"[오류] 새 글 확인 실패: {exc}")

    def _refresh_post_tree(self) -> None:
        for item in self.post_tree.get_children():
            self.post_tree.delete(item)
        for index, (feed_item, article) in enumerate(self.pending_items):
            self.post_tree.insert("", "end", iid=str(index), text=article.title or feed_item.title, values=(feed_item.source_url, feed_item.published_at))

    def _selected_pending(self) -> tuple[object, Article] | None:
        selected = self.post_tree.selection()
        if not selected:
            messagebox.showwarning("선택 필요", "새 글 목록에서 글을 선택해 주세요.")
            return None
        index = int(selected[0])
        return self.pending_items[index] if index < len(self.pending_items) else None

    def start_generate_selected(self) -> None:
        selected = self._selected_pending()
        if not selected:
            return
        self.save_current_settings()
        self.log("[생성] 선택 글 초안 생성을 시작합니다.")
        threading.Thread(target=self._generate_selected_worker, args=(selected,), daemon=True).start()

    def _generate_selected_worker(self, selected: tuple[object, Article]) -> None:
        feed_item, article = selected
        try:
            draft, _ = generate_blog_draft(
                articles=[article],
                api_key=self.api_key_entry.get().strip(),
                style=self.style_var.get(),
                target_length=self.length_entry.get().strip(),
                keyword=article.title,
                mode_name="구독 블로그 새 글 기반 작성",
                article_prompt=self.settings.get("article_prompt", DEFAULT_ARTICLE_PROMPT),
                publish_type="임시 저장",
                log=self.log,
            )
            self.generated_text = draft
            path = export_draft(article.title, draft)
            mark_post(feed_item.source_url, feed_item.post_url, article.title, feed_item.published_at, article.text, "draft_saved", str(path))
            self.after(0, self._show_draft, draft)
            self.log(f"[생성] 초안 저장 완료: {path}")
            self.refresh_history()
        except Exception as exc:
            self.log(f"[오류] 초안 생성 실패: {exc}")

    def start_image_search(self) -> None:
        self.log("[이미지] 무료 이미지 검색을 시작합니다.")
        threading.Thread(target=self._image_search_worker, daemon=True).start()

    def _image_search_worker(self) -> None:
        try:
            draft = self.draft_text.get("1.0", "end").strip() or self.manual_result_text.get("1.0", "end").strip()
            query = self.keyword_entry.get().strip() or "business technology"
            if "OpenAI" in draft or "오픈AI" in draft:
                query = "AI data center semiconductor memory chip"
            candidates = search_free_images(query, self.pexels_key_entry.get().strip(), self.pixabay_key_entry.get().strip(), limit=10)
            lines = [f"검색어: {query}", f"후보 수: {len(candidates)}", ""]
            self.downloaded_image_paths = []
            for i, candidate in enumerate(candidates, start=1):
                lines += [f"[{i}] {candidate.provider} - {candidate.title}", f"이미지: {candidate.image_url}", f"페이지: {candidate.page_url}", f"출처: {candidate.attribution()}", ""]
            if self.auto_download_images_var.get():
                for candidate in candidates[:2]:
                    try:
                        path = download_image(candidate)
                        self.downloaded_image_paths.append(str(path))
                        lines.append(f"다운로드 완료: {path}")
                    except Exception as exc:
                        lines.append(f"다운로드 실패: {exc}")
            lines.append("\n" + attribution_block(candidates[:2]))
            self.after(0, self._show_images, "\n".join(lines))
            self.log("[이미지] 검색 완료")
        except Exception as exc:
            self.log(f"[오류] 이미지 검색 실패: {exc}")

    def start_naver_send(self, mode: str) -> None:
        content = self.draft_text.get("1.0", "end").strip() or self.manual_result_text.get("1.0", "end").strip()
        if not content:
            messagebox.showwarning("본문 없음", "먼저 초안을 생성해 주세요.")
            return
        if not self.naver_blog_id_entry.get().strip():
            messagebox.showwarning("블로그 ID 필요", "설정 탭에서 내 블로그 ID를 입력해 주세요.")
            return
        self.log("[네이버] 브라우저 자동화를 시작합니다.")
        threading.Thread(target=self._naver_send_worker, args=(mode, content), daemon=True).start()

    def _naver_send_worker(self, mode: str, content: str) -> None:
        try:
            title = "자동 생성 초안"
            for line in content.splitlines():
                if line.strip() and not line.startswith(("-", "1.", "2.", "3.", "4.", "---")):
                    title = line.strip()[:90]
                    break
            publish_to_naver(
                PublishRequest(
                    blog_id=self.naver_blog_id_entry.get().strip(),
                    title=title,
                    body=content,
                    image_paths=self.downloaded_image_paths,
                    mode=mode,
                    naver_id=self.naver_id_entry.get().strip(),
                    naver_password=self.naver_pw_entry.get().strip(),
                    manual_login=self.manual_login_var.get(),
                ),
                log=self.log,
            )
        except Exception as exc:
            self.log(f"[오류] 네이버 보내기 실패: {exc}")

    def start_monitor(self) -> None:
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.log("[감시] 이미 실행 중입니다.")
            return
        if not self._subscription_sources():
            messagebox.showwarning("입력 필요", "구독 블로그 ID/URL을 입력하거나 저장 링크를 선택해 주세요.")
            return
        self.save_current_settings()
        self.monitor_stop.clear()
        self.monitor_thread = threading.Thread(target=self._monitor_worker, daemon=True)
        self.monitor_thread.start()
        self.log("[감시] 자동 감시를 시작했습니다.")

    def _monitor_worker(self) -> None:
        while not self.monitor_stop.is_set():
            try:
                results = process_new_posts_once(
                    sources=self._subscription_sources(),
                    api_key=self.api_key_entry.get().strip(),
                    style=self.style_var.get(),
                    target_length=self.length_entry.get().strip(),
                    article_prompt=self.settings.get("article_prompt", DEFAULT_ARTICLE_PROMPT),
                    publish_type="예약 발행",
                    pexels_key=self.pexels_key_entry.get().strip(),
                    pixabay_key=self.pixabay_key_entry.get().strip(),
                    auto_download_images=self.auto_download_images_var.get(),
                    auto_publish=self.auto_publish_var.get(),
                    naver_blog_id=self.naver_blog_id_entry.get().strip(),
                    naver_id=self.naver_id_entry.get().strip(),
                    naver_password=self.naver_pw_entry.get().strip(),
                    manual_login=self.manual_login_var.get(),
                    log=self.log,
                )
                self.log(f"[감시] 처리 완료: {len(results)}개")
                self.after(0, self.refresh_history)
            except Exception as exc:
                self.log(f"[오류] 감시 처리 실패: {exc}")
            interval = self._monitor_interval()
            self.log(f"[감시] 다음 확인까지 {interval}시간 대기")
            self.monitor_stop.wait(interval * 3600)

    def stop_monitor(self) -> None:
        self.monitor_stop.set()
        self.log("[감시] 중지 요청")

    def start_manual_crawl(self) -> None:
        threading.Thread(target=self._manual_crawl_worker, daemon=True).start()

    def _manual_crawl_worker(self) -> None:
        try:
            articles, _ = self._collect_manual_articles()
            self.after(0, self._show_manual_result, self._format_articles(articles))
        except Exception as exc:
            self.log(f"[오류] 수동 크롤링 실패: {exc}")

    def start_manual_generate(self) -> None:
        threading.Thread(target=self._manual_generate_worker, daemon=True).start()

    def _manual_generate_worker(self) -> None:
        try:
            articles, mode_name = self._collect_manual_articles()
            draft, _ = generate_blog_draft(
                articles=articles,
                api_key=self.api_key_entry.get().strip(),
                style=self.style_var.get(),
                target_length=self.length_entry.get().strip(),
                keyword=self.keyword_entry.get().strip(),
                mode_name=mode_name,
                article_prompt=self.settings.get("article_prompt", DEFAULT_ARTICLE_PROMPT),
                publish_type="임시 저장",
                log=self.log,
            )
            self.generated_text = draft
            self.after(0, self._show_manual_result, draft)
            self.after(0, self._show_draft, draft)
        except Exception as exc:
            self.log(f"[오류] 수동 생성 실패: {exc}")

    def _collect_manual_articles(self) -> tuple[list[Article], str]:
        if self.mode_var.get() == "url":
            urls = [line.strip() for line in self.url_text.get("1.0", "end").splitlines() if line.strip()]
            return fetch_articles(urls, log=self.log), "참고 링크 기반 작성"
        return collect_overseas_sources(self.keyword_entry.get().strip(), log=self.log), "키워드 해외 자료 검색 작성"

    def _format_articles(self, articles: list[Article]) -> str:
        if not articles:
            return "수집한 글이 없습니다."
        blocks = []
        for article in articles:
            blocks.append(f"제목: {article.title}\nURL: {article.url}\n글자 수: {len(article.text):,}자\n\n{article.text[:4000]}")
        return "\n\n---\n\n".join(blocks)

    def _show_draft(self, text: str) -> None:
        self.draft_text.delete("1.0", "end")
        self.draft_text.insert("1.0", text)
        self.tabs.select(self.work_tab)

    def _show_images(self, text: str) -> None:
        self.image_text.delete("1.0", "end")
        self.image_text.insert("1.0", text)

    def _show_manual_result(self, text: str) -> None:
        self.manual_result_text.delete("1.0", "end")
        self.manual_result_text.insert("1.0", text)

    def refresh_history(self) -> None:
        rows = recent_posts(80)
        lines = []
        for row in rows:
            lines.append(f"[{row.get('created_at')}] {row.get('status')} | {row.get('title')}\nURL: {row.get('post_url')}\n초안: {row.get('draft_path')}\n")
        self.history_text.delete("1.0", "end")
        self.history_text.insert("1.0", "\n".join(lines) or "처리 이력이 없습니다.")

    def save_as_txt(self) -> None:
        content = self.manual_result_text.get("1.0", "end").strip() or self.draft_text.get("1.0", "end").strip()
        if not content:
            messagebox.showwarning("저장 불가", "저장할 내용이 없습니다.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text", "*.txt")])
        if path:
            save_txt(path, content)
            self.log(f"[저장] txt 저장 완료: {path}")

    def save_as_docx(self) -> None:
        content = self.manual_result_text.get("1.0", "end").strip() or self.draft_text.get("1.0", "end").strip()
        if not content:
            messagebox.showwarning("저장 불가", "저장할 내용이 없습니다.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".docx", filetypes=[("Word", "*.docx")])
        if path:
            save_docx(path, content)
            self.log(f"[저장] docx 저장 완료: {path}")


if __name__ == "__main__":
    app = BlogDraftApp()
    app.mainloop()
