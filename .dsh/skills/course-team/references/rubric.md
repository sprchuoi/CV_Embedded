# The rubric (advisory)

The structural rules catch what a machine can catch. These six dimensions catch
what it cannot: whether the page actually teaches.

**A rubric score never fails a gate.** It is not checked by
`tool/check_page_contract.py` and it must not be added to it. It is recorded in
the transcript's `## Notes` or the QA findings so that a disagreement is about a
named dimension with an anchor, rather than a feeling about a draft. Scores are
for the author, who is allowed to disagree and say why.

Score each dimension 0–4. Anchor 2 is "this is what a competent version of this
course does"; 4 is the standard the corpus already reaches in its best chapters.

---

## 1. Intuition before formalism

*Can the reader see the thing before being asked to manipulate it?*

- **0** — A derivation with no picture. The reader who cannot follow the algebra
  has no second route.
- **2** — A figure establishes the picture, then the algebra follows it. Most
  chapters here.
- **4** — The figure *is* the argument; the algebra afterwards is bookkeeping
  the reader could almost have predicted. The sampling chapter's four-quadrant
  diagram is the reference.

## 2. Every number is computed

*Does each quantity trace to something that produces it?*

- **0** — Numbers asserted in prose, no figure and no source.
- **2** — Every number has a figure; where a figure models rather than measures,
  its caption says so.
- **4** — A reader can change an input, re-run a figure script, and watch the
  claim move. The dispersion chapter's tap-count and latency trade is the
  reference.

**A 0 here is disqualifying in practice** even though it is not machine-checked.
If you find one, raise it as a QA finding, not a rubric note.

## 3. Transfer — work and life

*Where does this touch a link that ships, and where does it touch the reader's
week?*

- **0** — No transfer, or a restatement of the chapter's importance.
- **2** — `::: try` is doable today with something the reader already has;
  `::: optical` names a real block, at rate, within power.
- **4** — The transfer changes a decision the reader will actually make — the
  decibels chapter's cache of 3 dB and 6 dB rules is the reference.

## 4. Calibrated to a post-university reader

*Assumes an adult who has forgotten the mathematics, without either flattering
or gatekeeping.*

- **0** — Assumes a course the reader has not taken, or explains what an
  integer is.
- **2** — Names its prerequisites, defines a symbol at first use, expands an
  acronym once; assumes numeracy and motivation.
- **4** — A `newcomer` transcript with no stalls *and* an `engineer` transcript
  that found the derivation honest. Both, not either.

## 5. Voice

*Sounds like this course.* See `voice.md` for the measured rules.

- **0** — `we`, exclamation marks, `obviously`, marketing register.
- **2** — Direct address, bold lead-ins, em-dash asides, no filler.
- **4** — A position taken and defended with arithmetic, and one honest caveat
  the author would rather not have needed.

## 6. The figure earns its place

*Would the chapter be worse without it, and does the caption state the takeaway?*

- **0** — Decorative, or a caption that restates the title ("Figure 3: the
  FFT").
- **2** — Each figure carries one idea, captioned with its takeaway, legible in
  dark mode, no external fonts.
- **4** — A reader could reconstruct the section from its figures alone, which
  is the test this course is built on.

---

## Using it

- Score **after** the cold read, not before. A teacher's own score is always at
  least a 2.
- Give the dimension, the score and one sentence of evidence. `3 — intuition
  arrives in section 3, but section 2 asks the reader to accept the window
  function first`.
- **Never average.** Six numbers with one 0 hiding inside a 3.5 is how a
  disqualifying page publishes. Report the lowest dimension by name.
- An `engineer` and a `newcomer` transcript disagreeing on dimension 4 is the
  expected, useful signal: it means the chapter is calibrated between them, and
  the author should decide which side to move.
