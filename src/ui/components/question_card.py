"""
Question Card Component for Search Results List
"""

from datetime import datetime
import html
from typing import Dict, Any, Callable
import customtkinter as ctk
from src.ui.theme import (
    SO_ORANGE, COLOR_SUCCESS,
    COLOR_BG_CARD, COLOR_BG_CARD_HOVER, COLOR_BG_CARD_ACTIVE,
    COLOR_BG_SIDEBAR, COLOR_BG_TAG, COLOR_BORDER,
    COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_TEXT_MUTED, COLOR_TEXT_TAG
)


class QuestionCard(ctk.CTkFrame):
    """
    Card representing a single question in the search results list.
    Displays score pill, answer count pill, view count, title, tags, and author.
    """

    def __init__(
        self,
        master,
        question_data: Dict[str, Any],
        on_click_callback: Callable[[int], None],
        **kwargs
    ):
        self.normal_bg = COLOR_BG_CARD
        self.hover_bg = COLOR_BG_CARD_HOVER
        self.active_bg = COLOR_BG_CARD_ACTIVE
        self.border_color = COLOR_BORDER

        super().__init__(
            master,
            fg_color=self.normal_bg,
            border_color=self.border_color,
            border_width=1,
            corner_radius=10,
            cursor="hand2",
            **kwargs
        )

        self.question_data = question_data
        self.question_id = question_data.get("question_id", 0)
        self.on_click_callback = on_click_callback
        self.is_selected = False

        self.setup_ui()
        self.bind_events()

    def setup_ui(self):
        # Data extraction
        title = self.question_data.get("title", "Untitled Question")
        score = self.question_data.get("score", 0)
        answer_count = self.question_data.get("answer_count", 0)
        is_answered = self.question_data.get("is_answered", False)
        view_count = self.question_data.get("view_count", 0)
        tags = self.question_data.get("tags", [])
        owner = self.question_data.get("owner", {})
        author = owner.get("display_name", "Anonymous")
        
        # Created Date
        created_ts = self.question_data.get("creation_date", 0)
        created_str = datetime.fromtimestamp(created_ts).strftime("%b %d, %Y") if created_ts else ""

        # Formatting Views (e.g. 1.5k)
        if view_count >= 1000000:
            views_formatted = f"{view_count/1000000:.1f}M"
        elif view_count >= 1000:
            views_formatted = f"{view_count/1000:.1f}k"
        else:
            views_formatted = str(view_count)

        # Top Meta Row: Score, Answers, Views, Date
        self.top_row = ctk.CTkFrame(self, fg_color="transparent")
        self.top_row.pack(fill="x", padx=14, pady=(12, 6))

        # Score Badge
        score_prefix = "▲ " if score >= 0 else "▼ "
        score_color = COLOR_SUCCESS if score > 0 else (COLOR_TEXT_MUTED if score == 0 else "#ef4444")
        self.score_badge = ctk.CTkLabel(
            self.top_row,
            text=f"{score_prefix}{score}",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=score_color
        )
        self.score_badge.pack(side="left", padx=(0, 10))

        # Answers Pill
        if is_answered:
            ans_bg = COLOR_SUCCESS
            ans_text = f"✓ {answer_count} ans"
            ans_fg = "#ffffff"
        elif answer_count > 0:
            ans_bg = COLOR_BG_TAG
            ans_text = f"{answer_count} ans"
            ans_fg = COLOR_TEXT_TAG
        else:
            ans_bg = COLOR_BG_SIDEBAR
            ans_text = "0 ans"
            ans_fg = COLOR_TEXT_MUTED

        self.ans_pill = ctk.CTkLabel(
            self.top_row,
            text=f" {ans_text} ",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            fg_color=ans_bg,
            text_color=ans_fg,
            corner_radius=5
        )
        self.ans_pill.pack(side="left", padx=(0, 10))

        # Views
        self.views_label = ctk.CTkLabel(
            self.top_row,
            text=f"👁 {views_formatted}",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=COLOR_TEXT_MUTED
        )
        self.views_label.pack(side="left", padx=(0, 10))

        # Date
        self.date_label = ctk.CTkLabel(
            self.top_row,
            text=f"📅 {created_str}",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=COLOR_TEXT_MUTED
        )
        self.date_label.pack(side="right")

        # Question Title (Main focus)
        clean_title = html.unescape(title)
        self.title_label = ctk.CTkLabel(
            self,
            text=clean_title,
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=COLOR_TEXT_PRIMARY,
            justify="left",
            anchor="w",
            wraplength=410
        )
        self.title_label.pack(fill="x", padx=14, pady=(2, 8))

        # Bottom Row: Tags & Author
        self.bottom_row = ctk.CTkFrame(self, fg_color="transparent")
        self.bottom_row.pack(fill="x", padx=14, pady=(0, 12))

        # Render up to 3 tags
        tags_container = ctk.CTkFrame(self.bottom_row, fg_color="transparent")
        tags_container.pack(side="left", fill="x", expand=True)

        for tag in tags[:3]:
            t_label = ctk.CTkLabel(
                tags_container,
                text=f" {tag} ",
                font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
                fg_color=COLOR_BG_TAG,
                text_color=COLOR_TEXT_TAG,
                corner_radius=4
            )
            t_label.pack(side="left", padx=(0, 5))

        # Author Name
        self.author_label = ctk.CTkLabel(
            self.bottom_row,
            text=f"👤 {author[:18]}",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=COLOR_TEXT_SECONDARY
        )
        self.author_label.pack(side="right")

    def bind_events(self):
        """Bind hover and click events to the card and all its children."""
        self.bind("<Enter>", self.on_hover_enter)
        self.bind("<Leave>", self.on_hover_leave)
        self.bind("<Button-1>", self.on_card_click)

        # Propagate click & hover to children
        for child in self.winfo_children():
            self._bind_child(child)

    def _bind_child(self, widget):
        widget.bind("<Button-1>", self.on_card_click, add="+")
        widget.bind("<Enter>", self.on_hover_enter, add="+")
        widget.bind("<Leave>", self.on_hover_leave, add="+")
        for sub in widget.winfo_children():
            self._bind_child(sub)

    def on_hover_enter(self, event=None):
        if not self.is_selected:
            self.configure(fg_color=self.hover_bg)

    def on_hover_leave(self, event=None):
        if not self.is_selected:
            self.configure(fg_color=self.normal_bg)

    def set_selected(self, selected: bool):
        """Highlight card with active accent border and background."""
        self.is_selected = selected
        if selected:
            self.configure(
                fg_color=self.active_bg,
                border_color=SO_ORANGE,
                border_width=2
            )
        else:
            self.configure(
                fg_color=self.normal_bg,
                border_color=self.border_color,
                border_width=1
            )

    def on_card_click(self, event=None):
        if self.on_click_callback:
            self.on_click_callback(self.question_id)
