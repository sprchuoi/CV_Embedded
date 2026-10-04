#!/usr/bin/env python3
"""Update docs/index.html placeholder regions from docs/NguyenQuangBinh_CV.dox.

Markers in the HTML delimit each generated region:

    <!-- CONTACT_INFO_START -->    ... <!-- CONTACT_INFO_END -->
    <!-- SUMMARY_START -->         ... <!-- SUMMARY_END -->
    <!-- SKILLS_START -->          ... <!-- SKILLS_END -->
    <!-- AWARDS_START -->          ... <!-- AWARDS_END -->
    <!-- WORK_EXPERIENCE_START --> ... <!-- WORK_EXPERIENCE_END -->
    <!-- WORK_EXPERIENCE_FULL_START --> ... <!-- WORK_EXPERIENCE_FULL_END -->
    <!-- PROJECTS_START -->        ... <!-- PROJECTS_END -->
    <!-- EDUCATION_START -->       ... <!-- EDUCATION_END -->
    <!-- ACHIEVEMENTS_START -->    ... <!-- ACHIEVEMENTS_END -->

WORK_EXPERIENCE renders as a flow chart only -- company, role and dates, one
step per role, each linking to that company's detail page under docs/work/.
WORK_EXPERIENCE_FULL is the same content as those detail pages, rendered inline
for the page's "Full" view; both call cv_html.render_company_roles, so the
inline view and the pages cannot disagree.

Structure and inline-markup parsing live in cv_dox.py, shared with the LaTeX
sidebar renderer so the two cannot drift. Body, field and bullet rendering is
shared with the work-detail page builder and lives in cv_html.py.
"""

import html as html_mod
import sys
from pathlib import Path

import cv_dox as C
from cv_html import (bullet_html, inline_html, render_body_items,
                     render_company_roles, split_title_dates, work_companies,
                     work_slug)

REPO_ROOT = Path(__file__).resolve().parent.parent
DOX_FILE = REPO_ROOT / 'docs' / 'NguyenQuangBinh_CV.dox'
HTML_FILE = REPO_ROOT / 'docs' / 'index.html'

MARKERS = {
    'contact_info':    ('<!-- CONTACT_INFO_START -->',    '<!-- CONTACT_INFO_END -->'),
    'summary':         ('<!-- SUMMARY_START -->',         '<!-- SUMMARY_END -->'),
    'skills':          ('<!-- SKILLS_START -->',          '<!-- SKILLS_END -->'),
    'awards':          ('<!-- AWARDS_START -->',          '<!-- AWARDS_END -->'),
    'work_experience': ('<!-- WORK_EXPERIENCE_START -->', '<!-- WORK_EXPERIENCE_END -->'),
    'work_experience_full': ('<!-- WORK_EXPERIENCE_FULL_START -->', '<!-- WORK_EXPERIENCE_FULL_END -->'),
    'projects':        ('<!-- PROJECTS_START -->',        '<!-- PROJECTS_END -->'),
    'open_source':     ('<!-- OPEN_SOURCE_START -->',     '<!-- OPEN_SOURCE_END -->'),
    'education':       ('<!-- EDUCATION_START -->',       '<!-- EDUCATION_END -->'),
    'achievements':    ('<!-- ACHIEVEMENTS_START -->',    '<!-- ACHIEVEMENTS_END -->'),
    'interests':       ('<!-- INTERESTS_START -->',       '<!-- INTERESTS_END -->'),
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


def build_work_chart(block: C.Block) -> str:
    """Work history as a flow chart of links: company, role and dates only.

    One step per role, so a company the CV lists twice (Bosch: SDV then Central
    Gateway) shows the sequence it actually had. Every step links to that
    company's detail page -- the responsibilities, nested projects and tools
    that used to sit on this page now live there, built by
    tool/build_work_pages.py from the same .dox.

    The bullet detail is deliberately absent: this page is the timeline, the
    work/ pages are the record.
    """
    steps = []
    for company in work_companies(block):
        href = f'work/{work_slug(company.key)}.html'
        company_name, _ = split_title_dates(company.title)
        for role in company.children:
            title, dates = split_title_dates(role.title)
            current = ' is-current' if 'present' in dates.lower() else ''
            date_icon = 'far fa-calendar-alt'
            steps.append(
                f'\t<li class="work-flow-step">\n'
                f'\t\t<a class="work-flow-card{current}" href="{html_mod.escape(href, quote=True)}">\n'
                f'\t\t\t<span class="work-flow-dot" aria-hidden="true"></span>\n'
                f'\t\t\t<span class="work-flow-text">\n'
                f'\t\t\t\t<span class="work-flow-company">{inline_html(company_name)}</span>\n'
                f'\t\t\t\t<span class="work-flow-role">{inline_html(title)}</span>\n'
                f'\t\t\t\t<span class="work-flow-dates">'
                f'<i class="{date_icon} mr-1" aria-hidden="true"></i>{inline_html(dates)}</span>\n'
                f'\t\t\t</span>\n'
                f'\t\t\t<span class="work-flow-open" aria-hidden="true">'
                f'<i class="fas fa-arrow-right"></i></span>\n'
                f'\t\t</a>\n'
                f'\t</li>')

    if not steps:
        return '<div class="item mb-3"><em>No work experience parsed.</em></div>'
    return '<ol class="work-flow">\n' + '\n'.join(steps) + '\n</ol>'


def build_work_full(block: C.Block) -> str:
    """The full work detail inline, for the CV page's "Full" view.

    Deliberately the same body as each company's work/ page -- both go through
    cv_html.render_company_roles -- so the inline view can never disagree with
    the page it links to. Each company keeps a link to that page, which is
    where the flow-chart cards point too.
    """
    divs = []
    for company in work_companies(block):
        company_name, location = split_title_dates(company.title)
        slug = html_mod.escape(work_slug(company.key), quote=True)

        head = (f'\t<h4 class="resume-position-title font-weight-bold mb-1">'
                f'{inline_html(company_name)}')
        if location:
            head += f' <span class="work-full-location">{inline_html(location)}</span>'
        head += '</h4>'

        divs.append('\n'.join([
            '<div class="work-full-company">',
            head,
            f'\t<p class="work-full-page-link"><a class="resume-link" href="work/{slug}.html">'
            f'Open full page<i class="fas fa-external-link-alt ml-2" aria-hidden="true"></i></a></p>',
            render_company_roles(company),
            '</div>',
        ]))

    if not divs:
        return '<div class="item mb-3"><em>No work experience parsed.</em></div>'
    return '\n\n'.join(divs)


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
                out.append(f'\t\t<li>{bullet_html(kid)}</li>')
            out.append('\t</ul>')
            out.append('</li>')
        else:
            out.append(f'<li class="mb-2"><i class="{icon} mr-2 text-primary"></i>{bullet_html(it)}</li>')
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
    'work_experience': build_work_chart,
    'work_experience_full': build_work_full,
    'projects': build_projects,
    'education': build_education,
    'achievements': build_achievements,
    'languages': build_languages,
    # Technical interests share the skills shape ("Category: value"), and open
    # source entries share the projects shape ("@subsection" + bullets + Link),
    # so both reuse those renderers rather than duplicating them.
    'interests': build_skills,
    'open_source': build_projects,
}

# Renderers whose output key is not a .dox section key of its own: the work
# history renders the same section twice, as the chart and as the full view.
RENDERER_SECTIONS = {
    'work_experience_full': 'work_experience',
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
        source = RENDERER_SECTIONS.get(key, key)
        if source not in sections:
            continue
        inner = render(sections[source])
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
