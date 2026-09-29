"""The HTML shell, head and chrome shared by every generated blog page.

Kept separate from :mod:`tool.blog.site` so that page *structure* (this file)
and page *content* (site.py) can be reviewed independently.

Every generated page lives directly in ``docs/blog/``, so asset links are
uniformly relative (``assets/blog.css``, ``../index.html`` for the CV) and the
whole site also works straight off the filesystem over ``file://``.
"""

from __future__ import annotations

import html
import json
from dataclasses import dataclass

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


def head(*, title: str, description: str, depth: int, extra_head: str = "") -> str:
    """<head> contents for a page ``depth`` directories below docs/blog."""
    up = "../" * depth
    # The favicon lives at docs/favicon.ico, one level above docs/blog/.
    root = "../" * (depth + 1)
    return f"""<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
<meta name="color-scheme" content="light dark">
<meta property="og:type" content="article">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<link rel="icon" href="{root}favicon.ico">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{FONTS}">
<link rel="stylesheet" href="{FONTAWESOME}">
<link rel="stylesheet" href="{up}assets/blog.css">
{_mathjax_setup()}{extra_head}"""


def header(*, site: Site, depth: int, active: str) -> str:
    """Sticky header. ``active`` marks the current nav item for assistive tech."""
    up = "../" * depth
    cv = f"{'../' * (depth + 1)}index.html" if depth else "../index.html"

    def nav(label: str, href: str, key: str) -> str:
        current = ' aria-current="page"' if key == active else ""
        return f'<a href="{href}"{current}>{esc(label)}</a>'

    return f"""<header class="site-header">
  <div class="inner">
    <a class="brand" href="{up}index.html">
      <span class="mark" aria-hidden="true">DSP</span>
      <span>{esc(site.author.get('name', 'Nguyen Quang Binh'))}</span>
      <span class="sub">signal processing notes</span>
    </a>
    <nav class="site-nav" aria-label="Primary">
      {nav('Curriculum', f'{up}index.html', 'home')}
      {nav('CV', cv, 'cv')}
      {nav('GitHub', site.author.get('github', '#'), 'github')}
      <button class="icon-btn" type="button" data-theme-toggle aria-pressed="false"
              title="Switch theme" aria-label="Switch colour theme"><i class="fa-solid fa-moon" aria-hidden="true"></i></button>
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
             body: str) -> str:
    """Assemble a complete HTML document."""
    up = "../" * depth
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
{head(title=title, description=description, depth=depth)}
</head>
<body>
<a class="skip-link" href="#main">Skip to content</a>
{header(site=site, depth=depth, active=active)}
{body}
{footer(site=site, depth=depth)}
<script src="{up}assets/blog.js" defer></script>
</body>
</html>
"""
