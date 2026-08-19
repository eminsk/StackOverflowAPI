"""
Syntax Highlighter & HTML Parser Utility
Converts Stack Overflow HTML responses into structured UI blocks and provides Pygments syntax highlighting.
"""

import html
import re
from typing import List, Tuple, Dict, Any, Optional
from bs4 import BeautifulSoup, NavigableString, Tag
from pygments import lex
from pygments.lexers import get_lexer_by_name, guess_lexer, TextLexer
from pygments.token import (
    Token, Keyword, Name, Comment, String, Number, Operator, Punctuation, Generic
)


# Syntax Highlight Colors for Dark & Light themes
THEME_COLORS = {
    "dark": {
        "bg": "#1e1e2e",
        "fg": "#cdd6f4",
        "select_bg": "#45475a",
        "Keyword": "#cba6f7",       # Mauve / Purple
        "Keyword.Constant": "#fab387",# Peach
        "Keyword.Type": "#f9e2af",    # Yellow
        "Name": "#cdd6f4",          # Light text
        "Name.Function": "#89b4fa", # Blue
        "Name.Class": "#f9e2af",    # Yellow
        "Name.Builtin": "#89dceb",  # Sky
        "Name.Tag": "#f38ba8",      # Red
        "Name.Attribute": "#a6e3a1",# Green
        "String": "#a6e3a1",        # Green
        "String.Doc": "#6c7086",    # Slate
        "Number": "#fab387",        # Peach / Orange
        "Comment": "#6c7086",       # Overlay0
        "Comment.Single": "#6c7086",
        "Comment.Multiline": "#6c7086",
        "Operator": "#89dceb",      # Sky
        "Punctuation": "#9399b2",   # Overlay2
        "Generic.Heading": "#89b4fa",
        "Generic.Subheading": "#b4befe",
        "Generic.Deleted": "#f38ba8",
        "Generic.Inserted": "#a6e3a1",
        "Generic.Error": "#f38ba8",
        "Default": "#cdd6f4"
    },
    "light": {
        "bg": "#f8fafc",
        "fg": "#1e293b",
        "select_bg": "#cbd5e1",
        "Keyword": "#7c3aed",       # Violet
        "Keyword.Constant": "#ea580c",# Orange
        "Keyword.Type": "#d97706",    # Amber
        "Name": "#1e293b",          # Dark Slate
        "Name.Function": "#2563eb", # Royal Blue
        "Name.Class": "#d97706",    # Amber
        "Name.Builtin": "#0284c7",  # Sky Blue
        "Name.Tag": "#dc2626",      # Red
        "Name.Attribute": "#16a34a",# Green
        "String": "#16a34a",        # Emerald
        "String.Doc": "#64748b",    # Muted Slate
        "Number": "#ea580c",        # Orange
        "Comment": "#64748b",       # Muted Slate
        "Comment.Single": "#64748b",
        "Comment.Multiline": "#64748b",
        "Operator": "#0284c7",      # Sky Blue
        "Punctuation": "#475569",   # Slate
        "Generic.Heading": "#2563eb",
        "Generic.Subheading": "#4338ca",
        "Generic.Deleted": "#dc2626",
        "Generic.Inserted": "#16a34a",
        "Generic.Error": "#dc2626",
        "Default": "#1e293b"
    }
}


class CodeHighlighter:
    """Provides Pygments lexing and token color mapping for text widgets."""

    @staticmethod
    def get_lexer(code: str, lang_hint: Optional[str] = None):
        """Determine the best lexer for the given code and hint."""
        if lang_hint:
            # Clean hint e.g. lang-py, language-python, default
            clean_hint = re.sub(r'^(lang-|language-|default-)', '', lang_hint.strip().lower())
            # Common alias mapping
            alias_map = {
                "py": "python",
                "js": "javascript",
                "ts": "typescript",
                "cs": "csharp",
                "cpp": "cpp",
                "c++": "cpp",
                "sh": "bash",
                "zsh": "bash",
                "ps1": "powershell",
                "rb": "ruby",
                "rs": "rust",
                "golang": "go",
                "htm": "html",
                "yml": "yaml"
            }
            clean_hint = alias_map.get(clean_hint, clean_hint)
            try:
                return get_lexer_by_name(clean_hint), clean_hint.upper()
            except Exception:
                pass

        # Try guessing
        try:
            lexer = guess_lexer(code)
            return lexer, lexer.name
        except Exception:
            return TextLexer(), "CODE"

    @classmethod
    def tokenize(cls, code: str, lang_hint: Optional[str] = None) -> Tuple[List[Tuple[str, str]], str]:
        """
        Tokenize code using Pygments.
        Returns (tokens_list, display_language_name).
        Each token is (token_type_string, token_value).
        """
        lexer, lang_name = cls.get_lexer(code, lang_hint)
        try:
            raw_tokens = list(lex(code, lexer))
        except Exception:
            raw_tokens = [(Token.Text, code)]

        processed = []
        for t_type, t_val in raw_tokens:
            t_name = str(t_type)
            if t_name.startswith("Token."):
                t_name = t_name[6:]  # Strip 'Token.'
            processed.append((t_name, t_val))

        return processed, lang_name

    @classmethod
    def get_token_color(cls, token_type: str, mode: str = "dark") -> str:
        """Find matching color for token type hierarchically in current theme."""
        palette = THEME_COLORS.get(mode, THEME_COLORS["dark"])

        # Exact match
        if token_type in palette:
            return palette[token_type]

        # Hierarchical match (e.g. Keyword.Declaration -> Keyword)
        parts = token_type.split('.')
        while len(parts) > 1:
            parts.pop()
            parent = '.'.join(parts)
            if parent in palette:
                return palette[parent]

        return palette.get("Default", "#cdd6f4")


def clean_node_text(node) -> str:
    """Extract clean unescaped text from a BeautifulSoup node while preserving spacing."""
    if isinstance(node, NavigableString):
        return str(node)
    text = node.get_text()
    return html.unescape(text)


def parse_html_to_blocks(html_content: str) -> List[Dict[str, Any]]:
    """
    Parses Stack Overflow HTML into a structured list of blocks for CustomTkinter rendering.
    Block types:
    - 'paragraph': text with optional inline elements
    - 'code': raw code snippet, language
    - 'blockquote': quote text
    - 'list': list of string items (bulleted or numbered)
    - 'heading': header text and level
    - 'hr': horizontal rule
    """
    if not html_content:
        return []

    soup = BeautifulSoup(html_content, 'html.parser')
    blocks = []

    for child in soup.children:
        if isinstance(child, NavigableString):
            text = str(child).strip()
            if text:
                blocks.append({"type": "paragraph", "text": html.unescape(text)})
            continue

        if not isinstance(child, Tag):
            continue

        tag_name = child.name.lower()

        # 1. Code Block (<pre><code>...</code></pre> or <pre>...</pre>)
        if tag_name == "pre":
            code_tag = child.find("code")
            if code_tag:
                raw_code = code_tag.get_text()
                classes = child.get("class", []) + code_tag.get("class", [])
            else:
                raw_code = child.get_text()
                classes = child.get("class", [])

            # Extract language hint
            lang_hint = None
            for c in classes:
                if isinstance(c, str) and (c.startswith("lang-") or c.startswith("language-")):
                    lang_hint = c
                    break

            raw_code = html.unescape(raw_code.rstrip())
            blocks.append({
                "type": "code",
                "code": raw_code,
                "language": lang_hint
            })

        # 2. Blockquote
        elif tag_name == "blockquote":
            quote_text = clean_node_text(child).strip()
            if quote_text:
                blocks.append({
                    "type": "blockquote",
                    "text": quote_text
                })

        # 3. Lists (<ul>, <ol>)
        elif tag_name in ("ul", "ol"):
            items = []
            for li in child.find_all("li", recursive=False):
                li_text = clean_node_text(li).strip()
                if li_text:
                    items.append(li_text)
            if items:
                blocks.append({
                    "type": "list",
                    "ordered": tag_name == "ol",
                    "items": items
                })

        # 4. Headings (<h1>..<h6>)
        elif tag_name in ("h1", "h2", "h3", "h4", "h5", "h6"):
            h_text = clean_node_text(child).strip()
            if h_text:
                level = int(tag_name[1])
                blocks.append({
                    "type": "heading",
                    "level": level,
                    "text": h_text
                })

        # 5. Horizontal rule (<hr>)
        elif tag_name == "hr":
            blocks.append({"type": "hr"})

        # 6. Paragraph (<p>) or other tags
        else:
            # Check if there's a pre inside (e.g. <div><pre>...</pre></div>)
            pre_inside = child.find("pre")
            if pre_inside:
                # Recurse or parse direct children
                for sub in child.children:
                    if isinstance(sub, Tag) and sub.name == "pre":
                        c_tag = sub.find("code")
                        raw_c = c_tag.get_text() if c_tag else sub.get_text()
                        blocks.append({
                            "type": "code",
                            "code": html.unescape(raw_c.rstrip()),
                            "language": None
                        })
                    else:
                        sub_text = clean_node_text(sub).strip()
                        if sub_text:
                            blocks.append({"type": "paragraph", "text": sub_text})
            else:
                p_text = clean_node_text(child).strip()
                if p_text:
                    blocks.append({"type": "paragraph", "text": p_text})

    return blocks
