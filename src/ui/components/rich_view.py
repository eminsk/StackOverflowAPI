"""
Rich Content View Component
Renders structured HTML content (paragraphs, headings, lists, blockquotes, code blocks)
with visible, syntax-highlighted code blocks, 1-click code copying, and continuous
multi-line text selection for all text sections.
"""

import sys
import tkinter as tk
from typing import Dict, Any, List, Union, Tuple, Optional
import customtkinter as ctk
from src.utils.highlighter import parse_html_to_blocks
from src.ui.components.code_block import CodeBlockWidget
from src.ui.theme import (
    SO_ORANGE, COLOR_PRIMARY,
    COLOR_BG_CARD, COLOR_BG_BLOCKQUOTE, COLOR_BORDER,
    COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_TEXT_MUTED
)

# Selection background colors for light and dark modes
THEME_SELECTION_BG = {
    "dark": "#45475a",
    "light": "#cbd5e1"
}


class SelectableTextBlock(tk.Text):
    """
    A read-only Tkinter Text widget representing a continuous block of rich text
    (paragraphs, headings, lists, blockquotes) with multi-line selection.
    """

    def __init__(
        self,
        master,
        blocks: List[Dict[str, Any]],
        bg_color: Union[str, Tuple[str, str]] = COLOR_BG_CARD,
        **kwargs
    ):
        self.blocks = blocks
        self.card_bg_color = bg_color

        mode = ctk.get_appearance_mode().lower()
        self.mode = "light" if mode == "light" else "dark"

        bg = self._resolve_color(self.card_bg_color, self.mode)
        fg = self._resolve_color(COLOR_TEXT_PRIMARY, self.mode)
        select_bg = THEME_SELECTION_BG.get(self.mode, THEME_SELECTION_BG["dark"])

        super().__init__(
            master,
            wrap="word",
            font=("Segoe UI", 12),
            bg=bg,
            fg=fg,
            selectbackground=select_bg,
            selectforeground=fg,
            bd=0,
            padx=2,
            pady=2,
            highlightthickness=0,
            relief="flat",
            cursor="xterm",
            spacing1=1,
            spacing3=1,
            **kwargs
        )

        self._setup_tags()
        self._populate_content()

        # Bindings for resizing, right-click, keyboard copy, and mousewheel
        self.bind("<Configure>", self._on_configure)
        self.bind("<Button-3>", self._show_context_menu)
        self.bind("<MouseWheel>", self._on_mousewheel)
        self.bind("<Control-c>", self._on_copy_shortcut)
        self.bind("<Control-C>", self._on_copy_shortcut)
        self.bind("<Control-a>", self._on_select_all_shortcut)
        self.bind("<Control-A>", self._on_select_all_shortcut)

    def _get_current_mode(self) -> str:
        mode = ctk.get_appearance_mode().lower()
        return "light" if mode == "light" else "dark"

    def _resolve_color(self, color_spec: Union[str, Tuple[str, str], list], mode: str) -> str:
        if isinstance(color_spec, (tuple, list)):
            return color_spec[0] if mode == "light" else color_spec[1]
        return color_spec

    def _setup_tags(self):
        """Configure typography and colors for different HTML elements."""
        fg_primary = self._resolve_color(COLOR_TEXT_PRIMARY, self.mode)
        fg_secondary = self._resolve_color(COLOR_TEXT_SECONDARY, self.mode)
        fg_muted = self._resolve_color(COLOR_TEXT_MUTED, self.mode)
        bg_quote = self._resolve_color(COLOR_BG_BLOCKQUOTE, self.mode)

        self.tag_configure("p", font=("Segoe UI", 12), foreground=fg_primary, spacing1=3, spacing3=6)
        self.tag_configure("h1", font=("Segoe UI", 16, "bold"), foreground=fg_primary, spacing1=10, spacing3=4)
        self.tag_configure("h2", font=("Segoe UI", 14, "bold"), foreground=fg_primary, spacing1=8, spacing3=4)
        self.tag_configure("h3", font=("Segoe UI", 13, "bold"), foreground=fg_primary, spacing1=6, spacing3=3)
        self.tag_configure(
            "blockquote",
            font=("Segoe UI", 11, "italic"),
            foreground=fg_secondary,
            lmargin1=16,
            lmargin2=16,
            background=bg_quote,
            spacing1=4,
            spacing3=4
        )
        self.tag_configure(
            "list_item",
            font=("Segoe UI", 12),
            foreground=fg_primary,
            lmargin1=8,
            lmargin2=24,
            spacing1=2,
            spacing3=2
        )
        self.tag_configure("list_bullet", font=("Segoe UI", 12, "bold"), foreground=SO_ORANGE)
        self.tag_configure("muted", font=("Segoe UI", 11), foreground=fg_muted)

    def _populate_content(self):
        """Insert block contents into the text widget."""
        self.configure(state="normal")
        self.delete("1.0", "end")

        for b in self.blocks:
            b_type = b.get("type")
            if b_type == "paragraph":
                p_text = b.get("text", "")
                if p_text:
                    self.insert("end", p_text + "\n\n", "p")
            elif b_type == "heading":
                level = b.get("level", 2)
                h_text = b.get("text", "")
                tag = f"h{min(max(level, 1), 3)}"
                if h_text:
                    self.insert("end", h_text + "\n\n", tag)
            elif b_type == "blockquote":
                q_text = b.get("text", "")
                if q_text:
                    self.insert("end", q_text + "\n\n", "blockquote")
            elif b_type == "list":
                items = b.get("items", [])
                ordered = b.get("ordered", False)
                for idx, item in enumerate(items, 1):
                    prefix = f"{idx}. " if ordered else "• "
                    self.insert("end", prefix, "list_bullet")
                    self.insert("end", item + "\n", "list_item")
                self.insert("end", "\n")
            elif b_type == "hr":
                self.insert("end", "—" * 35 + "\n\n", "muted")

        self.configure(state="disabled")
        self._adjust_height()

    def _adjust_height(self):
        """Dynamically adjust widget height based on wrapped display lines."""
        try:
            self.update_idletasks()
            dlines = self.count("1.0", "end-1c", "displaylines")
            if dlines:
                total_lines = max(1, dlines[0])
                if self.cget("height") != total_lines:
                    self.configure(height=total_lines)
        except Exception:
            pass

    def _on_configure(self, event=None):
        self._adjust_height()

    def _on_mousewheel(self, event):
        """Forward mousewheel event to parent scrollable container with native speed."""
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

    def _on_copy_shortcut(self, event=None):
        self._copy_selection()
        return "break"

    def _on_select_all_shortcut(self, event=None):
        self._select_all()
        return "break"

    def _show_context_menu(self, event):
        menu = tk.Menu(self, tearoff=0)
        has_sel = bool(self.tag_ranges("sel"))
        if has_sel:
            menu.add_command(label="Копировать (Copy)", command=self._copy_selection)
        else:
            menu.add_command(label="Копировать всё (Copy All)", command=self._copy_all)

        menu.add_command(label="Выделить всё (Select All)", command=self._select_all)
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def _copy_selection(self):
        try:
            sel = self.get("sel.first", "sel.last")
            if sel:
                self.clipboard_clear()
                self.clipboard_append(sel)
        except Exception:
            pass

    def _copy_all(self):
        try:
            text = self.get("1.0", "end-1c")
            if text:
                self.clipboard_clear()
                self.clipboard_append(text)
        except Exception:
            pass

    def _select_all(self):
        self.tag_add("sel", "1.0", "end-1c")

    def apply_theme(self, mode: Optional[str] = None):
        """Update colors when appearance mode changes."""
        if mode:
            self.mode = "light" if mode.lower() == "light" else "dark"
        else:
            self.mode = self._get_current_mode()

        bg = self._resolve_color(self.card_bg_color, self.mode)
        fg = self._resolve_color(COLOR_TEXT_PRIMARY, self.mode)
        select_bg = THEME_SELECTION_BG.get(self.mode, THEME_SELECTION_BG["dark"])

        try:
            self.configure(
                bg=bg,
                fg=fg,
                selectbackground=select_bg,
                selectforeground=fg
            )
            self._setup_tags()
        except Exception:
            pass


class RichContentView(ctk.CTkFrame):
    """
    Renders rich HTML content with:
    - Visible, syntax-highlighted code blocks with 1-click copy buttons.
    - Selectable multi-line text blocks between code snippets.
    - Full width expansion and proper height calculation.
    - Synchronized fast mouse wheel scrolling.
    - Seamless dark/light theme switching.
    """

    def __init__(
        self,
        master,
        html_content: str,
        wraplength: int = 680,
        bg_color: Union[str, Tuple[str, str]] = COLOR_BG_CARD,
        **kwargs
    ):
        super().__init__(
            master,
            fg_color="transparent",
            **kwargs
        )

        self.html_content = html_content
        self.wraplength = wraplength
        self.card_bg_color = bg_color
        self.text_blocks: List[SelectableTextBlock] = []
        self.code_widgets: List[CodeBlockWidget] = []

        self.render_content()

    def render_content(self):
        """Parse HTML into grouped text blocks and full-width code block widgets."""
        for child in self.winfo_children():
            child.destroy()

        self.text_blocks.clear()
        self.code_widgets.clear()

        blocks = parse_html_to_blocks(self.html_content)

        if not blocks:
            empty_block = [{"type": "paragraph", "text": "No content available."}]
            tb = SelectableTextBlock(self, blocks=empty_block, bg_color=self.card_bg_color)
            tb.pack(fill="x", expand=True, pady=2)
            self.text_blocks.append(tb)
            return

        current_group = []

        def flush_group():
            if current_group:
                tb = SelectableTextBlock(self, blocks=list(current_group), bg_color=self.card_bg_color)
                tb.pack(fill="x", expand=True, pady=(2, 4))
                self.text_blocks.append(tb)
                current_group.clear()

        for b in blocks:
            b_type = b.get("type")
            if b_type == "code":
                flush_group()
                raw_code = b.get("code", "")
                lang_hint = b.get("language")
                if raw_code:
                    cw = CodeBlockWidget(self, code=raw_code, language_hint=lang_hint)
                    cw.pack(fill="x", expand=True, pady=(6, 10))
                    self.code_widgets.append(cw)
            else:
                current_group.append(b)

        flush_group()

    def _select_all(self):
        """Select all text in the first available text block."""
        if self.text_blocks:
            self.text_blocks[0]._select_all()

    def apply_theme(self, mode: Optional[str] = None):
        """Update colors when appearance mode changes."""
        for tb in self.text_blocks:
            tb.apply_theme(mode)
        for cw in self.code_widgets:
            if hasattr(cw, "apply_theme"):
                cw.apply_theme(mode if mode else ctk.get_appearance_mode().lower())
