Reviewed-hash: <sha1 of blog/posts/<slug>.md — run: sha1sum blog/posts/<slug>.md>
Verdict: <PASS | SHUT>

<!--
Copy to blog/evidence/<slug>/gate.md. Run by a FRESH Checker that received the
repository and references/gate-checks.md and nothing else — no brief rationale,
no transcript conclusions, no summary of the session.

The Verdict line must be in the header, before the first `##`.

Delete these comments.
-->

## Checker

State what you were given, and confirm independence. If the prompt contained any
account of how the page was made, say so here and treat the check as
contaminated — a contaminated PASS is not a PASS.

"Fresh session. Given the repository and references/gate-checks.md. No brief,
no transcripts' conclusions, no session summary."

## Commands

Every command, with its exit status.

```
$ python3 tool/check_page_contract.py --report
$ python3 tool/check_page_contract.py --crossrefs
$ python3 tool/build_blog.py --check
$ python3 tool/build_blog.py
$ python3 -m unittest discover -s tool/tests -t . -v
$ sha1sum blog/posts/<slug>.md
```

## Findings

One entry per check in `references/gate-checks.md`, including the ones that
passed. A check that was skipped is a finding, not a blank.

- contract: <result>
- cross-references: <result, including what each reference resolves to>
- build: <result>
- tests: <result>
- evidence freshness: <the hash you compared, and whether all four match>
- read the rendered page: <what you saw as a reader — the defects a machine
  cannot see, or that you found none>
- two languages: <result>

## If SHUT

The specific command and the specific finding. One entry per blocking finding.

- `evidence-stale`: gate.md reviewed `a1b2c3`, the post is now `d4e5f6`.

"The quality is not there yet" is not a gate verdict. Name the check, the
artifact and the revision.
