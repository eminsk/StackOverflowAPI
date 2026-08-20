import sys
import os
import unittest
import customtkinter as ctk

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.api.stackoverflow import StackOverflowAPI
from src.utils.highlighter import parse_html_to_blocks, html_to_markdown, CodeHighlighter
from src.ui.components.selectable_label import SelectableLabel
from src.ui.components.rich_view import RichContentView
from src.ui.components.details_view import QuestionDetailsView
from src.ui.app import StackOverflowApp


class TestStackOverflow(unittest.TestCase):
    def test_api_client(self):
        api = StackOverflowAPI()
        res = api.search_questions("python json", language="English", pagesize=2)
        self.assertIn("items", res)
        self.assertTrue(len(res["items"]) > 0)

    def test_html_parsing(self):
        sample_html = '<p>Test paragraph</p><pre><code class="lang-python">x = 42</code></pre><blockquote>Quote</blockquote>'
        blocks = parse_html_to_blocks(sample_html)
        self.assertEqual(len(blocks), 3)
        self.assertEqual(blocks[0]["type"], "paragraph")
        self.assertEqual(blocks[1]["type"], "code")
        self.assertEqual(blocks[2]["type"], "blockquote")

    def test_html_to_markdown(self):
        sample_html = '<p>Explanation here</p><pre><code class="lang-python">print("hello")</code></pre><blockquote>Quoted advice</blockquote>'
        md = html_to_markdown(sample_html)
        self.assertIn("Explanation here", md)
        self.assertIn("```python", md)
        self.assertIn('print("hello")', md)
        self.assertIn("> Quoted advice", md)

    def test_code_tokenization(self):
        tokens, lang = CodeHighlighter.tokenize("def hello():\n    return 'world'", "python")
        self.assertEqual(lang, "PYTHON")
        self.assertTrue(len(tokens) > 0)

    def test_selectable_label(self):
        root = ctk.CTk()
        lbl = SelectableLabel(root, text="Selectable test paragraph")
        lbl.pack()
        root.update()

        # Check content and select all
        lbl._select_all()
        selected = lbl.get("sel.first", "sel.last")
        self.assertEqual(selected, "Selectable test paragraph")

        # Test theme adaptation
        lbl.apply_theme("light")
        lbl.apply_theme("dark")

        root.destroy()

    def test_rich_content_view_selectable(self):
        root = ctk.CTk()
        html = '<p>First paragraph with multiple words</p><pre><code>let y = 10;</code></pre><ul><li>Item 1</li><li>Item 2</li></ul>'
        rich = RichContentView(root, html_content=html)
        rich.pack(fill="x")
        root.update()

        # Verify unified text widget exists and has content
        self.assertIsNotNone(rich.text_widget)
        rich._select_all()
        selected = rich.text_widget.get("sel.first", "sel.last")
        self.assertIn("First paragraph", selected)
        self.assertIn("Item 1", selected)

        rich.apply_theme("light")
        rich.apply_theme("dark")
        root.destroy()

    def test_question_details_view_with_answers(self):
        root = ctk.CTk()
        dv = QuestionDetailsView(root, on_fetch_comments_callback=lambda *args: None)
        dv.pack(fill="both", expand=True)

        sample_q = {
            "question_id": 12345,
            "title": "How to do X in Python?",
            "score": 10,
            "view_count": 500,
            "creation_date": 1600000000,
            "tags": ["python", "json"],
            "owner": {"display_name": "DevUser", "reputation": 1000},
            "body": "<p>Here is my question description.</p><pre><code>x = 1</code></pre>"
        }

        sample_answers = [
            {
                "answer_id": 99991,
                "is_accepted": True,
                "score": 25,
                "creation_date": 1600001000,
                "owner": {"display_name": "Expert", "reputation": 50000},
                "body": "<p>Use this solution:</p><pre><code class=\"lang-python\">def solve():\n    return True</code></pre>"
            }
        ]

        dv.load_question(sample_q, "English")
        dv.display_answers(sample_answers)
        root.update()

        self.assertEqual(dv.current_question["question_id"], 12345)
        self.assertEqual(len(dv.current_answers), 1)

        root.destroy()

    def test_ui_lifecycle(self):
        app = StackOverflowApp()
        app.update()
        app.destroy()

    def test_theme_switching(self):
        app = StackOverflowApp()
        app.update()
        app.on_theme_changed("light")
        app.update()
        app.on_theme_changed("dark")
        app.update()
        app.on_theme_changed("system")
        app.update()
        app.destroy()


if __name__ == "__main__":
    unittest.main()