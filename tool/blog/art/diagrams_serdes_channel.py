"""Hand-authored diagrams for the SerDes channel and link-budget chapter.

    serdes-link-budget     the signal and noise terms of a serial lane on one
                           decibel axis, as a waterfall
    com-decomposition      what channel operating margin is made of, and which
                           terms an engineer can actually change
    crosstalk-environment  why lane density sets the interference, drawn as a
                           package cross-section

These three figures are the SerDes equivalent of the Ethernet loss budget, at
four to forty times the bandwidth and with crosstalk as a first-class term
rather than an afterthought.
"""

from __future__ import annotations

from . import svg as S


def serdes_link_budget() -> str:
    note = [
        "The signal term and the noise terms are separated because they are "
        "fixed by different people. The available signal is set by the "
        "transmitter's swing and the channel's loss; the noise is set by the "
        "receiver, the crosstalk environment and the reference clock. A "
        "budget that mixes them cannot tell you whose problem a shortfall is.",
        "The margin line at the bottom is the pass/fail boundary, and it is "
        "why the arithmetic exists. Everything above it is margin; everything "
        "below it is a link that will fail intermittently and expensively.",
    ]
    c = S.Canvas(880, int(500 + S.callout_height(808, note, body_size=11.5) + 14),
                 title="A serial lane's budget: signal above, noise below")

    left, right = 118, 806
    base, top = 322, 92
    lo, hi = -40.0, 6.0

    def py(db):
        return base - (db - lo) / (hi - lo) * (base - top)

    for db in (0, -10, -20, -30, -40):
        y = py(db)
        c.add(S.line(left - 6, y, right, y, stroke=S.RULE_SOFT, width=1),
              S.text(left - 12, y, f"{db}", size=9.5, fill=S.MUTED,
                     anchor="end", family=S.MONO))
    c.add(S.text(left - 12, 74, "dB", size=10, fill=S.MUTED, anchor="end",
                 weight=700))

    # signal terms: a descending staircase
    signal = [
        ("TX swing", 0.0, S.NOTE),
        ("channel loss\nat Nyquist", -26.0, S.WARN),
        ("package +\nconnector", -29.5, S.WARN),
        ("TX FFE\nde-emphasis", -33.0, S.WARN),
        ("after RX\nequalisation", -13.0, S.ACCENT),
    ]
    step = (right - left) / len(signal)
    prev = None
    for i, (label, level, colour) in enumerate(signal):
        x = left + i * step
        if prev is not None:
            c.add(S.rect(x, py(max(prev, level)), step * 0.6,
                         abs(py(level) - py(prev)), fill=colour, stroke=None,
                         rx=3, opacity=0.30),
                  S.text(x + step * 0.3,
                         py((prev + level) / 2) + (0 if level > prev else 0),
                         f"{level - prev:+.1f}", size=9.5, fill=colour,
                         anchor="middle", weight=700, family=S.MONO))
        c.add(S.line(x, py(level), x + step * 0.6, py(level), stroke=colour,
                     width=2.4),
              S.dot(x + step * 0.3, py(level), r=4.4, fill=colour))
        for j, line in enumerate(label.split("\n")):
            c.add(S.text(x + step * 0.3, base + 20 + j * 13, line, size=9.5,
                         fill=colour if j == 0 else S.MUTED, anchor="middle",
                         weight=700 if j == 0 else 400))
        prev = level

    # the noise floor, as a band at the bottom of the equaliser's output
    nf = -31.0
    c.add(S.rect(left, py(nf), right - left, 12, fill=S.OPTICAL, stroke=None,
                 rx=3, opacity=0.25),
          S.text(left, py(nf) - 14, "noise: receiver, crosstalk, reference "
                 "clock", size=10, fill=S.OPTICAL_DARK, weight=700))

    margin = -13.0 - nf
    c.add(S.line(right + 6, py(-13.0), right + 6, py(nf), stroke=S.ACCENT,
                 width=2.4),
          S.line(right, py(-13.0), right + 12, py(-13.0), stroke=S.ACCENT,
                 width=1.6),
          S.line(right, py(nf), right + 12, py(nf), stroke=S.ACCENT, width=1.6),
          S.text(right + 20, py((-13.0 + nf) / 2), f"margin\n{margin:+.1f} dB",
                 size=10.5, fill=S.ACCENT_DARK, weight=700))

    c.add(S.text(left, 62, "all terms at the Nyquist frequency; the equaliser "
                 "gain is shown net of its own noise enhancement",
                 size=9.5, fill=S.MUTED))

    c.add(S.callout(36, 402, 808, "Reading the waterfall", note, kind="accent"))
    return c.render()


def com_decomposition() -> str:
    note = [
        "Channel operating margin collapses a long list of impairments into "
        "one number: the ratio of available signal to total noise at the "
        "slicer, after a reference equaliser, minus the signal-to-noise ratio "
        "the target error ratio needs. Above 3 dB the channel passes; below "
        "it, the channel is the problem.",
        "The useful part is the decomposition. When a channel fails COM, the "
        "figure tells you whether to change the board (loss, crosstalk) or "
        "the silicon (equaliser taps, noise). Those are different teams, and "
        "COM is often the only shared language they have.",
    ]
    c = S.Canvas(880, int(508 + S.callout_height(808, note, body_size=11.5) + 14),
                 title="What channel operating margin is made of")

    # numerator box
    c.add(S.rect(48, 92, 372, 132, fill=S.ACCENT_WASH, stroke=S.ACCENT, rx=8,
                 width=1.4),
          S.text(234, 116, "available signal", size=12.5, fill=S.ACCENT_DARK,
                 anchor="middle", weight=700))
    num_in = [
        "TX differential swing",
        "minus channel insertion loss at Nyquist",
        "minus package and connector loss",
        "minus TX FFE de-emphasis",
        "after the reference RX equaliser",
    ]
    for i, item in enumerate(num_in):
        c.add(S.text(68, 142 + i * 17, "\u2022  " + item, size=10,
                     fill=S.SOFT))

    # denominator box
    c.add(S.rect(460, 92, 372, 132, fill=S.OPTICAL_WASH, stroke=S.OPTICAL,
                 rx=8, width=1.4),
          S.text(646, 116, "total noise at the slicer", size=12.5,
                 fill=S.OPTICAL_DARK, anchor="middle", weight=700))
    den_in = [
        "receiver noise, referred to the slicer",
        "crosstalk: NEXT, FEXT, ICN",
        "reflections from return loss",
        "jitter converted to an amplitude penalty",
        "equaliser noise enhancement",
    ]
    for i, item in enumerate(den_in):
        c.add(S.text(480, 142 + i * 17, "\u2022  " + item, size=10,
                     fill=S.SOFT))

    # the equation
    c.add(S.text(440, 258, "COM  =  20 log\u2081\u2080 ( signal / noise )  "
                 "\u2212  required SNR", size=13, fill=S.INK,
                 anchor="middle", weight=700))
    c.add(S.line(240, 276, 640, 276, stroke=S.RULE, width=1.2))

    # the three thresholds
    bands = [
        ("fails", "< 0 dB", S.WARN, "the channel, not the silicon"),
        ("marginal", "0 - 3 dB", S.NOTE, "sensitive to temperature and corners"),
        ("passes", "> 3 dB", S.ACCENT, "margin for age and environment"),
    ]
    bw = 244
    for i, (name, rng, colour, comment) in enumerate(bands):
        bx = 48 + i * (bw + 22)
        c.add(S.rect(bx, 300, bw, 76, fill=S.PANEL, stroke=colour, rx=8,
                     width=1.6),
              S.text(bx + bw / 2, 324, name, size=12, fill=colour,
                     anchor="middle", weight=700),
              S.text(bx + bw / 2, 346, rng, size=11, fill=S.INK,
                     anchor="middle", family=S.MONO),
              S.text(bx + bw / 2, 364, comment, size=9.5, fill=S.MUTED,
                     anchor="middle"))

    c.add(S.callout(36, 404, 808, "The number and its decomposition", note,
                    kind="accent"))
    return c.render()


def crosstalk_environment() -> str:
    note = [
        "Every adjacent lane is a noise source. The coupling is capacitive "
        "and inductive between traces, and electromagnetic between the "
        "connector pins and the package vias, and it rises with frequency "
        "because the coupling impedance falls.",
        "This is why lane density is a signal-integrity decision, not a "
        "layout convenience. Doubling the number of lanes in the same width "
        "halves the spacing and can cost several decibels of margin, which "
        "is why high-density modules spend on shielding, on ground vias, and "
        "on differential routing discipline.",
    ]
    c = S.Canvas(880, int(474 + S.callout_height(808, note, body_size=11.5) + 14),
                 title="Why lane density sets the noise floor")

    # two cross-sections: a sparse and a dense package escape
    for panel, (x0, title, pitch, colour) in enumerate((
            (70, "wide pitch: -35 dB coupling", 78, S.ACCENT),
            (470, "half the pitch: -22 dB coupling", 42, S.WARN))):
        y0 = 108
        c.add(S.text(x0, y0 - 18, title, size=11, fill=colour, weight=700))
        for lane in range(5):
            lx = x0 + lane * pitch
            # the aggressor pair
            aggressor = lane in (0, 4)
            fill = S.WARN_WASH if aggressor else S.ACCENT_WASH
            stroke = S.WARN if aggressor else S.ACCENT
            c.add(S.rect(lx, y0, pitch * 0.42, 26, fill=fill, stroke=stroke,
                         rx=3, width=1.2),
                  S.rect(lx, y0 + 34, pitch * 0.42, 26, fill=fill,
                         stroke=stroke, rx=3, width=1.2))
        # the victim, in the middle
        vx = x0 + 2 * pitch
        c.add(S.text(vx + pitch * 0.21, y0 + 76, "victim lane", size=9.5,
                     fill=S.INK, anchor="middle", weight=600))
        # coupling arcs from the aggressors to the victim
        for lane in (0, 4):
            ax = x0 + lane * pitch + pitch * 0.21
            c.add(S.path(f"M {ax} {y0 + 60} Q {(ax + vx + pitch * 0.21) / 2} "
                         f"{y0 + 110} {vx + pitch * 0.21} {y0 + 60}",
                         stroke=S.WARN, width=1.4, dash="4 3", fill="none"))
        c.add(S.text(x0, y0 + 128, "aggressors shown in amber", size=9.5,
                     fill=S.MUTED, style="italic"))

    # the coupling against pitch, schematically
    c.add(S.rect(70, 300, 762, 24, fill=S.RULE_SOFT, stroke=None, rx=3))
    for i, (db, frac) in enumerate((("-22 dB", 0.78), ("-28 dB", 0.5),
                                    ("-35 dB", 0.28))):
        bx = 78 + i * 254
        c.add(S.rect(bx, 302, 244 * frac, 20, fill=S.WARN, stroke=None, rx=3,
                     opacity=0.35),
              S.text(bx + 4, 318, f"coupling {db}", size=9.5,
                     fill=S.WARN, weight=700))
    c.add(S.text(70, 344, "coupling falls roughly with the square of the "
                 "spacing, and rises with frequency", size=10, fill=S.SOFT))

    c.add(S.callout(36, 372, 808, "The layout decision that becomes a link "
                    "budget term", note, kind="warn"))
    return c.render()


FIGURES = {
    "serdes-link-budget": serdes_link_budget,
    "com-decomposition": com_decomposition,
    "crosstalk-environment": crosstalk_environment,
}
