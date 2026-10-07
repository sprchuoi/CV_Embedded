"""Hand-authored diagrams for the compliance-test chapter.

    compliance-test-setup   the bench, drawn honestly: where the probes go, what
                            the fixture does, and what has to be calibrated
    compliance-failure-modes  the four ways to get a wrong answer from a
                            correct instrument
    ethernet-part-map       every chapter of this part, and how they connect

The map is the chapter's real deliverable: a reader who has finished the part
should be able to point at any symptom and say which chapter diagnoses it.
"""

from __future__ import annotations

from . import svg as S


def compliance_test_setup() -> str:
    note = [
        "The fixture is not an accessory, it is part of the measurement. Its "
        "loss and its impedance are de-embedded from the result, and if you "
        "cannot de-embed it you cannot claim the number.",
        "The pattern generator must be the one the standard names, the "
        "termination must be the one the standard names, and the link must be "
        "in the state the standard names -- training complete, FEC locked, "
        "equaliser converged. A compliance run is only meaningful at "
        "steady state.",
    ]
    c = S.Canvas(880, int(470 + S.callout_height(808, note, body_size=11.5) + 14),
                 title="A compliance bench, and what each block is for")

    blocks = [
        ("Pattern gen", "PRBS as specified", "note"),
        ("DUT", "port under test,\ntrained and locked", "accent"),
        ("Fixture", "de-embedded loss,\ncontrolled impedance", "warn"),
        ("Scope", "> 2x baud analogue\nbandwidth", "plain"),
        ("Analysis", "mask, eye, jitter,\nBER extrapolation", "optical"),
    ]
    box_w, gap, by, bh = 152, 22, 150, 108
    x0 = (880 - (len(blocks) * box_w + (len(blocks) - 1) * gap)) / 2
    centres = []
    for i, (title, sub, kind) in enumerate(blocks):
        bx = x0 + i * (box_w + gap)
        centres.append(bx + box_w / 2)
        # block() centres the title; the body lines hang below that centre.
        c.add(S.block(bx, by, box_w, bh, title.split("\n")[0], kind=kind,
                      title_size=11.5))
        for j, line in enumerate(sub.split("\n")):
            c.add(S.text(bx + box_w / 2, by + bh / 2 + 26 + j * 14, line,
                         size=9.5, fill=S.SOFT, anchor="middle"))
        if i < len(blocks) - 1:
            c.add(S.arrow(bx + box_w + 2, by + bh / 2, bx + box_w + gap - 2,
                          by + bh / 2, stroke=S.MUTED, width=1.5))

    # the probe: a tap between the fixture and the scope, drawn as a branch
    tap_x = centres[3]
    c.add(S.arrow_path([(tap_x, by + bh), (tap_x, by + bh + 40),
                        (centres[4], by + bh + 40), (centres[4], by + bh)],
                       stroke=S.OPTICAL, width=1.5),
          S.text(tap_x - 12, by + bh + 34, "probe here, at the DUT's own "
                 "reference plane", size=10, fill=S.OPTICAL_DARK,
                 anchor="end", weight=600))

    # the four calibration facts, as a row of checks
    checks = [
        ("probe de-embedding", "the probe loads the line"),
        ("fixture loss", "subtracted, in dB, at Nyquist"),
        ("reference plane", "moved by the de-embedding"),
        ("steady state", "trained, locked, converged"),
    ]
    cw = 190
    for i, (title, sub) in enumerate(checks):
        cx = 40 + i * 204
        c.add(S.rect(cx, 324, cw, 62, fill=S.ACCENT_WASH, stroke=S.ACCENT,
                     rx=6, width=1.2),
              S.text(cx + cw / 2, 346, title, size=10.5, fill=S.ACCENT_DARK,
                     anchor="middle", weight=700),
              S.text(cx + cw / 2, 366, sub, size=9.5, fill=S.SOFT,
                     anchor="middle"))

    c.add(S.callout(36, 402, 808, "What makes a number defensible", note,
                    kind="accent"))
    return c.render()


def compliance_failure_modes() -> str:
    note = [
        "None of these is an instrument fault. Each is a correct instrument "
        "answering a slightly different question than the standard asked, "
        "and each produces a number that looks entirely reasonable.",
        "The defence is procedural: state the reference plane, state the "
        "pattern, state the equaliser state, and record the fixture's "
        "de-embedding alongside the result. A margin with no provenance is "
        "not a margin.",
    ]
    c = S.Canvas(880, int(492 + S.callout_height(808, note, body_size=11.5) + 14),
                 title="Four ways to get the wrong answer with a good scope")

    modes = [
        ("1. Wrong reference plane",
         "Probing at the fixture output instead of the DUT's own pins moves "
         "the plane by the fixture's loss and its stub.",
         "the eye looks better or worse by several dB, consistently"),
        ("2. Unequalised measurement",
         "Measuring before the link's own equaliser has converged - or with "
         "the receiver's DFE switched off - reports the channel, not the link.",
         "the eye is closed where the product's is open"),
        ("3. Too little analogue bandwidth",
         "A scope at less than twice the baud rate removes the high-frequency "
         "content that the mask exists to constrain.",
         "jitter and rise time are flattered, the mask passes"),
        ("4. Pattern mismatch",
         "Running PRBS7 where the standard specifies PRBS31 skips the long "
         "runs that stress baseline wander and AC coupling.",
         "a clean result on a link that fails in the field"),
    ]

    y0, dy = 96, 92
    for i, (title, body, symptom) in enumerate(modes):
        y = y0 + i * dy
        c.add(S.rect(40, y, 800, 76, fill=S.WARN_WASH if i % 2 == 0 else S.PANEL,
                     stroke=S.WARN, rx=6, width=1.2),
              S.dot(60, y + 22, r=5, fill=S.WARN),
              S.text(76, y + 22, title, size=11.5, fill=S.WARN, weight=700))
        # wrap the body by hand to two lines at ~92 chars
        words, line, lines = body.split(), "", []
        for w in words:
            if len(line) + len(w) + 1 <= 96:
                line = f"{line} {w}".strip()
            else:
                lines.append(line)
                line = w
        lines.append(line)
        for j, entry in enumerate(lines[:2]):
            c.add(S.text(76, y + 43 + j * 14, entry, size=9.5, fill=S.SOFT))
        c.add(S.text(76, y + 66, "symptom: " + symptom, size=9.5,
                     fill=S.MUTED, style="italic"))

    c.add(S.callout(36, 468, 808, "The common thread", note, kind="warn"))
    return c.render()


def ethernet_part_map() -> str:
    note = [
        "Read it as a diagnostic: a symptom names a chapter. An eye that will "
        "not open? The eye chapter. Post-FEC errors? The BERT chapter, then "
        "the budget. A spectral-mask failure? The DFT chapter.",
        "The two arrows out of the part are the point of it. Every Ethernet "
        "chapter ends in the same place -- a coherent optical receiver runs "
        "the same four steps at a higher baud rate, and the DSP it uses is "
        "the DSP this course has been building since chapter one.",
    ]
    c = S.Canvas(880, int(546 + S.callout_height(808, note, body_size=11.5) + 14),
                 title="The Ethernet part, and where it connects")

    # the spine: the four-step processing view, reused as the organising idea
    spine_y = 122
    steps = ["Prepare", "Cross", "Recover", "Decide"]
    box_w, gap = 176, 32
    x0 = (880 - (len(steps) * box_w + (len(steps) - 1) * gap)) / 2
    for i, name in enumerate(steps):
        bx = x0 + i * (box_w + gap)
        c.add(S.block(bx, spine_y, box_w, 62, name, kind="plain",
                      title_size=12.5))
        if i < len(steps) - 1:
            c.add(S.arrow(bx + box_w + 3, spine_y + 31, bx + box_w + gap - 3,
                          spine_y + 31, stroke=S.MUTED, width=1.5))

    # the chapters, mapped under the step they belong to
    chapters = [
        (0, "Generations", "six generations, four steps"),
        (1, "Gain and budget", "loss in dB at Nyquist"),
        (2, "Eye diagram", "height, width, mask"),
        (2, "BERT and FEC", "BER, bathtub, contract"),
        (3, "FFT and DFT", "spectra, masks, S-params"),
        (3, "Compliance test", "the procedure, and its traps"),
    ]
    row_y = 236
    per_col = {}
    for col, title, sub in chapters:
        n = per_col.get(col, 0)
        per_col[col] = n + 1
        bx = x0 + col * (box_w + gap)
        by = row_y + n * 66
        c.add(S.rect(bx, by, box_w, 52, fill=S.ACCENT_WASH, stroke=S.ACCENT,
                     rx=6, width=1.2),
              S.text(bx + box_w / 2, by + 18, title, size=10.5,
                     fill=S.ACCENT_DARK, anchor="middle", weight=700),
              S.text(bx + box_w / 2, by + 36, sub, size=9, fill=S.SOFT,
                     anchor="middle"))
        c.add(S.line(bx + box_w / 2, spine_y + 62, bx + box_w / 2, by,
                     stroke=S.RULE, width=1.2, dash="3 3"))

    # the two exits, parked at different heights so their captions cannot meet
    exit_y = row_y + 2 * 66 + 6
    c.add(S.arrow_path([(x0 + box_w / 2, exit_y), (x0 + box_w / 2, exit_y + 30)],
                       stroke=S.OPTICAL, width=1.8),
          S.text(x0 + box_w / 2 + 14, exit_y + 30,
                 "the same four steps, 100+ GBd, coherent optical "
                 "(the optical part)", size=10, fill=S.OPTICAL_DARK,
                 weight=600))
    right_x = x0 + 3 * (box_w + gap) + box_w / 2
    c.add(S.arrow_path([(right_x, exit_y), (right_x, exit_y + 62)],
                       stroke=S.NOTE, width=1.8),
          S.text(right_x - 14, exit_y + 62,
                 "the DSP fundamentals behind each step "
                 "(parts one to six)", size=10, fill=S.NOTE_DARK,
                 anchor="end", weight=600))

    c.add(S.callout(36, 522, 808, "How to use this map", note, kind="optical"))
    return c.render()


FIGURES = {
    "compliance-test-setup": compliance_test_setup,
    "compliance-failure-modes": compliance_failure_modes,
    "ethernet-part-map": ethernet_part_map,
}
