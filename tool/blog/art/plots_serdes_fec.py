"""Computed figures for the SerDes FEC and error-budget chapter.

    burst-error-interleaving   a simulated DFE error process, with and without
                               interleaving, decoded by the same code
    end-to-end-error-budget    every term as an equivalent error ratio, summed,
                               against the code's threshold

The first figure simulates error propagation so the burstiness is a measured
property of the process rather than a claim; the second is the budget arithmetic
in one picture.
"""

from __future__ import annotations

import numpy as np

from . import plotstyle as P

RNG = np.random.default_rng(31337)


def _dfe_error_process(n_bits: int, p_raw: float, feedback: float = 0.55):
    """A crude DFE error model: one error can trigger the next.

    Each bit is wrong with probability ``p_raw``; a wrong bit raises the chance
    that the following bit is also wrong to ``feedback``. That is the mechanism
    behind error propagation, and it is enough to produce the burstiness the
    figure is about.
    """
    errors = np.zeros(n_bits, dtype=bool)
    rng = RNG.random(n_bits)
    propagated = False
    for i in range(n_bits):
        p = feedback if propagated else p_raw
        if rng[i] < p:
            errors[i] = True
            propagated = True
        else:
            propagated = False
    return errors


def _runs(errors: np.ndarray) -> np.ndarray:
    """Lengths of the consecutive runs of True."""
    if not errors.any():
        return np.array([0])
    idx = np.flatnonzero(np.diff(np.concatenate(([0], errors.view(np.int8),
                                                 [0]))))
    return (idx[1::2] - idx[::2])


def burst_error_interleaving() -> str:
    n = 400000
    p_raw = 2.0e-4
    errors = _dfe_error_process(n, p_raw)

    fig, axes = P.figure(height=4.0, ncols=3)
    ax0, ax1, ax2 = axes

    # --- 1: the error process itself ---
    window = 4000
    occupied = np.flatnonzero(errors)[:120]
    if len(occupied):
        lo = max(0, occupied[0] - 20)
        hi = min(n, lo + window)
        ax0.plot(np.arange(lo, hi), errors[lo:hi].astype(float), color=P.WARN,
                 lw=1.4, drawstyle="steps-post")
    P.title(ax0, "The error process", subtitle="a DFE's errors arrive in bursts")
    P.tidy(ax0, xlabel="bit index", ylabel="error")
    ax0.set_ylim(-0.1, 1.2)
    ax0.grid(axis="y", visible=False)

    # --- 2: the burst-length distribution ---
    runs = _runs(errors)
    runs = runs[runs > 0]
    max_len = int(runs.max()) if len(runs) else 1
    bins = np.arange(0.5, min(max_len, 12) + 1.5, 1.0)
    counts, edges = np.histogram(runs, bins=bins)
    ax1.bar(edges[:-1], counts, width=0.8, color=P.NOTE, zorder=3)
    P.title(ax1, "Burst lengths", subtitle="measured on the process at the left")
    P.tidy(ax1, xlabel="consecutive errors", ylabel="occurrences",
           xaxis_int=True)
    ax1.grid(axis="x", visible=False)

    # --- 3: what interleaving does to the correction budget ---
    # RS(544, 514) corrects 15 symbol errors. A burst of L consecutive bit
    # errors spans about L/10 symbols when 10 bits map to a symbol, and
    # spreading it over 16 interleaved codewords divides that span.
    depths = np.array([1, 2, 4, 8, 16, 32])
    symbols_per_codeword = 15.0
    worst_burst_bits = 9.0
    symbols_per_burst = worst_burst_bits / 10.0
    per_codeword = symbols_per_burst / depths
    margin = symbols_per_codeword / np.maximum(per_codeword, 1e-9)
    ax2.semilogy(depths, margin, color=P.ACCENT, lw=2.6, marker="o", ms=6,
                 markeredgecolor=P.PANEL, markeredgewidth=1.3, zorder=5)
    ax2.axhline(1.0, color=P.WARN, lw=1.6, ls=(0, (5, 4)), zorder=3)
    ax2.text(1.1, 1.25, "correction budget exhausted", fontsize=8.4,
             color=P.WARN, weight="bold")
    for d, m in zip(depths, margin):
        if d in (1, 16):
            ax2.annotate(f"{m:.0f}x", xy=(d, m), xytext=(0, 8),
                         textcoords="offset points", fontsize=8.4,
                         color=P.ACCENT_DARK, weight="bold", ha="center")
    P.title(ax2, "Interleaving buys budget",
            subtitle="same burst, spread over more codewords")
    P.tidy(ax2, xlabel="interleaving depth", ylabel="budget per codeword",
           xaxis_int=True)
    ax2.set_ylim(0.5, 400)
    ax2.grid(axis="x", visible=False)
    ax2.grid(which="minor", visible=False)
    return P.render(fig)


def end_to_end_error_budget() -> str:
    fig, ax = P.figure(height=3.8)
    P.title(ax, "The error budget, as error ratios rather than decibels",
            subtitle="every term converted to an equivalent pre-FEC error "
                     "ratio, summed in the exponent, against the code's limit")

    terms = [
        ("fibre + OSNR", -9.0, P.OPTICAL),
        ("transmitter + optics", -10.5, P.OPTICAL),
        ("channel loss + ISI", -8.2, P.WARN),
        ("crosstalk", -11.0, P.WARN),
        ("reflections", -13.0, P.WARN),
        ("CDR jitter", -12.2, P.NOTE),
        ("reference clock", -14.0, P.NOTE),
        ("receiver noise", -13.6, P.ACCENT),
    ]
    # Independent contributions add as error *rates*, so their exponents add
    # as powers of ten: log10(sum(10^e)) computed on the arrays.
    exps = np.array([t[1] for t in terms])
    total_exp = float(np.log10(np.sum(10.0 ** exps)))
    threshold_exp = float(np.log10(2.4e-4))

    y = np.arange(len(terms))[::-1]
    ax.barh(y, [10 ** (e - total_exp) for e in exps], color=[t[2] for t in terms],
            height=0.55, zorder=3)
    for yi, (name, e, _c) in zip(y, terms):
        share = 10 ** (e - total_exp) * 100.0
        ax.text(share + 0.01, yi, f"10{e:+.1f}  ({share:.0f}% of the total)",
                va="center", fontsize=8.4, color=P.SOFT)
    ax.set_yticks(y)
    ax.set_yticklabels([t[0] for t in terms], fontsize=9)
    ax.set_xscale("log")
    ax.set_xlim(1e-6, 3.0)
    ax.set_xlabel("share of the total error ratio")
    ax.grid(axis="y", visible=False)

    margin = threshold_exp - total_exp
    ax.text(0.98, 0.06,
            f"total 10{total_exp:+.1f}\nFEC limit 10{threshold_exp:+.1f}\n"
            f"margin {margin:.1f} orders of magnitude",
            transform=ax.transAxes, fontsize=9, family="monospace",
            color=P.ACCENT_DARK, ha="right", va="bottom",
            bbox=dict(boxstyle="round,pad=0.5", facecolor=P.PANEL,
                      edgecolor=P.ACCENT, linewidth=1.2))
    return P.render(fig)


FIGURES = {
    "burst-error-interleaving": burst_error_interleaving,
    "end-to-end-error-budget": end_to_end_error_budget,
}
