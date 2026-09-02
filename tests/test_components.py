import sys
import os
import unittest
import customtkinter as ctk

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.api.stackoverflow import StackOverflowAPI
from src.utils.highlighter import parse_html_to_blocks, html_to_markdown, CodeHighlighter, extract_text_preview
from src.utils.bookmarks import BookmarkManager
from src.ui.components.selectable_label import SelectableLabel
from src.ui.components.code_block import CodeBlockWidget
from src.ui.components.question_card import QuestionCard
from src.ui.components.rich_view import RichContentView
from src.ui.components.details_view import QuestionDetailsView
from src.ui.app import StackOverflowApp


class TestStackOverflow(unittest.TestCase):
    def test_api_client(self):
        api = StackOverflowAPI()
        res = api.search_questions("python json", language="English", pagesize=2)
        self.assertIn("items", res)
        self.assertTrue(len(res["items"]) > 0)
        self.assertIsNotNone(api.last_quota_remaining)

    def test_html_parsing_and_inline_segments(self):
        sample_html = (
            '<p>Use <code>requests.get()</code> with <strong>timeout=5</strong>. '
            'See <a href="https://example.com">here</a>.</p>'
            '<pre><code class="lang-python">x = 42</code></pre>'
            '<blockquote>Important note</blockquote>'
        )
        blocks = parse_html_to_blocks(sample_html)
        self.assertEqual(len(blocks), 3)
        self.assertEqual(blocks[0]["type"], "paragraph")
        self.assertEqual(blocks[1]["type"], "code")
        self.assertEqual(blocks[2]["type"], "blockquote")

        # Verify inline segments
        segments = blocks[0]["segments"]
        tags = [seg[1] for seg in segments]
        self.assertIn("code_inline", tags)
        self.assertIn("bold", tags)
        self.assertIn("link", tags)

    def test_text_preview_extractor(self):
        html = "<p>This is a <strong>great</strong> description.<pre><code>def foo(): pass</code></pre>Follow these steps.</p>"
        preview = extract_text_preview(html, max_chars=50)
        self.assertIn("This is a great description.", preview)
        self.assertNotIn("def foo():", preview)

    def test_html_to_markdown(self):
        sample_html = '<p>Explanation here with <code>inline_code</code></p><pre><code class="lang-python">print("hello")</code></pre><blockquote>Quoted advice</blockquote>'
        md = html_to_markdown(sample_html)
        self.assertIn("Explanation here", md)
        self.assertIn("`inline_code`", md)
        self.assertIn("```python", md)
        self.assertIn('print("hello")', md)
        self.assertIn("> Quoted advice", md)

    def test_code_tokenization(self):
        tokens, lang = CodeHighlighter.tokenize("def hello():\n    return 'world'", "python")
        self.assertEqual(lang, "PYTHON")
        self.assertTrue(len(tokens) > 0)

    def test_code_block_wrap_toggle(self):
        root = ctk.CTk()
        cw = CodeBlockWidget(root, code="long_line = " + "x" * 150)
        cw.pack()
        root.update()

        self.assertFalse(cw.is_wrapped)
        cw.toggle_wrap()
        self.assertTrue(cw.is_wrapped)
        cw.toggle_wrap()
        self.assertFalse(cw.is_wrapped)
        root.destroy()

    def test_bookmark_manager(self):
        bm = BookmarkManager()
        test_q = {
            "question_id": 999888,
            "title": "Bookmark Test Question",
            "score": 5,
            "owner": {"display_name": "Tester"},
            "creation_date": 1600000000
        }
        # Clean state
        bm.remove_bookmark(999888)
        self.assertFalse(bm.is_bookmarked(999888))

        # Add
        bm.add_bookmark(test_q, "English")
        self.assertTrue(bm.is_bookmarked(999888))
        self.assertIsNotNone(bm.get_bookmark(999888))

        # Toggle
        res = bm.toggle_bookmark(test_q, "English")
        self.assertFalse(res)
        self.assertFalse(bm.is_bookmarked(999888))

    def test_question_card_selection(self):
        root = ctk.CTk()
        sample_q = {
            "question_id": 777,
            "title": "Card Selection Question",
            "score": 12,
            "answer_count": 3,
            "is_answered": True,
            "view_count": 1400,
            "tags": ["python", "asyncio"],
            "owner": {"display_name": "DevGuy", "reputation": 2500},
            "body": "<p>Preview body text</p>"
        }
        card = QuestionCard(root, question_data=sample_q, on_click_callback=lambda q_id, c: None)
        card.pack()
        root.update()

        self.assertFalse(card.is_selected)
        card.set_selected(True)
        self.assertTrue(card.is_selected)
        card.set_selected(False)
        self.assertFalse(card.is_selected)
        root.destroy()

    def test_selectable_label(self):
        root = ctk.CTk()
        lbl = SelectableLabel(root, text="Selectable test paragraph")
        lbl.pack()
        root.update()

        lbl._select_all()
        selected = lbl.get("sel.first", "sel.last")
        self.assertEqual(selected, "Selectable test paragraph")

        lbl.apply_theme("light")
        lbl.apply_theme("dark")
        root.destroy()

    def test_rich_content_view_selectable(self):
        root = ctk.CTk()
        html = '<p>First paragraph with multiple words and <code>inline_code</code></p><pre><code>let y = 10;</code></pre><ul><li>Item 1</li><li>Item 2</li></ul>'
        rich = RichContentView(root, html_content=html)
        rich.pack(fill="x")
        root.update()

        self.assertEqual(len(rich.text_blocks), 2)
        self.assertEqual(len(rich.code_widgets), 1)

        cw = rich.code_widgets[0]
        self.assertGreater(cw.winfo_width(), 0)
        self.assertGreater(cw.winfo_height(), 0)

        tb = rich.text_blocks[0]
        tb._select_all()
        selected = tb.get("sel.first", "sel.last")
        self.assertIn("First paragraph", selected)

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