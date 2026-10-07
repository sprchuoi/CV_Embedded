# The DSP blog — source of truth

A diagram-first course in digital signal processing, from first principles to
the coherent optical link. Published as part of the same GitHub Pages site as
the CV, at `docs/blog/`.

```
blog/
  curriculum.json   the full roadmap: parts, chapters, ordering, summaries
  posts/            one Markdown file per chapter -- prose only, no metadata
  pages/            standalone prose: the index framing and the Vision page
  assets/           blog.css and blog.js, copied verbatim into docs/blog/assets/
  vi/               the same three things again, in Vietnamese
tool/
  build_blog.py         render the site (standard library only)
  build_blog_assets.py  regenerate the figures (needs numpy/matplotlib/scipy)
  blog/
    i18n.py       the chrome strings per language, and the list of languages
    markdown.py   the Markdown subset the articles are written in
    site.py       curriculum loading, page assembly, link checking, the build
    theme.py      the HTML shell: head, header, footer, language selector
    art/svg.py    an SVG builder for hand-authored diagrams
    art/plotstyle.py  shared matplotlib styling, so plots match the diagrams
    art/diagrams_*.py hand-authored block diagrams, per chapter
    art/plots_*.py    computed signal plots, per chapter
```

## The two rules that keep this from rotting

**1. `curriculum.json` owns structure; Markdown owns prose.**

Every chapter — including ones not written yet — is listed in
`curriculum.json`. That is why the roadmap on the blog index is always the
complete plan rather than a list of what happens to exist.

Whether a chapter is *published* is decided by exactly one thing: does
`blog/posts/<slug>.md` exist? There is no second `status` field to drift out of
sync with reality. Delete the file and the chapter reverts to "Planned"; add it
and the chapter goes live.

**2. The build fails on a broken figure.**

Every relative `src`/`href` in the generated HTML is resolved against the
output directory after all pages are written. A renamed or misspelled SVG is a
build error, not a broken image on the live site. The build also refuses to
write anything at all if it found errors, so a half-consistent site cannot be
published.

`tool/tests/test_blog_site.py` goes further and asserts that every figure
committed under `docs/blog/assets/` is referenced by some chapter, and that
every figure a script builds is actually used.

## Writing a chapter

1. Add an entry to the right part in `curriculum.json` with a kebab-case
   `slug`, a `title`, and a one-line `summary` (the summary is the standfirst
   on the page and the description in the roadmap — write it as the promise the
   chapter delivers).
2. Create `blog/posts/<slug>.md`. The body starts at `##`; the page template
   renders the `<h1>`.
3. Reference figures as `![Caption](assets/diagrams/name.svg)`. A lone image on
   its own paragraph becomes a numbered `<figure>`; the number is assigned in
   document order, so **if you reorder figures, fix the "Figure N" references
   in the prose.**
4. Build and check:

```sh
python3 tool/build_blog.py            # renders into docs/blog/
python3 -m http.server -d docs        # then open http://localhost:8000/blog/
```

### The Markdown subset

`tool/blog/markdown.py` is purpose-built and strict: an unrecognised construct
is a build error rather than something silently dropped. What exists:

| Construct | Syntax |
|---|---|
| Sections | `## Heading`, `### Heading` (`#` is an error — the template owns it) |
| Lists | `- item`, `1. item`, nested by indentation |
| Tables | pipe syntax with a `---` separator row |
| Code | fenced ``` blocks, and `` `inline` `` |
| Maths | `$inline$` and `$$display$$` (MathJax, configured in `theme.py`) |
| Figures | `![Caption](path.svg)` alone in a paragraph |
| Callouts | `::: kind Title` … `:::` |

Callout kinds: `note`, `key`, `warn`, `optical`, `math`, `aside`, `try`.

`optical` is the one that matters most. **Every chapter, at every level, ends
with an "In the optical link" callout** — that is the whole point of the blog:
it is not a generic DSP tutorial, it is a DSP tutorial by someone who ships
optical DSP. Do not skip it.

## Adding a figure

Hand-authored diagrams go in `tool/blog/art/diagrams_<chapter>.py`; computed
plots go in `art/plots_<chapter>.py`. Either way you add an entry to the
module's `FIGURES` mapping:

```python
from . import svg as S          # or: from . import plotstyle as P

def my_figure() -> str:
    c = S.Canvas(880, 320, title="What this figure shows")
    c.heading("The takeaway, in one line")
    c.add(S.block(40, 120, 160, 60, "FFE", "feed-forward"))
    ...
    return c.render()

FIGURES = {"my-figure": my_figure}
```

The key becomes the file name, so names must be globally unique across all
modules — `collect()` raises on a duplicate rather than overwriting one.

Then:

```sh
python3 tool/build_blog_assets.py --only diagrams   # no numeric stack needed
build_environment/.venv/bin/python tool/build_blog_assets.py   # everything
```

The computed plots need numpy, matplotlib and scipy. They live in a venv rather
than the system interpreter because that is the same separation the site build
relies on — `.venv` is already in `.gitignore`:

```sh
python3 -m venv build_environment/.venv
build_environment/.venv/bin/python -m pip install numpy matplotlib scipy
```

The generated SVGs are **committed**. The site build never runs a figure
script, so a matplotlib or scipy problem cannot take the published site down —
and CI checks that the committed SVGs still match a fresh build.

To eyeball a figure, rasterise it:

```sh
build_environment/.venv/bin/python tool/build_blog_assets.py --png-dir /tmp/figs
```

### Figure house style

Both families share one palette (defined in `art/svg.py` and mirrored in
`art/plotstyle.py` and `assets/blog.css`): accent `#54B689`, ink `#2c3e50`,
optical `#7a5cc0`, warn `#d9822b`, note `#3b7fb5`.

SVG figures are self-contained by design — inline presentation attributes, no
external fonts and their own opaque background. An SVG referenced through
`<img src="...">` is a separate document that inherits nothing from the page, so
it must also stay legible when the reader switches the page to dark mode.

Subscripts and superscripts in SVG labels use `~x~` and `^x^`: `f~s~/2` renders
as *f*<sub>s</sub>/2, `z^-1^` as *z*<sup>−1</sup>. Unicode is not an option —
there is no subscript `s` or `c` in every font.

## Languages

The blog is published in English and Vietnamese. English is the default and
keeps the root of `docs/blog/`; every other language is a subdirectory named for
it, so `docs/blog/vi/the-fft.html` mirrors `docs/blog/the-fft.html`. Adding a
language never moves an existing URL.

A language is three things and no code:

1. An entry in `i18n.CATALOGUE` (chrome strings: nav labels, "On this page",
   "Planned", the figure label) plus its code in `i18n.LANGS`.
2. `blog/<lang>/curriculum.json` -- the same `parts`, `id`s, article `slug`s and
   page `slug`s as the English file, in the same order, with translated titles,
   summaries and blurbs.
3. `blog/<lang>/posts/<slug>.md` and `blog/<lang>/pages/<slug>.md`, translated
   from the English prose, for as many chapters as are ready.

Then `python3 tool/build_blog.py` publishes every language in `i18n.LANGS`. A
declared language with no curriculum is a build error rather than a silent
skip -- a monolingual site published without saying so is the one outcome worse
than failing. `theme.py` already takes a `depth`, so a subtree needs no path
logic: at depth 1 the same templates emit `../assets/blog.css` and
`../../index.html`, and the build prepends `../` to figure sources so the
translated prose can say `assets/diagrams/x.svg` exactly as the English does.

Four rules keep the two trees honest:

- **The plan may not drift.** `check_parity` fails the build, naming the slugs,
  if a language's `curriculum.json` declares a different set of parts, chapters
  or pages from English. New chapter in English means an entry in every
  language -- the *prose* may lag as far behind as it likes.
- **Written and untranslated is not the same as unwritten.** A chapter with an
  English post and no Vietnamese one is marked "English only" in the Vietnamese
  roadmap and links to the English page. It is never rendered as "Planned",
  which would be a lie, and never hidden, which would be a dead end.
- **Figures are shared.** The SVGs are language-neutral and live in one
  `docs/blog/assets/` tree; labels inside them stay English, as do technical
  terms in the prose.
- **Chrome is not prose.** No user-visible literal belongs in `theme.py` or
  `site.py`; it goes in `i18n.py`. `blog.js` reads its few strings
  (`Copy`, the theme toggle) from `data-` attributes on `<body>`, so the script
  carries no language at all.

Each page carries `<html lang>`, `hreflang` alternates and a `<link
rel="canonical">` when `curriculum.json` declares a `site_url`; without one the
alternates are emitted relative, which readers follow but crawlers will not.

## Running the tests

```sh
python3 -m unittest discover -s tool/tests -t . -v
```

The suite covers the Markdown renderer, the curriculum validator, the link
checker, and a full build into a throwaway directory. One test is skipped
unless numpy is importable; it cross-checks the figure registry against what the
chapters actually reference.

### Python version

**3.11 is the floor, and CI enforces it.** The `test` job runs on 3.11 and 3.12,
and byte-compiles `tool/` before the tests. That byte-compile step exists because
it caught a real regression: the figure modules are only *imported* when numpy is
present, so a 3.12-only construct inside one of them (a multi-line f-string,
which is PEP 701) passed the unit tests on a 3.12 laptop and died as a
`SyntaxError` in the figures job on the 3.11 runner.

If you add code to `tool/`, keep it 3.11-compatible — in particular, no newline
inside a single-quoted f-string. Check with:

```sh
python3 -m compileall -q tool
```
