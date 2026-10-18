---
name: course-team
description: >
  Write a chapter of the DSP course in blog/. The default is fast: pick the next
  chapter, write the prose and its figures, run the build and one structural
  check, publish — the author checks the facts. `--review` turns on the heavier
  cold-read / QA / gate loop, but only when someone asks for it. Use this skill
  whenever you are about to write, rewrite, promote or extend a chapter of
  blog/, when the user asks "what's next" for the course or "where are we", or
  when `tool/check_page_contract.py` reports a structural finding.
---

# Course Team — write one chapter

A chapter is written, not adjudicated. The default loop has four steps and no
review rounds: **position → draft → build → publish**, with two automatic checks
doing the work a reviewer would otherwise repeat. The user reads the facts; the
checker only refuses a page that is broken in a way a machine can see.

## The two commands

```sh
python3 tool/build_blog.py --check    # markdown subset, figure links, curriculum parity
python3 tool/check_page_contract.py   # the page anatomy and prose hygiene
```

Both exit 0 and the chapter is publishable. If one exits 1, it names the rule and
the line; fix that and run again. Nothing else is required.

## The fast loop (default)

1. **Position.** The next chapter is the earliest unwritten one in curriculum
   order — `python3 tool/check_page_contract.py --report` lists published and
   pending. The user may name a different one; that wins.
2. **Draft.** One pass, in one or two agent calls:
   - `blog/posts/<slug>.md` — body starts at `##`, opening paragraph before the
     first section, 3+ figures, a closing takeaway list, one `::: try`, and the
     `::: optical` callout **last**. No placeholders, balanced `$`, no `#`.
   - `tool/blog/art/plots_<chapter>.py` (or `diagrams_`) with a `FIGURES`
     mapping, and the module added to `tool/blog/art/__init__.py`.
   - Build the assets, look at the PNGs of the two load-bearing figures, fix
     anything unreadable at ~660 px.
3. **Build.** `build_blog_assets.py --only plots`, then `build_blog.py`, then the
   two checks above. Fix what they report.
4. **Publish.** Rebuild `docs/blog/`, report what changed. The user checks the
   numbers and the argument; that is their job, not a simulated reader's.

A brief (`blog/contracts/<slug>.md`) is optional in this mode. Write one when
the chapter is hard enough that its design needs deciding before its prose — the
template is `templates/page-brief.md`. A brief that exists is still validated.

## The review mode (opt-in)

```sh
python3 tool/check_page_contract.py --review
```

This adds the paperwork the fast loop skips: a **mandatory brief**, and a **fresh
evidence pack** per published chapter — two cold reads, QA findings, a gate —
each citing the post's SHA-1, so any edit to the prose invalidates it. Use it
when the user asks for a deep check, or when a chapter has to survive a reader
who will do their own arithmetic (a spec, a paid piece, a teaching deck).

The nine roles and their charters are in `references/roles.md`; the gate checks
are in `references/gate-checks.md`; the templates are in `templates/`. Dispatch
each role as a fresh agent with its charter verbatim and only the artifacts it
may read. The separation that matters: **the author never grades their own
page** — Creator ≠ Student ≠ QA ≠ Checker.

The evidence pack is not deleted by using the fast loop. `blog/evidence/<slug>/`
may hold a pack from an earlier review; it is ignored unless `--review` is on.

## What is always checked, in either mode

- **Structure:** an opening paragraph, at least three figures, a takeaway list,
  a `::: try` callout, the `::: optical` callout last, no placeholders, balanced
  math, every "chapter N" inside 1..48 and never the page itself.
- **Prose hygiene in every language**, translated pages included.
- **The curriculum and the figures:** every figure a script builds is referenced,
  every referenced SVG exists, and the EN/VI plans declare the same chapters.
- **Legacy:** the chapters in `blog/contracts/legacy.txt` predate the contract and
  are exempt from the anatomy. The list may only shrink; a new chapter satisfies
  the contract or does not publish.

## Artifacts

```
blog/posts/<slug>.md            the prose
tool/blog/art/*_<chapter>.py    the figures, registered in art/__init__.py
docs/blog/assets/               the rendered SVGs (committed; the site build never runs a script)
blog/contracts/<slug>.md        optional brief (required with --review)
blog/contracts/legacy.txt       pre-contract chapters (may only shrink)
blog/evidence/<slug>/           optional review pack (required with --review)
tool/check_page_contract.py     the check; --report, --crossrefs, --review
tool/blog/contract.py           the rules, importable, covered by tests
```

## Exit

A page is done when both commands exit 0 and `docs/blog/<slug>.html` renders.
The skill is healthy when a fresh session can name the next chapter from
`--report`, write it in one pass, and hand over a built page with the numbers
stated in the prose and computed in the figures.
