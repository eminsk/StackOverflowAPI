"""
Syntax Highlighter & HTML Parser Utility
Converts Stack Overflow HTML responses into structured UI blocks with rich inline formatting
(inline code chips, bold, italic, clickable links) and Pygments syntax highlighting.
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


# Syntax Highlight Colors for Dark & Light themes (VS Code / Catppuccin & GitHub Light styled)
THEME_COLORS = {
    "dark": {
        "bg": "#141620",
        "fg": "#cdd6f4",
        "select_bg": "#3e4259",
        "Keyword": "#cba6f7",          # Mauve / Purple
        "Keyword.Constant": "#fab387",   # Peach
        "Keyword.Type": "#f9e2af",       # Yellow
        "Name": "#cdd6f4",             # Clean light text
        "Name.Function": "#89b4fa",    # Sky Blue
        "Name.Class": "#f9e2af",       # Yellow
        "Name.Builtin": "#89dceb",     # Cyan
        "Name.Tag": "#f38ba8",         # Coral Red
        "Name.Attribute": "#a6e3a1",   # Green
        "String": "#a6e3a1",           # Emerald Green
        "String.Doc": "#7f849c",       # Muted Slate
        "Number": "#fab387",           # Peach / Orange
        "Comment": "#7f849c",          # Muted Slate
        "Comment.Single": "#7f849c",
        "Comment.Multiline": "#7f849c",
        "Operator": "#89dceb",         # Cyan
        "Punctuation": "#9399b2",      # Slate
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
        "Keyword": "#7c3aed",          # Violet
        "Keyword.Constant": "#ea580c",   # Orange
        "Keyword.Type": "#d97706",       # Amber
        "Name": "#1e293b",             # Dark Slate
        "Name.Function": "#2563eb",    # Royal Blue
        "Name.Class": "#d97706",       # Amber
        "Name.Builtin": "#0284c7",     # Sky Blue
        "Name.Tag": "#dc2626",         # Red
        "Name.Attribute": "#16a34a",   # Green
        "String": "#16a34a",           # Emerald
        "String.Doc": "#64748b",       # Muted Slate
        "Number": "#ea580c",           # Orange
        "Comment": "#64748b",          # Muted Slate
        "Comment.Single": "#64748b",
        "Comment.Multiline": "#64748b",
        "Operator": "#0284c7",         # Sky Blue
        "Punctuation": "#475569",      # Slate
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

    ALIAS_MAP = {
        "py": "python",
        "python3": "python",
        "js": "javascript",
        "jsx": "javascript",
        "ts": "typescript",
        "tsx": "typescript",
        "cs": "csharp",
        "cpp": "cpp",
        "c++": "cpp",
        "c": "c",
        "sh": "bash",
        "shell": "bash",
        "zsh": "bash",
        "ps1": "powershell",
        "rb": "ruby",
        "rs": "rust",
        "golang": "go",
        "htm": "html",
        "yml": "yaml",
        "json": "json",
        "sql": "sql",
        "css": "css",
        "scss": "scss",
        "dockerfile": "docker",
        "docker": "docker",
        "kt": "kotlin",
        "swift": "swift",
        "md": "markdown",
        "xml": "xml",
        "java": "java",
        "php": "php",
    }

    @classmethod
    def get_lexer(cls, code: str, lang_hint: Optional[str] = None):
        """Determine the best lexer for the given code and hint."""
        if lang_hint:
            clean_hint = re.sub(r'^(lang-|language-|default-)', '', lang_hint.strip().lower())
            clean_hint = cls.ALIAS_MAP.get(clean_hint, clean_hint)
            try:
                return get_lexer_by_name(clean_hint), clean_hint.upper()
            except Exception:
                pass

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
                t_name = t_name[6:]
            processed.append((t_name, t_val))

        return processed, lang_name

    @classmethod
    def get_token_color(cls, token_type: str, mode: str = "dark") -> str:
        """Find matching color for token type hierarchically in current theme."""
        palette = THEME_COLORS.get(mode, THEME_COLORS["dark"])

        if token_type in palette:
            return palette[token_type]

        parts = token_type.split('.')
        while len(parts) > 1:
            parts.pop()
            parent = '.'.join(parts)
            if parent in palette:
                return palette[parent]

        return palette.get("Default", "#cdd6f4")


def clean_node_text(node) -> str:
    """Extract clean unescaped text from a BeautifulSoup node."""
    if isinstance(node, NavigableString):
        return str(node)
    return html.unescape(node.get_text())


def extract_inline_segments(node) -> List[Tuple[str, str, Optional[str]]]:
    """
    Extract structured inline styled segments from a node.
    Returns a list of tuples: (text, tag_type, opt_url)
    tag_types: 'text', 'code_inline', 'bold', 'italic', 'link', 'kbd'
    """
    segments: List[Tuple[str, str, Optional[str]]] = []

    def _walk(item, current_tag="text", current_url=None):
        if isinstance(item, NavigableString):
            raw = str(item)
            if raw:
                segments.append((html.unescape(raw), current_tag, current_url))
            return

        if not isinstance(item, Tag):
            return

        tag_name = item.name.lower()
        if tag_name == "br":
            segments.append(("\n", "text", None))
            return

        next_tag = current_tag
        next_url = current_url

        if tag_name == "code":
            next_tag = "code_inline"
        elif tag_name in ("strong", "b"):
            next_tag = "bold"
        elif tag_name in ("em", "i"):
            next_tag = "italic"
        elif tag_name == "kbd":
            next_tag = "kbd"
        elif tag_name == "a":
            next_tag = "link"
            next_url = item.get("href", "")

        for child in item.children:
            _walk(child, next_tag, next_url)

    _walk(node)

    # Merge consecutive segments with the exact same tag and url for efficiency
    merged: List[Tuple[str, str, Optional[str]]] = []
    for text, tag, url in segments:
        if not text:
            continue
        if merged and merged[-1][1] == tag and merged[-1][2] == url:
            merged[-1] = (merged[-1][0] + text, tag, url)
        else:
            merged.append((text, tag, url))

    return merged


def extract_text_preview(html_content: str, max_chars: int = 130) -> str:
    """Extract a clean 1-line plain text teaser excerpt from HTML content."""
    if not html_content:
        return ""
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        # Remove code blocks so they don't clutter the card preview
        for tag in soup.find_all(['pre', 'code']):
            tag.decompose()
        text = soup.get_text()
        text = " ".join(text.split())
        text = html.unescape(text)
        if len(text) > max_chars:
            return text[:max_chars].rstrip() + "..."
        return text
    except Exception:
        return ""


def parse_html_to_blocks(html_content: str) -> List[Dict[str, Any]]:
    """
    Parses Stack Overflow HTML into a structured list of blocks with rich inline formatting.
    Block types:
    - 'paragraph': text, segments
    - 'code': raw code snippet, language
    - 'blockquote': text, segments
    - 'list': list of items (each item has text & segments), ordered (bool)
    - 'heading': level (int), text, segments
    - 'hr': horizontal divider
    """
    if not html_content:
        return []

    soup = BeautifulSoup(html_content, 'html.parser')
    blocks = []

    for child in soup.children:
        if isinstance(child, NavigableString):
            raw = str(child).strip()
            if raw:
                text_clean = html.unescape(raw)
                blocks.append({
                    "type": "paragraph",
                    "text": text_clean,
                    "segments": [(text_clean, "text", None)]
                })
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
                    "text": quote_text,
                    "segments": extract_inline_segments(child)
                })

        # 3. Lists (<ul>, <ol>)
        elif tag_name in ("ul", "ol"):
            items = []
            item_segments = []
            for li in child.find_all("li", recursive=False):
                li_text = clean_node_text(li).strip()
                if li_text:
                    items.append(li_text)
                    item_segments.append(extract_inline_segments(li))
            if items:
                blocks.append({
                    "type": "list",
                    "ordered": tag_name == "ol",
                    "items": items,
                    "item_segments": item_segments
                })

        # 4. Headings (<h1>..<h6>)
        elif tag_name in ("h1", "h2", "h3", "h4", "h5", "h6"):
            h_text = clean_node_text(child).strip()
            if h_text:
                level = int(tag_name[1])
                blocks.append({
                    "type": "heading",
                    "level": level,
                    "text": h_text,
                    "segments": extract_inline_segments(child)
                })

        # 5. Horizontal rule (<hr>)
        elif tag_name == "hr":
            blocks.append({"type": "hr"})

        # 6. Paragraph (<p>) or other wrappers
        else:
            pre_inside = child.find("pre")
            if pre_inside:
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
                            blocks.append({
                                "type": "paragraph",
                                "text": sub_text,
                                "segments": extract_inline_segments(sub)
                            })
            else:
                p_text = clean_node_text(child).strip()
                if p_text:
                    blocks.append({
                        "type": "paragraph",
                        "text": p_text,
                        "segments": extract_inline_segments(child)
                    })

    return blocks


def html_to_markdown(html_content: str) -> str:
    """
    Convert Stack Overflow HTML content into clean, readable Markdown text
    suitable for 1-click copying to clipboard.
    """
    blocks = parse_html_to_blocks(html_content)
    if not blocks:
        soup = BeautifulSoup(html_content or "", 'html.parser')
        return soup.get_text().strip()

    md_parts = []
    for b in blocks:
        b_type = b.get("type")
        if b_type == "heading":
            level = b.get("level", 2)
            md_parts.append(f"{'#' * level} {b.get('text', '')}\n")
        elif b_type == "paragraph":
            segments = b.get("segments")
            if segments:
                line = ""
                for seg_text, tag, url in segments:
                    if tag == "code_inline":
                        line += f"`{seg_text}`"
                    elif tag == "bold":
                        line += f"**{seg_text}**"
                    elif tag == "italic":
                        line += f"*{seg_text}*"
                    elif tag == "link" and url:
                        line += f"[{seg_text}]({url})"
                    else:
                        line += seg_text
                md_parts.append(f"{line.strip()}\n")
            else:
                text = b.get("text", "")
                if text:
                    md_parts.append(f"{text}\n")
        elif b_type == "code":
            code = b.get("code", "")
            lang = b.get("language") or ""
            if lang.startswith("lang-") or lang.startswith("language-"):
                lang = re.sub(r'^(lang-|language-)', '', lang)
            md_parts.append(f"```{lang}\n{code}\n```\n")
        elif b_type == "blockquote":
            text = b.get("text", "")
            quoted = "\n".join(f"> {line}" for line in text.splitlines())
            md_parts.append(f"{quoted}\n")
        elif b_type == "list":
            items = b.get("items", [])
            ordered = b.get("ordered", False)
            for idx, item in enumerate(items, 1):
                prefix = f"{idx}." if ordered else "-"
                md_parts.append(f"{prefix} {item}")
            md_parts.append("")
        elif b_type == "hr":
            md_parts.append("---\n")

    return "\n".join(md_parts).strip()
