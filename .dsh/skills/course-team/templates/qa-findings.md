Reviewed-hash: <sha1 of blog/posts/<slug>.md — run: sha1sum blog/posts/<slug>.md>

<!--
Copy to blog/evidence/<slug>/qa-findings.md.

Every claim in the brief's `## Claims to verify` gets a finding. A finding is
`[open]`, `[fixed]` or `[withdrawn]`, and `[open]` fails the contract check: a
page publishes with findings CLOSED, not with findings NOTED.

`[withdrawn]` means the claim was wrong or uncheckable and the prose was changed
to stop making it — say which sentence changed. It is not a way to drop a claim
you could not check.

Delete these comments.
-->

## Findings

- [fixed] <the claim>: <what was wrong, and what was changed>. Verified with
  <the command or figure script>.
- [withdrawn] <the claim>: uncheckable from this repository. The sentence
  "<the original sentence>" was changed to <the weaker, true claim>.
- [open] <the claim>: <what is unresolved>. **This blocks publication.**

If a check found nothing, say so in the same format — do not leave the section
empty, because an empty section cannot be told apart from an unrun check:

- [withdrawn] Nothing found: the arithmetic, the links, the cross-references and
  the EN/VI parity all check out at this revision.

## Build

The exact commands run, and their result. Not "tests pass" — the command and the
exit status.

```
$ python3 tool/build_blog.py --check
blog: curriculum and figures are consistent            (exit 0)

$ python3 tool/check_page_contract.py
contract: every enforced chapter is publishable        (exit 0)

$ python3 -m unittest discover -s tool/tests -t . -v
Ran <n> tests ... OK                                   (exit 0)
```

Copy the counts from the run you actually did — do not carry a number over from
a previous chapter. A recorded count that does not match the suite is a finding
against the evidence.

## Checks performed

- [ ] every number in the prose traced to the figure that computes it
- [ ] arithmetic re-derived independently of the figure script
- [ ] relative links resolved against `docs/blog/`
- [ ] `--crossrefs` read after any curriculum change
- [ ] EN/VI curriculum parity (the build's `check_parity`)
- [ ] terminology matches the neighbouring chapters
- [ ] no figure contradicts its caption
