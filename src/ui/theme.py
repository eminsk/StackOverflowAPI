"""
Theme & Styling Constants for Stack Overflow Search Pro
Modern, clean dark/light palette with StackOverflow brand accents.
CustomTkinter uses tuples (light_mode_color, dark_mode_color) for automatic theme switching.
"""

# Brand Colors (Light, Dark)
SO_ORANGE = "#F48024"
SO_ORANGE_HOVER = "#DA670B"
SO_ORANGE_LIGHT = "#FF7A00"
SO_ORANGE_BG = ("#FFF2E8", "#3D2410")

# Status & Badge Colors
COLOR_SUCCESS = "#10B981"         # Emerald Green (Accepted answer)
COLOR_SUCCESS_BG = ("#D1FAE5", "#064E3B")
COLOR_SUCCESS_FG = "#ffffff"

COLOR_PRIMARY = ("#2563eb", "#38bdf8")
COLOR_PRIMARY_HOVER = ("#1d4ed8", "#0284c7")
COLOR_PRIMARY_BG = ("#dbeafe", "#1e3a8a")

COLOR_WARNING = "#f59e0b"
COLOR_DANGER = "#ef4444"

# CustomTkinter Dual-Mode Color Tuples: (Light Mode, Dark Mode)
COLOR_BG_WINDOW = ("#f1f5f9", "#11111b")        # App background
COLOR_BG_SIDEBAR = ("#ffffff", "#181825")       # Left results panel & top bar
COLOR_BG_CARD = ("#ffffff", "#1e1e2e")          # Card background
COLOR_BG_CARD_HOVER = ("#f8fafc", "#28283d")    # Card hover background
COLOR_BG_CARD_ACTIVE = ("#e2e8f0", "#313244")   # Selected card background
COLOR_BG_INPUT = ("#f8fafc", "#181825")         # Text input bg
COLOR_BG_CODE = ("#f8fafc", "#181825")          # Code block background
COLOR_BG_CODE_HEADER = ("#e2e8f0", "#252538")   # Code header bar
COLOR_BG_TAG = ("#e0f2fe", "#2b2d42")           # Tag chip background
COLOR_BG_TAG_HOVER = ("#bae6fd", "#3b3e5b")     # Tag chip hover
COLOR_BG_BLOCKQUOTE = ("#f8fafc", "#252538")    # Blockquote background

COLOR_BORDER = ("#cbd5e1", "#313244")           # Standard border
COLOR_BORDER_FOCUS = (SO_ORANGE, SO_ORANGE)     # Active focus border
COLOR_BORDER_ACCEPTED = (COLOR_SUCCESS, COLOR_SUCCESS) # Accepted solution border

COLOR_TEXT_PRIMARY = ("#0f172a", "#f8fafc")     # Main headings & text
COLOR_TEXT_SECONDARY = ("#475569", "#94a3b8")   # Subheadings & meta
COLOR_TEXT_MUTED = ("#94a3b8", "#64748b")       # Dim timestamps & stats
COLOR_TEXT_TAG = ("#0284c7", "#7dd3fc")         # Tag text
COLOR_TEXT_LINK = ("#0284c7", "#38bdf8")        # Links

# Typography
FONT_FAMILY = "Segoe UI"
FONT_FAMILY_MONO = "Consolas"
