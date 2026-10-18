# Gate checks

The Checker's whole job. It receives the repository and this file. Nothing else
— no brief reasoning, no transcripts' conclusions, no account of the session.

Write the outcome into `blog/evidence/<slug>/gate.md` using
`templates/gate.md`.

## Independence

> A checker told what was decided will confirm it was done.

Reject the task, and say so in the gate file, if the prompt contains any of:
the author's notes, the brief's rationale, a summary of what changed, the
Student transcripts' conclusions, or the QA findings' verdicts. The Checker may
read the *files*; it may not be told what they mean. If in doubt, run the checks
and note the contamination — a contaminated PASS is not a PASS.

Run the check in a **fresh session**. The session that built the page is the
worst judge of whether it landed.

## The checks

Run these in order. Record the exact command and its result for each.

### 1. The contract

```sh
python3 tool/check_page_contract.py --report
```

**PASS requires exit 0.** Every non-legacy violation is a SHUT.

Then read the debt and ask the question a report cannot: is the chapter you are
gating listed in `legacy.txt`? If it is, the structural rules are not being
applied to it at all, and the gate is weaker than it looks. A chapter that has a
brief should not be in `legacy.txt`; if it is, that is a SHUT with the reason
"promoted but still exempt".

### 2. The cross-references

```sh
python3 tool/check_page_contract.py --crossrefs
```

Read the resolved table for the chapter **and for everything after it**. A
numeric reference that resolves to a chapter about something else is a stale
reference — the range check cannot see this, because the number is still in
range. There is a known example: `what-is-a-signal` says "Untangling the two is
chapters 29 to 32", but 29–32 are the Ethernet compliance chapters and the
optical material it means begins at chapter 33. A renumbering left it stale.

### 3. The build

```sh
python3 tool/build_blog.py --check
python3 tool/build_blog.py
```

The site must build and the chapter's page must be written to `docs/blog/`.
Record both.

### 4. The tests

```sh
python3 -m unittest discover -s tool/tests -t . -v
```

Green, or a SHUT naming the test.

### 5. The evidence is fresh

```sh
cd blog && sha1sum posts/<slug>.md
```

Compare against `Reviewed-hash:` in all four evidence files. **Any mismatch is a
SHUT** — the evidence reviewed a different revision. The contract check catches
this too, but read it yourself: it is the single most important check on this
page, because it is the one that stops old reviews vouching for new prose.

### 6. Read the page yourself

```sh
python3 tool/build_blog.py
build_environment/.venv/bin/python tool/build_blog_assets.py --png-dir /tmp/figs
```

Then read `docs/blog/<slug>.html` as a reader, and use `read_image` on the
figures in `/tmp/figs` (or on the committed SVGs) — a caption that contradicts
its own figure is checkable that way, and it is a defect nothing else catches.

**Know your limit.** There is no browser here, so MathJax is not executed: you
cannot tell whether `$…$` renders or shows as literal text, and you cannot judge
legibility or contrast on a real screen. Say so in the gate file rather than
implying you looked. Everything else in this list is checkable from the source
plus the images:

- a `::: warn` that states a truism, or a `::: key` that is not load-bearing.
- a figure whose caption contradicts its content (source + image).
- a section whose title promises something the section does not deliver.
- a link that resolves but points at the wrong chapter.
- a takeaway bullet that is a topic rather than a claim.
- math that is *syntactically* broken in a way the checker cannot see — the
  checker covers the delimiters themselves, including inside tables, so what is
  left for you is a construct that is balanced but wrong (`$a + b$` where the
  prose needs `$a - b$`), and whether MathJax renders it at all. That second
  part needs a browser and is a human check; say so rather than implying you
  looked.

### 7. The two languages

```sh
python3 -c "
import json
en = json.load(open('blog/curriculum.json'))
vi = json.load(open('blog/vi/curriculum.json'))
slugs = lambda d: [a['slug'] for p in d['parts'] for a in p['articles']]
pages = lambda d: [p['slug'] for p in d['pages']]
print('plan matches' if slugs(en) == slugs(vi) and pages(en) == pages(vi)
      else 'DRIFT: ' + str(set(slugs(en)) ^ set(slugs(vi))))
"
```

The build's `check_parity` already fails on drift between the trees, so if step 3
passed, the plan is consistent — this prints the same fact in a form you can
quote in the gate file. What no check can tell you is whether a *translated*
chapter still says what the English now says. If the English chapter's prose
changed after the Vietnamese was written, that is a finding for the Editor, not
a SHUT.

## The verdict

- **PASS** — every check above ran, and nothing found is unresolved.
- **SHUT** — one or more checks failed, or the evidence is stale, or the check
  was contaminated.

Write SHUT with the specific command and the specific finding. "Quality is not
there yet" is not a gate verdict; `evidence-stale: gate.md reviewed a1b2c3,
the post is now d4e5f6` is.

The Checker **never repairs the page**. A Checker that fixes what it finds
cannot report it, and the loop loses its adversary.

## After a SHUT

The Producer sends each finding to the role that owns it — a stale hash back to
stages 4–7, a voice rule to the Editor, a wrong number to QA — and then re-runs
the gate with a **new** Checker. Not the same one: it has now seen the failure
and will read for confirmation.

## If the harness itself is wrong

A gate that produces a false SHUT, or misses a real defect twice, is a harness
defect, not a page defect. That belongs in `tool/blog/contract.py` or this file,
with a test in `tool/tests/test_page_contract.py` — a rule that cannot be
tested is a preference.
