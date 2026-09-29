"""Hand-authored diagrams for the FIR filter design chapter.

    fir-tapped-delay-line       the structure itself, and what it costs
    fir-specification           how a filter requirement becomes a tap count
    fir-linear-phase-symmetry   the four symmetric-tap cases and what each allows
"""

from __future__ import annotations

import math

from . import svg as S

# --------------------------------------------------------------------------- #
# 1. the transversal structure
# --------------------------------------------------------------------------- #


def _multiplier(x, y_top, y_apex, *, wash, stroke):
    """A downwards-pointing multiplier triangle centred on ``x``."""
    d = (f"M {S.num(x - 21)} {S.num(y_top)} L {S.num(x + 21)} {S.num(y_top)} "
         f"L {S.num(x)} {S.num(y_apex)} Z")
    return S.path(d, fill=wash, stroke=stroke, width=1.6)


def fir_tapped_delay_line() -> str:
    c = S.Canvas(880, 436, title="A four-tap FIR filter drawn as a tapped delay line")
    c.heading("The FIR, drawn as it is actually built")

    taps = 5
    x_first, spacing = 100, 150
    path_y = 118
    mult_top, mult_apex = 194, 244
    bus_y = 292
    last_x = x_first + (taps - 1) * spacing

    # --- the delay line -----------------------------------------------------
    c.add(S.arrow(30, path_y, x_first - 6, path_y, stroke=S.INK, width=1.8),
          S.text(36, path_y - 22, "x[n]", size=12, fill=S.INK, weight=700))
    c.add(S.line(x_first, path_y, last_x, path_y, stroke=S.INK, width=1.8))

    for k in range(taps - 1):
        bx = x_first + k * spacing + 34
        c.add(S.rect(bx, path_y - 18, 82, 36, fill=S.PLOT_BG, stroke=S.NOTE,
                     rx=6, width=1.5),
              S.text(bx + 41, path_y, "z^-1^", size=12.5, fill=S.NOTE,
                     anchor="middle", weight=700))

    # --- tap points, multipliers, coefficients -----------------------------
    for k in range(taps):
        tx = x_first + k * spacing
        c.add(S.dot(tx, path_y, r=4.2, fill=S.INK),
              S.line(tx, path_y, tx, mult_top, stroke=S.RULE, width=1.5),
              _multiplier(tx, mult_top, mult_apex, wash=S.ACCENT_WASH,
                          stroke=S.ACCENT),
              S.text(tx + 30, (mult_top + mult_apex) / 2, f"h~{k}~", size=11.5,
                     fill=S.ACCENT_DARK, anchor="start", weight=700),
              S.line(tx, mult_apex, tx, bus_y, stroke=S.RULE, width=1.5))

    # --- the summing bus ----------------------------------------------------
    c.add(S.line(x_first, bus_y, 780, bus_y, stroke=S.RULE, width=2.2))
    for k in range(taps):
        c.add(S.dot(x_first + k * spacing, bus_y, r=3.6, fill=S.RULE))
    c.add(S.circle(806, bus_y, 22, fill=S.NOTE_WASH, stroke=S.NOTE, width=1.8),
          S.text(806, bus_y, "Σ", size=16, fill=S.NOTE, anchor="middle",
                 weight=700),
          S.arrow(828, bus_y, 866, bus_y, stroke=S.INK, width=1.8),
          S.text(838, bus_y - 24, "y[n]", size=12, fill=S.INK, weight=700))

    # --- annotations --------------------------------------------------------
    c.add(S.text(30, 56, "One multiply-accumulate per tap, per output sample.",
                 size=11, fill=S.MUTED, style="italic"),
          S.text(x_first, 86, "tapped delay line", size=10.5,
                 fill=S.MUTED, weight=600),
          S.text(x_first, bus_y + 32, "the coefficients are the whole design: "
                                      "h[0..4] here, 11 to 100+ in a real link",
                 size=10.5, fill=S.MUTED, style="italic"))

    c.add(S.callout(30, 342, 820, "Why the tap count is a silicon decision",
                    ["Every output sample costs one multiply and one add per tap, at the "
                     "full sample rate.",
                     "A 60-tap FFE on a 64 GBd link is 3.8 Tera-MAC/s before any "
                     "parallelism - so taps are bought with area and power, not just error."],
                    kind="accent"))
    return c.render()


# --------------------------------------------------------------------------- #
# 2. the specification
# --------------------------------------------------------------------------- #


def fir_specification() -> str:
    c = S.Canvas(880, 448, title="The four numbers that specify a lowpass filter")
    c.heading("A filter specification is four numbers, not a curve")

    px0, px1 = 100, 620
    base_y, top_y = 330, 108
    fp, fs_stop = 0.20, 0.30
    delta_p, delta_s = 0.035, 0.022
    span = (px1 - px0) / 0.5

    def fx(freq):
        return px0 + freq * span

    def mag_y(magnitude):
        """1.0 sits just under the top of the plot; 0.0 on the baseline."""
        return base_y - (base_y - top_y - 20) * magnitude

    # --- the transition band sits behind everything else --------------------
    c.add(S.rect(fx(fp), top_y - 10, fx(fs_stop) - fx(fp), base_y - top_y + 10,
                 fill=S.NOTE_WASH, stroke=None, rx=0),
          S.text((fx(fp) + fx(fs_stop)) / 2, top_y - 34, "transition", size=10,
                 fill=S.NOTE, anchor="middle", weight=700),
          S.text((fx(fp) + fx(fs_stop)) / 2, top_y - 18, "band", size=10,
                 fill=S.NOTE, anchor="middle", weight=700))

    # --- the response -------------------------------------------------------
    points = []
    steps = 400
    for i in range(steps + 1):
        f = 0.5 * i / steps
        if f <= fp:
            magnitude = 1.0 + delta_p * 0.85 * math.cos(9 * math.pi * f / fp)
        elif f >= fs_stop:
            magnitude = delta_s * 0.5 * (
                1 + math.cos(14 * math.pi * (f - fs_stop) / (0.5 - fs_stop)))
        else:
            t = (f - fp) / (fs_stop - fp)
            smooth = t * t * (3 - 2 * t)
            magnitude = (1.0 + delta_p * 0.85) * (1 - smooth) - delta_s * 0.5 * smooth
        points.append((fx(f), mag_y(magnitude)))
    c.add(S.polyline(points, stroke=S.ACCENT, width=2.4))

    c.add(S.line(px0, mag_y(0), px1, mag_y(0), stroke=S.INK, width=1.5),
          S.line(px0, base_y, px0, top_y, stroke=S.INK, width=1.5))

    # --- tolerances ---------------------------------------------------------
    c.add(S.line(px0, mag_y(1 + delta_p), fx(fs_stop), mag_y(1 + delta_p),
                 stroke=S.ACCENT_DARK, width=1.1, dash="5 4"),
          S.line(px0, mag_y(1 - delta_p), fx(fp), mag_y(1 - delta_p),
                 stroke=S.ACCENT_DARK, width=1.1, dash="5 4"),
          S.line(px0, mag_y(1), fx(fp), mag_y(1), stroke=S.RULE, width=1,
                 dash="2 4"))

    for freq, label, color in ((fp, "f~p~", S.ACCENT_DARK),
                               (fs_stop, "f~st~", S.WARN)):
        c.add(S.line(fx(freq), base_y - 6, fx(freq), base_y, stroke=color,
                     width=1.4),
              S.text(fx(freq), base_y + 20, label, size=11, fill=color,
                     anchor="middle", weight=700))

    # --- annotations --------------------------------------------------------
    c.add(S.text(px0, top_y - 34, "passband", size=10.5, fill=S.ACCENT_DARK,
                 weight=700),
          S.text(px1, top_y - 34, "stopband", size=10.5, fill=S.WARN,
                 anchor="end", weight=700),
          S.text(px0 + 8, mag_y(1 + delta_p) - 16, "1 + \u03b4~p~", size=10,
                 fill=S.ACCENT_DARK),
          S.text(px0 + 8, mag_y(1 - delta_p) + 16, "1 - \u03b4~p~", size=10,
                 fill=S.ACCENT_DARK),
          S.text(px0 - 12, mag_y(1), "1", size=10, fill=S.MUTED, anchor="end"),
          S.text(px0 - 12, mag_y(0), "0", size=10, fill=S.MUTED, anchor="end"),
          S.text(px0, base_y + 52, "normalised frequency  (\u00d7\u03c0 rad/sample)",
                 size=10.5, fill=S.SOFT, anchor="middle", weight=600),
          S.text(px0 - 66, (base_y + top_y) / 2, "|H(f)|", size=10.5, fill=S.SOFT,
                 anchor="middle", weight=600, rotate=-90),
          S.text(px1, base_y + 72, "tolerances exaggerated for legibility",
                 size=9.5, fill=S.MUTED, anchor="end", style="italic"))

    # --- the formula box ---------------------------------------------------
    c.add(S.callout(646, 96, 210, "Windowed-sinc estimate",
                    ["A = 20 log\u2081\u2080 (1 / \u03b4~s~)  dB",
                     "\u0394\u03c9 = 2\u03c0 (f~st~ - f~p~)",
                     "",
                     "N \u2248 (A - 8) / (2.285 \u0394\u03c9)"],
                    kind="note", body_size=11))
    c.add(S.text(646, 208, "The transition width, not the cutoff,", size=10,
                 fill=S.MUTED),
          S.text(646, 224, "drives the length. Halving \u0394\u03c9", size=10,
                 fill=S.MUTED),
          S.text(646, 240, "doubles N.", size=10, fill=S.MUTED))

    # --- a magnified look at the stopband, which is invisible above ---------
    c.add(_stopband_detail(646, 264, 210, 122, delta_s))
    return c.render()


def _stopband_detail(x, y, w, h, delta_s) -> str:
    """A schematic zoom of the stopband tolerance, drawn not to scale.

    On a linear-magnitude plot a -33 dB stopband is 2% of the height: correct
    and completely unreadable. Rather than distort the main curve, the ripple
    gets its own magnified panel and the figure says the tolerances are
    exaggerated.
    """
    left, right = x + 34, x + w - 12
    floor_y, ceil_y = y + h - 22, y + 30
    out = [S.rect(x, y, w, h, fill=S.PLOT_BG, stroke=S.RULE, rx=6, width=1.2),
           S.text(x + 12, y + 14, "stopband detail (\u00d7 20)", size=9.5,
                  fill=S.MUTED, weight=700),
           S.line(left, floor_y, right, floor_y, stroke=S.INK, width=1.3),
           S.line(left, floor_y, left, ceil_y, stroke=S.INK, width=1.3),
           S.line(left, ceil_y, right, ceil_y, stroke=S.WARN, width=1.2,
                  dash="5 4"),
           S.text(left - 6, ceil_y, "\u03b4~s~", size=10, fill=S.WARN,
                  anchor="end", weight=700),
           S.text(left - 6, floor_y, "0", size=9.5, fill=S.MUTED, anchor="end")]

    points = []
    steps = 240
    for i in range(steps + 1):
        u = i / steps
        ripple = 0.5 * (1 + math.cos(24 * math.pi * u)) * (0.85 + 0.15 * u)
        points.append((left + u * (right - left), floor_y - ripple * (floor_y - ceil_y)))
    out.append(S.polyline(points, stroke=S.ACCENT, width=1.7))
    out.append(S.text((left + right) / 2, floor_y + 15, "f~st~   \u2192   0.5",
                      size=9, fill=S.MUTED, anchor="middle"))
    return "".join(out)


# --------------------------------------------------------------------------- #
# 3. linear-phase symmetry types
# --------------------------------------------------------------------------- #


_SYMMETRY_CASES = (
    ("Type I", "odd N, symmetric", "any response, including highpass",
     [0.10, 0.42, 0.80, 1.00, 0.80, 0.42, 0.10]),
    ("Type II", "even N, symmetric", "no highpass - zero at Nyquist",
     [0.14, 0.50, 0.86, 1.00, 1.00, 0.86, 0.50, 0.14]),
    ("Type III", "odd N, antisymmetric", "differentiators, Hilbert transformers",
     [0.90, 0.62, 0.30, 0.00, -0.30, -0.62, -0.90]),
    ("Type IV", "even N, antisymmetric", "differentiators, Hilbert transformers",
     [0.95, 0.70, 0.38, 0.06, -0.06, -0.38, -0.70, -0.95]),
)


def fir_linear_phase_symmetry() -> str:
    c = S.Canvas(880, 404, title="The four linear-phase FIR types")
    c.heading("Symmetry in h[n] is what makes the phase linear")

    col_x = (40, 470)
    row_y = (62, 222)
    panel_w = 370

    for index, (name, shape, consequence, taps) in enumerate(_SYMMETRY_CASES):
        px = col_x[index % 2]
        py = row_y[index // 2]
        zero_y = py + 74
        amp = 30
        step = panel_w / (len(taps) + 1)

        c.add(S.text(px, py, name, size=12.5, fill=S.INK, weight=700),
              S.text(px + 62, py, shape, size=10.5, fill=S.MUTED),
              S.text(px, py + 17, consequence, size=9.5, fill=S.ACCENT_DARK,
                     style="italic"))

        # the centre of symmetry
        mid = (len(taps) - 1) / 2
        cx = px + 14 + (mid + 1) * step
        c.add(S.line(cx, zero_y - amp - 14, cx, zero_y + amp + 14,
                     stroke=S.RULE, width=1.1, dash="4 4"))

        c.add(S.line(px + 8, zero_y, px + panel_w, zero_y, stroke=S.RULE,
                     width=1.3))
        for j, value in enumerate(taps):
            sx = px + 14 + (j + 1) * step
            sy = zero_y - value * amp
            c.add(S.line(sx, zero_y, sx, sy, stroke=S.ACCENT, width=1.8),
                  S.dot(sx, sy, r=3.4, fill=S.ACCENT, stroke=S.PANEL, width=1.2),
                  S.text(sx, zero_y + 18, str(j), size=8.5, fill=S.MUTED,
                         anchor="middle"))
        c.add(S.text(px + panel_w, zero_y + 18, "n", size=9.5, fill=S.MUTED,
                     anchor="end", style="italic"))

    c.add(S.text(40, 386, "All four give exactly linear phase; they differ only in "
                          "which responses are reachable.", size=11.5,
                 fill=S.SOFT, style="italic"))
    return c.render()


FIGURES = {
    "fir-tapped-delay-line": fir_tapped_delay_line,
    "fir-specification": fir_specification,
    "fir-linear-phase-symmetry": fir_linear_phase_symmetry,
}
