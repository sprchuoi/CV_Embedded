"""Hand-authored diagrams for the SerDes equalisation chapter.

    serdes-equaliser-types   the four equalisers, their shapes, and the cost
                             each one pays
    dfe-principle            why a decision-feedback equaliser is exact and why
                             it is dangerous
    equaliser-adaptation     the sign-sign LMS loop, and where its error signal
                             comes from

The chapter's argument is that a real lane uses all four equalisers at once,
because each one is cheap in a different currency: the CTLE in power, the FFE
in precision, the DFE in latency, and the transmit FFE in launch amplitude.
"""

from __future__ import annotations

from . import svg as S


def serdes_equaliser_types() -> str:
    note = [
        "The four equalisers are not alternatives. A 100G lane typically has "
        "a CTLE with a few decibels of peaking, a transmit FFE with three to "
        "five taps, a receive FFE of similar length, and a DFE with five to "
        "fifteen taps. Each one is cheap in a currency the others are "
        "expensive in.",
        "The ordering matters too. The CTLE runs before the ADC, so it must "
        "be cheap and it cannot be perfect. The FFE runs after the ADC, so it "
        "can be precise. The DFE runs at the decision, so it can be exact -- "
        "and it is the only one that can remove post-cursor ISI without "
        "amplifying noise.",
    ]
    c = S.Canvas(880, int(514 + S.callout_height(808, note, body_size=11.5) + 14),
                 title="Four equalisers, four currencies")

    cards = [
        ("CTLE", "continuous-time\nlinear equaliser", "analogue peaking",
         "costs power and\nadds noise", "warn"),
        ("TX FFE", "transmit\nfeed-forward", "pre-distortion",
         "costs launch\namplitude", "note"),
        ("RX FFE", "receive\nfeed-forward", "linear, precise",
         "amplifies noise\nwith the signal", "accent"),
        ("DFE", "decision-feedback", "post-cursor, exact",
         "costs latency;\ncan propagate errors", "optical"),
    ]
    bw, gap, by, bh = 194, 22, 108, 148
    x0 = (880 - (len(cards) * bw + (len(cards) - 1) * gap)) / 2
    for i, (name, full, what, cost, kind) in enumerate(cards):
        bx = x0 + i * (bw + gap)
        fill, stroke, ink = S._kind(kind)
        c.add(S.rect(bx, by, bw, bh, fill=fill, stroke=stroke, rx=8, width=1.4),
              S.text(bx + bw / 2, by + 26, name, size=14, fill=ink,
                     anchor="middle", weight=700))
        for j, line in enumerate(full.split("\n")):
            c.add(S.text(bx + bw / 2, by + 48 + j * 14, line, size=9.5,
                         fill=S.SOFT, anchor="middle"))
        c.add(S.line(bx + 20, by + 80, bx + bw - 20, by + 80, stroke=stroke,
                     width=1),
              S.text(bx + bw / 2, by + 98, what, size=10.5, fill=ink,
                     anchor="middle", weight=600),
              S.text(bx + bw / 2, by + 124, cost, size=9.5, fill=S.MUTED,
                     anchor="middle"))

    # where each sits in the chain
    chain_y = 296
    c.add(S.text(48, chain_y - 16, "where each one sits in the receive chain",
                 size=10.5, fill=S.MUTED, weight=600))
    order = ["channel", "CTLE", "ADC", "RX FFE", "DFE", "slicer"]
    ow, og = 124, 14
    ox = 48
    for i, name in enumerate(order):
        c.add(S.rect(ox, chain_y, ow, 40, fill=S.PANEL, stroke=S.RULE, rx=6,
                     width=1.1),
              S.text(ox + ow / 2, chain_y + 20, name, size=10.5, fill=S.INK,
                     anchor="middle", weight=600))
        if i < len(order) - 1:
            c.add(S.arrow(ox + ow + 1, chain_y + 20, ox + ow + og - 1,
                          chain_y + 20, stroke=S.MUTED, width=1.3))
        ox += ow + og

    # TX FFE, shown before the channel
    c.add(S.text(48, chain_y + 62, "TX FFE sits before the channel, at the "
                 "other end of the link", size=10, fill=S.NOTE_DARK,
                 weight=600))

    c.add(S.callout(36, 410, 808, "Why all four, and not the best one", note,
                    kind="accent"))
    return c.render()


def dfe_principle() -> str:
    note = [
        "A DFE subtracts a weighted sum of the bits it has already decided "
        "from the signal it is about to decide. Because those bits are known "
        "exactly -- they are digital -- the subtraction is exact, and no "
        "noise is amplified in the process. This is the one trick that beats "
        "a linear equaliser.",
        "The catch is that a wrong decision feeds back as a wrong "
        "subtraction, so one error can cause the next. That is error "
        "propagation, and it is why a DFE's output has bursty errors rather "
        "than independent ones -- which matters enormously to the FEC that "
        "has to repair them.",
    ]
    c = S.Canvas(880, int(500 + S.callout_height(808, note, body_size=11.5) + 14),
                 title="Decision feedback: exact, and dangerous")

    # a pulse response with a post-cursor
    x0, x1 = 96, 620
    base = 250
    c.add(S.text(x0, 84, "pulse response at the slicer, in units of the main "
                 "cursor", size=10.5, fill=S.MUTED))

    taps = {0: 1.0, 1: 0.34, 2: 0.16, 3: 0.08, 4: 0.04}
    step = (x1 - x0) / 7
    def py(v):
        return base - v * 120
    for k in range(7):
        v = taps.get(k, 0.0)
        x = x0 + k * step
        colour = S.ACCENT if k == 0 else (S.WARN if v > 0 else S.MUTED)
        c.add(S.line(x, base, x, py(v), stroke=colour, width=3),
              S.dot(x, py(v), r=4.5, fill=colour),
              S.text(x, base + 18, f"h[{k}]", size=9.5, fill=S.MUTED,
                     anchor="middle", family=S.MONO))
        if v:
            c.add(S.text(x, py(v) - 14, f"{v:.2f}", size=9.5, fill=colour,
                         anchor="middle", family=S.MONO))
    c.add(S.line(x0 - 20, base, x1 + 20, base, stroke=S.RULE, width=1.2))
    c.add(S.rect(x0 + step * 0.5, py(0.42), step * 6, py(0.34) - py(0.42),
                 fill=S.WARN, stroke=None, rx=4, opacity=0.18),
          S.text(x0 + step * 3.5, py(0.42) + 14, "post-cursor ISI: what the "
                 "DFE subtracts", size=10, fill=S.WARN, anchor="middle",
                 weight=600))

    # the loop, as a small block diagram
    lx, ly = 660, 120
    c.add(S.block(lx, ly, 180, 56, "slicer", kind="optical", title_size=11.5),
          S.block(lx, ly + 96, 180, 56, "feedback filter", kind="accent",
                  title_size=11.5),
          S.arrow(lx + 90, ly + 56, lx + 90, ly + 92, stroke=S.INK, width=1.5),
          S.arrow_path([(lx - 4, ly + 124), (lx - 30, ly + 124),
                        (lx - 30, ly + 28), (lx - 4, ly + 28)],
                       stroke=S.ACCENT, width=1.5),
          S.text(lx - 36, ly + 78, "subtract", size=9.5, fill=S.ACCENT_DARK,
                 anchor="end", weight=600),
          S.text(lx + 90, ly + 172, "taps weighted by the decided bits",
                 size=9.5, fill=S.MUTED, anchor="middle"))

    c.add(S.callout(36, 360, 808, "The trade, in one line", note, kind="optical"))
    return c.render()


def equaliser_adaptation() -> str:
    note = [
        "Every equaliser in the chain has coefficients, and every coefficient "
        "has to be set. Some are set once at bring-up from a training "
        "exchange; some adapt continuously from the slicer's own error. The "
        "loop that does the adapting is almost always a sign-sign LMS, "
        "because at 50 gigabaud a multiplier per tap per sample is not "
        "affordable and a comparator is.",
        "The error signal is the whole design. Before the link is trained "
        "there are no reliable decisions, so adaptation runs on a known "
        "pattern; after training it runs on the slicer's own output, which "
        "means a wrong decision corrupts the adaptation for a moment. That is "
        "why adaptation bandwidth is a stability parameter, not a speed "
        "parameter.",
    ]
    c = S.Canvas(880, int(500 + S.callout_height(808, note, body_size=11.5) + 14),
                 title="How the taps get their values")

    # the loop
    blocks = [
        (48, "sampler", "y[n]", "plain"),
        (218, "slicer", "\\u0177[n]", "optical"),
        (388, "error", "e[n] = \\u0177 \\u2212 y", "warn"),
        (588, "tap update", "w[n+1] = w[n] + \\u00b5 e x", "accent"),
    ]
    by, bh = 132, 76
    for x, title, sub, kind in blocks:
        c.add(S.block(x, by, 158, bh, title, kind=kind, title_size=11.5))
        c.add(S.text(x + 79, by + 48, sub, size=9.5, fill=S.SOFT,
                     anchor="middle", family=S.MONO))
        if x < 588:
            c.add(S.arrow(x + 160, by + bh / 2, x + 196, by + bh / 2,
                          stroke=S.MUTED, width=1.5))

    c.add(S.arrow_path([(666, by + bh), (666, by + bh + 54), (127, by + bh + 54),
                        (127, by + bh)], stroke=S.ACCENT, width=1.6),
          S.text(396, by + bh + 72, "the corrected signal, and the taps that "
                 "produced it", size=10, fill=S.ACCENT_DARK, anchor="middle",
                 weight=600))

    # the sign-sign reduction
    c.add(S.rect(48, 336, 380, 96, fill=S.NOTE_WASH, stroke=S.NOTE, rx=8,
                 width=1.2),
          S.text(238, 360, "LMS, then sign-sign LMS", size=11.5,
                 fill=S.NOTE_DARK, anchor="middle", weight=700),
          S.text(66, 384, "w[n+1] = w[n] + \u00b5 \u00b7 e[n] \u00b7 x[n]",
                 size=10.5, fill=S.INK, family=S.MONO),
          S.text(66, 404, "w[n+1] = w[n] + \u00b5 \u00b7 sgn(e) \u00b7 sgn(x)",
                 size=10.5, fill=S.INK, family=S.MONO),
          S.text(66, 422, "one comparator per tap per sample, no multiplier",
                 size=9.5, fill=S.MUTED))

    c.add(S.rect(452, 336, 380, 96, fill=S.WARN_WASH, stroke=S.WARN, rx=8,
                 width=1.2),
          S.text(642, 360, "What sets the step size", size=11.5,
                 fill=S.WARN, anchor="middle", weight=700),
          S.text(470, 384, "\u2022  large step: fast acquisition, noisy taps",
                 size=10, fill=S.SOFT),
          S.text(470, 403, "\u2022  small step: stable taps, slow to adapt",
                 size=10, fill=S.SOFT),
          S.text(470, 422, "\u2022  real links gear-shift: coarse then fine",
                 size=10, fill=S.SOFT))

    c.add(S.callout(36, 448, 808, "Adaptation is a control loop, not a filter",
                    note, kind="accent"))
    return c.render()


FIGURES = {
    "serdes-equaliser-types": serdes_equaliser_types,
    "dfe-principle": dfe_principle,
    "equaliser-adaptation": equaliser_adaptation,
}
