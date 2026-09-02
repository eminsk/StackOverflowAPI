"""
Selectable Text Label Component for CustomTkinter
Provides seamless read-only text with mouse selection, clipboard copy,
right-click context menu, and mouse-wheel scroll forwarding.
"""

import sys
import tkinter as tk
from typing import Union, Tuple, Optional
import customtkinter as ctk
from src.ui.theme import (
    COLOR_BG_CARD, COLOR_TEXT_PRIMARY, FONT_FAMILY, resolve_color
)

# Selection background colors for light and dark modes
THEME_SELECTION_BG = {
    "dark": "#3e4259",
    "light": "#cbd5e1"
}


class SelectableLabel(tk.Text):
    """
    A read-only Tkinter Text widget styled and behaving like a label:
    - Text can be highlighted and selected with the mouse across multiple lines.
    - Standard shortcuts (Ctrl+C, Ctrl+A) and right-click context menu.
    - Automatic height calculation based on wrapped display lines.
    - Mouse wheel events are forwarded to parent CTkScrollableFrame.
    - Fully supports CustomTkinter dark/light theme switching.
    """

    def __init__(
        self,
        master,
        text: str = "",
        font: Union[Tuple[str, int], Tuple[str, int, str], ctk.CTkFont] = (FONT_FAMILY, 12),
        text_color: Union[str, Tuple[str, str]] = COLOR_TEXT_PRIMARY,
        bg_color: Union[str, Tuple[str, str]] = COLOR_BG_CARD,
        padx: int = 0,
        pady: int = 0,
        justify: str = "left",
        **kwargs
    ):
        self.text_color_spec = text_color
        self.bg_color_spec = bg_color
        self.raw_text = text

        if isinstance(font, ctk.CTkFont):
            f_family = font.cget("family")
            f_size = font.cget("size")
            f_weight = font.cget("weight")
            f_slant = font.cget("slant")
            font_spec = (f_family, f_size)
            if f_weight and f_weight != "normal":
                font_spec = (f_family, f_size, f_weight)
            elif f_slant and f_slant != "roman":
                font_spec = (f_family, f_size, f_slant)
        else:
            font_spec = font

        self.font_spec = font_spec
        self.mode = self._get_current_mode()

        bg = resolve_color(self.bg_color_spec, self.mode)
        fg = resolve_color(self.text_color_spec, self.mode)
        select_bg = THEME_SELECTION_BG.get(self.mode, THEME_SELECTION_BG["dark"])

        initial_lines = max(1, text.count('\n') + 1)

        super().__init__(
            master,
            wrap="word",
            font=self.font_spec,
            bg=bg,
            fg=fg,
            selectbackground=select_bg,
            selectforeground=fg,
            bd=0,
            padx=padx,
            pady=pady,
            highlightthickness=0,
            relief="flat",
            cursor="xterm",
            height=initial_lines,
            spacing1=1,
            spacing3=1,
            **kwargs
        )

        self.insert("1.0", text)
        self.configure(state="disabled")

        # Bindings
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

    def _on_configure(self, event=None):
        try:
            self.update_idletasks()
            dlines = self.count("1.0", "end-1c", "displaylines")
            if dlines:
                lines = max(1, dlines[0])
                if self.cget("height") != lines:
                    self.configure(height=lines)
        except Exception:
            pass

    def _on_mousewheel(self, event):
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
        self.tag_add("sel", "1.0", "end-1c")
        return "break"

    def _show_context_menu(self, event):
        menu = tk.Menu(self, tearoff=0)
        has_selection = False
        try:
            has_selection = bool(self.tag_ranges("sel"))
        except Exception:
            pass

        if has_selection:
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

    def set_text(self, text: str):
        self.raw_text = text
        self.configure(state="normal")
        self.delete("1.0", "end")
        self.insert("1.0", text)
        self.configure(state="disabled")
        self._on_configure()

    def apply_theme(self, mode: Optional[str] = None):
        if mode:
            self.mode = "light" if mode.lower() == "light" else "dark"
        else:
            self.mode = self._get_current_mode()

        bg = resolve_color(self.bg_color_spec, self.mode)
        fg = resolve_color(self.text_color_spec, self.mode)
        select_bg = THEME_SELECTION_BG.get(self.mode, THEME_SELECTION_BG["dark"])

        try:
            self.configure(
                bg=bg,
                fg=fg,
                selectbackground=select_bg,
                selectforeground=fg
            )
        except Exception:
            pass
