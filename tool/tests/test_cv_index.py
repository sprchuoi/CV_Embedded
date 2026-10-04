"""Tests for the CV page's Summary/Full toggle and its GitHub star badges.

docs/index.html now renders the work history twice from the same .dox: the
compact flow chart ("Summary", the default pane) and the full detail inline
("Full"), the latter being exactly what each docs/work/<company>.html page
shows. These tests pin that they stay identical, that the toggle's ARIA wiring
points at real panels, and that the star-count script parses every GitHub link
the page actually contains.

Run from the repo root:

    python3 -m unittest discover -s tool/tests -t . -v
"""

import json
import re
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
TOOL = REPO / "tool"
sys.path.insert(0, str(TOOL))

import cv_dox as C  # noqa: E402
import cv_html as H  # noqa: E402

DOX = REPO / "docs" / "NguyenQuangBinh_CV.dox"
INDEX = REPO / "docs" / "index.html"
WORK = REPO / "docs" / "work"
CV_JS = REPO / "docs" / "assets" / "js" / "cv.js"
DOM_TEST = TOOL / "tests" / "cv_dom_test.js"
CSS = REPO / "docs" / "assets" / "css" / "work-flow.css"

NODE = shutil.which("node")

SECTIONS = C.parse_doc(DOX.read_text(encoding="utf-8"))
COMPANIES = H.work_companies(SECTIONS["work_experience"])

FULL_START = "<!-- WORK_EXPERIENCE_FULL_START -->"
FULL_END = "<!-- WORK_EXPERIENCE_FULL_END -->"
HTML = INDEX.read_text(encoding="utf-8")


def between(text, start, end):
    """The generated region between two HTML markers."""
    return text.split(start, 1)[1].split(end, 1)[0]


def github_hrefs(html):
    """Every link to github.com, exactly as the browser sees it.

    Includes the profile link and the release-asset link, which name no single
    repo: the star script must leave those alone rather than invent one.
    """
    return re.findall(r'href="(https?://github\.com/[^"]*)"', html)


def repo_of(url):
    """The owner/repo a GitHub URL names, or None -- the oracle for the JS."""
    path = url.split("github.com/", 1)[1]
    path = path.split("?", 1)[0].split("#", 1)[0].rstrip("/")
    if path.endswith(".git"):
        path = path[:-4]
    parts = [p for p in path.split("/") if p]
    return "/".join(parts) if len(parts) == 2 else None


class ToggleMarkupTests(unittest.TestCase):
    """The Summary/Full control is wired as two ARIA tabs and two panels."""

    def test_two_tabs_and_two_panels_exist(self):
        self.assertEqual(len(re.findall(r'role="tab"', HTML)), 2)
        self.assertEqual(len(re.findall(r'role="tabpanel"', HTML)), 2)
        self.assertIn('role="tablist"', HTML)

    def test_each_tab_controls_a_real_panel(self):
        controls = re.findall(r'role="tab"[^>]*aria-controls="([^"]+)"', HTML)
        self.assertEqual(len(controls), 2)
        for control in controls:
            self.assertIn(f'id="{control}"', HTML)

    def test_summary_is_selected_and_full_starts_hidden(self):
        summary = HTML.split('id="work-tab-summary"', 1)[1].split(">", 1)[0]
        full = HTML.split('id="work-tab-full"', 1)[1].split(">", 1)[0]
        self.assertIn('aria-selected="true"', summary)
        self.assertIn("is-active", summary)
        self.assertIn('aria-selected="false"', full)
        self.assertNotIn("is-active", full)

        full_panel = HTML.split('id="work-view-full"', 1)[1].split(">", 1)[0]
        self.assertIn("hidden", full_panel)
        summary_panel = HTML.split('id="work-view-summary"', 1)[1].split(">", 1)[0]
        self.assertNotIn("hidden", summary_panel)

    def test_hidden_attribute_actually_hides(self):
        # The pane styles set display on other elements; [hidden] must win.
        self.assertIn("[hidden]", CSS.read_text(encoding="utf-8"))


class FullViewTests(unittest.TestCase):
    """The Full pane is the same content as the company pages."""

    def setUp(self):
        self.full = between(HTML, FULL_START, FULL_END)

    def test_full_view_is_not_empty(self):
        self.assertGreater(len(self.full.strip()), 500)

    def test_full_view_matches_the_company_pages_exactly(self):
        for company in COMPANIES:
            rendered = H.render_company_roles(company)
            self.assertIn(rendered, self.full,
                          f"{company.key}: inline view drifted from render_company_roles")
            page = (WORK / f"{H.work_slug(company.key)}.html").read_text(encoding="utf-8")
            self.assertIn(rendered, page,
                          f"{company.key}: company page drifted from render_company_roles")

    def test_every_company_links_to_its_page(self):
        for company in COMPANIES:
            link = f'href="work/{H.work_slug(company.key)}.html"'
            self.assertIn(link, self.full)
            self.assertTrue((REPO / "docs" / "work" / f"{H.work_slug(company.key)}.html").exists())

    def test_summary_pane_keeps_the_chart(self):
        summary = between(HTML, "<!-- WORK_EXPERIENCE_START -->", "<!-- WORK_EXPERIENCE_END -->")
        self.assertIn("work-flow", summary)
        self.assertNotIn("work-full-company", summary)

    def test_full_view_has_no_chart(self):
        self.assertNotIn("work-flow-card", self.full)


class StarBadgeTests(unittest.TestCase):
    """The GitHub links the star script must be able to turn into badges."""

    def test_page_loads_the_script_deferred(self):
        self.assertIn('<script src="assets/js/cv.js" defer></script>', HTML)
        self.assertTrue(CV_JS.exists())

    def test_badge_style_exists(self):
        self.assertIn(".git-stars", CSS.read_text(encoding="utf-8"))

    def test_the_page_has_github_repo_links_to_decorate(self):
        self.assertGreaterEqual(sum(1 for u in github_hrefs(HTML) if repo_of(u)), 5)

    def test_the_page_also_keeps_github_links_that_are_not_repos(self):
        # Guards the test above from being vacuous: the profile link and the
        # release-asset link are both present and neither names a repo.
        non_repos = [u for u in github_hrefs(HTML) if repo_of(u) is None]
        self.assertTrue(any(u.rstrip("/").endswith("github.com/sprchuoi")
                            for u in non_repos), non_repos)
        self.assertTrue(any("/releases/download/" in u for u in non_repos), non_repos)

    @unittest.skipUnless(NODE, "node is not installed")
    def test_the_script_parses_the_page_links_exactly_like_the_oracle(self):
        urls = github_hrefs(HTML)
        program = (
            "var cv = require(%s);"
            "var urls = %s;"
            "console.log(JSON.stringify(urls.map(function (u) { return cv.repoFromHref(u); })));"
            % (json.dumps(str(CV_JS)), json.dumps(urls))
        )
        proc = subprocess.run([NODE, "-e", program], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)

        parsed = json.loads(proc.stdout)
        self.assertEqual(len(parsed), len(urls))
        self.assertEqual(parsed, [repo_of(u) for u in urls],
                         "the star script disagrees with the page's link shapes")


@unittest.skipUnless(NODE, "node is not installed")
class JavaScriptTests(unittest.TestCase):
    """The script itself, checked by the Node that the tests can find."""

    def test_cv_js_is_syntactically_valid(self):
        proc = subprocess.run([NODE, "--check", str(CV_JS)], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_repo_parser_accepts_repo_urls_and_rejects_the_rest(self):
        cases = [
            ("https://github.com/sprchuoi/Smart_Server", "sprchuoi/Smart_Server"),
            ("http://github.com/owner/repo", "owner/repo"),
            ("https://github.com/owner/repo.git", "owner/repo"),
            ("https://github.com/owner/repo/", "owner/repo"),
            ("https://github.com/owner/repo?tab=readme-ov-file", "owner/repo"),
            ("https://github.com/sprchuoi", None),
            ("https://github.com/sprchuoi/", None),
            ("https://github.com/owner/repo/tree/main", None),
            ("https://gitlab.com/owner/repo", None),
            ("https://leetcode.com/sprchuoi", None),
            ("mailto:quangbinhlxcity@gmail.com", None),
        ]
        program = (
            "var cv = require(%s);"
            "var urls = %s;"
            "console.log(JSON.stringify(urls.map(function (u) { return cv.repoFromHref(u); })));"
            % (json.dumps(str(CV_JS)), json.dumps([c[0] for c in cases]))
        )
        proc = subprocess.run([NODE, "-e", program], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(json.loads(proc.stdout), [c[1] for c in cases])


@unittest.skipUnless(NODE, "node is not installed")
class DomBehaviourTests(unittest.TestCase):
    """cv.js driven against a stub DOM in Node, so the features really run.

    The markup tests above pin the contract; this one proves the toggle switches
    panes and moves the tab stop, the arrow keys work, the badges are filled
    from the API, and a GitHub link that is not a repo is left alone.
    """

    def test_toggle_and_star_badges_behave(self):
        proc = subprocess.run([NODE, str(DOM_TEST)], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)


if __name__ == "__main__":
    unittest.main()
