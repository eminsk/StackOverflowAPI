"""
Stack Overflow Search Pro 2.0
Lightweight, modern desktop search client built with CustomTkinter.
"""

import sys
import os
import ctypes

# Set Windows AppUserModelID so taskbar grouping & icon work cleanly
MYAPPID = "stackoverflow.search.pro.customtkinter.2.0"
try:
    if sys.platform == "win32":
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(MYAPPID)
except Exception:
    pass

from src.ui.app import StackOverflowApp


def main():
    """Application entrypoint."""
    app = StackOverflowApp()
    app.mainloop()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        error_text = traceback.format_exc()
        print(f"Application crash: {error_text}", file=sys.stderr)
        with open("crash_log.txt", "w", encoding="utf-8") as f:
            f.write(error_text)
        
        try:
            if sys.platform == "win32":
                ctypes.windll.user32.MessageBoxW(
                    0,
                    f"Application encountered an error:\n{str(e)}\n\nSee crash_log.txt for details.",
                    "Stack Overflow Search Pro Error",
                    0x10
                )
        except Exception:
            pass
        sys.exit(1)
