"""Computed figures for the convolution chapter.

Four numpy/matplotlib figures, in the order the article uses them:

    convolution-worked-example   x[n] * h[n] the slow way, sample by sample
    convolution-theorem          the same answer from an fft/ifft round trip
    moving-average-filter        the simplest useful kernel, honestly assessed
    convolution-cost             multiplies per output, and where the FFT takes over

Every number on these figures is measured on the same arrays the curves are drawn
from: the theorem's error is the actual ``max|ifft(...) - convolve|`` of this
module's ``x`` and ``h``, the moving average's sidelobe is the actual peak of its
``freqz`` response, and the crossover is the smallest filter length at which an
overlap-save block transform really is the cheaper form. An annotation therefore
cannot drift away from the curve under it.

Conventions, shared with the rest of the ``plots_*`` family: frequency is
normalised to Nyquist (``w / pi``, so 1.0 is the folding frequency) and magnitude
is in dB, clipped at a floor rather than left to dive.

The chapter's running example is deliberately asymmetric -- a symmetric pair
convolves into something symmetric, which hides the index arithmetic the first
figure exists to show.
"""

from __future__ import annotations

import numpy as np
from scipy import signal

from . import plotstyle as P

# Nothing in this module draws random numbers. The generator is declared anyway,
# so a stochastic figure added later has one obvious, reproducible source.
RNG = np.random.default_rng(0)

# --- the worked pair, shared by figures 1 and 2 -----------------------------
X_SEQ = np.array([1.0, 2.0, 3.0, 2.0, 1.0])     # n = 0..4
H_SEQ = np.array([1.0, 0.5, -0.5])              # n = 0..2
OUT_LEN = len(X_SEQ) + len(H_SEQ) - 1           # 7: the shortest block that is linear

SPEC_N = 2048            # points on the theorem's frequency axis
DB_FLOOR = -60.0         # spectra stop here instead of diving to -inf
MA_TAPS = 5              # the moving average of figure 3
MAX_TAPS = 4096          # the longest filter length figure 4 plots


# --------------------------------------------------------------------------- #
# local helpers
# --------------------------------------------------------------------------- #


def _next_pow2(value: int) -> int:
    """Smallest power of two >= ``value``; an exact power is returned unchanged."""
    value = max(1, int(value))
    return 1 << (value - 1).bit_length()


def _stem(ax, n, values, colour, *, markersize=4.2):
    """A stem plot in the house palette; matplotlib's defaults are too loud."""
    markerline, stemlines, baseline = ax.stem(n, values)
    markerline.set_color(colour)
    markerline.set_markersize(markersize)
    stemlines.set_color(colour)
    stemlines.set_linewidth(1.2)
    baseline.set_color(P.RULE_SOFT)
    baseline.set_linewidth(1.0)
    return markerline, stemlines, baseline


def _callout(ax, text, x, y, *, colour=P.SOFT, size=8.4):
    """A monospace box for numbers, parked in space no curve occupies."""
    ax.text(x, y, text, family="monospace", fontsize=size, color=colour,
            ha="left", va="top", zorder=6,
            bbox=dict(boxstyle="round,pad=0.45", facecolor=P.PANEL,
                      edgecolor=P.RULE_SOFT, linewidth=1.0))


def _seq_text(name, values) -> str:
    """``x = {1, 2, 3, 2, 1}   at n = 0..4`` -- built from the array itself."""
    body = ", ".join(f"{v:g}" for v in values)
    return f"{name} = {{{body}}}   at n = 0..{len(values) - 1}"


# --------------------------------------------------------------------------- #
# 1. the worked example
# --------------------------------------------------------------------------- #


def convolution_worked_example() -> str:
    """x[n], h[n] and y[n] on one shared axis, with the index arithmetic spelled out."""
    n_x = np.arange(len(X_SEQ))
    n_h = np.arange(len(H_SEQ))
    y = np.convolve(X_SEQ, H_SEQ)
    n_y = np.arange(len(y))

    fig, axes = P.figure(height=5.0, nrows=3, sharex=True, hspace=0.62)
    ax_x, ax_h, ax_y = axes

    _stem(ax_x, n_x, X_SEQ, P.ACCENT)
    _stem(ax_h, n_h, H_SEQ, P.NOTE)
    _stem(ax_y, n_y, y, P.ACCENT_DARK)

    # The sample whose arithmetic the figure spells out gets a ring around it.
    ax_y.plot([2], [y[2]], marker="o", markersize=8.0, markerfacecolor="none",
              markeredgecolor=P.WARN, markeredgewidth=1.6, zorder=7)

    # --- top two panels: what goes in ---------------------------------------
    _callout(ax_x, _seq_text("x", X_SEQ), 5.7, 4.15, colour=P.ACCENT_DARK)
    _callout(ax_h, _seq_text("h", H_SEQ), 5.7, 1.60, colour=P.NOTE)

    ax_x.set_ylim(-0.5, 4.6)
    ax_h.set_ylim(-1.1, 1.75)
    ax_y.set_ylim(-1.4, 4.4)
    ax_y.set_xlim(-2, 14)

    P.title(ax_x, "x[n]  ·  the input, five samples")
    P.title(ax_h, "h[n]  ·  the kernel, three samples")
    P.title(ax_y, "y[n]  ·  the output, read off one sample at a time")

    P.tidy(ax_x, ylabel="x[n]")
    P.tidy(ax_h, ylabel="h[n]")

    # --- bottom panel: where the extra sample comes from --------------------
    rows = [
        f"len(y) = len(x) + len(h) - 1 = {OUT_LEN} samples",
        "",
        "y[2] = x[0]h[2] + x[1]h[1] + x[2]h[0]",
        "     = " + f"{X_SEQ[0]:g}({H_SEQ[2]:g}) + {X_SEQ[1]:g}({H_SEQ[1]:g})"
        + f" + {X_SEQ[2]:g}({H_SEQ[0]:g}) = {y[2]:.2f}",
    ]
    _callout(ax_y, "\n".join(rows), 5.7, 3.35, colour=P.ACCENT_DARK)
    P.tidy(ax_y, xlabel="sample index  n", ylabel="y[n]", xaxis_int=True)
    return P.render(fig)


# --------------------------------------------------------------------------- #
# 2. the convolution theorem
# --------------------------------------------------------------------------- #


def convolution_theorem() -> str:
    """The same convolution through fft/ifft, with the error measured, not asserted."""
    n_y = np.arange(OUT_LEN)
    y_conv = np.convolve(X_SEQ, H_SEQ)

    # The whole trick: at length N the circular product has nowhere to wrap to,
    # so the round trip is the linear convolution and nothing else.
    y_fft = np.real(np.fft.ifft(np.fft.fft(X_SEQ, OUT_LEN) * np.fft.fft(H_SEQ, OUT_LEN)))
    error = float(np.max(np.abs(y_fft - y_conv)))

    # A shorter block than OUT_LEN would fold the tail back over the head; this
    # is exactly why the zero-padding is not optional.
    wrapped = np.real(np.fft.ifft(np.fft.fft(X_SEQ, 5) * np.fft.fft(H_SEQ, 5)))

    # Dense spectra. N_SPEC >= OUT_LEN, so the pointwise product is the DTFT of
    # the linear convolution and |Y| must equal |X|*|H| at every frequency.
    freq = np.fft.rfftfreq(SPEC_N) * 2.0          # 0..1, 1 = Nyquist
    X = np.fft.rfft(X_SEQ, SPEC_N)
    H = np.fft.rfft(H_SEQ, SPEC_N)
    Y = X * H
    floor = 10.0 ** (DB_FLOOR / 20.0)
    x_db = 20.0 * np.log10(np.maximum(np.abs(X), floor))
    h_db = 20.0 * np.log10(np.maximum(np.abs(H), floor))
    y_db = 20.0 * np.log10(np.maximum(np.abs(Y), floor))
    product_db = 20.0 * np.log10(np.maximum(np.abs(X) * np.abs(H), floor))
    spectral_rel = float(np.max(np.abs(np.abs(X) * np.abs(H) - np.abs(Y)))
                         / np.max(np.abs(Y)))

    fig, axes = P.figure(height=5.0, nrows=2, hspace=0.55)
    ax_spec, ax_out = axes

    # --- top: one multiplication, frequency by frequency --------------------
    # The shaded band is |H| in dB: the gap that turns |X| into |Y|.
    ax_spec.fill_between(freq, x_db, y_db, color=P.NOTE, alpha=0.10,
                         linewidth=0.0, zorder=1)
    ax_spec.plot(freq, x_db, color=P.OPTICAL, label="|X(f)|  the input")
    ax_spec.plot(freq, h_db, color=P.NOTE, label="|H(f)|  the kernel")
    ax_spec.plot(freq, y_db, color=P.ACCENT, label="|Y(f)|  the output")
    ax_spec.plot(freq, product_db, color=P.INK, linewidth=1.0,
                 linestyle=(0, (1.5, 2.5)), label="|X(f)|·|H(f)|  computed directly")

    ax_spec.set_xlim(0, 1)
    ax_spec.set_ylim(DB_FLOOR, 38)
    P.title(ax_spec, "The convolution theorem: in frequency it is a product",
            subtitle=f"|Y(f)| and |X(f)|·|H(f)| agree to {spectral_rel:.1e} "
                     f"relative (measured); spectra clipped at {DB_FLOOR:.0f} dB")

    # The N explanation goes in the empty top-right corner; the four legend rows
    # go in the equally empty lower left, where every curve is still above +8 dB.
    rows = [
        f"N = len(x) + len(h) - 1 = {OUT_LEN}",
        f"at N = 5, y[0] reads {wrapped[0]:.2f}, not {y_conv[0]:.2f}:",
        "the padding is what removes the wrap-around",
    ]
    _callout(ax_spec, "\n".join(rows), 0.52, 36.0, colour=P.SOFT)
    P.tidy(ax_spec, xlabel="normalised frequency  (1 = Nyquist)",
           ylabel="magnitude  (dB)",
           legend=["|X(f)|  the input", "|H(f)|  the kernel",
                   "|Y(f)|  the output", "|X(f)|·|H(f)|  computed directly"],
           legend_loc="lower left")

    # --- bottom: the round trip lands on the same samples -------------------
    ax_out.plot(n_y, y_fft, color=P.WARN, marker="o", markersize=4.6,
                label="y = ifft(fft(x, N) · fft(h, N))")
    ax_out.plot(n_y, y_conv, linestyle="none", marker="s", markersize=9.0,
                markerfacecolor="none", markeredgecolor=P.ACCENT_DARK,
                markeredgewidth=1.5, label="numpy.convolve(x, h)")

    ax_out.set_xlim(-2, 14)
    ax_out.set_ylim(-1.4, 4.4)
    P.title(ax_out, "The inverse transform returns the same seven samples")
    rows = [
        f"N = {OUT_LEN}, so no wrap-around",
        f"max |y_fft - convolve| = {error:.2e}",
    ]
    _callout(ax_out, "\n".join(rows), 5.7, 3.35, colour=P.WARN)
    P.tidy(ax_out, xlabel="sample index  n", ylabel="y[n]", xaxis_int=True,
           legend=["y = ifft(fft(x, N) · fft(h, N))", "numpy.convolve(x, h)"],
           legend_loc="lower right")
    return P.render(fig)


# --------------------------------------------------------------------------- #
# 3. the moving average
# --------------------------------------------------------------------------- #


def moving_average_filter() -> str:
    """Five equal taps: unity DC gain, a sinc-like response, an honest sidelobe."""
    h = np.ones(MA_TAPS) / MA_TAPS                 # normalised: sum(h) = 1
    delay = (MA_TAPS - 1) / 2.0                    # 2 samples of group delay
    null_freq = 2.0 / MA_TAPS                      # 0.4 of Nyquist = 1/5 cycle/sample

    fig, axes = P.figure(height=5.2, nrows=3, hspace=0.72)
    ax_taps, ax_mag, ax_step = axes

    # --- 1: the taps --------------------------------------------------------
    n = np.arange(MA_TAPS)
    _stem(ax_taps, n, h, P.ACCENT)
    ax_taps.set_xlim(-0.6, 6.4)
    ax_taps.set_ylim(-0.03, 0.44)
    rows = [
        "sum h[n] = 1  ->  DC gain 0 dB",
        f"unnormalised the five taps sum to {MA_TAPS} (+{20 * np.log10(MA_TAPS):.1f} dB)",
    ]
    _callout(ax_taps, "\n".join(rows), 0.35, 0.42, colour=P.ACCENT_DARK)
    P.title(ax_taps, "A 5-point moving average: five equal taps")
    P.tidy(ax_taps, xlabel="tap index  n", ylabel="tap value  h[n]", xaxis_int=True)

    # --- 2: what those taps do to frequency ---------------------------------
    w, H = signal.freqz(h, worN=4096)
    freq = w / np.pi                               # normalised to Nyquist
    mag_db = 20.0 * np.log10(np.maximum(np.abs(H), 10.0 ** (DB_FLOOR / 20.0)))
    null_at = float(freq[int(np.argmin(np.abs(freq - null_freq)))])
    after_null = freq > null_at + 0.02
    lobe_at = int(np.argmax(np.where(after_null, mag_db, -np.inf)))
    lobe_db = float(mag_db[lobe_at])
    lobe_freq = float(freq[lobe_at])

    ax_mag.plot(freq, mag_db, color=P.ACCENT)
    ax_mag.axvline(null_at, color=P.NOTE, linestyle=(0, (2, 2)), linewidth=1.3,
                   zorder=1)
    ax_mag.axhline(lobe_db, color=P.WARN, linestyle=(0, (1.5, 2.5)), linewidth=1.4,
                   zorder=1)
    # The null's label sits to the left of the dive, in the band below the
    # passband that no part of the response occupies.
    ax_mag.annotate(f"first null  f = {null_at:.1f}  (f_s/{MA_TAPS})",
                    xy=(null_at, -52), xytext=(0.13, -27), color=P.NOTE,
                    fontsize=8.6, ha="left", va="bottom", zorder=6,
                    arrowprops=dict(arrowstyle="->", color=P.NOTE, linewidth=1.1,
                                    shrinkA=3, shrinkB=3))
    # Above the -12 dB lobe line the right-hand side is empty, so both the
    # measured lobe and the continuous-sinc comparison fit there.
    lobe_text = (f"highest lobe {lobe_db:.1f} dB: only {abs(lobe_db):.0f} dB down\n"
                 f"(a continuous sinc reaches {20 * np.log10(0.2172):.1f} dB)")
    ax_mag.annotate(lobe_text, xy=(lobe_freq, lobe_db), xytext=(0.50, 8.0),
                    color=P.WARN, fontsize=8.6, ha="left", va="top", zorder=6,
                    arrowprops=dict(arrowstyle="->", color=P.WARN, linewidth=1.1,
                                    shrinkA=3, shrinkB=3))
    ax_mag.set_xlim(0, 1)
    ax_mag.set_ylim(DB_FLOOR, 12)
    P.title(ax_mag, "A sinc-like response with deep nulls -- and shallow lobes")
    P.tidy(ax_mag, xlabel="normalised frequency  (1 = Nyquist)",
           ylabel="magnitude  (dB)")

    # --- 3: the ramp, and the delay that comes with it ----------------------
    n_step = np.arange(MA_TAPS + 3)
    step = np.cumsum(np.r_[h, np.zeros(3)])        # 0.2, 0.4, 0.6, 0.8, 1.0, 1.0...
    ax_step.plot(n_step, np.ones_like(n_step, dtype=float), color=P.MUTED,
                 linestyle=(0, (4, 3)), linewidth=1.3, label="input step  u[n]")
    ax_step.plot(n_step, step, color=P.ACCENT, marker="o", markersize=4.6,
                 label="step response  s[n]")
    ax_step.axvline(delay, color=P.NOTE, linestyle=(0, (2, 2)), linewidth=1.3,
                    zorder=1)
    ax_step.plot([delay], [step[int(delay)]], marker="o", markersize=8.0,
                 markerfacecolor="none", markeredgecolor=P.NOTE, markeredgewidth=1.6,
                 zorder=6)
    ax_step.text(2.2, 0.16,
                 f"group delay (N-1)/2 = {delay:.0f} samples\n"
                 f"ramp done at n = N-1 = {MA_TAPS - 1}",
                 color=P.NOTE, fontsize=8.8, ha="left", va="bottom")
    ax_step.annotate("", xy=(MA_TAPS - 1, 1.12), xytext=(0, 1.12),
                     arrowprops=dict(arrowstyle="<->", color=P.MUTED, linewidth=1.0))
    ax_step.text(delay, 1.145, f"{MA_TAPS}-sample ramp", color=P.SOFT, fontsize=8.8,
                 ha="center", va="bottom")
    ax_step.set_xlim(-1, 8)
    ax_step.set_ylim(-0.05, 1.32)
    P.title(ax_step, "The step response: a ramp, not an edge")
    P.tidy(ax_step, xlabel="sample index  n", ylabel="step response", xaxis_int=True,
           legend=["input step  u[n]", "step response  s[n]"],
           legend_loc="center right")
    return P.render(fig)


# --------------------------------------------------------------------------- #
# 4. what a convolution costs
# --------------------------------------------------------------------------- #


def convolution_cost() -> str:
    """Multiplies per output: direct against an overlap-save block transform."""
    n_taps = np.arange(1, MAX_TAPS + 1)
    block = np.array([_next_pow2(2 * int(v)) for v in n_taps])
    # The chapter's accounting: two size-B transforms at 2 B log2 B real
    # multiplies, plus B for the pointwise product, per block of B outputs. Real
    # overlap-save yields B - N + 1 outputs per block, which pushes the crossover
    # a little to the right; the idealisation is what makes the two curves
    # comparable on one axis. B = next_pow2(2N) so the filter fits in a block.
    fft_per_output = 2.0 * np.log2(block) + 1.0          # (2 B log2 B + B) / B
    direct_per_output = n_taps.astype(float)             # N multiplies per sample

    # The staircase crosses the diagonal on a tie; the honest statement is both.
    at_least_as_cheap = n_taps[fft_per_output <= direct_per_output]
    strictly_cheaper = n_taps[fft_per_output < direct_per_output]
    crossover = int(at_least_as_cheap[0])                # 11, where both cost 11
    takes_over = int(strictly_cheaper[0])                # 12, first strict win

    fig, axes = P.figure(height=5.2, nrows=2, hspace=0.62)
    ax_cost, ax_lat = axes

    # --- top: multiplies per output sample, log-log -------------------------
    ax_cost.plot(n_taps, direct_per_output, color=P.OPTICAL,
                 label="direct: N per output")
    ax_cost.plot(n_taps, fft_per_output, color=P.ACCENT, drawstyle="steps-post",
                 label="overlap-save FFT: 2·log2(B) + 1")
    ax_cost.plot([crossover], [crossover], marker="o", markersize=8.0,
                 markerfacecolor="none", markeredgecolor=P.WARN, markeredgewidth=1.6,
                 zorder=7)
    ax_cost.axvline(crossover, color=P.WARN, linestyle=(0, (2, 2)), linewidth=1.1,
                    zorder=1)

    ax_cost.set_xscale("log")
    ax_cost.set_yscale("log")
    ax_cost.set_xlim(0.95, 4300)
    # The top of the axis is deliberately above the longest curve: the only space
    # in a log-log cost plot that no curve crosses is above the direct line.
    ax_cost.set_ylim(0.9, 60000)
    P.title(ax_cost, "Multiplies per output sample: the FFT buys the long filter")
    rows = [
        f"crossover = {crossover} multiplies/output",
        f"direct wins below N = {crossover}",
        f"FFT wins from N = {takes_over}",
    ]
    _callout(ax_cost, "\n".join(rows), 150, 45000, colour=P.MUTED)
    ax_cost.annotate(f"N = {crossover}", xy=(crossover, crossover), xytext=(1.4, 100),
                     color=P.WARN, fontsize=8.6, ha="left", va="bottom", zorder=6,
                     arrowprops=dict(arrowstyle="->", color=P.WARN, linewidth=1.1,
                                     shrinkA=3, shrinkB=3))
    P.tidy(ax_cost, xlabel="filter length  N  (taps)",
           ylabel="real multiplies per output sample",
           legend=["direct: N per output",
                   "overlap-save FFT: 2·log2(B) + 1"],
           legend_loc="upper left")

    # --- bottom: what the block transform costs in time ---------------------
    blocks = (2.0 ** np.arange(1, 14)).astype(float)     # 2 .. 8192 samples
    ax_lat.plot(blocks, np.zeros_like(blocks), color=P.OPTICAL, linewidth=2.4,
                label="direct form: no block latency")
    ax_lat.plot(blocks, blocks, color=P.NOTE, marker="o", markersize=3.8,
                label="overlap-save: one block = B samples")
    ax_lat.plot([1024], [1024], marker="o", markersize=8.0, markerfacecolor="none",
                markeredgecolor=P.WARN, markeredgewidth=1.6, zorder=7)
    ax_lat.annotate("B = 1024  ->  one block = 1024 samples late",
                    xy=(1024, 1024), xytext=(100, 5000), color=P.WARN, fontsize=8.6,
                    ha="left", va="bottom", zorder=6,
                    arrowprops=dict(arrowstyle="->", color=P.WARN, linewidth=1.1,
                                    shrinkA=3, shrinkB=3))
    ax_lat.text(2.2, 14000, "small equaliser (tens of taps):\n"
                            "direct form, no block latency",
                color=P.SOFT, fontsize=8.6, ha="left", va="top")
    ax_lat.text(200, 14000, "dispersion compensator (10^3 taps):\n"
                            "overlap-save, one block late",
                color=P.SOFT, fontsize=8.6, ha="left", va="top")
    ax_lat.set_xscale("log")
    ax_lat.set_xlim(1.6, 9000)
    # Headroom above the diagonal so the two regime labels clear the subtitle.
    ax_lat.set_ylim(-150, 15000)
    P.title(ax_lat, "The price of the block: latency, in samples",
            subtitle="the direct form's (N-1)/2 sample group delay is separate; "
                     "this is added block latency")
    P.tidy(ax_lat, xlabel="FFT block size  B  (samples)",
           ylabel="added latency  (samples)",
           legend=["direct form: no block latency",
                   "overlap-save: one block = B samples"],
           legend_loc="center left")
    return P.render(fig)


FIGURES = {
    "convolution-worked-example": convolution_worked_example,
    "convolution-theorem": convolution_theorem,
    "moving-average-filter": moving_average_filter,
    "convolution-cost": convolution_cost,
}


# --------------------------------------------------------------------------- #
# the numbers the figures annotate, printed on demand
# --------------------------------------------------------------------------- #


def _diagnostics() -> None:
    """Print every number a figure claims, so an annotation can be audited."""
    y_conv = np.convolve(X_SEQ, H_SEQ)
    print(f"worked example: {_seq_text('x', X_SEQ)}")
    print(f"                {_seq_text('h', H_SEQ)}")
    print(f"                y = {np.array2string(y_conv, precision=2)}"
          f"  len = {OUT_LEN}")
    print(f"                y[2] = {y_conv[2]:.4f} (annotated as {y_conv[2]:.2f})")

    y_fft = np.real(np.fft.ifft(np.fft.fft(X_SEQ, OUT_LEN)
                                * np.fft.fft(H_SEQ, OUT_LEN)))
    wrapped = np.real(np.fft.ifft(np.fft.fft(X_SEQ, 5) * np.fft.fft(H_SEQ, 5)))
    print(f"theorem: N = {OUT_LEN}, max |y_fft - convolve| = "
          f"{np.max(np.abs(y_fft - y_conv)):.3e}")
    print(f"         N = 5 wraps: y[0] = {wrapped[0]:.4f} "
          f"(linear answer {y_conv[0]:.4f})")
    freq = np.fft.rfftfreq(SPEC_N) * 2.0
    X = np.fft.rfft(X_SEQ, SPEC_N)
    H = np.fft.rfft(H_SEQ, SPEC_N)
    Y = X * H
    dev = float(np.max(np.abs(np.abs(X) * np.abs(H) - np.abs(Y))))
    print(f"         |Y| vs |X|·|H|: absolute {dev:.3e}, relative to peak "
          f"{dev / np.max(np.abs(Y)):.3e}")

    h = np.ones(MA_TAPS) / MA_TAPS
    print(f"moving average: h = {h}, sum = {h.sum():.1f} "
          f"(unnormalised sum {MA_TAPS} = {20 * np.log10(MA_TAPS):.2f} dB)")
    w, Hm = signal.freqz(h, worN=4096)
    fmag = w / np.pi
    mdb = 20.0 * np.log10(np.maximum(np.abs(Hm), 10.0 ** (DB_FLOOR / 20.0)))
    null_at = float(fmag[int(np.argmin(np.abs(fmag - 2.0 / MA_TAPS)))])
    after = fmag > null_at + 0.02
    lobe = float(mdb[int(np.argmax(np.where(after, mdb, -np.inf)))])
    print(f"                first null at {null_at:.4f} of Nyquist "
          f"(f_s/{MA_TAPS} = {1.0 / MA_TAPS:.2f} cycles/sample)")
    print(f"                highest sidelobe {lobe:.3f} dB "
          f"(continuous sinc asymptote {20 * np.log10(0.2172):.2f} dB)")
    print(f"                step response = {np.cumsum(h)}; "
          f"group delay (N-1)/2 = {(MA_TAPS - 1) / 2:.0f}")

    n_taps = np.arange(1, MAX_TAPS + 1)
    block = np.array([_next_pow2(2 * int(v)) for v in n_taps])
    fft_cost = 2.0 * np.log2(block) + 1.0
    tie = int(n_taps[fft_cost <= n_taps][0])
    strict = int(n_taps[fft_cost < n_taps][0])
    print(f"cost: crossover N = {tie} (identical cost {fft_cost[tie - 1]:.0f} "
          f"multiplies/output); FFT strictly cheaper from N = {strict}")
    for v in (16, 64, 256, 1024, 4096):
        i = v - 1
        print(f"      N = {v:5d}  B = {block[i]:6d}  "
              f"direct {v:6.1f}  FFT {fft_cost[i]:6.1f} multiplies/output")


if __name__ == "__main__":                          # pragma: no cover
    _diagnostics()
