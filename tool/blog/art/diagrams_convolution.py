"""Hand-authored diagrams for the convolution and LTI chapter.

    convolution-flip-slide     the flip-and-slide, drawn one overlap at a time
    impulse-decomposition      any input is a pile of scaled shifted impulses
    convolution-three-views    the sum, the polynomial and the matrix form
"""

from __future__ import annotations

from . import svg as S

# --------------------------------------------------------------------------- #
# shared stem-plot helper
# --------------------------------------------------------------------------- #


def _stems(c, x0, x1, y_zero, values, *, color, amp, label=None, labels=False,
           radius=3.6, width=1.8):
    """Draw ``values`` as a stem plot evenly spaced across ``[x0, x1]``."""
    step = (x1 - x0) / max(1, len(values) - 1)
    for i, value in enumerate(values):
        px = x0 + i * step
        py = y_zero - value * amp
        c.add(S.line(px, y_zero, px, py, stroke=color, width=width),
              S.dot(px, py, r=radius, fill=color, stroke=S.PANEL, width=1.4))
        if labels:
            c.add(S.text(px, y_zero + 15, str(i), size=8.5, fill=S.MUTED,
                         anchor="middle"))
    return step


def _panel(c, x, y, w, h, title, subtitle=None):
    c.add(S.rect(x, y, w, h, fill=S.PLOT_BG, stroke=S.RULE_SOFT, rx=6),
          S.text(x + 10, y + 15, title, size=10.5, fill=S.INK, weight=700))
    if subtitle:
        c.add(S.text(x + 10, y + 30, subtitle, size=9, fill=S.MUTED))


# --------------------------------------------------------------------------- #
# 1. flip and slide
# --------------------------------------------------------------------------- #


def convolution_flip_slide() -> str:
    c = S.Canvas(880, 548, title="Convolution as flip, shift, multiply, sum")
    c.heading("Convolution is one picture, repeated")

    x_vals = [1.0, 2.0, 3.0, 2.0, 1.0]
    h_vals = [1.0, 0.5, -0.5]

    # One shared k axis for every panel, so the slide is literally the same set
    # of stems moving right by one position at a time.
    k_min, k_max = -3, 5
    x0, x1 = 104, 806
    step = (x1 - x0) / (k_max - k_min)
    amp = 20

    def px(k):
        return x0 + (k - k_min) * step

    def frame(top, height, title, subtitle):
        c.add(S.rect(20, top, 840, height, fill=S.PLOT_BG, stroke=S.RULE_SOFT,
                     rx=6),
              S.text(32, top + 16, title, size=10.5, fill=S.INK, weight=700),
              S.text(32, top + 31, subtitle, size=9, fill=S.MUTED))

    def stems(baseline, values_by_k, color, radius=3.7, width=1.9):
        for k, value in values_by_k.items():
            c.add(S.line(px(k), baseline, px(k), baseline - value * amp,
                         stroke=color, width=width),
                  S.dot(px(k), baseline - value * amp, r=radius, fill=color,
                        stroke=S.PANEL, width=1.4))

    # ---- panel 0: the two sequences, each on its own row ------------------
    top, height = 48, 150
    frame(top, height, "x[k]   and   h[k]",
          "both in their natural order - separate rows, because their indices overlap")
    base_x, base_h = top + 80, top + 130
    c.add(S.line(x0 - 30, base_x, x1, base_x, stroke=S.RULE, width=1.2),
          S.line(x0 - 30, base_h, x1, base_h, stroke=S.RULE, width=1.2))
    stems(base_x, {k: v for k, v in enumerate(x_vals)}, S.ACCENT)
    stems(base_h, {k: v for k, v in enumerate(h_vals)}, S.NOTE)
    c.add(S.text(x0 - 38, base_x, "x[k]", size=10.5, fill=S.ACCENT_DARK,
                 anchor="end", weight=700),
          S.text(x0 - 38, base_h, "h[k]", size=10.5, fill=S.NOTE, anchor="end",
                 weight=700))

    # ---- panels 1-3: h flipped, then slid ---------------------------------
    for index, shift in enumerate((0, 1, 2)):
        panel_top = 206 + index * 108
        title = "h[0 \u2212 k]" if shift == 0 else f"h[{shift} \u2212 k]"
        subtitle = ("flip h about the origin" if shift == 0
                    else f"slide it {shift} step{'s' if shift > 1 else ''} right"
                         " - the shaded overlap is the product")
        frame(panel_top, 100, title, subtitle)
        baseline = panel_top + 74

        # h[n-k] is h[m] at position k = n - m, for m in 0..len(h)-1.
        h_here = {shift - m: h_vals[m] for m in range(len(h_vals))}

        # x[k] faint behind, so the overlap is visible rather than asserted.
        for k, value in enumerate(x_vals):
            c.add(S.line(px(k), baseline, px(k), baseline - value * amp,
                         stroke=S.RULE, width=1.3),
                  S.dot(px(k), baseline - value * amp, r=2.6, fill=S.RULE_SOFT))
        c.add(S.line(x0 - 30, baseline, x1, baseline, stroke=S.RULE, width=1.2))

        overlap = {k: x_vals[k] * h_here[k] for k in h_here
                   if 0 <= k < len(x_vals)}
        for k in overlap:
            c.add(S.rect(px(k) - step * 0.34, panel_top + 44, step * 0.68, 50,
                         fill=S.ACCENT_WASH, stroke=None, rx=3))
        stems(baseline, h_here, S.NOTE)
        for k, product in overlap.items():
            c.add(S.text(px(k), panel_top + 88, S.num(product), size=9.5,
                         fill=S.ACCENT_DARK, anchor="middle", weight=700))
        c.add(S.text(x1, panel_top + 88,
                     f"y[{shift}] = {S.num(sum(overlap.values()))}", size=10,
                     fill=S.ACCENT_DARK, anchor="end", weight=700,
                     family=S.MONO))

    c.add(S.text(20, 534, "Only the overlapping taps contribute at each shift, so "
                          "the cost is one multiply per tap.", size=11,
                 fill=S.SOFT, style="italic"))
    return c.render()


# --------------------------------------------------------------------------- #
# 2. impulse decomposition
# --------------------------------------------------------------------------- #


def impulse_decomposition() -> str:
    c = S.Canvas(880, 400, title="Any signal is a sum of scaled, shifted impulses")
    c.heading("This is why the impulse response is enough")

    x_vals = [1.0, 2.0, 3.0, 2.0, 1.0]
    parts = [(0, 1.0, S.ACCENT_DARK), (2, 3.0, S.ACCENT), (4, 1.0, S.NOTE)]

    y_zero = 128
    x0, x1 = 90, 800
    step = (x1 - x0) / 4

    # the original signal
    c.add(S.text(x0, 66, "x[n]", size=12, fill=S.INK, weight=700))
    _stems(c, x0, x1, y_zero, x_vals, color=S.INK, amp=30, labels=True)
    c.add(S.line(x0 - 24, y_zero, x1 + 24, y_zero, stroke=S.RULE, width=1.2))

    c.add(S.text(x0, 172, "becomes the sum of these", size=10.5, fill=S.MUTED,
                 style="italic"))

    # three component impulse trains
    box_w = (800 - 40 - 2 * 24) / 3
    for index, (n, amplitude, color) in enumerate(parts):
        bx = 40 + index * (box_w + 24)
        by = 196
        _panel(c, bx, by, box_w, 140, f"{S.num(amplitude)} \u00b7 \u03b4[n \u2212 "
                                      f"{n}]", None)
        local_zero = by + 104
        local_step = (box_w - 44) / 4
        for i in range(5):
            px = bx + 22 + i * local_step
            value = x_vals[i] if i == n else 0.0
            py = local_zero - value * 24
            c.add(S.line(px, local_zero, px, py,
                         stroke=color if i == n else S.RULE, width=1.8),
                  S.dot(px, py, r=3.4,
                        fill=color if i == n else S.RULE_SOFT,
                        stroke=S.PANEL, width=1.3))
        c.add(S.line(bx + 16, local_zero, bx + box_w - 16, local_zero,
                     stroke=S.RULE, width=1.1))

    c.add(S.text(40, 366, "Linearity gives you the scaling and the adding; time "
                          "invariance gives you the shifting.",
                 size=11, fill=S.SOFT, style="italic"))
    return c.render()


# --------------------------------------------------------------------------- #
# 3. three views of one operation
# --------------------------------------------------------------------------- #


def convolution_three_views() -> str:
    c = S.Canvas(880, 420, title="One operation, three ways to compute it")
    c.heading("The same seven numbers, whichever way you look at them")

    x_vals = [1.0, 2.0, 3.0]
    h_vals = [2.0, 1.0]

    col_w = 262
    gap = 22
    x_start = 22
    top = 52
    height = 300

    def frame(index, title, subtitle):
        bx = x_start + index * (col_w + gap)
        c.add(S.rect(bx, top, col_w, height, fill=S.PANEL, stroke=S.RULE,
                     rx=8),
              S.text(bx + 14, top + 22, title, size=11.5, fill=S.INK,
                     weight=700),
              S.text(bx + 14, top + 40, subtitle, size=9.5, fill=S.MUTED))
        return bx

    # --- column 1: the sum --------------------------------------------------
    bx = frame(0, "The sum", "y[n] = \u03a3 x[k]\u00b7h[n\u2212k]")
    lines = [
        "y[0] = x[0]h[0]",
        "         = 1\u00b72 = 2",
        "",
        "y[1] = x[0]h[1] + x[1]h[0]",
        "         = 1\u00b71 + 2\u00b72 = 5",
        "",
        "y[2] = x[1]h[1] + x[2]h[0]",
        "         = 2\u00b71 + 3\u00b72 = 8",
        "",
        "y[3] = x[2]h[1] = 3\u00b71 = 3",
        "",
        "y = [2, 5, 8, 3]",
    ]
    for i, line in enumerate(lines):
        mono = line.strip().startswith("y") or line.strip().startswith("=")
        c.add(S.text(bx + 14, top + 66 + i * 18, line, size=9.5,
                     fill=S.ACCENT_DARK if line.startswith("y =") else S.SOFT,
                     family=S.MONO if mono else S.FONT,
                     weight=700 if line.startswith("y =") else 400))

    # --- column 2: the polynomial ------------------------------------------
    bx = frame(1, "The polynomial", "multiply, then collect like powers")
    c.add(S.text(bx + 14, top + 68, "(1 + 2z\u207b\u00b9 + 3z\u207b\u00b2)", size=11,
                 fill=S.ACCENT_DARK, family=S.MONO),
          S.text(bx + 14, top + 90, "\u00d7  (2 + 1z\u207b\u00b9)", size=11,
                 fill=S.NOTE, family=S.MONO),
          S.line(bx + 14, top + 104, bx + col_w - 14, top + 104, stroke=S.RULE,
                 width=1.2),
          S.text(bx + 14, top + 126, "2 + 5z\u207b\u00b9 + 8z\u207b\u00b2 + 3z\u207b\u00b3",
                 size=11, fill=S.INK, family=S.MONO, weight=700))
    c.add(S.text(bx + 14, top + 164,
                 "The coefficients of the product", size=9.5, fill=S.MUTED),
          S.text(bx + 14, top + 180,
                 "are the convolution. Every", size=9.5, fill=S.MUTED),
          S.text(bx + 14, top + 196,
                 "multiply-and-add you write out", size=9.5, fill=S.MUTED),
          S.text(bx + 14, top + 212,
                 "by hand is already this.", size=9.5, fill=S.MUTED),
          S.text(bx + 14, top + 246, "y = [2, 5, 8, 3]", size=10.5,
                 fill=S.ACCENT_DARK, family=S.MONO, weight=700))

    # --- column 3: the matrix ----------------------------------------------
    bx = frame(2, "The matrix", "a Toeplitz matrix times the input")
    c.add(S.matrix(bx + 66, top + 66, 56, 128, 4, 3,
                   cell_labels=[["h0", "", ""],
                                ["h1", "h0", ""],
                                ["", "h1", "h0"],
                                ["", "", "h1"]],
                   row_labels=["y0", "y1", "y2", "y3"],
                   col_labels=["x0", "x1", "x2"],
                   fill=S.PLOT_BG, stroke=S.RULE, ink=S.SOFT))
    c.add(S.text(bx + 14, top + 222, "Zero-padded, and every diagonal", size=9.5,
                 fill=S.MUTED),
          S.text(bx + 14, top + 238, "is the same h. That structure is", size=9.5,
                 fill=S.MUTED),
          S.text(bx + 14, top + 254, "what makes convolution cheap -", size=9.5,
                 fill=S.MUTED),
          S.text(bx + 14, top + 270, "and what an FFT exploits.", size=9.5,
                 fill=S.MUTED),
          S.text(bx + 14, top + 292, "y = [2, 5, 8, 3]", size=10.5,
                 fill=S.ACCENT_DARK, family=S.MONO, weight=700))

    c.add(S.text(22, 386, "Three views, one result. When a block diagram says "
                          "\u2018filter\u2019, it means this.", size=11,
                 fill=S.SOFT, style="italic"))
    return c.render()


FIGURES = {
    "convolution-flip-slide": convolution_flip_slide,
    "impulse-decomposition": impulse_decomposition,
    "convolution-three-views": convolution_three_views,
}
