"""Computed figure for the compliance-test chapter.

    compliance-eye-margins   measured eye parameters against the limits they are
                             compared with, and the margin each one leaves

The point of the figure is that a pass/fail report is a *set* of comparisons,
and that the set almost never fails uniformly: one parameter is comfortable,
another is a few per cent from the line, and the report does not distinguish
between them unless you plot it.
"""

from __future__ import annotations

import numpy as np

from . import plotstyle as P

# (parameter, measured value, limit, unit, which side is good)
# A representative 10GBASE-KR port at the end of a compliance run. The numbers
# are illustrative; the structure -- one comfortable parameter, one marginal,
# one failing -- is the point.
ROWS = [
    ("eye height", 82.0, 60.0, "mV", "higher", True),
    ("eye width", 0.34, 0.30, "UI", "higher", True),
    ("total jitter", 0.29, 0.30, "UI", "lower", True),
    ("vertical eye opening", 46.0, 50.0, "mV", "higher", False),
    ("differential return loss", 11.5, 10.0, "dB", "higher", True),
]


def compliance_eye_margins() -> str:
    fig, axes = P.figure(height=3.6, ncols=2)
    ax0, ax1 = axes

    names = [r[0] for r in ROWS]
    y = np.arange(len(ROWS))[::-1]

    # --- left: measured against limit, normalised so limit = 1.0 ---
    for yi, (name, val, lim, unit, _side, ok) in zip(y, ROWS):
        ratio = val / lim
        colour = P.ACCENT if ok else P.WARN
        ax0.barh(yi, 1.0, height=0.52, color=P.RULE_SOFT, zorder=2)
        ax0.barh(yi, ratio, height=0.52, color=colour, zorder=3)
        ax0.text(max(ratio, 1.0) + 0.06, yi,
                 f"{val:g} {unit}   (limit {lim:g})", va="center", fontsize=8.4,
                 color=colour, weight="bold")
    ax0.axvline(1.0, color=P.INK, lw=1.6, zorder=4)
    ax0.text(1.0, len(ROWS) - 0.35, " limit", fontsize=8.6, color=P.INK,
             weight="bold", va="center")
    P.title(ax0, "Measured against limit",
            subtitle="each bar normalised so the limit is 1.0")
    P.tidy(ax0, xlabel="measured / limit")
    ax0.set_yticks(y)
    ax0.set_yticklabels(names, fontsize=9)
    ax0.set_xlim(0, 1.85)
    ax0.grid(axis="y", visible=False)

    # --- right: the margin, in the units that matter per parameter ---
    margins = []
    for name, val, lim, unit, side, ok in ROWS:
        margin = (val - lim) / lim * 100.0 if side == "higher" else \
                 (lim - val) / lim * 100.0
        margins.append((name, margin, unit, ok))

    for yi, (name, margin, unit, ok) in zip(y, margins):
        colour = P.ACCENT if margin >= 0 else P.WARN
        ax1.barh(yi, margin, height=0.52, color=colour, zorder=3)
        offset = 3.0 if margin >= 0 else -3.0
        ha = "left" if margin >= 0 else "right"
        ax1.text(margin + offset, yi, f"{margin:+.0f}%", va="center", ha=ha,
                 fontsize=8.4, color=colour, weight="bold")
    ax1.axvline(0.0, color=P.INK, lw=1.6, zorder=4)
    P.title(ax1, "Margin left, per parameter",
            subtitle="positive passes; the failing one is negative")
    P.tidy(ax1, xlabel="margin (%)")
    ax1.set_yticks(y)
    ax1.set_yticklabels([])
    ax1.set_xlim(-30, 55)
    ax1.grid(axis="y", visible=False)

    return P.render(fig)


FIGURES = {
    "compliance-eye-margins": compliance_eye_margins,
}
