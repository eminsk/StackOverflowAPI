import sys
import ctypes
import uuid
from bs4 import BeautifulSoup
from pygments import highlight
from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.formatters import HtmlFormatter

import requests
import json
import functools
import threading
from datetime import datetime

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QLineEdit, QPushButton,
                             QTextBrowser, QComboBox, QSplitter, QFrame,
                             QGridLayout, QTabWidget, QScrollArea)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QThread, QUrl
from PyQt6.QtGui import QFont, QIcon, QPixmap, QDesktopServices



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

    def get_answer_comments(self, answer_id, language='English'):
        """Retrieve comments for a specific answer"""
        params = {
            'site': self.SITE_NAMES[language],
            'order': 'desc',
            'sort': 'creation',
            'filter': 'default'
        }

        url = f"{self.BASE_URLS[language]}/answers/{answer_id}/comments"

        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"items": [], "error": f"Request Error: {str(e)}"}

    def get_question_comments(self, question_id, language='English'):
        """Retrieve comments for a specific question"""
        params = {
            'site': self.SITE_NAMES[language],
            'order': 'desc',
            'sort': 'creation',
            'filter': 'default'
        }

        url = f"{self.BASE_URLS[language]}/questions/{question_id}/comments"

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


class CommentsWorker(QThread):
    """Asynchronous comments fetching worker"""

    comments_ready = pyqtSignal(dict, int, str, str)  # comments, answer_id, language, comment_type

    def __init__(self, api, answer_id, language, comment_type='answer'):
        super().__init__()
        self.api = api
        self.answer_id = answer_id
        self.language = language
        self.comment_type = comment_type

    def run(self):
        if self.comment_type == 'answer':
            comments = self.api.get_answer_comments(self.answer_id, self.language)
        else:
            comments = self.api.get_question_comments(self.answer_id, self.language)
        self.comments_ready.emit(comments, self.answer_id, self.language, self.comment_type)


class StackOverflowGUI(QMainWindow):
    """Professional Stack Overflow search GUI with comments support"""

    def __init__(self):
        super().__init__()
        self.api = StackOverflowAPI()
        self.search_threads = []
        self.answers_threads = []
        self.comments_threads = []
        self.selected_question_id = None
        self.selected_language = None

        # Separate storage for each search query
        self.current_queries = {'English': '', 'Russian': ''}
        self.search_results = {'English': '', 'Russian': ''}
        self.question_cache = {'English': {}, 'Russian': {}}
        self.answers_cache = {}
        self.comments_cache = {}
        self.expanded_comments = set()  # Track which comments are expanded
        self.code_blocks_storage = {}   # Store raw code for copy functionality

        self.initUI()

    def initUI(self):
        """Initialize user interface with professional design"""
        self.setWindowTitle("Stack Overflow Search Pro")
        self.setMinimumSize(1280, 800)
        
        # Center window on screen
        self.center_window()

        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)

        # Search controls
        search_frame = QFrame()
        search_frame.setFrameShape(QFrame.Shape.StyledPanel)
        search_layout = QHBoxLayout(search_frame)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search Stack Overflow (e.g., 'pandas dataframe', 'python async')...")
        self.search_input.returnPressed.connect(self.perform_search)

        self.language_selector = QComboBox()
        self.language_selector.addItems(["Both", "English", "Russian"])

        search_button = QPushButton("🔍 Search")
        search_button.clicked.connect(self.perform_search)

        self.back_button = QPushButton("← Back to Results")
        self.back_button.setObjectName("back_button")
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
        self.question_details_browser.setOpenExternalLinks(False)
        self.question_details_browser.anchorClicked.connect(self.handle_link_click)

        self.answers_browser = QTextBrowser()
        self.answers_browser.setOpenExternalLinks(False)
        self.answers_browser.anchorClicked.connect(self.handle_link_click)

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

    def center_window(self):
        """Center the window on the screen"""
        from PyQt6.QtWidgets import QApplication
        screen = QApplication.primaryScreen().geometry()
        size = self.geometry()
        self.move(
            (screen.width() - size.width()) // 2,
            (screen.height() - size.height()) // 2
        )

    def handle_link_click(self, url):
        """Handle all link clicks - external, comments, etc."""
        url_str = url.toString()
        print(f"[DEBUG] Link clicked: {url_str}")
        print(f"[DEBUG] Code blocks in storage: {list(self.code_blocks_storage.keys())[:3]}...")

        # External link
        if url_str.startswith(('http://', 'https://')):
            QDesktopServices.openUrl(url)
            self.statusBar().showMessage(f"Opening: {url_str}")

        # Toggle comments for answer
        elif url_str.startswith('toggle_comments:'):
            answer_id = int(url_str.split(':')[1])
            self.toggle_comments(answer_id)

        # Toggle comments for question
        elif url_str.startswith('toggle_question_comments:'):
            question_id = int(url_str.split(':')[1])
            self.toggle_question_comments(question_id)

        # Copy code block
        elif url_str.startswith('copy_code:') or url_str.startswith('#copycode_'):
            # Handle both old and new format
            if url_str.startswith('#copycode_'):
                block_id = url_str.replace('#copycode_', '')
            else:
                block_id = url_str.split(':')[1]
            print(f"[DEBUG] Attempting copy with block_id: {block_id}")
            self.statusBar().showMessage(f"Attempting to copy block: {block_id}")
            if block_id in self.code_blocks_storage:
                content = self.code_blocks_storage[block_id]
                QApplication.clipboard().setText(content)
                self.statusBar().showMessage("✅ Code copied to clipboard!")
                print(f"[DEBUG] Successfully copied {len(content)} chars")
            else:
                self.statusBar().showMessage(f"❌ Error: Code block not found in memory ({block_id})")
                print(f"[DEBUG] Block {block_id} not found in storage")

    def toggle_comments(self, answer_id):
        """Toggle display of comments for an answer"""
        cache_key = f"{self.selected_language}_{answer_id}"

        # If comments are already expanded, collapse them
        if cache_key in self.expanded_comments:
            self.expanded_comments.remove(cache_key)
            self.render_answers()
            return

        # If comments are cached, just expand them
        if cache_key in self.comments_cache:
            self.expanded_comments.add(cache_key)
            self.render_answers()
            return

        # Otherwise, fetch comments
        self.statusBar().showMessage(f"Loading comments for answer {answer_id}...")

        for thread in self.comments_threads:
            thread.terminate() if thread.isRunning() else None
            thread.wait()
        self.comments_threads.clear()

        thread = CommentsWorker(self.api, answer_id, self.selected_language, 'answer')
        thread.comments_ready.connect(self.handle_comments)
        thread.start()
        self.comments_threads.append(thread)

    def toggle_question_comments(self, question_id):
        """Toggle display of comments for the question"""
        cache_key = f"{self.selected_language}_question_{question_id}"

        # If comments are already expanded, collapse them
        if cache_key in self.expanded_comments:
            self.expanded_comments.remove(cache_key)
            self.render_question()
            return

        # If comments are cached, just expand them
        if cache_key in self.comments_cache:
            self.expanded_comments.add(cache_key)
            self.render_question()
            return

        # Otherwise, fetch comments
        self.statusBar().showMessage(f"Loading comments for question {question_id}...")

        for thread in self.comments_threads:
            thread.terminate() if thread.isRunning() else None
            thread.wait()
        self.comments_threads.clear()

        thread = CommentsWorker(self.api, question_id, self.selected_language, 'question')
        thread.comments_ready.connect(self.handle_comments)
        thread.start()
        self.comments_threads.append(thread)

    def handle_comments(self, comments_data, item_id, language, comment_type):
        """Handle comments response and display them"""
        # Verify this matches current selection
        if language != self.selected_language:
            return

        if comment_type == 'question' and item_id != self.selected_question_id:
            return

        cache_key = f"{language}_{comment_type}_{item_id}" if comment_type == 'question' else f"{language}_{item_id}"

        if "error" in comments_data:
            self.statusBar().showMessage(f"Error loading comments: {comments_data['error']}")
            return

        # Cache comments
        self.comments_cache[cache_key] = comments_data.get("items", [])
        self.expanded_comments.add(cache_key)

        # Re-render to show comments
        if comment_type == 'question':
            self.render_question()
        else:
            self.render_answers()

        comment_count = len(self.comments_cache[cache_key])
        self.statusBar().showMessage(f"Loaded {comment_count} comments")

    def process_html_content(self, html_content):
        """Process HTML to highlight code and add copy buttons"""
        if not html_content:
            return html_content

        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Find all code blocks (pre > code or just pre)
            for pre in list(soup.find_all('pre')):
                code_tag = pre.find('code')
                
                # Get the raw HTML content and unescape it to preserve whitespace
                import html
                import re
                if code_tag:
                    # decode_contents() gets inner HTML
                    inner_html = code_tag.decode_contents()
                else:
                    inner_html = pre.decode_contents()
                
                # Remove HTML tags but preserve text content and whitespace
                # Use regex to strip tags while keeping all whitespace
                raw_code = re.sub(r'<[^>]+>', '', inner_html)
                # Unescape HTML entities like &lt; &gt; &amp; etc.
                raw_code = html.unescape(raw_code)
                
                # Detect language
                classes = pre.get('class', [])
                if code_tag:
                    classes.extend(code_tag.get('class', []))
                
                lexer = None
                for cls in classes:
                    if cls.startswith('lang-') or cls.startswith('language-'):
                        try:
                            lang = cls.split('-')[-1]
                            lexer = get_lexer_by_name(lang)
                            break
                        except:
                            pass
                
                if not lexer:
                    try:
                        lexer = guess_lexer(raw_code)
                    except:
                        lexer = get_lexer_by_name('text')
                
                # Formatter with dark style (monokai-like)
                # Use inline styles for spans
                formatter = HtmlFormatter(style='monokai', noclasses=True, nowrap=True)
                highlighted_html = highlight(raw_code, lexer, formatter)
                
                # Generate simple ID and store
                block_id = str(uuid.uuid4()).replace('-', '')
                self.code_blocks_storage[block_id] = raw_code
                
                # Build the complete table HTML as a string to avoid BeautifulSoup whitespace normalization
                # Escape raw_code for HTML display but preserve whitespace
                import html as html_module
                escaped_code = html_module.escape(raw_code)
                
                table_html = f'''
                <table width="100%" cellspacing="0" cellpadding="0" style="margin: 10px 0; border: 1px solid #444; background-color: #272822; border-radius: 6px; border-collapse: separate;">
                    <tr>
                        <td style="background-color: #383838; padding: 6px 12px; border-bottom: 1px solid #444; border-top-left-radius: 6px; border-top-right-radius: 6px;">
                            <table width="100%" cellspacing="0" cellpadding="0" style="background-color: transparent;">
                                <tr>
                                    <td style="color: #f8f8f2; font-family: sans-serif; font-size: 11px; font-weight: bold; border: none;">{lexer.name}</td>
                                    <td align="right" style="border: none;">
                                        <a href="#copycode_{block_id}" style="text-decoration: none; color: #ffffff; background-color: #555; font-family: sans-serif; font-size: 11px; padding: 4px 8px; border-radius: 4px;">&nbsp;📋 Copy Code&nbsp;</a>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 12px; background-color: #272822; color: #f8f8f2;">
                            <pre style="margin: 0; padding: 0; background-color: transparent; color: #f8f8f2; font-family: 'Courier New', Courier, monospace; font-size: 13px; line-height: 1.4; white-space: pre;">{escaped_code}</pre>
                        </td>
                    </tr>
                </table>
                '''
                
                # Create a new tag from the HTML string
                new_element = BeautifulSoup(table_html, 'html.parser')
                pre.replace_with(new_element)
                
            return str(soup)
        except Exception as e:
            print(f"Error processing HTML: {e}")
            return html_content

    def apply_styles(self):
        """Apply modern professional styling with beautiful design"""
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #f5f7fa, stop:1 #e8ecf1);
            }
            QWidget {
                background-color: #ffffff;
                color: #1a1a1a;
                font-family: 'Segoe UI', 'Microsoft YaHei UI', system-ui, -apple-system, sans-serif;
            }
            QFrame {
                border-radius: 8px;
                background-color: #ffffff;
                border: 1px solid #e1e8ed;
            }
            QLineEdit {
                padding: 12px 16px;
                border: 2px solid #e1e8ed;
                border-radius: 8px;
                background-color: #ffffff;
                font-size: 14px;
                selection-background-color: #1da1f2;
                selection-color: #ffffff;
            }
            QLineEdit:focus {
                border: 2px solid #1da1f2;
                background-color: #f7f9fc;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #1da1f2, stop:1 #0d8bd9);
                color: #ffffff;
                padding: 11px 24px;
                border: none;
                border-radius: 8px;
                font-weight: 600;
                font-size: 14px;
                min-height: 20px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #0d8bd9, stop:1 #0a7bc8);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #0a7bc8, stop:1 #0864a5);
            }
            QPushButton#back_button {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #657786, stop:1 #536471);
            }
            QPushButton#back_button:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #536471, stop:1 #42525c);
            }
            QTextBrowser {
                border: 1px solid #e1e8ed;
                border-radius: 8px;
                background-color: #ffffff;
                padding: 10px;
                selection-background-color: #1da1f2;
                selection-color: #ffffff;
                font-size: 14px;
            }
            QTabWidget::pane {
                border: 1px solid #e1e8ed;
                border-radius: 8px;
                background-color: #ffffff;
                top: -1px;
            }
            QTabBar::tab {
                background-color: #f7f9fc;
                color: #657786;
                padding: 12px 24px;
                margin-right: 2px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-weight: 600;
                font-size: 14px;
                min-width: 100px;
            }
            QTabBar::tab:selected {
                background-color: #ffffff;
                color: #1da1f2;
                border-bottom: 3px solid #1da1f2;
            }
            QTabBar::tab:hover:!selected {
                background-color: #e8f5fe;
                color: #0d8bd9;
            }
            QComboBox {
                padding: 11px 16px;
                border: 2px solid #e1e8ed;
                border-radius: 8px;
                background-color: #ffffff;
                min-width: 140px;
                font-size: 14px;
            }
            QComboBox:focus {
                border: 2px solid #1da1f2;
                background-color: #f7f9fc;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
                border-top-right-radius: 8px;
                border-bottom-right-radius: 8px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #657786;
                width: 0;
                height: 0;
                margin-right: 10px;
            }
            QComboBox QAbstractItemView {
                background-color: #ffffff;
                border: 2px solid #e1e8ed;
                border-radius: 8px;
                selection-background-color: #e8f5fe;
                selection-color: #1da1f2;
                padding: 4px;
            }
            QLabel {
                color: #14171a;
                font-weight: 500;
                font-size: 14px;
            }
            QSplitter::handle {
                background-color: #e1e8ed;
            }
            QSplitter::handle:horizontal {
                width: 5px;
                border-left: 2px solid transparent;
                border-right: 2px solid transparent;
            }
            QSplitter::handle:vertical {
                height: 5px;
                border-top: 2px solid transparent;
                border-bottom: 2px solid transparent;
            }
            QSplitter::handle:hover {
                background-color: #cbd5e0;
            }
            QStatusBar {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #f7f9fc, stop:1 #e8ecf1);
                color: #657786;
                border-top: 1px solid #e1e8ed;
                font-size: 13px;
                padding: 4px;
            }
            QScrollBar:vertical {
                border: none;
                background-color: #f7f9fc;
                width: 12px;
                border-radius: 6px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background-color: #cbd5e0;
                border-radius: 6px;
                min-height: 30px;
                margin: 2px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #a0b4c7;
            }
            QScrollBar:horizontal {
                border: none;
                background-color: #f7f9fc;
                height: 12px;
                border-radius: 6px;
                margin: 0;
            }
            QScrollBar::handle:horizontal {
                background-color: #cbd5e0;
                border-radius: 6px;
                min-width: 30px;
                margin: 2px;
            }
            QScrollBar::handle:horizontal:hover {
                background-color: #a0b4c7;
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

        # Clear caches
        self.comments_cache.clear()
        self.expanded_comments.clear()
        self.answers_cache.clear()

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
            <html><body style='font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif; padding: 30px; background: #f7f9fc;'>
                <div style='background: #ffffff; border-radius: 12px; padding: 30px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); max-width: 600px; margin: 0 auto;'>
                    <h3 style='color: #f4212e; margin-top: 0; font-size: 20px; font-weight: 600;'>❌ Error</h3>
                    <p style='color: #657786; font-size: 14px; line-height: 1.6;'>{results['error']}</p>
                </div>
            </body></html>
            """
            self.search_results[language] = error_html
            browser = self.english_questions_browser if language == "English" else self.russian_questions_browser
            browser.setHtml(error_html)
            return

        questions = results.get("items", [])

        if not questions:
            no_results_html = f"""
            <html><body style='font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif; padding: 30px; background: #f7f9fc;'>
                <div style='background: #ffffff; border-radius: 12px; padding: 40px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); max-width: 600px; margin: 0 auto; text-align: center;'>
                    <h3 style='color: #14171a; margin-top: 0; font-size: 22px; font-weight: 600;'>🔍 No results found</h3>
                    <p style='color: #657786; font-size: 15px; line-height: 1.6;'>Try different keywords or check your query:</p>
                    <p style='color: #1da1f2; font-size: 16px; font-weight: 600; margin: 15px 0;'>"{query}"</p>
                </div>
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
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif; padding: 20px; background: #f7f9fc; }}
                .query-info {{ background: linear-gradient(135deg, #e8f5fe 0%, #d4edfc 100%); padding: 16px 20px; border-radius: 10px; margin-bottom: 20px; border-left: 4px solid #1da1f2; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
                .question-card {{ background: #ffffff; padding: 20px; margin-bottom: 18px; border-left: 4px solid #1da1f2; border-radius: 10px; transition: all 0.2s ease; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border: 1px solid #e1e8ed; }}
                .question-card:hover {{ background: #f7f9fc; box-shadow: 0 4px 12px rgba(0,0,0,0.15); transform: translateY(-1px); }}
                .question-title {{ color: #1da1f2; text-decoration: none; font-size: 17px; font-weight: 600; line-height: 1.4; }}
                .question-title:hover {{ color: #0d8bd9; text-decoration: underline; }}
                .meta {{ color: #657786; font-size: 14px; margin-top: 12px; }}
                .meta span {{ margin-right: 18px; }}
                .badge {{ display: inline-block; padding: 4px 10px; background: #e8f5fe; color: #1da1f2; border-radius: 6px; font-size: 12px; font-weight: 500; }}
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

        # Clear comment caches
        self.comments_cache.clear()
        self.expanded_comments.clear()

        self.statusBar().showMessage("Returned to search results")

    def load_question(self, url, language):
        """Load and display question details with answers"""
        question_id = int(url.split(":")[-1])

        self.selected_question_id = question_id
        self.selected_language = language
        self.back_button.setVisible(True)

        # Clear comment caches for new question
        self.comments_cache.clear()
        self.expanded_comments.clear()

        self.render_question()

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

    def render_question(self):
        """Render question details with optional comments"""
        question = self.question_cache[self.selected_language].get(self.selected_question_id)

        if not question:
            self.question_details_browser.setHtml("<p style='color: #dc3545;'>❌ Question not found in cache</p>")
            return

        # Format question details
        title = question.get("title", "Untitled")
        body = self.process_html_content(question.get("body", "<p>No content available</p>"))
        score = question.get("score", 0)
        view_count = question.get("view_count", 0)
        answer_count = question.get("answer_count", 0)
        comment_count = question.get("comment_count", 0)
        created_date = datetime.fromtimestamp(question.get("creation_date", 0)).strftime("%Y-%m-%d %H:%M")
        tags = question.get("tags", [])
        owner = question.get("owner", {})
        author = owner.get("display_name", "Anonymous")
        reputation = owner.get("reputation", 0)
        link = question.get("link", "#")

        # Check if comments are expanded
        cache_key = f"{self.selected_language}_question_{self.selected_question_id}"
        comments_expanded = cache_key in self.expanded_comments
        comments = self.comments_cache.get(cache_key, [])

        # Build comments HTML
        comments_html = ""
        if comments_expanded and comments:
            comments_html = "<div style='margin-top: 15px; border-top: 2px solid #dee2e6; padding-top: 15px;'>"
            comments_html += "<h4 style='color: #495057; margin-bottom: 10px;'>💬 Comments</h4>"
            for comment in comments:
                comment_body = comment.get("body", "")
                comment_author = comment.get("owner", {}).get("display_name", "Anonymous")
                comment_score = comment.get("score", 0)
                comment_date = datetime.fromtimestamp(comment.get("creation_date", 0)).strftime("%Y-%m-%d %H:%M")

                comments_html += f"""
                <div style='background: #ffffff; padding: 14px; margin-bottom: 12px; border-left: 4px solid #657786; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border: 1px solid #e1e8ed;'>
                    <div style='color: #14171a; font-size: 14px; margin-bottom: 8px; line-height: 1.6;'>{comment_body}</div>
                    <div style='color: #657786; font-size: 13px;'>
                        <span>👤 <strong>{comment_author}</strong></span>
                        <span style='margin-left: 18px;'>⬆️ {comment_score}</span>
                        <span style='margin-left: 18px;'>📅 {comment_date}</span>
                    </div>
                </div>
                """
            comments_html += "</div>"

        # Comments toggle button
        toggle_text = "▼ Hide comments" if comments_expanded else f"▶ Show comments ({comment_count})"
        comments_button = f"<a href='toggle_question_comments:{self.selected_question_id}' style='display: inline-block; margin-top: 15px; padding: 10px 18px; background: linear-gradient(135deg, #657786 0%, #536471 100%); color: white; text-decoration: none; border-radius: 8px; font-size: 13px; font-weight: 500; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>{toggle_text}</a>" if comment_count > 0 else ""

        question_html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif; padding: 25px; line-height: 1.7; background: #f7f9fc; }}
                .title {{ color: #14171a; margin-bottom: 20px; font-size: 26px; font-weight: 700; line-height: 1.3; }}
                .meta {{ color: #657786; margin-bottom: 20px; font-size: 14px; background: linear-gradient(135deg, #f7f9fc 0%, #e8ecf1 100%); padding: 16px 20px; border-radius: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
                .meta span {{ margin-right: 22px; }}
                .tags {{ margin-bottom: 20px; }}
                .tag {{ display: inline-block; background: linear-gradient(135deg, #e8f5fe 0%, #d4edfc 100%); color: #1da1f2; padding: 6px 12px; margin: 4px 4px 4px 0; border-radius: 6px; font-size: 13px; font-weight: 500; box-shadow: 0 1px 2px rgba(0,0,0,0.1); }}
                .body {{ border-top: 2px solid #e1e8ed; padding-top: 25px; margin-top: 20px; }}
                .external-link {{ display: inline-block; margin-top: 20px; padding: 12px 24px; background: linear-gradient(135deg, #1da1f2 0%, #0d8bd9 100%); color: white; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 14px; box-shadow: 0 2px 6px rgba(29, 161, 242, 0.3); transition: all 0.2s; }}
                .external-link:hover {{ background: linear-gradient(135deg, #0d8bd9 0%, #0a7bc8 100%); box-shadow: 0 4px 12px rgba(29, 161, 242, 0.4); transform: translateY(-1px); }}
                a {{ color: #1da1f2; }}
                a:hover {{ color: #0d8bd9; }}
            </style>
        </head>
        <body>
            <h2 class="title">{title}</h2>
            <div class="meta">
                <span>👤 <strong>{author}</strong> ({reputation:,} rep)</span>
                <span>⬆️ Score: <strong>{score}</strong></span>
                <span>👁️ Views: <strong>{view_count:,}</strong></span>
                <span>💬 Answers: <strong>{answer_count}</strong></span>
                <span>💭 Comments: <strong>{comment_count}</strong></span>
                <span>📅 {created_date}</span>
            </div>
            <div class="tags">
                {"".join([f"<span class='tag'>{tag}</span>" for tag in tags])}
            </div>
            <div class="body">
                {body}
            </div>
            {comments_button}
            {comments_html}
            <a href="{link}" class="external-link">🔗 View on Stack Overflow</a>
        </body>
        </html>
        """

        self.question_details_browser.setHtml(question_html)

    def display_answers(self, response, question_id, language):
        """Display answers for the selected question"""
        # Validate this response matches current selection
        if question_id != self.selected_question_id or language != self.selected_language:
            return

        if "error" in response:
            self.answers_browser.setHtml(f"<p style='color: #dc3545; padding: 20px;'>❌ Error: {response['error']}</p>")
            return

        answers = response.get("items", [])
        self.answers_cache = {ans.get("answer_id"): ans for ans in answers}

        if not answers:
            self.answers_browser.setHtml("<p style='color: #6c757d; padding: 20px;'>💭 No answers available yet.</p>")
            return

        self.render_answers()

    def render_answers(self):
        """Render answers with optional comments"""
        answers = list(self.answers_cache.values())

        if not answers:
            return

        html_parts = ["""
        <html>
        <head>
            <style>
                body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif; padding: 25px; line-height: 1.7; background: #f7f9fc; }
                .answer { background: #ffffff; padding: 24px; margin-bottom: 24px; border-radius: 10px; border-left: 4px solid #657786; box-shadow: 0 2px 6px rgba(0,0,0,0.1); border: 1px solid #e1e8ed; transition: all 0.2s; }
                .answer:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
                .answer.accepted { border-left-color: #17bf63; background: linear-gradient(135deg, #f0fff4 0%, #e6f9ed 100%); border-left-width: 5px; }
                .answer-header { color: #14171a; margin-bottom: 18px; font-size: 15px; font-weight: 500; }
                .accepted-badge { background: linear-gradient(135deg, #17bf63 0%, #15a855 100%); color: white; padding: 6px 14px; border-radius: 6px; font-size: 12px; font-weight: 600; box-shadow: 0 2px 4px rgba(23, 191, 99, 0.3); }
                .answer-body { border-top: 2px solid #e1e8ed; padding-top: 20px; margin-bottom: 15px; }
                .comment { background: #ffffff; padding: 14px; margin: 10px 0; border-left: 4px solid #657786; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border: 1px solid #e1e8ed; }
                .comment-body { color: #14171a; font-size: 14px; margin-bottom: 8px; line-height: 1.6; }
                .comment-meta { color: #657786; font-size: 13px; }
                .comments-section { margin-top: 20px; padding-top: 20px; border-top: 2px solid #e1e8ed; }
                .toggle-btn { display: inline-block; padding: 10px 18px; background: linear-gradient(135deg, #657786 0%, #536471 100%); color: white; text-decoration: none; border-radius: 8px; font-size: 13px; font-weight: 500; box-shadow: 0 2px 4px rgba(0,0,0,0.1); transition: all 0.2s; }
                .toggle-btn:hover { background: linear-gradient(135deg, #536471 0%, #42525c 100%); box-shadow: 0 4px 8px rgba(0,0,0,0.2); transform: translateY(-1px); }
                a { color: #1da1f2; }
                a:hover { color: #0d8bd9; }
            </style>
        </head>
        <body>
        """]

        for i, answer in enumerate(answers, 1):
            answer_id = answer.get("answer_id")
            is_accepted = answer.get("is_accepted", False)
            score = answer.get("score", 0)
            body = self.process_html_content(answer.get("body", "<p>No content</p>"))
            comment_count = answer.get("comment_count", 0)
            created_date = datetime.fromtimestamp(answer.get("creation_date", 0)).strftime("%Y-%m-%d %H:%M")
            owner = answer.get("owner", {})
            author = owner.get("display_name", "Anonymous")
            reputation = owner.get("reputation", 0)

            accepted_class = "accepted" if is_accepted else ""
            accepted_badge = '<span class="accepted-badge">✓ ACCEPTED</span> ' if is_accepted else ''

            # Check if comments are expanded for this answer
            cache_key = f"{self.selected_language}_{answer_id}"
            comments_expanded = cache_key in self.expanded_comments
            comments = self.comments_cache.get(cache_key, [])

            # Build comments HTML
            comments_html = ""
            if comments_expanded and comments:
                comments_html = "<div class='comments-section'>"
                comments_html += "<h5 style='color: #14171a; margin-bottom: 14px; font-size: 16px; font-weight: 600;'>💬 Comments:</h5>"
                for comment in comments:
                    comment_body = comment.get("body", "")
                    comment_author = comment.get("owner", {}).get("display_name", "Anonymous")
                    comment_score = comment.get("score", 0)
                    comment_date = datetime.fromtimestamp(comment.get("creation_date", 0)).strftime("%Y-%m-%d %H:%M")

                    comments_html += f"""
                    <div class="comment">
                        <div class="comment-body">{comment_body}</div>
                        <div class="comment-meta">
                            <span>👤 <strong>{comment_author}</strong></span>
                            <span style='margin-left: 18px;'>⬆️ {comment_score}</span>
                            <span style='margin-left: 18px;'>📅 {comment_date}</span>
                        </div>
                    </div>
                    """
                comments_html += "</div>"

            # Comments toggle button
            toggle_text = "▼ Hide comments" if comments_expanded else f"▶ Show comments ({comment_count})"
            comments_button = f"<a href='toggle_comments:{answer_id}' class='toggle-btn'>{toggle_text}</a>" if comment_count > 0 else ""

            html_parts.append(f"""
                <div class="answer {accepted_class}">
                    <div class="answer-header">
                        {accepted_badge}
                        <strong>Answer #{i}</strong> by <strong>{author}</strong> ({reputation:,} rep)
                        <span style='margin-left: 20px;'>⬆️ Score: <strong>{score}</strong></span>
                        <span style='margin-left: 20px;'>💭 Comments: <strong>{comment_count}</strong></span>
                        <span style='margin-left: 20px;'>📅 {created_date}</span>
                    </div>
                    <div class="answer-body">
                        {body}
                    </div>
                    {comments_button}
                    {comments_html}
                </div>
            """)

        html_parts.append("</body></html>")
        self.answers_browser.setHtml("".join(html_parts))


def main():
    # Set AppUserModelID to ensure the taskbar icon is separate and visible on Windows
    myappid = 'stackoverflow.api.bilingual.search.2.0'
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception:
        pass  # Just in case of error on some systems

    app = QApplication(sys.argv)
    app.setApplicationName("Stack Overflow Search Pro")
    app.setApplicationDisplayName("Stack Overflow Search Pro")
    
    # Set application-wide window icon with fallback
    import os
    icon_path = 'icon.png'
    if os.path.exists(icon_path):
        app_icon = QIcon(icon_path)
        app.setWindowIcon(app_icon)
    else:
        # Create a simple default icon if file doesn't exist
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.GlobalColor.blue)
        app_icon = QIcon(pixmap)
        app.setWindowIcon(app_icon)
    
    window = StackOverflowGUI()
    window.setWindowIcon(app_icon)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    try:
        main()
    except Exception:
        import traceback
        with open("crash_log.txt", "w", encoding="utf-8") as f:
            f.write(traceback.format_exc())
        
        # Also try to show a message box if possible
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, "Application crashed! See crash_log.txt", "Error", 0x10)
        except:
            pass
        sys.exit(1)