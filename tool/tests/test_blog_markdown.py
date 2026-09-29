"""Tests for the blog's Markdown renderer.

Run from the repo root:

    python3 -m unittest discover -s tool/tests -v

Every case here corresponds to a construct an article actually uses, plus the
failure modes that would otherwise reach the live site silently: an unknown
callout, an unclosed block, a level-1 heading colliding with the page title.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tool.blog import markdown as md  # noqa: E402


class TestInline(unittest.TestCase):
    def test_bold_italic_code(self):
        self.assertEqual(md.render_inline("**a** and *b* and `c`"),
                         "<strong>a</strong> and <em>b</em> and <code>c</code>")

    def test_snake_case_survives(self):
        self.assertIn("snake_case_name", md.render_inline("call snake_case_name here"))

    def test_math_is_not_emphasis_processed(self):
        out = md.render_inline(r"the value $H(f) = e^{-j2\pi f \tau}$ ends")
        self.assertIn(r"e^{-j2\pi f \tau}", out)
        self.assertNotIn("<em>", out)

    def test_math_with_underscores(self):
        out = md.render_inline(r"$x_{n+1} = a_n x_n$")
        self.assertIn(r"x_{n+1}", out)
        self.assertNotIn("<em>", out)

    def test_link_and_autolink(self):
        self.assertIn('<a href="https://example.com" target="_blank"',
                      md.render_inline("see https://example.com now"))
        self.assertIn('<a href="plots/a.svg">label</a>', md.render_inline("[label](plots/a.svg)"))

    def test_html_is_escaped_but_raw_tags_pass(self):
        self.assertIn("&lt;not a tag", md.render_inline("<not a tag"))
        self.assertIn("<sub>2</sub>", md.render_inline("H<sub>2</sub>O"))

    def test_ampersand_entities_not_double_escaped(self):
        self.assertIn("R&amp;D", md.render_inline("R&D"))
        self.assertIn("&amp;", md.render_inline("R&amp;D"))
        self.assertNotIn("&amp;amp;", md.render_inline("R&amp;D"))

    def test_code_span_content_is_escaped(self):
        self.assertIn("<code>a &lt; b</code>", md.render_inline("`a < b`"))


class TestBlocks(unittest.TestCase):
    def test_headings_and_toc(self):
        res = md.render("## First part\n\ntext\n\n### Deeper\n\nmore")
        self.assertEqual([h.level for h in res.toc], [2, 3])
        self.assertEqual([h.text for h in res.toc], ["First part", "Deeper"])
        self.assertIn('<h2 id="first-part">', res.html)
        self.assertIn('<h3 id="deeper">', res.html)

    def test_duplicate_headings_get_unique_anchors(self):
        res = md.render("## Cost\n\na\n\n## Cost\n\nb")
        self.assertEqual([h.anchor for h in res.toc], ["cost", "cost-2"])

    def test_h1_is_rejected(self):
        with self.assertRaises(md.MarkdownError):
            md.render("# Title\n\nbody")

    def test_paragraphs_and_rule(self):
        res = md.render("one\n\n---\n\ntwo")
        self.assertIn("<p>one</p>", res.html)
        self.assertIn("<hr>", res.html)
        self.assertIn("<p>two</p>", res.html)

    def test_unordered_and_nested_list(self):
        res = md.render("- a\n- b\n  - b1\n  - b2\n- c")
        self.assertIn("<ul>", res.html)
        self.assertIn("<li>a</li>", res.html)
        self.assertEqual(res.html.count("<ul>"), 2)

    def test_ordered_list(self):
        res = md.render("1. one\n2. two")
        self.assertIn("<ol>", res.html)
        self.assertIn("<li>two</li>", res.html)

    def test_table(self):
        res = md.render("| a | b |\n|---|---|\n| 1 | 2 |")
        self.assertIn("<th", res.html)
        self.assertIn("<td", res.html)
        self.assertIn(">1<", res.html)

    def test_table_alignment(self):
        res = md.render("| a | b |\n|:--|--:|\n| 1 | 2 |")
        self.assertIn("text-align:left", res.html)
        self.assertIn("text-align:right", res.html)

    def test_fenced_code_is_escaped(self):
        res = md.render("```c\nif (a && b) {}\n```")
        self.assertIn('class="language-c"', res.html)
        self.assertIn("a &amp;&amp; b", res.html)

    def test_blockquote(self):
        res = md.render("> quoted **bold**")
        self.assertIn("<blockquote>", res.html)
        self.assertIn("<strong>bold</strong>", res.html)

    def test_display_math_block(self):
        res = md.render("$$\nX(k) = \\sum x[n] e^{-j2\\pi kn/N}\n$$")
        self.assertIn('class="math-display"', res.html)
        self.assertIn("X(k)", res.html)

    def test_callout(self):
        res = md.render("::: optical The coherent case\nBecause phase.\n:::")
        self.assertIn('class="callout callout-optical"', res.html)
        self.assertIn("The coherent case", res.html)
        self.assertIn("<p>Because phase.</p>", res.html)

    def test_callout_default_title(self):
        self.assertIn("Key idea", md.render("::: key\nx\n:::").html)

    def test_callout_can_contain_blocks(self):
        res = md.render("::: note T\n- a\n- b\n\n```\ncode\n```\n:::")
        self.assertIn("<ul>", res.html)
        self.assertIn("<pre>", res.html)

    def test_unknown_callout_is_rejected(self):
        with self.assertRaises(md.MarkdownError):
            md.render("::: bananatitle\nx\n:::")

    def test_unclosed_callout_is_rejected(self):
        with self.assertRaises(md.MarkdownError):
            md.render("::: note\nx")

    def test_unclosed_code_fence_is_rejected(self):
        with self.assertRaises(md.MarkdownError):
            md.render("```\nx")


class TestFigures(unittest.TestCase):
    def test_lone_image_becomes_numbered_figure(self):
        res = md.render("![Aliasing of a 7 Hz tone](plots/alias.svg)")
        self.assertEqual(len(res.figures), 1)
        self.assertIn("<figure", res.html)
        self.assertIn("Figure 1", res.html)
        self.assertIn("Aliasing of a 7 Hz tone", res.html)

    def test_figures_number_in_document_order(self):
        res = md.render(
            "![one](a.svg)\n\ntext\n\n![two](b.svg)\n\n![three](c.svg)"
        )
        self.assertEqual(len(res.figures), 3)
        self.assertIn("Figure 1", res.html)
        self.assertIn("Figure 3", res.html)

    def test_figure_classes_from_title(self):
        res = md.render('![x](a.svg "wide dark")')
        self.assertIn('class="figure wide dark"', res.html)

    def test_inline_image_is_not_a_figure(self):
        res = md.render("text with ![icon](i.svg) inline")
        self.assertNotIn("<figure", res.html)
        self.assertIn("<img", res.html)


class TestMetadata(unittest.TestCase):
    def test_reading_time_never_zero(self):
        self.assertEqual(md.render("hi").reading_minutes, 1)

    def test_word_count_ignores_code(self):
        self.assertLess(md.render("```\n" + "word " * 500 + "\n```").word_count, 50)


if __name__ == "__main__":
    unittest.main(verbosity=2)
