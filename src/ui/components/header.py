"""
Header Bar Component with Search Controls, Inline Clear, Quick Topic Chips,
Language Switcher, Sorting, and Appearance Mode Selector.
"""

from typing import Callable, Optional
import customtkinter as ctk
from src.ui.theme import (
    SO_ORANGE, SO_ORANGE_HOVER,
    COLOR_BG_SIDEBAR, COLOR_BG_CARD, COLOR_BG_CARD_HOVER, COLOR_BG_CARD_ACTIVE,
    COLOR_BG_INPUT, COLOR_BORDER, COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_TEXT_MUTED,
    COLOR_BG_TAG, COLOR_BG_TAG_HOVER, COLOR_TEXT_TAG, FONT_FAMILY
)


class HeaderBar(ctk.CTkFrame):
    """
    Top application header containing:
    - Logo & App branding
    - Search query input with inline ✕ clear button & Ctrl+K hint
    - Language selector (Both, English, Russian)
    - Sort selector (Relevance, Votes, Newest, Activity)
    - Search button with loading animation state
    - Theme switcher (Dark, Light, System)
    - Quick topic chips row for fast exploration
    """

    POPULAR_TOPICS = [
        "python", "javascript", "react", "fastapi", "asyncio", "pandas", "docker", "c++", "rust"
    ]

    def __init__(
        self,
        master,
        on_search_callback: Callable[[str, str, str], None],
        on_theme_change_callback: Callable[[str], None],
        **kwargs
    ):
        super().__init__(
            master,
            fg_color=COLOR_BG_SIDEBAR,
            border_color=COLOR_BORDER,
            border_width=1,
            corner_radius=0,
            **kwargs
        )

        self.on_search = on_search_callback
        self.on_theme_change = on_theme_change_callback
        self.is_searching = False

        self.setup_ui()

    def setup_ui(self):
        # 1. Main Controls Row
        self.controls_row = ctk.CTkFrame(self, fg_color="transparent")
        self.controls_row.pack(fill="x", padx=16, pady=(10, 6))

        # Logo / Brand
        logo_frame = ctk.CTkFrame(self.controls_row, fg_color="transparent")
        logo_frame.pack(side="left", padx=(0, 14))

        logo_badge = ctk.CTkLabel(
            logo_frame,
            text="⚡ SO",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
            fg_color=SO_ORANGE,
            text_color="#ffffff",
            corner_radius=6,
            width=50,
            height=32
        )
        logo_badge.pack(side="left", padx=(0, 8))

        title_lbl = ctk.CTkLabel(
            logo_frame,
            text="Search Pro",
            font=ctk.CTkFont(family=FONT_FAMILY, size=15, weight="bold"),
            text_color=COLOR_TEXT_PRIMARY
        )
        title_lbl.pack(side="left")

        # Search Entry Container (with Entry & Clear button)
        self.entry_container = ctk.CTkFrame(
            self.controls_row,
            fg_color=COLOR_BG_INPUT,
            border_color=COLOR_BORDER,
            border_width=1,
            corner_radius=8,
            height=38
        )
        self.entry_container.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.entry_container.pack_propagate(False)

        search_icon = ctk.CTkLabel(
            self.entry_container,
            text="🔍",
            font=ctk.CTkFont(size=12),
            text_color=COLOR_TEXT_MUTED
        )
        search_icon.pack(side="left", padx=(10, 4))

        self.search_entry = ctk.CTkEntry(
            self.entry_container,
            placeholder_text="Search Stack Overflow questions, errors, libraries, code... (Ctrl+K)",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            fg_color="transparent",
            border_width=0,
            text_color=COLOR_TEXT_PRIMARY
        )
        self.search_entry.pack(side="left", fill="both", expand=True, padx=(0, 4))
        self.search_entry.bind("<Return>", lambda e: self.trigger_search())
        self.search_entry.bind("<KeyRelease>", self._on_key_release)

        # Clear button (✕)
        self.clear_btn = ctk.CTkButton(
            self.entry_container,
            text="✕",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
            width=24,
            height=24,
            corner_radius=12,
            fg_color="transparent",
            hover_color=COLOR_BG_CARD_HOVER,
            text_color=COLOR_TEXT_MUTED,
            command=self.clear_search
        )
        # Initially unmapped until text is present

        # Shortcut hint badge
        self.shortcut_badge = ctk.CTkLabel(
            self.entry_container,
            text=" Ctrl+K ",
            font=ctk.CTkFont(family=FONT_FAMILY, size=10),
            fg_color=COLOR_BG_CARD,
            text_color=COLOR_TEXT_MUTED,
            corner_radius=4
        )
        self.shortcut_badge.pack(side="right", padx=(0, 8))

        # Language Selector
        self.lang_menu = ctk.CTkOptionMenu(
            self.controls_row,
            values=["🌐 Both", "🇬🇧 English", "🇷🇺 Russian"],
            font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"),
            dropdown_font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            fg_color=COLOR_BG_CARD,
            button_color=COLOR_BG_CARD_ACTIVE,
            button_hover_color=COLOR_BG_CARD_HOVER,
            text_color=COLOR_TEXT_PRIMARY,
            dropdown_fg_color=COLOR_BG_CARD,
            dropdown_text_color=COLOR_TEXT_PRIMARY,
            corner_radius=8,
            width=120,
            height=38
        )
        self.lang_menu.set("🌐 Both")
        self.lang_menu.pack(side="left", padx=(0, 8))

        # Sort Selector
        self.sort_menu = ctk.CTkOptionMenu(
            self.controls_row,
            values=["⭐ Relevance", "▲ Votes", "🕒 Newest", "⚡ Activity"],
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            dropdown_font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            fg_color=COLOR_BG_CARD,
            button_color=COLOR_BG_CARD_ACTIVE,
            button_hover_color=COLOR_BG_CARD_HOVER,
            text_color=COLOR_TEXT_PRIMARY,
            dropdown_fg_color=COLOR_BG_CARD,
            dropdown_text_color=COLOR_TEXT_PRIMARY,
            corner_radius=8,
            width=120,
            height=38
        )
        self.sort_menu.set("⭐ Relevance")
        self.sort_menu.pack(side="left", padx=(0, 10))

        # Search Button
        self.search_btn = ctk.CTkButton(
            self.controls_row,
            text="Search",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
            fg_color=SO_ORANGE,
            hover_color=SO_ORANGE_HOVER,
            text_color="#ffffff",
            corner_radius=8,
            width=90,
            height=38,
            command=self.trigger_search
        )
        self.search_btn.pack(side="left", padx=(0, 12))

        # Theme Selector
        self.theme_menu = ctk.CTkOptionMenu(
            self.controls_row,
            values=["🌙 Dark", "☀️ Light", "💻 System"],
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            fg_color=COLOR_BG_CARD,
            button_color=COLOR_BG_CARD_ACTIVE,
            button_hover_color=COLOR_BG_CARD_HOVER,
            text_color=COLOR_TEXT_SECONDARY,
            dropdown_fg_color=COLOR_BG_CARD,
            dropdown_text_color=COLOR_TEXT_PRIMARY,
            corner_radius=8,
            width=100,
            height=38,
            command=self.on_theme_selected
        )
        self.theme_menu.set("🌙 Dark")
        self.theme_menu.pack(side="right")

        # 2. Quick Topics Row
        self.topics_row = ctk.CTkFrame(self, fg_color="transparent")
        self.topics_row.pack(fill="x", padx=16, pady=(0, 8))

        lbl_quick = ctk.CTkLabel(
            self.topics_row,
            text="⚡ Quick Search:",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
            text_color=COLOR_TEXT_MUTED
        )
        lbl_quick.pack(side="left", padx=(0, 8))

        for topic in self.POPULAR_TOPICS:
            btn = ctk.CTkButton(
                self.topics_row,
                text=topic,
                font=ctk.CTkFont(family=FONT_FAMILY, size=10, weight="bold"),
                height=22,
                width=20,
                corner_radius=5,
                fg_color=COLOR_BG_TAG,
                hover_color=COLOR_BG_TAG_HOVER,
                text_color=COLOR_TEXT_TAG,
                command=lambda t=topic: self.quick_search(t)
            )
            btn.pack(side="left", padx=(0, 6))

    def _on_key_release(self, event=None):
        text = self.search_entry.get()
        if text:
            if not self.clear_btn.winfo_ismapped():
                self.shortcut_badge.pack_forget()
                self.clear_btn.pack(side="right", padx=(0, 6))
        else:
            if self.clear_btn.winfo_ismapped():
                self.clear_btn.pack_forget()
                self.shortcut_badge.pack(side="right", padx=(0, 8))

    def clear_search(self):
        """Clear search entry content and re-focus."""
        self.search_entry.delete(0, "end")
        self._on_key_release()
        self.search_entry.focus_set()

    def quick_search(self, topic: str):
        """Perform search with quick topic chip."""
        self.search_entry.delete(0, "end")
        self.search_entry.insert(0, topic)
        self._on_key_release()
        self.trigger_search()

    def focus_search(self):
        """Focus search entry and select all text."""
        self.search_entry.focus_set()
        self.search_entry.select_range(0, "end")

    def set_searching(self, is_searching: bool):
        """Toggle search button busy/active state."""
        self.is_searching = is_searching
        if is_searching:
            self.search_btn.configure(
                text="⏳ Searching...",
                state="disabled"
            )
        else:
            self.search_btn.configure(
                text="Search",
                state="normal"
            )

    def trigger_search(self):
        """Extract inputs and call search callback."""
        if self.is_searching:
            return

        query = self.search_entry.get().strip()
        lang_val = self.lang_menu.get()

        if "English" in lang_val:
            lang = "English"
        elif "Russian" in lang_val:
            lang = "Russian"
        else:
            lang = "Both"

        sort_raw = self.sort_menu.get()
        if "Vote" in sort_raw:
            sort = "votes"
        elif "New" in sort_raw:
            sort = "creation"
        elif "Activ" in sort_raw:
            sort = "activity"
        else:
            sort = "relevance"

        self.on_search(query, lang, sort)

    def on_theme_selected(self, theme_val: str):
        """Handle theme change."""
        if "Dark" in theme_val:
            mode = "dark"
        elif "Light" in theme_val:
            mode = "light"
        else:
            mode = "system"
        self.on_theme_change(mode)
