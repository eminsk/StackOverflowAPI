import sys
import requests
import json
import functools
import threading
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QLineEdit, QPushButton,
                             QTextBrowser, QComboBox, QSplitter, QFrame,
                             QGridLayout, QTabWidget, QScrollArea)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QThread
from PyQt6.QtGui import QFont, QIcon, QPixmap


class StackOverflowAPI:
    """Professional API handler with optimized memory usage and performance"""

    BASE_URLS = {
        'English': 'https://api.stackexchange.com/2.3',
        'Russian': 'https://api.stackexchange.com/2.3'
    }

    SITE_NAMES = {
        'English': 'stackoverflow',
        'Russian': 'ru.stackoverflow'
    }

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({'Accept-Encoding': 'gzip'})

    def search_questions(self, query, language='English', page=1, pagesize=10):
        """Search for questions using full-text search"""
        params = {
            'site': self.SITE_NAMES[language],
            'q': query,
            'order': 'desc',
            'sort': 'relevance',
            'filter': 'withbody',
            'page': page,
            'pagesize': pagesize
        }

        url = f"{self.BASE_URLS[language]}/search/advanced"

        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"items": [], "error": f"Request Error: {str(e)}"}

    def get_question_answers(self, question_id, language='English'):
        """Retrieve answers for a specific question"""
        params = {
            'site': self.SITE_NAMES[language],
            'filter': 'withbody',
            'order': 'desc',
            'sort': 'votes'
        }

        url = f"{self.BASE_URLS[language]}/questions/{question_id}/answers"

        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"items": [], "error": f"Request Error: {str(e)}"}


class SearchWorker(QThread):
    """Asynchronous search worker thread"""

    results_ready = pyqtSignal(dict, str, str)  # results, language, query

    def __init__(self, api, query, language):
        super().__init__()
        self.api = api
        self.query = query
        self.language = language

    def run(self):
        results = self.api.search_questions(self.query, self.language)
        self.results_ready.emit(results, self.language, self.query)


class AnswersWorker(QThread):
    """Asynchronous answers fetching worker"""

    answers_ready = pyqtSignal(dict, int, str)

    def __init__(self, api, question_id, language):
        super().__init__()
        self.api = api
        self.question_id = question_id
        self.language = language

    def run(self):
        answers = self.api.get_question_answers(self.question_id, self.language)
        self.answers_ready.emit(answers, self.question_id, self.language)


class StackOverflowGUI(QMainWindow):
    """Professional Stack Overflow search GUI with optimized architecture"""

    def __init__(self):
        super().__init__()
        self.api = StackOverflowAPI()
        self.search_threads = []
        self.answers_threads = []
        self.selected_question_id = None
        self.selected_language = None

        # Separate storage for each search query
        self.current_queries = {'English': '', 'Russian': ''}
        self.search_results = {'English': '', 'Russian': ''}
        self.question_cache = {'English': {}, 'Russian': {}}

        self.initUI()

    def initUI(self):
        """Initialize user interface with professional design"""
        self.setWindowTitle("Stack Overflow Bilingual Search - Professional Edition")
        self.setMinimumSize(1200, 800)

        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)

        # Search controls
        search_frame = QFrame()
        search_frame.setFrameShape(QFrame.Shape.StyledPanel)
        search_layout = QHBoxLayout(search_frame)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter your search query (e.g., 'pandas dataframe', 'python async')...")
        self.search_input.returnPressed.connect(self.perform_search)

        self.language_selector = QComboBox()
        self.language_selector.addItems(["Both", "English", "Russian"])

        search_button = QPushButton("🔍 Search")
        search_button.clicked.connect(self.perform_search)

        self.back_button = QPushButton("← Back to Results")
        self.back_button.clicked.connect(self.show_search_results)
        self.back_button.setVisible(False)

        search_layout.addWidget(QLabel("Query:"))
        search_layout.addWidget(self.search_input, 1)
        search_layout.addWidget(QLabel("Language:"))
        search_layout.addWidget(self.language_selector)
        search_layout.addWidget(search_button)
        search_layout.addWidget(self.back_button)

        # Split view for results and details
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Questions panel with tabs
        questions_widget = QWidget()
        questions_layout = QVBoxLayout(questions_widget)

        self.questions_tabs = QTabWidget()

        self.english_questions_browser = QTextBrowser()
        self.english_questions_browser.setOpenExternalLinks(False)
        self.english_questions_browser.anchorClicked.connect(
            lambda url: self.load_question(url.toString(), 'English'))

        self.russian_questions_browser = QTextBrowser()
        self.russian_questions_browser.setOpenExternalLinks(False)
        self.russian_questions_browser.anchorClicked.connect(
            lambda url: self.load_question(url.toString(), 'Russian'))

        self.questions_tabs.addTab(self.english_questions_browser, "🇬🇧 English Results")
        self.questions_tabs.addTab(self.russian_questions_browser, "🇷🇺 Russian Results")

        questions_layout.addWidget(self.questions_tabs)

        # Details panel
        details_widget = QWidget()
        details_layout = QVBoxLayout(details_widget)

        self.question_details_browser = QTextBrowser()
        self.answers_browser = QTextBrowser()

        details_splitter = QSplitter(Qt.Orientation.Vertical)

        question_frame = QFrame()
        question_layout = QVBoxLayout(question_frame)
        question_header = QLabel("📋 Question Details")
        question_header.setStyleSheet("font-weight: bold; font-size: 14px; padding: 5px;")
        question_layout.addWidget(question_header)
        question_layout.addWidget(self.question_details_browser)

        answers_frame = QFrame()
        answers_layout = QVBoxLayout(answers_frame)
        answers_header = QLabel("💡 Answers")
        answers_header.setStyleSheet("font-weight: bold; font-size: 14px; padding: 5px;")
        answers_layout.addWidget(answers_header)
        answers_layout.addWidget(self.answers_browser)

        details_splitter.addWidget(question_frame)
        details_splitter.addWidget(answers_frame)
        details_splitter.setSizes([300, 500])

        details_layout.addWidget(details_splitter)

        splitter.addWidget(questions_widget)
        splitter.addWidget(details_widget)
        splitter.setSizes([500, 700])

        main_layout.addWidget(search_frame)
        main_layout.addWidget(splitter, 1)

        self.statusBar().showMessage("Ready to search Stack Overflow")

        self.setCentralWidget(main_widget)
        self.apply_styles()

    def apply_styles(self):
        """Apply professional styling"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f8f9fa;
            }
            QWidget {
                background-color: #ffffff;
                color: #2c3e50;
            }
            QFrame {
                border-radius: 6px;
                background-color: #ffffff;
                border: 1px solid #dee2e6;
            }
            QLineEdit {
                padding: 10px;
                border: 2px solid #ced4da;
                border-radius: 5px;
                background-color: #ffffff;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 2px solid #0077cc;
                background-color: #f0f8ff;
            }
            QPushButton {
                background-color: #0077cc;
                color: #ffffff;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #0095ff;
            }
            QPushButton:pressed {
                background-color: #005fa3;
            }
            QTextBrowser {
                border: 1px solid #dee2e6;
                border-radius: 5px;
                background-color: #ffffff;
                padding: 5px;
                selection-background-color: #cce5ff;
            }
            QTabWidget::pane {
                border: 1px solid #dee2e6;
                border-radius: 5px;
                background-color: #ffffff;
            }
            QTabBar::tab {
                background-color: #e9ecef;
                color: #495057;
                padding: 10px 20px;
                margin-right: 3px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
                font-weight: 500;
            }
            QTabBar::tab:selected {
                background-color: #ffffff;
                border-bottom: 3px solid #0077cc;
            }
            QTabBar::tab:hover {
                background-color: #dee2e6;
            }
            QComboBox {
                padding: 10px;
                border: 2px solid #ced4da;
                border-radius: 5px;
                background-color: #ffffff;
                min-width: 120px;
            }
            QComboBox:focus {
                border: 2px solid #0077cc;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #ffffff;
                border: 1px solid #ced4da;
                selection-background-color: #cce5ff;
            }
            QLabel {
                color: #2c3e50;
                font-weight: 500;
            }
            QSplitter::handle {
                background-color: #ced4da;
            }
            QSplitter::handle:horizontal {
                width: 4px;
            }
            QSplitter::handle:vertical {
                height: 4px;
            }
            QStatusBar {
                background-color: #f8f9fa;
                color: #6c757d;
            }
        """)

    def perform_search(self):
        """Execute search with proper query handling"""
        query = self.search_input.text().strip()

        if not query:
            self.statusBar().showMessage("⚠️ Please enter a search query")
            return

        selected_language = self.language_selector.currentText()

        # Clear previous results completely
        self.english_questions_browser.clear()
        self.russian_questions_browser.clear()
        self.question_details_browser.clear()
        self.answers_browser.clear()
        self.back_button.setVisible(False)

        # Terminate existing threads
        for thread in self.search_threads:
            thread.terminate() if thread.isRunning() else None
            thread.wait()
        self.search_threads.clear()

        self.statusBar().showMessage(f"🔍 Searching for: '{query}'...")

        # Launch search threads based on language selection
        languages_to_search = ['English', 'Russian'] if selected_language == "Both" else [selected_language]

        for language in languages_to_search:
            # Store the current query for this language
            self.current_queries[language] = query
            self.search_results[language] = ""
            self.question_cache[language].clear()

            thread = SearchWorker(self.api, query, language)
            thread.results_ready.connect(self.handle_search_results)
            thread.start()
            self.search_threads.append(thread)

    def handle_search_results(self, results, language, query):
        """Process and display search results with query validation"""
        # Verify this result matches the current query for this language
        if query != self.current_queries.get(language, ''):
            return  # Ignore outdated results

        if "error" in results:
            error_html = f"""
            <html><body style='font-family: Arial, sans-serif; padding: 20px;'>
                <h3 style='color: #dc3545;'>❌ Error</h3>
                <p style='color: #6c757d;'>{results['error']}</p>
            </body></html>
            """
            self.search_results[language] = error_html
            browser = self.english_questions_browser if language == "English" else self.russian_questions_browser
            browser.setHtml(error_html)
            return

        questions = results.get("items", [])

        if not questions:
            no_results_html = f"""
            <html><body style='font-family: Arial, sans-serif; padding: 20px; text-align: center;'>
                <h3 style='color: #6c757d;'>🔍 No results found</h3>
                <p style='color: #adb5bd;'>Try different keywords or check your query: <b>"{query}"</b></p>
            </body></html>
            """
            self.search_results[language] = no_results_html
            browser = self.english_questions_browser if language == "English" else self.russian_questions_browser
            browser.setHtml(no_results_html)
            self.statusBar().showMessage(f"No results found for '{query}' in {language}")
            return

        # Build HTML results
        html_parts = [f"""
        <html>
        <head>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; padding: 15px; }}
                .query-info {{ background: #e7f3ff; padding: 12px; border-radius: 6px; margin-bottom: 15px; border-left: 4px solid #0077cc; }}
                .question-card {{ background: #f8f9fa; padding: 15px; margin-bottom: 15px; border-left: 4px solid #0077cc; border-radius: 6px; transition: background 0.2s; }}
                .question-card:hover {{ background: #e9ecef; }}
                .question-title {{ color: #0077cc; text-decoration: none; font-size: 16px; font-weight: 600; }}
                .question-title:hover {{ color: #0095ff; text-decoration: underline; }}
                .meta {{ color: #6c757d; font-size: 13px; margin-top: 8px; }}
                .meta span {{ margin-right: 15px; }}
                .badge {{ display: inline-block; padding: 3px 8px; background: #e9ecef; border-radius: 3px; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="query-info">
                <strong>Query:</strong> "{query}" | <strong>Results:</strong> {len(questions)}
            </div>
        """]

        for question in questions:
            question_id = question.get("question_id")
            title = question.get("title", "Untitled")
            score = question.get("score", 0)
            answer_count = question.get("answer_count", 0)
            view_count = question.get("view_count", 0)
            created_date = datetime.fromtimestamp(question.get("creation_date", 0)).strftime("%Y-%m-%d")

            # Cache question
            self.question_cache[language][question_id] = question

            has_accepted = "✓" if question.get("is_answered", False) else ""

            html_parts.append(f"""
                <div class="question-card">
                    <h3 style='margin: 0 0 8px 0;'>
                        <a href='question:{question_id}' class='question-title'>{has_accepted} {title}</a>
                    </h3>
                    <div class="meta">
                        <span>⬆️ <strong>{score}</strong></span>
                        <span>💬 <strong>{answer_count}</strong> answers</span>
                        <span>👁️ {view_count} views</span>
                        <span class="badge">📅 {created_date}</span>
                    </div>
                </div>
            """)

        html_parts.append("</body></html>")
        result_html = "".join(html_parts)

        # Store and display
        self.search_results[language] = result_html
        browser = self.english_questions_browser if language == "English" else self.russian_questions_browser
        browser.setHtml(result_html)

        self.statusBar().showMessage(f"✅ Found {len(questions)} results for '{query}' in {language}")

    def show_search_results(self):
        """Restore cached search results"""
        self.english_questions_browser.setHtml(self.search_results.get('English', ''))
        self.russian_questions_browser.setHtml(self.search_results.get('Russian', ''))

        self.question_details_browser.clear()
        self.answers_browser.clear()
        self.back_button.setVisible(False)

        self.selected_question_id = None
        self.selected_language = None

        self.statusBar().showMessage("Returned to search results")

    def load_question(self, url, language):
        """Load and display question details with answers"""
        question_id = int(url.split(":")[-1])

        self.selected_question_id = question_id
        self.selected_language = language
        self.back_button.setVisible(True)

        question = self.question_cache[language].get(question_id)

        if not question:
            self.question_details_browser.setHtml("<p style='color: #dc3545;'>❌ Question not found in cache</p>")
            return

        # Format question details
        title = question.get("title", "Untitled")
        body = question.get("body", "<p>No content available</p>")
        score = question.get("score", 0)
        view_count = question.get("view_count", 0)
        answer_count = question.get("answer_count", 0)
        created_date = datetime.fromtimestamp(question.get("creation_date", 0)).strftime("%Y-%m-%d %H:%M")
        tags = question.get("tags", [])
        owner = question.get("owner", {})
        author = owner.get("display_name", "Anonymous")
        reputation = owner.get("reputation", 0)
        link = question.get("link", "#")

        question_html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; padding: 20px; line-height: 1.6; }}
                .title {{ color: #0077cc; margin-bottom: 15px; }}
                .meta {{ color: #6c757d; margin-bottom: 15px; font-size: 14px; background: #f8f9fa; padding: 12px; border-radius: 5px; }}
                .meta span {{ margin-right: 20px; }}
                .tags {{ margin-bottom: 15px; }}
                .tag {{ display: inline-block; background: #e1ecf4; color: #39739d; padding: 5px 10px; margin: 3px; border-radius: 4px; font-size: 12px; }}
                .body {{ border-top: 2px solid #dee2e6; padding-top: 20px; }}
                .external-link {{ display: inline-block; margin-top: 15px; padding: 8px 15px; background: #28a745; color: white; text-decoration: none; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <h2 class="title">{title}</h2>
            <div class="meta">
                <span>👤 <strong>{author}</strong> ({reputation:,} rep)</span>
                <span>⬆️ Score: <strong>{score}</strong></span>
                <span>👁️ Views: <strong>{view_count:,}</strong></span>
                <span>💬 Answers: <strong>{answer_count}</strong></span>
                <span>📅 {created_date}</span>
            </div>
            <div class="tags">
                {"".join([f"<span class='tag'>{tag}</span>" for tag in tags])}
            </div>
            <div class="body">
                {body}
            </div>
            <a href="{link}" class="external-link" target="_blank">🔗 View on Stack Overflow</a>
        </body>
        </html>
        """

        self.question_details_browser.setHtml(question_html)
        self.answers_browser.setHtml("<p style='color: #6c757d; padding: 20px;'>⏳ Loading answers...</p>")

        # Fetch answers
        for thread in self.answers_threads:
            thread.terminate() if thread.isRunning() else None
            thread.wait()
        self.answers_threads.clear()

        thread = AnswersWorker(self.api, question_id, language)
        thread.answers_ready.connect(self.display_answers)
        thread.start()
        self.answers_threads.append(thread)

    def display_answers(self, response, question_id, language):
        """Display answers for the selected question"""
        # Validate this response matches current selection
        if question_id != self.selected_question_id or language != self.selected_language:
            return

        if "error" in response:
            self.answers_browser.setHtml(f"<p style='color: #dc3545; padding: 20px;'>❌ Error: {response['error']}</p>")
            return

        answers = response.get("items", [])

        if not answers:
            self.answers_browser.setHtml("<p style='color: #6c757d; padding: 20px;'>💭 No answers available yet.</p>")
            return

        html_parts = ["""
        <html>
        <head>
            <style>
                body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; padding: 20px; line-height: 1.6; }
                .answer { background: #f8f9fa; padding: 20px; margin-bottom: 20px; border-radius: 6px; border-left: 4px solid #6c757d; }
                .answer.accepted { border-left-color: #28a745; background: #f0f8f4; }
                .answer-header { color: #495057; margin-bottom: 15px; font-size: 14px; }
                .accepted-badge { background: #28a745; color: white; padding: 4px 10px; border-radius: 4px; font-size: 12px; }
                .answer-body { border-top: 1px solid #dee2e6; padding-top: 15px; }
            </style>
        </head>
        <body>
        """]

        for i, answer in enumerate(answers, 1):
            is_accepted = answer.get("is_accepted", False)
            score = answer.get("score", 0)
            body = answer.get("body", "<p>No content</p>")
            created_date = datetime.fromtimestamp(answer.get("creation_date", 0)).strftime("%Y-%m-%d %H:%M")
            owner = answer.get("owner", {})
            author = owner.get("display_name", "Anonymous")
            reputation = owner.get("reputation", 0)

            accepted_class = "accepted" if is_accepted else ""
            accepted_badge = '<span class="accepted-badge">✓ ACCEPTED</span> ' if is_accepted else ''

            html_parts.append(f"""
                <div class="answer {accepted_class}">
                    <div class="answer-header">
                        {accepted_badge}
                        <strong>Answer #{i}</strong> by <strong>{author}</strong> ({reputation:,} rep)
                        <span style='margin-left: 20px;'>⬆️ Score: <strong>{score}</strong></span>
                        <span style='margin-left: 20px;'>📅 {created_date}</span>
                    </div>
                    <div class="answer-body">
                        {body}
                    </div>
                </div>
            """)

        html_parts.append("</body></html>")
        self.answers_browser.setHtml("".join(html_parts))


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Stack Overflow Search Pro")
    window = StackOverflowGUI()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()