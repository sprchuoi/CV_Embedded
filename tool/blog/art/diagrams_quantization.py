"""Hand-authored diagrams for chapter 03, "Quantization, SNR and ENOB".

    quantizer-transfer-curve   the staircase, and the error it creates
    quantizer-types            mid-tread against mid-rise, and why it matters

Both figures work in **LSB units** rather than a normalised full scale, so the
step is exactly 1 and the levels are the small integers. That makes the two
conventions easy to state precisely:

    mid-tread   levels at 0, +-1, +-2, ...    a level sits at zero (odd count)
    mid-rise    levels at +-0.5, +-1.5, ...   zero is a threshold (even count)
"""

from __future__ import annotations

import math

from . import svg as S

BITS = 3
HALF_RANGE = 4.0          # the plots run over +-4 LSB


def _mid_tread_levels():
    top = 2 ** (BITS - 1) - 1          # 3 for 3 bits
    return [float(i) for i in range(-top, top + 1)]


def _mid_rise_levels():
    top = 2 ** (BITS - 1)              # 4 for 3 bits
    return [i - 0.5 for i in range(-top + 1, top + 1)]


def _frame(c, x, y, w, h, title, subtitle):
    c.add(S.rect(x, y, w, h, fill=S.PLOT_BG, stroke=S.RULE_SOFT, rx=6),
          S.text(x + 14, y + 20, title, size=11.5, fill=S.INK, weight=700),
          S.text(x + 14, y + 37, subtitle, size=9, fill=S.MUTED))


def _staircase(c, levels, to_x, to_y, *, colour, width=2.2):
    """Draw a uniform quantiser's transfer curve from its level list."""
    q = 1.0
    thresholds = [levels[0] - q / 2 + i * q for i in range(len(levels) + 1)]
    for i, level in enumerate(levels):
        lo, hi = thresholds[i], thresholds[i + 1]
        c.add(S.line(to_x(max(lo, -HALF_RANGE)), to_y(level),
                     to_x(min(hi, HALF_RANGE)), to_y(level), stroke=colour,
                     width=width))
        if i:
            c.add(S.line(to_x(lo), to_y(levels[i - 1]), to_x(lo), to_y(level),
                         stroke=colour, width=1.3, dash="3 3"))


# --------------------------------------------------------------------------- #
# 1. the transfer curve
# --------------------------------------------------------------------------- #


def quantizer_transfer_curve() -> str:
    note = ["It is a deterministic sawtooth in the input. Treating it "
            "as white noise is an assumption, not a fact - and it is "
            "exactly the assumption the next two figures test."]
    c = S.Canvas(880, int(372 + S.callout_height(824, note, body_size=11.5) + 14),
                 title="The quantiser transfer curve and its error")
    c.heading("A staircase, and an error that is a function of the input")

    levels = _mid_tread_levels()

    # --- left: the transfer curve ------------------------------------------
    x, y, w, h = 28, 56, 500, 292
    _frame(c, x, y, w, h, "Mid-tread transfer curve, 3 bits",
           "seven levels, so one of them is exactly zero")
    left, right = x + 54, x + w - 24
    top, bottom = y + 54, y + h - 42

    def px(value):
        return left + (value + HALF_RANGE) / (2 * HALF_RANGE) * (right - left)

    def py(value):
        return bottom - (value + HALF_RANGE) / (2 * HALF_RANGE) * (bottom - top)

    c.add(S.line(left, bottom, right, bottom, stroke=S.INK, width=1.2),
          S.line(left, bottom, left, top, stroke=S.INK, width=1.2),
          S.line(px(-HALF_RANGE), py(-HALF_RANGE), px(HALF_RANGE),
                 py(HALF_RANGE), stroke=S.RULE, width=1.2, dash="5 4"),
          S.text(px(HALF_RANGE) - 8, py(HALF_RANGE) + 16, "ideal", size=9,
                 fill=S.MUTED, anchor="end"),
          S.text((left + right) / 2, y + h - 16, "input  [LSB]", size=10,
                 fill=S.SOFT, anchor="middle", weight=600),
          S.text(x + 20, (top + bottom) / 2, "output  [LSB]", size=10, fill=S.SOFT,
                 anchor="middle", weight=600, rotate=-90))

    _staircase(c, levels, px, py, colour=S.ACCENT)

    # mark one LSB and one threshold
    c.add(S.line(px(1), py(1) - 4, px(1), py(1) - 30, stroke=S.NOTE, width=1.4),
          S.line(px(2), py(1) - 30, px(1), py(1) - 30, stroke=S.NOTE, width=1.4),
          S.text(px(1.5), py(1) - 40, "q = 1 LSB", size=10, fill=S.NOTE,
                 anchor="middle", weight=700),
          S.dot(px(0.5), py(0.5), r=4.4, fill=S.WARN),
          S.text(px(0.5) + 10, py(0.5) + 16, "decision threshold", size=9,
                 fill=S.WARN, weight=600))

    # --- right: the error ---------------------------------------------------
    ex, ey, ew, eh = 552, 56, 300, 292
    _frame(c, ex, ey, ew, eh, "Quantisation error", "x \u2212 x_q, in LSB")
    el, er = ex + 50, ex + ew - 20
    et, eb = ey + 74, ey + eh - 46
    mid = (et + eb) / 2
    scale = (eb - et) / 1.6

    def ex_(value):
        return el + (value + HALF_RANGE) / (2 * HALF_RANGE) * (er - el)

    def ey_(error):
        return mid - error * scale

    c.add(S.line(el, mid, er, mid, stroke=S.RULE, width=1.1),
          S.line(el, eb, el, et, stroke=S.INK, width=1.2))
    for bound, label, anchor_y in ((0.5, "+q/2", -10), (-0.5, "\u2212q/2", 16)):
        c.add(S.line(el, ey_(bound), er, ey_(bound), stroke=S.WARN, width=1.2,
                     dash="5 4"),
              S.text(er, ey_(bound) + anchor_y, label, size=9, fill=S.WARN,
                     anchor="end", weight=600))

    points = []
    steps = 480
    for i in range(steps + 1):
        value = -HALF_RANGE + 2 * HALF_RANGE * i / steps
        error = value - round(value)
        points.append((ex_(value), ey_(error)))
    c.add(S.polyline(points, stroke=S.ACCENT, width=1.8),
          S.text((el + er) / 2, ey + eh - 16, "input  [LSB]", size=10,
                 fill=S.SOFT, anchor="middle", weight=600),
          S.text(ex + 18, mid, "error", size=10, fill=S.SOFT, anchor="middle",
                 weight=600, rotate=-90))

    c.add(S.callout(28, 372, 824, "The error is not noise", note,
                    kind="accent"))
    return c.render()


# --------------------------------------------------------------------------- #
# 2. mid-tread against mid-rise
# --------------------------------------------------------------------------- #


def quantizer_types() -> str:
    note2 = ["The step is q = full-scale / 2^N and the error is bounded "
             "by +-q/2. Only the position of the levels changes."]
    c = S.Canvas(880, int(366 + S.callout_height(808, note2, body_size=11.5) + 14),
                 title="Mid-tread and mid-rise quantisers")
    c.heading("Whether a level sits at zero is a design decision")

    cases = [
        ("Mid-tread", "a level at zero - odd number of levels", S.ACCENT,
         _mid_tread_levels(), "zero is represented exactly",
         "a quiet input stays quiet", True),
        ("Mid-rise", "no level at zero - even number of levels", S.NOTE,
         _mid_rise_levels(), "zero is a decision, not a value",
         "an idle input toggles by one LSB", False),
    ]

    box_w, box_h = 384, 236
    for index, (name, subtitle, colour, levels, note_a, note_b, tread) in enumerate(cases):
        x, y = 36 + index * 424, 60
        _frame(c, x, y, box_w, box_h, name, subtitle)
        left, right = x + 36, x + box_w - 24
        mid = y + 132

        c.add(S.line(left, mid, right, mid, stroke=S.RULE, width=1.1))
        step = (right - left) / (len(levels) + 1)
        for i, level in enumerate(levels):
            sx = left + (i + 1) * step
            sy = mid - level * 20
            c.add(S.line(sx, mid, sx, sy, stroke=colour, width=2.0),
                  S.dot(sx, sy, r=4.2, fill=colour, stroke=S.PANEL, width=1.4))

        # The zero line is the entire point of the comparison.
        c.add(S.line(left - 10, mid, right + 10, mid, stroke=S.WARN, width=1.5,
                     dash="4 3"),
              S.text(right + 8, mid - 14, "zero", size=9, fill=S.WARN,
                     anchor="end", weight=600))

        if tread:
            zero_sx = left + (levels.index(0.0) + 1) * step
            c.add(S.circle(zero_sx, mid, 9, fill="none", stroke=S.ACCENT,
                           width=2),
                  S.text(zero_sx, mid + 30, "a real level at 0", size=9,
                         fill=S.ACCENT, anchor="middle", weight=700))
        else:
            c.add(S.circle(left + 4.5 * step, mid, 9, fill="none", stroke=S.WARN,
                           width=2),
                  S.text(left + 4.5 * step, mid + 30, "no level at 0", size=9,
                         fill=S.WARN, anchor="middle", weight=700))

        c.add(S.text(x + 14, y + box_h - 36, note_a, size=10, fill=S.INK,
                     weight=600),
              S.text(x + 14, y + box_h - 18, note_b, size=9.5, fill=S.MUTED,
                     style="italic"))

    c.add(S.text(36, 330,
                 "Mid-tread is what most converters use, because an input of "
                 "exactly zero should produce exactly zero.", size=11,
                 fill=S.SOFT, style="italic"),
          S.text(36, 350,
                 "Mid-rise gets one more level for the same word length and pays "
                 "for it with an idle tone at the LSB rate.", size=11,
                 fill=S.SOFT, style="italic"),
          S.callout(36, 366, 808, "In both conventions", note2,
                    kind="note"))
    return c.render()


FIGURES = {
    "quantizer-transfer-curve": quantizer_transfer_curve,
    "quantizer-types": quantizer_types,
}
