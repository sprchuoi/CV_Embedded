# The page anatomy

What every chapter of this course is, structurally. `tool/blog/contract.py`
checks all of it; this file explains why each rule is there and where its
threshold came from.

The thresholds are **derived from the corpus, not invented**. Each rule below
was measured across the 21 chapters that exist before being imposed, so the
contract is a description of the author's own best work rather than an
aspiration. `tool/tests/test_page_contract.py::test_the_rules_are_calibrated_to_the_corpus`
pins that: if a rule ever rises above what the corpus already does, that test
fails.

## Structure

| Rule | Requirement | Corpus |
|---|---|---|
| `opening` | at least one paragraph before the first `##` | every chapter has 2–4 |
| `figures` | at least 3 figures | minimum is 4 |
| `takeaways` | a closing list ("What to carry forward", "Takeaways", "What to remember") with at least 3 bullets | 9 of 21 have one |
| `try-callout` | a `::: try` callout | 11 of 21 |
| `optical-callout` | a `::: optical` callout | 9 of 21 |
| `optical-last` | it is the last block on the page | 6 of 21 |
| `math-balanced` | even `$` and `$$` delimiters | 21 of 21 |
| `no-placeholders` | no TODO / TBD / FIXME / XXX | 21 of 21 |
| `cross-ref-range` | every "chapter N" is in 1..48 | 21 of 21 |
| `cross-ref-self` | a chapter does not cite itself | 21 of 21 |

Fenced code is masked before every rule, so a shell snippet may contain `:::` or
the word TODO without tripping `no-placeholders` or inventing a callout.

There is exactly one deliberate exception: **`optical-last` judges trailing
content on the unmasked lines.** A fenced code block after the closing callout
is still something after it, and masking it away was a real bypass. Callout
*detection* stays masked, so a snippet containing the literal text `::: optical`
is not mistaken for the callout.

One residual, harmless because the build catches it: an *unclosed* `:::` at end
of file runs to EOF, so a fence after it hides inside the callout and
`optical-last` stays quiet. `tool/blog/markdown.py` rejects an unclosed callout
with a `MarkdownError`, so such a chapter never renders.

A second corner, worth knowing rather than fixing: a fenced block *inside* the
final callout that itself contains a line shaped like `::: optical`. Masking
hides the fence's contents, so the contract can close the callout one line early
and read the renderer's real closing `:::` as trailing prose. The renderer's own
output for such a body is degenerate — a stray `:::` paragraph — so this is a
malformed chapter, not a legitimate one the contract is wrong about. No chapter
in the corpus is shaped this way.

## Why these, and not others

**The opening paragraph.** Every chapter in the corpus orients before it
divides. The reader arriving from the previous chapter needs to know what
problem this one solves before it is cut into sections. It is also the paragraph
the `newcomer` Student persona is asked about first.

**Diagram-first.** Four figures is the corpus minimum and the rule asks for
three. A chapter with fewer is not a chapter of *this* course; it is an article
that happens to be on the same site. Figures are also where the arithmetic is
made checkable — the caption of a plotted figure says what it computes, which is
what QA verifies a claim against.

**The takeaway list.** It is what the two Student personas are asked to
reproduce from memory. If the author cannot write three sentences the reader
should leave with, the chapter has no shape to test. Nine chapters already do
this in the author's own words.

**The `try` callout.** A chapter the reader cannot act on has not transferred.
The corpus's own example is "take the next converter datasheet you open: sample
rate and bits place its output in exactly one of Figure 1's four worlds" — small,
concrete, doable today with what the reader already has.

**The `optical` callout, last.** `blog/README.md` already states this as the
rule that makes the course what it is: *"Every chapter, at every level, ends
with an 'In the optical link' callout — that is the whole point of the blog: it
is not a generic DSP tutorial, it is a DSP tutorial by someone who ships optical
DSP. Do not skip it."* It was never checkable, and 15 of 21 chapters break it in
one of two ways. That is the debt `--report` prints.

**Math delimiters.** An unbalanced `$` silently swallows the rest of the page.
Cheap to check, unpleasant to find on the live site.

## Standalone pages are not chapters

`blog/pages/` holds prose that is not a lesson: `domain` (the index framing) and
`vision` (explicitly *"a working document, not a finished statement"*). The
chapter anatomy does not apply to them, and applying it would be wrong — a
Vision document has no "In the optical link" callout, no figures, and no
takeaway list.

They get **two rules only**, the pair that holds for any prose on this site —
every chapter and every page, in **every language**:

- `no-placeholders`
- `math-balanced`

Nothing else. With two distinct English pages, one of which is by its own
description unfinished, a page *anatomy* would be a rule invented from a sample
of two.

The same two rules are what every language gets, for chapters and pages alike,
plus one rule that exists only because of them: `translation-without-source`,
which fires when a chapter is published in a translation while the canonical
English prose does not exist. A brief, a cold read and an evidence pack are
editorial artifacts written once for the canonical chapter; prose hygiene is
language-independent, so a `TODO` left in `blog/vi/pages/domain.md` is a finding
even though the translation itself is allowed to lag. That is why
`tool/blog/contract.py` loads every language in `i18n.LANGS` for these rules and
only `i18n.DEFAULT_LANG` for the anatomy.
When a third and fourth page appear and share a shape, that shape becomes
derivable; until then, this is the honest boundary.

## What is deliberately *not* machine-checked

Resist adding these to the checker. Each one needs a human or a persona, and a
regex that approximates it will be gamed in a week:

- Whether the intuition actually precedes the formalism.
- Whether an analogy is honest.
- Whether a `::: warn` is a real trap or a truism.
- Reading level. Word counts and syllable counts do not measure comprehension;
  the Student personas do.
- Whether the chapter is at the right level for its part. Only the
  `newcomer` transcript can say that, and only in prose.

The rubric (`rubric.md`) covers these *advisory* dimensions. A rubric score
never fails a gate.

## The brief

`blog/contracts/<slug>.md`, written **before** the prose. Required:

```
Slug: <slug>                       must match the file name and the curriculum
Level: <level>                     must match the curriculum's level for the part
Prerequisites: slug, slug | none    each must be an earlier chapter

## Outcomes                  >= 3 bullets; each demonstrable by a reader
## Claims to verify          >= 2 bullets or table rows, each >= 20 characters
## Transfer                  a substantive `Work:` line and a substantive `Life:` line
## Comprehension plan        must name both personas
```

A brief is validated from the moment it is written. A briefed chapter with no
prose is **in flight** — legitimate, visible in `--report`, and requiring no
evidence yet, because there is no revision to review. That is what makes the
design reviewable on its own, which is the point of writing it first.

## The evidence pack

`blog/evidence/<slug>/`. Required once the chapter is published:

```
student-engineer.md   Persona, Verdict (understood|partial|stalled),
                      ## Reproduced, ## Stalls, ## Dispositions
student-newcomer.md   the same
qa-findings.md        ## Findings, each [open]|[fixed]|[withdrawn], and ## Build
gate.md               Verdict: PASS, ## Checker, ## Commands
```

Every file carries `Reviewed-hash: <sha1 of blog/posts/<slug>.md>`. Edit the
prose and every hash is stale, and the contract check says which file reviewed
which revision. **Evidence is valid for one revision** — that single rule is
what stops a review from being a formality performed once and cited forever.

Every stall needs a disposition, and every disposition needs a reason. An
`[open]` QA finding fails the check: a page publishes with findings *closed*,
not with findings *noted*.

The word-count floor on a transcript (150 words) blocks an empty file. It is not
a measure of quality and the harness does not pretend otherwise — a
rubric-strong, honest, one-line transcript is possible and would fail; a
rubric-weak, padded one passes. That is the price of any mechanical floor, and
it is cheaper than the alternative of accepting a blank file.
