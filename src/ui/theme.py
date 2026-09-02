"""
Theme & Styling System for Stack Overflow Search Pro
Modern, clean, ergonomic dark/light palette with Stack Overflow brand accents.
CustomTkinter uses tuples (light_mode_color, dark_mode_color) for automatic theme switching.
"""

from typing import Tuple, Union
import tkinter.font as tkfont


# Brand Colors (Light, Dark)
SO_ORANGE = "#F48024"
SO_ORANGE_HOVER = "#DA670B"
SO_ORANGE_LIGHT = "#FF8F3D"
SO_ORANGE_BG = ("#FFF2E8", "#2E1B0D")

# Status & Badge Colors
COLOR_SUCCESS = "#10B981"               # Emerald Green
COLOR_SUCCESS_HOVER = "#059669"
COLOR_SUCCESS_BG = ("#D1FAE5", "#064E3B")
COLOR_SUCCESS_FG = "#ffffff"

COLOR_PRIMARY = ("#2563eb", "#38bdf8")
COLOR_PRIMARY_HOVER = ("#1d4ed8", "#0284c7")
COLOR_PRIMARY_BG = ("#dbeafe", "#1e3a8a")

COLOR_WARNING = "#f59e0b"
COLOR_DANGER = "#ef4444"
COLOR_DANGER_BG = ("#fee2e2", "#450a0a")

# Bookmark / Favorite Accents
COLOR_BOOKMARK = "#eab308"              # Gold Star
COLOR_BOOKMARK_HOVER = "#ca8a04"
COLOR_BOOKMARK_BG = ("#fef9c3", "#3d3209")

# Accepted Solution Banner
COLOR_ACCEPTED_BANNER_BG = ("#ecfdf5", "#083325")
COLOR_ACCEPTED_BANNER_BORDER = ("#10b981", "#059669")
COLOR_ACCEPTED_BANNER_TEXT = ("#065f46", "#6ee7b7")

# CustomTkinter Dual-Mode Color Tuples: (Light Mode, Dark Mode)
COLOR_BG_WINDOW = ("#f4f6f9", "#0f111a")        # Deep clean app background
COLOR_BG_SIDEBAR = ("#ffffff", "#161824")       # Left results panel & top bar
COLOR_BG_CARD = ("#ffffff", "#1d1f2e")          # Card surface background
COLOR_BG_CARD_HOVER = ("#f8fafc", "#25283c")    # Card hover background
COLOR_BG_CARD_ACTIVE = ("#eef2f6", "#2d3047")   # Selected card background
COLOR_BG_INPUT = ("#f8fafc", "#141620")         # Text input bg
COLOR_BG_CODE = ("#f8fafc", "#141620")          # Code block background
COLOR_BG_CODE_HEADER = ("#edf2f7", "#1e2130")   # Code header bar
COLOR_BG_BLOCKQUOTE = ("#f1f5f9", "#1b1d2b")    # Blockquote background

# Tag Chips
COLOR_BG_TAG = ("#e0f2fe", "#1e293b")           # Tag chip background
COLOR_BG_TAG_HOVER = ("#bae6fd", "#2c3e55")     # Tag chip hover
COLOR_BORDER_TAG = ("#bae6fd", "#334155")       # Tag chip border
COLOR_TEXT_TAG = ("#0284c7", "#7dd3fc")         # Tag text

# Borders
COLOR_BORDER = ("#d8e1ea", "#2b2e42")           # Standard border
COLOR_BORDER_FOCUS = (SO_ORANGE, SO_ORANGE)     # Active focus border
COLOR_BORDER_ACCEPTED = (COLOR_SUCCESS, COLOR_SUCCESS) # Accepted solution border

# Typography & Text Colors
COLOR_TEXT_PRIMARY = ("#0f172a", "#f8fafc")     # Main headings & primary text
COLOR_TEXT_SECONDARY = ("#334155", "#cbd5e1")   # Subheadings & readable meta
COLOR_TEXT_MUTED = ("#64748b", "#94a3b8")       # Dim timestamps, hints, icons
COLOR_TEXT_LINK = ("#0284c7", "#38bdf8")        # Clickable links

# Inline Code Styling
COLOR_INLINE_CODE_BG = ("#e2e8f0", "#282a3c")
COLOR_INLINE_CODE_FG = ("#c026d3", "#f472b6")   # Purple/pink distinctive code accent

# Typography Font Names
FONT_FAMILY = "Segoe UI"
FONT_FAMILY_MONO = "Consolas"


def resolve_color(color_spec: Union[str, Tuple[str, str]], mode: str = "dark") -> str:
    """Helper to safely resolve a dual-mode tuple or single hex color string."""
    if isinstance(color_spec, (tuple, list)):
        return color_spec[0] if mode == "light" else color_spec[1]
    return color_spec
