"""
Question Details & Answers View Component
Displays full question information, tags, rich selectable body with code copy,
bookmarking, 1-click answer/question copy, in-place smooth comment threads,
and sorted answers with accepted solution styling.
"""

import html
import webbrowser
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable
import customtkinter as ctk

from src.ui.components.rich_view import RichContentView
from src.ui.components.selectable_label import SelectableLabel
from src.utils.highlighter import html_to_markdown
from src.utils.bookmarks import BookmarkManager
from src.ui.theme import (
    SO_ORANGE, COLOR_SUCCESS, COLOR_PRIMARY, COLOR_BOOKMARK, COLOR_BOOKMARK_HOVER,
    COLOR_BG_WINDOW, COLOR_BG_CARD, COLOR_BG_CARD_HOVER, COLOR_BG_CARD_ACTIVE,
    COLOR_BG_SIDEBAR, COLOR_BG_TAG, COLOR_BORDER, COLOR_BORDER_ACCEPTED,
    COLOR_ACCEPTED_BANNER_BG, COLOR_ACCEPTED_BANNER_TEXT, COLOR_ACCEPTED_BANNER_BORDER,
    COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_TEXT_MUTED, COLOR_TEXT_TAG,
    FONT_FAMILY
)


class QuestionDetailsView(ctk.CTkScrollableFrame):
    """
    Scrollable full-view containing:
    - Question header, stats, author badge, browser link, bookmark button, copy buttons
    - Question tags
    - Question rich body with selectable text and syntax-highlighted code
    - In-place collapsible comments drawer (no scroll reset or flicker!)
    - Answers header & list of answers
    - Answer accepted solution banner, score, copy answer button, rich body, comments
    """

    def __init__(
        self,
        master,
        on_fetch_comments_callback: Callable[[int, str, str], None],
        **kwargs
    ):
        super().__init__(
            master,
            fg_color=COLOR_BG_WINDOW,
            **kwargs
        )

        self.on_fetch_comments = on_fetch_comments_callback
        self.bookmark_mgr = BookmarkManager()

        self.current_question: Optional[Dict[str, Any]] = None
        self.current_answers: List[Dict[str, Any]] = []
        self.current_language: str = "English"

        # Comments cache and tracking per widget
        self.comments_data: Dict[str, List[Dict[str, Any]]] = {}
        self.comment_subframes: Dict[str, ctk.CTkFrame] = {}
        self.comment_toggle_buttons: Dict[str, ctk.CTkButton] = {}
        self.expanded_comments: set = set()

        self.show_welcome_state()

    def show_welcome_state(self):
        """Display helpful welcome banner when no question is selected."""
        for child in self.winfo_children():
            child.destroy()

        welcome_card = ctk.CTkFrame(
            self,
            fg_color=COLOR_BG_CARD,
            border_color=COLOR_BORDER,
            border_width=1,
            corner_radius=12
        )
        welcome_card.pack(fill="x", padx=20, pady=40)

        icon_lbl = ctk.CTkLabel(
            welcome_card,
            text="⚡",
            font=ctk.CTkFont(size=44)
        )
        icon_lbl.pack(pady=(32, 10))

        title_lbl = ctk.CTkLabel(
            welcome_card,
            text="Stack Overflow Search Pro",
            font=ctk.CTkFont(family=FONT_FAMILY, size=20, weight="bold"),
            text_color=COLOR_TEXT_PRIMARY
        )
        title_lbl.pack(pady=(0, 8))

        desc_lbl = ctk.CTkLabel(
            welcome_card,
            text="Search questions simultaneously across Stack Overflow (English) and Russian Stack Overflow.\n"
                 "Select any question on the left to read full answers, copy code blocks with 1 click, and save bookmarks.\n\n"
                 "💡 Tip: Use Ctrl+K to quickly focus the search bar from anywhere.",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            text_color=COLOR_TEXT_SECONDARY,
            justify="center"
        )
        desc_lbl.pack(pady=(0, 32))

    def show_loading(self, message: str = "Loading question details..."):
        """Show loading spinner card."""
        for child in self.winfo_children():
            child.destroy()

        loading_frame = ctk.CTkFrame(
            self,
            fg_color=COLOR_BG_CARD,
            corner_radius=10,
            border_color=COLOR_BORDER,
            border_width=1
        )
        loading_frame.pack(fill="x", padx=20, pady=40)

        lbl = ctk.CTkLabel(
            loading_frame,
            text=f"⏳ {message}",
            font=ctk.CTkFont(family=FONT_FAMILY, size=14, weight="bold"),
            text_color=COLOR_TEXT_SECONDARY
        )
        lbl.pack(pady=32)

    def load_question(self, question: Dict[str, Any], language: str):
        """Render full question details."""
        self.current_question = question
        self.current_language = language
        self.expanded_comments.clear()
        self.comment_subframes.clear()
        self.comment_toggle_buttons.clear()

        for child in self.winfo_children():
            child.destroy()

        # 1. Main Question Card
        q_card = ctk.CTkFrame(
            self,
            fg_color=COLOR_BG_CARD,
            border_color=COLOR_BORDER,
            border_width=1,
            corner_radius=12
        )
        q_card.pack(fill="x", padx=16, pady=(16, 12))

        # Title (Selectable)
        raw_title = question.get("title", "Untitled Question")
        clean_title = html.unescape(raw_title)

        title_lbl = SelectableLabel(
            q_card,
            text=clean_title,
            font=(FONT_FAMILY, 16, "bold"),
            text_color=COLOR_TEXT_PRIMARY,
            bg_color=COLOR_BG_CARD,
            padx=4,
            pady=2
        )
        title_lbl.pack(fill="x", padx=18, pady=(18, 10))

        # Meta Row 1: Score, Views, Date, Author
        meta_row1 = ctk.CTkFrame(q_card, fg_color="transparent")
        meta_row1.pack(fill="x", padx=20, pady=(0, 8))

        score = question.get("score", 0)
        view_count = question.get("view_count", 0)
        created_ts = question.get("creation_date", 0)
        created_str = datetime.fromtimestamp(created_ts).strftime("%b %d, %Y %H:%M") if created_ts else ""
        owner = question.get("owner", {})
        author = owner.get("display_name", "Anonymous")
        rep = owner.get("reputation", 0)
        link = question.get("link", "")
        q_id = question.get("question_id", 0)

        # Score badge
        score_color = COLOR_SUCCESS if score > 0 else (COLOR_TEXT_MUTED if score == 0 else "#ef4444")
        s_lbl = ctk.CTkLabel(
            meta_row1,
            text=f"▲ {score}",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"),
            text_color=score_color
        )
        s_lbl.pack(side="left", padx=(0, 12))

        # Views
        v_lbl = ctk.CTkLabel(
            meta_row1,
            text=f"👁 {view_count:,} views",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            text_color=COLOR_TEXT_MUTED
        )
        v_lbl.pack(side="left", padx=(0, 12))

        # Date
        d_lbl = ctk.CTkLabel(
            meta_row1,
            text=f"📅 {created_str}",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            text_color=COLOR_TEXT_MUTED
        )
        d_lbl.pack(side="left", padx=(0, 12))

        # Author Pill
        a_lbl = ctk.CTkLabel(
            meta_row1,
            text=f"👤 {author} ({rep:,} rep)",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"),
            text_color=COLOR_TEXT_SECONDARY
        )
        a_lbl.pack(side="left", padx=(0, 12))

        # Meta Row 2: Action Toolbar (Bookmark, Copy Question, Copy Link, Browser)
        action_row = ctk.CTkFrame(q_card, fg_color="transparent")
        action_row.pack(fill="x", padx=20, pady=(0, 12))

        # Bookmark Button
        is_bookmarked = self.bookmark_mgr.is_bookmarked(q_id)
        bm_text = "★ Saved" if is_bookmarked else "☆ Save"
        bm_fg = COLOR_BOOKMARK if is_bookmarked else COLOR_BG_CARD_ACTIVE
        bm_txt_color = "#ffffff" if is_bookmarked else COLOR_TEXT_PRIMARY

        self.bm_btn = ctk.CTkButton(
            action_row,
            text=bm_text,
            font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
            width=78,
            height=26,
            corner_radius=6,
            fg_color=bm_fg,
            hover_color=COLOR_BOOKMARK_HOVER if is_bookmarked else COLOR_BG_CARD_HOVER,
            text_color=bm_txt_color,
            command=lambda: self.toggle_bookmark(question, language)
        )
        self.bm_btn.pack(side="left", padx=(0, 8))

        # Copy Question Button
        copy_q_btn = ctk.CTkButton(
            action_row,
            text="📋 Copy Question",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
            width=115,
            height=26,
            corner_radius=6,
            fg_color=COLOR_BG_CARD_ACTIVE,
            hover_color=COLOR_BG_CARD_HOVER,
            text_color=COLOR_TEXT_PRIMARY
        )
        copy_q_btn.configure(command=lambda btn=copy_q_btn, q=question: self.copy_question_to_clipboard(q, btn))
        copy_q_btn.pack(side="left", padx=(0, 8))

        # Copy Link Button
        if link:
            copy_link_btn = ctk.CTkButton(
                action_row,
                text="🔗 Copy Link",
                font=ctk.CTkFont(family=FONT_FAMILY, size=11),
                width=88,
                height=26,
                corner_radius=6,
                fg_color=COLOR_BG_CARD_ACTIVE,
                hover_color=COLOR_BG_CARD_HOVER,
                text_color=COLOR_TEXT_PRIMARY,
                command=lambda btn=action_row, u=link: self.copy_link_to_clipboard(u)
            )
            copy_link_btn.pack(side="left", padx=(0, 8))

            # Open in Browser button
            link_btn = ctk.CTkButton(
                action_row,
                text="🌐 Browser",
                font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
                width=80,
                height=26,
                corner_radius=6,
                fg_color=COLOR_BG_CARD_ACTIVE,
                hover_color=COLOR_BG_CARD_HOVER,
                text_color=COLOR_TEXT_PRIMARY,
                command=lambda: webbrowser.open(link)
            )
            link_btn.pack(side="right")

        # Tags Row
        tags = question.get("tags", [])
        if tags:
            tags_row = ctk.CTkFrame(q_card, fg_color="transparent")
            tags_row.pack(fill="x", padx=20, pady=(0, 12))

            for tag in tags:
                t_lbl = ctk.CTkLabel(
                    tags_row,
                    text=f" {tag} ",
                    font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
                    fg_color=COLOR_BG_TAG,
                    text_color=COLOR_TEXT_TAG,
                    corner_radius=4
                )
                t_lbl.pack(side="left", padx=(0, 6))

        # Divider
        divider = ctk.CTkFrame(q_card, height=1, fg_color=COLOR_BORDER)
        divider.pack(fill="x", padx=20, pady=(2, 14))

        # Question Body (Selectable Rich View with inline tags & code blocks)
        body_html = question.get("body", "<p>No body text</p>")
        rich_body = RichContentView(q_card, html_content=body_html, wraplength=660, bg_color=COLOR_BG_CARD)
        rich_body.pack(fill="x", expand=True, padx=20, pady=(0, 14))

        # Question Comments Section
        comment_count = question.get("comment_count", 0)
        self.render_comments_accordion(q_card, item_id=q_id, comment_count=comment_count, item_type="question")

        # 2. Answers Container Frame
        self.answers_container = ctk.CTkFrame(self, fg_color="transparent")
        self.answers_container.pack(fill="x", padx=16, pady=(8, 20))

        # Loading placeholder for answers
        loading_ans_lbl = ctk.CTkLabel(
            self.answers_container,
            text="⏳ Loading answers...",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
            text_color=COLOR_TEXT_MUTED
        )
        loading_ans_lbl.pack(pady=16)

    def toggle_bookmark(self, question: Dict[str, Any], language: str):
        """Toggle bookmark state and update UI button."""
        now_bookmarked = self.bookmark_mgr.toggle_bookmark(question, language)
        if now_bookmarked:
            self.bm_btn.configure(
                text="★ Saved",
                fg_color=COLOR_BOOKMARK,
                hover_color=COLOR_BOOKMARK_HOVER,
                text_color="#ffffff"
            )
        else:
            self.bm_btn.configure(
                text="☆ Save",
                fg_color=COLOR_BG_CARD_ACTIVE,
                hover_color=COLOR_BG_CARD_HOVER,
                text_color=COLOR_TEXT_PRIMARY
            )

    def copy_link_to_clipboard(self, url: str):
        """Copy question link to clipboard."""
        try:
            self.clipboard_clear()
            self.clipboard_append(url)
            self.update()
        except Exception as e:
            print(f"Error copying link: {e}")

    def display_answers(self, answers_list: List[Dict[str, Any]]):
        """Render answers list."""
        self.current_answers = answers_list

        for child in self.answers_container.winfo_children():
            child.destroy()

        if not answers_list:
            no_ans_card = ctk.CTkFrame(
                self.answers_container,
                fg_color=COLOR_BG_CARD,
                border_color=COLOR_BORDER,
                border_width=1,
                corner_radius=10
            )
            no_ans_card.pack(fill="x", pady=8)

            lbl = ctk.CTkLabel(
                no_ans_card,
                text="💭 No answers available for this question yet.",
                font=ctk.CTkFont(family=FONT_FAMILY, size=13),
                text_color=COLOR_TEXT_MUTED
            )
            lbl.pack(pady=20)
            return

        # Answers Section Header
        hdr_frame = ctk.CTkFrame(self.answers_container, fg_color="transparent")
        hdr_frame.pack(fill="x", pady=(4, 10))

        ans_count_lbl = ctk.CTkLabel(
            hdr_frame,
            text=f"💡 Answers ({len(answers_list)})",
            font=ctk.CTkFont(family=FONT_FAMILY, size=16, weight="bold"),
            text_color=COLOR_TEXT_PRIMARY
        )
        ans_count_lbl.pack(side="left")

        # Sort answers: accepted first, then by score descending
        sorted_answers = sorted(
            answers_list,
            key=lambda a: (1 if a.get("is_accepted") else 0, a.get("score", 0)),
            reverse=True
        )

        # Render each answer
        for idx, ans in enumerate(sorted_answers, 1):
            self.render_answer_card(self.answers_container, ans, idx)

    def render_answer_card(self, parent, ans_data: Dict[str, Any], index: int):
        """Render a single answer card with accepted banner, copy button, and selectable rich body."""
        is_accepted = ans_data.get("is_accepted", False)
        score = ans_data.get("score", 0)
        owner = ans_data.get("owner", {})
        author = owner.get("display_name", "Anonymous")
        rep = owner.get("reputation", 0)
        created_ts = ans_data.get("creation_date", 0)
        created_str = datetime.fromtimestamp(created_ts).strftime("%b %d, %Y %H:%M") if created_ts else ""
        ans_id = ans_data.get("answer_id", 0)
        comment_count = ans_data.get("comment_count", 0)

        border_color = COLOR_BORDER_ACCEPTED if is_accepted else COLOR_BORDER
        border_width = 2 if is_accepted else 1

        card = ctk.CTkFrame(
            parent,
            fg_color=COLOR_BG_CARD,
            border_color=border_color,
            border_width=border_width,
            corner_radius=12
        )
        card.pack(fill="x", pady=8)

        # Top Accepted Solution Banner
        if is_accepted:
            banner = ctk.CTkFrame(
                card,
                fg_color=COLOR_ACCEPTED_BANNER_BG,
                corner_radius=8,
                height=34
            )
            banner.pack(fill="x", padx=12, pady=(12, 4))
            banner.pack_propagate(False)

            b_icon = ctk.CTkLabel(
                banner,
                text="✓ ACCEPTED SOLUTION",
                font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
                text_color=COLOR_SUCCESS
            )
            b_icon.pack(side="left", padx=12)

            b_desc = ctk.CTkLabel(
                banner,
                text="• Verified and accepted by the question author",
                font=ctk.CTkFont(family=FONT_FAMILY, size=11),
                text_color=COLOR_TEXT_SECONDARY
            )
            b_desc.pack(side="left")

        # Answer Header Row
        hdr = ctk.CTkFrame(card, fg_color="transparent")
        hdr.pack(fill="x", padx=18, pady=(12 if not is_accepted else 6, 8))

        # Answer #
        num_lbl = ctk.CTkLabel(
            hdr,
            text=f"Answer #{index}",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
            text_color=COLOR_TEXT_PRIMARY
        )
        num_lbl.pack(side="left", padx=(0, 12))

        # Score
        score_color = COLOR_SUCCESS if score > 0 else (COLOR_TEXT_MUTED if score == 0 else "#ef4444")
        s_lbl = ctk.CTkLabel(
            hdr,
            text=f"▲ {score}",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"),
            text_color=score_color
        )
        s_lbl.pack(side="left", padx=(0, 12))

        # Copy Answer Button
        copy_ans_btn = ctk.CTkButton(
            hdr,
            text="📋 Copy Answer",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
            width=105,
            height=24,
            corner_radius=6,
            fg_color=COLOR_BG_CARD_ACTIVE,
            hover_color=COLOR_BG_CARD_HOVER,
            text_color=COLOR_TEXT_PRIMARY
        )
        copy_ans_btn.configure(command=lambda btn=copy_ans_btn, ans=ans_data: self.copy_answer_to_clipboard(ans, btn))
        copy_ans_btn.pack(side="right", padx=(8, 0))

        # Author & Date
        by_lbl = ctk.CTkLabel(
            hdr,
            text=f"by {author} ({rep:,} rep) • {created_str}",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            text_color=COLOR_TEXT_SECONDARY
        )
        by_lbl.pack(side="right")

        # Divider
        divider = ctk.CTkFrame(card, height=1, fg_color=COLOR_BORDER)
        divider.pack(fill="x", padx=18, pady=(2, 10))

        # Answer Body (Selectable Rich Text)
        body_html = ans_data.get("body", "<p>No content</p>")
        rich_body = RichContentView(card, html_content=body_html, wraplength=660, bg_color=COLOR_BG_CARD)
        rich_body.pack(fill="x", expand=True, padx=18, pady=(0, 12))

        # Answer Comments
        self.render_comments_accordion(card, item_id=ans_id, comment_count=comment_count, item_type="answer")

    def copy_question_to_clipboard(self, question: Dict[str, Any], btn: ctk.CTkButton):
        """Copy full question title, metadata, and markdown body to clipboard."""
        try:
            raw_title = question.get("title", "Untitled Question")
            clean_title = html.unescape(raw_title)
            score = question.get("score", 0)
            views = question.get("view_count", 0)
            link = question.get("link", "")
            owner = question.get("owner", {})
            author = owner.get("display_name", "Anonymous")
            rep = owner.get("reputation", 0)
            body_html = question.get("body", "")
            body_md = html_to_markdown(body_html)

            header_lines = [f"# {clean_title}\n"]
            meta = f"👤 Author: {author} ({rep:,} rep) | ▲ Score: {score} | 👁 Views: {views:,}"
            header_lines.append(meta)
            if link:
                header_lines.append(f"🌐 Link: {link}")
            header_lines.append("\n---\n")
            header_lines.append(body_md)

            full_text = "\n".join(header_lines)

            self.clipboard_clear()
            self.clipboard_append(full_text)
            self.update()

            btn.configure(
                text="✓ Copied!",
                fg_color=COLOR_SUCCESS,
                text_color="#ffffff"
            )
            self.after(1800, lambda: self._reset_copy_btn(btn, "📋 Copy Question"))
        except Exception as e:
            print(f"Error copying question: {e}")

    def copy_answer_to_clipboard(self, ans_data: Dict[str, Any], btn: ctk.CTkButton):
        """Copy formatted answer markdown body to clipboard."""
        try:
            body_html = ans_data.get("body", "")
            body_md = html_to_markdown(body_html)

            self.clipboard_clear()
            self.clipboard_append(body_md)
            self.update()

            btn.configure(
                text="✓ Copied!",
                fg_color=COLOR_SUCCESS,
                text_color="#ffffff"
            )
            self.after(1800, lambda: self._reset_copy_btn(btn, "📋 Copy Answer"))
        except Exception as e:
            print(f"Error copying answer: {e}")

    def _reset_copy_btn(self, btn: ctk.CTkButton, text: str):
        try:
            btn.configure(
                text=text,
                fg_color=COLOR_BG_CARD_ACTIVE,
                text_color=COLOR_TEXT_PRIMARY
            )
        except Exception:
            pass

    def render_comments_accordion(self, parent_card, item_id: int, comment_count: int, item_type: str = "answer"):
        """Render collapsible comments drawer with in-place expansion (no scroll reset)."""
        if comment_count <= 0:
            return

        cache_key = f"{self.current_language}_{item_type}_{item_id}"

        comments_container = ctk.CTkFrame(parent_card, fg_color="transparent")
        comments_container.pack(fill="x", padx=18, pady=(4, 12))

        toggle_btn = ctk.CTkButton(
            comments_container,
            text=f"💬 Show Comments ({comment_count})",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
            width=145,
            height=24,
            corner_radius=6,
            fg_color=COLOR_BG_CARD_ACTIVE,
            hover_color=COLOR_BG_CARD_HOVER,
            text_color=COLOR_TEXT_SECONDARY,
            command=lambda: self.toggle_comments(item_id, item_type, cache_key, comment_count)
        )
        toggle_btn.pack(anchor="w", pady=(0, 4))
        self.comment_toggle_buttons[cache_key] = toggle_btn

        # Subframe where comments are inserted dynamically
        subframe = ctk.CTkFrame(comments_container, fg_color="transparent")
        subframe.pack(fill="x")
        self.comment_subframes[cache_key] = subframe

    def toggle_comments(self, item_id: int, item_type: str, cache_key: str, comment_count: int):
        """Toggle comment visibility smoothly in-place without reloading the whole page."""
        subframe = self.comment_subframes.get(cache_key)
        toggle_btn = self.comment_toggle_buttons.get(cache_key)
        if not subframe:
            return

        if cache_key in self.expanded_comments:
            # Collapse comments
            self.expanded_comments.remove(cache_key)
            for child in subframe.winfo_children():
                child.destroy()
            if toggle_btn:
                toggle_btn.configure(text=f"💬 Show Comments ({comment_count})")
        else:
            # Expand comments
            self.expanded_comments.add(cache_key)
            if toggle_btn:
                toggle_btn.configure(text=f"▲ Hide Comments ({comment_count})")

            # Check if comments already cached
            if cache_key in self.comments_data:
                self._populate_comments_in_subframe(subframe, self.comments_data[cache_key])
            else:
                # Show loading placeholder inside subframe and fetch
                loading_lbl = ctk.CTkLabel(
                    subframe,
                    text="⏳ Loading comments...",
                    font=ctk.CTkFont(family=FONT_FAMILY, size=11),
                    text_color=COLOR_TEXT_MUTED
                )
                loading_lbl.pack(anchor="w", padx=10, pady=4)
                self.on_fetch_comments(item_id, self.current_language, item_type)

    def _populate_comments_in_subframe(self, subframe: ctk.CTkFrame, comments: List[Dict[str, Any]]):
        """Populate comments into their dedicated subframe."""
        for child in subframe.winfo_children():
            child.destroy()

        if not comments:
            lbl = ctk.CTkLabel(
                subframe,
                text="No comments found.",
                font=ctk.CTkFont(family=FONT_FAMILY, size=11),
                text_color=COLOR_TEXT_MUTED
            )
            lbl.pack(anchor="w", padx=10, pady=4)
            return

        for c in comments:
            self.render_comment_item(subframe, c)

    def set_comments(self, item_id: int, language: str, item_type: str, comments: List[Dict[str, Any]]):
        """Store comments and populate them smoothly in-place."""
        cache_key = f"{language}_{item_type}_{item_id}"
        self.comments_data[cache_key] = comments

        subframe = self.comment_subframes.get(cache_key)
        if subframe and cache_key in self.expanded_comments:
            self._populate_comments_in_subframe(subframe, comments)

    def render_comment_item(self, parent, comment_dict: Dict[str, Any]):
        """Render an individual comment pill with selectable text."""
        c_body = html.unescape(comment_dict.get("body", ""))
        c_owner = comment_dict.get("owner", {})
        c_author = c_owner.get("display_name", "Anonymous")
        c_score = comment_dict.get("score", 0)
        c_ts = comment_dict.get("creation_date", 0)
        c_date = datetime.fromtimestamp(c_ts).strftime("%b %d, %Y") if c_ts else ""

        c_frame = ctk.CTkFrame(
            parent,
            fg_color=COLOR_BG_SIDEBAR,
            border_color=COLOR_BORDER,
            border_width=1,
            corner_radius=6
        )
        c_frame.pack(fill="x", pady=3, padx=(10, 0))

        # Selectable Comment Text
        txt_lbl = SelectableLabel(
            c_frame,
            text=c_body,
            font=(FONT_FAMILY, 11),
            text_color=COLOR_TEXT_PRIMARY,
            bg_color=COLOR_BG_SIDEBAR,
            padx=8,
            pady=4
        )
        txt_lbl.pack(fill="x", padx=4, pady=(4, 2))

        # Meta
        meta_frame = ctk.CTkFrame(c_frame, fg_color="transparent")
        meta_frame.pack(fill="x", padx=10, pady=(0, 6))

        score_txt = f"▲ {c_score} • " if c_score > 0 else ""
        meta_lbl = ctk.CTkLabel(
            meta_frame,
            text=f"{score_txt}👤 {c_author} • {c_date}",
            font=ctk.CTkFont(family=FONT_FAMILY, size=10),
            text_color=COLOR_TEXT_MUTED
        )
        meta_lbl.pack(side="left")

    def refresh_view(self):
        """Re-render current question and answers when theme changes."""
        if self.current_question:
            self.load_question(self.current_question, self.current_language)
            if self.current_answers:
                self.display_answers(self.current_answers)
