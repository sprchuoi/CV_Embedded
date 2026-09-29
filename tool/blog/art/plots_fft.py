"""Computed figures for the FFT chapter.

Four figures, in the order the article uses them:

    fft-cost-scaling           N² against (N/2)·log₂N, and the ratio between them
    fft-vs-dft-verification    a hand-written DFT measured against ``np.fft.fft``
    fft-tone-spectrum          what the transform is for: resolution, not magnitude
    fft-twiddle-geometry       the unit circle, and the small table a stage reuses

The module does not assert that the FFT is fast or that it is correct; it counts
one and measures the other. The direct DFT below is a real N² transform built
from ``np.outer`` with no help from ``np.fft``, and the figure that compares it
against ``np.fft.fft`` prints the difference it found rather than a claim about
it. The twiddle figure's stage table is tallied by running an actual in-place
radix-2 decimation-in-time loop, so it reports what the algorithm does rather
than what a table in a book says it does.

Counting convention, stated on the cost figure and used wherever a multiply
count appears: **one complex multiply per butterfly**, so a radix-2 FFT of
length N costs (N/2)·log₂(N) complex multiplies. Multiplications by ±1 and ±j
are counted like any other; a real implementation folds most of them away, which
is exactly what the twiddle figure makes visible.

Every figure is deterministic. Where randomness is needed -- the noise in the
verification signal -- the generator is created inside the builder from a fixed
seed, so a figure does not depend on the order the module is built in.
"""

from __future__ import annotations

import numpy as np

from . import plotstyle as P

# --------------------------------------------------------------------------- #
# shared conventions
# --------------------------------------------------------------------------- #

XLABEL_N = "transform length  N  (samples)"
FLOOR_DB = -70.0                   # spectra are clipped here, not left to dive

# figure 1: the whole point, on one axis
N_LO, N_HI = 8, 1 << 20
MARK_SIZES = (1 << 10, 1 << 20)    # the two working points the figure annotates

# figure 2: the verification sweep, every power of two from 8 to 1024
VERIFY_SIZES = (8, 16, 32, 64, 128, 256, 512, 1024)
VERIFY_N = 64                      # the record whose spectrum is drawn on top
VERIFY_TONES = ((5, 1.0, 0.0), (11, 0.8, 0.7), (23, 0.6, 1.9))
VERIFY_NOISE = 0.05

# figure 3: the same three tones held fixed while only the record length changes
RECORD_REF = 64.0                  # frequency unit: cycles per 64-sample record
TONE_CYCLES = ((10.0, 1.0, 0.0), (10.3, 1.0, 0.0), (3.0, 0.7, 0.9))
SPECTRUM_PANELS = ((64, "hann", "Hann"), (512, "rectangular", "rectangular"))

# figure 4: the twiddle table
TWIDDLE_N = 8


# --------------------------------------------------------------------------- #
# local helpers
# --------------------------------------------------------------------------- #


def _direct_dft(x: np.ndarray) -> np.ndarray:
    """The textbook DFT as an N×N matrix, straight from the definition.

    ``np.outer(k, k)`` builds every product k·n, so this is N² complex
    multiplies in one BLAS call -- the same arithmetic a double loop performs,
    and deliberately not ``np.fft``. That is what makes figure 2 a measurement.
    """
    n = x.size
    k = np.arange(n)
    twiddles = np.exp(-2j * np.pi * np.outer(k, k) / n)
    return twiddles @ x


def _fft_multiplies(n: np.ndarray) -> np.ndarray:
    """Radix-2 butterfly count under the one-multiply-per-butterfly convention."""
    return 0.5 * n * np.log2(n)


def _grouped(value: float) -> str:
    """1048576 -> '1,048,576', so a multiply count can be read digit by digit."""
    return f"{int(round(value)):,}"


def _sci(value: float, digits: int = 2) -> str:
    """1234567.0 -> '$1.23\\times10^{6}$' (mathtext, for axis-side annotations)."""
    exponent = int(np.floor(np.log10(abs(value))))
    mantissa = value / 10.0 ** exponent
    return f"${mantissa:.{digits}f}\\times10^{{{exponent}}}$"


def ratio_at(size: int) -> float:
    """Speed-up of the radix-2 FFT over the naive DFT at a given length."""
    return size ** 2 / float(_fft_multiplies(float(size)))


def _size_ticks(ax) -> None:
    """Power-of-two ticks, because FFT lengths are powers of two."""
    ticks = [1 << k for k in (3, 5, 7, 9, 11, 13, 15, 17, 19, 20)]
    ax.set_xticks(ticks)
    ax.set_xticklabels([f"$2^{{{int(np.log2(t))}}}$" for t in ticks])


def _round_box(ax, half_height: float) -> float:
    """Give ``ax`` limits that draw a unit circle round, whatever its final size.

    ``set_aspect("equal")`` shrinks the axes *box*, which leaves this panel's
    title floating at a different height from the panel beside or below it.
    Choosing the limits from the box matplotlib has already laid out keeps the
    grid aligned and the circle circular. Returns the half-width actually used,
    so the caller can place marginal text inside the axes.
    """
    fig = ax.figure
    fig.canvas.draw()
    box = ax.get_position()
    width = (box.x1 - box.x0) * fig.get_figwidth()
    height = (box.y1 - box.y0) * fig.get_figheight()
    half_width = half_height * width / height
    ax.set_xlim(-half_width, half_width)
    ax.set_ylim(-half_height, half_height)
    return half_width


def _dit_stage_usage(n: int, rng) -> tuple[list[dict[int, int]], float]:
    """Twiddle exponents each radix-2 DIT stage uses, counted per butterfly.

    Runs the textbook in-place loop (bit-reversal, then doubling butterfly
    sizes) on a random vector and tallies the exponent k of ``W_n^k`` at every
    butterfly. Returns the per-stage tallies and the largest deviation of the
    result from ``np.fft.fft`` -- computed, not assumed.
    """
    x = rng.standard_normal(n)
    a = x.astype(complex)

    j = 0
    for i in range(1, n):                      # bit-reversal permutation
        bit = n >> 1
        while j & bit:
            j ^= bit
            bit >>= 1
        j |= bit
        if i < j:
            a[i], a[j] = a[j], a[i]

    usage: list[dict[int, int]] = []
    size = 2
    while size <= n:
        counts: dict[int, int] = {}
        half = size // 2
        step = n // size                       # W_size^j == W_n^(j*step)
        for start in range(0, n, size):
            for j_butterfly in range(half):
                w = np.exp(-2j * np.pi * j_butterfly / size)
                u = a[start + j_butterfly]
                v = a[start + j_butterfly + half] * w
                a[start + j_butterfly] = u + v
                a[start + j_butterfly + half] = u - v
                exponent = j_butterfly * step
                counts[exponent] = counts.get(exponent, 0) + 1
        usage.append(counts)
        size *= 2

    error = float(np.abs(a - np.fft.fft(x)).max())
    return usage, error


# --------------------------------------------------------------------------- #
# 1. why the FFT exists: the cost curve
# --------------------------------------------------------------------------- #


def fft_cost_scaling() -> str:
    """N² against (N/2)·log₂N, with the ratio that actually sells the algorithm."""
    sizes = np.logspace(np.log10(N_LO), np.log10(N_HI), 600)
    dft = sizes ** 2
    fft = _fft_multiplies(sizes)
    ratio = dft / fft

    fig, axes = P.figure(height=5.6, nrows=2, height_ratios=[1.35, 1.0],
                         hspace=0.55)
    ax_cost, ax_ratio = axes

    # --- the two cost curves -------------------------------------------------
    ax_cost.plot(sizes, dft, color=P.WARN, label="naive DFT:  N² complex multiplies")
    ax_cost.plot(sizes, fft, color=P.ACCENT,
                 label="radix-2 FFT:  (N/2)·log₂N butterflies")

    for size in MARK_SIZES:
        exponent = int(np.log2(size))
        ax_cost.axvline(size, color=P.RULE, linestyle=(0, (3, 3)), linewidth=1.0,
                        zorder=0)
        ax_cost.plot([size], [size ** 2], marker="o", ls="none", ms=6.0,
                     color=P.WARN, mec=P.PANEL, mew=1.2, zorder=6)
        ax_cost.plot([size], [_fft_multiplies(float(size))], marker="o", ls="none",
                     ms=6.0, color=P.ACCENT, mec=P.PANEL, mew=1.2, zorder=6)
        ax_cost.text(size, 1.9e12, f"$2^{{{exponent}}}$", color=P.MUTED,
                     fontsize=8.6, ha="center", va="bottom")

    # The two working points, as a table in the corner no curve enters.
    rows = ["        N       DFT multiplies     FFT multiplies     speed-up"]
    for size in MARK_SIZES:
        exponent = int(np.log2(size))
        speed = 2.0 * size / exponent
        rows.append(
            f"{'2^' + str(exponent):>9s}{_grouped(size ** 2):>21s}"
            f"{_grouped(_fft_multiplies(float(size))):>19s}{speed:>13.1f}x"
        )
    ax_cost.text(1.05e6, 1.12, "\n".join(rows), family="monospace", fontsize=7.7,
                 color=P.SOFT, ha="right", va="bottom", zorder=7,
                 bbox=dict(boxstyle="round,pad=0.40", facecolor=P.PANEL,
                           edgecolor=P.RULE_SOFT, linewidth=1.0))

    ax_cost.set_xscale("log")
    ax_cost.set_yscale("log")
    ax_cost.set_xlim(6.0, 3.2e6)
    ax_cost.set_ylim(1.0, 1.0e13)
    _size_ticks(ax_cost)
    P.tidy(ax_cost, ylabel="complex multiplies",
           legend=["naive DFT:  N² complex multiplies",
                   "radix-2 FFT:  (N/2)·log₂N butterflies"],
           legend_loc="upper left")
    P.title(ax_cost, "The FFT is the difference between N² and N log N",
            subtitle="counting convention: complex multiplies, not real ones — "
                     "one per butterfly, ±1 and ±j included")

    # --- the ratio: the number that sells it ---------------------------------
    ax_ratio.plot(sizes, ratio, color=P.NOTE)
    for size in MARK_SIZES:
        value = ratio_at(size)
        ax_ratio.axvline(size, color=P.RULE, linestyle=(0, (3, 3)), linewidth=1.0,
                         zorder=0)
        ax_ratio.plot([size], [value], marker="o", ls="none", ms=6.0,
                      color=P.NOTE, mec=P.PANEL, mew=1.2, zorder=6)

    ax_ratio.annotate(
        "N = $2^{10}$:  " + f"{ratio_at(1 << 10):,.1f}× fewer multiplies",
        xy=(1 << 10, ratio_at(1 << 10)), xytext=(60.0, 1.4e3),
        color=P.NOTE, fontsize=9, ha="left", va="bottom", zorder=6,
        arrowprops=dict(arrowstyle="->", color=P.NOTE, linewidth=1.1,
                        shrinkA=3, shrinkB=3))
    ax_ratio.annotate(
        "N = $2^{20}$:  " + f"{ratio_at(1 << 20):,.0f}×",
        xy=(1 << 20, ratio_at(1 << 20)), xytext=(9.0e5, 1.9e5),
        color=P.NOTE, fontsize=9, ha="right", va="bottom", zorder=6,
        arrowprops=dict(arrowstyle="->", color=P.NOTE, linewidth=1.1,
                        shrinkA=3, shrinkB=3))

    ax_ratio.text(9.0, 2.6e5, "$R = N^2 / ((N/2)\\log_2 N) = 2N/\\log_2 N$",
                  color=P.INK, fontsize=10, ha="left", va="top", zorder=6)

    ax_ratio.set_xscale("log")
    ax_ratio.set_yscale("log")
    ax_ratio.set_xlim(6.0, 3.2e6)
    ax_ratio.set_ylim(2.0, 4.0e5)
    _size_ticks(ax_ratio)
    P.tidy(ax_ratio, xlabel=XLABEL_N, ylabel="speed-up factor")
    P.title(ax_ratio, "What that buys, as a single number",
            subtitle="the ratio grows without bound: doubling N more than "
                     "doubles it")

    for size in MARK_SIZES:
        ratio_value = ratio_at(size)
        print(f"[fft-cost-scaling] N = 2^{int(np.log2(size))}: DFT "
              f"{_grouped(size ** 2)} multiplies, FFT "
              f"{_grouped(_fft_multiplies(float(size)))} multiplies, "
              f"speed-up {ratio_value:,.1f}x")
    return P.render(fig)


# --------------------------------------------------------------------------- #
# 2. the FFT against a DFT written out longhand
# --------------------------------------------------------------------------- #


def fft_vs_dft_verification() -> str:
    """A direct DFT and ``np.fft.fft`` on the same signal, then their difference."""
    rng = np.random.default_rng(0)

    # --- top: one record, two algorithms, one spectrum ------------------------
    n = np.arange(VERIFY_N)
    signal = VERIFY_NOISE * rng.standard_normal(VERIFY_N)
    for bin_index, amplitude, phase in VERIFY_TONES:
        signal = signal + amplitude * np.cos(2 * np.pi * bin_index * n / VERIFY_N
                                             + phase)

    spectrum_dft = _direct_dft(signal)
    spectrum_fft = np.fft.fft(signal)
    top_error = float(np.abs(spectrum_dft - spectrum_fft).max())
    top_peak = float(np.abs(spectrum_fft).max())

    half = VERIFY_N // 2 + 1
    bins = np.arange(half)

    fig, axes = P.figure(height=5.4, nrows=2, height_ratios=[1.25, 1.0],
                         hspace=0.55)
    ax_spec, ax_err = axes

    ax_spec.plot(bins, np.abs(spectrum_fft[:half]), color=P.ACCENT, lw=1.8,
                 label="np.fft.fft (line)", zorder=3)
    ax_spec.plot(bins, np.abs(spectrum_dft[:half]), marker="o", ls="none", ms=5.5,
                 color=P.WARN, mec=P.PANEL, mew=0.9, label="direct DFT (markers)",
                 zorder=4)

    for bin_index, amplitude, phase in VERIFY_TONES:
        ax_spec.axvline(bin_index, color=P.RULE, linestyle=(0, (3, 3)),
                        linewidth=1.0, zorder=0)
        ax_spec.text(bin_index, top_peak * 1.10, f"{bin_index}", color=P.MUTED,
                     fontsize=8.4, ha="center", va="bottom")

    ax_spec.text(13.0, top_peak * 1.05,
                 "the two agree bin for bin:\n"
                 f"max |direct − fft| = {top_error:.2e}\n"
                 f"= {top_error / top_peak:.1e} of the peak |X|",
                 color=P.INK, fontsize=8.8, ha="left", va="top", zorder=6,
                 bbox=dict(boxstyle="round,pad=0.45", facecolor=P.PANEL,
                           edgecolor=P.RULE_SOFT, linewidth=1.0))
    ax_spec.set_xlim(-0.6, 32.6)
    ax_spec.set_ylim(0.0, top_peak * 1.30)
    P.tidy(ax_spec, ylabel="$|X[k]|$",
           legend=["np.fft.fft (line)", "direct DFT (markers)"],
           legend_loc="upper center", ncol=2)
    P.title(ax_spec,
            f"Two algorithms, one answer  —  N = {VERIFY_N}, three tones plus noise",
            subtitle="the markers are a hand-written N² DFT: they sit on the "
                     "line, not near it")

    # --- bottom: the same comparison, swept over N ---------------------------
    absolute, relative = [], []
    for size in VERIFY_SIZES:
        t = np.arange(size)
        probe = np.zeros(size)
        for bin_index, amplitude, phase in ((1, 1.0, 0.0), (3, 0.8, 0.7),
                                            (5, 0.6, 1.9)):
            probe = probe + amplitude * np.cos(2 * np.pi * bin_index * t / size
                                               + phase)
        direct = _direct_dft(probe)
        fast = np.fft.fft(probe)
        error = float(np.abs(direct - fast).max())
        absolute.append(error)
        relative.append(error / float(np.abs(fast).max()))

    ax_err.plot(VERIFY_SIZES, absolute, color=P.ACCENT, marker="o", ms=5.0,
                mec=P.PANEL, mew=0.9, label="max |direct − fft|")
    ax_err.plot(VERIFY_SIZES, relative, color=P.NOTE, marker="s", ms=4.6,
                mec=P.PANEL, mew=0.9, label="the same, relative to the peak $|X|$")
    ax_err.axhline(np.finfo(float).eps, color=P.WARN, linestyle=(0, (1.5, 2.5)),
                   linewidth=1.4, zorder=1)
    ax_err.text(8.4, np.finfo(float).eps * 1.5,
                f"float64 machine epsilon  {_sci(np.finfo(float).eps)}",
                color=P.WARN, fontsize=8.6, ha="left", va="bottom", zorder=6)

    ax_err.text(8.4, 8.5e-9,
                "round-off, not error.  A floating-point sum of N terms\n"
                "accumulates $\\approx N\\epsilon\\max|X|$, so the absolute\n"
                "difference climbs with N while the relative one stays\n"
                "at machine precision: no bin is wrong anywhere on this plot.",
                color=P.INK, fontsize=8.8, ha="left", va="top", zorder=6,
                bbox=dict(boxstyle="round,pad=0.45", facecolor=P.PANEL,
                          edgecolor=P.RULE_SOFT, linewidth=1.0))

    ax_err.set_xscale("log")
    ax_err.set_yscale("log")
    ax_err.set_xlim(6.5, 1400.0)
    ax_err.set_ylim(1e-16, 1e-8)
    ax_err.set_xticks(list(VERIFY_SIZES))
    ax_err.set_xticklabels([str(s) for s in VERIFY_SIZES])
    P.tidy(ax_err, xlabel=XLABEL_N, ylabel="difference between the two",
           legend=["max |direct − fft|",
                   "the same, relative to the peak $|X|$"],
           legend_loc="lower right")
    P.title(ax_err, "The gap is floating-point round-off, and it is measured here",
            subtitle="identical arithmetic, two different orders of summation")

    print(f"[fft-vs-dft-verification] N = {VERIFY_N}: max |direct DFT - np.fft.fft| "
          f"= {top_error:.3e} (peak |X| = {top_peak:.1f}, "
          f"{top_error / top_peak:.2e} of peak)")
    for size, error, rel in zip(VERIFY_SIZES, absolute, relative):
        print(f"[fft-vs-dft-verification]   N = {size:5d}  max abs {error:.3e}"
              f"   relative to peak {rel:.3e}")
    return P.render(fig)


# --------------------------------------------------------------------------- #
# 3. what the transform is for: resolution
# --------------------------------------------------------------------------- #


def _tone_signal(size: int) -> np.ndarray:
    """The chapter's three tones, sampled on a record of ``size`` points.

    Frequencies are fixed in *cycles per 64-sample record*, so the same physical
    signal is used for both record lengths and the two panels share one axis.
    """
    t = np.arange(size)
    out = np.zeros(size)
    for cycles, amplitude, phase in TONE_CYCLES:
        out = out + amplitude * np.cos(2 * np.pi * cycles * t / RECORD_REF + phase)
    return out


def fft_tone_spectrum() -> str:
    """Three tones, two record lengths: the same signal, one line or two."""
    fig, axes = P.figure(height=5.4, nrows=2, sharex=True, hspace=0.55)
    ax_short, ax_long = axes

    measured = {}
    for ax, (size, window, window_label) in zip(axes, SPECTRUM_PANELS):
        t = np.arange(size)
        signal = _tone_signal(size)
        taper = np.hanning(size) if window == "hann" else np.ones(size)

        spectrum = np.abs(np.fft.rfft(signal * taper))
        floor = 10.0 ** (FLOOR_DB / 20.0)
        decibels = 20.0 * np.log10(np.maximum(spectrum / spectrum.max(), floor))
        axis = np.arange(spectrum.size) * RECORD_REF / size

        ax.plot(axis, decibels, color=P.ACCENT, lw=1.6)
        for cycles, _, _ in TONE_CYCLES:
            ax.axvline(cycles, color=P.RULE, linestyle=(0, (3, 3)), linewidth=1.0,
                       zorder=0)

        spacing = RECORD_REF / size                 # bin spacing, in axis units
        separation = (TONE_CYCLES[1][0] - TONE_CYCLES[0][0]) / spacing
        measured[size] = (spacing, separation, window_label, axis, decibels)
        ax.set_xlim(0.0, 13.0)
        ax.set_ylim(FLOOR_DB, 12.0)

    # --- short record: the two close tones are one line ----------------------
    ax_short.text(3.0, 2.0, "third tone", color=P.MUTED, fontsize=8.6,
                  ha="center", va="bottom")
    ax_short.annotate("10.0 and 10.3 arrive as one line", xy=(10.0, -1.6),
                      xytext=(5.4, 3.4), color=P.NOTE, fontsize=8.8, ha="left",
                      va="bottom", zorder=6,
                      arrowprops=dict(arrowstyle="->", color=P.NOTE, linewidth=1.1,
                                      shrinkA=3, shrinkB=3))

    # --- long record: two lines, and the gap between them --------------------
    ax_long.annotate("", xy=(10.0, 1.4), xytext=(10.3, 1.4),
                     arrowprops=dict(arrowstyle="<->", color=P.OPTICAL,
                                     linewidth=1.2, shrinkA=0, shrinkB=0))
    ax_long.text(10.15, 2.2,
                 "0.3 record-cycles = 2.4 bins of 512: two lines",
                 color=P.OPTICAL, fontsize=8.8, ha="center", va="bottom", zorder=6)

    short_spacing, short_separation, short_window = measured[SPECTRUM_PANELS[0][0]][:3]
    long_spacing, long_separation, long_window = measured[SPECTRUM_PANELS[1][0]][:3]
    P.title(ax_short, "Short record: one line",
            subtitle=f"N = {SPECTRUM_PANELS[0][0]} · {short_window} window, main "
                     f"lobe 4 bins wide · bin spacing "
                     f"$f_s/{SPECTRUM_PANELS[0][0]}$ = {short_spacing:.2f} "
                     f"record-cycle · the pair is {short_separation:.1f} bins apart")
    P.title(ax_long, "Long record: two lines",
            subtitle=f"N = {SPECTRUM_PANELS[1][0]} · {long_window} window, leakage "
                     f"skirts and all · bin spacing "
                     f"$f_s/{SPECTRUM_PANELS[1][0]}$ = {long_spacing:.3f} "
                     f"record-cycles · the pair is {long_separation:.1f} bins apart")
    P.tidy(ax_long, xlabel="frequency  $f\\cdot64/f_s$  (cycles per 64-sample "
                           "record — both panels, same signal)",
           ylabel="magnitude (dB, each panel normalised to its own peak)")

    for size in (panel[0] for panel in SPECTRUM_PANELS):
        spacing, separation, window_label, axis, decibels = measured[size]
        peak_bins = [float(axis[i]) for i in range(1, len(decibels) - 1)
                     if decibels[i] > -12.0
                     and decibels[i] >= decibels[i - 1]
                     and decibels[i] >= decibels[i + 1]]
        print(f"[fft-tone-spectrum] N = {size}: {window_label} window, bin spacing "
              f"fs/{size} = {spacing:.3f} record-cycles, close pair "
              f"{separation:.2f} bins apart, peaks above -12 dB at "
              f"{[round(b, 3) for b in peak_bins]}")
    return P.render(fig)


# --------------------------------------------------------------------------- #
# 4. twiddles: one circle, one small table
# --------------------------------------------------------------------------- #


def fft_twiddle_geometry() -> str:
    """The eighth roots of unity, and which of them each DIT stage multiplies by."""
    exponent = np.arange(TWIDDLE_N)
    phase = -2 * np.pi * exponent / TWIDDLE_N

    fig, axes = P.figure(height=6.2, nrows=2, height_ratios=[1.25, 1.0],
                         hspace=0.50)
    ax_circle, ax_stage = axes

    # --- top: the circle -----------------------------------------------------
    theta = np.linspace(0.0, 2.0 * np.pi, 400)
    half_width = _round_box(ax_circle, 1.34)
    ax_circle.plot(np.cos(theta), np.sin(theta), color=P.RULE, lw=1.4, zorder=1)
    ax_circle.axhline(0.0, color=P.RULE_SOFT, lw=1.0, zorder=0)
    ax_circle.axvline(0.0, color=P.RULE_SOFT, lw=1.0, zorder=0)
    ax_circle.grid(False)
    for k in exponent:                          # a spoke per point, from the origin
        ax_circle.plot([0.0, np.cos(phase[k])], [0.0, np.sin(phase[k])],
                       color=P.ACCENT, lw=1.2, zorder=2)
    ax_circle.scatter(np.cos(phase), np.sin(phase), s=58, color=P.NOTE,
                      edgecolors=P.PANEL, linewidths=1.3, zorder=5)

    # The conjugate pairs, joined across the real axis they mirror in.
    for upper, lower in ((1, 7), (3, 5)):
        ax_circle.plot([np.cos(phase[upper]), np.cos(phase[lower])],
                       [np.sin(phase[upper]), np.sin(phase[lower])],
                       color=P.OPTICAL, lw=1.1, linestyle=(0, (3, 2)), zorder=3)

    labels = {0: "$W_8^0 = 1$", 1: "$W_8^1$", 2: "$W_8^2 = -j$", 3: "$W_8^3$",
              4: "$W_8^4 = -1$", 5: "$W_8^5$", 6: "$W_8^6 = +j$", 7: "$W_8^7$"}
    radius = 1.16
    for k in exponent:
        x, y = radius * np.cos(phase[k]), radius * np.sin(phase[k])
        ha = "left" if np.cos(phase[k]) > 0.1 else ("right"
                                                   if np.cos(phase[k]) < -0.1
                                                   else "center")
        va = "bottom" if np.sin(phase[k]) > 0.1 else ("top"
                                                      if np.sin(phase[k]) < -0.1
                                                      else "center")
        ax_circle.text(x, y, labels[k], color=P.INK, fontsize=9, ha=ha, va=va,
                       zorder=6)

    ax_circle.text(-half_width + 0.15, 0.50,
                   "one multiply is one rotation:\n"
                   "$W_8^k$ turns a sample by $-45k°$\n"
                   "around this circle",
                   color=P.MUTED, fontsize=8.6, ha="left", va="top", zorder=6)
    ax_circle.text(half_width - 0.15, 0.50,
                   "the lower half mirrors the upper:\n"
                   "$W_8^1$ with $W_8^7$, $W_8^3$ with $W_8^5$.\n"
                   "A naive DFT needs all eight.",
                   color=P.OPTICAL, fontsize=8.6, ha="right", va="top", zorder=6)
    ax_circle.set_xticks([])
    ax_circle.set_yticks([])
    P.title(ax_circle, "The twiddles are the eighth roots of unity",
            subtitle="$W_8^k = e^{-j2\\pi k/8}$ — clockwise, one step per k")

    # --- bottom: what each stage of the FFT actually reaches for -------------
    rng = np.random.default_rng(0)
    usage, dit_error = _dit_stage_usage(TWIDDLE_N, rng)
    naive_counts = {int(k): TWIDDLE_N for k in exponent}   # N twiddles, N outputs

    rows = [("naive DFT", 0, naive_counts, P.MUTED)]
    for stage, counts in enumerate(usage):
        size = 2 ** (stage + 1)
        rows.append((f"stage {stage + 1}\n{size}-point", stage + 1, counts,
                     P.SERIES[stage % len(P.SERIES)]))

    for label, row, counts, colour in rows:
        ax_stage.axhline(row, color=P.RULE_SOFT, lw=0.9, zorder=0)
        for k, count in counts.items():
            ax_stage.scatter([k], [row], s=16.0 * count + 40.0, color=colour,
                             edgecolors=P.PANEL, linewidths=1.2, zorder=5)
            ax_stage.text(k + 0.19, row, str(count), color=P.SOFT, fontsize=8.4,
                          ha="left", va="center", zorder=6)
    for k in exponent:
        ax_stage.axvline(k, color=P.RULE_SOFT, lw=0.9, zorder=0)

    ax_stage.text(4.35, 3.55,
                  "$N = 8$: 12 butterflies reuse 4 distinct twiddles — 12 complex\n"
                  "multiplies. A naive DFT: 8 twiddles × 8 outputs = 64 products.",
                  color=P.INK, fontsize=8.8, ha="left", va="center", zorder=7,
                  bbox=dict(boxstyle="round,pad=0.45", facecolor=P.PANEL,
                            edgecolor=P.RULE_SOFT, linewidth=1.0))

    ax_stage.set_xlim(-0.65, 8.30)
    ax_stage.set_ylim(-1.05, 4.15)
    ax_stage.set_xticks(list(exponent))
    ax_stage.set_xticklabels(
        [f"$W_8^{{{k}}}$\n{int(np.degrees(phase[k]))}°" for k in exponent])
    ax_stage.set_yticks([0, 1, 2, 3])
    ax_stage.set_yticklabels([label for label, _, _, _ in rows])
    ax_stage.grid(axis="y", visible=False)
    P.tidy(ax_stage, xlabel="twiddle exponent  k  —  the markers are the count of "
                            "butterflies that use it",
           ylabel="stage")
    P.title(ax_stage, "Each stage reaches for a different handful",
            subtitle="marker area is how many butterflies reuse that twiddle — "
                     "the same k as the circle above")

    for stage, counts in enumerate(usage):
        size = 2 ** (stage + 1)
        print(f"[fft-twiddle-geometry] stage {stage + 1} ({size}-point "
              f"butterflies): exponents "
              f"{sorted(counts.items())}, {sum(counts.values())} butterflies")
    print(f"[fft-twiddle-geometry] N = {TWIDDLE_N}: "
          f"{sum(c for counts in usage for c in counts.values())} butterflies, "
          f"{len(set(k for counts in usage for k in counts))} distinct twiddle "
          f"values, naive DFT {TWIDDLE_N ** 2} products with {TWIDDLE_N} distinct "
          f"values")
    print(f"[fft-twiddle-geometry] the in-place DIT loop matches np.fft.fft to "
          f"{dit_error:.2e}")
    return P.render(fig)


FIGURES = {
    "fft-cost-scaling": fft_cost_scaling,
    "fft-vs-dft-verification": fft_vs_dft_verification,
    "fft-tone-spectrum": fft_tone_spectrum,
    "fft-twiddle-geometry": fft_twiddle_geometry,
}
