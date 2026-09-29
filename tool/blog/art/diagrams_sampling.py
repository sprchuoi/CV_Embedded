"""Hand-authored diagrams for the sampling and aliasing chapter.

Four figures, in the order the article uses them:

    sampling-frontend-chain        the analogue front end, stage by stage
    aliasing-two-tones             1 Hz and 11 Hz, sampled at 10 Hz: same numbers
    nyquist-zones                  where each band of frequencies folds to
    antialias-before-and-after     why the filter has to come *before* the sampler
"""

from __future__ import annotations

import math

from . import svg as S

TAU = 2 * math.pi


# --------------------------------------------------------------------------- #
# local drawing helpers
# --------------------------------------------------------------------------- #


def _tri(cx, half, height, base, *, stroke, wash, width=1.8, dash=None, opacity=None):
    """A filled triangular spectral lobe centred on ``cx``."""
    d = f"M {S.num(cx - half)} {S.num(base)} L {S.num(cx)} {S.num(base - height)} L {S.num(cx + half)} {S.num(base)} Z"
    return S.path(d, fill=wash, stroke=stroke, width=width, dash=dash, opacity=opacity)


def _hold(values, x0, x1, y_base, amp):
    """Sample-and-hold staircase polyline points."""
    n = len(values)
    step = (x1 - x0) / (n - 1)
    prev = y_base - values[0] * amp
    points = [(x0, prev)]
    for i in range(1, n):
        x = x0 + i * step
        points.append((x - step, prev))
        prev = y_base - values[i] * amp
        points.append((x, prev))
    return points


def _sample_ys(fn, count, y_base, amp):
    return [y_base - fn(i / (count - 1)) * amp for i in range(count)]


# --------------------------------------------------------------------------- #
# 1. the front-end chain
# --------------------------------------------------------------------------- #


def sampling_frontend_chain() -> str:
    c = S.Canvas(880, 330, title="The sampling front end, stage by stage")
    c.heading("The sampling front end - every compromise is on the left")

    stages = [
        ("x(t)", "analogue in", "plain"),
        ("Anti-alias", "LPF, f~c~ < f~s~/2", "warn"),
        ("Track & hold", "aperture t~a~", "plain"),
        ("ADC", "N bits at f~s~", "accent"),
        ("DSP", "x[n] at f~s~", "accent"),
    ]
    x0, width, gap = 27, 130, 44
    sketch_y, sketch_h = 58, 92
    block_y, block_h = 182, 62
    n = len(stages)

    # --- one small sketch per stage, each telling its part of the story ------
    for i in range(n):
        sx = x0 + i * (width + gap)
        c.add(S.rect(sx, sketch_y, width, sketch_h, fill=S.PLOT_BG, stroke=S.RULE_SOFT, rx=6))
        cx0, cx1 = sx + 12, sx + width - 12
        mid = sketch_y + sketch_h / 2
        amp = 26

        if i == 0:
            # signal plus an out-of-band interferer
            c.add(S.wave(lambda u: math.sin(TAU * 2 * u) + 0.32 * math.sin(TAU * 13 * u),
                         cx0, cx1, mid, amplitude=amp, stroke=S.SOFT, width=1.6))
        elif i == 1:
            # band-limited: interferer gone
            c.add(S.wave(lambda u: math.sin(TAU * 2 * u), cx0, cx1, mid,
                         amplitude=amp, stroke=S.ACCENT, width=2))
        elif i == 2:
            # Held: the staircase tracks the sine, ideal curve dashed behind it.
            fn = lambda u: math.sin(TAU * 2 * u)  # noqa: E731
            c.add(S.wave(fn, cx0, cx1, mid, amplitude=amp, stroke=S.RULE,
                         width=1.3, dash="3 3"))
            c.add(S.polyline(_hold([fn(j / 16) for j in range(17)], cx0, cx1, mid, amp),
                             stroke=S.SOFT, width=1.8))
        elif i == 3:
            # Quantised: the same holds, snapped to five levels.
            fn = lambda u: math.sin(TAU * 2 * u)  # noqa: E731
            levels = [round(fn(j / 16) * 3) / 3 for j in range(17)]
            c.add(S.polyline(_hold(levels, cx0, cx1, mid, amp),
                             stroke=S.WARN, width=1.8))
        else:
            fn = lambda u: math.sin(TAU * 2 * u)  # noqa: E731
            step = (cx1 - cx0) / 16
            for j in range(17):
                px = cx0 + j * step
                py = mid - fn(j / 16) * amp
                c.add(S.line(px, mid, px, py, stroke=S.RULE, width=1.2),
                      S.dot(px, py, r=2.8, fill=S.ACCENT))

    # --- the stage boxes and the arrows between them ------------------------
    for i, (title, subtitle, kind) in enumerate(stages):
        sx = x0 + i * (width + gap)
        c.add(S.block(sx, block_y, width, block_h, title, subtitle, kind=kind))
        if i < n - 1:
            c.add(S.arrow(sx + width + 5, block_y + block_h / 2,
                          sx + width + gap - 5, block_y + block_h / 2,
                          stroke=S.MUTED, width=1.6))

    # --- the analogue / digital boundary ------------------------------------
    boundary = x0 + 4 * (width + gap) - gap / 2
    axis_y = 288
    c.add(S.line(x0, axis_y, boundary, axis_y, stroke=S.RULE, width=2, dash="6 5"),
          S.line(boundary, axis_y, x0 + n * width + (n - 1) * gap, axis_y,
                 stroke=S.ACCENT, width=2.4),
          S.dot(boundary, axis_y, r=4.5, fill=S.INK),
          S.line(boundary, block_y + block_h + 6, boundary, axis_y - 6,
                 stroke=S.RULE, width=1.2, dash="3 4"),
          S.text(x0, 310, "continuous time", size=11, fill=S.MUTED, weight=600),
          S.text(x0 + n * width + (n - 1) * gap, 310, "discrete time",
                 size=11, fill=S.ACCENT_DARK, anchor="end", weight=600),
          S.text(boundary, 310, "sampling instant", size=10.5, fill=S.INK,
                 anchor="middle", weight=600))
    return c.render()


# --------------------------------------------------------------------------- #
# 2. two tones, identical samples
# --------------------------------------------------------------------------- #


def aliasing_two_tones() -> str:
    c = S.Canvas(880, 560, title="A 1 Hz and an 11 Hz tone produce the same samples at 10 Hz")
    c.heading("f~s~ = 10 Hz - two different signals, one set of samples")

    x0, x1 = 210, 840
    samples = 11           # n = 0 .. 10, i.e. one second at 10 Hz
    span = x1 - x0
    step = span / (samples - 1)
    amp = 54
    base_a, base_b = 210, 440

    def f_low(u):
        return math.sin(TAU * 1 * u)

    def f_high(u):
        return math.sin(TAU * 11 * u)

    # --- label blocks in the left margin -----------------------------------
    c.add(S.text(20, 200, "f = 1 Hz", size=13, fill=S.ACCENT_DARK, weight=700),
          S.text(20, 220, "below f~s~/2 = 5 Hz", size=10.5, fill=S.MUTED),
          S.text(20, 430, "f = 11 Hz", size=13, fill=S.WARN, weight=700),
          S.text(20, 450, "in the second Nyquist zone", size=10.5, fill=S.MUTED),
          S.text(20, 470, "folds to 11 - 10 = 1 Hz", size=10.5, fill=S.WARN))

    # --- sample connectors: the whole point of the figure ------------------
    low_ys = _sample_ys(f_low, samples, base_a, amp)
    high_ys = _sample_ys(f_high, samples, base_b, amp)
    for j in range(samples):
        px = x0 + j * step
        c.add(S.line(px, low_ys[j], px, high_ys[j], stroke=S.RULE_SOFT,
                     width=1.2, dash="3 5"))

    # --- panel A -----------------------------------------------------------
    c.add(S.line(x0, base_a, x1, base_a, stroke=S.RULE, width=1.4))
    c.add(S.wave(f_low, x0, x1, base_a, amplitude=amp, stroke=S.ACCENT, width=2.4))
    for j in range(samples):
        px = x0 + j * step
        c.add(S.line(px, base_a, px, low_ys[j], stroke=S.ACCENT, width=1.4),
              S.dot(px, low_ys[j], r=4.2, fill=S.ACCENT, stroke=S.PANEL, width=1.6))

    # --- panel B -----------------------------------------------------------
    c.add(S.line(x0, base_b, x1, base_b, stroke=S.RULE, width=1.4))
    c.add(S.wave(f_high, x0, x1, base_b, amplitude=amp, stroke=S.WARN, width=2))
    for j in range(samples):
        px = x0 + j * step
        c.add(S.line(px, base_b, px, high_ys[j], stroke=S.WARN, width=1.4),
              S.dot(px, high_ys[j], r=4.2, fill=S.WARN, stroke=S.PANEL, width=1.6))

    # --- shared time axis --------------------------------------------------
    axis_y = 508
    c.add(S.line(x0, axis_y, x1, axis_y, stroke=S.RULE, width=1.4))
    for j in (0, 5, 10):
        px = x0 + j * step
        c.add(S.line(px, axis_y, px, axis_y + 5, stroke=S.RULE),
              S.text(px, axis_y + 17, f"{j / 10:.1f} s", size=10.5, fill=S.MUTED,
                     anchor="middle"))
    c.add(S.text(x1 + 10, axis_y + 17, "t", size=11.5, fill=S.SOFT,
                 weight=600, style="italic"))

    c.add(S.text(x0, 546, "Same eleven numbers. No algorithm can recover which "
                          "signal was really there.", size=11.5, fill=S.SOFT,
                 style="italic"))
    return c.render()


# --------------------------------------------------------------------------- #
# 3. Nyquist zones
# --------------------------------------------------------------------------- #

_ZONE_FILLS = (S.ACCENT_WASH, S.PLOT_BG, S.PLOT_BG, S.PLOT_BG)


def _zone_axis(c, x0, x1, axis_y, *, band_h=30):
    """A frequency line with the four Nyquist zones drawn beneath it.

    Each row carries its own zone strip: with two worked examples stacked, the
    reader never has to guess which band a marker belongs to.
    """
    half = (x1 - x0) / 4.0
    for i, fill in enumerate(_ZONE_FILLS):
        c.add(S.rect(x0 + i * half, axis_y, half, band_h, fill=fill, stroke=None, rx=0))
    c.add(S.rect(x0, axis_y, x1 - x0, band_h, fill="none", stroke=S.RULE, rx=0, width=1.2))
    for i in range(1, 4):
        c.add(S.line(x0 + i * half, axis_y, x0 + i * half, axis_y + band_h,
                     stroke=S.RULE, width=1.1))
    for i, name in enumerate("1234"):
        c.add(S.text(x0 + (i + 0.5) * half, axis_y + band_h / 2 + 1, name, size=11.5,
                     fill=S.ACCENT_DARK if i == 0 else S.MUTED,
                     anchor="middle", weight=700))

    tick_y = axis_y + band_h
    c.add(S.line(x0, axis_y, x1, axis_y, stroke=S.INK, width=1.6))
    for i in range(5):
        tx = x0 + i * half
        c.add(S.line(tx, tick_y, tx, tick_y + 6, stroke=S.INK, width=1.3),
              S.text(tx, tick_y + 20, ["0", "½f~s~", "f~s~", "1½f~s~", "2f~s~"][i],
                     size=10.5, fill=S.SOFT, anchor="middle", weight=600))


def _fold_example(c, x0, x1, axis_y, *, true_mult, alias_mult, color, title):
    """One worked fold: a tone in a higher zone and the image it lands on."""
    def fx(multiple):
        return x0 + multiple * (x1 - x0) / 4.0

    tx, ax = fx(true_mult), fx(alias_mult)
    apex = axis_y - 56

    c.add(S.text(x0, axis_y - 96, title, size=12, fill=color, weight=700))
    _zone_axis(c, x0, x1, axis_y)
    c.add(S.path(f"M {S.num(tx)} {S.num(axis_y - 6)} "
                 f"Q {S.num((tx + ax) / 2)} {S.num(apex)} "
                 f"{S.num(ax)} {S.num(axis_y - 6)}",
                 stroke=color, width=1.9, marker_end="url(#arrow)"),
          S.dot(tx, axis_y, r=4.2, fill=color, stroke=S.PANEL, width=1.6),
          S.dot(ax, axis_y, r=4.2, fill=color, stroke=S.PANEL, width=1.6),
          # Names sit on opposite sides of the arc, which is what keeps the
          # two-three label collision in this figure from happening at all.
          S.text(tx + 9, axis_y - 15, f"{true_mult:.2f} f~s~", size=11,
                 fill=color, anchor="start", weight=700),
          S.text(ax - 9, axis_y - 15, f"{alias_mult:.2f} f~s~", size=11,
                 fill=color, anchor="end", weight=700),
          S.text((tx + ax) / 2, apex - 12, "folds", size=10.5, fill=color,
                 anchor="middle"))


def nyquist_zones() -> str:
    c = S.Canvas(880, 420, title="Nyquist zones and how each one folds back onto the first")
    c.heading("Nyquist zones - every band folds back onto the first")
    x0, x1 = 70, 850

    _fold_example(c, x0, x1, 152, true_mult=0.70, alias_mult=0.30,
                  color=S.ACCENT_DARK,
                  title="A 0.70 f~s~ tone sits in Zone 2")
    _fold_example(c, x0, x1, 332, true_mult=1.40, alias_mult=0.40,
                  color=S.OPTICAL,
                  title="A 1.40 f~s~ tone sits in Zone 3")
    c.add(S.text(x0, 404, "Zones 2, 3 and 4 are not empty - the sampler folds "
                          "every one of them onto Zone 1.", size=11.5,
                 fill=S.SOFT, style="italic"))
    return c.render()


# --------------------------------------------------------------------------- #
# 4. anti-alias filtering
# --------------------------------------------------------------------------- #


def antialias_before_and_after() -> str:
    c = S.Canvas(880, 500, title="Why the anti-alias filter must precede the sampler")
    c.heading("The filter must act before the sampler, not after")

    x0, x1 = 70, 840
    full = (x1 - x0) / 2.0                 # one f~s~ in pixels

    def fx(multiple):
        return x0 + multiple * full

    def spectrum_axis(base_y, *, nyquist=True):
        out = [S.line(x0, base_y, x1, base_y, stroke=S.INK, width=1.5)]
        for multiple, label in ((0, "0"), (0.5, "½f~s~"), (1.0, "f~s~"),
                                (1.5, "1½f~s~"), (2.0, "2f~s~")):
            tx = fx(multiple)
            out += [S.line(tx, base_y, tx, base_y + 5, stroke=S.INK, width=1.2),
                    S.text(tx, base_y + 18, label, size=10, fill=S.MUTED,
                           anchor="middle")]
        if nyquist:
            # Labelled down its own side, so the text never crosses a curve.
            ny = fx(0.5)
            out += [S.line(ny, base_y - 84, ny, base_y, stroke=S.WARN, width=1.3,
                           dash="5 4"),
                    S.text(ny - 9, base_y - 44, "Nyquist limit", size=9.5,
                           fill=S.WARN, anchor="middle", weight=700, rotate=-90)]
        return "".join(out)

    # ---------------- row 1: no filter -------------------------------------
    base1 = 196
    c.add(S.text(x0, 60, "Without an anti-alias filter", size=12.5, fill=S.WARN,
                 weight=700),
          spectrum_axis(base1),
          _tri(fx(0.12), 34, 66, base1, stroke=S.ACCENT, wash=S.ACCENT_WASH),
          S.text(fx(0.12), 118, "wanted", size=10.5, fill=S.ACCENT_DARK,
                 anchor="middle", weight=700),
          _tri(fx(1.40), 34, 66, base1, stroke=S.WARN, wash=S.WARN_WASH),
          S.text(fx(1.40), 118, "interferer", size=10.5, fill=S.WARN,
                 anchor="middle", weight=700),
          # the image the sampler creates, folded into Zone 1
          _tri(fx(0.40), 34, 66, base1, stroke=S.WARN, wash="none", dash="5 4"),
          S.text(fx(0.40), 236, "alias of the interferer", size=10.5, fill=S.WARN,
                 anchor="middle", weight=700),
          S.path(f"M {S.num(fx(1.40))} 100 Q {S.num((fx(1.40) + fx(0.40)) / 2)} 40 "
                 f"{S.num(fx(0.40))} 120",
                 stroke=S.WARN, width=1.7, dash="5 4", marker_end="url(#arrow)"))

    # ---------------- row 2: with filter -----------------------------------
    base2 = 406
    c.add(S.text(x0, 280, "With an anti-alias filter in front of the sampler",
                 size=12.5, fill=S.ACCENT_DARK, weight=700),
          spectrum_axis(base2, nyquist=False),
          _tri(fx(0.12), 34, 66, base2, stroke=S.ACCENT, wash=S.ACCENT_WASH),
          S.text(fx(0.12), 328, "wanted", size=10.5, fill=S.ACCENT_DARK,
                 anchor="middle", weight=700),
          _tri(fx(1.40), 34, 8, base2, stroke=S.RULE, wash=S.RULE_SOFT),
          S.text(fx(0.40), 446, "nothing folds in here", size=10.5, fill=S.MUTED,
                 anchor="middle"),
          S.text(fx(1.40), 446, "attenuated - cannot fold", size=10.5,
                 fill=S.MUTED, anchor="middle"))

    # the filter's own magnitude response, drawn over row 2
    points = []
    for i in range(161):
        multiple = 2.0 * (i / 160.0)
        if multiple <= 0.34:
            magnitude = 1.0
        elif multiple >= 0.62:
            magnitude = 0.03
        else:
            t = (multiple - 0.34) / (0.62 - 0.34)
            magnitude = 1.0 - 0.97 * (t * t * (3 - 2 * t))    # smoothstep
        points.append((fx(multiple), base2 - 30 - magnitude * 74))
    c.add(S.polyline(points, stroke=S.OPTICAL, width=2.2, dash="7 4"),
          S.text(fx(1.30), 284, "anti-alias filter response", size=10.5,
                 fill=S.OPTICAL, anchor="middle", weight=700))

    c.add(S.text(x0, 486, "Fold the interferer first and no later filter can tell "
                          "it apart from the wanted signal.", size=11.5,
                 fill=S.SOFT, style="italic"))
    return c.render()


FIGURES = {
    "sampling-frontend-chain": sampling_frontend_chain,
    "aliasing-two-tones": aliasing_two_tones,
    "nyquist-zones": nyquist_zones,
    "antialias-before-and-after": antialias_before_and_after,
}
