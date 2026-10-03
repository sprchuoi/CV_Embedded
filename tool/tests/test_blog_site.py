"""Tests for the blog's curriculum loader, link checker and build.

The generator is what decides the published site's contents, so these tests aim
at the failure modes that would otherwise reach production silently: a renamed
figure, a slug typo, an article file the curriculum does not know about, or a
figure that is built and committed but never referenced by anything.

Run from the repo root:

    python3 -m unittest discover -s tool/tests -t . -v
"""

import importlib.util
import json
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from tool.blog import site, theme  # noqa: E402

CURRICULUM = REPO / "blog" / "curriculum.json"
POSTS = REPO / "blog" / "posts"
PAGES = REPO / "blog" / "pages"
ASSETS = REPO / "docs" / "blog" / "assets"
HAVE_NUMPY = importlib.util.find_spec("numpy") is not None

MINIMAL = {
    "title": "T",
    "tagline": "t",
    "author": {"name": "A"},
    "pages": [],
    "parts": [
        {
            "id": "p1",
            "level": "Beginner",
            "title": "Part one",
            "blurb": "b",
            "articles": [
                {"slug": "one", "title": "One", "summary": "s", "tags": []},
                {"slug": "two", "title": "Two", "summary": "s", "tags": []},
            ],
        }
    ],
}


class TestCurriculumLoader(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.path = self.tmp / "curriculum.json"
        self.posts = self.tmp / "posts"
        self.posts.mkdir()
        self.pages = self.tmp / "pages"
        self.pages.mkdir()

    def write(self, data):
        self.path.write_text(json.dumps(data), encoding="utf-8")

    def test_loads_and_numbers_articles(self):
        self.write(MINIMAL)
        (self.posts / "one.md").write_text("## A\n\nbody\n", encoding="utf-8")
        curriculum = site.load_curriculum(self.path, self.posts, self.pages)
        self.assertEqual(len(curriculum.parts), 1)
        self.assertEqual([a.slug for a in curriculum.articles], ["one", "two"])
        self.assertEqual([a.number for a in curriculum.articles], [1, 2])
        self.assertEqual([a.published for a in curriculum.articles], [True, False])
        self.assertEqual(curriculum.published[0].minutes, 1)

    def test_duplicate_slug_is_rejected(self):
        data = json.loads(json.dumps(MINIMAL))
        data["parts"][0]["articles"][1]["slug"] = "one"
        self.write(data)
        with self.assertRaises(site.CurriculumError) as ctx:
            site.load_curriculum(self.path, self.posts, self.pages)
        self.assertIn("duplicate slug", str(ctx.exception))

    def test_non_kebab_slug_is_rejected(self):
        data = json.loads(json.dumps(MINIMAL))
        data["parts"][0]["articles"][0]["slug"] = "Not_Kebab"
        self.write(data)
        with self.assertRaises(site.CurriculumError):
            site.load_curriculum(self.path, self.posts, self.pages)

    def test_orphan_article_file_is_rejected(self):
        self.write(MINIMAL)
        (self.posts / "orphan.md").write_text("## A\n\nbody\n", encoding="utf-8")
        with self.assertRaises(site.CurriculumError) as ctx:
            site.load_curriculum(self.path, self.posts, self.pages)
        self.assertIn("orphan.md", str(ctx.exception))

    def test_missing_key_is_rejected(self):
        data = json.loads(json.dumps(MINIMAL))
        del data["parts"][0]["articles"][0]["summary"]
        self.write(data)
        with self.assertRaises(site.CurriculumError):
            site.load_curriculum(self.path, self.posts, self.pages)

    def test_malformed_article_reports_the_file(self):
        self.write(MINIMAL)
        (self.posts / "one.md").write_text("# top level heading\n", encoding="utf-8")
        with self.assertRaises(site.CurriculumError) as ctx:
            site.load_curriculum(self.path, self.posts, self.pages)
        self.assertIn("one.md", str(ctx.exception))


class TestLinkChecking(unittest.TestCase):
    def test_broken_relative_link_is_found(self):
        page = Path(tempfile.mkdtemp()) / "a.html"
        problems = site._check_links({page: '<img src="assets/missing.svg">'})
        self.assertEqual(len(problems), 1)
        self.assertIn("missing.svg", problems[0])

    def test_absolute_and_anchor_links_are_ignored(self):
        page = Path(tempfile.mkdtemp()) / "a.html"
        html = ('<a href="https://example.com/x">x</a>'
                '<a href="#section">s</a>'
                '<a href="mailto:a@b.c">m</a>'
                '<a href="//cdn.example.com/y">y</a>')
        self.assertEqual(site._check_links({page: html}), [])

    def test_link_to_a_page_generated_in_the_same_run_passes(self):
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        index, article = tmp / "index.html", tmp / "one.html"
        problems = site._check_links({
            index: '<a href="one.html">one</a>',
            article: '<a href="index.html">home</a>',
        })
        self.assertEqual(problems, [])


class TestFigureIntegrity(unittest.TestCase):
    """Checks the real curriculum and the real figure directory."""

    @classmethod
    def setUpClass(cls):
        cls.curriculum = site.load_curriculum(CURRICULUM, POSTS)

    def referenced(self):
        """slug -> list of figure paths, for every written article."""
        out = {}
        for article in self.curriculum.articles:
            if article.body:
                out[article.slug] = [
                    Path(src).name
                    for src in re.findall(
                        r"!\[[^\]]*\]\((\S+?)(?:\s+\"[^\"]*\")?\)", article.body)
                ]
        return out

    def test_every_article_has_figures(self):
        # A diagram-first blog: an article with no figures is a content bug.
        for slug, figures in self.referenced().items():
            with self.subTest(slug=slug):
                self.assertGreaterEqual(len(figures), 4,
                                        f"{slug} references only {len(figures)} figures")

    def test_every_referenced_figure_exists(self):
        for slug, figures in self.referenced().items():
            for name in figures:
                with self.subTest(slug=slug, figure=name):
                    matches = list(ASSETS.rglob(name))
                    self.assertEqual(len(matches), 1,
                                     f"{name} matched {len(matches)} files")

    def test_no_committed_figure_is_orphaned(self):
        used = {n for names in self.referenced().values() for n in names}
        committed = [p.name for p in ASSETS.rglob("*.svg")]
        self.assertTrue(committed, "no figures committed under docs/blog/assets")
        orphans = sorted(set(committed) - used)
        self.assertEqual(orphans, [], f"unreferenced figures: {orphans}")

    @unittest.skipUnless(HAVE_NUMPY, "figure registry needs numpy for the plot modules")
    def test_every_registered_figure_is_used(self):
        from tool.blog.art import collect

        # Importing the plot modules requires numpy/matplotlib, so this runs
        # only where the build toolchain is installed.
        try:
            registered = {f.name for f in collect()}
        except Exception as exc:  # pragma: no cover - environment problem
            self.skipTest(f"figure registry unavailable: {exc}")
        used = {Path(n).stem for names in self.referenced().values() for n in names}
        unused = sorted(registered - used)
        self.assertEqual(unused, [], f"figures built but never referenced: {unused}")


class TestPages(unittest.TestCase):
    """Standalone pages: the framing prose and the vision document."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.path = self.tmp / "curriculum.json"
        self.posts = self.tmp / "posts"
        self.posts.mkdir()
        self.pages = self.tmp / "pages"
        self.pages.mkdir()

    def write(self, pages):
        data = json.loads(json.dumps(MINIMAL))
        data["pages"] = pages
        self.path.write_text(json.dumps(data), encoding="utf-8")

    def test_loads_a_page_and_its_prose(self):
        self.write([{"slug": "vision", "title": "V", "summary": "s",
                     "placement": "page", "nav": "Vision"}])
        (self.pages / "vision.md").write_text("## A\n\nbody\n", encoding="utf-8")
        c = site.load_curriculum(self.path, self.posts, self.pages)
        self.assertEqual(len(c.pages), 1)
        self.assertTrue(c.pages[0].written)
        self.assertEqual([p.nav for p in c.nav_pages], ["Vision"])

    def test_unwritten_page_is_not_in_the_nav(self):
        self.write([{"slug": "vision", "title": "V", "summary": "s",
                     "placement": "page", "nav": "Vision"}])
        c = site.load_curriculum(self.path, self.posts, self.pages)
        self.assertFalse(c.pages[0].written)
        self.assertEqual(c.nav_pages, [])

    def test_bad_placement_is_rejected(self):
        self.write([{"slug": "v", "title": "V", "summary": "s",
                     "placement": "sidebar"}])
        with self.assertRaises(site.CurriculumError) as ctx:
            site.load_curriculum(self.path, self.posts, self.pages)
        self.assertIn("placement", str(ctx.exception))

    def test_page_slug_colliding_with_a_chapter_is_rejected(self):
        self.write([{"slug": "one", "title": "V", "summary": "s",
                     "placement": "page"}])
        with self.assertRaises(site.CurriculumError) as ctx:
            site.load_curriculum(self.path, self.posts, self.pages)
        self.assertIn("collides", str(ctx.exception))

    def test_orphan_page_file_is_rejected(self):
        self.write([])
        (self.pages / "stray.md").write_text("## A\n\nbody\n", encoding="utf-8")
        with self.assertRaises(site.CurriculumError) as ctx:
            site.load_curriculum(self.path, self.posts, self.pages)
        self.assertIn("stray.md", str(ctx.exception))

    def test_index_placement_is_rendered_into_the_index_only(self):
        self.write([{"slug": "domain", "title": "D", "summary": "s",
                     "placement": "index"}])
        (self.pages / "domain.md").write_text("## Framing\n\nwhy\n",
                                              encoding="utf-8")
        c = site.load_curriculum(self.path, self.posts, self.pages)
        self.assertEqual([p.slug for p in c.pages if p.placement == "index"],
                         ["domain"])
        site_obj = theme.Site(title=c.title, tagline=c.tagline, author=c.author)
        html = site.render_index(site_obj, c)
        self.assertIn('class="framing"', html)
        self.assertIn("why", html)


class TestBuild(unittest.TestCase):
    """Builds a throwaway copy of the repo so nothing in docs/ is touched."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        shutil.copytree(REPO / "blog", self.tmp / "blog")
        # The blog links back to the CV page and to the shared favicon, so the
        # fixture needs them or the link checker is right to complain.
        (self.tmp / "docs").mkdir(exist_ok=True)
        (self.tmp / "docs" / "index.html").write_text("<html></html>", encoding="utf-8")
        (self.tmp / "docs" / "favicon.ico").write_bytes(b"\x00")
        # Figure files, so the link checker has something to resolve.
        for kind in ("diagrams", "plots"):
            src = ASSETS / kind
            if src.is_dir():
                shutil.copytree(src, self.tmp / "docs" / "blog" / "assets" / kind)

    def test_build_writes_index_and_one_page_per_published_article(self):
        report = site.build(self.tmp)
        self.assertEqual(report.errors, [], f"build errors: {report.errors}")
        curriculum = site.load_curriculum(
            self.tmp / "blog" / "curriculum.json", self.tmp / "blog" / "posts",
            self.tmp / "blog" / "pages")
        published = curriculum.published
        self.assertTrue(published, "expected at least one published article")
        self.assertTrue((self.tmp / "docs" / "blog" / "index.html").exists())
        for article in published:
            self.assertTrue((self.tmp / "docs" / "blog" / f"{article.slug}.html").exists())
        # one document per published chapter, plus the index, plus any page that
        # asked for its own document (placement == "page").
        standalone = [p for p in curriculum.pages
                      if p.placement == "page" and p.written]
        for page in standalone:
            self.assertTrue((self.tmp / "docs" / "blog" / page.href).exists())
        self.assertEqual(len(report.pages), len(published) + 1 + len(standalone))

    def test_build_copies_the_stylesheet(self):
        site.build(self.tmp)
        for asset in ("blog.css", "blog.js"):
            self.assertTrue((self.tmp / "docs" / "blog" / "assets" / asset).exists())

    def test_build_is_idempotent(self):
        site.build(self.tmp)
        first = (self.tmp / "docs" / "blog" / "index.html").read_text()
        site.build(self.tmp)
        self.assertEqual(first, (self.tmp / "docs" / "blog" / "index.html").read_text())

    def test_missing_figure_fails_the_build_and_writes_nothing(self):
        plots = self.tmp / "docs" / "blog" / "assets" / "plots"
        if plots.is_dir():
            shutil.rmtree(plots)
        report = site.build(self.tmp, strict=True)
        self.assertTrue(report.errors)
        self.assertTrue(any("missing figure" in e for e in report.errors))
        self.assertFalse((self.tmp / "docs" / "blog" / "index.html").exists(),
                         "a failed strict build must not publish a partial site")

    def test_generated_pages_are_well_formed(self):
        from html.parser import HTMLParser

        site.build(self.tmp)
        void = {"area", "base", "br", "col", "embed", "hr", "img", "input",
                "link", "meta", "param", "source", "track", "wbr"}

        for page in (self.tmp / "docs" / "blog").glob("*.html"):
            stack, problems = [], []

            class Balance(HTMLParser):
                def handle_starttag(self, tag, attrs):
                    if tag not in void:
                        stack.append(tag)

                def handle_endtag(self, tag):
                    if tag in void:
                        return
                    if not stack:
                        problems.append(f"stray </{tag}>")
                    elif stack[-1] == tag:
                        stack.pop()
                    else:
                        problems.append(f"</{tag}> closes <{stack[-1]}>")

            parser = Balance(convert_charrefs=True)
            parser.feed(page.read_text(encoding="utf-8"))
            with self.subTest(page=page.name):
                self.assertEqual(problems, [])
                self.assertEqual(stack, [])


class TestDiagramLayout(unittest.TestCase):
    """Hand-built diagrams must not draw outside their own canvas.

    A figure whose content runs past the canvas edge is silently clipped, which
    is invisible in the module and obvious only to a reader. This is checked
    because it has already happened twice: once in the FFT decimation tree,
    where a callout was taller than the canvas, and once in a decibel figure
    written with the same mistake.
    """

    @staticmethod
    def _lowest_content(svg: str) -> float:
        lowest = 0.0
        for element in re.findall(r"<rect[^>]*>", svg):
            y = re.search(r'\by="([-\d.]+)"', element)
            h = re.search(r'\bheight="([-\d.]+)"', element)
            if y and h:
                lowest = max(lowest, float(y.group(1)) + float(h.group(1)))
        for element in re.findall(r"<text[^>]*>", svg):
            y = re.search(r'\by="([-\d.]+)"', element)
            if y:
                lowest = max(lowest, float(y.group(1)))
        for _, y in re.findall(r'\bd="M ([-\d.]+) ([-\d.]+)', svg):
            lowest = max(lowest, float(y))
        return lowest

    def test_no_hand_built_diagram_overflows_its_canvas(self):
        from tool.blog.art import MODULES, FigureError, collect

        try:
            figures = collect(kinds=("diagrams",))
        except FigureError as exc:      # pragma: no cover - environment problem
            self.skipTest(f"figure registry unavailable: {exc}")
        self.assertTrue(figures, "expected diagram modules to be registered")

        problems = []
        for figure in figures:
            svg = figure.builder()
            if not svg.lstrip().startswith("<svg"):
                continue
            match = re.search(r'\bheight="(\d+)"', svg)
            if not match:
                continue
            canvas = float(match.group(1))
            lowest = self._lowest_content(svg)
            if lowest > canvas:
                problems.append(
                    f"{figure.name}: canvas {canvas:.0f}, content reaches {lowest:.1f}")
        self.assertEqual(problems, [], "diagrams overflow their canvas")

    def test_every_diagram_declares_a_title(self):
        """An SVG with no <title> has no accessible name."""
        from tool.blog.art import FigureError, collect

        try:
            figures = collect(kinds=("diagrams",))
        except FigureError as exc:      # pragma: no cover
            self.skipTest(f"figure registry unavailable: {exc}")
        missing = [f.name for f in figures
                   if "<title>" not in f.builder()]
        self.assertEqual(missing, [], "diagrams with no accessible title")


class TestRenderedArticleMarkup(unittest.TestCase):
    """Guards the generated HTML against regressions the parser could hide."""

    @classmethod
    def setUpClass(cls):
        cls.curriculum = site.load_curriculum(CURRICULUM, POSTS)
        cls.site = theme.Site(
            title=cls.curriculum.title,
            tagline=cls.curriculum.tagline,
            author=cls.curriculum.author,
        )

    def test_article_page_has_title_standfirst_and_toc(self):
        if len(self.curriculum.published) < 2:
            self.skipTest("needs at least two published articles to build a pager")
        article = self.curriculum.published[0]
        html = site.render_article(self.site, self.curriculum, article, None,
                                  self.curriculum.published[1])
        self.assertIn(f"<h1>{article.title}</h1>", html)
        self.assertIn(article.summary, html)
        self.assertIn('class="toc"', html)
        self.assertIn('class="pager"', html)
        self.assertIn("MathJax", html)

    def test_index_lists_every_planned_chapter(self):
        html = site.render_index(self.site, self.curriculum)
        self.assertEqual(html.count('class="chapter is-planned"'),
                         len(self.curriculum.articles) - len(self.curriculum.published))
        for part in self.curriculum.parts:
            self.assertIn(part.title, html)


if __name__ == "__main__":
    unittest.main(verbosity=2)
