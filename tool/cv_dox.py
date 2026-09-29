#!/usr/bin/env python3
"""Shared parser for the CV source file (docs/NguyenQuangBinh_CV.dox).

The .dox is the single source of truth for both the PDF (Doxygen -> LaTeX) and
the webpage (docs/index.html). This module provides one structure parser and one
inline-markup tokeniser so the two renderers cannot drift apart.

Both entry points live in tool/, so a plain `import cv_dox` resolves when they
are run as `python3 tool/<script>.py`.

Markup contract
---------------
    @mainpage <Name>
    <blank>
    <one-line, '|'-separated contact details>

    @section <key> <TITLE>              top-level CV section
    @subsection <key> <Title>           a company / institution / project
    @subsubsection <key> <Title> | <Dates>   one role
    @paragraph <key> <Name>             a nested project under a role

Inside a body:
    - bullet                two-space "  - " for a nested bullet
    <b>Label:</b> value     a field on its own line
    <b>Label:</b>           a group header when nested bullets follow

Inline markup is limited to <b>, <em> and [text](url).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field as _field

# --- Structure ------------------------------------------------------------

LEVELS = {
    'section': 1,
    'subsection': 2,
    'subsubsection': 3,
    'paragraph': 4,
}

MARKER_RE = re.compile(
    r'^@(section|subsection|subsubsection|paragraph)\s+(\w+)\s*(.*)$',
    re.MULTILINE,
)

# A Doxygen horizontal rule. It renders as a real rule in the PDF, so it must
# stay in the .dox -- but it is noise to both renderers and is stripped here.
RULER_RE = re.compile(r'^\s*(?:-{3,}|\*{3,}|_{3,})\s*$')

# Bold-labelled fields. The .dox uses both spellings -- "<b>Label:</b> value"
# for fields and "<b>Label</b>: value" for skill categories -- because the
# template predates this CV. Both require an explicit colon, which is what
# keeps the education degree line ("<b>Degree</b> | <em>dates</em>") a
# paragraph instead of a mislabelled field.
FIELD_COLON_IN = re.compile(r'^<b>([^<]+):</b>\s*(.*)$')
FIELD_COLON_OUT = re.compile(r'^<b>([^<]+)</b>\s*:\s*(.*)$')


def match_field(line: str):
    """Return (label, value) for a bold field line, else None."""
    for rx in (FIELD_COLON_IN, FIELD_COLON_OUT):
        m = rx.match(line)
        if m:
            return m.group(1).strip(), m.group(2).strip()
    return None

# Inline markup. Group 1 = bold, 2 = em, 3+4 = link text + url.
INLINE_RE = re.compile(r'<b>(.*?)</b>|<em>(.*?)</em>|\[([^\]]+)\]\(([^)]+)\)', re.DOTALL)

# A markdown link used as a whole contact token.
LINK_LABEL_RE = re.compile(r'^\[([^\]]+)\]\(([^)]+)\)$')

# Phone numbers, with or without a country code / parentheses. The old parser
# required a literal "(" before a digit, so a bare "0369393615" was misread as
# a second location.
PHONE_RE = re.compile(r'^[\d\s()+.\-]{8,}$')


@dataclass
class Block:
    """One @section / @subsection / @subsubsection / @paragraph."""

    level: int
    key: str
    title: str
    body: str = ''
    children: list = _field(default_factory=list)


@dataclass
class Field:
    """A "<b>Label:</b> value" line."""

    label: str
    value: str


@dataclass
class Bullet:
    """A list item, optionally with nested children."""

    text: str
    label: str | None = None
    value: str = ''
    children: list = _field(default_factory=list)

    @property
    def is_group(self) -> bool:
        """True for a "- <b>Group:</b>" header that only introduces children."""
        return bool(self.label) and not self.value and bool(self.children)


@dataclass
class Para:
    """One or more plain text lines that are not a bullet or a field."""

    text: str


# --- Inline markup --------------------------------------------------------

def tokenize_inline(text: str):
    """Yield ('text', s) | ('bold', s) | ('em', s) | ('link', label, url).

    Renderers escape only the 'text' tokens, which makes it structurally
    impossible to double-escape generated markup -- the bug that produced
    invalid "\\textbf\\{...\\}" in the LaTeX sidebar renderer.
    """
    pos = 0
    for m in INLINE_RE.finditer(text):
        if m.start() > pos:
            yield ('text', text[pos:m.start()])
        if m.group(1) is not None:
            yield ('bold', m.group(1))
        elif m.group(2) is not None:
            yield ('em', m.group(2))
        else:
            yield ('link', m.group(3), m.group(4))
        pos = m.end()
    if pos < len(text):
        yield ('text', text[pos:])


def strip_inline(text: str) -> str:
    """Flatten inline markup to plain text (used for LaTeX escaping)."""
    return ''.join(tok[1] for tok in tokenize_inline(text))


# --- Body parsing ---------------------------------------------------------

def clean_body(text: str) -> str:
    """Strip rulers, stray Doxygen commands and blank-line runs from a body."""
    lines = []
    for raw in text.splitlines():
        line = raw.rstrip()
        if RULER_RE.match(line):
            continue
        if line.strip().startswith('@'):
            continue
        lines.append(line)

    out = []
    for line in lines:
        if not line.strip() and out and not out[-1].strip():
            continue
        out.append(line)
    return '\n'.join(out).strip()


def parse_doc(text: str) -> dict:
    """Parse the whole .dox into {key: Block} for the top-level sections."""
    matches = list(MARKER_RE.finditer(text))
    if not matches:
        return {}

    blocks = []
    for i, m in enumerate(matches):
        if i + 1 < len(matches):
            end = matches[i + 1].start()
        else:
            end = text.find('*/', m.end())
            if end == -1:
                end = len(text)
        blocks.append(
            Block(
                level=LEVELS[m.group(1)],
                key=m.group(2),
                title=m.group(3).strip(),
                body=clean_body(text[m.end():end]),
            )
        )

    roots = {}
    stack = []
    for b in blocks:
        while stack and stack[-1].level >= b.level:
            stack.pop()
        if stack:
            stack[-1].children.append(b)
        else:
            roots[b.key] = b
        stack.append(b)
    return roots


def _flush_para(items, pending):
    if pending:
        items.append(Para(' '.join(pending).strip()))
        pending.clear()


def parse_items(body: str) -> list:
    """Parse a block body into Field / Bullet / Para items.

    Indentation is measured on the raw line before stripping, and the nested
    case is checked first -- the old sidebar parser tested `line.startswith`
    against an already-stripped string, so its nested branch was unreachable
    and every sub-bullet was flattened to the top level.
    """
    items = []
    pending = []

    for raw in body.splitlines():
        stripped = raw.strip()
        if not stripped:
            _flush_para(items, pending)
            continue

        indent = len(raw) - len(raw.lstrip(' '))

        if stripped.startswith('-'):
            _flush_para(items, pending)
            content = stripped[1:].strip()
            f = match_field(content)
            b = Bullet(text=content, label=f[0], value=f[1]) if f else Bullet(text=content)
            if indent >= 2 and items and isinstance(items[-1], Bullet):
                items[-1].children.append(b)
            else:
                items.append(b)
            continue

        f = match_field(stripped)
        if f:
            _flush_para(items, pending)
            items.append(Field(label=f[0], value=f[1]))
        else:
            pending.append(stripped)

    _flush_para(items, pending)
    return items


# --- Contact classification ----------------------------------------------

def classify_contact(part: str):
    """Return (kind, text, href) for one '|'-separated contact token.

    Handles both the markdown form ([LinkedIn](url)) and a bare domain
    (linkedin.com/in/x) -- the old parser only understood the former, so a bare
    domain produced a relative href in the HTML and vanished from the sidebar.
    """
    p = part.strip()

    m = LINK_LABEL_RE.match(p)
    if m:
        label, url = m.group(1).strip(), m.group(2).strip()
        if '@' in label and ' ' not in label:
            return ('email', label, 'mailto:' + label)
        if not url.startswith('http'):
            url = 'https://' + url
        low = label.lower()
        if 'linkedin' in low:
            return ('linkedin', 'LinkedIn', url)
        if 'github' in low:
            return ('github', 'GitHub', url)
        return ('link', label, url)

    low = p.lower()
    if '@' in p and ' ' not in p:
        return ('email', p, 'mailto:' + p)
    if 'linkedin.com' in low:
        return ('linkedin', 'LinkedIn', p if p.startswith('http') else 'https://' + p)
    if 'github.com' in low:
        return ('github', 'GitHub', p if p.startswith('http') else 'https://' + p)
    if PHONE_RE.match(p) and any(ch.isdigit() for ch in p):
        return ('phone', p, 'tel:' + re.sub(r'[^\d+]', '', p))
    return ('location', p, None)


def extract_contact(dox_text: str) -> str:
    """Return the contact line following @mainpage."""
    m = re.search(r'@mainpage\s+([^\n]+)\n(.*)', dox_text, re.DOTALL)
    if not m:
        return ''
    for line in m.group(2).splitlines():
        s = line.strip()
        if s and not s.startswith('@') and not RULER_RE.match(s):
            return s
    return ''


def extract_name(dox_text: str) -> str:
    m = re.search(r'@mainpage\s+([^\n]+)', dox_text)
    return m.group(1).strip() if m else 'Name'


# --- Skills ---------------------------------------------------------------

# Single home for the category metadata that used to be duplicated as
# SKILL_BADGE_COLORS (HTML) and icon_map (LaTeX), each keyed on stale names.
SKILL_CATEGORIES = {
    'Programming Languages':          {'badge': 'primary',   'icon': 'code'},
    'Scripting':                      {'badge': 'secondary', 'icon': 'terminal'},
    'CI/CD & DevOps':                 {'badge': 'info',      'icon': 'server'},
    'DevOps & CI/CD':                 {'badge': 'info',      'icon': 'server'},
    'Automotive Software':            {'badge': 'success',   'icon': 'car'},
    'Domain Experience':              {'badge': 'success',   'icon': 'car'},
    'Linux Development':              {'badge': 'dark',      'icon': 'linux'},
    'Microcontroller & RTOS':         {'badge': 'warning',   'icon': 'microchip'},
    'Documentation & Automation':     {'badge': 'info',      'icon': 'book'},
    'Tools':                          {'badge': 'secondary', 'icon': 'wrench'},
    'Tools & Platforms':              {'badge': 'secondary', 'icon': 'wrench'},
    'Methodologies':                  {'badge': 'success',   'icon': 'project-diagram'},
    'Soft Skills':                    {'badge': 'warning',   'icon': 'users'},
    'Source Control & Collaboration': {'badge': 'secondary', 'icon': 'code-branch'},
}

DEFAULT_SKILL = {'badge': 'primary', 'icon': 'code'}


def skill_meta(category: str) -> dict:
    return SKILL_CATEGORIES.get(category.strip(), DEFAULT_SKILL)


def split_tag_list(value: str) -> list:
    """Split a comma list, ignoring commas inside parentheses."""
    result = []
    current = ''
    depth = 0
    for char in value:
        if char == '(':
            depth += 1
            current += char
        elif char == ')':
            depth -= 1
            current += char
        elif char == ',' and depth == 0:
            if current.strip():
                result.append(current.strip())
            current = ''
        else:
            current += char
    if current.strip():
        result.append(current.strip())
    return result


def is_prose(value: str) -> bool:
    """A skill value is prose when the .dox wrapped it in <em>.

    Deliberately explicit rather than heuristic: "no comma => prose" fails on
    real content such as "Skilled in CI/CD pipeline setup, GitHub Actions, and
    Docker-based deployment.", which has commas but must not become badges.
    """
    return '<em>' in value
