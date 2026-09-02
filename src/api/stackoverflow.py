"""
Stack Overflow API Client
High-performance client supporting English & Russian endpoints, pagination,
quota tracking, and robust error handling.
"""

from typing import Any, Dict, List, Optional
import requests


class StackOverflowAPI:
    """High-performance StackExchange API client with session management and gzip support."""

    BASE_URL = "https://api.stackexchange.com/2.3"

    SITE_MAP = {
        "English": "stackoverflow",
        "Russian": "ru.stackoverflow"
    }

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "Accept-Encoding": "gzip, deflate",
            "User-Agent": "StackOverflowSearchPro/2.1 (Windows; Python CustomTkinter Client)"
        })
        self.last_quota_remaining: Optional[int] = None
        self.last_quota_max: Optional[int] = None

    def search_questions(
        self,
        query: str,
        language: str = "English",
        sort: str = "relevance",
        page: int = 1,
        pagesize: int = 25
    ) -> Dict[str, Any]:
        """Search for questions using StackExchange search/advanced endpoint."""
        site = self.SITE_MAP.get(language, "stackoverflow")

        sort_param = "relevance"
        s_lower = sort.lower()
        if "vote" in s_lower:
            sort_param = "votes"
        elif "new" in s_lower or "creation" in s_lower:
            sort_param = "creation"
        elif "activ" in s_lower:
            sort_param = "activity"

        params = {
            "site": site,
            "q": query,
            "order": "desc",
            "sort": sort_param,
            "filter": "withbody",
            "page": page,
            "pagesize": pagesize
        }

        url = f"{self.BASE_URL}/search/advanced"
        try:
            resp = self.session.get(url, params=params, timeout=12)
            data = resp.json()

            if "quota_remaining" in data:
                self.last_quota_remaining = data["quota_remaining"]
                self.last_quota_max = data.get("quota_max")

            if resp.status_code != 200:
                error_msg = data.get("error_message", f"HTTP {resp.status_code}: {resp.reason}")
                return {"items": [], "error": error_msg}
            return data
        except requests.exceptions.Timeout:
            return {"items": [], "error": "Connection timed out. Please check your internet connection."}
        except requests.exceptions.RequestException as e:
            return {"items": [], "error": f"Network error: {str(e)}"}
        except Exception as e:
            return {"items": [], "error": f"Unexpected error: {str(e)}"}

    def get_question_by_id(self, question_id: int, language: str = "English") -> Dict[str, Any]:
        """Retrieve full details for a single question by ID."""
        site = self.SITE_MAP.get(language, "stackoverflow")
        params = {
            "site": site,
            "filter": "withbody"
        }
        url = f"{self.BASE_URL}/questions/{question_id}"
        try:
            resp = self.session.get(url, params=params, timeout=12)
            data = resp.json()
            if "quota_remaining" in data:
                self.last_quota_remaining = data["quota_remaining"]
                self.last_quota_max = data.get("quota_max")
            if resp.status_code != 200:
                return {"items": [], "error": data.get("error_message", f"HTTP {resp.status_code}: {resp.reason}")}
            return data
        except Exception as e:
            return {"items": [], "error": str(e)}

    def get_question_answers(self, question_id: int, language: str = "English") -> Dict[str, Any]:
        """Retrieve answers for a question sorted by score/acceptance."""
        site = self.SITE_MAP.get(language, "stackoverflow")
        params = {
            "site": site,
            "filter": "withbody",
            "order": "desc",
            "sort": "votes"
        }
        url = f"{self.BASE_URL}/questions/{question_id}/answers"
        try:
            resp = self.session.get(url, params=params, timeout=12)
            data = resp.json()
            if "quota_remaining" in data:
                self.last_quota_remaining = data["quota_remaining"]
                self.last_quota_max = data.get("quota_max")
            if resp.status_code != 200:
                return {"items": [], "error": data.get("error_message", f"HTTP {resp.status_code}: {resp.reason}")}
            return data
        except Exception as e:
            return {"items": [], "error": str(e)}

    def get_question_comments(self, question_id: int, language: str = "English") -> Dict[str, Any]:
        """Retrieve comments for a question."""
        site = self.SITE_MAP.get(language, "stackoverflow")
        params = {
            "site": site,
            "order": "asc",
            "sort": "creation",
            "filter": "withbody"
        }
        url = f"{self.BASE_URL}/questions/{question_id}/comments"
        try:
            resp = self.session.get(url, params=params, timeout=12)
            data = resp.json()
            if "quota_remaining" in data:
                self.last_quota_remaining = data["quota_remaining"]
                self.last_quota_max = data.get("quota_max")
            if resp.status_code != 200:
                return {"items": [], "error": data.get("error_message", f"HTTP {resp.status_code}: {resp.reason}")}
            return data
        except Exception as e:
            return {"items": [], "error": str(e)}

    def get_answer_comments(self, answer_id: int, language: str = "English") -> Dict[str, Any]:
        """Retrieve comments for an answer."""
        site = self.SITE_MAP.get(language, "stackoverflow")
        params = {
            "site": site,
            "order": "asc",
            "sort": "creation",
            "filter": "withbody"
        }
        url = f"{self.BASE_URL}/answers/{answer_id}/comments"
        try:
            resp = self.session.get(url, params=params, timeout=12)
            data = resp.json()
            if "quota_remaining" in data:
                self.last_quota_remaining = data["quota_remaining"]
                self.last_quota_max = data.get("quota_max")
            if resp.status_code != 200:
                return {"items": [], "error": data.get("error_message", f"HTTP {resp.status_code}: {resp.reason}")}
            return data
        except Exception as e:
            return {"items": [], "error": str(e)}
