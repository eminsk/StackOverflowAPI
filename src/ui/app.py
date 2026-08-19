"""
Main Application Window for Stack Overflow Search Pro
CustomTkinter-powered modern, responsive, and lightweight desktop client.
"""

import os
import sys
import time
import threading
from typing import Dict, Any, List, Optional
import customtkinter as ctk

from src.api.stackoverflow import StackOverflowAPI
from src.ui.theme import (
    SO_ORANGE, SO_ORANGE_HOVER, COLOR_SUCCESS, COLOR_PRIMARY,
    COLOR_BG_SIDEBAR, COLOR_BG_CARD, COLOR_BORDER,
    COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_TEXT_MUTED
)
from src.ui.components.header import HeaderBar
from src.ui.components.question_card import QuestionCard
from src.ui.components.details_view import QuestionDetailsView


class StackOverflowApp(ctk.CTk):
    """
    Main Application Window:
    - Top Header Bar with search controls
    - Split Layout: Left master questions list with language tabs, Right details pane
    - Bottom Status Bar
    - Asynchronous thread-safe API operations
    """

    def __init__(self):
        super().__init__()

        # Window Configuration
        self.title("Stack Overflow Search Pro")
        self.geometry("1380x880")
        self.minsize(1100, 720)

        # Default Appearance
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        # Load Icons
        self.setup_window_icon()

        # API & State
        self.api = StackOverflowAPI()
        self.search_results = {"English": [], "Russian": []}
        self.question_cache = {"English": {}, "Russian": {}}
        self.answers_cache = {}
        self.selected_question_id = None
        self.selected_language = "English"
        self.active_card_widget = None

        # Search Query State
        self.current_query = ""
        self.active_search_threads = []

        # Build Interface
        self.setup_ui()

        # Center on screen
        self.center_window()

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
        self.main_container.pack(fill="both", expand=True, padx=12, pady=(8, 4))

        # Configure Grid layout: Column 0 = Left List (width 480), Column 1 = Right Details (expand)
        self.main_container.grid_columnconfigure(0, weight=0, minsize=460)
        self.main_container.grid_columnconfigure(1, weight=1)
        self.main_container.grid_rowconfigure(0, weight=1)

        # --- LEFT PANEL: Results List ---
        self.left_panel = ctk.CTkFrame(
            self.main_container,
            fg_color="transparent",
            width=480
        )
        self.left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 6), pady=0)
        self.left_panel.grid_propagate(False)

        # Tabview for English / Russian
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
        self.tabs.set("🇬🇧 English")

        # English Scrollable List
        self.list_en = ctk.CTkScrollableFrame(
            self.tab_en,
            fg_color="transparent",
            corner_radius=0
        )
        self.list_en.pack(fill="both", expand=True, padx=2, pady=2)

        # Russian Scrollable List
        self.list_ru = ctk.CTkScrollableFrame(
            self.tab_ru,
            fg_color="transparent",
            corner_radius=0
        )
        self.list_ru.pack(fill="both", expand=True, padx=2, pady=2)

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
            height=28,
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
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=COLOR_TEXT_SECONDARY
        )
        self.status_label.pack(side="left", padx=14)

        self.status_right = ctk.CTkLabel(
            self.status_bar,
            text="🟢 Connected | v2.0 (CustomTkinter)",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=COLOR_TEXT_MUTED
        )
        self.status_right.pack(side="right", padx=14)

    def show_empty_list_state(self, scrollable_frame, lang_name: str):
        """Show initial helpful state in results list."""
        for child in scrollable_frame.winfo_children():
            child.destroy()

        card = ctk.CTkFrame(
            scrollable_frame,
            fg_color=COLOR_BG_CARD,
            border_color=COLOR_BORDER,
            border_width=1,
            corner_radius=10
        )
        card.pack(fill="x", padx=10, pady=20)

        lbl_icon = ctk.CTkLabel(card, text="🔍", font=ctk.CTkFont(size=28))
        lbl_icon.pack(pady=(16, 4))

        lbl_text = ctk.CTkLabel(
            card,
            text=f"No results yet for {lang_name}\nType a query above and hit Search",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=COLOR_TEXT_SECONDARY,
            justify="center"
        )
        lbl_text.pack(pady=(0, 16))

    def update_status(self, message: str, is_error: bool = False):
        """Thread-safe status bar update."""
        def _update():
            color = "#ef4444" if is_error else COLOR_TEXT_SECONDARY
            self.status_label.configure(text=message, text_color=color)
        self.after(0, _update)

    def on_theme_changed(self, mode: str):
        """Switch appearance mode (Dark, Light, System)."""
        target_mode = "Dark" if mode == "dark" else ("Light" if mode == "light" else "System")
        ctk.set_appearance_mode(target_mode)

        # Re-render active details view so Pygments code blocks and embedded text update colors
        if self.selected_question_id:
            self.details_view.refresh_view()

        self.update_status(f"Theme switched to {target_mode} mode.")

    def on_search_requested(self, query: str, language: str, sort: str):
        """Initiate search across selected languages asynchronously."""
        if not query:
            self.update_status("⚠️ Please enter a search query.", is_error=True)
            return

        self.current_query = query
        self.update_status(f"🔍 Searching for '{query}'...")

        # Clear existing lists
        for child in self.list_en.winfo_children():
            child.destroy()
        for child in self.list_ru.winfo_children():
            child.destroy()

        # Show searching spinner in lists
        self.show_searching_placeholder(self.list_en, "English")
        self.show_searching_placeholder(self.list_ru, "Russian")

        # Determine which languages to query
        targets = ["English", "Russian"] if language == "Both" else [language]

        start_time = time.time()

        for lang in targets:
            thread = threading.Thread(
                target=self._search_worker,
                args=(query, lang, sort, start_time),
                daemon=True
            )
            thread.start()

    def show_searching_placeholder(self, parent, lang: str):
        """Display animated/loading card in results column."""
        card = ctk.CTkFrame(
            parent,
            fg_color=COLOR_BG_CARD,
            border_color=COLOR_BORDER,
            border_width=1,
            corner_radius=10
        )
        card.pack(fill="x", padx=10, pady=20)

        lbl = ctk.CTkLabel(
            card,
            text=f"⏳ Fetching {lang} questions...",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=SO_ORANGE
        )
        lbl.pack(pady=20)

    def _search_worker(self, query: str, language: str, sort: str, start_time: float):
        """Worker running in background thread for search."""
        response = self.api.search_questions(query, language=language, sort=sort, pagesize=25)
        elapsed = time.time() - start_time
        # Safe UI callback
        self.after(0, self._handle_search_response, response, language, query, elapsed)

    def _handle_search_response(self, response: Dict[str, Any], language: str, query: str, elapsed: float):
        """Handle search API response on main thread."""
        if query != self.current_query:
            return  # Outdated search result, discard

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

        # Cache questions
        self.question_cache[language] = {q.get("question_id"): q for q in items}

        if not items:
            self.show_no_results_in_list(scroll_frame, query, language)
            self.update_status(f"No results found for '{query}' in {language}.")
            return

        # Render Question Cards
        for q_data in items:
            card = QuestionCard(
                scroll_frame,
                question_data=q_data,
                on_click_callback=lambda q_id, l=language: self.on_question_selected(q_id, l)
            )
            card.pack(fill="x", padx=6, pady=4)

        # Switch to the tab with results if single language or non-empty
        if language == "English":
            self.tabs.set("🇬🇧 English")

        self.update_status(f"✅ Found {len(items)} {language} results in {elapsed:.2f}s for '{query}'")

    def show_no_results_in_list(self, parent, query: str, lang: str):
        """Show clean no-results card."""
        card = ctk.CTkFrame(
            parent,
            fg_color=COLOR_BG_CARD,
            border_color=COLOR_BORDER,
            border_width=1,
            corner_radius=10
        )
        card.pack(fill="x", padx=10, pady=20)

        lbl_icon = ctk.CTkLabel(card, text="🔍", font=ctk.CTkFont(size=28))
        lbl_icon.pack(pady=(16, 4))

        lbl_text = ctk.CTkLabel(
            card,
            text=f"No results found for:\n'{query}'\nin {lang} Stack Overflow",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=COLOR_TEXT_SECONDARY,
            justify="center"
        )
        lbl_text.pack(pady=(0, 16))

    def show_error_in_list(self, parent, error: str):
        """Show error card in results column."""
        card = ctk.CTkFrame(
            parent,
            fg_color=COLOR_BG_CARD,
            border_color="#ef4444",
            border_width=1,
            corner_radius=10
        )
        card.pack(fill="x", padx=10, pady=20)

        lbl = ctk.CTkLabel(
            card,
            text=f"⚠️ {error}",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="#ef4444",
            wraplength=380
        )
        lbl.pack(pady=16, padx=12)

    def on_question_selected(self, question_id: int, language: str):
        """Handle selection of a question card from the list."""
        self.selected_question_id = question_id
        self.selected_language = language

        question_data = self.question_cache[language].get(question_id)
        if not question_data:
            return

        self.update_status(f"Loading details for question #{question_id}...")

        # Render Question in details view
        self.details_view.load_question(question_data, language)

        # Check answers cache
        cache_key = f"{language}_{question_id}"
        if cache_key in self.answers_cache:
            self.details_view.display_answers(self.answers_cache[cache_key])
            self.update_status(f"Loaded question #{question_id} (from cache)")
        else:
            # Fetch answers asynchronously
            thread = threading.Thread(
                target=self._answers_worker,
                args=(question_id, language),
                daemon=True
            )
            thread.start()

    def _answers_worker(self, question_id: int, language: str):
        """Fetch answers in background thread."""
        response = self.api.get_question_answers(question_id, language=language)
        self.after(0, self._handle_answers_response, response, question_id, language)

    def _handle_answers_response(self, response: Dict[str, Any], question_id: int, language: str):
        """Display answers on main thread."""
        if question_id != self.selected_question_id or language != self.selected_language:
            return  # Selection changed, ignore

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
        self.after(0, self._handle_comments_response, comments, item_id, language, item_type)

    def _handle_comments_response(self, comments: List[Dict[str, Any]], item_id: int, language: str, item_type: str):
        """Deliver fetched comments to details view."""
        self.details_view.set_comments(item_id, language, item_type, comments)
        self.update_status(f"Loaded {len(comments)} comments for {item_type} #{item_id}")
