#!/usr/bin/env python3
"""HTML primitives shared by the CV's web renderers.

Two scripts turn docs/NguyenQuangBinh_CV.dox into the published site:

    tool/update_html_from_dox.py   docs/index.html -- the work-history flow chart
                                   and every other section
    tool/build_work_pages.py       docs/work/<company>.html -- the work detail
                                   behind each flow-chart step

They must agree on how a .dox body becomes HTML, so the body/field/bullet
rendering lives here rather than in either script -- for the same reason the
structure parser lives in cv_dox.py.

Both entry points live in tool/, so a plain `import cv_html` resolves when they
are run as `python3 tool/<script>.py`.
"""

from __future__ import annotations

import html as html_mod

try:
    import cv_dox as C
except ImportError:  # imported as `tool.cv_html` (tests, -m)
    from . import cv_dox as C


# --- inline markup -> HTML ------------------------------------------------

def inline_html(text: str) -> str:
    """Render cv_dox inline tokens to HTML, escaping only literal text."""
    out = []
    for tok in C.tokenize_inline(text):
        if tok[0] == 'text':
            out.append(html_mod.escape(tok[1]))
        elif tok[0] == 'bold':
            out.append(f'<strong>{inline_html(tok[1])}</strong>')
        elif tok[0] == 'em':
            out.append(f'<em>{inline_html(tok[1])}</em>')
        else:
            url = html_mod.escape(tok[2], quote=True)
            out.append(f'<a href="{url}" target="_blank" rel="noopener">{inline_html(tok[1])}</a>')
    return ''.join(out)


def split_title_dates(title: str):
    """Split "Title | Dates" on the first pipe."""
    if '|' in title:
        left, right = title.split('|', 1)
        return left.strip(), right.strip()
    return title.strip(), ''


# --- bodies ---------------------------------------------------------------

def bullet_html(b: C.Bullet) -> str:
    """Render one bullet, recursing into nested children."""
    if b.label and b.value:
        text = f'<strong>{html_mod.escape(b.label)}:</strong> {inline_html(b.value)}'
    elif b.label and not b.children:
        text = f'<strong>{html_mod.escape(b.label)}</strong>'
    else:
        text = inline_html(b.text)

    if b.children:
        inner = '\n'.join(f'\t\t\t<li>{bullet_html(k)}</li>' for k in b.children)
        return f'{text}\n\t\t<ul class="resume-list">\n{inner}\n\t\t</ul>'
    return text


def render_body_items(items, child_blocks=()) -> list:
    """Render a parsed body into HTML lines.

    Fields and paragraphs break the bullet run; consecutive bullets are grouped
    into a single <ul>. Nested @paragraph projects are appended last, which is
    where they appear in the source.
    """
    out = []
    bullets = []

    def flush():
        if bullets:
            out.append('\t<ul class="resume-list">')
            out.extend(bullets)
            out.append('\t</ul>')
            bullets.clear()

    for it in items:
        if isinstance(it, C.Bullet):
            bullets.append(f'\t\t<li>{bullet_html(it)}</li>')
            continue

        flush()
        if isinstance(it, C.Field):
            label = html_mod.escape(it.label)
            if it.value:
                out.append(f'\t<p><strong>{label}:</strong> {inline_html(it.value)}</p>')
            else:
                out.append(f'\t<p class="mb-2"><strong>{label}:</strong></p>')
        elif isinstance(it, C.Para):
            out.append(f'\t<p class="mb-2">{inline_html(it.text)}</p>')

    flush()

    for child in child_blocks:
        name, sub = split_title_dates(child.title)
        out.append('\t<div class="item-meta text-muted mt-2"><strong>' + inline_html(name) + '</strong>'
                   + (f' &mdash; {inline_html(sub)}' if sub else '') + '</div>')
        out.extend(render_body_items(C.parse_items(child.body)))
        out.append('\t')
    return out


# --- work history ---------------------------------------------------------

def work_companies(work_block: C.Block) -> list:
    """Companies that belong on the flow chart: those with at least one role.

    A company @subsection with no @subsubsection has nothing to show on either
    the chart or a detail page, so both renderers skip it.
    """
    return [c for c in work_block.children if c.children]


def work_slug(key: str) -> str:
    """URL slug for a company @subsection key: exp_marvell -> marvell."""
    return key[len('exp_'):] if key.startswith('exp_') else key


def render_role(role: C.Block) -> str:
    """Render one role (@subsubsection) with its nested @paragraph projects."""
    parts = ['<div class="item mb-4">']
    title, dates = split_title_dates(role.title)
    meta = inline_html(title) + (f' | <em>{inline_html(dates)}</em>' if dates else '')
    parts.append(f'\t<div class="resume-position-time text-muted mb-2">{meta}</div>')
    parts.extend(render_body_items(C.parse_items(role.body), role.children))
    parts.append('</div>')
    return '\n'.join(parts)


def render_company_roles(company: C.Block) -> str:
    """Render every role of one company -- the body of its detail page."""
    roles = [render_role(r) for r in company.children]
    return '\n\n'.join(roles) or '<div class="item mb-3"><em>No roles recorded.</em></div>'
