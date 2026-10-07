"""Computed figures for the SerDes-in-a-module chapter.

    host-lane-response   what the host edge's channel does to a 26 GHz lane, at
                         each interface generation's band edge
    module-power         power per lane and per bit, which is the constraint that
                         decides retimed versus gearbox

Both figures exist to make one point: the host edge is where a module's budget
is spent, and it has been getting worse with every generation.
"""

from __future__ import annotations

import numpy as np

from . import plotstyle as P

# (name, per-lane rate Gbit/s, signalling, band edge GHz, allowed loss dB)
LANES = [
    ("10G NRZ", 10.0, "NRZ", 5.0, 20.0),
    ("25G NRZ", 25.0, "NRZ", 12.5, 26.0),
    ("50G PAM4", 50.0, "PAM4", 13.3, 26.0),
    ("100G PAM4", 100.0, "PAM4", 26.6, 28.0),
]


def _channel_loss(f_ghz: np.ndarray, loss_at_edge: float,
                  edge_ghz: float) -> np.ndarray:
    """A PCB channel: loss grows as the square root of frequency.

    Normalised so the curve passes through ``loss_at_edge`` at ``edge_ghz``,
    which is what the interface specification actually constrains.
    """
    f = np.maximum(f_ghz, 1e-3)
    return loss_at_edge * np.sqrt(f / edge_ghz)


def host_lane_response() -> str:
    fig, axes = P.figure(height=4.0, ncols=2)
    ax0, ax1 = axes

    f = np.linspace(0.1, 30.0, 700)
    for (name, rate, sig, edge, loss), colour in zip(LANES,
                                                     [P.ACCENT, P.NOTE,
                                                      P.WARN, P.OPTICAL]):
        curve = _channel_loss(f, loss, edge)
        ax0.plot(f, -curve, color=colour, lw=2.2, label=name)
        ax0.plot([edge], [-loss], marker="o", ms=7, color=colour,
                 markeredgecolor=P.PANEL, markeredgewidth=1.3, zorder=6)
        ax0.annotate(f"{loss:g} dB\n@ {edge:g} GHz", xy=(edge, -loss),
                     xytext=(4, -30), textcoords="offset points", fontsize=8.2,
                     color=colour, weight="bold")
    P.title(ax0, "Host-edge channel loss",
            subtitle="a model normalised to each interface's own band edge")
    P.tidy(ax0, xlabel="frequency (GHz)", ylabel="insertion loss (dB)",
           legend=True, legend_loc="lower right")
    ax0.set_xlim(0, 30)
    ax0.set_ylim(-40, 0)

    # --- right: loss against per-lane rate, the trend line ---
    rates = np.array([l[1] for l in LANES])
    losses = np.array([l[4] for l in LANES])
    edges = np.array([l[3] for l in LANES])
    ax1.plot(rates, losses, color=P.WARN, lw=2.2, marker="o", ms=7,
             markeredgecolor=P.PANEL, markeredgewidth=1.3, zorder=5)
    for name, r, lo, e in zip([l[0] for l in LANES], rates, losses, edges):
        ax1.annotate(f"{name}\n{e:g} GHz edge", xy=(r, lo),
                     xytext=(0, 12), textcoords="offset points", fontsize=8.2,
                     color=P.SOFT, ha="center")
    P.title(ax1, "The loss each generation accepts",
            subtitle="allowed insertion loss at the band edge, per lane")
    P.tidy(ax1, xlabel="per-lane rate (Gbit/s)", ylabel="allowed loss (dB)")
    ax1.set_xlim(0, 115)
    ax1.set_ylim(15, 33)
    return P.render(fig)


def module_power() -> str:
    fig, ax = P.figure(height=3.7)
    P.title(ax, "Power per lane, and why the middle of a module matters",
            subtitle="representative SerDes and DSP figures; the crossing is "
                     "the argument, not the absolute numbers")

    per_lane = np.array([1.0, 5.0, 25.0, 50.0, 100.0])
    # SerDes: roughly linear in rate, a little better per bit as it matures
    serdes = np.array([0.06, 0.075, 0.11, 0.16, 0.24])
    # retiming DSP: dominated by FEC and the datapath, sub-linear in rate
    dsp = np.array([0.0, 0.02, 0.06, 0.10, 0.16])
    # lane conversion (gearbox): much cheaper than full retiming
    gearbox = np.array([0.0, 0.01, 0.025, 0.04, 0.06])

    ax.plot(per_lane, serdes, color=P.NOTE, lw=2.4, marker="o", ms=6,
            markeredgecolor=P.PANEL, markeredgewidth=1.3,
            label="SerDes lane itself")
    ax.plot(per_lane, dsp, color=P.OPTICAL, lw=2.4, marker="s", ms=6,
            markeredgecolor=P.PANEL, markeredgewidth=1.3,
            label="full retiming + FEC")
    ax.plot(per_lane, gearbox, color=P.ACCENT, lw=2.4, marker="^", ms=6,
            markeredgecolor=P.PANEL, markeredgewidth=1.3,
            label="gearbox only")

    for name, series, colour in (("SerDes", serdes, P.NOTE),
                                 ("retimed", dsp, P.OPTICAL),
                                 ("gearbox", gearbox, P.ACCENT)):
        total = float(serdes[-1] + series[-1])
        ax.annotate(f"{name}: {total:.2f} W", xy=(per_lane[-1], total),
                    xytext=(-6, 8), textcoords="offset points", fontsize=8.4,
                    color=colour, weight="bold", ha="right")

    P.tidy(ax, xlabel="per-lane rate (Gbit/s)", ylabel="power per lane (W)",
           legend=True, legend_loc="upper left")
    ax.set_xlim(0, 108)
    ax.set_ylim(0, 0.46)
    return P.render(fig)


FIGURES = {
    "host-lane-response": host_lane_response,
    "module-power": module_power,
}
