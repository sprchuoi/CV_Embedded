# CV Generator - Nguyen Quang Binh

Generates this CV in three formats from a **single source file**:

| Output | Pipeline |
|---|---|
| `NguyenQuangBinh_CV.pdf` | `docs/NguyenQuangBinh_CV.dox` → Doxygen → LaTeX → `pdflatex` |
| `NguyenQuangBinh_CV_Sidebar.pdf` | same `.dox` → `tool/build_sidebar_cv.py` → two-column LaTeX template |
| `docs/index.html` | same `.dox` → `tool/update_html_from_dox.py` → Bootstrap web CV |

Both PDFs are published to the [`latest` release](../../releases/tag/latest) and the webpage is
deployed to GitHub Pages by [`.github/workflows/python-app.yml`](.github/workflows/python-app.yml).

## Editing the CV

**Edit `docs/NguyenQuangBinh_CV.dox` and nothing else.** It is the single source of truth; the
PDFs and the webpage are all regenerated from it.

### Markup contract

```
@mainpage <Name>
<blank>
<one-line '|'-separated contact details>

@section <key> <TITLE>                  top-level section
@subsection <key> <Title>               a company / institution / project
@subsubsection <key> <Title> | <Dates>  one role
@paragraph <key> <Name>                 a nested project under a role
```

Inside a body:

- `- bullet` — a list item; indent by two spaces for a nested bullet
- `<b>Label:</b> value` — a field on its own line
- Inline markup is limited to `<b>`, `<em>` and `[text](url)`
- A `---` line renders as a horizontal rule in the PDF (the parsers strip it)

Section **keys** are the contract with the renderers — `summary`, `work_experience`, `projects`,
`education`, `achievements`, `awards`, `skills`. Renaming a key without updating
`tool/update_html_from_dox.py` and the HTML markers will fail the build (by design).

In `skills`, wrap a category's value in `<em>` to render it as a prose sentence; leave it as a
comma list to render as tags/badges.

Two gotchas when writing Doxygen markup:

- **Put a blank line before a field that follows a list**, or Doxygen folds it into the last
  bullet instead of starting a new paragraph.
- **Write a raw `&`, not `&amp;`** — Doxygen escapes it for LaTeX, and the HTML renderer escapes
  it for the browser.

## Building locally

Requires `doxygen`, a TeX Live install (with `texlive-latex-extra`, `texlive-fonts-extra` and
`texlive-pictures`), and Python 3.11+. No third-party Python packages are needed.

```sh
./build_cv.sh              # main PDF (cmake + doxygen + pdflatex)
./build_sidebar_cv.sh      # sidebar PDF
python3 tool/update_html_from_dox.py   # regenerate docs/index.html
```

To inspect the web page:

```sh
python3 -m http.server -d docs
```

Without a TeX installation you can still review the sidebar pipeline's output as LaTeX:

```sh
python3 tool/build_sidebar_cv.py --emit-tex /tmp/cv.tex
```

## Layout

```
docs/NguyenQuangBinh_CV.dox      the CV source -- the only file you edit
docs/index.html                  generated webpage
docs/assets/css/devresume.css    Bootstrap 4 + DevResume theme (minified)
tool/cv_dox.py                   shared .dox parser and inline-markup tokeniser
tool/update_html_from_dox.py     .dox -> docs/index.html
tool/build_sidebar_cv.py         .dox -> sidebar LaTeX -> PDF
build_environment/tool/doxygen/  Doxygen config and the main-PDF LaTeX header
build_environment/tool/sidebar_cv/  sidebar LaTeX template
```

`tool/cv_dox.py` is shared by both renderers so their parsing cannot drift apart.
