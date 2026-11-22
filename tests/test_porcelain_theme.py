"""Regression checks for the optional light gray SuxenAI design layer."""
import re
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CSS=(ROOT/"static"/"theme-porcelain.css").read_text(encoding="utf-8")
HTML=(ROOT/"static"/"index.html").read_text(encoding="utf-8")


class PorcelainThemeTests(unittest.TestCase):
    def test_base_stylesheet_loads_before_theme(self):
        self.assertIn('href="/suxen.css"',HTML)
        self.assertIn('href="/theme-porcelain.css"',HTML)
        self.assertLess(HTML.index('href="/suxen.css"'),
                        HTML.index('href="/theme-porcelain.css"'))

    def test_balanced_css_and_light_mode(self):
        # Comments and quoted strings excluded from basic delimiter checking.
        cleaned=re.sub(r"/\*.*?\*/","",CSS,flags=re.S)
        self.assertEqual(cleaned.count("{"),cleaned.count("}"))
        self.assertIn("color-scheme: light",cleaned)

    def test_required_visual_surfaces(self):
        for selector in (".sidebar", ".topbar", ".conversation", ".inspector",
                         ".panel", ".composer", ".send", ".web-provider",
                         ".desktop-controls", "dialog"):
            with self.subTest(selector=selector):
                self.assertIn(selector,CSS)

    def test_theme_does_not_change_application_scripts(self):
        self.assertIn('<script src="/app.js"></script>',HTML)
        self.assertNotIn("<script",CSS)

if __name__=="__main__":
    unittest.main()
