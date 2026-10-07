"""Hand-authored diagrams for the clock-recovery and jitter chapter.

    cdr-loop             the phase detector, loop filter and phase interpolator,
                         and what each one costs
    jitter-decomposition  total jitter split into its random and deterministic
                          parts, and why the split is the useful measurement

The chapter is about the one loop in a SerDes that has no equivalent in the
optical DSP chain, and about the measurement that decides how much eye is left
after everything else has been accounted for.
"""

from __future__ import annotations

from . import svg as S


def cdr_loop() -> str:
    note = [
        "The phase detector compares the sampling clock against the data "
        "transitions. A bang-bang detector asks only whether the sample was "
        "early or late and produces a one-bit answer; a Mueller-Muller "
        "detector uses the samples themselves and produces a proportional "
        "one. The first is cheaper and noisier, the second needs decisions "
        "and is smoother.",
        "The loop filter sets the bandwidth, and the bandwidth is a genuine "
        "trade rather than a tuning knob. Wide tracks the transmitter's "
        "wander and passes more jitter through; narrow filters the incoming "
        "jitter and cannot follow a drifting clock. Every SerDes datasheet "
        "quotes a loop bandwidth for exactly this reason.",
    ]
    c = S.Canvas(880, int(508 + S.callout_height(808, note, body_size=11.5) + 14),
                 title="A clock and data recovery loop")

    blocks = [
        (48, "Phase\ndetector", "early / late\nor proportional", "note"),
        (238, "Loop\nfilter", "sets the\nbandwidth", "accent"),
        (428, "Phase\ninterpolator", "selects a phase\nfrom the VCO", "warn"),
        (618, "Sampler", "the recovered\nclock", "plain"),
    ]
    bw, gap, by, bh = 166, 24, 138, 100
    for x, title, sub, kind in blocks:
        c.add(S.block(x, by, bw, bh, title.replace("\n", " "), kind=kind,
                      title_size=11.5))
        for j, line in enumerate(sub.split("\n")):
            c.add(S.text(x + bw / 2, by + bh / 2 + 26 + j * 14, line,
                         size=9.5, fill=S.SOFT, anchor="middle"))
        if x < 618:
            c.add(S.arrow(x + bw + 2, by + bh / 2, x + bw + gap - 2,
                          by + bh / 2, stroke=S.MUTED, width=1.5))

    # the feedback: sampler output back to the phase detector
    fb_y = by + bh + 66
    c.add(S.arrow_path([(618 + bw / 2, by + bh), (618 + bw / 2, fb_y),
                        (48 + bw / 2, fb_y), (48 + bw / 2, by + bh)],
                       stroke=S.OPTICAL, width=1.6),
          S.text((48 + 618 + bw) / 2, fb_y + 18, "the recovered data, whose "
                 "transitions are the phase reference", size=10,
                 fill=S.OPTICAL_DARK, anchor="middle", weight=600))

    # reference clock
    c.add(S.arrow(300, 92, 300, by - 4, stroke=S.MUTED, width=1.4),
          S.text(300, 80, "reference clock", size=9.5, fill=S.MUTED,
                 anchor="middle"))

    # the two detector choices
    cards = [
        ("Bang-bang (Alexander)", "one bit per transition",
         "cheap, robust, quantisation noise", S.NOTE),
        ("Mueller-Muller", "proportional to the error",
         "smoother, needs reliable decisions", S.ACCENT),
    ]
    for i, (name, what, comment, colour) in enumerate(cards):
        bx = 48 + i * 412
        c.add(S.rect(bx, 348, 380, 86, fill=S.PANEL, stroke=colour, rx=8,
                     width=1.4),
              S.text(bx + 190, 372, name, size=11.5, fill=colour,
                     anchor="middle", weight=700),
              S.text(bx + 190, 394, what, size=10, fill=S.INK,
                     anchor="middle"),
              S.text(bx + 190, 416, comment, size=9.5, fill=S.MUTED,
                     anchor="middle"))

    c.add(S.callout(36, 456, 808, "Bandwidth is a trade, not a setting", note,
                    kind="accent"))
    return c.render()


def jitter_decomposition() -> str:
    note = [
        "Total jitter is the number a mask test compares against a limit. It "
        "is also the least useful number, because it mixes two things that "
        "behave differently: random jitter, which is unbounded and grows "
        "with the observation time, and deterministic jitter, which is "
        "bounded and does not.",
        "The split is what makes a measurement actionable. Random jitter is "
        "thermal and shot noise in the clock path; deterministic jitter is "
        "ISI, duty-cycle distortion, power-supply coupling and crosstalk. One "
        "improves with a quieter reference; the other needs a board change.",
    ]
    c = S.Canvas(880, int(516 + S.callout_height(808, note, body_size=11.5) + 14),
                 title="Total jitter, and the two things inside it")

    # left: the histogram with the two components
    x0, x1 = 84, 470
    base, top = 300, 110
    cx = (x0 + x1) / 2
    c.add(S.text(x0, 88, "jitter histogram at the crossing", size=11,
                 fill=S.INK, weight=700))
    c.add(S.line(x0, base, x1, base, stroke=S.INK, width=1.5),
          S.text(cx, base + 22, "time relative to the nominal crossing", size=9.5,
                 fill=S.MUTED, anchor="middle"))

    # two Gaussian lobes separated by deterministic jitter
    import math
    for sign, colour, label in ((-1, S.WARN, "DJ: ISI, DCD, crosstalk"),
                                (1, S.WARN, None)):
        mu = cx + sign * 26
        pts = []
        for i in range(121):
            t = -3.2 + i / 120 * 6.4
            x = mu + t * 22
            y = base - math.exp(-0.5 * t * t) * 150
            pts.append((x, y))
        c.add(S.polyline(pts, stroke=colour, width=2.2))
    # the random component, as the width of one lobe
    c.add(S.line(cx - 26 - 22, base - 40, cx - 26 + 22, base - 40,
                 stroke=S.NOTE, width=2),
          S.text(cx - 26, base - 52, "RJ", size=10.5, fill=S.NOTE,
                 anchor="middle", weight=700),
          S.line(cx - 26, base - 46, cx - 26, base - 34, stroke=S.NOTE,
                 width=1.2),
          S.line(cx + 22, base - 46, cx + 22, base - 34, stroke=S.NOTE,
                 width=1.2))
    c.add(S.line(cx - 26, base - 12, cx + 26, base - 12, stroke=S.WARN,
                 width=2),
          S.line(cx - 26, base - 18, cx - 26, base - 6, stroke=S.WARN,
                 width=1.2),
          S.line(cx + 26, base - 18, cx + 26, base - 6, stroke=S.WARN,
                 width=1.2),
          S.text(cx, base - 26, "DJ", size=10.5, fill=S.WARN,
                 anchor="middle", weight=700))

    # right: the growth law
    rx0, rx1 = 530, 844
    rbase, rtop = 300, 116
    c.add(S.text(rx0, 88, "TJ against the number of samples observed", size=11,
                 fill=S.INK, weight=700))
    c.add(S.axis(rx0, rbase, rx1, rtop, xlabel="log\u2081\u2080 (samples)",
                 xticks=[(rx0, "6"), ((rx0 + rx1) / 2, "9"), (rx1, "12")],
                 yticks=[(rbase, "0"), (rtop, "1")]))
    # DJ: a constant; RJ: growing as sqrt of the observation
    import math as _m
    dj, rj = [], []
    for i in range(61):
        u = i / 60
        x = rx0 + u * (rx1 - rx0)
        dj.append((x, rbase - 0.34 * (rbase - rtop)))
        rj.append((x, rbase - (0.20 + 0.72 * _m.sqrt(u)) * (rbase - rtop)))
    c.add(S.polyline(dj, stroke=S.WARN, width=2.4),
          S.polyline(rj, stroke=S.NOTE, width=2.4),
          # Labels parked clear of their own curves: a caption sitting on the
          # line it names is the most common way a figure lies.
          S.text(rx1 - 6, rbase - 0.42 * (rbase - rtop),
                 "deterministic: bounded", size=9.5, fill=S.WARN,
                 anchor="end", weight=600),
          S.text(rx0 + 10, rbase - 0.52 * (rbase - rtop),
                 "random: unbounded", size=9.5, fill=S.NOTE, weight=600))

    c.add(S.text(x0, 358, "Dual-Dirac model: TJ = DJ + 2 \u00b7 Q \u00b7 RJ, "
                 "with Q \u2248 7.03 for a 10\u207b\u00b9\u00b2 target",
                 size=11, fill=S.INK, weight=600))

    c.add(S.callout(36, 400, 808, "Why the decomposition is the deliverable",
                    note, kind="accent"))
    return c.render()


FIGURES = {
    "cdr-loop": cdr_loop,
    "jitter-decomposition": jitter_decomposition,
}
