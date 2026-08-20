"""
Code Block Widget with Syntax Highlighting, Vertical & Horizontal Scrollbars, and 1-Click Clipboard Copy
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
    Component displaying a code block with:
    - Language badge and 1-click clipboard copy button
    - Syntax-highlighted text using Pygments
    - Modern vertical CTkScrollbar for multi-line code
    - Modern horizontal CTkScrollbar for wide lines
    - Smart MouseWheel scrolling (scrolls code block vertically, forwards to page at boundaries)
    - Shift + MouseWheel horizontal scrolling
    """

    MAX_VISIBLE_LINES = 20

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

        # Code Text Area Frame
        total_lines = max(code.count('\n') + 1, 2)
        text_height = min(total_lines, self.MAX_VISIBLE_LINES)

        theme_palette = THEME_COLORS.get(self.mode, THEME_COLORS["dark"])

        self.text_frame = tk.Frame(self, bg=theme_palette["bg"])
        self.text_frame.pack(fill="x", expand=True, padx=8, pady=(4, 2))

        # Vertical scrollbar (CTkScrollbar)
        self.v_scroll = ctk.CTkScrollbar(
            self.text_frame,
            orientation="vertical",
            width=12
        )

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
            relief="flat",
            cursor="xterm"
        )

        # Horizontal scrollbar (CTkScrollbar)
        self.h_scroll = ctk.CTkScrollbar(
            self,
            orientation="horizontal",
            command=self.text_widget.xview,
            height=12
        )

        self.v_scroll.configure(command=self.text_widget.yview)
        self.text_widget.configure(
            xscrollcommand=self.h_scroll.set,
            yscrollcommand=self.v_scroll.set
        )

        # Pack vertical scrollbar and text widget
        if total_lines > self.MAX_VISIBLE_LINES:
            self.v_scroll.pack(side="right", fill="y", padx=(2, 0))
        self.text_widget.pack(side="left", fill="both", expand=True)

        # Always pack horizontal scrollbar
        self.h_scroll.pack(fill="x", padx=8, pady=(0, 6))

        # Insert and highlight code
        self.render_highlighted_code()

        # Bind smart mousewheel (vertical scrolling within code, forwarding at bounds)
        self.text_widget.bind("<MouseWheel>", self._on_mousewheel)
        self.text_widget.bind("<Shift-MouseWheel>", self._on_shift_mousewheel)
        self.text_widget.bind("<Button-3>", self._show_context_menu)

        # Make read-only
        self.text_widget.configure(state="disabled")

    def _on_mousewheel(self, event):
        """
        Smart vertical scrolling:
        - If code block has internal vertical overflow and not at top/bottom boundary,
          scrolls the code block internally.
        - Otherwise, forwards scrolling to the parent CTkScrollableFrame.
        """
        yv = self.text_widget.yview()
        is_scrollable = yv != (0.0, 1.0)
        delta = event.delta

        if is_scrollable:
            # Negative delta = scroll down, Positive delta = scroll up on Windows
            if delta < 0 and yv[1] < 1.0:
                self.text_widget.yview("scroll", -int(delta / 40), "units")
                return "break"
            elif delta > 0 and yv[0] > 0.0:
                self.text_widget.yview("scroll", -int(delta / 40), "units")
                return "break"

        # Forward to parent page
        curr = self.master
        while curr is not None:
            if hasattr(curr, "_parent_canvas") and curr._parent_canvas:
                try:
                    if sys.platform.startswith("win"):
                        scroll_delta = -int(delta / 6)
                    elif sys.platform == "darwin":
                        scroll_delta = -delta
                    else:
                        scroll_delta = -1 if event.num == 4 else 1
                    curr._parent_canvas.yview("scroll", scroll_delta, "units")
                    return "break"
                except Exception:
                    pass
            elif isinstance(curr, tk.Canvas):
                try:
                    if sys.platform.startswith("win"):
                        scroll_delta = -int(delta / 6)
                    else:
                        scroll_delta = -1 if event.num == 4 else 1
                    curr.yview("scroll", scroll_delta, "units")
                    return "break"
                except Exception:
                    pass
            curr = getattr(curr, "master", None)

    def _on_shift_mousewheel(self, event):
        """Scroll code horizontally when holding Shift + Mouse Wheel."""
        try:
            if sys.platform.startswith("win"):
                delta = -int(event.delta / 6)
            elif sys.platform == "darwin":
                delta = -event.delta
            else:
                delta = -1 if event.num == 4 else 1
            self.text_widget.xview("scroll", delta, "units")
            return "break"
        except Exception:
            pass

    def _show_context_menu(self, event):
        """Show context menu for copying code."""
        menu = tk.Menu(self.text_widget, tearoff=0)
        has_sel = bool(self.text_widget.tag_ranges("sel"))
        if has_sel:
            menu.add_command(label="Копировать (Copy)", command=self._copy_selection)
        else:
            menu.add_command(label="Копировать весь код (Copy All)", command=self.copy_to_clipboard)

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

    def _select_all(self):
        self.text_widget.tag_add("sel", "1.0", "end-1c")

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
