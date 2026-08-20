"""
Rich Content View Component
Renders structured HTML content (paragraphs, headings, lists, blockquotes, code blocks)
as a single unified document with continuous multi-line text selection, Ctrl+C, context menu,
and embedded interactive code blocks with 1-click copy.
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


class RichContentView(ctk.CTkFrame):
    """
    Renders rich HTML content in a single unified text document widget:
    - Allows continuous multi-line selection across paragraphs, headings, lists, and quotes.
    - Standard shortcuts (Ctrl+C, Ctrl+A) and right-click context menu.
    - Embedded interactive syntax-highlighted code blocks with 1-click copy buttons.
    - Smooth mouse wheel event forwarding to parent CTkScrollableFrame.
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
        self.embedded_code_widgets = []

        mode = ctk.get_appearance_mode().lower()
        self.mode = "light" if mode == "light" else "dark"

        bg = self._resolve_color(self.card_bg_color, self.mode)
        fg = self._resolve_color(COLOR_TEXT_PRIMARY, self.mode)
        select_bg = THEME_SELECTION_BG.get(self.mode, THEME_SELECTION_BG["dark"])

        self.text_widget = tk.Text(
            self,
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
            spacing3=1
        )
        self.text_widget.pack(fill="x", expand=True)

        self._setup_tags()
        self.render_content()

        # Bindings
        self.text_widget.bind("<Configure>", self._on_configure)
        self.text_widget.bind("<Button-3>", self._show_context_menu)
        self.text_widget.bind("<MouseWheel>", self._on_mousewheel)
        self.text_widget.bind("<Control-c>", self._on_copy_shortcut)
        self.text_widget.bind("<Control-C>", self._on_copy_shortcut)
        self.text_widget.bind("<Control-a>", self._on_select_all_shortcut)
        self.text_widget.bind("<Control-A>", self._on_select_all_shortcut)

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

        self.text_widget.tag_configure("p", font=("Segoe UI", 12), foreground=fg_primary, spacing1=3, spacing3=6)
        self.text_widget.tag_configure("h1", font=("Segoe UI", 16, "bold"), foreground=fg_primary, spacing1=10, spacing3=4)
        self.text_widget.tag_configure("h2", font=("Segoe UI", 14, "bold"), foreground=fg_primary, spacing1=8, spacing3=4)
        self.text_widget.tag_configure("h3", font=("Segoe UI", 13, "bold"), foreground=fg_primary, spacing1=6, spacing3=3)
        self.text_widget.tag_configure(
            "blockquote",
            font=("Segoe UI", 11, "italic"),
            foreground=fg_secondary,
            lmargin1=16,
            lmargin2=16,
            background=bg_quote,
            spacing1=4,
            spacing3=4
        )
        self.text_widget.tag_configure(
            "list_item",
            font=("Segoe UI", 12),
            foreground=fg_primary,
            lmargin1=8,
            lmargin2=24,
            spacing1=2,
            spacing3=2
        )
        self.text_widget.tag_configure("list_bullet", font=("Segoe UI", 12, "bold"), foreground=SO_ORANGE)
        self.text_widget.tag_configure("code_block_pad", spacing1=6, spacing3=6)
        self.text_widget.tag_configure("muted", font=("Segoe UI", 11), foreground=fg_muted)

    def render_content(self):
        """Parse HTML blocks and insert into unified text document with tags and code widgets."""
        self.embedded_code_widgets.clear()
        self.text_widget.configure(state="normal")
        self.text_widget.delete("1.0", "end")

        blocks = parse_html_to_blocks(self.html_content)

        if not blocks:
            self.text_widget.insert("end", "No content available.\n", "muted")
            self.text_widget.configure(state="disabled")
            self._adjust_height()
            return

        for block in blocks:
            b_type = block.get("type")

            # 1. Paragraph
            if b_type == "paragraph":
                p_text = block.get("text", "")
                if p_text:
                    self.text_widget.insert("end", p_text + "\n\n", "p")

            # 2. Heading
            elif b_type == "heading":
                level = block.get("level", 2)
                h_text = block.get("text", "")
                tag = f"h{min(max(level, 1), 3)}"
                if h_text:
                    self.text_widget.insert("end", h_text + "\n\n", tag)

            # 3. Blockquote
            elif b_type == "blockquote":
                q_text = block.get("text", "")
                if q_text:
                    self.text_widget.insert("end", q_text + "\n\n", "blockquote")

            # 4. List
            elif b_type == "list":
                items = block.get("items", [])
                ordered = block.get("ordered", False)
                for idx, item in enumerate(items, 1):
                    prefix = f"{idx}. " if ordered else "• "
                    self.text_widget.insert("end", prefix, "list_bullet")
                    self.text_widget.insert("end", item + "\n", "list_item")
                self.text_widget.insert("end", "\n")

            # 5. Code Block (embedded widget)
            elif b_type == "code":
                raw_code = block.get("code", "")
                lang_hint = block.get("language")
                if raw_code:
                    cw = CodeBlockWidget(self.text_widget, code=raw_code, language_hint=lang_hint)
                    self.embedded_code_widgets.append(cw)
                    self.text_widget.window_create("end", window=cw)
                    self.text_widget.insert("end", "\n\n", "code_block_pad")

            # 6. Horizontal Rule
            elif b_type == "hr":
                self.text_widget.insert("end", "—" * 35 + "\n\n", "muted")

        self.text_widget.configure(state="disabled")
        self._adjust_height()

    def _adjust_height(self):
        """Calculate and set required height in display lines."""
        try:
            self.text_widget.update_idletasks()
            dlines = self.text_widget.count("1.0", "end-1c", "displaylines")
            if dlines:
                total_lines = max(2, dlines[0])
                if self.text_widget.cget("height") != total_lines:
                    self.text_widget.configure(height=total_lines)
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
        menu = tk.Menu(self.text_widget, tearoff=0)
        has_sel = bool(self.text_widget.tag_ranges("sel"))
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
            sel = self.text_widget.get("sel.first", "sel.last")
            if sel:
                self.clipboard_clear()
                self.clipboard_append(sel)
        except Exception:
            pass

    def _copy_all(self):
        try:
            text = self.text_widget.get("1.0", "end-1c")
            if text:
                self.clipboard_clear()
                self.clipboard_append(text)
        except Exception:
            pass

    def _select_all(self):
        self.text_widget.tag_add("sel", "1.0", "end-1c")

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
            self.text_widget.configure(
                bg=bg,
                fg=fg,
                selectbackground=select_bg,
                selectforeground=fg
            )
            self._setup_tags()
        except Exception:
            pass

        # Forward theme change to embedded code widgets
        for cw in self.embedded_code_widgets:
            if hasattr(cw, "apply_theme"):
                try:
                    cw.apply_theme(self.mode)
                except Exception:
                    pass
