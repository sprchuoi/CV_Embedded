"""A small, dependency-free Markdown renderer for the DSP blog.

The repo's stated rule is that building it needs no third-party Python
packages, so this is a purpose-built subset rather than a dependency. It
supports exactly the constructs the articles use, and it fails loudly on
anything it does not understand -- a silently ignored construct would show up
as malformed prose on the live site.

Block constructs
    ## .. #### heading          (a level-1 heading is an error: the template owns it)
    paragraph, ---, > quote
    - / * / + and 1. lists, nested by indentation
    | pipe | tables |
    ``` fenced code ```
    $$ display math $$           also \\[ .. \\]
    ::: kind Title  ... :::     an admonition / callout
    ![alt](src "classes")        alone in a paragraph -> numbered <figure>

Inline constructs
    **bold**  *italic*  `code`  ~~strike~~  [text](url)  ![alt](src)
    $inline math$, \\( .. \\), raw inline HTML, auto-linked bare URLs

Two things are worth knowing before editing this file:

1. Math and raw HTML are lifted out into placeholders *before* escaping and
   *before* emphasis runs. Without that, ``$H(f) = e^{-j2\\pi f \\tau}$`` would
   come out with the ``\\pi`` italicised and the ``_`` mangled.
2. Figure numbering is per-article and assigned in document order, so prose
   that says "Figure 3" is only correct if figures are not reordered. The
   renderer records every caption (``RenderResult.figure_captions`` -- captions,
   not file paths) so a test can assert the numbering.
"""

from __future__ import annotations

import html
import re
from dataclasses import dataclass, field

# --------------------------------------------------------------------------- #
# Public result type
# --------------------------------------------------------------------------- #


@dataclass
class Heading:
    level: int
    text: str
    anchor: str


@dataclass
class RenderResult:
    html: str
    toc: list[Heading] = field(default_factory=list)
    figure_captions: list[str] = field(default_factory=list)
    word_count: int = 0

    @property
    def reading_minutes(self) -> int:
        # 200 wpm, rounded up, never zero -- a 40-word note still takes a minute.
        return max(1, round(self.word_count / 200))


class MarkdownError(ValueError):
    """Raised for input the renderer refuses to guess at."""


# --------------------------------------------------------------------------- #
# Escaping and anchors
# --------------------------------------------------------------------------- #

_ENTITY_RE = re.compile(r"&(?!(?:#\d+|[A-Za-z][A-Za-z0-9]*);)")


def escape_text(text: str) -> str:
    """Escape for HTML, leaving already-written entities alone."""
    text = _ENTITY_RE.sub("&amp;", text)
    return text.replace("<", "&lt;").replace(">", "&gt;")


def slugify(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE).strip().lower()
    return re.sub(r"[\s_-]+", "-", text) or "section"


class _Anchors:
    """Hands out unique, stable heading anchors within one document."""

    def __init__(self) -> None:
        self._seen: dict[str, int] = {}

    def make(self, text: str) -> str:
        base = slugify(text)
        count = self._seen.get(base, 0)
        self._seen[base] = count + 1
        return base if count == 0 else f"{base}-{count + 1}"


# --------------------------------------------------------------------------- #
# Inline rendering
# --------------------------------------------------------------------------- #

_MATH_RE = re.compile(
    r"(?P<display>\$\$.+?\$\$)"          # $$ ... $$
    r"|(?P<bracket>\\\[.+?\\\])"          # \[ ... \]
    r"|(?P<paren>\\\(.+?\\\))"            # \( ... \)
    r"|(?P<inline>(?<![\w$])\$(?!\s)[^$\n]+?(?<!\s)\$(?![\w$]))",
    re.DOTALL,
)

_HTML_TAG_RE = re.compile(r"</?[A-Za-z][A-Za-z0-9-]*(?:\s[^<>]*)?/?>")

_AUTOLINK_RE = re.compile(r"(?<![\"'>=])\b(https?://[^\s<>()\[\]]+[^\s<>()\[\].,;:!?])")


class _Inline:
    """Renders inline markdown, protecting math, code and raw HTML."""

    def __init__(self) -> None:
        self._store: list[str] = []

    def _stash(self, rendered: str) -> str:
        self._store.append(rendered)
        return f"\x00{len(self._store) - 1}\x00"

    def _restore(self, text: str) -> str:
        def sub(match: re.Match[str]) -> str:
            return self._store[int(match.group(1))]

        # Repeat: a restored fragment may itself contain a placeholder.
        for _ in range(8):
            new = re.sub(r"\x00(\d+)\x00", sub, text)
            if new == text:
                break
            text = new
        return text

    def render(self, text: str) -> str:
        text = _MATH_RE.sub(lambda m: self._stash(f'<span class="math">{m.group(0)}</span>'), text)
        text = _HTML_TAG_RE.sub(lambda m: self._stash(m.group(0)), text)

        # Code spans next: their contents must never see emphasis or links.
        def code(match: re.Match[str]) -> str:
            return self._stash(f"<code>{escape_text(match.group(1))}</code>")

        text = re.sub(r"`([^`]+)`", code, text)

        # Images before links -- the syntax is a superstring of it.
        def image(match: re.Match[str]) -> str:
            alt, src, title = match.group(1), match.group(2), match.group(3)
            cls = f' class="{html.escape(title, quote=True)}"' if title else ""
            return self._stash(
                f'<img src="{html.escape(src, quote=True)}" '
                f'alt="{html.escape(alt, quote=True)}"{cls}>'
            )

        text = re.sub(r'!\[([^\]]*)\]\((\S+?)(?:\s+"([^"]*)")?\)', image, text)

        text = escape_text(text)

        def link(match: re.Match[str]) -> str:
            label, href = match.group(1), match.group(2)
            external = ' target="_blank" rel="noopener"' if href.startswith(("http://", "https://")) else ""
            return self._stash(f'<a href="{href}"{external}>{label}</a>')

        text = re.sub(r"\[([^\]]+)\]\((\S+?)\)", link, text)

        text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text, flags=re.DOTALL)
        text = re.sub(r"~~(.+?)~~", r"<del>\1</del>", text)
        # Underscore emphasis only at word boundaries, so snake_case survives.
        text = re.sub(r"(?<![\w\\])__(?!\s)(.+?)(?<!\s)__(?![\w])", r"<strong>\1</strong>", text)
        text = re.sub(r"(?<![\w\\])\*(?!\s)(.+?)(?<!\s)\*(?![\w])", r"<em>\1</em>", text)
        text = re.sub(r"(?<![\w\\])_(?!\s)(.+?)(?<!\s)_(?![\w])", r"<em>\1</em>", text)

        text = _AUTOLINK_RE.sub(
            lambda m: f'<a href="{m.group(1)}" target="_blank" rel="noopener">{m.group(1)}</a>',
            text,
        )

        return self._restore(text)


def render_inline(text: str) -> str:
    return _Inline().render(text)


def strip_markup(text: str) -> str:
    """Plain text from a heading, for TOC labels and metadata."""
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"[*_~]", "", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"\s+", " ", text).strip()


# --------------------------------------------------------------------------- #
# Block-level helpers
# --------------------------------------------------------------------------- #

_ADMONITIONS = {
    "note": ("Note", "fa-circle-info"),
    "key": ("Key idea", "fa-key"),
    "warn": ("Watch out", "fa-triangle-exclamation"),
    "optical": ("In the optical link", "fa-tower-broadcast"),
    "math": ("The maths", "fa-square-root-variable"),
    "aside": ("Aside", "fa-comment-dots"),
    "try": ("Try it yourself", "fa-flask"),
}

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
_ULIST_RE = re.compile(r"^(\s*)([-*+])\s+(.*)$")
_OLIST_RE = re.compile(r"^(\s*)(\d+)[.)]\s+(.*)$")
_TABLE_SEP_RE = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$")
_FENCE_RE = re.compile(r"^\s*```\s*([\w+-]*)\s*$")
_DIV_OPEN_RE = re.compile(r"^\s*:::\s*([a-zA-Z]+)\s*(.*?)\s*$")
_DIV_CLOSE_RE = re.compile(r"^\s*:::\s*$")


class _Renderer:
    def __init__(self) -> None:
        self.anchors = _Anchors()
        self.toc: list[Heading] = []
        self.figure_captions: list[str] = []

    # -- entry point ------------------------------------------------------- #

    def render(self, text: str) -> str:
        # Normalise: tabs to spaces, strip trailing whitespace on each line so
        # "two spaces at end of line" cannot silently become a <br>.
        lines = [line.replace("\t", "    ").rstrip() for line in text.split("\n")]
        return self._blocks(lines)

    # -- block dispatcher -------------------------------------------------- #

    def _blocks(self, lines: list[str]) -> str:
        out: list[str] = []
        i = 0
        while i < len(lines):
            line = lines[i]

            if not line.strip():
                i += 1
                continue

            fence = _FENCE_RE.match(line)
            if fence:
                i = self._code_block(lines, i, fence.group(1), out)
                continue

            if _DIV_CLOSE_RE.match(line):
                raise MarkdownError(f"unmatched ':::' at line {i + 1}")

            div = _DIV_OPEN_RE.match(line)
            if div:
                i = self._admonition(lines, i, div.group(1), div.group(2), out)
                continue

            if line.strip().startswith("$$") or line.strip().startswith("\\["):
                i = self._display_math(lines, i, out)
                continue

            heading = _HEADING_RE.match(line)
            if heading:
                self._heading(heading, i, out)
                i += 1
                continue

            if re.match(r"^\s*(-{3,}|\*{3,}|_{3,})\s*$", line):
                out.append("<hr>")
                i += 1
                continue

            if line.lstrip().startswith(">"):
                i = self._quote(lines, i, out)
                continue

            if _ULIST_RE.match(line) or _OLIST_RE.match(line):
                i = self._list(lines, i, out)
                continue

            if "|" in line and i + 1 < len(lines) and _TABLE_SEP_RE.match(lines[i + 1]):
                i = self._table(lines, i, out)
                continue

            i = self._paragraph(lines, i, out)

        return "\n".join(out)

    # -- individual blocks ------------------------------------------------- #

    def _code_block(self, lines: list[str], i: int, lang: str, out: list[str]) -> int:
        i += 1
        body: list[str] = []
        while i < len(lines) and not _FENCE_RE.match(lines[i]):
            body.append(lines[i])
            i += 1
        if i >= len(lines):
            raise MarkdownError("unclosed ``` code fence")
        cls = f' class="language-{lang}"' if lang else ""
        out.append(f"<pre><code{cls}>{escape_text(chr(10).join(body))}</code></pre>")
        return i + 1

    def _admonition(self, lines: list[str], i: int, kind: str, title: str, out: list[str]) -> int:
        kind = kind.lower()
        if kind not in _ADMONITIONS:
            raise MarkdownError(
                f"unknown callout ':::{kind}' at line {i + 1}; "
                f"expected one of {', '.join(sorted(_ADMONITIONS))}"
            )
        depth, j = 1, i + 1
        body: list[str] = []
        while j < len(lines):
            if _DIV_OPEN_RE.match(lines[j]):
                depth += 1
            elif _DIV_CLOSE_RE.match(lines[j]):
                depth -= 1
                if depth == 0:
                    break
            body.append(lines[j])
            j += 1
        if j >= len(lines):
            raise MarkdownError(f"unclosed ':::{kind}' block opened at line {i + 1}")

        default_title, icon = _ADMONITIONS[kind]
        label = render_inline(title) if title else default_title
        inner = self._blocks(body)
        out.append(
            f'<aside class="callout callout-{kind}">\n'
            f'  <p class="callout-title"><i class="fa-solid {icon}" aria-hidden="true"></i> {label}</p>\n'
            f'  <div class="callout-body">\n{inner}\n  </div>\n'
            f"</aside>"
        )
        return j + 1

    def _display_math(self, lines: list[str], i: int, out: list[str]) -> int:
        first = lines[i].strip()
        if first.startswith("$$"):
            close = "$$"
            rest = first[2:]
            if rest.endswith("$$") and len(rest) > 2:
                out.append(f'<div class="math-display">{escape_text(first)}</div>')
                return i + 1
            body = [rest] if rest else []
        else:
            close = "\\]"
            rest = first[2:]
            if rest.endswith("\\]"):
                out.append(f'<div class="math-display">{escape_text(first)}</div>')
                return i + 1
            body = [rest] if rest else []

        i += 1
        while i < len(lines):
            stripped = lines[i].strip()
            if stripped.endswith(close):
                body.append(stripped[: -len(close)])
                out.append(f'<div class="math-display">{escape_text(chr(10).join(body))}</div>')
                return i + 1
            body.append(lines[i])
            i += 1
        raise MarkdownError("unclosed display-math block")

    def _heading(self, match: re.Match[str], index: int, out: list[str]) -> None:
        level = len(match.group(1))
        raw = match.group(2)
        if level == 1:
            raise MarkdownError(
                f"level-1 heading at line {index + 1}: the page template renders the "
                "article title, so start body sections at '##'"
            )
        level = min(level, 5)
        anchor = self.anchors.make(strip_markup(raw))
        self.toc.append(Heading(level=level, text=strip_markup(raw), anchor=anchor))
        label = render_inline(raw)
        out.append(
            f'<h{level} id="{anchor}">'
            f'<a class="heading-anchor" href="#{anchor}" aria-hidden="true">#</a>{label}'
            f"</h{level}>"
        )

    def _quote(self, lines: list[str], i: int, out: list[str]) -> int:
        body: list[str] = []
        while i < len(lines) and (lines[i].lstrip().startswith(">") or not lines[i].strip()):
            if not lines[i].strip():
                body.append("")
            else:
                body.append(re.sub(r"^\s*>\s?", "", lines[i]))
            i += 1
            if i < len(lines) and not lines[i].strip() and not (
                i + 1 < len(lines) and lines[i + 1].lstrip().startswith(">")
            ):
                break
        out.append(f"<blockquote>\n{self._blocks(body)}\n</blockquote>")
        return i

    def _list(self, lines: list[str], start: int, out: list[str]) -> int:
        ordered = bool(_OLIST_RE.match(lines[start]))
        tag = "ol" if ordered else "ul"
        items: list[list[str]] = []
        i = start
        base_indent: int | None = None

        while i < len(lines):
            line = lines[i]
            if not line.strip():
                # A blank line ends the list unless the next line is indented
                # continuation of the current item.
                if i + 1 < len(lines) and lines[i + 1].startswith("  ") and lines[i + 1].strip():
                    items[-1].append("")
                    i += 1
                    continue
                break
            match = (_OLIST_RE if ordered else _ULIST_RE).match(line)
            if match:
                indent = len(match.group(1))
                if base_indent is None:
                    base_indent = indent
                if indent > base_indent and items:
                    # Nested list: keep the raw line for the recursive render.
                    items[-1].append(line)
                    i += 1
                    continue
                if indent < base_indent:
                    break
                items.append([match.group(3)])
                i += 1
                continue
            if line.startswith("  ") and items:
                items[-1].append(line.strip())
                i += 1
                continue
            break

        rendered = []
        for item in items:
            body_lines, nested = [], []
            for entry in item:
                if _ULIST_RE.match(entry) or _OLIST_RE.match(entry):
                    nested.append(entry)
                else:
                    body_lines.append(entry)
            inner = self._blocks(body_lines)
            if nested:
                inner += "\n" + self._blocks(nested)
            # A single-paragraph item does not need <p> inside <li>.
            if inner.startswith("<p>") and inner.count("<p>") == 1 and "\n" not in inner.strip():
                inner = inner[3:-4]
            rendered.append(f"<li>{inner}</li>")
        out.append(f"<{tag}>\n" + "\n".join(rendered) + f"\n</{tag}>")
        return i

    def _table(self, lines: list[str], i: int, out: list[str]) -> int:
        def cells(row: str) -> list[str]:
            row = row.strip()
            if row.startswith("|"):
                row = row[1:]
            if row.endswith("|"):
                row = row[:-1]
            return [c.strip() for c in row.split("|")]

        header = cells(lines[i])
        aligns = []
        for spec in cells(lines[i + 1]):
            left, right = spec.startswith(":"), spec.endswith(":")
            aligns.append("center" if left and right else "right" if right else "left")

        i += 2
        rows: list[list[str]] = []
        while i < len(lines) and "|" in lines[i] and lines[i].strip():
            rows.append(cells(lines[i]))
            i += 1

        head = "".join(
            f'<th style="text-align:{aligns[k] if k < len(aligns) else "left"}">{render_inline(c)}</th>'
            for k, c in enumerate(header)
        )
        body = "\n".join(
            "<tr>"
            + "".join(
                f'<td style="text-align:{aligns[k] if k < len(aligns) else "left"}">{render_inline(c)}</td>'
                for k, c in enumerate(row)
            )
            + "</tr>"
            for row in rows
        )
        out.append(
            '<div class="table-wrap"><table>\n'
            f"<thead><tr>{head}</tr></thead>\n<tbody>\n{body}\n</tbody>\n</table></div>"
        )
        return i

    def _paragraph(self, lines: list[str], start: int, out: list[str]) -> int:
        body: list[str] = []
        i = start
        while i < len(lines):
            line = lines[i]
            if not line.strip():
                break
            if body and (
                _HEADING_RE.match(line)
                or _FENCE_RE.match(line)
                or _DIV_OPEN_RE.match(line)
                or _ULIST_RE.match(line)
                or _OLIST_RE.match(line)
                or line.lstrip().startswith(">")
                or re.match(r"^\s*(-{3,}|\*{3,}|_{3,})\s*$", line)
            ):
                break
            body.append(line.strip())
            i += 1

        text = " ".join(body)

        # A lone image becomes a numbered figure with its alt text as caption.
        sole_image = re.fullmatch(r'!\[([^\]]*)\]\((\S+?)(?:\s+"([^"]*)")?\)', text)
        if sole_image:
            alt, src, classes = sole_image.group(1), sole_image.group(2), sole_image.group(3) or ""
            number = len(self.figure_captions) + 1
            self.figure_captions.append(alt)
            cls = " ".join(["figure", *classes.split()])
            caption = (
                f'<figcaption><span class="fig-label">Figure {number}</span>'
                f"<span class=\"fig-text\">{render_inline(alt)}</span></figcaption>"
                if alt
                else ""
            )
            out.append(
                f'<figure class="{cls}">'
                f'<img src="{html.escape(src, quote=True)}" alt="{html.escape(strip_markup(alt), quote=True)}" loading="lazy">'
                f"{caption}</figure>"
            )
            return i

        out.append(f"<p>{render_inline(text)}</p>")
        return i


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #


def count_words(text: str) -> int:
    """Prose words, for the reading-time estimate.

    Display maths, table rows and figure captions are stripped first. Counting
    them would be badly wrong: a single ``$$`` block of a dozen LaTeX commands
    would read as a dozen words, and a wide results table would read as
    paragraphs.
    """
    text = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)        # fenced code
    text = re.sub(r"\$\$.*?\$\$", " ", text, flags=re.DOTALL)      # display maths
    text = re.sub(r"\\\[.*?\\\]", " ", text, flags=re.DOTALL)      # display maths
    text = re.sub(r"\$[^$\n]+\$", " ", text)                       # inline maths
    text = re.sub(r"\\\(.*?\\\)", " ", text, flags=re.DOTALL)      # inline maths
    text = re.sub(r"^\s*\|.*\|\s*$", " ", text, flags=re.MULTILINE)  # table rows
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", text)              # figure captions
    return len(re.findall(r"[\w'-]+", strip_markup(text)))


def render(text: str) -> RenderResult:
    """Render article Markdown to HTML plus its table of contents."""
    renderer = _Renderer()
    body = renderer.render(text)
    return RenderResult(html=body, toc=renderer.toc,
                        figure_captions=renderer.figure_captions,
                        word_count=count_words(text))
