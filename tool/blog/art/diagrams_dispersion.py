"""Hand-authored diagrams for the chromatic dispersion chapter.

    dispersion-pulse-broadening   why a short pulse arrives long and chirped
    dispersion-block-window       why the FDE block must exceed the dispersion memory
"""

from __future__ import annotations

import math

from . import svg as S

# Accumulated dispersion at D = 17 ps/(nm.km) -- the figure of merit quoted
# throughout the blog's optical chapters.
D_PS_NM_KM = 17


def _mix(a: str, b: str, t: float) -> str:
    """Linear interpolation between two ``#rrggbb`` colours."""
    t = max(0.0, min(1.0, t))
    ca = tuple(int(a[i:i + 2], 16) for i in (1, 3, 5))
    cb = tuple(int(b[i:i + 2], 16) for i in (1, 3, 5))
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(ca, cb))


def _envelope_path(cx, base_y, half_width, height, sigma, samples=80):
    """A Gaussian envelope as a closed path centred on ``cx``."""
    top, bottom = [], []
    for i in range(samples + 1):
        u = -3.2 + 6.4 * i / samples
        x = cx + u * half_width / 3.2
        y = base_y - math.exp(-0.5 * (u / sigma) ** 2) * height
        top.append((x, y))
        bottom.append((x, base_y))
    points = top + list(reversed(bottom))
    d = "M " + " L ".join(f"{S.num(x)} {S.num(y)}" for x, y in points) + " Z"
    return d


# --------------------------------------------------------------------------- #
# 1. pulse broadening along the fibre
# --------------------------------------------------------------------------- #


def dispersion_pulse_broadening() -> str:
    note = [
        "Each frequency travels at a slightly different speed, so a short pulse "
        "comes out long and frequency-swept.",
        "The energy is unchanged - |H(f)| = 1 exactly - which is why this is "
        "fixable by phase alone.",
    ]
    callout_y = 352
    height = int(callout_y + S.callout_height(840, note, body_size=11.5)
                 + 14)

    c = S.Canvas(880, height,
                 title="A pulse broadening and chirping along 100 km of fibre")
    c.heading("Dispersion is all-pass: the pulse spreads, nothing is absorbed")

    spans = [(0, 1.0), (50, 2.9), (100, 5.6)]
    row_h = 96
    top = 52
    cx, half, peak = 500, 210, 34

    for index, (distance, sigma) in enumerate(spans):
        py = top + index * row_h
        base = py + 58
        accumulated = distance * D_PS_NM_KM

        c.add(S.rect(20, py, 840, row_h - 8, fill=S.PLOT_BG, stroke=S.RULE_SOFT,
                     rx=6),
              S.text(36, py + 24, f"{distance} km", size=12, fill=S.INK,
                     weight=700),
              S.text(36, py + 42,
                     f"{accumulated} ps/nm" if accumulated else "no dispersion yet",
                     size=9.5, fill=S.MUTED),
              S.line(112, base, 846, base, stroke=S.RULE, width=1.2))

        # A blue-to-orange sweep across the envelope stands in for the chirp:
        # low frequencies arrive first, high frequencies last.
        segments = 30
        for seg in range(segments):
            u0 = -3.2 + 6.4 * seg / segments
            u1 = -3.2 + 6.4 * (seg + 1) / segments
            y0 = base - math.exp(-0.5 * (u0 / sigma) ** 2) * peak
            y1 = base - math.exp(-0.5 * (u1 / sigma) ** 2) * peak
            colour = _mix(S.NOTE, S.WARN, (seg + 0.5) / segments)
            c.add(S.path(f"M {S.num(cx + u0 * half / 3.2)} {S.num(y0)} "
                         f"L {S.num(cx + u1 * half / 3.2)} {S.num(y1)}",
                         stroke=colour, width=2.8))

        if index:
            c.add(S.text(cx, base - peak - 12, f"\u00d7{sigma:.1f} broader",
                         size=9.5, fill=S.MUTED, anchor="middle"))

    c.add(S.text(112, top + row_h - 22, "low frequencies", size=9, fill=S.NOTE,
                 weight=600),
          S.text(806, top + row_h - 22, "high frequencies", size=9, fill=S.WARN,
                 anchor="end", weight=600),
          S.callout(20, callout_y, 840, "The chirp is the whole problem", note,
                    kind="optical"))
    return c.render()


# --------------------------------------------------------------------------- #
# 2. why the block size matters
# --------------------------------------------------------------------------- #


def dispersion_block_window() -> str:
    c = S.Canvas(880, 386, title="Overlap-save block size against dispersion memory")
    c.heading("The block must be longer than the memory, or the wrap corrupts it")

    cases = [
        ("block \u226a memory", "circular wrap lands inside the block",
         S.WARN, 0.28, "the tail wraps around and adds to the front"),
        ("block \u2248 memory", "the whole response fits",
         S.ACCENT, 0.92, "one block holds the entire impulse response"),
        ("block \u226b memory", "correct, but later than it needs to be",
         S.NOTE, 1.0, "extra samples are pure latency and cost"),
    ]

    panel_w, panel_h = 264, 214
    for index, (title, subtitle, colour, window_frac, note) in enumerate(cases):
        px = 22 + index * (panel_w + 22)
        py = 52
        base = py + 156
        c.add(S.rect(px, py, panel_w, panel_h, fill=S.PLOT_BG, stroke=S.RULE_SOFT,
                     rx=6),
              S.text(px + 14, py + 22, title, size=11.5, fill=colour,
                     weight=700),
              S.text(px + 14, py + 39, subtitle, size=9, fill=S.MUTED))

        # The dispersion impulse response: long, chirped, and slowly decaying.
        span = panel_w - 40
        for tick in range(46):
            u = tick / 45
            x = px + 20 + u * span
            height = math.exp(-u * 2.1) * 46 + 4
            c.add(S.line(x, base, x, base - height,
                         stroke=_mix(S.ACCENT, S.ACCENT_WASH, u * 0.75),
                         width=1.6))

        # The block window the FDE actually uses.
        win_w = span * window_frac
        win_x = px + 20 + (span - win_w) / 2
        c.add(S.rect(win_x, base - 66, win_w, 66, fill="none", stroke=colour,
                     rx=3, width=1.8, dash="5 3"),
              S.text(win_x + win_w / 2, base - 78, "block", size=9.5,
                     fill=colour, anchor="middle", weight=700))

        c.add(S.text(px + 14, base + 22, "impulse response of H*(f)", size=8.5,
                     fill=S.MUTED),
              S.text(px + 14, base + 40, note, size=9, fill=S.SOFT,
                     style="italic"))

    c.add(S.callout(22, 286, 836, "The design rule this picture gives you",
                    ["Set the overlap-save block longer than the dispersion memory. "
                     "Below that the circular convolution folds the tail of the "
                     "response into the front of the block and no coefficient "
                     "choice can repair it.",
                     "Above it you are only buying latency: the extra samples sit "
                     "in a buffer doing nothing."],
                    kind="accent"))
    return c.render()


FIGURES = {
    "dispersion-pulse-broadening": dispersion_pulse_broadening,
    "dispersion-block-window": dispersion_block_window,
}
