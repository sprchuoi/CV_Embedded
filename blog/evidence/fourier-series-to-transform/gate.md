Reviewed-hash: ac9daff6a73b388c0c52a98b3c865d9112b9daaa
Verdict: SHUT

## Checker

The Checker (this session) ran every command below itself. It is a fresh session: given the repository and `.dsh/skills/course-team/references/gate-checks.md`; no brief rationale, no account of how the page was made, no session summary, no Student transcripts' conclusions and no QA verdicts in the prompt. Not contaminated.

The page under gate is `fourier-series-to-transform`, the only chapter `--report`
names as blocked. It is not in `blog/contracts/legacy.txt`; it has a brief. The
other three evidence files and this one all cite the same post revision.

## Commands

Run from `/home/sprchuoi/sandboxes/CV_Embedded`.

```
$ sha1sum blog/posts/fourier-series-to-transform.md
ac9daff6a73b388c0c52a98b3c865d9112b9daaa  blog/posts/fourier-series-to-transform.md
(exit 0)

$ python3 tool/check_page_contract.py --report
...
FAIL -- 1 finding(s) block the pull request:
  fourier-series-to-transform: [evidence-missing] no gate.md in the evidence pack
(exit 1; the finding is this file, which did not exist before the gate ran)

$ python3 tool/check_page_contract.py --report     # after this gate was written
...
FAIL -- 1 finding(s) block the pull request:
  fourier-series-to-transform: [evidence-gate] gate verdict is SHUT, not PASS
(exit 1; the contract is red because this gate is SHUT, not because of a fresh
structural finding)

$ python3 tool/check_page_contract.py --crossrefs
numeric chapter references, resolved against the curriculum:

  fourier-series-to-transform
      chapter  6 -> The DFT, Without Magic
      chapter  6 -> The DFT, Without Magic
      chapter  8 -> Windows, Leakage and Resolution
  what-is-a-signal
      chapter  8 -> Windows, Leakage and Resolution
      chapter 10 -> Convolution, and Why Every DSP Block Is One
      chapter 10 -> Convolution, and Why Every DSP Block Is One
      chapter 10 -> Convolution, and Why Every DSP Block Is One
      chapter 18 -> Random Signals, Autocorrelation and PSD
      chapter 18 -> Random Signals, Autocorrelation and PSD
      chapter 18 -> Random Signals, Autocorrelation and PSD
      chapter 29 -> Reading an Eye Diagram
      chapter 30 -> BERT, BER and the FEC Contract
      chapter 31 -> The FFT and DFT in Ethernet Compliance
      chapter 32 -> Compliance Test in Practice
(exit 1; `report.ok` is false for the missing gate, not for an unresolved
reference)

$ python3 tool/build_blog.py --check
blog: curriculum and figures are consistent
(exit 0)

$ python3 tool/build_blog.py
... docs/blog/fourier-series-to-transform.html
(exit 0; the chapter's page was written to docs/blog/)

$ python3 -m unittest discover -s tool/tests -t . -v
...
FAIL: test_the_contract_holds (tool.tests.test_page_contract.TestAgainstTheRealCorpus.test_the_contract_holds)
  AssertionError: False is not true : ['fourier-series-to-transform: [evidence-missing] no gate.md in the evidence pack']
FAIL: test_the_report_states_that_the_contract_holds (tool.tests.test_page_contract.TestTheReport.test_the_report_states_that_the_contract_holds)
  AssertionError: 'every enforced chapter is publishable' not found ...
Ran 202 tests ... FAILED (failures=2, skipped=1)
(exit 1 before the gate existed. After this gate is written the same two corpus
tests fail on `evidence-gate` instead of `evidence-missing`; no other test
fails. There is no independent test failure to name.)

$ build_environment/.venv/bin/python tool/build_blog_assets.py --png-dir /tmp/figs
...
figures: wrote 62 SVG(s)
(exit 0; all seven fourier-* figures rendered, to /tmp/figs/plots/)

$ python3 -c "import json; en=json.load(open('blog/curriculum.json')); vi=json.load(open('blog/vi/curriculum.json')); ..."
plan matches
(exit 0)
```

## Findings

- contract: The gated chapter's own rules are clean. Before this file existed the
  only finding was `evidence-missing` for `gate.md`; the chapter is not in
  `legacy.txt`, has a brief, and the structural rules (figures, opening,
  callouts, takeaways, placeholders, math, cross-ref range/self) all pass. After
  this file exists the only contract finding is `evidence-gate`, because the
  verdict is SHUT. No non-legacy structural violation was found.
- cross-references: The gated chapter's three references resolve correctly:
  chapter 6 (twice) -> "The DFT, Without Magic", chapter 8 -> "Windows, Leakage
  and Resolution", exactly as the prose intends. The same table contains the
  known stale reference in `what-is-a-signal`: its "chapters 29 to 32" resolves
  to the Ethernet compliance chapters (29 Reading an Eye Diagram, 30 BERT/BER,
  31 FFT/DFT in Ethernet Compliance, 32 Compliance Test in Practice), while the
  optical DSP material it means begins at chapter 33. That defect is in a legacy
  chapter, not in this page's prose; it is recorded for the Editor, and it is
  not the page-specific reason for this verdict.
- build: `--check` exit 0; the full build exit 0 and wrote
  `docs/blog/fourier-series-to-transform.html`; all seven `fourier-*` figure
  references resolve and all seven rendered.
- tests: The two failures are the corpus tests that assert the contract holds
  (`test_the_contract_holds`, `test_the_report_states_that_the_contract_holds`);
  they fail because the evidence pack is not PASS, first `evidence-missing`, now
  `evidence-gate`. No other test failed (202 run, 2 failed, 1 skipped).
- evidence freshness: `sha1sum blog/posts/fourier-series-to-transform.md` =
  `ac9daff6a73b388c0c52a98b3c865d9112b9daaa`. `student-engineer.md`,
  `student-newcomer.md`, `qa-findings.md` and this `gate.md` all carry that
  exact hash. All four match; no evidence is stale.
- read the rendered page: I read `docs/blog/fourier-series-to-transform.html`
  as a reader and rendered all seven figures with
  `build_blog_assets.py --png-dir /tmp/figs` and inspected them with
  `read_image`. The figures match their captions and the printed numbers (the
  coefficient table, the 0.5000/0.0000/0.2122 areas, the 0.0517/0.1034/0.1061
  lobes, the three symmetry shapes, the 0.4007/0.4414/0.4454/0.4458 rise-time
  sequence, the five seam numbers, the 0.22508/0.11254/0.05627 line heights and
  the rect-sinc widths). The defects I found are in the prose, and are recorded
  below. `::: key`, `::: math`, `::: try` and `::: optical` all render as
  callouts (no literal `:::`), there is no placeholder, and the optical callout
  is last. **Limit:** there is no browser here, so MathJax was not executed; I
  cannot certify that `$...$` renders rather than showing as literal text, nor
  judge legibility or contrast on a real screen. I did not look at a browser.
- two languages: The parity command exits 0 and prints `plan matches`. The
  English chapter has no Vietnamese counterpart yet (the vi tree has only
  `what-is-a-signal`), so there is no translated prose to compare and no
  `translation-without-source`. The English prose changed while no translation
  exists; that is an Editor matter, not a gate failure.

## If SHUT

- **The section-2 recipe divides by zero.**
  `blog/posts/fourier-series-to-transform.md:53` says: "multiply by the
  harmonic, average over a period, divide by the harmonic's own average." The
  ordinary average of a sine over a period is zero, so the recipe as written
  divides by zero. The intended divisor is the harmonic's mean square — the
  average of the harmonic against itself, which is 1/2 for a unit sine — or,
  equivalently, its own area `T_0/2`, which is what line 47 calls "the
  reference" and what the takeaway at line 165 says ("divide by the harmonic's
  own area `T0/2`"). The formula at line 55 is correct; the recipe sentence is
  not. At `T_0 = 1` the mean, the mean square and the area all coincide
  numerically (0.5000), which is why the error survives: the page never shows
  the general-`T_0` case where "average" and "area" differ by `T_0`. A reader
  who follows the recipe rather than the formula is led into a division by
  zero. This is a correctness defect in the sentence that teaches the central
  measurement, not a stylistic preference. The engineer transcript records the
  same stall and calls it "the only place in the chapter where a reader who
  trusts the prose is led into a division by zero"; the newcomer records it
  twice (the section recipe and the takeaway's "average"). The QA findings do
  not mention it. Command: rendered-page read, no machine rule catches it; the
  page is at the cited lines.
- **Second page finding: "At K = 3 at the corners" is contradicted by Figure 1.**
  This is a second finding for the same gate; the recipe above is the decisive
  one.
  `blog/posts/fourier-series-to-transform.md:15` says the error lives "at
  `K = 3` at the corners". Figure 1's blue `K = 3` curve visibly wobbles across
  the flat tops as well, and the page's own line 13 says the third harmonic
  makes "the whole thing pick up a wobble it did not have before". The error at
  `K = 3` is not confined to the corners; the sentence is a coarse summary that
  the figure and the adjacent paragraph contradict. The student-engineer
  records this stall and accepts it as "a coarse summary"; the figure is the
  evidence that the summary is wrong. Command: Figure 1
  (`docs/blog/assets/plots/fourier-square-partial-sums.svg`, PNG at
  `/tmp/figs/plots/fourier-square-partial-sums.png`) plus the prose at lines
  13-15.
- **Repository finding, outside this page:** `blog/posts/what-is-a-signal.md:205`
  says "Untangling the two is chapters 29 to 32." The resolved table maps
  29-32 to the Ethernet compliance chapters; the optical DSP material it means
  begins at chapter 33. This is the known stale reference named in
  `gate-checks.md`, and it should go to the Editor. It is in a legacy chapter,
  not in `fourier-series-to-transform`, so it is not the page-specific reason
  for the SHUT; it is recorded because the cross-reference check surfaced it.

**Why not PASS:** the page-specific recipe defect means a reader cannot
reproduce the coefficient measurement from the prose, and the Checker may not
repair it. The figures and the arithmetic are in good shape; the sentence that
teaches the recipe is not. SHUT with these two page findings; the Producer
should send them to the Creator/Editor, then re-run the gate with a new
Checker.
