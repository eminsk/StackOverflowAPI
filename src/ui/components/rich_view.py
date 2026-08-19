"""
Rich Content View
Parses and displays HTML blocks (paragraphs, code blocks, lists, blockquotes, headings) natively in CustomTkinter.
"""

from typing import Dict, Any, List
import customtkinter as ctk
from src.utils.highlighter import parse_html_to_blocks
from src.ui.components.code_block import CodeBlockWidget
from src.ui.theme import (
    SO_ORANGE, COLOR_PRIMARY,
    COLOR_BG_BLOCKQUOTE, COLOR_BORDER,
    COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_TEXT_MUTED
)


class RichContentView(ctk.CTkFrame):
    """
    Renders structured HTML content using native CustomTkinter widgets:
    - Styled paragraphs
    - Syntax-highlighted code blocks with 1-click copy
    - Formatted bullet/numbered lists
    - Accent-bordered blockquotes
    - Section headers
    """

    def __init__(self, master, html_content: str, wraplength: int = 680, **kwargs):
        super().__init__(
            master,
            fg_color="transparent",
            **kwargs
        )

        self.html_content = html_content
        self.wraplength = wraplength
        self.render_content()

    def render_content(self):
        """Parse HTML and instantiate native CTk widgets for each block."""
        blocks = parse_html_to_blocks(self.html_content)

        if not blocks:
            empty_lbl = ctk.CTkLabel(
                self,
                text="No content available.",
                font=ctk.CTkFont(family="Segoe UI", size=12),
                text_color=COLOR_TEXT_MUTED
            )
            empty_lbl.pack(anchor="w", pady=4)
            return

        for block in blocks:
            b_type = block.get("type")

            # 1. Paragraph
            if b_type == "paragraph":
                p_text = block.get("text", "")
                if p_text:
                    p_lbl = ctk.CTkLabel(
                        self,
                        text=p_text,
                        font=ctk.CTkFont(family="Segoe UI", size=13),
                        text_color=COLOR_TEXT_PRIMARY,
                        justify="left",
                        anchor="w",
                        wraplength=self.wraplength
                    )
                    p_lbl.pack(fill="x", anchor="w", pady=(2, 6))

            # 2. Code Block
            elif b_type == "code":
                raw_code = block.get("code", "")
                lang_hint = block.get("language")
                if raw_code:
                    code_widget = CodeBlockWidget(
                        self,
                        code=raw_code,
                        language_hint=lang_hint
                    )
                    code_widget.pack(fill="x", expand=True, pady=(6, 10))

            # 3. Blockquote
            elif b_type == "blockquote":
                q_text = block.get("text", "")
                if q_text:
                    q_frame = ctk.CTkFrame(
                        self,
                        fg_color=COLOR_BG_BLOCKQUOTE,
                        border_color=COLOR_PRIMARY,
                        border_width=2,
                        corner_radius=6
                    )
                    q_frame.pack(fill="x", pady=(4, 8), padx=(4, 0))

                    q_lbl = ctk.CTkLabel(
                        q_frame,
                        text=q_text,
                        font=ctk.CTkFont(family="Segoe UI", size=12, slant="italic"),
                        text_color=COLOR_TEXT_SECONDARY,
                        justify="left",
                        anchor="w",
                        wraplength=self.wraplength - 40
                    )
                    q_lbl.pack(fill="x", padx=12, pady=8)

            # 4. Lists (ul, ol)
            elif b_type == "list":
                items = block.get("items", [])
                is_ordered = block.get("ordered", False)
                for idx, item in enumerate(items, 1):
                    item_frame = ctk.CTkFrame(self, fg_color="transparent")
                    item_frame.pack(fill="x", anchor="w", pady=(1, 3), padx=(8, 0))

                    prefix = f"{idx}." if is_ordered else "•"
                    bullet_lbl = ctk.CTkLabel(
                        item_frame,
                        text=prefix,
                        font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
                        text_color=SO_ORANGE,
                        width=18
                    )
                    bullet_lbl.pack(side="left", anchor="n", padx=(0, 6))

                    item_lbl = ctk.CTkLabel(
                        item_frame,
                        text=item,
                        font=ctk.CTkFont(family="Segoe UI", size=13),
                        text_color=COLOR_TEXT_PRIMARY,
                        justify="left",
                        anchor="w",
                        wraplength=self.wraplength - 35
                    )
                    item_lbl.pack(side="left", fill="x", expand=True)

            # 5. Heading
            elif b_type == "heading":
                level = block.get("level", 2)
                h_text = block.get("text", "")
                h_size = max(18 - (level * 2), 13)

                h_lbl = ctk.CTkLabel(
                    self,
                    text=h_text,
                    font=ctk.CTkFont(family="Segoe UI", size=h_size, weight="bold"),
                    text_color=COLOR_TEXT_PRIMARY,
                    justify="left",
                    anchor="w",
                    wraplength=self.wraplength
                )
                h_lbl.pack(fill="x", anchor="w", pady=(10, 4))

            # 6. Horizontal Rule
            elif b_type == "hr":
                hr = ctk.CTkFrame(
                    self,
                    height=1,
                    fg_color=COLOR_BORDER
                )
                hr.pack(fill="x", pady=10)
