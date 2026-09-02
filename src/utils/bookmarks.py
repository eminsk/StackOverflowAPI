"""
Bookmarks Storage & Management Utility
Provides persistent offline bookmark storage for questions in JSON format.
Thread-safe, robust error handling with automatic fallback to local directory.
"""

import os
import sys
import json
import time
import threading
from typing import Dict, Any, List, Optional, Callable


class BookmarkManager:
    """Manages saved Stack Overflow questions with JSON persistence and change notification."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(BookmarkManager, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._data_lock = threading.Lock()
        self._change_listeners: List[Callable[[], None]] = []
        self._file_path = self._resolve_storage_path()
        self._bookmarks: Dict[str, Dict[str, Any]] = self._load()

    def _resolve_storage_path(self) -> str:
        """Resolve persistent storage path in AppData or local directory."""
        try:
            if sys.platform == "win32":
                app_data = os.environ.get("APPDATA")
                if app_data:
                    base_dir = os.path.join(app_data, "StackOverflowSearchPro")
                    os.makedirs(base_dir, exist_ok=True)
                    return os.path.join(base_dir, "bookmarks.json")
            # Fallback to user home or local directory
            home_dir = os.path.expanduser("~")
            base_dir = os.path.join(home_dir, ".stackoverflow_search_pro")
            os.makedirs(base_dir, exist_ok=True)
            return os.path.join(base_dir, "bookmarks.json")
        except Exception:
            return "bookmarks.json"

    def _load(self) -> Dict[str, Dict[str, Any]]:
        """Load bookmarks from file with fail-safe error handling."""
        if not os.path.exists(self._file_path):
            return {}
        try:
            with open(self._file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
        except Exception as e:
            print(f"Warning: Failed to load bookmarks: {e}")
        return {}

    def _save(self):
        """Save bookmarks atomically to disk."""
        temp_path = f"{self._file_path}.tmp"
        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(self._bookmarks, f, indent=2, ensure_ascii=False)
            if os.path.exists(self._file_path):
                os.replace(temp_path, self._file_path)
            else:
                os.rename(temp_path, self._file_path)
        except Exception as e:
            print(f"Warning: Failed to save bookmarks: {e}")
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass

    def add_listener(self, listener: Callable[[], None]):
        """Register a callback called whenever bookmarks change."""
        if listener not in self._change_listeners:
            self._change_listeners.append(listener)

    def remove_listener(self, listener: Callable[[], None]):
        """Unregister a change listener."""
        if listener in self._change_listeners:
            self._change_listeners.remove(listener)

    def _notify_listeners(self):
        for listener in list(self._change_listeners):
            try:
                listener()
            except Exception as e:
                print(f"Error in bookmark change listener: {e}")

    def is_bookmarked(self, question_id: int) -> bool:
        """Check if a question is currently bookmarked."""
        with self._data_lock:
            return str(question_id) in self._bookmarks

    def toggle_bookmark(self, question_data: Dict[str, Any], language: str = "English") -> bool:
        """Toggle bookmark state. Returns True if now bookmarked, False if removed."""
        q_id = str(question_data.get("question_id", 0))
        if not q_id or q_id == "0":
            return False

        with self._data_lock:
            if q_id in self._bookmarks:
                del self._bookmarks[q_id]
                now_bookmarked = False
            else:
                entry = dict(question_data)
                entry["_language"] = language
                entry["_bookmarked_at"] = time.time()
                self._bookmarks[q_id] = entry
                now_bookmarked = True
            self._save()

        self._notify_listeners()
        return now_bookmarked

    def add_bookmark(self, question_data: Dict[str, Any], language: str = "English") -> bool:
        """Save a question to bookmarks."""
        q_id = str(question_data.get("question_id", 0))
        if not q_id or q_id == "0":
            return False

        with self._data_lock:
            entry = dict(question_data)
            entry["_language"] = language
            entry["_bookmarked_at"] = time.time()
            self._bookmarks[q_id] = entry
            self._save()

        self._notify_listeners()
        return True

    def remove_bookmark(self, question_id: int) -> bool:
        """Remove a question from bookmarks."""
        q_id = str(question_id)
        with self._data_lock:
            if q_id in self._bookmarks:
                del self._bookmarks[q_id]
                self._save()
                removed = True
            else:
                removed = False

        if removed:
            self._notify_listeners()
        return removed

    def get_bookmark(self, question_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve a single bookmarked question."""
        with self._data_lock:
            return self._bookmarks.get(str(question_id))

    def get_all_bookmarks(self) -> List[Dict[str, Any]]:
        """Retrieve all bookmarks sorted by bookmark time (newest first)."""
        with self._data_lock:
            items = list(self._bookmarks.values())
        items.sort(key=lambda x: x.get("_bookmarked_at", 0), reverse=True)
        return items

    def get_bookmark_count(self) -> int:
        """Get total number of bookmarked questions."""
        with self._data_lock:
            return len(self._bookmarks)
