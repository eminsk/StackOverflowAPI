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
    """Class to handle Stack Exchange API calls for both English and Russian sites"""
    
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
    
    def search_questions(self, query, language='English', page=1, pagesize=10):
        """Search for questions on Stack Overflow in the specified language"""
        params = {
            'site': self.SITE_NAMES[language],
            'intitle': query,  # Using 'intitle' as it's more reliable
            'order': 'desc',
            'sort': 'relevance',
            'filter': 'withbody',
            'page': page,
            'pagesize': pagesize
        }
        
        url = f"{self.BASE_URLS[language]}/search/advanced"
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                error_message = f"API Error: {response.status_code}"
                try:
                    error_data = response.json()
                    if 'error_message' in error_data:
                        error_message += f" - {error_data['error_message']}"
                except:
                    pass
                return {"items": [], "error": error_message}
                
        except requests.exceptions.RequestException as e:
            return {"items": [], "error": f"Request Error: {str(e)}"}
    
    def get_question_answers(self, question_id, language='English'):
        """Get answers for a specific question"""
        params = {
            'site': self.SITE_NAMES[language],
            'filter': 'withbody',
            'order': 'desc',
            'sort': 'votes'
        }
        
        url = f"{self.BASE_URLS[language]}/questions/{question_id}/answers"
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                error_message = f"API Error: {response.status_code}"
                try:
                    error_data = response.json()
                    if 'error_message' in error_data:
                        error_message += f" - {error_data['error_message']}"
                except:
                    pass
                return {"items": [], "error": error_message}
                
        except requests.exceptions.RequestException as e:
            return {"items": [], "error": f"Request Error: {str(e)}"}

class SearchWorker(QThread):
    """Worker thread to perform search operations asynchronously"""
    results_ready = pyqtSignal(dict, str)
    
    def __init__(self, api, query, language):
        super().__init__()
        self.api = api
        self.query = query
        self.language = language
        
    def run(self):
        results = self.api.search_questions(self.query, self.language)
        self.results_ready.emit(results, self.language)


class AnswersWorker(QThread):
    """Worker thread to fetch answers asynchronously"""
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
    """Main GUI application for Stack Overflow search"""
    
    def __init__(self):
        super().__init__()
        self.api = StackOverflowAPI()
        self.search_threads = []
        self.answers_threads = []
        self.selected_question_id = None
        self.selected_language = None
        self.question_cache = {'English': {}, 'Russian': {}}
        
        # Store search results and query to prevent losing them
        self.current_search_query = ""
        self.search_results = {'English': "", 'Russian': ""}
        self.last_search_language = "Both"
        
        self.initUI()
        
    def initUI(self):
        """Initialize the user interface"""
        self.setWindowTitle("Stack Overflow Bilingual Search")
        self.setMinimumSize(1000, 700)
        
        # Main layout
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        
        # Search section
        search_frame = QFrame()
        search_frame.setFrameShape(QFrame.Shape.StyledPanel)
        search_layout = QHBoxLayout(search_frame)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter your search query...")
        self.search_input.returnPressed.connect(self.perform_search)
        
        self.language_selector = QComboBox()
        self.language_selector.addItems(["Both", "English", "Russian"])
        
        search_button = QPushButton("Search")
        search_button.clicked.connect(self.perform_search)
        
        # Add back to results button
        self.back_button = QPushButton("← Back to Results")
        self.back_button.clicked.connect(self.show_search_results)
        self.back_button.setVisible(False)  # Initially hidden
        
        search_layout.addWidget(QLabel("Search:"))
        search_layout.addWidget(self.search_input, 1)
        search_layout.addWidget(QLabel("Language:"))
        search_layout.addWidget(self.language_selector)
        search_layout.addWidget(search_button)
        search_layout.addWidget(self.back_button)
        
        # Content section (split view)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Questions panel
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
        
        self.questions_tabs.addTab(self.english_questions_browser, "English Results")
        self.questions_tabs.addTab(self.russian_questions_browser, "Russian Results")
        
        questions_layout.addWidget(self.questions_tabs)
        
        # Details panel
        details_widget = QWidget()
        details_layout = QVBoxLayout(details_widget)
        
        self.question_details_browser = QTextBrowser()
        self.answers_browser = QTextBrowser()
        
        details_splitter = QSplitter(Qt.Orientation.Vertical)
        
        question_frame = QFrame()
        question_layout = QVBoxLayout(question_frame)
        question_layout.addWidget(QLabel("<b>Question Details</b>"))
        question_layout.addWidget(self.question_details_browser)
        
        answers_frame = QFrame()
        answers_layout = QVBoxLayout(answers_frame)
        answers_layout.addWidget(QLabel("<b>Answers</b>"))
        answers_layout.addWidget(self.answers_browser)
        
        details_splitter.addWidget(question_frame)
        details_splitter.addWidget(answers_frame)
        details_splitter.setSizes([300, 400])
        
        details_layout.addWidget(details_splitter)
        
        # Add widgets to splitter
        splitter.addWidget(questions_widget)
        splitter.addWidget(details_widget)
        splitter.setSizes([400, 600])
        
        # Add all components to main layout
        main_layout.addWidget(search_frame)
        main_layout.addWidget(splitter, 1)
        
        # Status bar
        self.statusBar().showMessage("Ready")
        
        self.setCentralWidget(main_widget)
        
        # Apply styles
        self.apply_styles()
        
    def apply_styles(self):
        """Apply custom styling to the application"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
                color: #333333;
            }
            QWidget {
                background-color: #ffffff;
                color: #333333;
            }
            QFrame {
                border-radius: 5px;
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
            }
            QLineEdit {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: #ffffff;
                color: #333333;
            }
            QLineEdit:focus {
                border: 2px solid #0077cc;
            }
            QPushButton {
                background-color: #0077cc;
                color: #ffffff;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0095ff;
            }
            QPushButton:pressed {
                background-color: #005fa3;
            }
            QTextBrowser {
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: #ffffff;
                color: #333333;
                selection-background-color: #b3d9ff;
            }
            QTabWidget::pane {
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: #ffffff;
            }
            QTabWidget::tab-bar {
                alignment: center;
            }
            QTabBar::tab {
                background-color: #f0f0f0;
                color: #333333;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #ffffff;
                border-bottom: 2px solid #0077cc;
            }
            QTabBar::tab:hover {
                background-color: #e8e8e8;
            }
            QComboBox {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: #ffffff;
                color: #333333;
                min-width: 100px;
            }
            QComboBox::drop-down {
                border: none;
                background-color: transparent;
            }
            QComboBox::down-arrow {
                image: none;
                border-style: solid;
                border-width: 5px;
                border-color: #666666 transparent transparent transparent;
            }
            QComboBox QAbstractItemView {
                background-color: #ffffff;
                color: #333333;
                border: 1px solid #ddd;
                selection-background-color: #b3d9ff;
            }
            QLabel {
                color: #333333;
            }
            QSplitter::handle {
                background-color: #ddd;
            }
            QSplitter::handle:horizontal {
                width: 3px;
            }
            QSplitter::handle:vertical {
                height: 3px;
            }
        """)
        
    def perform_search(self):
        """Execute search across selected languages"""
        query = self.search_input.text().strip()
        if not query:
            self.statusBar().showMessage("Please enter a search query")
            return
            
        selected_language = self.language_selector.currentText()
        
        # Store the current search parameters
        self.current_search_query = query
        self.last_search_language = selected_language
        
        # Clear previous results
        self.english_questions_browser.clear()
        self.russian_questions_browser.clear()
        self.question_details_browser.clear()
        self.answers_browser.clear()
        self.search_results = {'English': "", 'Russian': ""}
        
        # Hide back button during search
        self.back_button.setVisible(False)
        
        self.statusBar().showMessage(f"Searching for: {query}...")
        
        # Clear any existing search threads
        for thread in self.search_threads:
            if thread.isRunning():
                thread.terminate()
                thread.wait()
        
        self.search_threads.clear()
        
        # Start new search threads based on selected language
        if selected_language in ("Both", "English"):
            english_thread = SearchWorker(self.api, query, "English")
            english_thread.results_ready.connect(self.handle_search_results)
            english_thread.start()
            self.search_threads.append(english_thread)
            
        if selected_language in ("Both", "Russian"):
            russian_thread = SearchWorker(self.api, query, "Russian")
            russian_thread.results_ready.connect(self.handle_search_results)
            russian_thread.start()
            self.search_threads.append(russian_thread)
    
    def handle_search_results(self, results, language):
        """Process and display search results"""
        if "error" in results:
            error_html = f"<p>Error: {results['error']}</p>"
            self.search_results[language] = error_html
            if language == "English":
                self.english_questions_browser.setHtml(error_html)
            else:
                self.russian_questions_browser.setHtml(error_html)
            return
            
        questions = results.get("items", [])
        
        if not questions:
            no_results_html = "<p>No results found.</p>"
            self.search_results[language] = no_results_html
            browser = self.english_questions_browser if language == "English" else self.russian_questions_browser
            browser.setHtml(no_results_html)
            return
            
        # Format results for display
        html_results = ["<html><body>"]
        
        for question in questions:
            question_id = question.get("question_id")
            title = question.get("title", "Untitled")
            score = question.get("score", 0)
            answer_count = question.get("answer_count", 0)
            
            created_date = datetime.fromtimestamp(question.get("creation_date", 0)).strftime("%Y-%m-%d")
            
            # Cache the question details
            self.question_cache[language][question_id] = question
            
            html_results.append(
                f"""<div style="margin-bottom: 10px; padding: 5px; border-bottom: 1px solid #ddd;">
                <a href="{question_id}" style="font-weight: bold; color: #0077cc; text-decoration: none;">
                {title}</a>
                <div style="margin-top: 5px; color: #666;">
                Score: {score} | Answers: {answer_count} | Created: {created_date}
                </div>
                </div>"""
            )
            
        html_results.append("</body></html>")
        results_html = ''.join(html_results)
        
        # Store the formatted results
        self.search_results[language] = results_html
        
        # Update the appropriate browser
        browser = self.english_questions_browser if language == "English" else self.russian_questions_browser
        browser.setHtml(results_html)
        
        self.statusBar().showMessage(f"Found {len(questions)} results in {language}")
        
        # Switch to the appropriate tab
        tab_index = 0 if language == "English" else 1
        self.questions_tabs.setCurrentIndex(tab_index)
    
    def show_search_results(self):
        """Restore the search results view"""
        if self.search_results['English']:
            self.english_questions_browser.setHtml(self.search_results['English'])
        if self.search_results['Russian']:
            self.russian_questions_browser.setHtml(self.search_results['Russian'])
        
        # Clear question details and answers
        self.question_details_browser.clear()
        self.answers_browser.clear()
        
        # Hide back button
        self.back_button.setVisible(False)
        
        # Reset selection
        self.selected_question_id = None
        self.selected_language = None
        
        self.statusBar().showMessage(f"Showing results for: {self.current_search_query}")
    
    def load_question(self, question_id_str, language):
        """Load detailed information for a selected question"""
        try:
            question_id = int(question_id_str)
        except ValueError:
            self.statusBar().showMessage("Invalid question ID")
            return
            
        self.selected_question_id = question_id
        self.selected_language = language
        
        # Show back button
        self.back_button.setVisible(True)
        
        # Get question details from cache
        question = self.question_cache[language].get(question_id)
        
        if not question:
            self.question_details_browser.setText("Question not found in cache")
            return
            
        # Display question details
        title = question.get("title", "Untitled")
        body = question.get("body", "No content available")
        score = question.get("score", 0)
        view_count = question.get("view_count", 0)
        answer_count = question.get("answer_count", 0)
        created_date = datetime.fromtimestamp(question.get("creation_date", 0)).strftime("%Y-%m-%d %H:%M")
        
        owner = question.get("owner", {})
        author = owner.get("display_name", "Anonymous")
        
        tags = question.get("tags", [])
        tags_html = ''.join([f'<span style="background-color: #E1ECF4; padding: 2px 6px; margin-right: 5px; border-radius: 3px;">{tag}</span>' for tag in tags])
        
        question_html = f"""
        <h2>{title}</h2>
        <div style="margin-bottom: 10px;">
            Asked by <b>{author}</b> on {created_date} | 
            Score: {score} | Views: {view_count} | Answers: {answer_count}
        </div>
        <div style="margin-bottom: 15px;">
            {tags_html}
        </div>
        <div style="border-top: 1px solid #ddd; padding-top: 10px;">
            {body}
        </div>
        """
        
        self.question_details_browser.setHtml(question_html)
        
        # Clear previous answers and show loading message
        self.answers_browser.setHtml("<p>Loading answers...</p>")
        
        # Fetch answers in a separate thread
        for thread in self.answers_threads:
            if thread.isRunning():
                thread.terminate()
                thread.wait()
                
        self.answers_threads.clear()
        
        answers_thread = AnswersWorker(self.api, question_id, language)
        answers_thread.answers_ready.connect(self.display_answers)
        answers_thread.start()
        self.answers_threads.append(answers_thread)
        
    def display_answers(self, response, question_id, language):
        """Display answers for the selected question"""
        if question_id != self.selected_question_id or language != self.selected_language:
            return  # This is an old response, ignore it
            
        if "error" in response:
            self.answers_browser.setHtml(f"<p>Error loading answers: {response['error']}</p>")
            return
            
        answers = response.get("items", [])
        
        if not answers:
            self.answers_browser.setHtml("<p>No answers available for this question yet.</p>")
            return
            
        answers_html = ["<html><body>"]
        
        for i, answer in enumerate(answers, 1):
            is_accepted = answer.get("is_accepted", False)
            score = answer.get("score", 0)
            body = answer.get("body", "No content")
            created_date = datetime.fromtimestamp(answer.get("creation_date", 0)).strftime("%Y-%m-%d %H:%M")
            
            owner = answer.get("owner", {})
            author = owner.get("display_name", "Anonymous")
            
            acceptance_mark = ""
            if is_accepted:
                acceptance_mark = '<span style="background-color: #5fba7d; color: white; padding: 3px 6px; border-radius: 3px; margin-right: 8px;">✓</span>'
                
            answers_html.append(f"""
            <div style="margin-bottom: 20px; padding-bottom: 15px; border-bottom: 1px solid #ddd;">
                <div style="display: flex; margin-bottom: 10px;">
                    {acceptance_mark}
                    <div style="margin-right: 10px; font-weight: bold; color: {'green' if score > 0 else 'red' if score < 0 else 'gray'};">
                        Score: {score}
                    </div>
                    <div>
                        Answered by <b>{author}</b> on {created_date}
                    </div>
                </div>
                <div>{body}</div>
            </div>
            """)
            
        answers_html.append("</body></html>")
        
        self.answers_browser.setHtml(''.join(answers_html))
        self.statusBar().showMessage(f"Loaded {len(answers)} answers")


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = StackOverflowGUI()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()