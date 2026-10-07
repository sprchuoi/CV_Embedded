"""Computed figures for the BERT, BER and FEC chapter.

    ber-vs-snr-fec   BER against SNR for NRZ and PAM4, with the FEC thresholds
                     drawn as the horizontal lines they are
    bert-measurement-time  how long you must wait to see one error, which is the
                     real cost of a longer PRBS pattern

These are the two numbers that decide whether a link is signed off: the SNR it
achieves, and the error ratio the FEC is contracted to correct.
"""

from __future__ import annotations

import numpy as np
from scipy.special import erfc

from . import plotstyle as P


def _qfunc(x: np.ndarray) -> np.ndarray:
    """Gaussian tail probability: BER = Q(x) for a two-level slicer."""
    return 0.5 * erfc(x / np.sqrt(2.0))


def _pam_ber(snr_power_db: np.ndarray, m: int) -> np.ndarray:
    """Symbol and bit error ratio of an ideal M-PAM slicer.

    The SNR convention here is the one a link budget uses: the ratio of the
    *average* signal power to the noise power in the same bandwidth. For M
    equally spaced levels the average power is ``(M^2 - 1)/12 * d^2``, so the
    eye spacing ``d`` follows from the SNR, and the symbol error ratio is the
    sum of the two half-Gaussian tails at each of the ``M - 1`` thresholds.

    Dividing by ``log2(M)`` converts symbol errors to bit errors, which is the
    standard Gray-coding approximation -- valid because a Gray-coded PAM4
    symbol is wrong in exactly one bit almost all of the time.
    """
    snr = 10 ** (snr_power_db / 10.0)
    d = np.sqrt(12.0 * snr / (m ** 2 - 1))          # eye spacing, noise sigma = 1
    # thresholds sit at +/-(M-1), +/-(M-3), ... times d/2
    thresholds = np.arange(m - 1, 0, -2) * d[..., None] / 2.0
    ser = np.sum(2.0 * _qfunc(thresholds) / m, axis=-1)
    return ser / np.log2(m)


def ber_vs_snr_fec() -> str:
    fig, ax = P.figure(height=3.9)
    P.title(ax, "BER against SNR, and where FEC takes over",
            subtitle="ideal slicers, average-power SNR; the horizontal gap "
                     "between the curves is the PAM4 penalty at equal bit rate")

    snr_db = np.linspace(4, 34, 400)
    ber_nrz = _pam_ber(snr_db, 2)
    ber_pam4 = _pam_ber(snr_db, 4)

    ax.semilogy(snr_db, ber_nrz, color=P.NOTE, lw=2.6,
                label="NRZ  (1 bit/symbol)")
    ax.semilogy(snr_db, ber_pam4, color=P.ACCENT, lw=2.6,
                label="PAM4 (2 bits/symbol)")

    # the penalty, measured off this array at a fixed error ratio. Only the
    # entries above the erfc underflow floor are interpolable: below about
    # 1e-16 the ideal slicer reports an exact zero and the log is -inf.
    valid = ber_nrz > 0.0
    target = 1e-4
    s_nrz = float(np.interp(np.log10(target), np.log10(ber_nrz[valid][::-1]),
                            snr_db[valid][::-1]))
    valid4 = ber_pam4 > 0.0
    s_pam4 = float(np.interp(np.log10(target),
                             np.log10(ber_pam4[valid4][::-1]),
                             snr_db[valid4][::-1]))
    penalty = s_pam4 - s_nrz
    ax.annotate("", xy=(s_pam4, target), xytext=(s_nrz, target),
                arrowprops=dict(arrowstyle="<->", color=P.WARN, lw=1.6))
    ax.text((s_nrz + s_pam4) / 2, target * 2.2,
            f"{penalty:.1f} dB\nPAM4 penalty\nat {target:g}",
            fontsize=8.6, color=P.WARN, ha="center", va="bottom",
            weight="bold")
    for s, colour, name in ((s_nrz, P.NOTE, "NRZ"), (s_pam4, P.ACCENT, "PAM4")):
        ax.plot([s], [target], marker="o", ms=8, color=colour,
                markeredgecolor=P.PANEL, markeredgewidth=1.4, zorder=6)
        ax.text(s, target * 0.35, f"{s:.1f} dB", fontsize=8.4, color=colour,
                ha="center", va="top", weight="bold")

    # FEC thresholds: the pre-FEC error ratio each code is contracted to see
    for level, label, colour in (
        (2.4e-4, "RS(544,514)  KP4  \u2014  100G/lane", P.WARN),
        (1e-5, "RS(528,514)  KR4  \u2014  legacy 25G", P.OPTICAL),
        (1e-12, "post-FEC target", P.MUTED),
    ):
        ax.axhline(level, color=colour, lw=1.3, ls=(0, (5, 4)), zorder=2)
        ax.text(33.6, level * 1.6, label, fontsize=8.4, color=colour,
                ha="right", va="bottom", weight="bold")

    P.tidy(ax, xlabel="SNR at the slicer (dB, average power)",
           ylabel="bit error ratio")
    ax.set_ylim(1e-16, 1e-1)
    ax.set_xlim(4, 34)
    ax.grid(which="minor", visible=False)
    ax.legend(loc="lower left", fontsize=8.6)
    return P.render(fig)


def bert_measurement_time() -> str:
    fig, axes = P.figure(height=3.4, ncols=2)
    ax0, ax1 = axes

    # --- left: the Q factor behind the number ---
    ber = np.logspace(-16, -1, 300)
    # invert BER = Q(Qfactor) numerically by interpolating a fine table
    q_tab = np.linspace(0.1, 9.0, 4000)
    ber_tab = _qfunc(q_tab)
    q_of_ber = np.interp(ber, ber_tab[::-1], q_tab[::-1])

    ax0.semilogx(ber, 20 * np.log10(q_of_ber), color=P.OPTICAL, lw=2.6)
    for level, label in ((1e-4, "10\u207b\u2074"), (1e-12, "10\u207b\u00b9\u00b2"),
                         (1e-15, "10\u207b\u00b9\u2075")):
        q = float(np.interp(level, ber_tab[::-1], q_tab[::-1]))
        ax0.plot([level], [20 * np.log10(q)], marker="o", ms=7,
                 color=P.OPTICAL, markeredgecolor=P.PANEL,
                 markeredgewidth=1.4, zorder=5)
        ax0.annotate(f"{20*np.log10(q):.1f} dB", xy=(level, 20 * np.log10(q)),
                     xytext=(6, -12), textcoords="offset points", fontsize=8.4,
                     color=P.OPTICAL_DARK, weight="bold")
    P.title(ax0, "The Q factor hiding in a BER",
            subtitle="required SNR for a given error ratio, NRZ")
    P.tidy(ax0, xlabel="bit error ratio", ylabel="required Q (dB)")
    ax0.set_ylim(8, 27)
    ax0.grid(which="minor", visible=False)

    # --- right: how long one error takes to appear ---
    years = 3.156e7
    ber2 = np.logspace(-18, -3, 300)
    for rate, colour, label in ((10e9, P.NOTE, "10 Gb/s"),
                                (100e9, P.ACCENT, "100 Gb/s"),
                                (800e9, P.WARN, "800 Gb/s")):
        bits = 1.0 / ber2
        seconds = bits / rate
        ax1.loglog(ber2, seconds, color=colour, lw=2.4, label=label)
    for secs, label in ((1.0, "1 s"), (60.0, "1 min"), (3600.0, "1 hour"),
                        (years, "1 year")):
        ax1.axhline(secs, color=P.RULE, lw=1.0, ls=(0, (4, 4)), zorder=2)
        ax1.text(1e-18, secs, f" {label}", fontsize=8, color=P.MUTED,
                 va="bottom", ha="left")
    ax1.axvline(2.4e-4, color=P.WARN, lw=1.3, ls=(0, (5, 4)), zorder=3)
    ax1.text(2.4e-4, 1e-6, " KP4 pre-FEC\n target", fontsize=8.2,
             color=P.WARN, rotation=90, va="bottom", weight="bold")
    P.title(ax1, "Time to observe one error",
            subtitle="the cost of measuring a low error ratio")
    P.tidy(ax1, xlabel="bit error ratio", ylabel="seconds per expected error",
           legend=True, legend_loc="upper left")
    ax1.set_ylim(1e-4, 1e10)
    ax1.grid(which="minor", visible=False)
    return P.render(fig)


FIGURES = {
    "ber-vs-snr-fec": ber_vs_snr_fec,
    "bert-measurement-time": bert_measurement_time,
}
