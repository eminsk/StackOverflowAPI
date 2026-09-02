"""
Main Application Window for Stack Overflow Search Pro
CustomTkinter-powered modern, responsive, ergonomic, and lightweight desktop client.
"""

import os
import sys
import time
import queue
import threading
from typing import Dict, Any, List, Optional
import customtkinter as ctk

from src.api.stackoverflow import StackOverflowAPI
from src.utils.bookmarks import BookmarkManager
from src.ui.theme import (
    SO_ORANGE, SO_ORANGE_HOVER, COLOR_SUCCESS, COLOR_PRIMARY, COLOR_BOOKMARK,
    COLOR_BG_SIDEBAR, COLOR_BG_CARD, COLOR_BG_CARD_ACTIVE, COLOR_BG_CARD_HOVER,
    COLOR_BORDER, COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_TEXT_MUTED,
    FONT_FAMILY
)
from src.ui.components.header import HeaderBar
from src.ui.components.question_card import QuestionCard
from src.ui.components.details_view import QuestionDetailsView


class StackOverflowApp(ctk.CTk):
    """
    Main Application Window:
    - Top Header Bar with search controls, inline clear, quick topics, theme switcher
    - Split Layout: Left master list with English / Russian / Bookmarks tabs, Right details pane
    - Client-side real-time results filter
    - Active question card highlighting
    - Pagination ("Load More Results")
    - Local persistent bookmarks storage with offline viewing
    - Bottom Status Bar with API quota tracking and health indicator
    - Thread-safe queue architecture for crash-proof asynchronous background operations
    - Global keyboard shortcuts
    """

    def __init__(self):
        super().__init__()

        # Window Configuration
        self.title("Stack Overflow Search Pro")
        self.geometry("1420x900")
        self.minsize(1120, 740)

        # Thread-safe UI queue
        self.ui_queue = queue.Queue()
        self._poll_job = None
        self._poll_ui_queue()

        # Default Appearance
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        # Load Icons
        self.setup_window_icon()

        # API & State
        self.api = StackOverflowAPI()
        self.bookmark_mgr = BookmarkManager()

        self.search_results = {"English": [], "Russian": []}
        self.question_cache = {"English": {}, "Russian": {}}
        self.answers_cache = {}

        self.current_page = {"English": 1, "Russian": 1}
        self.has_more = {"English": False, "Russian": False}
        self.is_loading_more = {"English": False, "Russian": False}

        self.selected_question_id: Optional[int] = None
        self.selected_language: str = "English"
        self.active_card_widget: Optional[QuestionCard] = None

        self.current_query = ""
        self.current_sort = "relevance"
        self.pending_searches = 0

        # Build Interface
        self.setup_ui()

        # Keyboard shortcuts
        self.setup_shortcuts()

        # Listen to bookmark changes
        self.bookmark_mgr.add_listener(self.on_bookmarks_changed)
        self.render_bookmarks()

        # Center on screen
        self.center_window()

    def _poll_ui_queue(self):
        """Process tasks queued from background threads safely on main thread."""
        if not self.winfo_exists():
            return
        try:
            while not self.ui_queue.empty():
                callback, args = self.ui_queue.get_nowait()
                try:
                    callback(*args)
                except Exception as e:
                    print(f"Error in UI queue callback: {e}")
        except Exception:
            pass
        finally:
            if self.winfo_exists():
                self._poll_job = self.after(25, self._poll_ui_queue)

    def run_on_ui_thread(self, callback, *args):
        """Thread-safe queue dispatch to execute callback on main GUI thread."""
        self.ui_queue.put((callback, args))

    def destroy(self):
        """Clean teardown of window and timers."""
        if self._poll_job:
            try:
                self.after_cancel(self._poll_job)
                self._poll_job = None
            except Exception:
                pass
        super().destroy()

    def setup_window_icon(self):
        """Set application icon if icon.ico or icon.png exists."""
        try:
            if os.path.exists("icon.ico"):
                self.iconbitmap("icon.ico")
            elif os.path.exists("icon.png"):
                from PIL import Image, ImageTk
                img = Image.open("icon.png")
                photo = ImageTk.PhotoImage(img)
                self.wm_iconphoto(True, photo)
        except Exception as e:
            print(f"Icon setup note: {e}")

    def center_window(self):
        """Center the main window on the primary screen."""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def setup_shortcuts(self):
        """Bind ergonomic global keyboard shortcuts."""
        self.bind_all("<Control-k>", lambda e: self.header.focus_search())
        self.bind_all("<Control-K>", lambda e: self.header.focus_search())
        self.bind_all("<Control-f>", lambda e: self.header.focus_search())
        self.bind_all("<Control-F>", lambda e: self.header.focus_search())
        self.bind_all("<Escape>", lambda e: self.on_escape())
        self.bind_all("<Control-b>", lambda e: self.toggle_current_bookmark())
        self.bind_all("<Control-B>", lambda e: self.toggle_current_bookmark())
        self.bind_all("<F5>", lambda e: self.reload_current_question())

    def on_escape(self):
        """Handle Escape key: clear focus."""
        self.focus_set()

    def toggle_current_bookmark(self):
        """Toggle bookmark on currently open question via shortcut."""
        if self.selected_question_id and self.details_view.current_question:
            self.details_view.toggle_bookmark(self.details_view.current_question, self.selected_language)

    def reload_current_question(self):
        """Reload currently selected question and its answers."""
        if self.selected_question_id:
            self.on_question_selected(self.selected_question_id, self.selected_language)

    def setup_ui(self):
        """Construct the full application layout."""
        # 1. Header Bar
        self.header = HeaderBar(
            self,
            on_search_callback=self.on_search_requested,
            on_theme_change_callback=self.on_theme_changed
        )
        self.header.pack(fill="x", side="top")

        # 2. Main Content Split View
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=12, pady=(6, 4))

        self.main_container.grid_columnconfigure(0, weight=0, minsize=480)
        self.main_container.grid_columnconfigure(1, weight=1)
        self.main_container.grid_rowconfigure(0, weight=1)

        # --- LEFT PANEL: Results List ---
        self.left_panel = ctk.CTkFrame(
            self.main_container,
            fg_color="transparent",
            width=500
        )
        self.left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 6), pady=0)
        self.left_panel.grid_propagate(False)

        # Quick Results Filter Bar
        self.filter_frame = ctk.CTkFrame(self.left_panel, fg_color="transparent", height=32)
        self.filter_frame.pack(fill="x", pady=(0, 6))

        self.filter_entry = ctk.CTkEntry(
            self.filter_frame,
            placeholder_text="⚡ Filter loaded results (by title or tag)...",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            fg_color=COLOR_BG_CARD,
            border_color=COLOR_BORDER,
            border_width=1,
            corner_radius=6,
            height=28
        )
        self.filter_entry.pack(fill="x", side="left", expand=True)
        self.filter_entry.bind("<KeyRelease>", self.on_filter_changed)

        # Tabview for English / Russian / Bookmarks
        self.tabs = ctk.CTkTabview(
            self.left_panel,
            fg_color=COLOR_BG_SIDEBAR,
            segmented_button_fg_color=COLOR_BG_CARD,
            segmented_button_selected_color=SO_ORANGE,
            segmented_button_selected_hover_color=SO_ORANGE_HOVER,
            segmented_button_unselected_color=COLOR_BG_CARD,
            segmented_button_unselected_hover_color=COLOR_BG_SIDEBAR,
            text_color=COLOR_TEXT_PRIMARY,
            corner_radius=10
        )
        self.tabs.pack(fill="both", expand=True)

        self.tab_en = self.tabs.add("🇬🇧 English")
        self.tab_ru = self.tabs.add("🇷🇺 Russian")
        self.tab_bm = self.tabs.add("⭐ Bookmarks")
        self.tabs.set("🇬🇧 English")

        # English Scrollable List
        self.list_en = ctk.CTkScrollableFrame(self.tab_en, fg_color="transparent", corner_radius=0)
        self.list_en.pack(fill="both", expand=True, padx=2, pady=2)

        # Russian Scrollable List
        self.list_ru = ctk.CTkScrollableFrame(self.tab_ru, fg_color="transparent", corner_radius=0)
        self.list_ru.pack(fill="both", expand=True, padx=2, pady=2)

        # Bookmarks Scrollable List
        self.list_bm = ctk.CTkScrollableFrame(self.tab_bm, fg_color="transparent", corner_radius=0)
        self.list_bm.pack(fill="both", expand=True, padx=2, pady=2)

        self.show_empty_list_state(self.list_en, "English")
        self.show_empty_list_state(self.list_ru, "Russian")

        # --- RIGHT PANEL: Details View ---
        self.details_view = QuestionDetailsView(
            self.main_container,
            on_fetch_comments_callback=self.fetch_comments_async,
            corner_radius=10
        )
        self.details_view.grid(row=0, column=1, sticky="nsew", padx=(6, 0), pady=0)

        # 3. Bottom Status Bar
        self.status_bar = ctk.CTkFrame(
            self,
            height=30,
            fg_color=COLOR_BG_SIDEBAR,
            border_color=COLOR_BORDER,
            border_width=1,
            corner_radius=0
        )
        self.status_bar.pack(fill="x", side="bottom")
        self.status_bar.pack_propagate(False)

        self.status_label = ctk.CTkLabel(
            self.status_bar,
            text="Ready to search Stack Overflow",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            text_color=COLOR_TEXT_SECONDARY
        )
        self.status_label.pack(side="left", padx=14)

        self.status_right = ctk.CTkLabel(
            self.status_bar,
            text="⚡ API Quota: Active | 🟢 Connected | v2.1",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            text_color=COLOR_TEXT_MUTED
        )
        self.status_right.pack(side="right", padx=14)

    def update_tab_label(self, tab_id: str, label_text: str):
        """Update tab text title safely."""
        try:
            if hasattr(self.tabs, "_segmented_button") and tab_id in self.tabs._segmented_button._buttons_dict:
                self.tabs._segmented_button._buttons_dict[tab_id].configure(text=label_text)
        except Exception:
            pass

    def show_empty_list_state(self, scrollable_frame, lang_name: str):
        """Show helpful empty state in results column."""
        for child in scrollable_frame.winfo_children():
            child.destroy()

        card = ctk.CTkFrame(
            scrollable_frame,
            fg_color=COLOR_BG_CARD,
            border_color=COLOR_BORDER,
            border_width=1,
            corner_radius=10
        )
        card.pack(fill="x", padx=10, pady=24)

        lbl_icon = ctk.CTkLabel(card, text="🔍", font=ctk.CTkFont(size=30))
        lbl_icon.pack(pady=(20, 6))

        lbl_text = ctk.CTkLabel(
            card,
            text=f"No results yet for {lang_name}\nType a query above or click a quick search topic chip",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            text_color=COLOR_TEXT_SECONDARY,
            justify="center"
        )
        lbl_text.pack(pady=(0, 20))

    def update_status(self, message: str, is_error: bool = False):
        """Thread-safe status bar update with quota reporting."""
        def _update():
            color = "#ef4444" if is_error else COLOR_TEXT_SECONDARY
            self.status_label.configure(text=message, text_color=color)

            if self.api.last_quota_remaining is not None:
                max_str = f"/{self.api.last_quota_max}" if self.api.last_quota_max else ""
                self.status_right.configure(
                    text=f"⚡ API Quota: {self.api.last_quota_remaining}{max_str} | 🟢 Connected | v2.1"
                )
        self.run_on_ui_thread(_update)

    def on_theme_changed(self, mode: str):
        """Switch appearance mode (Dark, Light, System)."""
        target_mode = "Dark" if mode == "dark" else ("Light" if mode == "light" else "System")
        ctk.set_appearance_mode(target_mode)

        if self.selected_question_id:
            self.details_view.refresh_view()

        self.update_status(f"Theme switched to {target_mode} mode.")

    def on_search_requested(self, query: str, language: str, sort: str):
        """Initiate search across selected languages asynchronously."""
        if not query:
            self.update_status("⚠️ Please enter a search query.", is_error=True)
            return

        self.current_query = query
        self.current_sort = sort
        self.header.set_searching(True)
        self.update_status(f"🔍 Searching for '{query}'...")

        # Clear existing lists
        for child in self.list_en.winfo_children():
            child.destroy()
        for child in self.list_ru.winfo_children():
            child.destroy()

        self.show_searching_placeholder(self.list_en, "English")
        self.show_searching_placeholder(self.list_ru, "Russian")

        targets = ["English", "Russian"] if language == "Both" else [language]
        self.pending_searches = len(targets)
        start_time = time.time()

        for lang in targets:
            self.current_page[lang] = 1
            thread = threading.Thread(
                target=self._search_worker,
                args=(query, lang, sort, 1, start_time),
                daemon=True
            )
            thread.start()

    def show_searching_placeholder(self, parent, lang: str):
        """Display loading indicator card in results column."""
        card = ctk.CTkFrame(
            parent,
            fg_color=COLOR_BG_CARD,
            border_color=COLOR_BORDER,
            border_width=1,
            corner_radius=10
        )
        card.pack(fill="x", padx=10, pady=24)

        lbl = ctk.CTkLabel(
            card,
            text=f"⏳ Fetching {lang} questions...",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
            text_color=SO_ORANGE
        )
        lbl.pack(pady=22)

    def _search_worker(self, query: str, language: str, sort: str, page: int, start_time: float):
        """Worker running in background thread for search."""
        response = self.api.search_questions(query, language=language, sort=sort, page=page, pagesize=25)
        elapsed = time.time() - start_time
        self.run_on_ui_thread(self._handle_search_response, response, language, query, elapsed, page)

    def _handle_search_response(self, response: Dict[str, Any], language: str, query: str, elapsed: float, page: int):
        """Handle search API response on main thread."""
        self.pending_searches = max(0, self.pending_searches - 1)
        if self.pending_searches == 0:
            self.header.set_searching(False)

        if query != self.current_query:
            return

        scroll_frame = self.list_en if language == "English" else self.list_ru

        for child in scroll_frame.winfo_children():
            child.destroy()

        if "error" in response and not response.get("items"):
            err_msg = response.get("error", "Unknown error")
            self.show_error_in_list(scroll_frame, err_msg)
            self.update_status(f"❌ Error fetching {language} results: {err_msg}", is_error=True)
            return

        items = response.get("items", [])
        self.search_results[language] = items
        self.question_cache[language] = {q.get("question_id"): q for q in items}

        self.has_more[language] = response.get("has_more", False)
        self.current_page[language] = page

        # Update dynamic tab title
        tab_key = "🇬🇧 English" if language == "English" else "🇷🇺 Russian"
        self.update_tab_label(tab_key, f"{tab_key} ({len(items)})")

        if not items:
            self.show_no_results_in_list(scroll_frame, query, language)
            self.update_status(f"No results found for '{query}' in {language}.")
            return

        # Render Question Cards
        for q_data in items:
            card = QuestionCard(
                scroll_frame,
                question_data=q_data,
                on_click_callback=lambda q_id, c, l=language: self.on_question_selected(q_id, l, c)
            )
            card.pack(fill="x", padx=6, pady=4)

        if self.has_more[language]:
            self.render_load_more_button(scroll_frame, language)

        if language == "English":
            self.tabs.set("🇬🇧 English")

        self.update_status(f"✅ Found {len(items)} {language} results in {elapsed:.2f}s for '{query}'")

    def render_load_more_button(self, parent, language: str):
        """Append sleek Load More button at bottom of results list."""
        btn_frame = ctk.CTkFrame(parent, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=10)

        load_more_btn = ctk.CTkButton(
            btn_frame,
            text=f"⬇ Load More {language} Questions (+25)",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"),
            height=32,
            corner_radius=8,
            fg_color=COLOR_BG_CARD,
            hover_color=COLOR_BG_CARD_HOVER,
            border_color=COLOR_BORDER,
            border_width=1,
            text_color=COLOR_TEXT_PRIMARY,
            command=lambda btn=btn_frame, l=language: self.load_more_results(l, btn)
        )
        load_more_btn.pack(fill="x")

    def load_more_results(self, language: str, button_frame: ctk.CTkFrame):
        """Fetch next page of results for pagination."""
        if self.is_loading_more[language] or not self.has_more[language]:
            return

        self.is_loading_more[language] = True
        button_frame.destroy()

        scroll_frame = self.list_en if language == "English" else self.list_ru

        loading_lbl = ctk.CTkLabel(
            scroll_frame,
            text="⏳ Loading more questions...",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
            text_color=SO_ORANGE
        )
        loading_lbl.pack(pady=8)

        next_page = self.current_page[language] + 1
        thread = threading.Thread(
            target=self._load_more_worker,
            args=(self.current_query, language, self.current_sort, next_page, loading_lbl),
            daemon=True
        )
        thread.start()

    def _load_more_worker(self, query: str, language: str, sort: str, page: int, loading_lbl: ctk.CTkLabel):
        response = self.api.search_questions(query, language=language, sort=sort, page=page, pagesize=25)
        self.run_on_ui_thread(self._handle_load_more_response, response, language, page, loading_lbl)

    def _handle_load_more_response(self, response: Dict[str, Any], language: str, page: int, loading_lbl: ctk.CTkLabel):
        self.is_loading_more[language] = False
        try:
            loading_lbl.destroy()
        except Exception:
            pass

        scroll_frame = self.list_en if language == "English" else self.list_ru
        new_items = response.get("items", [])

        if not new_items:
            self.has_more[language] = False
            return

        self.search_results[language].extend(new_items)
        for q in new_items:
            self.question_cache[language][q.get("question_id")] = q

        self.current_page[language] = page
        self.has_more[language] = response.get("has_more", False)

        tab_key = "🇬🇧 English" if language == "English" else "🇷🇺 Russian"
        total_items = len(self.search_results[language])
        self.update_tab_label(tab_key, f"{tab_key} ({total_items})")

        for q_data in new_items:
            card = QuestionCard(
                scroll_frame,
                question_data=q_data,
                on_click_callback=lambda q_id, c, l=language: self.on_question_selected(q_id, l, c)
            )
            card.pack(fill="x", padx=6, pady=4)

        if self.has_more[language]:
            self.render_load_more_button(scroll_frame, language)

        self.update_status(f"✅ Loaded {len(new_items)} more {language} questions (Page {page})")

    def show_no_results_in_list(self, parent, query: str, lang: str):
        card = ctk.CTkFrame(
            parent,
            fg_color=COLOR_BG_CARD,
            border_color=COLOR_BORDER,
            border_width=1,
            corner_radius=10
        )
        card.pack(fill="x", padx=10, pady=24)

        lbl_icon = ctk.CTkLabel(card, text="🔍", font=ctk.CTkFont(size=30))
        lbl_icon.pack(pady=(18, 4))

        lbl_text = ctk.CTkLabel(
            card,
            text=f"No results found for:\n'{query}'\nin {lang} Stack Overflow",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            text_color=COLOR_TEXT_SECONDARY,
            justify="center"
        )
        lbl_text.pack(pady=(0, 18))

    def show_error_in_list(self, parent, error: str):
        card = ctk.CTkFrame(
            parent,
            fg_color=COLOR_BG_CARD,
            border_color="#ef4444",
            border_width=1,
            corner_radius=10
        )
        card.pack(fill="x", padx=10, pady=24)

        lbl = ctk.CTkLabel(
            card,
            text=f"⚠️ {error}",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            text_color="#ef4444",
            wraplength=400
        )
        lbl.pack(pady=18, padx=14)

    def on_filter_changed(self, event=None):
        """Real-time filter cards in currently visible list tab."""
        filter_text = self.filter_entry.get().strip().lower()
        current_tab = self.tabs.get()

        if "English" in current_tab:
            scroll_frame = self.list_en
        elif "Russian" in current_tab:
            scroll_frame = self.list_ru
        else:
            scroll_frame = self.list_bm

        for child in scroll_frame.winfo_children():
            if isinstance(child, QuestionCard):
                q = child.question_data
                title = q.get("title", "").lower()
                tags = " ".join(q.get("tags", [])).lower()
                if not filter_text or filter_text in title or filter_text in tags:
                    child.pack(fill="x", padx=6, pady=4)
                else:
                    child.pack_forget()

    def on_question_selected(self, question_id: int, language: str, card_widget: Optional[QuestionCard] = None):
        """Handle selection of a question card with active visual highlight."""
        if self.active_card_widget and self.active_card_widget != card_widget:
            try:
                self.active_card_widget.set_selected(False)
            except Exception:
                pass

        if card_widget:
            card_widget.set_selected(True)
            self.active_card_widget = card_widget

        self.selected_question_id = question_id
        self.selected_language = language

        question_data = None
        if language in self.question_cache and question_id in self.question_cache[language]:
            question_data = self.question_cache[language][question_id]
        else:
            bm = self.bookmark_mgr.get_bookmark(question_id)
            if bm:
                question_data = bm

        if not question_data:
            return

        self.update_status(f"Loading details for question #{question_id}...")
        self.details_view.load_question(question_data, language)

        cache_key = f"{language}_{question_id}"
        if cache_key in self.answers_cache:
            self.details_view.display_answers(self.answers_cache[cache_key])
            self.update_status(f"Loaded question #{question_id} (from cache)")
        else:
            thread = threading.Thread(
                target=self._answers_worker,
                args=(question_id, language),
                daemon=True
            )
            thread.start()

    def _answers_worker(self, question_id: int, language: str):
        """Fetch answers in background thread."""
        response = self.api.get_question_answers(question_id, language=language)
        self.run_on_ui_thread(self._handle_answers_response, response, question_id, language)

    def _handle_answers_response(self, response: Dict[str, Any], question_id: int, language: str):
        """Display answers on main thread."""
        if question_id != self.selected_question_id or language != self.selected_language:
            return

        answers = response.get("items", [])
        cache_key = f"{language}_{question_id}"
        self.answers_cache[cache_key] = answers

        self.details_view.display_answers(answers)
        self.update_status(f"✅ Loaded question #{question_id} with {len(answers)} answers")

    def fetch_comments_async(self, item_id: int, language: str, item_type: str):
        """Asynchronously load comments for question or answer."""
        self.update_status(f"Loading comments for {item_type} #{item_id}...")
        thread = threading.Thread(
            target=self._comments_worker,
            args=(item_id, language, item_type),
            daemon=True
        )
        thread.start()

    def _comments_worker(self, item_id: int, language: str, item_type: str):
        if item_type == "question":
            response = self.api.get_question_comments(item_id, language=language)
        else:
            response = self.api.get_answer_comments(item_id, language=language)

        comments = response.get("items", [])
        self.run_on_ui_thread(self._handle_comments_response, comments, item_id, language, item_type)

    def _handle_comments_response(self, comments: List[Dict[str, Any]], item_id: int, language: str, item_type: str):
        self.details_view.set_comments(item_id, language, item_type, comments)
        self.update_status(f"Loaded {len(comments)} comments for {item_type} #{item_id}")

    def on_bookmarks_changed(self):
        """Callback invoked when bookmarks are added or removed."""
        self.run_on_ui_thread(self.render_bookmarks)

    def render_bookmarks(self):
        """Render all saved bookmarks in the Bookmarks tab."""
        for child in self.list_bm.winfo_children():
            child.destroy()

        bookmarks = self.bookmark_mgr.get_all_bookmarks()
        self.update_tab_label("⭐ Bookmarks", f"⭐ Bookmarks ({len(bookmarks)})")

        if not bookmarks:
            card = ctk.CTkFrame(
                self.list_bm,
                fg_color=COLOR_BG_CARD,
                border_color=COLOR_BORDER,
                border_width=1,
                corner_radius=10
            )
            card.pack(fill="x", padx=10, pady=24)

            lbl_icon = ctk.CTkLabel(card, text="⭐", font=ctk.CTkFont(size=30), text_color=COLOR_BOOKMARK)
            lbl_icon.pack(pady=(18, 4))

            lbl_text = ctk.CTkLabel(
                card,
                text="No bookmarked questions yet.\nClick '☆ Save' on any question to bookmark it for offline reference.",
                font=ctk.CTkFont(family=FONT_FAMILY, size=12),
                text_color=COLOR_TEXT_SECONDARY,
                justify="center"
            )
            lbl_text.pack(pady=(0, 18))
            return

        for bm in bookmarks:
            bm_lang = bm.get("_language", "English")
            card = QuestionCard(
                self.list_bm,
                question_data=bm,
                on_click_callback=lambda q_id, c, l=bm_lang: self.on_question_selected(q_id, l, c)
            )
            card.pack(fill="x", padx=6, pady=4)
