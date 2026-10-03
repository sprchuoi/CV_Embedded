"""Hand-authored diagrams for chapter 01, "What a Signal Actually Is".

    signal-four-domains   the four-way classification, one sketch per quadrant
    signal-four-views     the same four numbers as a graph, a table, a vector
                          and a sum of impulses
"""

from __future__ import annotations

import math

from . import svg as S

TAU = 2 * math.pi


def _sketch_box(c, x, y, w, h, title, subtitle, *, axis_labels=True):
    """A mini plot area with a time/amplitude axis pair."""
    c.add(S.rect(x, y, w, h, fill=S.PLOT_BG, stroke=S.RULE_SOFT, rx=6),
          S.text(x + 12, y + 18, title, size=11.5, fill=S.INK, weight=700),
          S.text(x + 12, y + 34, subtitle, size=9, fill=S.MUTED))
    left, right = x + 30, x + w - 14
    mid = y + h * 0.62
    c.add(S.line(left, mid, right, mid, stroke=S.RULE, width=1.1),
          S.line(left, mid, left, y + 46, stroke=S.RULE, width=1.1))
    if axis_labels:
        c.add(S.text(right, mid + 14, "t", size=9.5, fill=S.MUTED,
                     anchor="end", style="italic"),
              S.text(left - 6, y + 48, "x", size=9.5, fill=S.MUTED,
                     anchor="end", style="italic"))
    return left, right, mid


# --------------------------------------------------------------------------- #
# 1. the four-way classification
# --------------------------------------------------------------------------- #


def signal_four_domains() -> str:
    c = S.Canvas(880, 524, title="Continuous and discrete, in time and in amplitude")
    c.heading("Two independent questions, four different worlds")

    quadrants = [
        (0, 0, "Continuous time, continuous amplitude", "the physical world - a voltage",
         S.ACCENT, "analogue"),
        (1, 0, "Discrete time, continuous amplitude", "sampled, not yet rounded",
         S.NOTE, "sampled"),
        (0, 1, "Continuous time, discrete amplitude", "a quantised analogue waveform",
         S.WARN, "quantised"),
        (1, 1, "Discrete time, discrete amplitude", "the only one a processor holds",
         S.OPTICAL, "digital"),
    ]

    box_w, box_h = 384, 176
    xs = (78, 472)
    ys = (96, 304)

    for col, row, title, subtitle, colour, _tag in quadrants:
        x, y = xs[col], ys[row]
        left, right, mid = _sketch_box(c, x, y, box_w, box_h, title, subtitle)
        span = right - left
        amp = 34

        if row == 0:
            # continuous in amplitude: a smooth curve
            c.add(S.wave(lambda u: math.sin(TAU * 1.1 * u), left, right, mid,
                         amplitude=amp, stroke=colour, width=2.2))
        else:
            # discrete in amplitude: a staircase, four levels
            levels = [round(math.sin(TAU * 1.1 * (i / 11)) * 2) / 2
                      for i in range(12)]
            if col == 0:
                step = span / (len(levels) - 1)
                points = [(left, mid - levels[0] * amp)]
                for i in range(1, len(levels)):
                    px = left + i * step
                    points.append((px - step, points[-1][1]))
                    points.append((px, mid - levels[i] * amp))
                c.add(S.polyline(points, stroke=colour, width=2.2))
            else:
                step = span / (len(levels) - 1)
                for i, value in enumerate(levels):
                    px = left + i * step
                    if i:
                        c.add(S.line(px - step, mid - levels[i - 1] * amp, px,
                                     mid - levels[i - 1] * amp, stroke=colour,
                                     width=2.0))
                    c.add(S.line(px, mid - levels[i - 1] * amp if i else mid, px,
                                 mid - value * amp, stroke=colour, width=2.0),
                          S.dot(px, mid - value * amp, r=3.6, fill=colour,
                                stroke=S.PANEL, width=1.3))

        if col == 1 and row == 0:
            # the samples, with the continuous signal ghosted behind
            c.add(S.wave(lambda u: math.sin(TAU * 1.1 * u), left, right, mid,
                         amplitude=amp, stroke=S.RULE, width=1.2, dash="3 3"))
            step = span / 11
            for i in range(12):
                px = left + i * step
                py = mid - math.sin(TAU * 1.1 * (i / 11)) * amp
                c.add(S.line(px, mid, px, py, stroke=colour, width=1.5),
                      S.dot(px, py, r=3.4, fill=colour, stroke=S.PANEL, width=1.3))

    # The grid is (time down the columns) x (amplitude down the rows), so label
    # the axes rather than repeating the classification inside every panel.
    for row, label in enumerate(("continuous amplitude", "discrete amplitude")):
        cy = ys[row] + box_h / 2
        c.add(S.text(42, cy, label, size=10.5, fill=S.MUTED, weight=700,
                     anchor="middle", rotate=-90))
    for col, label in enumerate(("continuous time", "discrete time")):
        c.add(S.text(xs[col] + box_w / 2, 76, label, size=10.5, fill=S.MUTED,
                     anchor="middle", weight=700))

    c.add(S.text(36, 508,
                 "The two axes are independent. Sampling makes one discrete; "
                 "quantising makes the other discrete.", size=11, fill=S.SOFT,
                 style="italic"))
    return c.render()


# --------------------------------------------------------------------------- #
# 2. four views of the same signal
# --------------------------------------------------------------------------- #


def signal_four_views() -> str:
    c = S.Canvas(880, 470, title="One signal, four equivalent descriptions")
    c.heading("A processor only ever holds one of these")

    values = [2.0, 3.0, 1.0, 0.5]
    box_w, box_h = 384, 178
    xs = (36, 460)
    ys = (72, 268)

    def frame(col, row, title, subtitle):
        x, y = xs[col], ys[row]
        c.add(S.rect(x, y, box_w, box_h, fill=S.PLOT_BG, stroke=S.RULE_SOFT,
                     rx=6),
              S.text(x + 12, y + 18, title, size=11.5, fill=S.INK, weight=700),
              S.text(x + 12, y + 34, subtitle, size=9, fill=S.MUTED))
        return x, y

    # --- 1. the graph ------------------------------------------------------
    x, y = frame(0, 0, "As a graph", "what you draw")
    left, right, mid = x + 34, x + box_w - 18, y + 120
    c.add(S.line(left, mid, right, mid, stroke=S.RULE, width=1.2))
    step = (right - left) / 3.4
    for i, value in enumerate(values):
        px = left + 14 + i * step
        py = mid - value * 24
        c.add(S.line(px, mid, px, py, stroke=S.ACCENT, width=1.8),
              S.dot(px, py, r=4, fill=S.ACCENT, stroke=S.PANEL, width=1.4),
              S.text(px, mid + 15, str(i), size=9, fill=S.MUTED, anchor="middle"))
    c.add(S.text(right, mid - 46, "x[n]", size=10, fill=S.ACCENT_DARK,
                 anchor="end", weight=700))

    # --- 2. the table ------------------------------------------------------
    x, y = frame(1, 0, "As a table", "what you write in a notebook")
    c.add(S.matrix(x + 96, y + 66, 96, 100, 4, 2,
                   cell_labels=[["0", "2.0"], ["1", "3.0"], ["2", "1.0"],
                                ["3", "0.5"]],
                   col_labels=["n", "x[n]"], fill=S.PANEL, stroke=S.RULE,
                   ink=S.SOFT))

    # --- 3. the vector -----------------------------------------------------
    x, y = frame(0, 1, "As a vector", "what a processor actually holds")
    tx = x + 40
    c.add(S.matrix(tx + 26, y + 60, 74, 108, 4, 1,
                   cell_labels=[["2.0"], ["3.0"], ["1.0"], ["0.5"]],
                   fill=S.ACCENT_WASH, stroke=S.ACCENT, ink=S.ACCENT_DARK))
    c.add(S.text(tx + 6, y + 116, "x  =", size=13, fill=S.INK, weight=700),
          S.text(tx + 63, y + 50, "4 x 1", size=9, fill=S.MUTED,
                 anchor="middle"),
          S.text(x + 190, y + 96, "Four numbers.", size=10.5, fill=S.SOFT),
          S.text(x + 190, y + 116, "Fixed length. No", size=10.5, fill=S.SOFT),
          S.text(x + 190, y + 136, "time axis attached", size=10.5, fill=S.SOFT),
          S.text(x + 190, y + 156, "unless you supply one.", size=10.5,
                 fill=S.SOFT))

    # --- 4. the impulse sum ------------------------------------------------
    x, y = frame(1, 1, "As a sum of impulses", "what makes convolution possible")
    c.add(S.text(x + 16, y + 58,
                 "x[n] = 2\u03b4[n] + 3\u03b4[n\u22121] + 1\u03b4[n\u22122] "
                 "+ 0.5\u03b4[n\u22123]", size=10.5, fill=S.INK,
                 family=S.MONO, weight=700))
    for i, value in enumerate(values):
        sx = x + 26 + i * 88
        base = y + 152
        c.add(S.line(sx - 12, base, sx + 60, base, stroke=S.RULE, width=1.1))
        for j in range(4):
            px = sx + j * 17
            height = value * 22 if j == i else 0
            colour = S.ACCENT if j == i else S.RULE_SOFT
            c.add(S.line(px, base, px, base - height, stroke=colour, width=1.5),
                  S.dot(px, base - height, r=2.6, fill=colour))
        c.add(S.text(sx + 24, base + 15, f"{S.num(value)}\u03b4[n\u2212{i}]",
                     size=8.5, fill=S.ACCENT_DARK if i == 0 else S.MUTED,
                     anchor="middle"))

    c.add(S.text(36, 462,
                 "They are the same signal. The vector view is the one that "
                 "runs; the impulse view is the one that explains filtering.",
                 size=11, fill=S.SOFT, style="italic"))
    return c.render()


FIGURES = {
    "signal-four-domains": signal_four_domains,
    "signal-four-views": signal_four_views,
}
