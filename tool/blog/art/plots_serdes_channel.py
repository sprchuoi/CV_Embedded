"""Computed figures for the SerDes channel and link-budget chapter.

    serdes-channel-loss      the channel against the interface mask it has to
                             meet, at each band edge
    lane-crosstalk-scaling   coupling against pitch, and what it costs at the
                             slicer

The channel model is the same square-root-of-frequency shape the Ethernet part
uses, moved four to forty times up in frequency. What changes at these rates is
that crosstalk, not loss, becomes the term that fails first.
"""

from __future__ import annotations

import numpy as np

from . import plotstyle as P

# (name, band edge GHz, allowed loss dB, reach mm)
MASKS = [
    ("CEI-25G-LR", 12.5, 20.0, 500.0),
    ("CEI-56G-VSR", 14.0, 15.0, 120.0),
    ("CEI-56G-MR", 14.0, 26.0, 500.0),
    ("100G/lane VSR", 26.6, 15.0, 120.0),
]


def serdes_channel_loss() -> str:
    fig, ax = P.figure(height=4.0)
    P.title(ax, "SerDes channel loss against the interface masks",
            subtitle="loss rises as the square root of frequency; each mask "
                     "constrains a different band edge and reach")

    f = np.linspace(0.1, 30.0, 800)
    colours = [P.ACCENT, P.NOTE, P.WARN, P.OPTICAL]
    for (name, edge, loss, reach), colour in zip(MASKS, colours):
        curve = loss * np.sqrt(np.maximum(f, 1e-3) / edge)
        ax.plot(f, -curve, color=colour, lw=2.2, label=f"{name} ({reach:g} mm)")
        ax.plot([edge], [-loss], marker="o", ms=7, color=colour,
                markeredgecolor=P.PANEL, markeredgewidth=1.3, zorder=6)

    # the two band edges the whole figure is organised around
    for edge, label in ((14.0, "28 GBd PAM4\nNyquist"), (26.6, "53 GBd PAM4\nNyquist")):
        ax.axvline(edge, color=P.MUTED, lw=1.2, ls=(0, (5, 4)), zorder=2)
        ax.text(edge, -1.0, f" {label}", fontsize=8.4, color=P.MUTED,
                va="top", weight="bold")

    P.tidy(ax, xlabel="frequency (GHz)", ylabel="insertion loss (dB)",
           legend=True, legend_loc="lower right")
    ax.set_xlim(0, 30)
    ax.set_ylim(-40, 2)
    return P.render(fig)


def lane_crosstalk_scaling() -> str:
    fig, axes = P.figure(height=3.7, ncols=2)
    ax0, ax1 = axes

    # --- left: coupling against pitch ---
    pitch = np.linspace(0.20, 1.60, 300)          # mm, trace-centre spacing
    # Coupling falls with the square of the spacing at these geometries, and a
    # pair at 0.20 mm coupling couples about -18 dB.
    coupling_db = -18.0 - 40.0 * np.log10(pitch / 0.20)
    ax0.plot(pitch, coupling_db, color=P.WARN, lw=2.6)
    for p, label in ((0.25, "dense escape"), (0.60, "typical"),
                     (1.20, "wide pitch")):
        value = float(np.interp(p, pitch, coupling_db))
        ax0.plot([p], [value], marker="o", ms=8, color=P.WARN,
                 markeredgecolor=P.PANEL, markeredgewidth=1.4, zorder=6)
        ax0.annotate(f"{value:.0f} dB\n{label}", xy=(p, value),
                     xytext=(6, 8), textcoords="offset points", fontsize=8.4,
                     color=P.WARN, weight="bold")
    P.title(ax0, "Coupling against trace pitch",
            subtitle="differential pairs, no shielding, at the band edge")
    P.tidy(ax0, xlabel="centre-to-centre pitch (mm)", ylabel="coupled power (dB)")
    ax0.set_ylim(-52, -12)

    # --- right: the same coupling as an SNR cost at the slicer ---
    aggressors = np.arange(0, 8)
    for level, colour, label in ((1.0, P.ACCENT, "-18 dB per aggressor"),
                                 (2.0, P.WARN, "-15 dB per aggressor")):
        per = level * 12.0
        # N equal uncorrelated aggressors add in power
        total = per + 10.0 * np.log10(np.maximum(aggressors, 1e-9))
        total[0] = 0.0
        ax1.plot(aggressors, total, color=colour, lw=2.4, marker="o", ms=5,
                 markeredgecolor=P.PANEL, markeredgewidth=1.2, label=label)
    P.title(ax1, "Adding aggressors costs decibels",
            subtitle="uncorrelated crosstalk adds in power, so it is 3 dB "
                     "for the second aggressor")
    P.tidy(ax1, xlabel="number of adjacent lanes driven", ylabel="SNR lost (dB)",
           legend=True, legend_loc="upper left")
    ax1.set_xlim(0, 7)
    ax1.set_ylim(0, 22)
    return P.render(fig)


FIGURES = {
    "serdes-channel-loss": serdes_channel_loss,
    "lane-crosstalk-scaling": lane_crosstalk_scaling,
}
