"""Computed figures for the clock-recovery and jitter chapter.

    jitter-decomposition-plot   one jitter histogram separated into its random
                                and deterministic parts
    cdr-loop-bandwidth          the bandwidth trade, measured as tracking error
                                against jitter frequency

Both figures are generated from a synthesised jitter process, so the numbers in
the annotations are measured from the same arrays the curves are drawn from.
"""

from __future__ import annotations

import numpy as np
from scipy.special import erfc

from . import plotstyle as P

RNG = np.random.default_rng(5150)


def _dj_rj_histogram(n_per_lobe: int = 20000, rj_sigma: float = 0.010,
                     dj_split: float = 0.045):
    """Total jitter as two Gaussian lobes separated by the deterministic part.

    This is the dual-Dirac model in its generative form: draw from one of two
    means, then add the random part to each.
    """
    for sign in (-1.0, 1.0):
        mu = sign * dj_split / 2.0
        yield RNG.normal(mu, rj_sigma, n_per_lobe)


def jitter_decomposition_plot() -> str:
    fig, axes = P.figure(height=4.0, ncols=2)
    ax0, ax1 = axes

    sigma = 0.010
    dj = 0.045
    samples = np.concatenate(list(_dj_rj_histogram(rj_sigma=sigma,
                                                   dj_split=dj)))
    ax0.hist(samples, bins=140, color=P.NOTE, alpha=0.8, zorder=3)
    for sign in (-1.0, 1.0):
        ax0.axvline(sign * dj / 2.0, color=P.WARN, lw=1.6, ls=(0, (5, 4)),
                    zorder=4)
    # the 10^-12 tails, which is what a mask limit is built from
    q = 7.034
    lo_tail = -dj / 2.0 - q * sigma
    hi_tail = dj / 2.0 + q * sigma
    for x, label, colour in ((lo_tail, "left tail", P.OPTICAL),
                             (hi_tail, "right tail", P.OPTICAL)):
        ax0.axvline(x, color=colour, lw=1.8, zorder=5)
        ax0.text(x, ax0.get_ylim()[1] * 0.86, f" {label}\n 10\u207b\u00b9\u00b2",
                 fontsize=8.2, color=colour, weight="bold",
                 ha="left" if x > 0 else "right")
    P.title(ax0, "One jitter histogram, two mechanisms",
            subtitle="deterministic jitter separates the lobes; random jitter "
                     "widens them")
    P.tidy(ax0, xlabel="time relative to the nominal crossing (UI)",
           ylabel="counts")
    ax0.set_xlim(-0.10, 0.10)
    ax0.grid(axis="x", visible=False)

    # --- right: total jitter against observation length ---
    observations = np.logspace(6, 13, 200)
    # BER floor of the measurement maps to a Q, and Q grows with the log of
    # the number of samples: Q = sqrt(2) * erfinv(1 - 2/N) approximately.
    from scipy.special import erfinv
    q_of_n = np.sqrt(2.0) * erfinv(1.0 - 2.0 / observations)
    tj = dj + 2.0 * q_of_n * sigma
    rj_part = 2.0 * q_of_n * sigma

    ax1.semilogx(observations, tj, color=P.ACCENT, lw=2.6, label="total jitter")
    ax1.semilogx(observations, np.full_like(observations, dj), color=P.WARN,
                 lw=2.2, ls=(0, (6, 4)), label="deterministic part")
    ax1.semilogx(observations, rj_part, color=P.NOTE, lw=2.2, ls=(0, (2, 3)),
                 label="random part")
    for n, label in ((1e9, "10\u2079 samples"), (1e12, "10\u00b9\u00b2 samples")):
        value = float(np.interp(n, observations, tj))
        ax1.plot([n], [value], marker="o", ms=7, color=P.ACCENT,
                 markeredgecolor=P.PANEL, markeredgewidth=1.3, zorder=6)
        ax1.annotate(f"{value:.3f} UI\nat {label}", xy=(n, value),
                     xytext=(0, 10), textcoords="offset points", fontsize=8.2,
                     color=P.ACCENT_DARK, weight="bold", ha="center")
    P.title(ax1, "Total jitter grows with the measurement",
            subtitle="the random part grows without bound; the deterministic "
                     "part does not")
    P.tidy(ax1, xlabel="samples observed", ylabel="jitter (UI)", legend=True,
           legend_loc="upper left")
    ax1.set_ylim(0, max(tj) * 1.15)
    return P.render(fig)


def cdr_loop_bandwidth() -> str:
    fig, axes = P.figure(height=3.9, ncols=2)
    ax0, ax1 = axes

    f = np.logspace(4, 10, 500)            # jitter frequency, Hz

    # A first-order tracking loop: the transfer from input jitter to tracking
    # error is high-pass, |H| = (f/fc)/sqrt(1+(f/fc)^2). A second-order loop
    # with peaking is modelled by the damping factor below.
    for fc, colour, label in ((1e6, P.ACCENT, "1 MHz loop"),
                              (1e7, P.NOTE, "10 MHz loop"),
                              (5e7, P.WARN, "50 MHz loop")):
        tracking = (f / fc) / np.sqrt(1.0 + (f / fc) ** 2)
        ax0.loglog(f, 20 * np.log10(np.maximum(tracking, 1e-6)), color=colour,
                   lw=2.4, label=label)

    ax0.axhline(0, color=P.RULE, lw=1.0)
    P.title(ax0, "Tracking error against jitter frequency",
            subtitle="above the loop bandwidth, incoming jitter is not "
                     "tracked and passes straight through")
    P.tidy(ax0, xlabel="jitter frequency (Hz)", ylabel="untracked jitter (dB)",
           legend=True, legend_loc="lower right")
    ax0.set_ylim(-60, 4)
    ax0.grid(which="minor", visible=False)

    # --- right: the peaking that a second-order loop adds ---
    for zeta, colour, label in ((0.5, P.WARN, "\u03b6 = 0.5 (peaking)"),
                                (0.707, P.NOTE, "\u03b6 = 0.707 (Butterworth)"),
                                (1.5, P.ACCENT, "\u03b6 = 1.5 (overdamped)")):
        # normalised second-order high-pass magnitude
        r = f / 1e7
        mag2 = r ** 4 / ((1.0 - r ** 2) ** 2 + (2.0 * zeta * r) ** 2)
        ax1.loglog(f, 20 * np.log10(np.maximum(np.sqrt(mag2), 1e-6)),
                   color=colour, lw=2.4, label=label)
    ax1.axhline(0, color=P.RULE, lw=1.0)
    P.title(ax1, "The same loop, second order",
            subtitle="low damping buys acquisition speed and adds jitter "
                     "peaking just below the corner")
    P.tidy(ax1, xlabel="jitter frequency (Hz)", ylabel="untracked jitter (dB)",
           legend=True, legend_loc="lower right")
    ax1.set_ylim(-60, 12)
    ax1.grid(which="minor", visible=False)
    return P.render(fig)


FIGURES = {
    "jitter-decomposition-plot": jitter_decomposition_plot,
    "cdr-loop-bandwidth": cdr_loop_bandwidth,
}
