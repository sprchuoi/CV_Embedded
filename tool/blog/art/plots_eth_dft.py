"""Computed figures for the FFT/DFT-in-Ethernet chapter.

    dft-resolution-demo   one tone at two record lengths: the same signal, two
                          spectra, and the resolution that separates them
    ethernet-spectral-mask  1000BASE-T's transmit spectrum against its mask, and
                          the window's own resolution shown as a bar

Both figures are generated with numpy's FFT, so `np.fft` is doing to the figure
exactly what it does to a compliance measurement.
"""

from __future__ import annotations

import numpy as np

from . import plotstyle as P

RNG = np.random.default_rng(4242)


def _one_sided(signal: np.ndarray, fs: float):
    """The one-sided amplitude spectrum of a real record, in dB relative to FS."""
    n = len(signal)
    window = np.hanning(n)
    coherent_gain = window.sum()
    spec = np.abs(np.fft.rfft(signal * window)) / coherent_gain
    spec_db = 20 * np.log10(np.maximum(spec, 1e-12))
    freqs = np.fft.rfftfreq(n, d=1.0 / fs)
    return freqs, spec_db


def dft_resolution_demo() -> str:
    fig, axes = P.figure(height=4.2, nrows=2, sharex=False)
    ax0, ax1 = axes

    fs = 1.0e9                      # 1 GS/s, a convenient round number
    f1, f2 = 100.0e6, 112.0e6       # two tones 12 MHz apart
    amp = 0.5

    for ax, n, title in ((ax0, 512, "512 samples"),
                         (ax1, 16384, "16384 samples")):
        t = np.arange(n) / fs
        x = amp * np.sin(2 * np.pi * f1 * t) + amp * np.sin(2 * np.pi * f2 * t)
        freqs, spec_db = _one_sided(x, fs)
        bin_hz = fs / n
        ax.plot(freqs / 1e6, spec_db, color=P.NOTE, lw=1.6)
        ax.set_xlim(60, 160)
        ax.set_ylim(-90, 6)
        ax.axvline(f1 / 1e6, color=P.ACCENT, lw=1.0, ls=(0, (4, 4)), zorder=2)
        ax.axvline(f2 / 1e6, color=P.WARN, lw=1.0, ls=(0, (4, 4)), zorder=2)
        P.title(ax, title,
                subtitle=f"bin spacing f\u209b/N = {bin_hz/1e6:.3f} MHz  "
                         f"\u2014  {'the two tones are one blur' if n == 512 else 'the two tones are resolved'}")
        P.tidy(ax, ylabel="magnitude (dB)")

    ax1.set_xlabel("frequency (MHz)")
    ax0.text(0.985, 0.06, "two tones, 100 and 112 MHz",
             transform=ax0.transAxes, fontsize=8.4, color=P.SOFT, ha="right",
             family="monospace")
    return P.render(fig)


def ethernet_spectral_mask() -> str:
    fig, ax = P.figure(height=3.9)
    P.title(ax, "1000BASE-T transmit spectrum against its mask",
            subtitle="a model of the specified spectral shape (solid) and the "
                     "limit it must stay under (dashed)")

    f = np.linspace(0.1, 200.0, 1200)       # MHz
    # 1000BASE-T scrambles 4 PAM5 pairs and shapes the spectrum between roughly
    # 1 MHz and 100 MHz. This is a smooth model of the specified shape, not a
    # measured transmitter: the point of the figure is the comparison, not the
    # absolute level.
    highpass = (f / 1.0) / np.sqrt(1.0 + (f / 1.0) ** 2)
    lowpass = 1.0 / np.sqrt(1.0 + (f / 100.0) ** 8)
    tx = highpass * lowpass
    tx_db = 20 * np.log10(np.maximum(tx, 1e-8)) - 30.0   # arbitrary 0 dB ref

    mask = np.full_like(f, -30.0)
    mask[f < 1.0] = -30.0 - 20.0 * np.log10(1.0 / np.maximum(f[f < 1.0], 0.1))
    mask[f > 100.0] = -30.0 - 40.0 * np.log10(f[f > 100.0] / 100.0)

    ax.plot(f, tx_db, color=P.ACCENT, lw=2.4, zorder=5, label="transmitter")
    ax.plot(f, mask, color=P.WARN, lw=2.0, ls=(0, (6, 4)), zorder=4,
            label="mask")

    # resolution bar: 10 MHz, the bin spacing of the example in the diagram
    ax.plot([120, 130], [-72, -72], color=P.OPTICAL, lw=3.0, solid_capstyle="butt",
            zorder=6)
    ax.text(125, -69, "10 MHz\nbin spacing", fontsize=8.2, color=P.OPTICAL_DARK,
            ha="center", va="bottom", weight="bold")

    over = tx_db - mask
    worst = float(np.max(over))
    ax.text(0.02, 0.05, f"worst-case margin to the mask: {worst:+.1f} dB",
            transform=ax.transAxes, fontsize=8.6, color=P.SOFT,
            family="monospace",
            bbox=dict(boxstyle="round,pad=0.4", facecolor=P.PANEL,
                      edgecolor=P.RULE_SOFT, linewidth=1.0))

    P.tidy(ax, xlabel="frequency (MHz)", ylabel="PSD (dB, relative)",
           legend=True, legend_loc="upper right")
    ax.set_xlim(0, 200)
    ax.set_ylim(-80, -10)
    return P.render(fig)


FIGURES = {
    "dft-resolution-demo": dft_resolution_demo,
    "ethernet-spectral-mask": ethernet_spectral_mask,
}
