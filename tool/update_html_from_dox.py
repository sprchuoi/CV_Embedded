#!/usr/bin/env python3
"""Update docs/index.html placeholder regions from docs/NguyenQuangBinh_CV.dox.

Markers in the HTML delimit each generated region:

    <!-- CONTACT_INFO_START -->    ... <!-- CONTACT_INFO_END -->
    <!-- SUMMARY_START -->         ... <!-- SUMMARY_END -->
    <!-- SKILLS_START -->          ... <!-- SKILLS_END -->
    <!-- AWARDS_START -->          ... <!-- AWARDS_END -->
    <!-- WORK_EXPERIENCE_START --> ... <!-- WORK_EXPERIENCE_END -->
    <!-- PROJECTS_START -->        ... <!-- PROJECTS_END -->
    <!-- EDUCATION_START -->       ... <!-- EDUCATION_END -->
    <!-- ACHIEVEMENTS_START -->    ... <!-- ACHIEVEMENTS_END -->

Structure and inline-markup parsing live in cv_dox.py, shared with the LaTeX
sidebar renderer so the two cannot drift.
"""

import html as html_mod
import sys
from pathlib import Path

import cv_dox as C

REPO_ROOT = Path(__file__).resolve().parent.parent
DOX_FILE = REPO_ROOT / 'docs' / 'NguyenQuangBinh_CV.dox'
HTML_FILE = REPO_ROOT / 'docs' / 'index.html'

MARKERS = {
    'contact_info':    ('<!-- CONTACT_INFO_START -->',    '<!-- CONTACT_INFO_END -->'),
    'summary':         ('<!-- SUMMARY_START -->',         '<!-- SUMMARY_END -->'),
    'skills':          ('<!-- SKILLS_START -->',          '<!-- SKILLS_END -->'),
    'awards':          ('<!-- AWARDS_START -->',          '<!-- AWARDS_END -->'),
    'work_experience': ('<!-- WORK_EXPERIENCE_START -->', '<!-- WORK_EXPERIENCE_END -->'),
    'projects':        ('<!-- PROJECTS_START -->',        '<!-- PROJECTS_END -->'),
    'education':       ('<!-- EDUCATION_START -->',       '<!-- EDUCATION_END -->'),
    'achievements':    ('<!-- ACHIEVEMENTS_START -->',    '<!-- ACHIEVEMENTS_END -->'),
    # Dormant: no Languages section in the current CV. Kept so re-adding one is
    # a .dox + HTML edit with no code change.
    'languages':       ('<!-- LANGUAGES_START -->',       '<!-- LANGUAGES_END -->'),
}

CONTACT_ICONS = {
    'phone':    ('fas fa-phone-square',    0),
    'email':    ('fas fa-envelope-square', 1),
    'linkedin': ('fab fa-linkedin',        2),
    'github':   ('fab fa-github',          3),
    'link':     ('fas fa-external-link-alt', 4),
    'location': ('fas fa-map-marker-alt',  5),
}


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


def _bullet_html(b: C.Bullet) -> str:
    """Render one bullet, recursing into nested children."""
    if b.label and b.value:
        text = f'<strong>{html_mod.escape(b.label)}:</strong> {inline_html(b.value)}'
    elif b.label and not b.children:
        text = f'<strong>{html_mod.escape(b.label)}</strong>'
    else:
        text = inline_html(b.text)

    if b.children:
        inner = '\n'.join(f'\t\t\t<li>{_bullet_html(k)}</li>' for k in b.children)
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
            bullets.append(f'\t\t<li>{_bullet_html(it)}</li>')
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


# --- section renderers ----------------------------------------------------

def build_contact_info(raw: str) -> str:
    rows = []
    for part in raw.split('|'):
        if not part.strip():
            continue
        kind, text, href = C.classify_contact(part)
        icon, order = CONTACT_ICONS.get(kind, CONTACT_ICONS['location'])
        body = html_mod.escape(text)
        if href:
            target = '' if kind in ('email', 'phone') else ' target="_blank" rel="noopener"'
            body = f'<a class="resume-link" href="{html_mod.escape(href, quote=True)}"{target}>{body}</a>'
        rows.append([order, f'<li class="mb-2"><i class="{icon} fa-fw fa-lg mr-2"></i>{body}</li>'])

    rows.sort(key=lambda r: r[0])
    if rows:
        rows[-1][1] = rows[-1][1].replace('class="mb-2"', 'class="mb-0"', 1)
    return '\n'.join(r[1] for r in rows)


def build_summary(block: C.Block) -> str:
    text = ' '.join(block.body.split())
    return f'<p class="mb-0">{inline_html(text)}</p>'


def build_skills(block: C.Block) -> str:
    """Skill categories, written as either "- <b>Cat</b>: v" or "<b>Cat</b>: v"."""
    blocks = []
    for item in C.parse_items(block.body):
        if isinstance(item, C.Field):
            label, value = item.label, item.value
        elif isinstance(item, C.Bullet) and item.label:
            label, value = item.label, item.value
        else:
            continue
        if not value:
            continue

        meta = C.skill_meta(label)
        if C.is_prose(value):
            inner = f'<p class="item-meta text-muted mb-0">{inline_html(value)}</p>'
        else:
            tags = C.split_tag_list(value)
            inner = ('<div class="item-content">\n\t\t'
                     + '\n\t\t'.join(
                         f'<span class="badge badge-{meta["badge"]} mr-1 mb-1">{html_mod.escape(t)}</span>'
                         for t in tags)
                     + '\n\t</div>')
        blocks.append('<div class="item mb-3">\n'
                      f'\t<h4 class="item-title">{html_mod.escape(label)}</h4>\n'
                      f'\t{inner}\n'
                      '</div>')
    return '\n'.join(blocks)


def build_work(block: C.Block) -> str:
    """Companies (@subsection) -> roles (@subsubsection) -> projects (@paragraph)."""
    divs = []
    for company in block.children:
        for i, role in enumerate(company.children):
            first = (i == 0)
            parts = ['<div class="item mb-4">' if first else '<div class="item mb-3">']
            if first:
                parts.append(f'\t<h4 class="resume-position-title font-weight-bold mb-1">'
                             f'{inline_html(company.title)}</h4>')
            title, dates = split_title_dates(role.title)
            meta = inline_html(title) + (f' | <em>{inline_html(dates)}</em>' if dates else '')
            parts.append(f'\t<div class="resume-position-time text-muted mb-2">{meta}</div>')
            parts.extend(render_body_items(C.parse_items(role.body), role.children))
            parts.append('</div>')
            divs.append('\n'.join(parts))
    return '\n\n'.join(divs) or '<div class="item mb-3"><em>No work experience parsed.</em></div>'


def build_projects(block: C.Block) -> str:
    divs = []
    for proj in block.children:
        name, sub = split_title_dates(proj.title)
        parts = ['<div class="item mb-4">',
                 f'\t<h4 class="resume-position-title font-weight-bold mb-1">{inline_html(name)}</h4>']
        if sub:
            parts.append(f'\t<div class="resume-position-time text-muted mb-2"><em>{inline_html(sub)}</em></div>')
        parts.extend(render_body_items(C.parse_items(proj.body)))
        parts.append('</div>')
        divs.append('\n'.join(parts))
    return '\n\n'.join(divs) or f'<div class="item mb-3"><em>{inline_html(block.body)}</em></div>'


def build_education(block: C.Block) -> str:
    entries = block.children or [C.Block(level=2, key='', title='', body=block.body)]
    items = []
    for inst in entries:
        paras = [inline_html(p.text) for p in C.parse_items(inst.body) if isinstance(p, C.Para)]
        lines = ['<li class="mb-3">']
        if inst.title:
            lines.append(f'\t<h4 class="mb-1">{inline_html(inst.title)}</h4>')
        if paras:
            lines.append('\t' + '<br>\n\t'.join(paras))
        lines.append('</li>')
        items.append('\n'.join(lines))
    return '<ul class="list-unstyled resume-education-list">\n' + '\n'.join(items) + '\n</ul>'


def _build_list_section(block: C.Block, icon: str) -> str:
    out = []
    for it in C.parse_items(block.body):
        if not isinstance(it, C.Bullet):
            continue
        if it.children:
            head = it.label or C.strip_inline(it.text)
            out.append(f'<li class="mb-2"><i class="{icon} mr-2 text-primary"></i>'
                       f'<strong>{html_mod.escape(head)}</strong>')
            out.append('\t<ul class="list-unstyled item-meta text-muted mb-0 mt-1">')
            for kid in it.children:
                out.append(f'\t\t<li>{_bullet_html(kid)}</li>')
            out.append('\t</ul>')
            out.append('</li>')
        else:
            out.append(f'<li class="mb-2"><i class="{icon} mr-2 text-primary"></i>{_bullet_html(it)}</li>')
    return '\n'.join(out)


def build_achievements(block: C.Block) -> str:
    return _build_list_section(block, 'fas fa-trophy')


def build_awards(block: C.Block) -> str:
    return _build_list_section(block, 'fas fa-award')


def build_languages(block: C.Block) -> str:
    items = []
    for it in C.parse_items(block.body):
        if isinstance(it, C.Bullet):
            if it.label:
                items.append(f'<li class="mb-2"><strong>{html_mod.escape(it.label)}:</strong> '
                             f'{inline_html(it.value)}</li>')
            else:
                items.append(f'<li class="mb-2">{inline_html(it.text)}</li>')
    return '\n'.join(items) or '<li>No languages listed</li>'


RENDERERS = {
    'summary': build_summary,
    'skills': build_skills,
    'awards': build_awards,
    'work_experience': build_work,
    'projects': build_projects,
    'education': build_education,
    'achievements': build_achievements,
    'languages': build_languages,
}


def replace_block(html: str, start: str, end: str, new_inner: str):
    """Replace a marked region. Returns (html, found)."""
    import re
    pattern = re.compile(re.escape(start) + r'.*?' + re.escape(end), re.DOTALL)
    if not pattern.search(html):
        return html, False
    return pattern.sub(f'{start}\n{new_inner}\n{end}', html, count=1), True


VOID_TAGS = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input',
             'link', 'meta', 'param', 'source', 'track', 'wbr'}


def check_structure(html: str) -> list:
    """Return structural problems: unbalanced markers or unbalanced tags.

    A previous edit deleted a whole <section> including its closing tag, which
    silently mis-nested everything after it and went unnoticed for weeks.
    """
    from html.parser import HTMLParser

    problems = []
    for key, (start, end) in MARKERS.items():
        ns, ne = html.count(start), html.count(end)
        if ns != ne:
            problems.append(f'marker {key}: {ns} start vs {ne} end')
        elif ns > 1:
            problems.append(f'marker {key}: appears {ns} times')

    class Balance(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.stack = []
            self.problems = []

        def handle_starttag(self, tag, attrs):
            if tag not in VOID_TAGS:
                self.stack.append(tag)

        def handle_endtag(self, tag):
            if tag in VOID_TAGS:
                return
            if not self.stack:
                self.problems.append(f'stray </{tag}>')
            elif self.stack[-1] == tag:
                self.stack.pop()
            elif tag in self.stack:
                self.problems.append(f'</{tag}> closes <{self.stack[-1]}>')
                while self.stack and self.stack.pop() != tag:
                    pass
            else:
                self.problems.append(f'stray </{tag}>')

    parser = Balance()
    parser.feed(html)
    problems.extend(parser.problems)
    if parser.stack:
        problems.append(f'unclosed tags: {parser.stack}')
    return problems


def main() -> int:
    if not DOX_FILE.exists():
        print(f'DOX file not found: {DOX_FILE}', file=sys.stderr)
        return 1
    if not HTML_FILE.exists():
        print(f'HTML file not found: {HTML_FILE}', file=sys.stderr)
        return 1

    dox_text = DOX_FILE.read_text(encoding='utf-8')
    sections = C.parse_doc(dox_text)
    html = HTML_FILE.read_text(encoding='utf-8')

    missing = []

    contact = C.extract_contact(dox_text)
    if contact:
        html, ok = replace_block(html, *MARKERS['contact_info'], build_contact_info(contact))
        if not ok:
            missing.append('contact_info')

    empty = []
    for key, render in RENDERERS.items():
        if key not in sections:
            continue
        inner = render(sections[key])
        if not inner.strip():
            empty.append(key)
        html, ok = replace_block(html, *MARKERS[key], inner)
        if not ok:
            missing.append(key)

    failed = False
    if missing:
        # The previous version only warned here, which is exactly how a deleted
        # Certifications section went unnoticed for weeks.
        print(f'ERROR: .dox has sections with no matching HTML markers: {missing}', file=sys.stderr)
        print('Add the markers to docs/index.html or remove the section from the .dox.', file=sys.stderr)
        failed = True
    if empty:
        print(f'ERROR: .dox sections rendered to nothing: {empty}', file=sys.stderr)
        failed = True

    problems = check_structure(html)
    if problems:
        print('ERROR: generated HTML is malformed:', file=sys.stderr)
        for p in problems:
            print(f'  - {p}', file=sys.stderr)
        failed = True

    if failed:
        return 1

    HTML_FILE.write_text(html + ('' if html.endswith('\n') else '\n'), encoding='utf-8')
    print(f'index.html updated from {DOX_FILE.name} ({len(sections)} sections).')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
