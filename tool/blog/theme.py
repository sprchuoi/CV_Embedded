"""The HTML shell, head and chrome shared by every generated blog page.

Kept separate from :mod:`tool.blog.site` so that page *structure* (this file)
and page *content* (site.py) can be reviewed independently.

Every generated page lives directly in ``docs/blog/`` -- or one level down in
``docs/blog/<lang>/`` -- so asset links are uniformly relative (``assets/blog.css``,
``../index.html`` for the CV) and the whole site also works straight off the
filesystem over ``file://``. The ``depth`` argument every function here takes is
what makes a language subtree cost no new path logic: at ``depth=1`` the same
templates produce ``../assets/blog.css`` and ``../../index.html``.

Chrome text (nav labels, "On this page", the selector) comes from
:mod:`tool.blog.i18n`, never from a literal in this file.
"""

from __future__ import annotations

import html
import json
from dataclasses import dataclass

from . import i18n

# Font Awesome 6 for callout glyphs. If the CDN is unreachable the callout still
# carries its text title and its accent colour, so nothing becomes unreadable.
FONTAWESOME = "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.2/css/all.min.css"
MATHJAX = "https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"
FONTS = "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap"


def esc(value: object, quote: bool = True) -> str:
    """HTML-escape any value for use in text or an attribute."""
    return html.escape(str(value), quote=quote)


@dataclass(frozen=True)
class Site:
    """Values the shell needs that come from curriculum.json."""

    title: str
    tagline: str
    author: dict
    # (label, href) pairs for standalone pages that asked to be in the nav.
    nav_pages: tuple[tuple[str, str], ...] = ()
    lang: str = i18n.DEFAULT_LANG
    # How many directories below docs/blog this language is published at: 0 for
    # the default language, 1 for every other. Asset and back-link paths follow
    # from it, so a language subtree needs no path logic of its own.
    depth: int = 0
    # Absolute base URL of the published blog (trailing slash), from the
    # curriculum's optional "site_url". Only hreflang/canonical need it.
    site_url: str | None = None

    @property
    def strings(self) -> i18n.Strings:
        return i18n.strings(self.lang)

    @property
    def root_prefix(self) -> str:
        return ""


def _mathjax_setup() -> str:
    """Configure MathJax before it loads.

    ``skipHtmlTags`` keeps ``$`` inside code blocks and ``<code>`` untouched,
    which is the usual way a shell prompt ends up typeset as mathematics.
    """
    config = {
        "tex": {
            "inlineMath": [["$", "$"], ["\\(", "\\)"]],
            "displayMath": [["$$", "$$"], ["\\[", "\\]"]],
            "processEscapes": True,
            "tags": "none",
            "macros": {
                # Used constantly in the optical chapters.
                "twopi": "2\\pi",
                "dd": "\\mathrm{d}",
                "E": "\\mathbb{E}",
                "j": "\\mathrm{j}",
                "argmin": "\\operatorname*{arg\\,min}",
            },
        },
        "options": {
            "skipHtmlTags": ["script", "noscript", "style", "textarea", "pre", "code"],
            "ignoreHtmlClass": "no-mathjax",
        },
        "chtml": {"scale": 1.02},
    }
    return (
        "<script>\n"
        "  window.MathJax = " + json.dumps(config, indent=2) + ";\n"
        "</script>\n"
        f'<script id="MathJax-script" async src="{MATHJAX}"></script>'
    )


def _alternates(*, site: Site, canonical_href: str, alt_canonical: str) -> str:
    """hreflang alternates for this page and its counterpart in the other language.

    ``canonical_href`` and ``alt_canonical`` are both paths relative to the blog
    root -- not to the page, so they can be made absolute by prefixing the site
    URL. When the curriculum declares a ``site_url`` they are made absolute,
    which is what hreflang requires to be honoured; without one the links are
    still emitted relative, which browsers and readers follow even though
    crawlers will not.
    """
    other = i18n.other_lang(site.lang)
    default_href = canonical_href if site.lang == i18n.DEFAULT_LANG else alt_canonical
    base = site.site_url or ""

    def link(hreflang: str, href: str) -> str:
        return (f'<link rel="alternate" hreflang="{esc(hreflang)}" '
                f'href="{esc(base + href, quote=True)}">')

    links = [link(site.strings.code, canonical_href), link(other, alt_canonical)]
    if base:
        # x-default names the version to serve a reader whose language we do
        # not publish, so it always points at the default language.
        links.append(link("x-default", default_href))
        links.append(f'<link rel="canonical" href="{esc(base + canonical_href, quote=True)}">')
    return "\n".join(links)


def head(*, site: Site, title: str, description: str, depth: int,
         canonical_href: str = "", alt_canonical: str = "",
         extra_head: str = "") -> str:
    """<head> contents for a page ``depth`` directories below docs/blog.

    The hreflang alternates are emitted only when the caller knows both this
    page's location and its counterpart's; a render with no location (a unit
    test, a scratch page) simply gets none rather than a broken link.
    """
    up = "../" * depth
    # The favicon lives at docs/favicon.ico, one level above docs/blog/.
    root = "../" * (depth + 1)
    alternates = ""
    if canonical_href and alt_canonical:
        alternates = _alternates(site=site, canonical_href=canonical_href,
                                 alt_canonical=alt_canonical) + "\n"
    return f"""<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
<meta name="color-scheme" content="light dark">
<meta property="og:type" content="article">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:locale" content="{esc(site.strings.code)}">
{alternates}<link rel="icon" href="{root}favicon.ico">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{FONTS}">
<link rel="stylesheet" href="{FONTAWESOME}">
<link rel="stylesheet" href="{up}assets/blog.css">
{_mathjax_setup()}{extra_head}"""


def _language_switch(*, site: Site, alt_href: str) -> str:
    """The language selector: current language inert, the other one a link.

    A plain generated link, so switching language works with JavaScript off and
    lands on the *same page* rather than the blog front page. When this page has
    no counterpart in the other language the caller points ``alt_href`` at that
    language's index, which is where a reader who cannot read this one wants to
    be -- the roadmap there marks the gap as "English only" rather than as
    unwritten.
    """
    s = site.strings
    other = i18n.strings(i18n.other_lang(site.lang))
    return (
        f'<div class="lang-switch" role="group" aria-label="{esc(s.aria_language)}">'
        f'<span class="is-current" lang="{esc(s.code)}" aria-current="true">{esc(s.label)}</span>'
        f'<a href="{esc(alt_href, quote=True)}" hreflang="{esc(other.code)}" '
        f'lang="{esc(other.code)}" title="{esc(other.name)}">{esc(other.label)}</a>'
        f'</div>'
    )


def header(*, site: Site, depth: int, active: str, alt_href: str = "") -> str:
    """Sticky header. ``active`` marks the current nav item for assistive tech.

    With no ``alt_href`` there is nowhere to switch to, so the selector is left
    out entirely rather than rendered as a dead link.
    """
    up = "../" * depth
    cv = f"{'../' * (depth + 1)}index.html" if depth else "../index.html"
    s = site.strings

    def nav(label: str, href: str, key: str) -> str:
        current = ' aria-current="page"' if key == active else ""
        return f'<a href="{href}"{current}>{esc(label)}</a>'

    # Standalone pages first -- they are the "about this site" material, which
    # reads better ahead of the curriculum link than buried after it.
    pages = "".join(nav(label, f"{up}{href}", href) for label, href in site.nav_pages)
    switch = _language_switch(site=site, alt_href=alt_href) if alt_href else ""

    return f"""<header class="site-header">
  <div class="inner">
    <a class="brand" href="{up}index.html">
      <span class="mark" aria-hidden="true">DSP</span>
      <span>{esc(site.author.get('name', 'Nguyen Quang Binh'))}</span>
      <span class="sub">{esc(s.brand_sub)}</span>
    </a>
    <nav class="site-nav" aria-label="{esc(s.aria_primary)}">
      {pages}
      {nav(s.nav_curriculum, f'{up}index.html', 'home')}
      {nav(s.nav_cv, cv, 'cv')}
      {nav(s.nav_github, site.author.get('github', '#'), 'github')}
      {switch}
      <button class="icon-btn" type="button" data-theme-toggle aria-pressed="false"
              title="{esc(s.theme_toggle_title)}" aria-label="{esc(s.theme_toggle_title)}"><i class="fa-solid fa-moon" aria-hidden="true"></i></button>
    </nav>
  </div>
  <div class="read-progress" role="presentation"></div>
</header>"""


def footer(*, site: Site, depth: int) -> str:
    up = "../" * depth
    author = site.author
    links = [
        f'<a href="{esc(author.get("github", "#"))}" target="_blank" rel="noopener">GitHub</a>',
        f'<a href="{esc(author.get("linkedin", "#"))}" target="_blank" rel="noopener">LinkedIn</a>',
        f'<a href="mailto:{esc(author.get("email", ""))}">{esc(author.get("email", ""))}</a>',
        f'<a href="{"../" * (depth + 1)}index.html">CV</a>',
    ]
    return f"""<footer class="site-footer">
  <div class="inner">
    <span>&copy; {esc(author.get('name', ''))} &middot; {esc(author.get('role', ''))}</span>
    <span class="spacer"></span>
    {' &middot; '.join(links)}
  </div>
</footer>"""


def document(*, site: Site, depth: int, active: str, title: str, description: str,
             body: str, canonical_href: str = "", alt_canonical: str = "",
             alt_href: str = "") -> str:
    """Assemble a complete HTML document.

    ``canonical_href`` is this page's own path relative to the blog root and
    ``alt_canonical`` its counterpart in the other language, both used for the
    hreflang alternates. ``alt_href`` is the same counterpart expressed relative
    to *this page*, which is what the selector link needs.
    """
    up = "../" * depth
    s = site.strings
    return f"""<!DOCTYPE html>
<html lang="{esc(s.code)}">
<head>
{head(site=site, title=title, description=description, depth=depth,
      canonical_href=canonical_href, alt_canonical=alt_canonical)}
</head>
<body data-copy="{esc(s.copy)}" data-copied="{esc(s.copied)}"
      data-copy-failed="{esc(s.copy_failed)}"
      data-theme-dark="{esc(s.theme_switch_dark)}" data-theme-light="{esc(s.theme_switch_light)}">
<a class="skip-link" href="#main">{esc(s.skip_to_content)}</a>
{header(site=site, depth=depth, active=active, alt_href=alt_href)}
{body}
{footer(site=site, depth=depth)}
<script src="{up}assets/blog.js" defer></script>
</body>
</html>
"""
