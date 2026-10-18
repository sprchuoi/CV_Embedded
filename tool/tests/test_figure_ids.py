"""Figure SVGs must be reproducible on a machine that is not this one.

The committed SVGs under ``docs/blog/assets/`` are checked by regenerating them
and diffing the tree, so any byte the renderer varies between environments fails
CI even though the drawing is identical. matplotlib has one such byte: the ids it
derives from a hash of the clip path, which shift between Python builds
(3.11 and 3.12 disagree) while every other byte of the file matches.

``normalise_ids`` rewrites those derived ids to a sequence number. These tests
pin the rewrite itself — that it is deterministic, that it keeps readable ids,
and that two different renderings of the same figure normalise to the same bytes
— and then the rest of the suite covers the figures it is applied to.

They live in their own file rather than in ``test_blog_site.py`` because the
behaviour they pin is about reproducibility, not about the site.
"""

from __future__ import annotations

import unittest

from tool.blog.art import normalise_ids

# The two ids the same figure produced on Python 3.11 and 3.12, from the run
# that failed CI. Everything else in those two files was byte-identical.
RENDER_A = (
    '<svg><defs><clipPath id="p3ea2d041b1"><rect/></clipPath></defs>'
    '<g clip-path="url(#p3ea2d041b1)"><path d="M0 0"/></g></svg>'
)
RENDER_B = (
    '<svg><defs><clipPath id="pbe6f3cc4a4"><rect/></clipPath></defs>'
    '<g clip-path="url(#pbe6f3cc4a4)"><path d="M0 0"/></g></svg>'
)


class TestNormaliseIds(unittest.TestCase):
    def test_two_renderings_of_one_figure_normalise_identically(self):
        self.assertEqual(normalise_ids(RENDER_A), normalise_ids(RENDER_B))

    def test_the_definition_and_the_reference_still_agree(self):
        once = normalise_ids(RENDER_A)
        self.assertIn('id="p1"', once)
        self.assertIn("url(#p1)", once)
        self.assertNotIn("p3ea2d041b1", once)

    def test_readable_ids_are_left_alone(self):
        markup = ('<g id="figure_1"><g id="axes_2"/></g>')
        self.assertEqual(normalise_ids(markup), markup)

    def test_the_mapping_follows_first_appearance(self):
        markup = (
            '<defs><clipPath id="m0123456789"/><clipPath id="pabcdef0123"/></defs>'
            '<g clip-path="url(#pabcdef0123)"/><g clip-path="url(#m0123456789)"/>'
        )
        self.assertEqual(
            normalise_ids(markup),
            '<defs><clipPath id="m1"/><clipPath id="p1"/></defs>'
            '<g clip-path="url(#p1)"/><g clip-path="url(#m1)"/>',
        )

    def test_the_rewrite_is_idempotent(self):
        once = normalise_ids(RENDER_A)
        self.assertEqual(normalise_ids(once), once)


if __name__ == "__main__":
    unittest.main()
