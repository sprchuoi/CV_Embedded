"""Tests for the work-history flow chart and the company detail pages.

docs/index.html shows the work history as a linked flow chart -- company, role
and dates, no bullets -- and docs/work/<company>.html carries the detail. These
tests pin the contract between the two: every chart step resolves to a page
that exists, the chart is a timeline rather than a second copy of the CV, the
detail pages keep every bullet the .dox holds, and the committed HTML still
matches a fresh render.

Run from the repo root:

    python3 -m unittest discover -s tool/tests -t . -v
"""

import io
import re
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
TOOL = REPO / "tool"
sys.path.insert(0, str(TOOL))

import build_work_pages as W  # noqa: E402
import cv_dox as C  # noqa: E402
import cv_html as H  # noqa: E402
import update_html_from_dox as U  # noqa: E402

DOX = REPO / "docs" / "NguyenQuangBinh_CV.dox"
INDEX = REPO / "docs" / "index.html"
WORK = REPO / "docs" / "work"

DOX_TEXT = DOX.read_text(encoding="utf-8")
SECTIONS = C.parse_doc(DOX_TEXT)
WORK_BLOCK = SECTIONS["work_experience"]
COMPANIES = H.work_companies(WORK_BLOCK)


def count_bullets(company: C.Block) -> int:
    """Every bullet the detail body will emit: role bodies + nested projects."""
    total = 0
    for role in company.children:
        blocks = [role.body] + [child.body for child in role.children]
        for body in blocks:
            for item in C.parse_items(body):
                if isinstance(item, C.Bullet):
                    total += 1 + len(item.children)
    return total


class ChartTests(unittest.TestCase):
    """The chart on docs/index.html."""

    def setUp(self):
        self.chart = U.build_work_chart(WORK_BLOCK)

    def test_one_step_per_role(self):
        roles = [role for company in COMPANIES for role in company.children]
        self.assertEqual(len(re.findall(r'<li class="work-flow-step">', self.chart)),
                         len(roles))
        for role in roles:
            _, dates = H.split_title_dates(role.title)
            self.assertIn(dates, self.chart)

    def test_every_step_links_to_a_generated_page(self):
        links = re.findall(r'class="work-flow-card[^"]*" href="([^"]+)"', self.chart)
        self.assertEqual(len(links), sum(len(c.children) for c in COMPANIES))
        for link in links:
            self.assertTrue(link.startswith("work/"), link)
            self.assertTrue((REPO / "docs" / link).exists(),
                            f"chart links to a missing page: {link}")

    def test_chart_carries_no_bullet_detail(self):
        self.assertNotIn("<ul", self.chart)
        self.assertNotIn("Responsibilities", self.chart)
        self.assertNotIn("<li>", self.chart)

    def test_chart_marks_the_current_role(self):
        self.assertEqual(self.chart.count("is-current"), 1)
        current_company, _ = H.split_title_dates(COMPANIES[0].title)
        self.assertIn(current_company, self.chart)

    def test_committed_index_contains_the_fresh_chart(self):
        self.assertIn(self.chart, INDEX.read_text(encoding="utf-8"))

    def test_company_without_roles_is_skipped(self):
        dox = ("@section work_experience WORK\n"
               "@subsection exp_a A | Loc\n"
               "@subsubsection r T | D\n"
               "- b\n"
               "@subsection exp_empty Empty | Loc\n")
        chart = U.build_work_chart(C.parse_doc(dox)["work_experience"])
        self.assertIn(">A<", chart)
        self.assertNotIn("Empty", chart)


class WorkPageTests(unittest.TestCase):
    """The company pages under docs/work/."""

    def test_one_page_per_company_with_roles(self):
        _, pages = W.planned_pages(DOX_TEXT)
        expected = {f"{H.work_slug(c.key)}.html" for c in COMPANIES}
        self.assertEqual(set(pages), expected)
        for filename in expected:
            self.assertTrue((WORK / filename).exists(), filename)

    def test_committed_pages_match_a_fresh_render(self):
        _, pages = W.planned_pages(DOX_TEXT)
        for filename, html in pages.items():
            self.assertEqual((WORK / filename).read_text(encoding="utf-8"), html,
                             f"{filename} is stale -- run tool/build_work_pages.py")

    def test_detail_pages_keep_every_bullet(self):
        for company in COMPANIES:
            page = (WORK / f"{H.work_slug(company.key)}.html").read_text(encoding="utf-8")
            body = page.split('<div class="work-page-roles">', 1)[1]
            self.assertEqual(body.count("<li>"), count_bullets(company),
                             f"{company.key}: bullet count drifted")
            for role in company.children:
                title, dates = H.split_title_dates(role.title)
                self.assertIn(title, body)
                self.assertIn(dates, body)

    def test_pages_link_back_to_the_cv(self):
        for company in COMPANIES:
            page = (WORK / f"{H.work_slug(company.key)}.html").read_text(encoding="utf-8")
            self.assertIn('href="../index.html"', page)
            self.assertIn(W.GENERATED_MARK, page)

    def test_nav_lists_every_company_and_marks_the_current_one(self):
        for company in COMPANIES:
            page = (WORK / f"{H.work_slug(company.key)}.html").read_text(encoding="utf-8")
            nav = page.split('class="work-page-links"', 1)[1].split("</ul>", 1)[0]
            self.assertEqual(nav.count('class="work-page-link'), len(COMPANIES))
            self.assertEqual(nav.count("is-active"), 1)
            self.assertIn(f'href="{H.work_slug(company.key)}.html"', nav)

    def test_duplicate_slugs_are_rejected(self):
        dox = ("@section work_experience WORK\n"
               "@subsection exp_x A | Loc\n"
               "@subsubsection r1 T | D\n"
               "- b\n"
               "@subsection exp_x B | Loc\n"
               "@subsubsection r2 T | D\n"
               "- b\n")
        with self.assertRaises(ValueError):
            W.planned_pages(dox)

    def test_missing_work_section_is_rejected(self):
        with self.assertRaises(ValueError):
            W.planned_pages("@section summary S\n\nhello\n")

    def test_stale_page_is_deleted_but_hand_written_files_survive(self):
        with tempfile.TemporaryDirectory() as tmp:
            work_dir = Path(tmp)
            (work_dir / "old.html").write_text(W.GENERATED_MARK, encoding="utf-8")
            (work_dir / "handwritten.html").write_text("<html>mine</html>",
                                                       encoding="utf-8")
            original = W.WORK_DIR
            W.WORK_DIR = work_dir
            try:
                with redirect_stdout(io.StringIO()):
                    rc = W.main()
            finally:
                W.WORK_DIR = original

            self.assertEqual(rc, 0)
            self.assertFalse((work_dir / "old.html").exists())
            self.assertTrue((work_dir / "handwritten.html").exists())
            self.assertTrue((work_dir / "marvell.html").exists())


if __name__ == "__main__":
    unittest.main()
