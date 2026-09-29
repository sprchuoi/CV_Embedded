"""Computed figures for the FIR filter design chapter.

Four figures, in the order the article uses them:

    fir-truncation-gibbs        why more taps is not the same as less ripple
    fir-window-responses        the main-lobe / sidelobe trade-off, window by window
    fir-linear-phase-response   symmetric taps are what buy a constant group delay
    fir-design-comparison       windowed-sinc, least squares and Parks-McClellan at N = 41

Nothing here is sketched. ``scipy.signal.firwin``, ``firls`` and ``remez``
design real filters and ``freqz`` evaluates them, and every number the figures
annotate is measured on the same 4096-point grid the curves are drawn from --
so a claim on the figure and the curve under it cannot drift apart.

Conventions, applied everywhere: frequency is normalised to Nyquist (``w / pi``,
so 1.0 is the folding frequency), magnitude is in dB and floored at -100 dB, and
the passband of a windowed-sinc design sits at 0 dB because ``firwin`` scales the
taps to unity DC gain.
"""

from __future__ import annotations

import numpy as np
from scipy import signal

from . import plotstyle as P

WORN = 4096                       # points on every frequency axis
FLOOR_DB = -100.0                 # curves are clipped here, not left to dive
CUTOFF = 0.25                     # the chapter's shared cutoff, x/pi = 0.25
XLABEL = "normalised frequency (×π rad/sample)"
YLABEL = "magnitude (dB)"

# The four rectangular-windowed lengths of figure 1, longest last.
TRUNCATION_TAPS = (11, 21, 41, 81)

# label -> scipy window name, for figure 2. "rectangular" is scipy's own alias
# for the boxcar window.
WINDOWS = (
    ("rectangular", "rectangular"),
    ("Hann", "hann"),
    ("Hamming", "hamming"),
    ("Blackman", "blackman"),
)


# --------------------------------------------------------------------------- #
# local helpers
# --------------------------------------------------------------------------- #


def _response_db(h, worN: int = WORN):
    """Magnitude response of ``h`` in dB, against frequency normalised to Nyquist."""
    w, H = signal.freqz(h, worN=worN)
    floor = 10.0 ** (FLOOR_DB / 20.0)
    return w / np.pi, 20.0 * np.log10(np.maximum(np.abs(H), floor))


def _peak_sidelobe(x, magnitude_db, *, above: float = CUTOFF) -> float:
    """Highest local maximum past the cutoff: the worst stopband lobe.

    Local maxima are the honest way to measure this. A plain maximum over
    ``x > cutoff`` just reports the skirt of the transition band, which falls
    with N and would hide the very thing figure 1 is about.
    """
    peaks = [magnitude_db[i] for i in range(1, len(x) - 1)
             if x[i] > above and magnitude_db[i] < -6.0
             and magnitude_db[i] >= magnitude_db[i - 1]
             and magnitude_db[i] >= magnitude_db[i + 1]]
    return max(peaks) if peaks else float(FLOOR_DB)


def _dotted(ax, y, colour):
    ax.axhline(y, color=colour, linestyle=(0, (1.5, 2.5)), linewidth=1.4, zorder=1)


def _arrow(ax, text, xy, xytext, colour, *, size=9.0):
    """A callout that lives in empty space and points at the curve it describes."""
    ax.annotate(text, xy=xy, xytext=xytext, color=colour, fontsize=size,
                ha="left", va="bottom", zorder=6,
                arrowprops=dict(arrowstyle="->", color=colour, linewidth=1.1,
                                shrinkA=3, shrinkB=3))


# --------------------------------------------------------------------------- #
# 1. truncation of the ideal impulse response
# --------------------------------------------------------------------------- #


def fir_truncation_gibbs() -> str:
    """Rectangular-windowed sincs of four lengths: narrower transition, same ripple."""
    fig, ax = P.figure(height=3.2)

    taps = list(TRUNCATION_TAPS)
    sidelobes = []
    for index, count in enumerate(TRUNCATION_TAPS):
        n = np.arange(count)
        centre = (count - 1) / 2.0
        h = np.sinc(CUTOFF * (n - centre))       # the ideal response, cut short
        h = h / h.sum()                          # unity gain at DC
        x, magnitude = _response_db(h)
        ax.plot(x, magnitude, color=P.SERIES[index], label=f"N = {count} taps")
        sidelobes.append(_peak_sidelobe(x, magnitude))

    # The ripple floor: the same to within a decibel for every length, which is
    # the whole point of the figure.
    floor = float(np.mean(sidelobes))
    _dotted(ax, floor, P.WARN)

    # The one region no response ever enters is the band above 0 dB, so the
    # callout and the legend both live up there.
    _arrow(ax,
           "more taps narrow the transition,\n"
           f"but the ripple floor stays put at ≈ {floor:.0f} dB",
           xy=(0.55, floor + 0.5), xytext=(0.05, 5.0), colour=P.WARN)

    ax.set_xlim(0, 1)
    ax.set_ylim(FLOOR_DB, 16)
    P.tidy(ax, xlabel=XLABEL, ylabel=YLABEL,
           legend=[f"N = {count} taps" for count in taps], legend_loc="upper right",
           ncol=2)
    return P.render(fig)


# --------------------------------------------------------------------------- #
# 2. the window trade-off
# --------------------------------------------------------------------------- #


def fir_window_responses() -> str:
    """Four windows at N = 65: the shapes, and the responses they buy."""
    fig, axes = P.figure(height=4.6, nrows=2, height_ratios=[1, 1.5])
    ax_time, ax_freq = axes

    count = 65
    n = np.arange(count)
    for index, (label, name) in enumerate(WINDOWS):
        colour = P.SERIES[index]

        ax_time.plot(n, signal.get_window(name, count), color=colour, label=label)

        x, magnitude = _response_db(signal.firwin(count, CUTOFF, window=name))
        ax_freq.plot(x, magnitude, color=colour, label=label)

    # --- top: the windows themselves ---------------------------------------
    ax_time.set_xlim(0, count - 1)
    ax_time.set_ylim(-0.05, 1.22)
    ax_time.text(1.0, 1.16, f"N = {count} taps", color=P.MUTED, fontsize=9,
                 ha="left", va="top")
    P.tidy(ax_time, xlabel="tap index  n", ylabel="window weight  w[n]",
           xaxis_int=True)

    # --- bottom: what they cost and buy -------------------------------------
    ax_freq.set_xlim(0, 1)
    ax_freq.set_ylim(-118, 6)

    # Blackman's shoulder has the widest main lobe; rectangular's stopband is by
    # far the shallowest. Below the boxcar's -21 dB lobe peaks every band is
    # crossed by somebody's skirts, so both labels live in the clear air above.
    _arrow(ax_freq, "Blackman: widest main lobe", xy=(0.305, -33),
           xytext=(0.30, -4), colour=P.OPTICAL, size=8.8)
    _arrow(ax_freq, "rectangular: shallowest stopband", xy=(0.66, -27),
           xytext=(0.63, -4), colour=P.ACCENT, size=8.8)

    P.tidy(ax_freq, xlabel=XLABEL, ylabel=YLABEL,
           legend=[label for label, _ in WINDOWS], legend_loc="lower left")
    return P.render(fig)


# --------------------------------------------------------------------------- #
# 3. linear phase
# --------------------------------------------------------------------------- #


def fir_linear_phase_response() -> str:
    """A 41-tap Hamming design: symmetric taps, flat passband, flat group delay."""
    taps = 41
    delay = (taps - 1) / 2.0                     # 20 samples
    mask_db = -60.0                              # group delay is noise below this

    h = signal.firwin(taps, CUTOFF, window="hamming")
    fig, axes = P.figure(height=5.4, nrows=3, height_ratios=[1, 1.4, 1])
    ax_taps, ax_mag, ax_delay = axes

    # --- 1: the taps, and the mirror line they sit on ----------------------
    n = np.arange(taps)
    markerline, stemlines, baseline = ax_taps.stem(n, h)
    markerline.set_color(P.ACCENT)
    markerline.set_markersize(3.4)
    stemlines.set_color(P.ACCENT)
    stemlines.set_linewidth(1.1)
    baseline.set_color(P.RULE_SOFT)
    baseline.set_linewidth(1.0)

    ax_taps.axvline(delay, color=P.NOTE, linestyle=(0, (2, 2)), linewidth=1.3,
                    zorder=1)
    ax_taps.plot([delay], [h[int(delay)]], marker="o", markersize=5.0,
                 color=P.NOTE, zorder=5)
    ax_taps.annotate(f"centre tap  n = (N-1)/2 = {delay:.0f}",
                     xy=(delay, h[int(delay)]),
                     xytext=(delay + 1.2, h[int(delay)] + 0.02),
                     color=P.NOTE, fontsize=8.8, ha="left", va="bottom", zorder=6)

    top = float(h.max()) + 0.10
    ax_taps.annotate("", xy=(taps - 1, top), xytext=(0, top),
                     arrowprops=dict(arrowstyle="<->", color=P.MUTED, linewidth=1.0))
    ax_taps.text(delay, top + 0.012, "h[n] = h[N-1-n]", color=P.SOFT, fontsize=9,
                 ha="center", va="bottom")
    ax_taps.set_xlim(-1, taps)
    ax_taps.set_ylim(float(h.min()) - 0.05, top + 0.07)
    P.tidy(ax_taps, xlabel="tap index  n", ylabel="tap value  h[n]", xaxis_int=True)

    # --- 2: the magnitude it produces --------------------------------------
    x, magnitude = _response_db(h)
    ax_mag.plot(x, magnitude, color=P.ACCENT)
    ax_mag.axvline(CUTOFF, color=P.RULE, linestyle=(0, (4, 3)), linewidth=1.1,
                   zorder=1)
    ax_mag.text(CUTOFF + 0.012, 2.0, "cutoff  0.25π", color=P.MUTED, fontsize=8.8,
                ha="left", va="bottom")
    ax_mag.set_xlim(0, 1)
    ax_mag.set_ylim(FLOOR_DB, 6)
    P.tidy(ax_mag, xlabel=XLABEL, ylabel=YLABEL)

    # --- 3: the group delay, where there is any signal to measure it on -----
    w, H = signal.freqz(h, worN=WORN)
    phase = np.unwrap(np.angle(H))
    group_delay = -np.diff(phase) / np.diff(w)
    mid = 0.5 * (w[:-1] + w[1:]) / np.pi
    mag = 20.0 * np.log10(np.maximum(np.abs(H), 10.0 ** (FLOOR_DB / 20.0)))
    mag_mid = 0.5 * (mag[:-1] + mag[1:])
    visible = np.where(mag_mid > mask_db, group_delay, np.nan)

    ax_delay.plot(mid, visible, color=P.ACCENT)
    # Drawn over the data, which sits exactly on it -- that coincidence is the
    # message, so the reference line has to stay visible.
    ax_delay.axhline(delay, color=P.NOTE, linestyle=(0, (1.5, 2.5)), linewidth=1.4,
                     zorder=5)
    ax_delay.text(0.45, delay + 1.5, f"flat at (N-1)/2 = {delay:.0f} samples",
                  color=P.NOTE, fontsize=9, ha="left", va="bottom")
    ax_delay.set_xlim(0, 1)
    ax_delay.set_ylim(0, 40)
    P.tidy(ax_delay, xlabel=XLABEL,
           ylabel=f"group delay, samples  (|H| > {mask_db:.0f} dB)")
    return P.render(fig)


# --------------------------------------------------------------------------- #
# 4. three ways to spend 41 taps
# --------------------------------------------------------------------------- #


def fir_design_comparison() -> str:
    """Windowed-sinc, least squares and Parks-McClellan on one 41-tap spec."""
    taps = 41
    passband, stopband = 0.20, 0.30
    bands = [0.0, passband, stopband, 1.0]

    # Every design is expressed on the same axis: frequency in units of Nyquist
    # (firwin's ``cutoff``, and ``fs=2.0`` for the two band-edge designers). With
    # remez's own default of fs=1.0 the same band list would mean 0.4π and 0.6π.
    designs = (
        ("windowed-sinc (Hamming)",
         signal.firwin(taps, 0.25, window="hamming")),
        ("least squares (firls)",
         signal.firls(taps, bands, [1, 1, 0, 0], weight=[1.0, 1.0], fs=2.0)),
        ("Parks-McClellan (remez)",
         signal.remez(taps, bands, [1, 0], fs=2.0)),
    )

    fig, ax = P.figure(height=3.6)
    measured = []
    for index, (label, h) in enumerate(designs):
        x, magnitude = _response_db(h)
        short = label.split(" (")[0]
        ax.plot(x, magnitude, color=P.SERIES[index], label=short)
        in_pass = magnitude[x <= passband]
        in_stop = magnitude[x >= stopband]
        measured.append((short, float(in_pass.max() - in_pass.min()),
                         float(in_stop.max())))

    # The two spec edges, so the reader can see where each design is meant to be.
    # Labelled just under the passband, which is where the curves part company.
    for edge in (passband, stopband):
        ax.axvline(edge, color=P.RULE, linestyle=(0, (4, 3)), linewidth=1.1, zorder=1)
        ax.text(edge, -6.0, f"{edge:.2f}π", color=P.MUTED, fontsize=8.6,
                ha="center", va="top")

    # The measured numbers, on the figure rather than in the prose. Every design
    # is well past its transition by 0.42, so the space above -30 dB is empty.
    rows = ["design             ripple    stopband"]
    for label, ripple, worst in measured:
        rows.append(f"{label:<18s}{ripple:5.2f} dB   {worst:6.1f} dB")
    ax.text(0.42, -2, "\n".join(rows), family="monospace", fontsize=8.2,
            color=P.SOFT, ha="left", va="top", zorder=6,
            bbox=dict(boxstyle="round,pad=0.45", facecolor=P.PANEL,
                      edgecolor=P.RULE_SOFT, linewidth=1.0))

    ax.set_xlim(0, 1)
    ax.set_ylim(FLOOR_DB, 8)
    # Left-hand side, where the stopband has not started yet: the only strip the
    # three responses leave empty for a legend.
    P.tidy(ax, xlabel=XLABEL, ylabel=YLABEL,
           legend=[label.split(" (")[0] for label, _ in designs],
           legend_loc="center left")
    return P.render(fig)


FIGURES = {
    "fir-truncation-gibbs": fir_truncation_gibbs,
    "fir-window-responses": fir_window_responses,
    "fir-linear-phase-response": fir_linear_phase_response,
    "fir-design-comparison": fir_design_comparison,
}
