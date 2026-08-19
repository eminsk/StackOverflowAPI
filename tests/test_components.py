import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.api.stackoverflow import StackOverflowAPI
from src.utils.highlighter import parse_html_to_blocks, CodeHighlighter
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

    def test_code_tokenization(self):
        tokens, lang = CodeHighlighter.tokenize("def hello():\n    return 'world'", "python")
        self.assertEqual(lang, "PYTHON")
        self.assertTrue(len(tokens) > 0)

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