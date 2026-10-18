"""The course-team page contract: what makes a chapter publishable.

The blog's own README states two obligations that nothing enforced: every
chapter is diagram-first, and every chapter ends with an "In the optical link"
callout. This module turns that prose into a check, and adds the three things a
chapter needs before it is a *teaching* page rather than a correct one:

* a **brief** (``blog/contracts/<slug>.md``) -- the learning contract the author
  and the Teacher agree before the prose exists: the outcomes the reader can
  demonstrate afterwards, the claims QA must verify, and where the idea touches
  work and ordinary life;
* an **evidence pack** (``blog/evidence/<slug>/``) -- two cold-read comprehension
  transcripts from the Student personas, the QA findings, and the gate verdict;
* the **structural anatomy** every chapter shares.

The rules are derived from the corpus, not invented. ``MIN_FIGURES`` is 3
against a corpus minimum of 4; ``MIN_OPENING_PARAGRAPHS`` is 1 against a corpus
minimum of 2; the takeaway section exists in 9 of 21 chapters and the optical
callout is the last block in 6 -- those two are the debt this harness exists to
burn down (``--report``).

Two kinds of rule, and only one of them can fail a build:

``legacy.txt``
    The chapters published before this contract existed, one slug per line. A
    listed chapter is exempt from the structural rules -- so a typo fix in an
    old chapter is never blocked. The list may only shrink, in both directions:
    a chapter that has been given a brief *and* already satisfies every
    structural rule must be removed from it (``legacy-stale-exemption``), and a
    slug that is not in :data:`LEGACY_BASELINE` cannot be added to it
    (``legacy-added``). The baseline is here rather than in the data file so
    that exempting a new chapter is a visible edit to the harness.

Everything else is enforced, and the enforcement is deliberately narrow: this
check never fails a *deploy*, only a pull request. The site build is stdlib-only
and independent on purpose (see ``.github/workflows/python-app.yml``); a
pedagogy finding must not be able to take a published page down.

Standard library only, and importable, so ``tool/tests`` can exercise every rule
without a subprocess.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path

from . import i18n, site

# --------------------------------------------------------------------------- #
# The rules, and the corpus measurement each one is set from.
# --------------------------------------------------------------------------- #

#: Corpus minimum is 4 ("serdes-in-an-optical-module"); the blog is diagram-first.
MIN_FIGURES = 3

#: Corpus minimum is 2 ("bert-ber-and-fec"); every chapter orients before it
#: divides the problem into sections.
MIN_OPENING_PARAGRAPHS = 1

#: Bullets in the closing "what to carry forward" list.
MIN_TAKEAWAYS = 3

#: Outcomes in a brief. Fewer than three is not a learning contract.
MIN_OUTCOMES = 3

#: Claims a brief hands to QA.
MIN_CLAIMS = 2

#: A comprehension transcript shorter than this is a rubber stamp, not a read.
#: It is a floor that blocks an empty file; it is not evidence of understanding.
MIN_STUDENT_WORDS = 150

#: Section titles that count as the closing takeaway list. The author's own
#: heading is "What to carry forward"; the rest are the shapes a chapter from
#: another hand would plausibly use.
TAKEAWAY_TITLES = (
    "what to carry forward",
    "carry forward",
    "what to remember",
    "takeaways",
    "takeaway",
    "key points",
)

#: Placeholders that mean the chapter is not finished.
PLACEHOLDER_RE = re.compile(r"\b(TODO|TBD|FIXME|XXX)\b|lorem ipsum", re.I)

#: "chapter 10", "chapters 29 to 32", "chapter 8". The em/en dash and "through"
#: are here because a range written with them still has to resolve.
CHAPTER_REF_RE = re.compile(
    r"\bchapters?\s+(\d{1,3})(?:\s*(?:to|through|and|,|-|\u2013|\u2014)\s*(\d{1,3}))?",
    re.I,
)

#: Dispositions a Student transcript may carry for a stall, and a QA finding.
STALL_DISPOSITIONS = ("fixed", "accepted", "rejected")
QA_DISPOSITIONS = ("open", "fixed", "withdrawn")

#: The two Student personas. Both read every chapter: one catches rigour gaps,
#: the other catches unexplained jargon and missing intuition.
PERSONAS = ("engineer", "newcomer")

#: Every file an evidence pack must contain.
EVIDENCE_FILES = tuple(f"student-{p}.md" for p in PERSONAS) + (
    "qa-findings.md",
    "gate.md",
)


# --------------------------------------------------------------------------- #
# Findings
# --------------------------------------------------------------------------- #


#: Every chapter that was published before this contract existed, frozen.
#:
#: ``blog/contracts/legacy.txt`` may name a subset of this set and nothing else.
#: A chapter published *after* the contract has no exemption available to it: it
#: must satisfy the anatomy and carry a brief, or it does not publish.
#:
#: This lives in the checker rather than in the data file on purpose. The point
#: of the ratchet is that weakening it has to be a visible, reviewable change to
#: the harness itself, not a one-line append to a list. Editing this frozenset
#: is how a reviewer sees that someone exempted a chapter -- and the diff says
#: so in the one place a reviewer is already looking.
LEGACY_BASELINE = frozenset({
    "bert-ber-and-fec",
    "chromatic-dispersion-and-the-fde",
    "coherent-optical-dsp-pipeline",
    "convolution-and-lti",
    "decibels-and-dynamic-range",
    "ethernet-compliance-test-in-practice",
    "ethernet-gain-and-the-link-budget",
    "ethernet-generations-and-the-data-processing-view",
    "fft-and-dft-in-ethernet-compliance",
    "fir-filter-design",
    "quantization-and-enob",
    "reading-an-eye-diagram",
    "sampling-and-aliasing",
    "serdes-anatomy",
    "serdes-channels-and-the-link-budget",
    "serdes-clock-recovery-and-jitter",
    "serdes-equalisation",
    "serdes-fec-and-error-budget",
    "serdes-in-an-optical-module",
    "the-fft",
    "what-is-a-signal",
})

#: The two rules that hold for any prose on this site, chapter or page.
PROSE_RULES = ("no-placeholders", "math-balanced")


@dataclass(frozen=True)
class Violation:
    """One rule broken by one chapter (or by the repo's own bookkeeping)."""

    slug: str
    rule: str
    detail: str

    def __str__(self) -> str:
        return f"{self.slug}: [{self.rule}] {self.detail}"


@dataclass
class ChapterResult:
    """What the checker found for one chapter (or one chapter's brief)."""

    slug: str
    number: int
    title: str
    level: str
    published: bool
    legacy: bool
    briefed: bool
    structural: list[Violation] = field(default_factory=list)
    paperwork: list[Violation] = field(default_factory=list)
    metrics: dict[str, int] = field(default_factory=dict)

    @property
    def violations(self) -> list[Violation]:
        return self.structural + self.paperwork

    @property
    def in_flight(self) -> bool:
        """Briefed but not yet written: the design exists, the prose does not."""
        return self.briefed and not self.published

    @property
    def promoted(self) -> bool:
        """A chapter held to the full contract: briefed, and structurally clean."""
        return self.briefed and not self.structural

    @property
    def enforced(self) -> bool:
        """Whether a violation here can fail the build."""
        return not self.legacy


@dataclass
class PageResult:
    """What the checker found for one standalone page (``blog/pages/``).

    A page is prose that is not a lesson -- the index framing, the Vision
    document. The chapter anatomy deliberately does not apply: a Vision page has
    no "In the optical link" callout and no figures. Only the two rules that
    hold for any prose, chapter or not, are enforced here.
    """

    slug: str
    title: str
    written: bool
    violations: list[Violation] = field(default_factory=list)

    @property
    def enforced(self) -> bool:
        return self.written


@dataclass
class Report:
    """The whole run: per-chapter results plus repo-level findings."""

    chapters: list[ChapterResult] = field(default_factory=list)
    pages: list[PageResult] = field(default_factory=list)
    repo: list[Violation] = field(default_factory=list)
    crossrefs: list[tuple[str, int, str]] = field(default_factory=list)
    review: bool = False

    @property
    def failures(self) -> list[Violation]:
        out = list(self.repo)
        for chapter in self.chapters:
            if chapter.enforced:
                out.extend(chapter.violations)
        for page in self.pages:
            if page.enforced:
                out.extend(page.violations)
        return out

    @property
    def debt(self) -> list[ChapterResult]:
        """Legacy chapters that still break a structural rule."""
        return [c for c in self.chapters if c.legacy and c.structural]

    @property
    def promotable(self) -> list[ChapterResult]:
        """Legacy chapters that are structurally clean: only a brief is missing."""
        return [c for c in self.chapters
                if c.legacy and c.published and not c.structural]

    @property
    def in_flight(self) -> list[ChapterResult]:
        """Briefed chapters whose prose is not written yet."""
        return [c for c in self.chapters if c.in_flight]

    @property
    def published(self) -> list[ChapterResult]:
        return [c for c in self.chapters if c.published]

    @property
    def ok(self) -> bool:
        return not self.failures


class ContractError(RuntimeError):
    """The repository cannot be checked at all (e.g. an unreadable curriculum)."""


# --------------------------------------------------------------------------- #
# Markdown scanning
# --------------------------------------------------------------------------- #


def mask_code(body: str) -> list[str]:
    """Return the body's lines with fenced-code content blanked out.

    A shell snippet is allowed to contain ``:::`` or the word TODO without
    tripping a rule about prose. Blanking keeps the line count, so a reported
    line number still points at the real file.
    """
    lines = body.splitlines()
    out: list[str] = []
    fence = False
    for line in lines:
        if line.lstrip().startswith("```"):
            fence = not fence
            out.append("")
            continue
        out.append("" if fence else line)
    return out


def sentences_to_blocks(lines: list[str]) -> list[list[str]]:
    """Split lines into blank-line-separated non-empty blocks."""
    blocks: list[list[str]] = []
    current: list[str] = []
    for line in lines:
        if line.strip():
            current.append(line)
        elif current:
            blocks.append(current)
            current = []
    if current:
        blocks.append(current)
    return blocks


def callouts(lines: list[str]) -> list[tuple[str, int, int]]:
    """Every top-level ``::: kind`` callout as ``(kind, start, end)`` line indices.

    Nesting is counted, exactly as ``tool/blog/markdown.py`` counts it: a callout
    may contain another callout, and reading the inner ``:::`` as the outer one's
    close made a chapter that legitimately ends with an optical callout holding a
    nested note look like it had content after the callout.

    ``end`` is the index of the closing ``:::`` of the outermost block. An
    unclosed callout runs to the end of the file; the Markdown renderer rejects
    those, so this only has to be forgiving enough not to crash on one.
    """
    # The renderer's own shapes, so the two cannot disagree about what is a
    # callout: an open is `::: kind` plus an optional title, a close is `:::`.
    open_re = re.compile(r"^\s*:::\s*([a-zA-Z]+)\s*(.*?)\s*$")
    close_re = re.compile(r"^\s*:::\s*$")

    found: list[tuple[str, int, int]] = []
    start: int | None = None
    kind = ""
    depth = 0
    for index, line in enumerate(lines):
        if start is None:
            match = open_re.match(line)
            if match:
                start, kind, depth = index, match.group(1), 1
        elif open_re.match(line):
            depth += 1
        elif close_re.match(line):
            depth -= 1
            if depth == 0:
                found.append((kind, start, index))
                start = None
    if start is not None:
        found.append((kind, start, len(lines) - 1))
    return found


def parse_doc(text: str) -> tuple[dict[str, str], dict[str, str]]:
    """Split a brief or evidence file into its header and its ``##`` sections.

    The header is the ``Key: value`` block before the first ``##`` heading. Keys
    are lower-cased; section titles are lower-cased and stripped. Only the last
    occurrence of a duplicated key wins, which is the least surprising choice
    for a hand-written file.
    """
    header: dict[str, str] = {}
    sections: dict[str, str] = {}
    current: str | None = None
    body: list[str] = []

    def flush() -> None:
        if current is not None:
            sections[current] = "\n".join(body).strip()

    for line in text.splitlines():
        heading = re.match(r"^##\s+(.+?)\s*$", line)
        if heading:
            flush()
            current = heading.group(1).strip().lower()
            body = []
            continue
        if current is None:
            field_match = re.match(r"^([A-Za-z][A-Za-z0-9 _-]*):\s*(.*)$", line)
            if field_match:
                header[field_match.group(1).strip().lower()] = field_match.group(2).strip()
            continue
        body.append(line)
    flush()
    return header, sections


def bullets(text: str) -> list[str]:
    """Top-level ``- item`` bullets in a section, in order."""
    return [line.strip()[2:].strip() for line in text.splitlines()
            if line.startswith("- ")]


def sha1_of(path: Path) -> str:
    """The content hash a brief's evidence has to cite."""
    return hashlib.sha1(path.read_bytes()).hexdigest()


def _word_count(text: str) -> int:
    return len(re.findall(r"\b[\w'-]+\b", text))


def _table_rows(text: str) -> list[str]:
    """Data rows of the first Markdown table in a section, minus the header.

    A brief may state its claims as bullets or as a table; either has to yield
    the claim text itself, or the length floor below would be measuring blanks.
    """
    rows = [
        line.strip() for line in text.splitlines()
        if line.strip().startswith("|")
        and not re.match(r"^\s*\|[\s:|-]+\|\s*$", line)
    ]
    return rows[1:] if rows else []


# --------------------------------------------------------------------------- #
# Structural rules (the page anatomy)
# --------------------------------------------------------------------------- #


def check_anatomy(body: str, *, slug: str, number: int,
                  planned: int) -> tuple[list[Violation], dict[str, int]]:
    """The rules every non-legacy chapter satisfies. Returns findings + metrics."""
    out: list[Violation] = check_prose(body, slug=slug)
    lines = mask_code(body)

    figures = [line for line in lines if line.startswith("![")]
    if len(figures) < MIN_FIGURES:
        out.append(_v(slug, "figures",
                      f"{len(figures)} figure(s); this course is diagram-first "
                      f"and needs at least {MIN_FIGURES}"))

    # Opening: prose before the first section, so the reader is oriented before
    # the chapter subdivides the problem.
    opening_end = next((i for i, line in enumerate(lines)
                        if line.startswith("## ")), len(lines))
    opening = [block for block in sentences_to_blocks(lines[:opening_end])
               if not block[0].strip().startswith(":::")]
    if len(opening) < MIN_OPENING_PARAGRAPHS:
        out.append(_v(slug, "opening",
                      "no orientation paragraph before the first '##' section"))

    found = callouts(lines)
    kinds = [kind for kind, _, _ in found]

    if "optical" not in kinds:
        out.append(_v(slug, "optical-callout",
                      "no '::: optical' callout -- the blog README makes it "
                      "mandatory at every level"))

    if found:
        kind, _, end = found[-1]
        # Trailing content is judged on the *unmasked* lines: a fenced code
        # block after the optical callout is still something after it. Callout
        # detection above stays on the masked lines, so a snippet cannot open a
        # callout that does not exist.
        raw_lines = body.splitlines()
        trailing = "\n".join(raw_lines[end + 1:]).strip()
        if kind != "optical" or trailing:
            out.append(_v(slug, "optical-last",
                          f"the last block is {kind!r}, not the optical callout "
                          f"(or prose follows it)"))

    if "try" not in kinds:
        out.append(_v(slug, "try-callout",
                      "no '::: try' callout -- a chapter the reader cannot act "
                      "on has not transferred"))

    # The takeaway list the two Student personas are asked to reproduce.
    headings = [(i, line[3:].strip()) for i, line in enumerate(lines)
                if line.startswith("## ")]
    takeaways = []
    for index, (line_no, title) in enumerate(headings):
        if title.strip().lower().rstrip(":") in TAKEAWAY_TITLES:
            end = headings[index + 1][0] if index + 1 < len(headings) else len(lines)
            takeaways = bullets("\n".join(lines[line_no:end]))
            break
    if not takeaways:
        out.append(_v(slug, "takeaways",
                      "no closing 'What to carry forward' section -- name it "
                      "that, or 'Takeaways'/'What to remember'"))
    elif len(takeaways) < MIN_TAKEAWAYS:
        out.append(_v(slug, "takeaways",
                      f"{len(takeaways)} takeaway bullet(s); at least "
                      f"{MIN_TAKEAWAYS} are needed to be worth reproducing"))

    # Cross-references: ranges are the ones a renumbering breaks.
    joined = "\n".join(lines)
    refs = []
    for match in CHAPTER_REF_RE.finditer(joined):
        first = int(match.group(1))
        last = int(match.group(2)) if match.group(2) else first
        refs.extend(range(first, last + 1))
    for target in sorted(set(refs)):
        if not 1 <= target <= planned:
            out.append(_v(slug, "cross-ref-range",
                          f"references chapter {target}, but the curriculum "
                          f"plans 1..{planned}"))
        elif target == number:
            out.append(_v(slug, "cross-ref-self",
                          f"references itself as chapter {target}"))

    metrics = {
        "figures": len(figures),
        "callouts": len(found),
        "words": _word_count(joined),
        "display_math": joined.count("$$") // 2,
    }
    return out, metrics


def _v(slug: str, rule: str, detail: str) -> Violation:
    return Violation(slug=slug, rule=rule, detail=detail)


def check_prose(body: str, *, slug: str) -> list[Violation]:
    """The rules that hold for any prose on this site, chapter or page.

    Two rules only, and both are corpus-derived: all 21 chapters and both
    standalone pages satisfy them. There is no page *anatomy* -- with two
    distinct pages, one of which is explicitly a working document rather than a
    finished statement, inventing a shape for them would be inventing a rule
    from a sample of two.
    """
    out: list[Violation] = []
    lines = mask_code(body)
    joined = "\n".join(lines)

    match = PLACEHOLDER_RE.search(joined)
    if match:
        out.append(_v(slug, "no-placeholders",
                      f"unfinished marker {match.group(0)!r} in the prose"))
    if joined.count("$$") % 2:
        out.append(_v(slug, "math-balanced", "an odd number of '$$' delimiters"))
    if len(re.findall(r"(?<!\\)\$", joined.replace("$$", ""))) % 2:
        out.append(_v(slug, "math-balanced", "an odd number of inline '$' delimiters"))
    return out


# --------------------------------------------------------------------------- #
# The brief (blog/contracts/<slug>.md)
# --------------------------------------------------------------------------- #


def check_brief(text: str, *, slug: str, level: str,
                preceding: dict[str, int]) -> list[Violation]:
    """Validate one page brief. ``preceding`` maps an already-earlier slug to its number."""
    out: list[Violation] = []
    header, sections = parse_doc(text)

    declared = header.get("slug", "")
    if declared != slug:
        out.append(_v(slug, "brief-slug",
                      f"brief declares slug {declared!r}, expected {slug!r}"))

    declared_level = header.get("level", "")
    if declared_level and declared_level != level:
        out.append(_v(slug, "brief-level",
                      f"brief declares level {declared_level!r}, the curriculum "
                      f"says {level!r}"))

    raw_prereqs = header.get("prerequisites", "").strip()
    # "None" is a value, not a slug that happens to be missing.
    if raw_prereqs.lower() in ("", "none"):
        prereqs: list[str] = []
    else:
        prereqs = [p.strip() for p in raw_prereqs.split(",") if p.strip()]
        if not prereqs:
            out.append(_v(slug, "brief-prerequisites", "empty Prerequisites field"))
    for prereq in prereqs:
        if prereq not in preceding:
            out.append(_v(slug, "brief-prerequisites",
                          f"prerequisite {prereq!r} is not an earlier chapter "
                          f"of this curriculum"))

    outcomes = bullets(sections.get("outcomes", ""))
    if len(outcomes) < MIN_OUTCOMES:
        out.append(_v(slug, "brief-outcomes",
                      f"{len(outcomes)} outcome(s); at least {MIN_OUTCOMES} are "
                      f"needed for the Student roles to test anything"))

    claims_section = sections.get("claims to verify", "")
    claims = bullets(claims_section) or _table_rows(claims_section)
    substantive = [c for c in claims if len(c) >= 20]
    if len(substantive) < MIN_CLAIMS:
        out.append(_v(slug, "brief-claims",
                      f"{len(substantive)} substantive claim(s); QA needs at "
                      f"least {MIN_CLAIMS} named claims"))

    transfer = sections.get("transfer", "")
    for field_name in ("work", "life"):
        match = re.search(rf"^\s*{field_name}\s*:\s*(.+)$", transfer,
                          re.I | re.M)
        if not match or len(match.group(1).strip()) < 15:
            out.append(_v(slug, "brief-transfer",
                          f"the Transfer section needs a substantive "
                          f"'{field_name}:' line"))

    plan = sections.get("comprehension plan", "")
    lowered = plan.lower()
    for persona in PERSONAS:
        if persona not in lowered:
            out.append(_v(slug, "brief-plan",
                          f"the comprehension plan says nothing about the "
                          f"'{persona}' persona"))
    return out


# --------------------------------------------------------------------------- #
# The evidence pack (blog/evidence/<slug>/)
# --------------------------------------------------------------------------- #


def check_evidence(directory: Path, *, slug: str, post: Path) -> list[Violation]:
    """Validate one evidence pack against the revision of the post it reviewed."""
    out: list[Violation] = []
    digest = sha1_of(post)

    for name in EVIDENCE_FILES:
        if not (directory / name).is_file():
            out.append(_v(slug, "evidence-missing", f"no {name} in the evidence pack"))
    if any(not (directory / name).is_file() for name in EVIDENCE_FILES):
        return out

    for name in EVIDENCE_FILES:
        text = (directory / name).read_text(encoding="utf-8")
        header, sections = parse_doc(text)
        reviewed = header.get("reviewed-hash", "")
        if reviewed != digest:
            out.append(_v(slug, "evidence-stale",
                          f"{name} reviewed {reviewed[:12] or '(nothing)'}, the "
                          f"post is now {digest[:12]} -- re-run the review"))
        if name.startswith("student-"):
            out.extend(_check_transcript(text, header, sections, slug=slug, name=name))
        elif name == "qa-findings.md":
            out.extend(_check_qa(sections, slug=slug))
        else:
            out.extend(_check_gate(header, sections, slug=slug))
    return out


def _check_transcript(text: str, header: dict[str, str], sections: dict[str, str],
                      *, slug: str, name: str) -> list[Violation]:
    out: list[Violation] = []
    verdict = header.get("verdict", "").lower()
    if verdict not in ("understood", "partial", "stalled"):
        out.append(_v(slug, "evidence-verdict",
                      f"{name} has Verdict {verdict!r}; expected understood, "
                      f"partial or stalled"))
    if _word_count(text) < MIN_STUDENT_WORDS:
        out.append(_v(slug, "evidence-thin",
                      f"{name} is {_word_count(text)} words; a cold read that "
                      f"short is a rubber stamp, not a transcript"))

    if not bullets(sections.get("reproduced", "")):
        out.append(_v(slug, "evidence-reproduced",
                      f"{name} lists nothing the reader could reproduce"))

    stalls = bullets(sections.get("stalls", ""))
    dispositions = bullets(sections.get("dispositions", ""))
    if len(dispositions) < len(stalls):
        out.append(_v(slug, "evidence-dispositions",
                      f"{name} names {len(stalls)} stall(s) but only "
                      f"{len(dispositions)} disposition(s)"))
    for item in dispositions:
        tag = re.match(r"\[(\w+)\]", item)
        if not tag or tag.group(1).lower() not in STALL_DISPOSITIONS:
            out.append(_v(slug, "evidence-dispositions",
                          f"{name}: disposition {item[:40]!r} must start with "
                          f"[fixed], [accepted] or [rejected]"))
        elif len(item) < 25:
            out.append(_v(slug, "evidence-dispositions",
                          f"{name}: disposition {item[:40]!r} gives no reason"))
    return out


def _check_qa(sections: dict[str, str], *, slug: str) -> list[Violation]:
    out: list[Violation] = []
    findings = bullets(sections.get("findings", ""))
    if not findings:
        out.append(_v(slug, "evidence-qa",
                      "qa-findings.md has no '## Findings' bullets (write "
                      "'- [withdrawn] nothing found', if that is the truth)"))
    for item in findings:
        tag = re.match(r"\[(\w+)\]", item)
        if not tag or tag.group(1).lower() not in QA_DISPOSITIONS:
            out.append(_v(slug, "evidence-qa",
                          f"QA finding {item[:40]!r} must start with [open], "
                          f"[fixed] or [withdrawn]"))
        elif tag.group(1).lower() == "open":
            out.append(_v(slug, "evidence-qa-open",
                          f"QA finding still open: {item[:80]!r}"))
    if not sections.get("build", "").strip():
        out.append(_v(slug, "evidence-qa",
                      "qa-findings.md has no '## Build' section recording the "
                      "commands run and their result"))
    return out


def _check_gate(header: dict[str, str], sections: dict[str, str],
                *, slug: str) -> list[Violation]:
    out: list[Violation] = []
    verdict = header.get("verdict", "").upper()
    if verdict != "PASS":
        out.append(_v(slug, "evidence-gate",
                      f"gate verdict is {verdict or '(absent)'}, not PASS"))
    if not sections.get("checker", "").strip():
        out.append(_v(slug, "evidence-gate",
                      "gate.md does not name the checker that ran it"))
    if not sections.get("commands", "").strip():
        out.append(_v(slug, "evidence-gate",
                      "gate.md does not record the commands it ran"))
    return out


# --------------------------------------------------------------------------- #
# Legacy exemptions
# --------------------------------------------------------------------------- #


def load_legacy(path: Path) -> tuple[list[str], list[Violation]]:
    """Read ``legacy.txt``: one slug per line, ``#`` comments allowed."""
    if not path.is_file():
        return [], [_v("(repo)", "legacy-missing",
                       f"{path.name} not found; every published chapter would "
                       f"be held to a contract written after it")]
    slugs: list[str] = []
    problems: list[Violation] = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        stripped = line.split("#", 1)[0].strip()
        if not stripped:
            continue
        if stripped in slugs:
            problems.append(_v("(repo)", "legacy-duplicate",
                               f"{stripped!r} listed twice (line {number})"))
            continue
        slugs.append(stripped)
    return slugs, problems


# --------------------------------------------------------------------------- #
# The run
# --------------------------------------------------------------------------- #


def check(repo_root: Path, *, review: bool = False) -> Report:
    """Check the whole course. Raises ``ContractError`` if it cannot be loaded.

    Two modes, because they cost different things:

    * **fast** (default) -- the rules that are free to check: the page anatomy,
      prose hygiene, the curriculum and the figure registry. This is the mode a
      chapter is written in: write it, build it, and the checker either accepts
      it or names a structural defect.
    * **review** (``--review``) -- the same, plus the paperwork that costs a
      reader's time: a mandatory brief and a fresh evidence pack (two cold
      reads, QA findings, a gate). Opt-in, for a chapter that warrants it.
    """
    curriculum_path = repo_root / "blog" / "curriculum.json"
    posts_dir = repo_root / "blog" / "posts"
    try:
        curriculum = site.load_curriculum(
            curriculum_path, posts_dir, lang=i18n.DEFAULT_LANG
        )
    except site.CurriculumError as exc:
        raise ContractError(str(exc)) from exc

    articles = [a for part in curriculum.parts for a in part.articles]
    planned = len(articles)
    number_of = {a.slug: a.number for a in articles}

    report = Report(review=review)
    legacy, problems = load_legacy(repo_root / "blog" / "contracts" / "legacy.txt")
    report.repo.extend(problems)
    legacy_set = set(legacy)
    en_published = {a.slug for a in articles if a.published}

    for slug in legacy:
        if slug not in number_of:
            report.repo.append(_v("(repo)", "legacy-unknown",
                                  f"{slug!r} is exempted but is not a chapter of "
                                  f"this curriculum"))
        elif not (posts_dir / f"{slug}.md").is_file():
            report.repo.append(_v("(repo)", "legacy-unwritten",
                                  f"{slug!r} is exempted but has no prose"))
        if slug not in LEGACY_BASELINE:
            # The hole this closes: without it, one line in legacy.txt exempts a
            # brand-new chapter from the anatomy *and* from the brief, and the
            # gate then reports that every enforced chapter is publishable.
            report.repo.append(_v("(repo)", "legacy-added",
                                  f"{slug!r} is not in LEGACY_BASELINE -- the "
                                  f"exemption list predates the contract and may "
                                  f"only shrink; a new chapter must satisfy the "
                                  f"contract or not publish"))

    for article in articles:
        post = posts_dir / f"{article.slug}.md"
        brief_path = repo_root / "blog" / "contracts" / f"{article.slug}.md"
        evidence_dir = repo_root / "blog" / "evidence" / article.slug
        briefed = brief_path.is_file()

        if not article.published and not briefed:
            # Nothing exists for this chapter yet: not a finding, just unwritten.
            continue

        structural: list[Violation] = []
        metrics: dict[str, int] = {}
        if article.published:
            structural, metrics = check_anatomy(article.body or "",
                                                slug=article.slug,
                                                number=article.number,
                                                planned=planned)

        paperwork: list[Violation] = []
        if briefed:
            # A brief is checked from the moment it is written, before any
            # prose exists: the design is reviewable on its own, which is the
            # whole point of writing it first.
            preceding = {a.slug: a.number for a in articles
                         if a.number < article.number}
            paperwork.extend(check_brief(brief_path.read_text(encoding="utf-8"),
                                         slug=article.slug, level=article.level,
                                         preceding=preceding))
            if review and article.published:
                # The evidence pack is the expensive half, so it is opt-in:
                # --review asks for it, the default mode does not.
                paperwork.extend(check_evidence(evidence_dir, slug=article.slug,
                                                post=post))
        elif review and article.published and article.slug not in legacy_set:
            paperwork.append(_v(article.slug, "brief-missing",
                                "no blog/contracts/<slug>.md -- a chapter written "
                                "outside the harness cannot be reviewed"))

        result = ChapterResult(
            slug=article.slug,
            number=article.number,
            title=article.title,
            level=article.level,
            published=article.published,
            legacy=article.slug in legacy_set,
            briefed=briefed,
            structural=structural,
            paperwork=paperwork,
            metrics=metrics,
        )
        report.chapters.append(result)

        if result.legacy and result.promoted and result.published:
            report.repo.append(_v(article.slug, "legacy-stale-exemption",
                                  "exempted from the contract but already "
                                  "structurally clean and briefed -- remove it "
                                  "from legacy.txt"))

    # The standalone pages: index framing and the Vision document. They get the
    # prose-agnostic rules and nothing else -- see check_prose.
    for page in curriculum.pages:
        report.pages.append(PageResult(
            slug=page.slug,
            title=page.title,
            written=page.written,
            violations=(check_prose(page.body or "", slug=page.slug)
                        if page.written else []),
        ))

    # Every other language. The *teaching* contract is the canonical chapter's
    # job -- a brief and a cold read are editorial artifacts written once -- but
    # prose hygiene is language-independent, and a `TODO` left in a translated
    # page was passing silently. So: the prose rules for every language, the
    # anatomy and the evidence for English only. The blog README already says the
    # translated prose may lag as far behind as it likes; the plan may not drift,
    # and the build's own check_parity enforces that.
    for lang in i18n.LANGS:
        if lang == i18n.DEFAULT_LANG:
            continue
        curriculum_path = repo_root / "blog" / lang / "curriculum.json"
        if not curriculum_path.is_file():
            # A declared language with no curriculum source is the *build's*
            # error (``check_parity``), not this check's; duplicating it here
            # would only mean reporting the same fault twice, in two voices.
            continue
        try:
            other = site.load_curriculum(
                curriculum_path, repo_root / "blog" / lang / "posts", lang=lang,
            )
        except site.CurriculumError as exc:
            report.repo.append(_v("(repo)", "language-unreadable",
                                  f"{lang}: {exc}"))
            continue
        written = [(p.slug, p.body or "") for p in other.pages if p.written]
        written += [(a.slug, a.body or "") for a in other.articles if a.published]
        for slug, body in written:
            report.repo.extend(check_prose(body, slug=f"{lang}/{slug}"))

        # The canonical language is the source of truth. A chapter published in a
        # translation while the English original does not exist is not "prose that
        # lagged" -- there is nothing for it to be a translation of, so it skipped
        # the anatomy, the brief and the gate entirely. The plan matching in both
        # curricula is not enough: it says the chapter is planned, not written.
        #
        # No legacy exemption is needed here: an exempted slug with no English
        # prose already fails `legacy-unwritten`, and one with English prose is in
        # `en_published` by definition.
        for article in other.articles:
            if article.published and article.slug not in en_published:
                report.repo.append(_v(f"{lang}/{article.slug}",
                                      "translation-without-source",
                                      f"published here but the "
                                      f"{i18n.DEFAULT_LANG} chapter does not "
                                      f"exist -- the canonical prose is the one "
                                      f"the contract reviews"))

    # The cross-reference table a human reads after any renumbering.
    title_of = {a.number: a.title for a in articles}
    for article in articles:
        if not article.published:
            continue
        for line in mask_code(article.body or ""):
            for match in CHAPTER_REF_RE.finditer(line):
                first = int(match.group(1))
                last = int(match.group(2)) if match.group(2) else first
                for target in range(first, last + 1):
                    report.crossrefs.append((article.slug, target,
                                             title_of.get(target, "(out of range)")))
    return report


def render(report: Report, *, verbose: bool) -> str:
    """A human-readable summary, in the voice of the rest of ``tool/``."""
    lines: list[str] = []
    chapters = report.published
    lines.append(f"contract: {len(chapters)} published chapter(s), "
                 f"{len(report.in_flight)} in flight, "
                 f"{len(report.promotable)} promotable, "
                 f"{len(report.debt)} carry debt, "
                 f"{len([p for p in report.pages if p.written])} standalone page(s)")
    lines.append("mode: review -- brief and a fresh evidence pack are required"
                 if report.review else
                 "mode: fast -- structure only; --review adds the brief and evidence pack")

    if verbose:
        lines.append("")
        lines.append(f"{'#':>3}  {'chapter':44} {'fig':>3} {'call':>4} {'legacy':>6}  contract")
        for chapter in chapters:
            state = "clean" if not chapter.violations else \
                f"{len(chapter.violations)} finding(s)"
            lines.append(
                f"{chapter.number:3}  {chapter.slug:44} "
                f"{chapter.metrics.get('figures', 0):3} "
                f"{chapter.metrics.get('callouts', 0):4} "
                f"{('yes' if chapter.legacy else 'no'):>6}  {state}"
            )

    if report.in_flight:
        lines.append("")
        lines.append(f"In flight: {len(report.in_flight)} briefed chapter(s) with "
                     f"no prose yet.")
        for chapter in report.in_flight:
            lines.append(f"    {chapter.slug} -- brief is valid; the prose is next")

    if report.promotable:
        lines.append("")
        lines.append(f"Promotable: {len(report.promotable)} grandfathered "
                     f"chapter(s) already satisfy the anatomy.")
        lines.append("  Each needs a brief and an evidence pack, and then its line "
                     "deleted from legacy.txt:")
        for chapter in report.promotable:
            lines.append(f"    {chapter.slug}")

    if report.failures:
        lines.append("")
        lines.append(f"FAIL -- {len(report.failures)} finding(s) block the pull request:")
        for failure in report.failures:
            lines.append(f"  {failure}")

    debt = report.debt
    if debt:
        lines.append("")
        lines.append(f"Debt (advisory): {len(debt)} grandfathered chapter(s) predate "
                     f"the contract.")
        lines.append("  These do not block anything. Promote one by giving it a "
                     "brief and fixing its anatomy:")
        for chapter in debt:
            rules = ", ".join(sorted({v.rule for v in chapter.structural}))
            lines.append(f"    {chapter.slug} -- {rules}")

    if not report.failures:
        lines.append("")
        lines.append("contract: every enforced chapter is publishable")
    return "\n".join(lines)


def render_crossrefs(report: Report) -> str:
    """Every numeric chapter reference, resolved, for a renumbering review."""
    lines = ["numeric chapter references, resolved against the curriculum:", ""]
    current = None
    for slug, target, title in sorted(report.crossrefs):
        if slug != current:
            lines.append(f"  {slug}")
            current = slug
        lines.append(f"      chapter {target:2} -> {title}")
    if not report.crossrefs:
        lines.append("  (none)")
    return "\n".join(lines)
