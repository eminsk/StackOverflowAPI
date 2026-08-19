"""
Header Bar Component with Search Controls, Language Switcher, Sorting, and Theme Mode Selector
"""

from typing import Callable
import customtkinter as ctk
from src.ui.theme import (
    SO_ORANGE, SO_ORANGE_HOVER,
    COLOR_BG_SIDEBAR, COLOR_BG_CARD, COLOR_BG_CARD_HOVER, COLOR_BG_CARD_ACTIVE,
    COLOR_BG_INPUT, COLOR_BORDER, COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY
)


class HeaderBar(ctk.CTkFrame):
    """
    Top application header containing:
    - Search query entry
    - Language selector (Both, English, Russian)
    - Sort selector (Relevance, Votes, Newest, Activity)
    - Search button
    - Theme switcher (Dark, Light, System)
    """

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
            height=68,
            **kwargs
        )
        self.pack_propagate(False)

        self.on_search = on_search_callback
        self.on_theme_change = on_theme_change_callback

        self.setup_ui()

    def setup_ui(self):
        # Container
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=16, pady=10)

        # 1. App Title / Logo Badge
        logo_frame = ctk.CTkFrame(container, fg_color="transparent")
        logo_frame.pack(side="left", padx=(0, 16))

        logo_badge = ctk.CTkLabel(
            logo_frame,
            text="⚡ SO",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            fg_color=SO_ORANGE,
            text_color="#ffffff",
            corner_radius=6,
            width=48,
            height=30
        )
        logo_badge.pack(side="left", padx=(0, 8))

        title_lbl = ctk.CTkLabel(
            logo_frame,
            text="Search Pro",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            text_color=COLOR_TEXT_PRIMARY
        )
        title_lbl.pack(side="left")

        # 2. Search Entry
        self.search_entry = ctk.CTkEntry(
            container,
            placeholder_text="🔍 Search Stack Overflow (e.g., 'python asyncio', 'pandas merge', 'error 403')...",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            fg_color=COLOR_BG_INPUT,
            border_color=COLOR_BORDER,
            text_color=COLOR_TEXT_PRIMARY,
            border_width=1,
            corner_radius=8,
            height=38
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 12))
        self.search_entry.bind("<Return>", lambda e: self.trigger_search())

        # 3. Language Selector
        self.lang_menu = ctk.CTkOptionMenu(
            container,
            values=["🌐 Both", "🇬🇧 English", "🇷🇺 Russian"],
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            dropdown_font=ctk.CTkFont(family="Segoe UI", size=12),
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
        self.lang_menu.pack(side="left", padx=(0, 10))

        # 4. Sort Menu
        self.sort_menu = ctk.CTkOptionMenu(
            container,
            values=["Relevance", "Votes", "Newest", "Activity"],
            font=ctk.CTkFont(family="Segoe UI", size=12),
            dropdown_font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color=COLOR_BG_CARD,
            button_color=COLOR_BG_CARD_ACTIVE,
            button_hover_color=COLOR_BG_CARD_HOVER,
            text_color=COLOR_TEXT_PRIMARY,
            dropdown_fg_color=COLOR_BG_CARD,
            dropdown_text_color=COLOR_TEXT_PRIMARY,
            corner_radius=8,
            width=110,
            height=38
        )
        self.sort_menu.set("Relevance")
        self.sort_menu.pack(side="left", padx=(0, 10))

        # 5. Search Button
        self.search_btn = ctk.CTkButton(
            container,
            text="Search",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            fg_color=SO_ORANGE,
            hover_color=SO_ORANGE_HOVER,
            text_color="#ffffff",
            corner_radius=8,
            width=90,
            height=38,
            command=self.trigger_search
        )
        self.search_btn.pack(side="left", padx=(0, 14))

        # 6. Theme Selector
        self.theme_menu = ctk.CTkOptionMenu(
            container,
            values=["🌙 Dark", "☀️ Light", "💻 System"],
            font=ctk.CTkFont(family="Segoe UI", size=11),
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

    def trigger_search(self):
        """Extract inputs and call search callback."""
        query = self.search_entry.get().strip()
        lang_val = self.lang_menu.get()
        # Clean language name
        if "English" in lang_val:
            lang = "English"
        elif "Russian" in lang_val:
            lang = "Russian"
        else:
            lang = "Both"

        sort = self.sort_menu.get().lower()
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
