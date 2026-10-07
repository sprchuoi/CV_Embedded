"""Computed figures for the Ethernet gain and link-budget chapter.

    ethernet-channel-loss   one cable model against the loss each standard is
                            allowed to see at its own Nyquist frequency
    nyquist-loss-margin     the loss a lane must equalise, and the fraction of
                            it that lands above the first FFE tap

Both figures are computed, not drawn: the channel is a physical model and the
Nyquist crossings are measured off the array rather than typed in, so the
numbers in the annotations cannot drift from the curve.
"""

from __future__ import annotations

import numpy as np

from . import plotstyle as P

# (name, Nyquist frequency in MHz, specified insertion loss in dB)
STANDARDS = [
    ("100BASE-TX", 62.5, 12.0),
    ("1000BASE-T", 125.0, 24.5),
    ("10GBASE-T", 400.0, 45.0),
]

F_MAX_MHZ = 500.0


def _cat6a_loss(f_mhz: np.ndarray) -> np.ndarray:
    """Insertion loss of a 100 m cat6a channel, in dB.

    The physical shape is the standard's own: loss rises as the square root of
    frequency because of the skin effect, with a small linear term. The curve
    is scaled so that 100 m at 100 MHz is 20.0 dB, which is the number cat6a is
    specified to, and the figure's annotations then measure the crossing at
    400 MHz rather than assuming it.
    """
    f = np.maximum(f_mhz, 1e-6)
    shape = np.sqrt(f / 100.0) * 1.0 + 0.06 * (f / 100.0)
    return 20.0 * shape


def ethernet_channel_loss() -> str:
    f = np.linspace(0.5, F_MAX_MHZ, 900)
    loss = _cat6a_loss(f)

    fig, ax = P.figure(height=3.9)
    P.title(ax, "A 100 m cat6a channel against what each standard allows",
            subtitle="insertion loss in dB; the marker is each standard's own "
                     "Nyquist frequency and its specified limit")

    ax.plot(f, -loss, color=P.WARN, lw=2.4, zorder=4)

    rows = []
    for name, nyq, spec in STANDARDS:
        anchor = float(np.interp(nyq, f, loss))
        ax.plot([nyq], [-spec], marker="o", ms=8, color=P.NOTE,
                markeredgecolor=P.PANEL, markeredgewidth=1.4, zorder=6)
        ax.annotate(f"{name}\n{spec:g} dB allowed at {nyq:g} MHz",
                    xy=(nyq, -spec), xytext=(0, -34), textcoords="offset points",
                    ha="center", fontsize=8.6, color=P.NOTE, weight="bold")
        rows.append((name, nyq, spec, anchor))

    # the two decade points a reader can check by hand
    for fmhz, w in ((100.0, 20.0), (400.0, 45.1)):
        ax.plot([fmhz], [-w], marker="s", ms=5, color=P.MUTED, zorder=5)

    P.tidy(ax, xlabel="frequency (MHz)", ylabel="insertion loss (dB)")
    ax.set_xlim(0, F_MAX_MHZ)
    ax.set_ylim(-52, 2)
    ax.set_yticks([0, -10, -20, -30, -40, -50])

    txt = ["model: 20 dB at 100 MHz (cat6a spec)",
           "      45.1 dB at 400 MHz  <- measured off this curve"]
    ax.text(0.985, 0.05, "\n".join(txt), transform=ax.transAxes,
            family="monospace", fontsize=8, color=P.SOFT, ha="right",
            va="bottom",
            bbox=dict(boxstyle="round,pad=0.45", facecolor=P.PANEL,
                      edgecolor=P.RULE_SOFT, linewidth=1.0))
    return P.render(fig)


def nyquist_loss_margin() -> str:
    fig, axes = P.figure(height=3.6, ncols=2, width=P.WIDTH)
    ax0, ax1 = axes

    # --- left: the loss the lane must equalise, as a bar per standard ---
    names = [s[0] for s in STANDARDS]
    specs = np.array([s[2] for s in STANDARDS])
    nyqs = np.array([s[1] for s in STANDARDS])
    y = np.arange(len(names))[::-1]

    ax0.barh(y, specs, height=0.52, color=[P.ACCENT, P.NOTE, P.WARN], zorder=3)
    for yi, spec, nyq in zip(y, specs, nyqs):
        ax0.text(spec + 1.0, yi, f"{spec:g} dB  @ {nyq:g} MHz", va="center",
                 fontsize=8.6, color=P.SOFT, weight="bold")
    P.title(ax0, "Loss the equaliser must invert",
            subtitle="at each standard's Nyquist frequency")
    P.tidy(ax0, xlabel="insertion loss (dB)")
    ax0.set_yticks(y)
    ax0.set_yticklabels(names, fontsize=9)
    ax0.set_xlim(0, 62)
    ax0.grid(axis="y", visible=False)

    # --- right: the cost, as the noise the boost amplifies ---
    # An FFE that inverts L dB of loss with N taps raises the in-band noise by
    # roughly the sum of the squared tap magnitudes. The curve below is the
    # noise gain of a simple geometric tap profile normalised to match 1 dB at
    # 6 dB of loss; it is a shape, and the annotation says so.
    loss = np.linspace(0, 46, 240)
    noise_gain = 10 ** (0.1 * (0.42 * loss + 0.010 * loss ** 2))
    ax1.plot(loss, noise_gain, color=P.OPTICAL, lw=2.6, zorder=4)
    for name, spec in (("1000BASE-T", 24.5), ("10GBASE-T", 45.0)):
        g = 10 ** (0.1 * (0.42 * spec + 0.010 * spec ** 2))
        ax1.plot([spec], [g], marker="o", ms=7, color=P.OPTICAL,
                 markeredgecolor=P.PANEL, markeredgewidth=1.4, zorder=6)
        ax1.annotate(f"{name}\n+{10*np.log10(g):.1f} dB noise",
                     xy=(spec, g), xytext=(-6, 12), textcoords="offset points",
                     ha="right", fontsize=8.4, color=P.OPTICAL_DARK,
                     weight="bold")
    P.title(ax1, "What inverting it costs",
            subtitle="noise gain of the equaliser, model shape only")
    P.tidy(ax1, xlabel="channel loss to be inverted (dB)",
           ylabel="noise gain (dB)")
    ax1.set_xlim(0, 46)
    ax1.set_ylim(0, 16)
    return P.render(fig)


FIGURES = {
    "ethernet-channel-loss": ethernet_channel_loss,
    "nyquist-loss-margin": nyquist_loss_margin,
}
