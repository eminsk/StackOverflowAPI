"""
Code Block Widget with Syntax Highlighting and 1-Click Clipboard Copy
"""

import sys
import tkinter as tk
import customtkinter as ctk
from src.utils.highlighter import CodeHighlighter, THEME_COLORS
from src.ui.theme import (
    FONT_FAMILY_MONO, COLOR_SUCCESS,
    COLOR_BG_CODE, COLOR_BG_CODE_HEADER, COLOR_BORDER,
    COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_BG_CARD, COLOR_BG_CARD_HOVER
)


class CodeBlockWidget(ctk.CTkFrame):
    """
    Component displaying a code block with language header, 
    syntax-highlighted text, and a copy button with visual feedback.
    """

    def __init__(self, master, code: str, language_hint: str = None, **kwargs):
        super().__init__(
            master,
            fg_color=COLOR_BG_CODE,
            border_color=COLOR_BORDER,
            border_width=1,
            corner_radius=8,
            **kwargs
        )

        self.code = code
        self.language_hint = language_hint

        mode = ctk.get_appearance_mode().lower()
        if mode not in ("dark", "light"):
            mode = "dark"
        self.mode = mode

        # Header Bar
        self.header_frame = ctk.CTkFrame(
            self,
            fg_color=COLOR_BG_CODE_HEADER,
            corner_radius=6,
            height=32
        )
        self.header_frame.pack(fill="x", padx=2, pady=2)
        self.header_frame.pack_propagate(False)

        # Tokenize code to get language name
        self.tokens, self.lang_name = CodeHighlighter.tokenize(code, language_hint)

        # Language Label
        self.lang_label = ctk.CTkLabel(
            self.header_frame,
            text=f"  ⚡ {self.lang_name}",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=COLOR_TEXT_SECONDARY
        )
        self.lang_label.pack(side="left", padx=8, pady=4)

        # Copy Button
        self.copy_btn = ctk.CTkButton(
            self.header_frame,
            text="📋 Copy Code",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            width=90,
            height=22,
            corner_radius=5,
            fg_color=COLOR_BG_CARD,
            hover_color=COLOR_BG_CARD_HOVER,
            text_color=COLOR_TEXT_PRIMARY,
            command=self.copy_to_clipboard
        )
        self.copy_btn.pack(side="right", padx=6, pady=4)

        # Code Text Area
        line_count = min(max(code.count('\n') + 1, 2), 35)
        text_height = min(max(line_count, 2), 30)

        theme_palette = THEME_COLORS.get(self.mode, THEME_COLORS["dark"])

        self.text_frame = tk.Frame(self, bg=theme_palette["bg"])
        self.text_frame.pack(fill="x", expand=True, padx=8, pady=(4, 8))

        # Tkinter Text widget
        self.text_widget = tk.Text(
            self.text_frame,
            wrap="none",
            height=text_height,
            font=(FONT_FAMILY_MONO, 10),
            bg=theme_palette["bg"],
            fg=theme_palette["fg"],
            selectbackground=theme_palette["select_bg"],
            selectforeground=theme_palette["fg"],
            bd=0,
            padx=8,
            pady=6,
            highlightthickness=0,
            relief="flat"
        )
        
        # Horizontal scrollbar if code is wide
        self.h_scroll = tk.Scrollbar(
            self.text_frame,
            orient="horizontal",
            command=self.text_widget.xview,
            bg=theme_palette["bg"]
        )
        self.text_widget.configure(xscrollcommand=self.h_scroll.set)

        self.text_widget.pack(fill="both", expand=True)

        # Only pack h_scroll if long lines exist
        max_line_len = max([len(line) for line in code.split('\n')] or [0])
        if max_line_len > 60:
            self.h_scroll.pack(fill="x")

        # Insert and highlight code
        self.render_highlighted_code()

        # Bind mousewheel to scroll parent page with native speed
        self.text_widget.bind("<MouseWheel>", self._on_mousewheel)

        # Make read-only
        self.text_widget.configure(state="disabled")

    def _on_mousewheel(self, event):
        """Propagate mouse wheel events upward to parent CTkScrollableFrame with native speed."""
        curr = self.master
        while curr is not None:
            if hasattr(curr, "_parent_canvas") and curr._parent_canvas:
                try:
                    if sys.platform.startswith("win"):
                        delta = -int(event.delta / 6)
                    elif sys.platform == "darwin":
                        delta = -event.delta
                    else:
                        delta = -1 if event.num == 4 else 1
                    curr._parent_canvas.yview("scroll", delta, "units")
                    return "break"
                except Exception:
                    pass
            elif isinstance(curr, tk.Canvas):
                try:
                    if sys.platform.startswith("win"):
                        delta = -int(event.delta / 6)
                    else:
                        delta = -1 if event.num == 4 else 1
                    curr.yview("scroll", delta, "units")
                    return "break"
                except Exception:
                    pass
            curr = getattr(curr, "master", None)

    def render_highlighted_code(self):
        """Insert tokens and configure tag colors in Tk Text widget."""
        self.text_widget.configure(state="normal")
        self.text_widget.delete("1.0", "end")

        configured_tags = set()

        for token_type, token_val in self.tokens:
            tag_name = f"tok_{token_type}"

            if tag_name not in configured_tags:
                color = CodeHighlighter.get_token_color(token_type, self.mode)
                self.text_widget.tag_configure(tag_name, foreground=color)
                configured_tags.add(tag_name)

            self.text_widget.insert("end", token_val, tag_name)

        self.text_widget.configure(state="disabled")

    def apply_theme(self, mode: str):
        """Update colors of standard Tk Text widget when appearance mode changes."""
        self.mode = mode.lower()
        if self.mode not in ("dark", "light"):
            self.mode = "dark"

        theme_palette = THEME_COLORS.get(self.mode, THEME_COLORS["dark"])
        self.text_frame.configure(bg=theme_palette["bg"])
        self.text_widget.configure(
            bg=theme_palette["bg"],
            fg=theme_palette["fg"],
            selectbackground=theme_palette["select_bg"],
            selectforeground=theme_palette["fg"]
        )
        self.h_scroll.configure(bg=theme_palette["bg"])
        self.render_highlighted_code()

    def copy_to_clipboard(self):
        """Copy raw code to clipboard and show visual checkmark."""
        try:
            self.clipboard_clear()
            self.clipboard_append(self.code)
            self.update()

            # Visual feedback
            self.copy_btn.configure(
                text="✓ Copied!",
                fg_color=COLOR_SUCCESS,
                text_color="#ffffff"
            )

            # Revert after 1.8 seconds
            self.after(1800, self.reset_copy_button)
        except Exception as e:
            print(f"Clipboard error: {e}")

    def reset_copy_button(self):
        """Reset copy button back to initial state."""
        try:
            self.copy_btn.configure(
                text="📋 Copy Code",
                fg_color=COLOR_BG_CARD,
                text_color=COLOR_TEXT_PRIMARY
            )
        except Exception:
            pass
