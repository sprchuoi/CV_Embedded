#!/usr/bin/env python3
"""Build the two-column sidebar PDF CV from the DOX file.

    1. Parses docs/NguyenQuangBinh_CV.dox   (via cv_dox, shared with the HTML renderer)
    2. Fills build_environment/tool/sidebar_cv/sidebar_cv_template.tex
    3. Compiles with pdflatex

Output: NguyenQuangBinh_CV_Sidebar.pdf

Use --emit-tex <path> to write the generated LaTeX without compiling, which is
the only way to inspect this pipeline on a machine without a TeX installation.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import cv_dox as C

REPO_ROOT = Path(__file__).resolve().parent.parent
DOX_FILE = REPO_ROOT / 'docs' / 'NguyenQuangBinh_CV.dox'
TEMPLATE_FILE = REPO_ROOT / 'build_environment' / 'tool' / 'sidebar_cv' / 'sidebar_cv_template.tex'
OUTPUT_PDF = REPO_ROOT / 'NguyenQuangBinh_CV_Sidebar.pdf'

TOKENS = ('@@NAME@@', '@@CONTACT@@', '@@SUMMARY@@', '@@SKILLS@@', '@@INTERESTS@@',
          '@@AWARDS@@', '@@EXPERIENCE@@', '@@PROJECTS@@', '@@OPEN_SOURCE@@',
          '@@EDUCATION@@', '@@ACHIEVEMENTS@@')

CONTACT_ICONS = {
    'phone': 'phone',
    'email': 'envelope',
    'linkedin': 'linkedin',
    'github': 'github',
    'link': 'external-link-alt',
    'location': 'map-marker-alt',
}


# --- LaTeX escaping -------------------------------------------------------

# Backslash MUST be escaped first, otherwise the backslashes introduced by the
# later replacements get escaped again. The old version also applied escaping
# *after* injecting \textbf{...}, producing invalid "\textbf\{...\}" -- here
# escaping is only ever applied to literal text tokens, so that cannot happen.
LATEX_ESCAPES = (
    ('\\', r'\textbackslash{}'),
    ('&', r'\&'),
    ('%', r'\%'),
    ('$', r'\$'),
    ('#', r'\#'),
    ('_', r'\_'),
    ('{', r'\{'),
    ('}', r'\}'),
    ('~', r'\textasciitilde{}'),
    ('^', r'\textasciicircum{}'),
)


def latex_escape(text: str) -> str:
    for old, new in LATEX_ESCAPES:
        text = text.replace(old, new)
    return text


def latex_url(url: str) -> str:
    """Minimal escaping for the argument of \\href.

    Only the characters that break TeX parsing are touched; '&' and '~' are
    left alone because hyperref handles them and Doxygen emits them raw too.
    """
    return url.replace('%', r'\%').replace('#', r'\#').replace('_', r'\_')


def latex_inline(text: str) -> str:
    """Render cv_dox inline tokens to LaTeX, escaping only literal text."""
    parts = []
    for tok in C.tokenize_inline(text):
        if tok[0] == 'text':
            parts.append(latex_escape(tok[1]))
        elif tok[0] == 'bold':
            parts.append('\\textbf{' + latex_inline(tok[1]) + '}')
        elif tok[0] == 'em':
            parts.append('\\emph{' + latex_inline(tok[1]) + '}')
        else:
            parts.append('\\href{' + latex_url(tok[2]) + '}{' + latex_inline(tok[1]) + '}')
    return ''.join(parts)


def split_title_dates(title: str):
    if '|' in title:
        left, right = title.split('|', 1)
        return left.strip(), right.strip()
    return title.strip(), ''


def bullet_latex(b: C.Bullet) -> str:
    if b.label and b.value:
        text = f'\\textbf{{{latex_escape(b.label)}:}} {latex_inline(b.value)}'
    elif b.label and not b.children:
        text = f'\\textbf{{{latex_escape(b.label)}}}'
    else:
        text = latex_inline(b.text)

    if b.children:
        inner = '\n'.join(f'\\item {bullet_latex(k)}' for k in b.children)
        return f'{text}\n\\begin{{itemize}}\n{inner}\n\\end{{itemize}}'
    return text


def render_items_latex(items, child_blocks=()) -> str:
    """Render a parsed body, grouping consecutive bullets into itemize."""
    out = []
    buf = []

    def flush():
        if buf:
            out.append('\\begin{itemize}')
            out.extend(f'\\item {b}' for b in buf)
            out.append('\\end{itemize}')
            buf.clear()

    for it in items:
        if isinstance(it, C.Bullet):
            buf.append(bullet_latex(it))
            continue

        flush()
        if isinstance(it, C.Field):
            if it.label.lower() in ('responsibilities', 'achievements'):
                # Group header; the bullets that follow speak for themselves.
                out.append(f'\\entryfield{{{latex_escape(it.label)}}}'
                           f'{{\\relax}}')
            else:
                out.append(f'\\entryfield{{{latex_escape(it.label)}}}'
                           f'{{{latex_inline(it.value)}}}')
        elif isinstance(it, C.Para):
            out.append(latex_inline(it.text))

    flush()

    for child in child_blocks:
        name, sub = split_title_dates(child.title)
        head = latex_escape(name)
        if sub:
            head += (r' \textnormal{\small\textcolor{subtextcolor}{\textbar\ '
                     + latex_escape(sub) + '}}')
        out.append(f'\\projectentry{{{head}}}{{{render_items_latex(C.parse_items(child.body))}}}')
    return '\n'.join(out)


# --- section builders -----------------------------------------------------

def build_contact(raw: str) -> str:
    lines = []
    for part in raw.split('|'):
        if not part.strip():
            continue
        kind, text, href = C.classify_contact(part)
        icon = CONTACT_ICONS.get(kind, 'map-marker-alt')
        body = latex_escape(text)
        if href and kind in ('email', 'linkedin', 'github', 'link'):
            body = f'\\href{{{latex_url(href)}}}{{{body}}}'
        lines.append(f'\\contactitem{{{icon}}}{{{body}}}')
    return '\n'.join(lines)


def build_summary(block: C.Block) -> str:
    return latex_inline(' '.join(block.body.split()))


def build_skills(block: C.Block) -> str:
    blocks = []
    for it in C.parse_items(block.body):
        if isinstance(it, C.Field):
            label, value = it.label, it.value
        elif isinstance(it, C.Bullet) and it.label:
            label, value = it.label, it.value
        else:
            continue
        if not value:
            continue

        icon = C.skill_meta(label)['icon']
        out = [f'\\skillcategory{{{icon}}}{{{latex_escape(label)}}}']
        if C.is_prose(value):
            out.append(f'\\skillprose{{{latex_escape(C.strip_inline(value))}}}')
        else:
            tags = ' '.join(f'\\skilltag{{{latex_escape(t)}}}'
                            for t in C.split_tag_list(value))
            out.append(tags + '\n\\vspace{0.4em}')
        blocks.append('\n'.join(out))
    return '\n'.join(blocks)


def build_experience(block: C.Block) -> str:
    """Companies (@subsection) -> roles (@subsubsection) -> projects (@paragraph)."""
    entries = []
    for company in block.children:
        for i, role in enumerate(company.children):
            title, dates = split_title_dates(role.title)
            head = latex_escape(company.title) if i == 0 else ''
            body = render_items_latex(C.parse_items(role.body), role.children)
            entries.append(
                f'\\experienceentry{{{head}}}{{{latex_escape(title)}}}'
                f'{{{latex_escape(dates)}}}{{\n{body}\n}}'
            )
    return '\n\n'.join(entries)


def build_projects(block: C.Block) -> str:
    out = []
    for proj in block.children:
        name, sub = split_title_dates(proj.title)
        head = latex_escape(name)
        if sub:
            head += (r' \textnormal{\small\textcolor{subtextcolor}{\textbar\ '
                     + latex_escape(sub) + '}}')
        out.append(f'\\projectentry{{{head}}}{{{render_items_latex(C.parse_items(proj.body))}}}')
    return '\n'.join(out)


def build_education(block: C.Block) -> str:
    entries = []
    for inst in block.children:
        degree = dates = ''
        extra = []
        for p in C.parse_items(inst.body):
            if not isinstance(p, C.Para):
                continue
            m = re.match(r'^<b>(.*?)</b>\s*\|\s*<em>(.*?)</em>$', p.text.strip())
            if m:
                degree, dates = m.group(1), m.group(2)
            else:
                extra.append(latex_inline(p.text))
        entries.append(
            f'\\educationentry{{{latex_escape(inst.title)}}}{{{latex_escape(degree)}}}'
            f'{{{latex_escape(dates)}}}{{{" ".join(extra)}}}'
        )
    return '\n\n'.join(entries)


def build_achievements(block: C.Block) -> str:
    # \achievementitem, not \awarditem: this section sits in the right column on
    # white paper, so it needs dark text.
    out = []
    for it in C.parse_items(block.body):
        if isinstance(it, C.Bullet):
            out.append(f'\\achievementitem{{trophy}}{{{bullet_latex(it)}}}')
    return '\n'.join(out)


def build_awards(block: C.Block) -> str:
    out = []
    for it in C.parse_items(block.body):
        if not isinstance(it, C.Bullet):
            continue
        head = it.label or C.strip_inline(it.text)
        out.append(f'\\awarditem{{award}}{{\\textbf{{{latex_escape(head)}}}}}')
        for kid in it.children:
            out.append(f'\\awarddetail{{{latex_inline(kid.text)}}}')
    return '\n'.join(out)


def render(dox_text: str) -> str:
    sections = C.parse_doc(dox_text)
    template = TEMPLATE_FILE.read_text(encoding='utf-8')

    for token in TOKENS:
        if token not in template:
            raise SystemExit(f'ERROR: template is missing the {token} placeholder')

    values = {
        '@@NAME@@': latex_escape(C.extract_name(dox_text)),
        '@@CONTACT@@': build_contact(C.extract_contact(dox_text)),
    }
    # token -> (section key in the .dox, builder). Technical interests reuse the
    # skills shape and open source reuses the projects shape, so they share
    # builders rather than duplicating them; the HTML renderer does the same.
    builders = {
        '@@SUMMARY@@':      ('summary',         build_summary),
        '@@SKILLS@@':       ('skills',          build_skills),
        '@@INTERESTS@@':    ('interests',       build_skills),
        '@@AWARDS@@':       ('awards',          build_awards),
        '@@EXPERIENCE@@':   ('work_experience', build_experience),
        '@@PROJECTS@@':     ('projects',        build_projects),
        '@@OPEN_SOURCE@@':  ('open_source',     build_projects),
        '@@EDUCATION@@':    ('education',       build_education),
        '@@ACHIEVEMENTS@@': ('achievements',    build_achievements),
    }
    for token, (key, fn) in builders.items():
        block = sections.get(key)
        values[token] = fn(block) if block else ''

    latex = template
    for token, value in values.items():
        latex = latex.replace(token, value)

    leftover = [t for t in re.findall(r'@@\w+@@', latex)]
    if leftover:
        raise SystemExit(f'ERROR: unsubstituted placeholders remain: {leftover}')
    return latex


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--emit-tex', metavar='PATH',
                        help='write the generated LaTeX here and skip pdflatex')
    args = parser.parse_args()

    if not DOX_FILE.exists():
        print(f'Error: DOX file not found: {DOX_FILE}', file=sys.stderr)
        return 1
    if not TEMPLATE_FILE.exists():
        print(f'Error: Template file not found: {TEMPLATE_FILE}', file=sys.stderr)
        return 1
    if not args.emit_tex and shutil.which('pdflatex') is None:
        print('Error: pdflatex not found. Install TeX Live, or use --emit-tex to '
              'inspect the generated LaTeX without compiling.', file=sys.stderr)
        return 1

    print(f'Reading {DOX_FILE.name}')
    latex = render(DOX_FILE.read_text(encoding='utf-8'))

    if args.emit_tex:
        Path(args.emit_tex).write_text(latex, encoding='utf-8')
        print(f'LaTeX written to {args.emit_tex} (not compiled)')
        return 0

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        (tmpdir / 'cv.tex').write_text(latex, encoding='utf-8')
        print('Compiling PDF (this may take a moment)...')

        for i in range(2):
            result = subprocess.run(
                ['pdflatex', '-interaction=nonstopmode', '-halt-on-error',
                 '-file-line-error', 'cv.tex'],
                cwd=tmpdir, capture_output=True,
            )
            if result.returncode != 0:
                print(f'LaTeX compilation failed (pass {i + 1}):', file=sys.stderr)
                print(result.stdout.decode('utf-8', errors='replace')[-2000:], file=sys.stderr)
                log_file = tmpdir / 'cv.log'
                if log_file.exists():
                    print('\n--- Last 50 lines of log ---', file=sys.stderr)
                    lines = log_file.read_text(encoding='utf-8', errors='replace').splitlines()
                    print('\n'.join(lines[-50:]), file=sys.stderr)
                return 1

        pdf_file = tmpdir / 'cv.pdf'
        if not pdf_file.exists():
            print('Error: PDF was not generated', file=sys.stderr)
            return 1
        shutil.copy(pdf_file, OUTPUT_PDF)
        print(f'Success! Created: {OUTPUT_PDF}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
