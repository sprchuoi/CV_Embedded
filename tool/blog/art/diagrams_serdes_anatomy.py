"""Hand-authored diagrams for the SerDes anatomy chapter.

    serdes-tx-chain     serializer to driver, with the equalisation folded into
                        the transmit path
    serdes-rx-chain     the receive path: CTLE, VGA, sampler, slicer, DFE
    pre-emphasis        what a transmit FFE does to the waveform, and what it
                        costs in amplitude
    slicer-decision     the last analogue decision, drawn as the comparison it is

The four processing steps from the Ethernet part -- prepare, cross, recover,
decide -- reappear here at chip scale, and the figures name the same functions
with the names a SerDes datasheet uses.
"""

from __future__ import annotations

import math

from . import svg as S


def _fmt(value: float) -> str:
    """A signed number trimmed of trailing zeros: +1, -0.333, +0.667."""
    text = f"{value:+.3f}".rstrip("0").rstrip(".")
    return "+0" if text in ("+", "-") else text


def serdes_tx_chain() -> str:
    note = [
        "The transmit equaliser is deliberately a filter the signal passes "
        "through, so it is placed before the driver, not after it. Its taps "
        "are set from a link training exchange or from a fixed preset, and "
        "every decibel of de-emphasis is a decibel of peak amplitude the "
        "driver must still be able to produce.",
        "The output is AC-coupled almost everywhere, which is why the "
        "termination and the coupling capacitors appear in the path rather "
        "than beside it. Their corner frequency is part of the low-frequency "
        "budget, and a long run of identical bits is what tests it.",
    ]
    c = S.Canvas(880, int(470 + S.callout_height(808, note, body_size=11.5) + 14),
                 title="The transmit side of a serial lane")

    stages = [
        ("Bits in", "from the PCS,\nper lane", "plain"),
        ("Serializer", "50:1 or so,\nretime", "note"),
        ("TX FFE", "pre-emphasis,\n2-5 taps", "accent"),
        ("Driver", "CML, 50 ohm,\nprogrammable swing", "warn"),
        ("Coupling\n+ channel", "AC caps,\nconnector", "plain"),
    ]
    bw, gap, by, bh = 148, 20, 150, 104
    x0 = (880 - (len(stages) * bw + (len(stages) - 1) * gap)) / 2
    for i, (title, sub, kind) in enumerate(stages):
        bx = x0 + i * (bw + gap)
        c.add(S.block(bx, by, bw, bh, title.split("\n")[0], kind=kind,
                      title_size=11.5))
        for j, line in enumerate(sub.split("\n")):
            c.add(S.text(bx + bw / 2, by + bh / 2 + 28 + j * 14, line,
                         size=9.5, fill=S.SOFT, anchor="middle"))
        if i < len(stages) - 1:
            c.add(S.arrow(bx + bw + 2, by + bh / 2, bx + bw + gap - 2,
                          by + bh / 2, stroke=S.MUTED, width=1.5))

    # the clock, feeding the serializer and the FFE
    clk_y = by + bh + 56
    c.add(S.arrow_path([(x0 + 1.5 * (bw + gap), by + bh),
                        (x0 + 1.5 * (bw + gap), clk_y),
                        (x0 + bw / 2, clk_y), (x0 + bw / 2, by + bh)],
                       stroke=S.OPTICAL, width=1.4, head=False),
          S.text(x0 + 1.5 * (bw + gap) + 12, clk_y, "the transmit clock, and "
                 "the FFE's tap weights", size=10, fill=S.OPTICAL_DARK,
                 weight=600))

    # the swing annotation
    c.add(S.text(x0 + 3 * (bw + gap), by - 26,
                 "swing set by the standard; de-emphasis eats into it",
                 size=9.5, fill=S.WARN, anchor="middle", weight=600))

    c.add(S.callout(36, clk_y + 34, 808, "Where the margin is spent before "
                    "the channel", note, kind="accent"))
    return c.render()


def serdes_rx_chain() -> str:
    note = [
        "Receive equalisation is split between a continuous-time analogue "
        "stage and a digital one, because the two have different cost "
        "structures. The CTLE is cheap in power and adds noise; the FFE is "
        "precise and needs an ADC; the DFE is exact at the decision point and "
        "cannot be adapted from an error before the decision is made.",
        "This is the same FFE-versus-DFE trade the optical parts describe for "
        "PAM4 over copper, drawn at chip scale. Nothing about the mathematics "
        "changes; what changes is that the receiver also has to recover a "
        "clock, and the clock comes from the decisions this chain makes.",
    ]
    c = S.Canvas(880, int(500 + S.callout_height(808, note, body_size=11.5) + 14),
                 title="The receive side of a serial lane")

    stages = [
        ("Channel", "loss +\ncrosstalk", "plain"),
        ("CTLE", "analogue\npeaking", "warn"),
        ("VGA", "AGC to\nfull scale", "note"),
        ("Sampler\n+ ADC", "slices the\neye", "plain"),
        ("FFE / DFE", "digital\nequalise", "accent"),
        ("Slicer", "decide\nbits", "optical"),
    ]
    bw, gap, by, bh = 124, 16, 146, 104
    x0 = (880 - (len(stages) * bw + (len(stages) - 1) * gap)) / 2
    centres = []
    for i, (title, sub, kind) in enumerate(stages):
        bx = x0 + i * (bw + gap)
        centres.append(bx + bw / 2)
        c.add(S.block(bx, by, bw, bh, title.split("\n")[0], kind=kind,
                      title_size=11))
        for j, line in enumerate(sub.split("\n")):
            c.add(S.text(bx + bw / 2, by + bh / 2 + 28 + j * 14, line,
                         size=9.5, fill=S.SOFT, anchor="middle"))
        if i < len(stages) - 1:
            c.add(S.arrow(bx + bw + 2, by + bh / 2, bx + bw + gap - 2,
                          by + bh / 2, stroke=S.MUTED, width=1.4))

    # the CDR loop, from the slicer back to the sampler
    loop_y = by + bh + 52
    c.add(S.arrow_path([(centres[5], by + bh), (centres[5], loop_y),
                        (centres[3], loop_y), (centres[3], by + bh)],
                       stroke=S.OPTICAL, width=1.6),
          S.text((centres[3] + centres[5]) / 2, loop_y + 18,
                 "clock recovery: the decisions set the phase", size=10,
                 fill=S.OPTICAL_DARK, anchor="middle", weight=600))

    # the DFE feedback, which is local to the decision
    c.add(S.arrow_path([(centres[5], by + bh + 2), (centres[5], by + bh + 26),
                        (centres[4], by + bh + 26), (centres[4], by + bh + 2)],
                       stroke=S.ACCENT, width=1.4, head=False),
          S.text(centres[4] + 6, by + bh + 26, "DFE feedback", size=9.5,
                 fill=S.ACCENT_DARK, weight=600))

    c.add(S.callout(36, loop_y + 38, 808, "Two loops, two timescales", note,
                    kind="accent"))
    return c.render()


def pre_emphasis() -> str:
    note = [
        "De-emphasis is pre-distortion, not amplification. A transmitter "
        "cannot boost high frequencies without spending peak amplitude, so it "
        "lowers the low-frequency content instead and lets the channel's own "
        "loss restore the shape. The eye at the receiver is the point; the "
        "waveform at the driver is deliberately ugly.",
        "The cost is that the launched eye is smaller than the swing would "
        "allow. A three-tap FFE that de-emphasises by 6 dB gives away 6 dB of "
        "launch amplitude to buy back more than that at the far end -- which "
        "is a good trade only on a channel that actually has the loss.",
    ]
    c = S.Canvas(880, int(452 + S.callout_height(808, note, body_size=11.5) + 14),
                 title="What a transmit FFE does to the waveform")

    x0, x1 = 96, 800
    base = 300
    amp = 70

    # (label, per-symbol main cursor, de-emphasis levels, colour)
    panels = [
        ("No equalisation", [1.0, 1.0, 1.0, -1.0, -1.0, 1.0, -1.0, 1.0], None,
         S.NOTE, 96),
        ("3-tap FFE, 6 dB de-emphasis", [1.0, 1.0, 1.0, -1.0, -1.0, 1.0, -1.0, 1.0],
         0.5, S.ACCENT, 250),
    ]

    for title, symbols, deemph, colour, cy in panels:
        c.add(S.text(x0, cy - amp - 26, title, size=11, fill=colour,
                     weight=700))
        step = (x1 - x0) / len(symbols)
        pts = []
        for i, sym in enumerate(symbols):
            # An FFE emphasises a bit that differs from the one before it and
            # de-emphasises one that repeats. This is that rule, applied.
            repeated = i > 0 and symbols[i] == symbols[i - 1]
            level = sym * (deemph if (deemph is not None and repeated) else 1.0)
            x_a = x0 + i * step
            pts.extend([(x_a, cy - level * amp), (x_a + step, cy - level * amp)])
        c.add(S.polyline(pts, stroke=colour, width=2.4))
        c.add(S.line(x0, cy, x1, cy, stroke=S.RULE, width=1, dash="4 4"))

        if deemph is not None:
            # measure the two levels on the figure itself
            hi = cy - 1.0 * amp
            lo = cy - deemph * amp
            c.add(S.line(x1 + 8, lo, x1 + 8, hi, stroke=S.WARN, width=1.6),
                  S.line(x1 + 4, lo, x1 + 12, lo, stroke=S.WARN, width=1.4),
                  S.line(x1 + 4, hi, x1 + 12, hi, stroke=S.WARN, width=1.4),
                  S.text(x1 + 18, (lo + hi) / 2,
                         f"peak-to-de-emphasis\n= {-20 * math.log10(deemph):.1f} dB",
                         size=9, fill=S.WARN, weight=600))

    c.add(S.text(x0, 372, "same symbol sequence, same driver swing; only the "
                 "tap weights differ", size=10, fill=S.SOFT, style="italic"))

    c.add(S.callout(36, 400, 808, "Why the ugly waveform is the right one",
                    note, kind="warn"))
    return c.render()


def slicer_decision() -> str:
    note = [
        "The slicer is a comparator with a threshold and a clock. Its output "
        "is a hard decision, and everything the receiver does afterwards -- "
        "FEC, the error counter, the adaptation loop -- consumes that hard "
        "decision. The analogue information above and below the threshold is "
        "thrown away, which is exactly why error-correction coding has to be "
        "designed around what a hard slicer can report.",
        "For PAM4 there are three thresholds and two comparators per level, "
        "and the same argument applies three times over. A soft-decision "
        "demodulator would keep the analogue distance and do better; almost "
        "no high-speed SerDes does, because the power and latency are not "
        "available at 100 Gbit/s per lane.",
    ]
    c = S.Canvas(880, int(446 + S.callout_height(808, note, body_size=11.5) + 14),
                 title="The last analogue decision")

    # NRZ: one threshold; PAM4: three
    left = (60, 420)
    right = (480, 840)

    for x0, x1, levels, label, colour in (
            (left[0], left[1], [-1.0, 1.0], "NRZ: one threshold", S.NOTE),
            (right[0], right[1], [-1.0, -1 / 3, 1 / 3, 1.0],
             "PAM4: three thresholds", S.ACCENT)):
        mid_x = (x0 + x1) / 2
        top, bot = 108, 300
        c.add(S.text(x0, 88, label, size=11, fill=colour, weight=700))

        def py(v):
            return bot - (v + 1.2) / 2.4 * (bot - top)

        # level guides
        for lv in levels:
            c.add(S.line(x0, py(lv), x1, py(lv), stroke=S.RULE, width=1,
                         dash="3 4"),
                  S.text(x0 - 8, py(lv), _fmt(lv), size=9, fill=S.MUTED,
                         anchor="end", family=S.MONO))

        # thresholds, drawn as the comparators they are
        thresholds = [(levels[i] + levels[i + 1]) / 2
                      for i in range(len(levels) - 1)]
        for t in thresholds:
            c.add(S.line(x0, py(t), x1, py(t), stroke=S.WARN, width=1.8),
                  S.text(x1, py(t) - 12, "threshold " + _fmt(t),
                         size=9, fill=S.WARN, anchor="end", weight=600))

        # a noisy cloud on each level
        for lv in levels:
            for k in range(28):
                u = (k / 27) - 0.5
                xx = mid_x + u * (x1 - x0) * 0.72
                yy = py(lv) + math.sin(k * 2.7) * 6 + (k % 3) * 2
                c.add(S.dot(xx, yy, r=2.2, fill=colour))

    c.add(S.callout(36, 340, 808, "What the hard decision throws away", note,
                    kind="optical"))
    return c.render()


FIGURES = {
    "serdes-tx-chain": serdes_tx_chain,
    "serdes-rx-chain": serdes_rx_chain,
    "pre-emphasis": pre_emphasis,
    "slicer-decision": slicer_decision,
}
