"""Curriculum loading, page assembly and the build itself.

Two design decisions are worth stating up front, because they are what keeps
this site from rotting:

1. **curriculum.json owns structure, Markdown owns prose.** Every chapter --
   including ones not written yet -- is listed in the curriculum, so the
   roadmap on the index page is always the full plan. Whether a chapter is
   *published* is decided by one thing only: does ``blog/posts/<slug>.md``
   exist? There is no second `status` field to drift out of sync with reality.

2. **The build fails on a broken figure.** Every relative ``src``/``href`` in
   generated HTML is resolved against the output directory after all pages are
   written. A renamed SVG becomes a build error instead of a broken image on
   the live site.
"""

from __future__ import annotations

import json
import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path

from . import markdown as md
from . import theme

EXCERPT_SEP = "\n\n"


class CurriculumError(ValueError):
    """Raised when curriculum.json or the posts directory is inconsistent."""


# --------------------------------------------------------------------------- #
# Model
# --------------------------------------------------------------------------- #


@dataclass
class Article:
    slug: str
    title: str
    summary: str
    tags: list[str]
    part_id: str
    part_title: str
    level: str
    number: int  # 1-based position across the whole curriculum
    number_in_part: int
    order: int
    updated: str | None = None
    body: str | None = None
    rendered: md.RenderResult | None = None

    @property
    def published(self) -> bool:
        return self.body is not None

    @property
    def href(self) -> str:
        return f"{self.slug}.html"

    @property
    def minutes(self) -> int:
        return self.rendered.reading_minutes if self.rendered else 0


@dataclass
class Part:
    id: str
    level: str
    title: str
    blurb: str
    articles: list[Article] = field(default_factory=list)


@dataclass
class Page:
    """A standalone piece of prose that is not a chapter of the course.

    ``placement`` decides where it goes:

    ``page``
        its own document at ``docs/blog/<slug>.html``, optionally in the header
        nav via ``nav``.
    ``index``
        rendered inline on the blog index, above the roadmap -- used for the
        framing that should be read before the curriculum.
    """

    slug: str
    title: str
    summary: str
    placement: str
    nav: str | None = None
    body: str | None = None
    rendered: md.RenderResult | None = None

    @property
    def href(self) -> str:
        return f"{self.slug}.html"

    @property
    def written(self) -> bool:
        return self.body is not None


@dataclass
class Curriculum:
    title: str
    tagline: str
    author: dict
    parts: list[Part] = field(default_factory=list)
    articles: list[Article] = field(default_factory=list)
    pages: list[Page] = field(default_factory=list)

    @property
    def published(self) -> list[Article]:
        return [a for a in self.articles if a.published]

    @property
    def figures(self) -> int:
        total = sum(len(a.rendered.figure_captions)
                    for a in self.articles if a.rendered)
        return total + sum(len(p.rendered.figure_captions)
                           for p in self.pages if p.rendered)

    @property
    def nav_pages(self) -> list[Page]:
        """Pages that asked to appear in the header nav."""
        return [p for p in self.pages if p.nav and p.written]

    def by_slug(self, slug: str) -> Article | None:
        return next((a for a in self.articles if a.slug == slug), None)

    def page_by_slug(self, slug: str) -> Page | None:
        return next((p for p in self.pages if p.slug == slug), None)

    def page_at(self, placement: str) -> Page | None:
        return next((p for p in self.pages
                     if p.placement == placement and p.written), None)


PLACEMENTS = ("page", "index")


def load_curriculum(path: Path, posts_dir: Path,
                    pages_dir: Path | None = None) -> Curriculum:
    """Read curriculum.json, attach any available prose, and validate.

    ``pages_dir`` holds the non-chapter prose (``blog/pages/*.md``); it defaults
    to a sibling of ``posts_dir`` so existing callers keep working.
    """
    if pages_dir is None:
        pages_dir = posts_dir.parent / "pages"
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise CurriculumError(f"curriculum not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise CurriculumError(f"{path.name} is not valid JSON: {exc}") from exc

    for key in ("title", "tagline", "author", "parts"):
        if key not in raw:
            raise CurriculumError(f"curriculum is missing the '{key}' key")

    curriculum = Curriculum(
        title=raw["title"], tagline=raw["tagline"], author=raw["author"]
    )

    seen: dict[str, str] = {}
    number = 0
    for p_index, part_raw in enumerate(raw["parts"], start=1):
        for key in ("id", "level", "title", "blurb", "articles"):
            if key not in part_raw:
                raise CurriculumError(f"part #{p_index} is missing '{key}'")
        part = Part(
            id=part_raw["id"],
            level=part_raw["level"],
            title=part_raw["title"],
            blurb=part_raw["blurb"],
        )
        if not part_raw["articles"]:
            raise CurriculumError(f"part '{part.id}' has no articles")

        for a_index, art_raw in enumerate(part_raw["articles"], start=1):
            number += 1
            for key in ("slug", "title", "summary"):
                if key not in art_raw:
                    raise CurriculumError(
                        f"article #{a_index} in part '{part.id}' is missing '{key}'"
                    )
            slug = art_raw["slug"]
            if slug in seen:
                raise CurriculumError(
                    f"duplicate slug '{slug}' (in '{part.id}' and '{seen[slug]}')"
                )
            seen[slug] = part.id
            if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
                raise CurriculumError(f"slug '{slug}' must be lower-case kebab-case")

            article = Article(
                slug=slug,
                title=art_raw["title"],
                summary=art_raw["summary"],
                tags=list(art_raw.get("tags", [])),
                part_id=part.id,
                part_title=part.title,
                level=part.level,
                number=number,
                number_in_part=a_index,
                order=number,
                updated=art_raw.get("updated"),
            )

            source = posts_dir / f"{slug}.md"
            if source.exists():
                article.body = source.read_text(encoding="utf-8").strip() + "\n"
                try:
                    article.rendered = md.render(article.body)
                except md.MarkdownError as exc:
                    raise CurriculumError(f"{source.name}: {exc}") from exc
            part.articles.append(article)

        curriculum.parts.append(part)
        curriculum.articles.extend(part.articles)

    # An article file that the curriculum does not know about is a silent
    # orphan -- it would never be linked, so fail instead.
    if posts_dir.exists():
        known = set(seen)
        for source in sorted(posts_dir.glob("*.md")):
            if source.stem not in known:
                raise CurriculumError(
                    f"{source.name} has no entry in {path.name}; add it to a part "
                    "or delete the file"
                )

    # ------------------------------------------------------------- pages --
    page_slugs: set[str] = set()
    for index, page_raw in enumerate(raw.get("pages", []), start=1):
        for key in ("slug", "title", "summary", "placement"):
            if key not in page_raw:
                raise CurriculumError(f"page #{index} is missing '{key}'")
        slug = page_raw["slug"]
        if slug in seen:
            raise CurriculumError(
                f"page slug '{slug}' collides with a chapter slug")
        if slug in page_slugs:
            raise CurriculumError(f"duplicate page slug '{slug}'")
        page_slugs.add(slug)
        if page_raw["placement"] not in PLACEMENTS:
            raise CurriculumError(
                f"page '{slug}': placement must be one of {PLACEMENTS}")
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
            raise CurriculumError(f"page slug '{slug}' must be kebab-case")

        page = Page(slug=slug, title=page_raw["title"],
                    summary=page_raw["summary"],
                    placement=page_raw["placement"], nav=page_raw.get("nav"))
        source = pages_dir / f"{slug}.md"
        if source.exists():
            page.body = source.read_text(encoding="utf-8").strip() + "\n"
            try:
                page.rendered = md.render(page.body)
            except md.MarkdownError as exc:
                raise CurriculumError(f"{source.name}: {exc}") from exc
        curriculum.pages.append(page)

    if pages_dir.exists():
        declared = page_slugs
        for source in sorted(pages_dir.glob("*.md")):
            if source.stem not in declared:
                raise CurriculumError(
                    f"{source.name} has no entry under 'pages' in {path.name}; "
                    "add it or delete the file"
                )
    return curriculum


# --------------------------------------------------------------------------- #
# Link checking
# --------------------------------------------------------------------------- #

_REL_LINK_RE = re.compile(r'(?:src|href)="([^"#][^"]*)"')
_ABSOLUTE_RE = re.compile(r"^(?:[a-z][a-z0-9+.-]*:|//)", re.IGNORECASE)


def _check_links(pages: dict[Path, str]) -> list[str]:
    """Every relative link in the generated pages must resolve on disk."""
    problems: list[str] = []
    written = {p.resolve() for p in pages}
    for page, html in sorted(pages.items()):
        for target in _REL_LINK_RE.findall(html):
            if _ABSOLUTE_RE.match(target) or target.startswith("#"):
                continue
            resolved = (page.parent / target.split("#", 1)[0]).resolve()
            if resolved in written or resolved.exists():
                continue
            problems.append(f"{page.name}: broken link -> {target}")
    return problems


def _check_orphan_assets(curriculum: Curriculum, docs_blog: Path) -> list[str]:
    """Figures nothing references are dead weight in the published site."""
    used: set[str] = set()
    bodies = [a.body for a in curriculum.articles if a.body]
    bodies += [p.body for p in curriculum.pages if p.body]
    for body in bodies:
        for src in re.findall(r"!\[[^\]]*\]\((\S+?)(?:\s+\"[^\"]*\")?\)", body):
            used.add(Path(src).name)

    warnings: list[str] = []
    for sub in ("diagrams", "plots", "images"):
        folder = docs_blog / "assets" / sub
        if not folder.is_dir():
            continue
        for asset in sorted(folder.iterdir()):
            if asset.is_file() and asset.name not in used:
                warnings.append(f"unreferenced figure: assets/{sub}/{asset.name}")
    return warnings


# --------------------------------------------------------------------------- #
# Page rendering
# --------------------------------------------------------------------------- #


def _level_badge(level: str) -> str:
    return f'<span class="level-badge" data-level="{theme.esc(level)}">{theme.esc(level)}</span>'


def _taglist(tags: list[str]) -> str:
    if not tags:
        return ""
    items = "".join(f'<span class="tag">{theme.esc(t)}</span>' for t in tags)
    return f'<div class="taglist">{items}</div>'


def _toc(article: Article) -> str:
    headings = [h for h in article.rendered.toc if h.level <= 3]
    if len(headings) < 2:
        return ""
    items = "".join(
        f'<li class="lvl-{h.level}"><a href="#{h.anchor}">{theme.esc(h.text)}</a></li>'
        for h in headings
    )
    return (
        '<nav class="toc" aria-label="On this page">\n'
        '<p class="toc-title">On this page</p>\n'
        f"<ol>{items}</ol>\n</nav>"
    )


def render_article(site: theme.Site, curriculum: Curriculum, article: Article,
                   prev: Article | None, next_: Article | None) -> str:
    assert article.rendered is not None
    meta_bits = [_level_badge(article.level), f"<span>{article.minutes} min read</span>"]
    if article.updated:
        meta_bits.append(f'<span>Updated {theme.esc(article.updated)}</span>')

    pager = ""
    if prev or next_:
        left = (
            f'<a class="prev" href="{prev.href}"><span class="dir">&larr; Previous</span>'
            f'<span class="ttl">{theme.esc(prev.title)}</span></a>'
            if prev else "<span></span>"
        )
        right = (
            f'<a class="next" href="{next_.href}"><span class="dir">Next &rarr;</span>'
            f'<span class="ttl">{theme.esc(next_.title)}</span></a>'
            if next_ else "<span></span>"
        )
        pager = f'<nav class="pager" aria-label="Chapter navigation">{left}{right}</nav>'

    body = f"""<div class="layout">
{_toc(article)}
<main id="main" class="prose">
  <nav class="breadcrumb" aria-label="Breadcrumb">
    <a href="index.html">Curriculum</a><span class="sep">/</span>{theme.esc(article.part_title)}
  </nav>
  <header class="article-head">
    <h1>{theme.esc(article.title)}</h1>
    <p class="article-standfirst">{theme.esc(article.summary)}</p>
    <div class="article-meta">{''.join(meta_bits)}{_taglist(article.tags)}</div>
  </header>
{article.rendered.html}
{pager}
</main>
</div>"""

    return theme.document(
        site=site, depth=0, active="home",
        title=f"{article.title} - {site.title}",
        description=article.summary,
        body=body,
    )


def render_page(site: theme.Site, page: Page) -> str:
    """A standalone document (placement == "page")."""
    assert page.rendered is not None
    toc = ""
    headings = [h for h in page.rendered.toc if h.level <= 3]
    if len(headings) >= 2:
        items = "".join(
            f'<li class="lvl-{h.level}"><a href="#{h.anchor}">{theme.esc(h.text)}</a></li>'
            for h in headings
        )
        toc = ('<nav class="toc" aria-label="On this page">\n'
               '<p class="toc-title">On this page</p>\n'
               f"<ol>{items}</ol>\n</nav>")

    body = f"""<div class="layout">
{toc}
<main id="main" class="prose">
  <header class="article-head">
    <h1>{theme.esc(page.title)}</h1>
    <p class="article-standfirst">{theme.esc(page.summary)}</p>
  </header>
{page.rendered.html}
</main>
</div>"""

    return theme.document(
        site=site, depth=0, active=page.href,
        title=f"{page.title} - {site.title}",
        description=page.summary,
        body=body,
    )


def render_index(site: theme.Site, curriculum: Curriculum) -> str:
    published = curriculum.published
    total = len(curriculum.articles)

    features = "".join(
        f'<a class="feature" href="{a.href}">'
        f"{_level_badge(a.level)}"
        f"<h3>{theme.esc(a.title)}</h3>"
        f"<p>{theme.esc(a.summary)}</p></a>"
        for a in published
    )

    parts_html = []
    for index, part in enumerate(curriculum.parts, start=1):
        chapters = []
        for article in part.articles:
            state = (
                f'<span class="chapter-state">{article.minutes} min</span>'
                if article.published
                else '<span class="chapter-state">Planned</span>'
            )
            inner = (
                f'<span class="chapter-idx">{article.number:02d}</span>'
                f'<span class="chapter-body"><span class="chapter-title">{theme.esc(article.title)}</span>'
                f'<span class="chapter-sum">{theme.esc(article.summary)}</span></span>'
                f"{state}"
            )
            if article.published:
                chapters.append(
                    f'<li class="chapter"><a class="chapter-link" href="{article.href}">{inner}</a></li>'
                )
            else:
                chapters.append(f'<li class="chapter is-planned"><div class="chapter-plain">{inner}</div></li>')

        parts_html.append(f"""<section class="part" id="part-{theme.esc(part.id)}">
  <div class="part-head">
    <span class="part-num">Part {index:02d}</span>
    <h2>{theme.esc(part.title)}</h2>
    {_level_badge(part.level)}
  </div>
  <p class="part-blurb">{theme.esc(part.blurb)}</p>
  <ol class="chapter-list">
{chr(10).join(chapters)}
  </ol>
</section>""")

    # The framing prose (placement == "index") reads before the roadmap, so the
    # reader knows what the subject is before being handed 36 chapter titles.
    framing_page = curriculum.page_at("index")
    framing = ""
    if framing_page is not None:
        framing = ('<section class="framing" aria-label="'
                   + theme.esc(framing_page.title) + '">\n'
                   + framing_page.rendered.html + "\n</section>")

    body = f"""<div class="layout layout-single">
<main id="main">
  <div class="hero">
    <h1>{theme.esc(curriculum.title)}</h1>
    <p>{theme.esc(curriculum.tagline)}</p>
    <div class="hero-stats">
      <span><b>{len(curriculum.parts)}</b>parts</span>
      <span><b>{total}</b>chapters planned</span>
      <span><b>{len(published)}</b>published</span>
      <span><b>{curriculum.figures}</b>diagrams</span>
    </div>
  </div>

  {framing}

  {'<section class="start-here"><h2>Start here</h2><div class="feature-grid">' + features + "</div></section>" if features else ""}

  <section aria-label="Full curriculum">
    {' '.join(parts_html)}
  </section>
</main>
</div>"""

    return theme.document(
        site=site, depth=0, active="home",
        title=curriculum.title,
        description=curriculum.tagline,
        body=body,
    )


# --------------------------------------------------------------------------- #
# Build
# --------------------------------------------------------------------------- #


@dataclass
class BuildReport:
    pages: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def build(repo_root: Path, *, strict: bool = False) -> BuildReport:
    """Render the whole blog into ``docs/blog/``. Idempotent."""
    blog_src = repo_root / "blog"
    docs = repo_root / "docs"
    docs_blog = docs / "blog"

    report = BuildReport()

    curriculum = load_curriculum(blog_src / "curriculum.json", blog_src / "posts",
                                 blog_src / "pages")

    # Publish the stylesheet/JS alongside the generated pages. Note that the
    # figure directories are *not* cleared here: the SVGs are checked in and
    # regenerated by tool/build_blog_assets.py, not by this build.
    assets_src = blog_src / "assets"
    assets_dst = docs_blog / "assets"
    assets_dst.mkdir(parents=True, exist_ok=True)
    for asset in sorted(assets_src.iterdir()):
        if asset.is_file():
            shutil.copy2(asset, assets_dst / asset.name)

    site = theme.Site(
        title=curriculum.title,
        tagline=curriculum.tagline,
        author=curriculum.author,
        nav_pages=tuple((p.nav, p.href) for p in curriculum.nav_pages),
    )

    pages: dict[Path, str] = {}

    published = curriculum.published
    for position, article in enumerate(published):
        prev = published[position - 1] if position > 0 else None
        next_ = published[position + 1] if position + 1 < len(published) else None
        pages[docs_blog / f"{article.slug}.html"] = render_article(
            site, curriculum, article, prev, next_
        )

    for page in curriculum.pages:
        if page.placement == "page" and page.written:
            # Chapters own the top level of docs/blog, so a page that wants its
            # own document must not collide with one -- checked in the loader.
            pages[docs_blog / page.href] = render_page(site, page)

    pages[docs_blog / "index.html"] = render_index(site, curriculum)

    report.errors.extend(_check_links(pages))
    report.errors.extend(
        f"{a.slug}: {problem}"
        for a in curriculum.articles
        if a.rendered
        for problem in _figure_problems(a.body or "", docs_blog)
    )
    report.errors.extend(
        f"page {p.slug}: {problem}"
        for p in curriculum.pages
        if p.rendered
        for problem in _figure_problems(p.body or "", docs_blog)
    )
    report.warnings.extend(_check_orphan_assets(curriculum, docs_blog))

    if report.errors and strict:
        # Do not write a half-consistent site.
        return report

    docs_blog.mkdir(parents=True, exist_ok=True)
    for path, html in sorted(pages.items()):
        path.write_text(html if html.endswith("\n") else html + "\n", encoding="utf-8")
        report.pages.append(str(path.relative_to(repo_root)))

    return report


def _figure_problems(body: str, docs_blog: Path) -> list[str]:
    """A figure whose file is absent is a hard error, whether it sits in a
    chapter or in a standalone page."""
    problems = []
    for src in re.findall(r"!\[[^\]]*\]\((\S+?)(?:\s+\"[^\"]*\")?\)", body):
        if _ABSOLUTE_RE.match(src):
            continue
        if not (docs_blog / src).exists():
            problems.append(f"missing figure file: {src}")
    return problems
