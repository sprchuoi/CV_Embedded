"""Computed figures for the DFT chapter.

Six figures, in the order the article uses them:

    dft-bin-mapping             one tone as 64 numbers: the record, the stems
                                against bin index, and the same stems against
                                k·fs/N in hertz at two sample rates
    dft-record-is-one-period    a record that does not repeat, its butt-jointed
                                copies, and its spectrum repeating every fs
    dft-conjugate-mirror        |X[k]| and phase for a real record, two-sided,
                                with the mirror pairs and the Nyquist bin marked
    dft-on-and-off-bin          a tone on a bin against the same tone half a bin
                                off it: one line against a skirt
    dft-parseval                the record's energy against Σ|X[k]|²/N, for an
                                on-bin record and for a leaky one
    dft-cost                    N² multiplies against the (N/2)log₂N the FFT
                                will reach, and the N×N twiddle matrix the
                                vectorised route materialises

Nothing here asserts a spectrum. Every number the chapter prints is measured
from a record built in this module, printed on the figure, and printed again to
stdout under the figure's name so a build log can be audited against the page.

Measurement conventions, stated once and used throughout:

* **The standard record.** ``N = 64`` samples at ``fs = 8 kHz``: 125 Hz per bin
  and 8 ms long, small enough to draw every sample and check by hand. Every
  figure except the cost sweep uses it, so the numbers in one section can be
  recognised in the next.
* **Amplitude.** A real tone of amplitude ``A`` on a bin puts ``|X[k]| = A·N/2``
  in that bin, so ``2|X[k]|/N`` is the amplitude; a DC level ``L`` puts ``L·N``
  in bin 0. The figures print the raw sums and the conversion, never a
  pre-scaled "amplitude" with nothing behind it.
* **Two-sided indexing.** ``X[-k]`` means ``X[N-k]``, the bin at ``-k·fs/N``.
  Bin ``N/2`` is both ``+fs/2`` and ``-fs/2``: it is its own mirror, which is
  why the mirror figure marks it rather than pairing it.
* **A correlation, not a formula.** ``X[k] / N`` is the mean product of the
  record with the unit-amplitude probe ``e^{-j2πkn/N}``; the sum of squares of
  that probe is exactly ``N`` and its cross-correlation with the next probe is
  exactly zero, and both are measured here rather than quoted.
* **The optical landing place.** The last line of the bin-mapping footnote
  computes the same ``fs/N`` at the FDE's working point — a 512-point block on
  the 128 GSa/s front end of a 64 GBd link — so the frequency axis quoted in
  the closing callout is arithmetic done here, not a remembered number.

Every figure is deterministic: no randomness is used anywhere in this module,
and no wall-clock measurement is printed, so two builds of the same commit
produce the same SVG.
"""

from __future__ import annotations

import numpy as np

from . import plotstyle as P

# --------------------------------------------------------------------------- #
# shared conventions
# --------------------------------------------------------------------------- #

N = 64                      # samples in the standard record
FS = 8000.0                 # Hz, the standard sample rate
BIN = FS / N                # 125 Hz per bin
RECORD = N / FS             # 8 ms of signal

TONE_BIN = 8                # the on-bin tone, in bins
TONE_OFF = 8.5              # the same tone moved half a bin
HALF_RATE = 2.0 * FS        # the second ruler the mapping figure reads at

# figure 2: a record whose ends do not meet
RECORD_TAU = 6.0            # decay constant, samples
DTFT_POINTS = 18_001        # the fine grid the continuous spectrum is drawn on

# figure 4: one real record with four frequency components
MIRROR_DC = 1.0             # level, in bin 0
MIRROR_TONES = ((3, 1.0, 0.3), (7, 0.5, -1.0))   # (bin, amplitude, phase)
MIRROR_NYQ = 0.25           # amplitude of the (-1)^n term, the fs/2 tone
MIRROR_ARROWS = (44.0, 36.0)   # heights of the two pair arrows, clear of stems

# figure 5: the cost sweep
COST_NS = (8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096)
COST_MARKS = (64, 512, 1024)
BYTES_COMPLEX = 16          # complex128: two float64 per twiddle

# the optical landing place, quoted so the chapter's footnote is computed:
# a 512-point overlap-save FDE on the 128 GSa/s front end of a 64 GBd link
FDE_N = 512
FDE_FS = 128.0e9
FDE_EDGE_HZ = 32.0e9        # the 32 GHz band edge the dispersion chapter states


# --------------------------------------------------------------------------- #
# local helpers
# --------------------------------------------------------------------------- #


def _bins() -> np.ndarray:
    """``k = 0 … N−1``, the bin indices the record is transformed onto."""
    return np.arange(N)


def _probe(k: np.ndarray | int, n: np.ndarray | None = None) -> np.ndarray:
    """The probe for bin ``k``: ``e^{-j2πkn/N}``, one number per sample.

    This is the vector the record is correlated against, and the row of the
    twiddle matrix that the definition spends a multiply on at every sample.
    """
    n = np.arange(N) if n is None else n
    return np.exp(-2.0j * np.pi * k * n / N)


def _spectrum(x: np.ndarray) -> np.ndarray:
    """``X[k]`` for the record, from the same sum the chapter writes out."""
    return np.fft.fft(x)


def _two_sided(X: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """``(k, X[k])`` for ``k = −N/2 … N/2−1``, i.e. ``−fs/2 … fs/2``."""
    k = np.arange(-N // 2, N // 2)
    return k, X[np.mod(k, N)]


def _amp(magnitude: float) -> float:
    """The amplitude a bin's magnitude corresponds to, for a real tone."""
    return 2.0 * magnitude / N


def _stems(ax, x, y, *, colour: str, label: str | None = None, ms: float = 4.2,
           lw: float = 1.3, zorder: int = 4) -> None:
    """A stem plot in the house style: a line from zero and a point on top."""
    ax.vlines(x, 0.0, y, color=colour, lw=lw, zorder=zorder)
    ax.plot(x, y, "o", ms=ms, color=colour, mec=P.PANEL, mew=0.8, ls="none",
            zorder=zorder + 1, label=label)


def _footnote(ax, x: float, y: float, text: str, *, colour: str = P.INK,
              size: float = 8.8, ha: str = "left", va: str = "top",
              mono: bool = False) -> None:
    """A round-cornered note inside the axes, the way every figure here does it."""
    ax.text(x, y, text, transform=ax.transAxes, color=colour, fontsize=size,
            ha=ha, va=va, zorder=9,
            family="monospace" if mono else "sans-serif", linespacing=1.35,
            bbox=dict(boxstyle="round,pad=0.38", facecolor=P.PANEL,
                      edgecolor=P.RULE_SOFT, linewidth=1.0))


def _jsci(value: complex, digits: int = 3) -> str:
    """A complex number as ``re + im j``, for a printed correlation."""
    return f"{value.real:.{digits}f} {'+' if value.imag >= 0 else '−'} " \
           f"{abs(value.imag):.{digits}f}j"


# --------------------------------------------------------------------------- #
# 1. a record is N numbers, and bin k is a frequency
# --------------------------------------------------------------------------- #


def dft_bin_mapping() -> str:
    """One tone, 64 numbers, three panels: the record, the stems, the hertz."""
    n = _bins()
    x = np.cos(2.0 * np.pi * TONE_BIN * n / N)
    X = _spectrum(x)
    half = np.arange(N // 2 + 1)
    magnitude = np.abs(X)[:N // 2 + 1]

    # the two correlations the definition is made of
    self_correlation = complex(np.sum(_probe(TONE_BIN) * np.conj(_probe(TONE_BIN))))
    cross_correlation = complex(np.sum(_probe(TONE_BIN) * np.conj(_probe(TONE_BIN + 1))))
    peak = float(magnitude[TONE_BIN])
    amplitude = _amp(peak)

    fig, axes = P.figure(height=9.6, nrows=3, hspace=1.02,
                         height_ratios=[0.92, 1.0, 1.0])
    ax_rec, ax_k, ax_hz = axes

    # --- top: the record, and nothing else ----------------------------------
    ax_rec.plot(n, x, color=P.NOTE, lw=1.1, marker="o", ms=3.2, mfc=P.NOTE,
                mec=P.PANEL, mew=0.5, zorder=4)
    ax_rec.set_xlim(-1.0, N)
    ax_rec.set_ylim(-1.45, 1.45)
    ax_rec.set_yticks([-1, 0, 1])
    ax_rec.set_xticks([0, 8, 16, 24, 32, 40, 48, 56, 64])
    P.tidy(ax_rec, xlabel="sample index  n  (one sample = 0.125 ms)",
           ylabel="value")
    P.title(ax_rec, "A record is N numbers — here 64 of them, and no more",
            subtitle=f"$f_s$ = {FS:,.0f} Hz, N = {N}, so one record is "
                     f"{1000.0 * RECORD:.3f} ms; a 1 kHz cosine is eight cycles "
                     "of it")

    # --- middle: the transform, against the bin index -----------------------
    _stems(ax_k, half, magnitude, colour=P.ACCENT)
    ax_k.plot([TONE_BIN], [peak], "o", ms=8.0, color=P.WARN, mec=P.PANEL,
              mew=1.2, zorder=8)
    ax_k.annotate(f"bin {TONE_BIN}:  $|X|$ = {peak:.3f} = N/2\n"
                  f"amplitude $2|X|/N$ = {amplitude:.3f}",
                  xy=(TONE_BIN, peak), xytext=(12.0, 13.0), color=P.WARN,
                  fontsize=9.2, ha="left", va="center", zorder=9,
                  arrowprops=dict(arrowstyle="->", color=P.WARN, linewidth=1.0,
                                  shrinkA=2, shrinkB=4))
    ax_k.set_xlim(-1.0, N // 2 + 1)
    ax_k.set_ylim(0.0, 36.0)
    ax_k.set_xticks([0, 8, 16, 24, 32])
    _footnote(ax_k, 0.985, 0.94,
              f"$\\langle$probe {TONE_BIN}, probe {TONE_BIN}$\\rangle$ = "
              f"{_jsci(self_correlation)}\n"
              f"$\\langle$probe {TONE_BIN}, probe {TONE_BIN + 1}$\\rangle$ = "
              f"{_jsci(cross_correlation)}\n"
              f"the sum of squares of one probe is N = {N},\n"
              "so dividing by it is what turns a sum\n"
              "into an average",
              ha="right", size=8.6)
    P.tidy(ax_k, xlabel="bin index  k", ylabel="$|X[k]|$")
    P.title(ax_k, "One output number per bin, and one bin carries the tone",
            subtitle=f"bin $k$ is $k\\times${BIN:g} Hz here; bin {N // 2} is "
                     f"{FS / 2:,.0f} Hz = $f_s/2$. Every other bin is 0.000 to "
                     "the last bit")

    # --- bottom: the same numbers on two rulers ------------------------------
    hz = half * BIN
    _stems(ax_hz, hz, magnitude, colour=P.ACCENT,
           label=f"read at $f_s$ = {FS:,.0f} Hz:  {BIN:g} Hz per bin")
    hz2 = half * (HALF_RATE / N)
    ax_hz.vlines(hz2, 0.0, magnitude, color=P.OPTICAL, lw=1.1, ls=(0, (3, 2)),
                 zorder=3)
    ax_hz.plot(hz2, magnitude, "o", ms=3.6, color=P.OPTICAL, mfc=P.PANEL,
               mew=1.0, ls="none", zorder=5,
               label=f"the same 64 numbers at {HALF_RATE:,.0f} Hz:  "
                     f"{HALF_RATE / N:g} Hz per bin")
    ax_hz.plot([TONE_BIN * BIN], [peak], "o", ms=8.0, color=P.WARN, mec=P.PANEL,
               mew=1.2, zorder=8)
    ax_hz.plot([TONE_BIN * HALF_RATE / N], [peak], "o", ms=8.0, color=P.WARN,
               mec=P.PANEL, mew=1.2, zorder=8)
    ax_hz.annotate(f"bin {TONE_BIN} = {TONE_BIN * BIN:,.0f} Hz",
                   xy=(TONE_BIN * BIN, peak), xytext=(430.0, 17.5),
                   color=P.ACCENT, fontsize=9.2, ha="left", va="center",
                   zorder=9,
                   arrowprops=dict(arrowstyle="->", color=P.ACCENT,
                                   linewidth=1.0, shrinkA=2, shrinkB=4))
    ax_hz.annotate(f"bin {TONE_BIN} = {TONE_BIN * HALF_RATE / N:,.0f} Hz",
                   xy=(TONE_BIN * HALF_RATE / N, peak), xytext=(2360.0, 22.0),
                   color=P.OPTICAL, fontsize=9.2, ha="left", va="center",
                   zorder=9,
                   arrowprops=dict(arrowstyle="->", color=P.OPTICAL,
                                   linewidth=1.0, shrinkA=2, shrinkB=4))
    ax_hz.text(60.0, 35.2, f"$f_s$ = {FS:,.0f} Hz", color=P.ACCENT,
               fontsize=9.2, ha="left", va="top", zorder=9)
    ax_hz.text(2600.0, 35.2, f"the same numbers at $f_s$ = {HALF_RATE:,.0f} Hz",
               color=P.OPTICAL, fontsize=9.2, ha="left", va="top", zorder=9)
    ax_hz.set_xlim(-60.0, HALF_RATE / 2 + 60.0)
    ax_hz.set_ylim(0.0, 36.0)
    _footnote(ax_hz, 0.985, 0.06,
              f"{FS:,.0f} Hz:  {BIN:g} Hz per bin, "
              f"{1000.0 * RECORD:.3f} ms per record\n"
              f"{HALF_RATE:,.0f} Hz:  {HALF_RATE / N:g} Hz per bin, "
              f"{1000.0 * N / HALF_RATE:.3f} ms per record\n"
              f"the same formula at {FDE_FS / 1e9:.0f} GSa/s over {FDE_N} "
              f"points: {FDE_FS / FDE_N / 1e6:.0f} MHz per bin,\n"
              f"so the {FDE_EDGE_HZ / 1e9:.0f} GHz band edge is bin "
              f"{FDE_EDGE_HZ * FDE_N / FDE_FS:.0f} and $f_s/2$ is bin "
              f"{FDE_N // 2} ({FDE_FS / 2e9:.0f} GHz)",
              ha="right", va="bottom", size=8.6)
    P.tidy(ax_hz, xlabel="frequency  $f = k\\cdot f_s/N$  (Hz)",
           ylabel="$|X[k]|$")
    P.title(ax_hz, "A bin index is not a frequency until you name the sample rate",
            subtitle="the heights are identical because the numbers are "
                     "identical; only the ruler the transform cannot see changed")

    print(f"[dft-bin-mapping] N = {N}, fs = {FS:g} Hz: bin width fs/N = "
          f"{BIN:g} Hz, record N/fs = {1000.0 * RECORD:.3f} ms, "
          f"1/T = {1.0 / RECORD:g} Hz")
    print(f"[dft-bin-mapping] tone at {TONE_BIN * BIN:g} Hz is bin {TONE_BIN}; "
          f"|X[{TONE_BIN}]| = {peak:.3f} = N/2, amplitude 2|X|/N = "
          f"{amplitude:.3f}")
    print(f"[dft-bin-mapping] probes: <b{TONE_BIN},b{TONE_BIN}> = "
          f"{_jsci(self_correlation)}, <b{TONE_BIN},b{TONE_BIN + 1}> = "
          f"{_jsci(cross_correlation)}")
    print(f"[dft-bin-mapping] the same 64 numbers read at {HALF_RATE:g} Hz: "
          f"bin width {HALF_RATE / N:g} Hz, record {1000.0 * N / HALF_RATE:.3f} ms, "
          f"bin {TONE_BIN} = {TONE_BIN * HALF_RATE / N:g} Hz")
    print(f"[dft-bin-mapping] {FDE_FS / 1e9:.0f} GSa/s over {FDE_N} points: "
          f"{FDE_FS / FDE_N / 1e6:.0f} MHz per bin; {FDE_EDGE_HZ / 1e9:.0f} GHz "
          f"= bin {FDE_EDGE_HZ * FDE_N / FDE_FS:.0f}; fs/2 = bin "
          f"{FDE_N // 2} ({FDE_FS / 2e9:.0f} GHz)")
    return P.render(fig)


# --------------------------------------------------------------------------- #
# 2. the record is one period, in both domains
# --------------------------------------------------------------------------- #


def dft_record_is_one_period() -> str:
    """A record, its copies, the seam, and the spectrum repeating every fs."""
    n = _bins()
    record = np.exp(-n / RECORD_TAU)
    seam_high = float(record[0])
    seam_low = float(record[-1])
    seam_jump = seam_high - seam_low

    # the continuous spectrum of the record, and the same thing one period up
    f = np.linspace(-FS, 2.0 * FS, DTFT_POINTS)
    kernel = np.exp(-2.0j * np.pi * np.outer(f / FS, n))
    envelope = record @ kernel.T
    shifted = record @ np.exp(-2.0j * np.pi * np.outer((f + FS) / FS, n)).T
    residual = float(np.max(np.abs(shifted - envelope)))
    peak = float(np.max(np.abs(envelope)))
    dft = _spectrum(record)

    fig, axes = P.figure(height=7.8, nrows=2, hspace=0.62)
    ax_time, ax_freq = axes

    # --- top: one record and two copies -------------------------------------
    grid = np.arange(-N, 2 * N)
    copies = np.exp(-np.mod(grid, N) / RECORD_TAU)
    ax_time.plot(grid, copies, color=P.RULE, lw=3.0, zorder=1,
                 label="the repetition the probes see")
    ax_time.plot(n, record, color=P.ACCENT, lw=1.8, marker="o", ms=2.4,
                 mec=P.PANEL, mew=0.0, zorder=4,
                 label=f"one record: N = {N}")
    for seam in (0, N, 2 * N):
        ax_time.axvline(seam, color=P.WARN, lw=1.0, ls=(0, (2, 2)), zorder=2)
    ax_time.annotate("", xy=(0.0, seam_high), xytext=(0.0, seam_low),
                     arrowprops=dict(arrowstyle="<->", color=P.WARN,
                                     linewidth=1.3, shrinkA=0, shrinkB=0))
    _footnote(ax_time, 0.345, 0.06,
              f"the seam: {seam_low:.4f} up to {seam_high:.4f} —\n"
              f"a jump of {seam_jump:.4f} the record never had",
              colour=P.WARN, ha="left", va="bottom")
    ax_time.set_xlim(-N, 2 * N)
    ax_time.set_ylim(-0.08, 1.12)
    ax_time.set_xticks([-N, 0, N, 2 * N])
    ax_time.set_xticklabels(["$-N$", "0", "$N$", "$2N$"])
    P.tidy(ax_time, xlabel="sample index, in records of N", ylabel="value",
           legend=["the repetition the probes see", f"one record: N = {N}"],
           legend_loc="upper right")
    P.title(ax_time, "The transform's input is one period, repeated — by definition",
            subtitle="every probe in the sum has period N samples, so the sum "
                     "cannot tell the record from its repetition")

    # --- bottom: the spectrum, one period of it every fs --------------------
    ax_freq.plot(f, np.abs(envelope), color=P.NOTE, lw=1.5, zorder=4)
    ax_freq.plot(np.arange(-N // 2, N // 2) * BIN, np.abs(np.fft.fftshift(dft)),
                 "o", ms=3.6, color=P.ACCENT, mec=P.PANEL, mew=0.7, ls="none",
                 zorder=6)
    for edge in (-FS, 0.0, FS, 2.0 * FS):
        ax_freq.axvline(edge, color=P.RULE, lw=1.2, ls=(0, (4, 3)), zorder=2)
    # the period boundaries are the dashed rules; the note names them rather
    # than labelling each one, because a rotated label is unreadable at the
    # width this figure is displayed at
    ax_freq.text(1.0 * FS, 12.6, "$f_s$", color=P.MUTED, fontsize=10.0,
                 ha="center", va="center", zorder=7)
    ax_freq.text(2.0 * FS - 120.0, 12.6, "$2f_s$", color=P.MUTED, fontsize=10.0,
                 ha="right", va="center", zorder=7)

    ax_freq.annotate("the same 64 bins, one period higher",
                     xy=(FS + 700.0, 3.2), xytext=(FS + 2600.0, 9.4),
                     color=P.OPTICAL, fontsize=9.0, ha="left", va="center",
                     zorder=9,
                     arrowprops=dict(arrowstyle="->", color=P.OPTICAL,
                                     linewidth=1.0, shrinkA=2, shrinkB=4))
    _footnote(ax_freq, 0.015, 0.94,
              "the curve is the record's spectrum; the dots are the\n"
              "64 numbers the transform returns, once per period of "
              f"{FS:,.0f} Hz:\n"
              f"measured over {DTFT_POINTS:,} grid points, "
              f"max $|X(f+f_s) - X(f)|$ = {residual:.1e}\n"
              f"= {residual / peak:.1e} of the peak {peak:.3f}",
              size=8.6, ha="left", va="top")
    ax_freq.set_xlim(-FS, 2.0 * FS)
    ax_freq.set_ylim(0.0, 14.6)
    ax_freq.set_xticks([-FS, -FS / 2, 0.0, FS / 2, FS, 1.5 * FS, 2.0 * FS])
    ax_freq.set_xticklabels([f"$-{FS:,.0f}$", f"$-{FS / 2:,.0f}$", "0",
                             f"{FS / 2:,.0f}", f"{FS:,.0f}", f"{1.5 * FS:,.0f}",
                             f"{2 * FS:,.0f}"])
    P.tidy(ax_freq, xlabel="frequency  (Hz)", ylabel="$|X(f)|$")
    P.title(ax_freq, "The spectrum repeats every $f_s$, and the DFT samples it once",
            subtitle="the periodicity is the sampling chapter's, seen at 64 "
                     "points: a comb in time is a comb in frequency")

    print(f"[dft-record-is-one-period] record e^(-n/{RECORD_TAU:g}) over "
          f"{N} samples at {FS:g} Hz; ends {seam_high:.4f} and {seam_low:.4f}; "
          f"seam jump {seam_jump:.4f}")
    print(f"[dft-record-is-one-period] spectrum periodicity residual over "
          f"{DTFT_POINTS:,} grid points: {residual:.3e} = "
          f"{residual / peak:.3e} of the peak {peak:.3f}")
    print(f"[dft-record-is-one-period] {N} samples per period in time; "
          f"{N} bins per period in frequency; period = fs = {FS:g} Hz")
    return P.render(fig)


# --------------------------------------------------------------------------- #
# 3. on a bin, and between two bins
# --------------------------------------------------------------------------- #


def dft_on_and_off_bin() -> str:
    """One tone on bin 8, the same tone at bin 8.5, and the skirt it leaves."""
    n = _bins()
    half = np.arange(N // 2 + 1)
    on = np.cos(2.0 * np.pi * TONE_BIN * n / N)
    off = np.cos(2.0 * np.pi * TONE_OFF * n / N)
    on_mag = np.abs(_spectrum(on))[:N // 2 + 1]
    off_mag = np.abs(_spectrum(off))[:N // 2 + 1]

    peak_on = float(on_mag[TONE_BIN])
    low = float(off_mag[int(np.floor(TONE_OFF))])
    high = float(off_mag[int(np.ceil(TONE_OFF))])
    pair_power = low * low + high * high
    on_bin_power = peak_on * peak_on
    pair_amplitude = float(np.sqrt(pair_power))
    total_power = float(np.sum(off * off))
    skirt_min = float(np.min(off_mag[1:]))
    skirt_at = float(off_mag[20])

    fig, axes = P.figure(height=7.0, nrows=2, hspace=0.52, sharey=True)
    ax_on, ax_off = axes

    _stems(ax_on, half, on_mag, colour=P.ACCENT)
    ax_on.plot([TONE_BIN], [peak_on], "o", ms=8.0, color=P.WARN, mec=P.PANEL,
               mew=1.2, zorder=8)
    ax_on.annotate(f"bin {TONE_BIN} = {TONE_BIN * BIN:,.0f} Hz\n"
                   f"|X| = {peak_on:.3f}, amplitude {_amp(peak_on):.3f}",
                   xy=(TONE_BIN, peak_on), xytext=(11.5, 27.0), color=P.WARN,
                   fontsize=9.2, ha="left", va="center", zorder=9,
                   arrowprops=dict(arrowstyle="->", color=P.WARN, linewidth=1.0,
                                   shrinkA=2, shrinkB=4))
    _footnote(ax_on, 0.985, 0.94,
              f"on a bin: one stem of {peak_on:.3f}\n"
              f"every other bin = {float(np.max(np.delete(on_mag, TONE_BIN))):.3f}",
              colour=P.ACCENT, ha="right")
    ax_on.set_xlim(-1.0, N // 2 + 1)
    ax_on.set_ylim(0.0, 36.0)
    P.tidy(ax_on, ylabel="$|X[k]|$")
    P.title(ax_on, "A tone exactly on a bin: one line, and the amplitude is there",
            subtitle=f"{TONE_BIN * BIN:,.1f} Hz in {BIN:g} Hz bins is exactly "
                     f"bin {TONE_BIN}: eight whole cycles in the record")

    _stems(ax_off, half, off_mag, colour=P.NOTE)
    for bin_index, value in ((int(np.floor(TONE_OFF)), low),
                             (int(np.ceil(TONE_OFF)), high)):
        ax_off.plot([bin_index], [value], "o", ms=8.0, color=P.WARN,
                    mec=P.PANEL, mew=1.2, zorder=8)
    ax_off.annotate(f"bins 8 and 9: {low:.3f} and {high:.3f}\n"
                    f"neither is {peak_on:.3f}",
                    xy=(TONE_OFF, high), xytext=(14.5, 25.0), color=P.WARN,
                    fontsize=9.2, ha="left", va="center", zorder=9,
                    arrowprops=dict(arrowstyle="->", color=P.WARN, linewidth=1.0,
                                    shrinkA=2, shrinkB=4))
    ax_off.annotate("", xy=(20, 0.0), xytext=(20, skirt_at),
                    arrowprops=dict(arrowstyle="-", color=P.OPTICAL, linewidth=1.0))
    ax_off.plot([20], [skirt_at], "v", ms=6.0, color=P.OPTICAL, mec=P.PANEL,
                mew=1.0, zorder=8)
    ax_off.text(21.0, skirt_at + 0.6,
                f"bin 20, 11.5 bins out: {skirt_at:.3f}", color=P.OPTICAL,
                fontsize=9.0, ha="left", va="bottom", zorder=9)
    _footnote(ax_off, 0.015, 0.94,
              f"half a bin off ({TONE_OFF * BIN:,.1f} Hz):\n"
              f"$|X[8]| + |X[9]|$ = {low + high:.3f} = "
              f"{(low + high) / peak_on:.2f}x the line's magnitude\n"
              f"power in those two bins = {pair_power:.3f} = "
              f"{100.0 * pair_power / on_bin_power:.2f}% of the "
              f"{on_bin_power:.0f} the line carried\n"
              f"amplitude from the pair = {pair_amplitude:.3f} "
              f"({20.0 * np.log10(pair_amplitude / peak_on):+.2f} dB)",
              colour=P.NOTE, ha="left", size=8.6)
    ax_off.set_xlim(-1.0, N // 2 + 1)
    ax_off.set_ylim(0.0, 36.0)
    ax_off.set_xticks([0, 8, 16, 24, 32])
    P.tidy(ax_off, xlabel="bin index  k", ylabel="$|X[k]|")
    P.title(ax_off, "Half a bin off, the same tone is a skirt in every bin",
            subtitle=f"{TONE_OFF * BIN:,.1f} Hz is not a whole number of cycles "
                     "in 8 ms, so the record starts and ends at different "
                     "places in the cycle")

    print(f"[dft-on-and-off-bin] on a bin: |X[{TONE_BIN}]| = {peak_on:.6f}, "
          f"amplitude {_amp(peak_on):.6f}, largest other bin "
          f"{float(np.max(np.delete(on_mag, TONE_BIN))):.1e}")
    print(f"[dft-on-and-off-bin] half a bin off ({TONE_OFF * BIN:g} Hz): "
          f"|X[8]| = {low:.6f}, |X[9]| = {high:.6f}, sum {low + high:.6f}")
    print(f"[dft-on-and-off-bin] pair power {pair_power:.6f} = "
          f"{100.0 * pair_power / on_bin_power:.4f}% of the "
          f"{on_bin_power:.0f} the on-bin line carried; amplitude from the pair "
          f"{pair_amplitude:.6f} = {pair_amplitude / peak_on:.4f} of "
          f"{peak_on:.3f} = {20.0 * np.log10(pair_amplitude / peak_on):+.2f} dB")
    print(f"[dft-on-and-off-bin] record power {total_power:.6f}; smallest "
          f"skirt bin {skirt_min:.6f}; |X[20]| = {skirt_at:.6f} at 11.5 bins")
    return P.render(fig)


# --------------------------------------------------------------------------- #
# 4. negative frequency is the mirror
# --------------------------------------------------------------------------- #


def dft_conjugate_mirror() -> str:
    """A real record, its two-sided spectrum, and the half that is redundant."""
    n = _bins()
    x = np.full(N, MIRROR_DC, dtype=float)
    for bin_index, amplitude, phase in MIRROR_TONES:
        x = x + amplitude * np.cos(2.0 * np.pi * bin_index * n / N + phase)
    x = x + MIRROR_NYQ * ((-1.0) ** n)
    X = _spectrum(x)

    k, two_sided = _two_sided(X)
    magnitude = np.abs(two_sided)
    phase = np.angle(two_sided)

    # the mirror, measured rather than asserted
    mirror = X[np.mod(-np.arange(N), N)]
    mirror_residual = float(np.max(np.abs(mirror - np.conj(X))))
    independent = N // 2 + 1
    nyquist = complex(X[N // 2])
    phases = {bin_index: float(np.angle(X[bin_index]))
              for bin_index, _, _ in MIRROR_TONES}

    fig, axes = P.figure(height=7.6, nrows=2, hspace=0.34, sharex=True,
                         height_ratios=[1.15, 1.0])
    ax_mag, ax_phase = axes

    # --- magnitude ----------------------------------------------------------
    _stems(ax_mag, k, magnitude, colour=P.ACCENT)
    # the pair arrows are lifted clear of every stem, so that a pair is marked
    # without an arrow crossing somebody else's line
    for arrow_y, (bin_index, amplitude, _) in zip(MIRROR_ARROWS, MIRROR_TONES):
        for sign in (1, -1):
            ax_mag.plot([sign * bin_index], [amplitude * N / 2], "o", ms=8.0,
                        color=P.WARN, mec=P.PANEL, mew=1.2, zorder=8)
        ax_mag.annotate("", xy=(bin_index, arrow_y), xytext=(-bin_index, arrow_y),
                        arrowprops=dict(arrowstyle="<->", color=P.OPTICAL,
                                        linewidth=1.0, shrinkA=1, shrinkB=1))
    ax_mag.plot([0.0], [magnitude[0]], "o", ms=8.0, color=P.WARN, mec=P.PANEL,
                mew=1.2, zorder=8)
    ax_mag.plot([-N // 2], [magnitude[0]], "o", ms=8.0, color=P.NOTE,
                mec=P.PANEL, mew=1.2, zorder=8)
    ax_mag.annotate("Nyquist: bin $N/2$ = $f_s/2$\n"
                    f"{MIRROR_NYQ:.2f}$\\times$64 = {nyquist.real:.3f}, real",
                    xy=(-N // 2, magnitude[0]), xytext=(-30.0, 46.0),
                    color=P.NOTE, fontsize=9.0, ha="left", va="center", zorder=9,
                    arrowprops=dict(arrowstyle="->", color=P.NOTE, linewidth=1.0,
                                    shrinkA=2, shrinkB=4))
    _footnote(ax_mag, 0.985, 0.94,
              f"max $|X[N-k] - \\overline{{X[k]}}|$ = {mirror_residual:.1e}\n"
              f"{independent} of {N} bins are new information\n"
              "the arrows are mirror pairs",
              ha="right", size=8.6)
    ax_mag.set_ylim(0.0, 76.0)
    ax_mag.set_yticks([0, 16, 32, 48, 64])
    P.tidy(ax_mag, ylabel="$|X[k]|$")
    P.title(ax_mag, "A real record has a mirror half, and the transform "
                    "computes it twice",
            subtitle="magnitude is even in k, phase is odd, and bin $N/2$ is its "
                     "own mirror — so it cannot help being real")

    # --- phase --------------------------------------------------------------
    # a bin with no energy has no phase to plot: its angle is rounding noise,
    # so the stems are drawn only where there is something to take an angle of
    occupied = magnitude > 1.0e-6
    _stems(ax_phase, k[occupied], phase[occupied], colour=P.NOTE)
    for bin_index, _, true_phase in MIRROR_TONES:
        # the mirror bin's phase is the same angle with the opposite sign
        ax_phase.plot([-bin_index], [-true_phase], "o", ms=7.0,
                      color=P.WARN, mec=P.PANEL, mew=1.1, zorder=8)
    ax_phase.plot([-N // 2], [0.0], "o", ms=7.0, color=P.NOTE, mec=P.PANEL,
                  mew=1.1, zorder=8)
    ax_phase.axhline(0.0, color=P.SOFT, lw=1.0, zorder=2)
    labels = []
    for bin_index, _, true_phase in MIRROR_TONES:
        labels.append(f"bin {bin_index}: {phases[bin_index]:+.3f} rad, "
                      f"bin {N - bin_index}: {-phases[bin_index]:+.3f} rad")
    _footnote(ax_phase, 0.015, 0.06, "\n".join(labels), colour=P.NOTE, size=8.6,
              va="bottom")
    ax_phase.set_xlim(-N // 2 - 1, N // 2)
    ax_phase.set_ylim(-1.45, 1.45)
    ax_phase.set_xticks([-32, -24, -16, -8, 0, 8, 16, 24])
    ax_phase.set_xticklabels(["$-32$\n$-4{,}000$", "$-24$\n$-3{,}000$",
                              "$-16$\n$-2{,}000$", "$-8$\n$-1{,}000$",
                              "0\n0", "8\n1{,}000", "16\n2{,}000",
                              "24\n3{,}000"])
    P.tidy(ax_phase, xlabel="bin index  k, two-sided: negative k is bin N+k",
           ylabel="phase  (rad)")
    P.title(ax_phase, "The phase is the mirror's odd half",
            subtitle="a conjugate pair carries two numbers, not four: the "
                     "magnitudes agree and the phases are the same angle with "
                     "opposite sign")

    print(f"[dft-conjugate-mirror] real record: DC {MIRROR_DC}, tones "
          + ", ".join(f"bin {b} amp {a}" for b, a, _ in MIRROR_TONES)
          + f", Nyquist {MIRROR_NYQ}")
    print(f"[dft-conjugate-mirror] max |X[N-k] - conj(X[k])| = "
          f"{mirror_residual:.3e}")
    print(f"[dft-conjugate-mirror] X[0] = {X[0].real:.3f}, "
          f"X[N/2] = {nyquist.real:.3f} {'+' if nyquist.imag >= 0 else '−'} "
          f"{abs(nyquist.imag):.3f}j (Nyquist, real)")
    for bin_index, amplitude, _ in MIRROR_TONES:
        print(f"[dft-conjugate-mirror]   bin {bin_index}: |X| = "
              f"{abs(X[bin_index]):.3f}, phase {np.angle(X[bin_index]):+.6f} rad; "
              f"bin {N - bin_index}: |X| = {abs(X[N - bin_index]):.3f}, phase "
              f"{np.angle(X[N - bin_index]):+.6f} rad")
    print(f"[dft-conjugate-mirror] {independent} of {N} bins are new; the "
          f"other {N - independent} are conjugates")
    return P.render(fig)


# --------------------------------------------------------------------------- #
# 5. what it costs
# --------------------------------------------------------------------------- #


def dft_cost() -> str:
    """N² complex multiplies, the N×N matrix that contains them, and the ratio."""
    ns = np.array(COST_NS, dtype=float)
    direct = ns ** 2
    fft = (ns / 2.0) * np.log2(ns)
    ratio = direct / fft

    smallest = float(np.min(ratio))
    smallest_n = int(ns[int(np.argmin(ratio))])
    matrix_bytes = ns * ns * BYTES_COMPLEX
    record_bytes = ns * BYTES_COMPLEX

    fig, axes = P.figure(height=7.2, nrows=2, hspace=0.60)
    ax_count, ax_mem = axes

    # --- top: the two counts -------------------------------------------------
    ax_count.plot(ns, direct, color=P.WARN, lw=1.9, marker="o", ms=4.0,
                  mec=P.PANEL, mew=0.8, zorder=4,
                  label="$N^2$: the definition, counted")
    ax_count.plot(ns, fft, color=P.ACCENT, lw=1.9, marker="o", ms=4.0,
                  mec=P.PANEL, mew=0.8, zorder=4,
                  label="$(N/2)\\log_2 N$: chapter 7's count")
    for mark in COST_MARKS:
        i = COST_NS.index(mark)
        ax_count.plot([mark, mark], [fft[i], direct[i]], color=P.RULE, lw=1.0,
                      ls=(0, (2, 3)), zorder=2)
        ax_count.annotate(f"{ratio[i]:.1f}×", xy=(mark, np.sqrt(direct[i] * fft[i])),
                          xytext=(mark * 1.12, np.sqrt(direct[i] * fft[i])),
                          color=P.MUTED, fontsize=9.0, ha="left", va="center",
                          zorder=7)
    ax_count.set_xscale("log")
    ax_count.set_yscale("log")
    ax_count.set_xlim(7.0, 5200.0)
    ax_count.set_ylim(8.0, 3.0e7)
    ax_count.set_xticks(list(COST_NS))
    ax_count.set_xticklabels([str(int(v)) for v in COST_NS])
    _footnote(ax_count, 0.015, 0.06,
              f"the ratio $2N/\\log_2 N$ is smallest at the smallest N:\n"
              f"{smallest:.2f}× at N = {smallest_n}; the curves never cross",
              size=8.6, va="bottom")
    _footnote(ax_count, 0.985, 0.94,
              f"N = {COST_MARKS[0]}: {int(COST_MARKS[0] ** 2):,} against "
              f"{int(COST_MARKS[0] / 2 * np.log2(COST_MARKS[0])):,}\n"
              f"N = 512: 262,144 against 2,304\n"
              f"N = {COST_MARKS[2]}: 1,048,576 against 5,120",
              ha="right", size=8.6, mono=True)
    P.tidy(ax_count, xlabel="transform length  N", ylabel="complex multiplies",
           legend=["$N^2$: the definition, counted",
                   "$(N/2)\\log_2 N$: chapter 7's count"],
           legend_loc="lower right")
    P.title(ax_count, "The definition costs $N^2$ multiplies, and it never stops costing them",
            subtitle="one output is a sum of N products, and there are N outputs; "
                     "the FFT's count is the promise the next chapter keeps")

    # --- bottom: the matrix the vectorised route materialises ----------------
    ax_mem.plot(ns, matrix_bytes, color=P.OPTICAL, lw=1.9, marker="o", ms=4.0,
                mec=P.PANEL, mew=0.8, zorder=4,
                label="the $N\\times N$ twiddle matrix")
    ax_mem.plot(ns, record_bytes, color=P.NOTE, lw=1.9, marker="o", ms=4.0,
                mec=P.PANEL, mew=0.8, zorder=4, label="the record itself")
    i = COST_NS.index(1024)
    ax_mem.annotate(f"N = 1,024: {matrix_bytes[i] / 1e6:.2f} MB of twiddles\n"
                    f"against {record_bytes[i] / 1e3:.1f} kB of record: "
                    f"{matrix_bytes[i] / record_bytes[i]:.0f}× the data",
                    xy=(1024.0, matrix_bytes[i]), xytext=(9.0, 5.0e7),
                    color=P.OPTICAL, fontsize=9.0, ha="left", va="center",
                    zorder=9,
                    arrowprops=dict(arrowstyle="->", color=P.OPTICAL,
                                    linewidth=1.0, shrinkA=2, shrinkB=4))
    ax_mem.set_xscale("log")
    ax_mem.set_yscale("log")
    ax_mem.set_xlim(7.0, 5200.0)
    ax_mem.set_ylim(5.0e2, 6.0e8)
    ax_mem.set_xticks(list(COST_NS))
    ax_mem.set_xticklabels([str(int(v)) for v in COST_NS])
    P.tidy(ax_mem, xlabel="transform length  N", ylabel="bytes, complex128",
           legend=["the $N\\times N$ twiddle matrix", "the record itself"],
           legend_loc="lower right")
    P.title(ax_mem, "Vectorising changes the constant, not the exponent",
            subtitle="the matrix has one entry per input-output pair, so it is "
                     "N times the record it transforms")

    for mark in COST_MARKS:
        i = COST_NS.index(mark)
        print(f"[dft-cost] N = {mark:4d}: direct {int(direct[i]):,} complex "
              f"multiplies, FFT {int(fft[i]):,}, ratio {ratio[i]:.3f}x")
    print(f"[dft-cost] the ratio 2N/log2(N) is monotone over N = "
          f"{int(ns[0])}..{int(ns[-1])}: smallest {smallest:.4f}x at "
          f"N = {smallest_n}, so the curves never cross")
    print(f"[dft-cost] twiddle matrix at N = 1024: {matrix_bytes[i]:,.0f} bytes "
          f"({matrix_bytes[i] / 1e6:.2f} MB) against {record_bytes[i]:,.0f} bytes "
          f"({record_bytes[i] / 1e3:.1f} kB) of record: "
          f"{matrix_bytes[i] / record_bytes[i]:.0f}x")
    return P.render(fig)


# --------------------------------------------------------------------------- #
# 6. the energy is the same in both domains
# --------------------------------------------------------------------------- #


def dft_parseval() -> str:
    """Two records, their energy computed both ways, and where it sits."""
    n = _bins()
    clean = (0.4 + np.cos(2.0 * np.pi * 5 * n / N)
             + 0.6 * np.cos(2.0 * np.pi * 12 * n / N + 0.7)
             + 0.3 * np.cos(2.0 * np.pi * 20 * n / N - 2.0))
    leaky = np.cos(2.0 * np.pi * TONE_OFF * n / N)

    measured = []
    for record in (clean, leaky):
        spectrum = _spectrum(record)
        energy_time = float(np.sum(record * record))
        energy_freq = float(np.sum(np.abs(spectrum) ** 2) / N)
        occupied = int(np.sum(np.abs(spectrum) ** 2 > 1.0e-9 * N * energy_time))
        measured.append((energy_time, energy_freq, occupied, spectrum))
    (e_clean_t, e_clean_f, clean_bins, clean_spec) = measured[0]
    (e_leaky_t, e_leaky_f, leaky_bins, leaky_spec) = measured[1]

    half = np.arange(N // 2 + 1)
    fig, axes = P.figure(height=8.0, nrows=2, ncols=2, hspace=0.66)
    fig.subplots_adjust(wspace=0.30, bottom=0.135)
    ax_clean_t, ax_clean_f = axes[0]
    ax_leaky_t, ax_leaky_f = axes[1]

    rows = ((ax_clean_t, clean, "Record A: three tones on bins", P.ACCENT),
            (ax_leaky_t, leaky, "Record B: one tone, half a bin off", P.NOTE))
    for ax_time, record, heading, colour in rows:
        ax_time.plot(n, record, color=colour, lw=1.5, zorder=4)
        ax_time.axhline(0.0, color=P.SOFT, lw=0.9, zorder=2)
        ax_time.set_xlim(0, N)
        ax_time.set_ylim(-1.55, 2.25)
        P.tidy(ax_time, xlabel="sample index  n", ylabel="value")
        P.title(ax_time, heading)

    panels = ((ax_clean_f, clean_spec, clean_bins, e_clean_t, e_clean_f,
               P.ACCENT, "on a bin with a level"),
              (ax_leaky_f, leaky_spec, leaky_bins, e_leaky_t, e_leaky_f,
               P.NOTE, "half a bin off"))
    for ax_freq, spectrum, bins, energy_time, energy_freq, colour, name in panels:
        _stems(ax_freq, half, np.abs(spectrum)[:N // 2 + 1], colour=colour)
        ax_freq.set_xlim(-1.0, N // 2 + 1)
        ax_freq.set_ylim(0.0, 74.0 if name == "on a bin with a level" else 30.0)
        P.tidy(ax_freq, xlabel="bin index  k", ylabel="$|X[k]|$")
        _footnote(ax_freq, 0.985, 0.94,
                  f"$\\sum x^2$ = {energy_time:.4f}\n"
                  f"$\\sum |X|^2/N$ = {energy_freq:.4f}\n"
                  f"difference {energy_freq - energy_time:+.1e}\n"
                  f"{bins} of {N} bins nonzero",
                  colour=colour, ha="right", size=8.8)
    P.title(ax_clean_f, "7 of 64 bins carry it all")
    P.title(ax_leaky_f, "all 64 bins carry it")

    fig.text(0.012, 0.075,
             "The same record counted twice, in the two domains. Leakage moves "
             "energy between bins and creates none: record B's\n"
             "spectrum is spread over every bin, and its sum is still the "
             "energy the record started with, to the last bit of the sum.",
             fontsize=8.8, color=P.MUTED, ha="left", va="top", linespacing=1.5)

    print(f"[dft-parseval] record A (three on-bin tones + level): "
          f"sum x^2 = {e_clean_t:.6f}, sum |X|^2/N = {e_clean_f:.6f}, "
          f"difference {e_clean_f - e_clean_t:.3e}, {clean_bins} bins nonzero")
    print(f"[dft-parseval] record B (one tone half a bin off): "
          f"sum x^2 = {e_leaky_t:.6f}, sum |X|^2/N = {e_leaky_f:.6f}, "
          f"difference {e_leaky_f - e_leaky_t:.3e}, {leaky_bins} bins nonzero")
    top2 = float(np.sum(np.sort(np.abs(leaky_spec) ** 2)[-2:]))
    print(f"[dft-parseval] record B's two largest bins hold "
          f"{100.0 * top2 / (N * e_leaky_t):.2f}% of the energy; record A's "
          f"six largest hold "
          f"{100.0 * np.sum(np.sort(np.abs(clean_spec) ** 2)[-6:]) / (N * e_clean_t):.2f}%")
    return P.render(fig)


FIGURES = {
    "dft-bin-mapping": dft_bin_mapping,
    "dft-record-is-one-period": dft_record_is_one_period,
    "dft-conjugate-mirror": dft_conjugate_mirror,
    "dft-on-and-off-bin": dft_on_and_off_bin,
    "dft-parseval": dft_parseval,
    "dft-cost": dft_cost,
}
