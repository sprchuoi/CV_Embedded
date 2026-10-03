"""Computed figures for the quantisation, SNR and ENOB chapter.

Three numpy/matplotlib figures, in the order the article uses them:

    quantization-error-sawtooth   what the error is, in time and in spectrum
    snr-versus-bits               6.02N + 1.76, measured, then oversampled
    osr-and-noise-shaping         what a sigma-delta buys, and what it costs

Everything here is simulated from an explicit quantiser; nothing is quoted from a
datasheet. The chapter's argument is that the names on a converter's front panel
promise more resolution than the device delivers, so every number that reaches
the page is measured, printed by the builder that computes it, and annotated
onto the figure.

Conventions, fixed once so the three figures agree:

* Full scale is ``FS = 1.0``, so a full-scale sinusoid is ``sin(2*pi*f*t)`` with
  peak amplitude 1 and power ``FS**2/2``.
* An ``N``-bit mid-tread quantiser puts ``2**N`` levels across ``[-FS, +FS]``,
  so its step is ``q = 2*FS/2**N`` and its error variance, for an input that
  sweeps the levels without clipping, is ``q**2/12``. That is the ``q`` the
  ideal ``6.02*N + 1.76`` dB line is built from -- the two agree to better than
  0.15 dB from N = 5 upward, which is the point of figure 2.
* Spectra are computed with an explicit coherent DFT (an integer number of
  cycles in a power-of-two record) rather than with a window, so there is no
  leakage skirt to mistake for a spur. Where a figure leans on that choice the
  annotation says so.
* Frequencies are normalised: ``f = 0.5`` is Nyquist, and ``OSR = 0.5/f``.

Randomness is confined to the dithered spectrum in figure 1, and every call
builds a generator from :data:`SEED`, so two builds of the same figure are
byte-identical. The rendered SVG still carries matplotlib's own ``<dc:date>``
and object-identity element ids; suppressing those is ``plotstyle.render``'s
business, not this module's.
"""

from __future__ import annotations

import numpy as np

from . import plotstyle as P

# Rebuilds must be reproducible, and byte-for-byte so: CI regenerates every
# figure and fails if the committed SVGs differ. A generator created once at
# import time would advance between calls and make the dithered spectrum
# irreproducible, so every figure builds its own from this seed.
SEED = 0

FS = 1.0                          # full scale, amplitudes run -1 .. +1
FS_POWER = FS ** 2 / 2.0          # power of a full-scale sinusoid


# --------------------------------------------------------------------------- #
# shared helpers
# --------------------------------------------------------------------------- #


def _quantise(x, bits, step=None, limit=None):
    """An ideal uniform mid-tread quantiser over ``[-FS, +FS]``.

    ``step`` and ``limit`` override the ``bits``-derived values so that the
    noise-shaping model can reuse the same (single) quantiser definition.
    """
    if step is None:
        step = 2.0 * FS / 2 ** bits
    if limit is None:
        limit = FS - step / 2.0
    index = np.floor(np.asarray(x) / step + 0.5)
    return np.clip(index * step, -limit, limit)


def _coherent_sine(m, cycles):
    """``cycles`` whole periods of a full-scale sine in an ``m``-sample record."""
    k = np.arange(m)
    return k, np.sin(2.0 * np.pi * cycles * k / m)


def _integrate(y, x):
    """Trapezoidal integral.

    Spelled out rather than called as ``np.trapz``/``np.trapezoid``: the former
    is deprecated and the latter only exists from numpy 2.0, and this repo does
    not pin numpy. Six lines here are cheaper than a version floor.
    """
    y = np.asarray(y, dtype=float)
    x = np.asarray(x, dtype=float)
    return float(np.sum(0.5 * (y[1:] + y[:-1]) * np.diff(x)))


def _integrate_to(y, x, edge):
    """Integral from ``x[0]`` to ``edge``, interpolating the last interval.

    Snapping to the last sample below the edge instead would add or drop up to
    one grid cell of a rising spectrum, and at OSR 512 the whole band is only
    a handful of cells wide. Measuring the noise-shaping slopes from these
    integrals is the point of figure 3, so the edge is taken properly.
    """
    y = np.asarray(y, dtype=float)
    x = np.asarray(x, dtype=float)
    last = int(np.searchsorted(x, edge, side="right")) - 1
    last = min(max(last, 0), len(x) - 1)
    total = _integrate(y[:last + 1], x[:last + 1])
    if last < len(x) - 1:
        span = float(x[last + 1] - x[last])
        if span > 0.0:
            top = float(y[last] + (y[last + 1] - y[last])
                        * float(edge - x[last]) / span)
            total += 0.5 * (float(y[last]) + top) * float(edge - x[last])
    return total


def _dft(samples):
    """One-sided DFT magnitude at bins 0 .. m/2 of a coherent record."""
    m = len(samples)
    k = np.arange(m)
    bins = np.arange(m // 2 + 1)
    kernel = np.exp(-2j * np.pi * np.outer(bins, k) / m) / np.sqrt(m)
    return np.abs(kernel @ samples)


def _signal_bin(spectrum):
    """Index of the tone, assumed to be the largest non-DC bin."""
    return int(np.argmax(spectrum[1:]) + 1)


def _tone_mask(n_bins, peak, *, guard=1):
    """Bins that are neither DC, Nyquist, nor part of the tone's neighbourhood."""
    mask = np.ones(n_bins, dtype=bool)
    mask[0] = False
    mask[n_bins - 1] = False
    mask[max(peak - guard, 1):peak + guard + 1] = False
    return mask


def _head(ax, title, subtitle=None):
    """Title plus a subtitle that clears it.

    ``P.title`` draws both at the same offset above the axes, so on the short
    panels used here the second line lands on the first. Lifting the title by a
    few extra points is all the separation the pair needs.
    """
    if subtitle is None:
        P.title(ax, title)
        return
    ax.set_title(title, pad=22)
    ax.text(0.0, 1.012, subtitle, transform=ax.transAxes, fontsize=9,
            color=P.MUTED, va="bottom")


# --------------------------------------------------------------------------- #
# 1. what the quantisation error actually looks like
# --------------------------------------------------------------------------- #


def quantization_error_sawtooth() -> str:
    """A 4-bit quantiser in time, its error, and the spectrum of that error.

    Top and middle panels are drawn from a continuous-time sweep so the error
    shows as a real sawtooth; the spectrum panel goes back to a coherent
    discrete record, because that is the only thing a DFT is entitled to
    transform.
    """
    bits = 4
    step = 2.0 * FS / 2 ** bits
    levels = 2 ** bits
    limit = FS - step / 2.0

    # --- time domain, swept finely so the staircase has vertical edges -------
    t = np.linspace(0.0, 1.0, 120001)
    x = np.sin(2.0 * np.pi * t)
    x_q = _quantise(x, bits)
    error = (x - x_q) / step                       # in LSB, |error| <= 0.5
    rms_error = float(np.sqrt(np.mean(error ** 2)))
    peak_error = float(np.max(np.abs(error)))

    with np.errstate(invalid="ignore"):
        smooth = np.flatnonzero(np.diff(error) != 0.0)
    period_samples = float(np.mean(np.diff(smooth))) if len(smooth) > 2 else float("nan")

    # --- spectrum, coherent: 127 whole cycles in an 8192-sample record -------
    m = 8192
    cycles = 127
    _, s = _coherent_sine(m, cycles)
    s_q = _quantise(s, bits)
    s_err = s - s_q

    # Quiet dither: enough to break the error's correlation with the input and
    # spread the spurs, small enough that it does not swamp them. TPDF is the
    # textbook width, but a full 1 LSB here would put 20 dB of extra noise under
    # every bin and bury the point.
    rng = np.random.default_rng(SEED)
    dither_pk = 0.4 * step
    dither = rng.uniform(-0.5, 0.5, m) * dither_pk
    s_q_dithered = _quantise(s + dither, bits)
    dither_err = (s + dither) - s_q_dithered

    tone = _dft(s)
    err_spectrum = _dft(s_err)
    dither_spectrum = _dft(dither_err)
    peak_bin = _signal_bin(tone)
    carrier = float(tone[peak_bin])
    with np.errstate(divide="ignore"):
        err_db = 20.0 * np.log10(np.maximum(err_spectrum, 1e-18) / carrier)
        dither_db = 20.0 * np.log10(np.maximum(dither_spectrum, 1e-18) / carrier)

    noisy = _tone_mask(len(tone), peak_bin)
    worst_spur_db = float(np.max(err_db[noisy]))
    worst_spur_bin = int(np.flatnonzero(noisy)[np.argmax(err_db[noisy])])
    worst_spur_f = worst_spur_bin / m
    dither_floor_db = float(10.0 * np.log10(np.mean(
        (dither_spectrum[noisy] / carrier) ** 2)))
    spur_energy_db = float(10.0 * np.log10(
        np.sum(err_spectrum[noisy] ** 2) / np.sum(dither_spectrum[noisy] ** 2)))
    rms_dither = float(np.sqrt(np.mean(dither_err ** 2)) / step)

    # --- draw ---------------------------------------------------------------
    fig, axes = P.figure(height=8.4, nrows=3, hspace=1.15,
                         height_ratios=[1.05, 0.95, 1.20])
    ax, ax_err, ax_spec = axes

    line_x, = ax.plot(t, x, color=P.MUTED, lw=1.1, label="$x(t)$")
    line_q, = ax.plot(t, x_q, color=P.ACCENT, lw=1.6, drawstyle="steps-post",
                      label="$x_q(t)$")
    ax.set_xlim(0.0, 1.0)
    ax.set_ylim(-2.22, 1.34)
    ax.set_yticks([-1.0, -0.5, 0.0, 0.5, 1.0])
    ax.tick_params(labelbottom=False)
    ax.legend([line_x, line_q],
              ["$x(t)$, full scale", "$x_q(t)$, steps-post"],
              loc="lower center", ncol=2)
    _head(ax, "One period through a 4-bit quantiser",
          "16 levels across FS - step $q$ = " + f"{step:.3f} FS"
          + " - the sine spans " + f"{2.0 / step:.0f}" + " of them")
    P.tidy(ax, ylabel="amplitude (FS)")

    ax_err.plot(t, error, color=P.WARN, lw=0.5)
    for bound in (-0.5, 0.5):
        ax_err.axhline(bound, color=P.ACCENT_DARK, lw=0.9, ls=(0, (4, 3)),
                       zorder=1)
    ax_err.set_xlim(0.0, 1.0)
    ax_err.set_ylim(-0.95, 1.15)
    ax_err.set_yticks([-0.5, 0.0, 0.5])
    ax_err.text(0.005, 1.08, "not noise: a deterministic function of $x$ - "
                             "the same input always gives the same error",
                color=P.INK, fontsize=8.5, ha="left", va="top")
    ax_err.text(0.995, 0.52, "one crossing per drawn sample - "
                             + f"{levels}" + " per period",
                color=P.WARN, fontsize=8.5, ha="right", va="top")
    ax_err.text(0.0, -0.91, "$\\pm$½ LSB: every sample is inside it "
                            f"(max {peak_error:.3f}, rms {rms_error:.3f} LSB)",
                color=P.MUTED, fontsize=8.5, ha="left", va="bottom")
    _head(ax_err, "Quantisation error: a sawtooth, not a noise generator")
    P.tidy(ax_err, xlabel="input phase (periods)", ylabel="error (LSB)")

    view = m * 0.05
    f = np.arange(len(tone)) / m
    spec_mask = f <= view
    ax_spec.plot(f[spec_mask], dither_db[spec_mask], color=P.NOTE, lw=0.7,
                 alpha=0.9, label="dithered input: broad floor")
    ax_spec.plot(f[spec_mask], err_db[spec_mask], color=P.WARN, lw=0.9,
                 label="plain 4-bit quantiser: discrete spurs")
    ax_spec.plot(worst_spur_f, worst_spur_db, marker="o", ls="none", ms=5.5,
                 color=P.WARN, mec=P.PANEL, mew=1.1, zorder=6)
    ax_spec.annotate(f"worst spur {worst_spur_db:.1f} dBc: the plain quantiser "
                     "puts its error energy in a few lines",
                     xy=(worst_spur_f, worst_spur_db),
                     xytext=(0.0065, -44.0), ha="left", va="center",
                     color=P.WARN, fontsize=8.5,
                     textcoords="data", arrowprops=dict(arrowstyle="->", color=P.WARN, lw=1.0,
                                     shrinkA=2, shrinkB=2))
    # The only thing the dithered curve needs is a leader: what it is, and how
    # far its floor sits above the plain quantiser's total, is in the subtitle
    # and the legend. A 70-character label anchored at the right edge would
    # start outside the axes.
    ax_spec.annotate("", xy=(0.0455, dither_floor_db + 1.0),
                     xytext=(0.0345, dither_floor_db + 21.0),
                     textcoords="data",
                     arrowprops=dict(arrowstyle="->", color=P.NOTE, lw=1.0,
                                     shrinkA=2, shrinkB=3))
    ax_spec.text(0.0004, worst_spur_db + 12.0,
                 "the DFT has no window: every line above is real",
                 color=P.MUTED, fontsize=8.5, ha="left", va="top")
    ax_spec.set_xlim(0.0, view)
    ax_spec.set_ylim(dither_floor_db - 22.0, worst_spur_db + 16.0)
    ticks = [k * m * 0.01 for k in range(6)]
    ax_spec.set_xticks(ticks, labels=[f"{k * 0.01:.2f}" for k in range(6)])
    ax_spec.legend(loc="lower left", ncol=1)
    _head(ax_spec, "The spectrum of that error",
          f"{cycles} whole cycles in {m} samples is coherent, so no leakage; "
          + f"the dithered floor is {dither_floor_db:.0f} dBc")
    P.tidy(ax_spec, xlabel="normalised frequency (f/fs)",
           ylabel="error relative to carrier (dBc)")

    print("[quantization-error-sawtooth]")
    print(f"  step q = {step:.4f} FS, {levels} levels, "
          + f"sine spans {2.0 / step:.0f} steps")
    print("  error: max " + f"{peak_error:.4f}" + " LSB, rms "
          + f"{rms_error:.4f}" + " LSB (ideal uniform rms = "
          + f"{1.0 / np.sqrt(12.0):.4f}" + " LSB)")
    print("  error is a deterministic sawtooth: "
          + f"{levels} crossings per period, one per "
          + f"{period_samples:.1f}" + " drawn samples")
    print(f"  coherent record: {cycles} cycles / {m} samples, tone bin "
          + f"{peak_bin}, f = {cycles / m:.5f}")
    print("  plain quantiser: worst spur " + f"{worst_spur_db:.2f}" + " dBc at "
          + f"bin {worst_spur_bin} (f = {worst_spur_f:.5f})")
    print("  dithered input: mean floor " + f"{dither_floor_db:.2f}" + " dBc; "
          + "no spur stands above it")
    print("  total error energy: dithered minus plain = "
          + f"{-spur_energy_db:+.2f}" + " dB")
    print("  dither residual rms " + f"{rms_dither:.4f}" + " LSB "
          + "(vs " + f"{rms_error:.4f}" + " LSB without it)")
    return P.render(fig)


# --------------------------------------------------------------------------- #
# 2. the 6.02N + 1.76 line, measured, and what oversampling adds
# --------------------------------------------------------------------------- #


def snr_versus_bits() -> str:
    """Measure the quantiser's SNR bit by bit, then add the oversampling term."""
    bits_all = np.arange(1, 17)
    m = 8192
    cycles = 127

    ideal = 6.02 * bits_all + 1.76
    measured = []
    for n in bits_all:
        _, x = _coherent_sine(m, int(cycles))
        x_q = _quantise(x, int(n))
        dist = x_q - x
        measured.append(10.0 * np.log10(np.mean(x_q ** 2) / np.mean(dist ** 2)))
    measured = np.array(measured)
    deviation = measured - ideal

    fig, axes = P.figure(height=6.6, nrows=2, hspace=0.62,
                         height_ratios=[1.10, 1.00])
    ax, ax_osr = axes

    ideal_line, = ax.plot(bits_all, ideal, color=P.ACCENT, lw=2.1,
                          label="ideal  $6.02N + 1.76$ dB")
    meas_line, = ax.plot(bits_all, measured, color=P.NOTE, lw=1.4, ls="none",
                         marker="o", ms=4.6, mec=P.PANEL, mew=0.9,
                         label="measured, simulated 4-level..64k-level quantiser")
    ax.legend([ideal_line, meas_line],
              ["ideal  $6.02N + 1.76$ dB",
               "measured from a simulated quantiser"],
              loc="upper left", ncol=1)
    for mark in (8, 12, 16):
        ax.plot(mark, float(measured[mark - 1]), marker="o", ls="none", ms=6.5,
                color=P.WARN, mec=P.PANEL, mew=1.2, zorder=6)
    # Three two-line callouts cannot sit around one diagonal without landing on
    # it or on each other, so the numbers go in one block; the ringed markers
    # tie it to the points.
    ax.text(17.4, 26.0, "\n".join(
        f"N = {mark}:  measured {measured[mark - 1]:.2f} dB,  ideal "
        + f"{6.02 * mark + 1.76:.2f} dB  "
        + f"(gap {measured[mark - 1] - (6.02 * mark + 1.76):+.2f} dB)"
        for mark in (8, 12, 16)),
        color=P.WARN, fontsize=8.5, ha="right", va="top")
    ax.text(17.4, 108.0,
            "The ideal line assumes a full-scale sinusoid and a\n"
            "uniform, white, uncorrelated error. This chapter\n"
            "attacks all three.",
            color=P.INK, fontsize=8.5, ha="right", va="top")
    ax.set_xlim(0.5, 17.6)
    ax.set_ylim(0.0, 122.0)
    _head(ax, "Resolution buys SNR, about 6 dB per bit",
          "each marker is an 8192-sample coherent record through a "
          "mid-tread quantiser")
    P.tidy(ax, xlabel="resolution N (bits)", ylabel="SNR (dB)", xaxis_int=True)

    osr = np.logspace(0.0, np.log10(512.0), 400)
    note_marks = (1, 4, 16, 256)
    for n, color in ((4, P.ACCENT), (8, P.NOTE)):
        base = 6.02 * n + 1.76
        line, = ax_osr.semilogx(osr, base + 10.0 * np.log10(osr), color=color,
                                lw=2.1, label=f"N = {n}:  "
                                              + f"$6.02N + 1.76 + 10\\log_{{10}}$OSR")
        for mark in note_marks:
            ax_osr.semilogx(mark, base + 10.0 * np.log10(mark), marker="o",
                            ls="none", ms=5.0, color=color, mec=P.PANEL,
                            mew=1.0, zorder=6)
    ax_osr.semilogx([], [], ls="none", label="")
    # One block, not a label per marker, and not a stagger: these strings are
    # ~160 px wide while the markers are 90 px apart, so anything anchored to a
    # marker collides with its neighbour. The conversion does not depend on
    # where the curve is, so it is stated once. Lines are ~13 px, hence the
    # 10 dB row pitch.
    ax_osr.text(1.02, 46.0,
                "Oversampling, as bits:\n"
                + "\n".join(
                    f"OSR {mark:>3d}:  +{10.0 * np.log10(mark):4.1f} dB"
                    + f"  = {10.0 * np.log10(mark) / 6.02:.2f} bits"
                    for mark in note_marks),
                color=P.MUTED, fontsize=8, ha="left", va="center")
    ax_osr.text(505.0, 21.5, "ideal line only: full-scale sinusoid, uniform\n"
                "white uncorrelated error, brick-wall filter at fs/2OSR",
                color=P.INK, fontsize=8.5, ha="right", va="bottom")
    ax_osr.set_xlim(1.0, 512.0)
    ax_osr.set_ylim(20.0, 108.0)
    ax_osr.legend(loc="upper left", ncol=1)
    _head(ax_osr, "Oversampling buys the same thing without more bits",
          "3 dB per doubling - halving the band halves the noise that lands in it")
    P.tidy(ax_osr, xlabel="oversampling ratio OSR = fs / (2 B)",
           ylabel="in-band SNR (dB)")

    print("[snr-versus-bits]")
    print("  measured SNR (time-domain, coherent " + f"{m}" + "-sample record):")
    for n, value, dev in zip(bits_all, measured, deviation):
        print(f"    N = {int(n):2d}  measured {value:7.3f} dB   "
              + f"ideal {6.02 * n + 1.76:7.3f} dB   gap {dev:+6.3f} dB")
    print("  annotated N = 8, 12, 16:  " + ", ".join(
        f"{float(measured[n - 1]):.2f}" for n in (8, 12, 16)) + " dB")
    print("  worst gap from the ideal line: "
          + f"{float(np.max(np.abs(deviation[3:]))):.3f}" + " dB for N >= 4")
    print("  OSR bits: " + ", ".join(
        f"OSR {o} = {10.0 * np.log10(o) / 6.02:.2f} bits" for o in note_marks))
    return P.render(fig)


# --------------------------------------------------------------------------- #
# 3. sigma-delta: the noise is moved, not removed
# --------------------------------------------------------------------------- #


def osr_and_noise_shaping() -> str:
    """Flat versus first-order-shaped noise, in band and in total power.

    The model is an ideal quantiser followed by an ideal integrator: flat
    ``q^2/12`` for Nyquist-rate sampling, and ``q^2/12 * |1 - z^-1|^2`` for the
    first-order shaped case. Both curves are integrated numerically here, and
    the printed fractions are the ones annotated on the figure.
    """
    bits = 4
    step = 2.0 * FS / 2 ** bits
    total_variance = step ** 2 / 12.0
    flat_level = total_variance                     # FS^2 per unit bandwidth

    # A log-spaced OSR grid evaluates each band on its own samples, so the
    # curves below carry no interpolation error. At OSR 512 the band is 0.00049
    # wide, which is why the grid has to be this fine.
    osr = np.logspace(0.0, np.log10(512.0), 400)
    f = np.linspace(0.0, 0.5, 40001)
    flat = np.full_like(f, flat_level)
    shaped = flat_level * 4.0 * np.sin(np.pi * f) ** 2
    flat_db = 10.0 * np.log10(flat)
    shaped_db = 10.0 * np.log10(np.maximum(shaped, flat_level * 1e-12))

    total_flat = _integrate(flat, f)
    total_shaped = _integrate(shaped, f)
    power_ratio = total_shaped / total_flat

    def band_limited(osr_value):
        """In-band noise power for both models at one oversampling ratio."""
        edge = 0.5 / osr_value
        return (_integrate_to(flat, f, edge), _integrate_to(shaped, f, edge))

    def snr_at(osr_value):
        """In-band SNR of both models, in dB, at one oversampling ratio."""
        flat_band, shaped_band = band_limited(osr_value)
        return (10.0 * np.log10(FS_POWER / flat_band),
                10.0 * np.log10(FS_POWER / shaped_band))

    mark_osr = 16
    flat_band, shaped_band = band_limited(mark_osr)
    flat_fraction = flat_band / total_flat
    shaped_fraction = shaped_band / total_shaped

    fig, axes = P.figure(height=6.6, nrows=2, hspace=0.60,
                         height_ratios=[1.05, 1.00])
    ax, ax_snr = axes

    half = 0.5 / mark_osr
    ax.axvspan(0.0, half, color=P.RULE_SOFT, lw=0.0, zorder=0)
    ax.axvline(half, color=P.RULE, lw=1.1, ls=(0, (4, 3)), zorder=1)
    # The OSR-16 band is only ~19 px wide, so this label starts just inside it
    # and runs right, into the empty bottom of the panel.
    ax.text(0.004, -82.0, "signal band", color=P.MUTED,
            fontsize=8, ha="left", va="bottom")

    flat_line, = ax.plot(f, flat_db, color=P.ACCENT, lw=2.0,
                         label="flat: $q^2/12$ over the whole band")
    shaped_line, = ax.plot(f, shaped_db, color=P.WARN, lw=2.0,
                           label="first-order shaped: $q^2/12\\,|1 - z^{-1}|^2$")
    # The in-band fractions live in the legend rather than beside the curves:
    # the shaped curve fills the middle of the panel, and every placement that
    # sat in the remaining wedge either landed on it or on the other label.
    ax.legend([flat_line, shaped_line],
              ["flat:  $q^2/12$, "
               + f"{flat_fraction * 100:.3f}" + " % of it in band",
               "shaped:  $q^2/12\\,|1 - z^{-1}|^2$, "
               + f"{shaped_fraction * 100:.5f}" + " % in band, total x"
               + f"{power_ratio:.2f}"],
              loc="upper center", ncol=2)
    ax.text(0.485, -84.0, "shaping removes no noise: it trades in-band power\n"
                          "for total power",
            color=P.INK, fontsize=8.5, ha="right", va="center")
    ax.set_ylim(-90.0, 6.0)          # headroom so the legend clears the data
    ax.set_xlim(0.0, 0.5)
    _head(ax, "Quantisation noise power spectral density",
          "a model: ideal quantiser and integrator, white error - the shaped "
          "total power is up, not down")
    P.tidy(ax, xlabel="normalised frequency (f/fs)",
           ylabel="PSD (dBFS / unit bandwidth)")

    snr_flat = np.empty_like(osr)
    snr_shaped = np.empty_like(osr)
    for i, ratio in enumerate(osr):
        snr_flat[i], snr_shaped[i] = snr_at(ratio)

    ax_snr.semilogx(osr, snr_flat, color=P.ACCENT, lw=2.1,
                    label="unshaped: 3 dB per doubling")
    ax_snr.semilogx(osr, snr_shaped, color=P.WARN, lw=2.1,
                    label="first-order shaped: 9 dB per doubling")

    def slope_per_doubling(values):
        """dB gained per doubling of OSR, from the grid itself.

        The grid is log-spaced with a constant step ``dlog`` in log10(OSR), so
        the gain across one step is scaled to one octave by ``log10(2)/dlog``.
        Every point that has a neighbour one octave up is measured; nothing here
        is copied from a textbook.
        """
        dlog = float(np.log10(osr[1] / osr[0]))
        keep = osr[:-1] * 2.0 <= osr[-1]
        steps = (values[1:] - values[:-1])[keep]
        return steps * float(np.log10(2.0)) / dlog

    flat_slopes = slope_per_doubling(snr_flat)
    shaped_slopes = slope_per_doubling(snr_shaped)
    flat_typical = float(np.median(flat_slopes))
    shaped_typical = float(np.median(shaped_slopes))
    # The slope is only asymptotic once the band edge is well inside the shaped
    # noise's rise; from OSR 8 up it holds to a few hundredths of a dB. Below
    # that the curve is still in its knee, which is the crossing drawn above,
    # not a failure of the slope.
    slope_osr = osr[:-1][osr[:-1] * 2.0 <= osr[-1]]
    asymptotic = slope_osr >= 8.0
    flat_worst = float(np.max(np.abs(flat_slopes[asymptotic] - 3.010)))
    shaped_worst = float(np.max(np.abs(shaped_slopes[asymptotic] - 9.031)))
    knee_worst = float(np.max(np.abs(shaped_slopes[~asymptotic] - 9.031)))

    # Shaping only pays once the in-band shelf is narrow enough to beat the 3 dB
    # it adds to the total. Find that crossing rather than assuming it.
    probe = np.logspace(0.0, np.log10(32.0), 4000)
    gap = np.array([snr_at(ratio)[1] - snr_at(ratio)[0] for ratio in probe])
    crossing_index = int(np.argmin(np.abs(gap)))
    crossing_osr = float(probe[crossing_index])
    crossing_value = float(snr_at(crossing_osr)[1])

    # Three short lines, not four: the box is 280 px wide and the unshaped
    # curve crosses any row that reaches past x ~ 3.
    ax_snr.text(1.15, 17.0,
                "measured, per doubling:\n"
                + "unshaped " + f"{flat_typical:.2f}" + " dB\n"
                + "shaped   " + f"{shaped_typical:.2f}" + " dB",
                color=P.INK, fontsize=8.5, ha="left", va="bottom")
    # A plain leader line and a plain label: an annotate arrow would make the
    # text's bounding box span the whole leader, which is a liar's bbox for
    # anyone checking that labels do not collide.
    ax_snr.plot([crossing_osr, 120.0], [crossing_value, 53.0], color=P.MUTED,
                lw=0.9, ls=(0, (3, 3)), zorder=3)
    ax_snr.text(200.0, 56.0, f"crossover at OSR {crossing_osr:.1f}",
                ha="center", va="center", color=P.MUTED, fontsize=8.5)
    for ratio in (1, 4, 16, 64, 256):
        marker_flat, marker_shaped = snr_at(ratio)
        ax_snr.semilogx(ratio, marker_flat, marker="o", ls="none", ms=5.0,
                        color=P.ACCENT, mec=P.PANEL, mew=1.0, zorder=6)
        ax_snr.semilogx(ratio, marker_shaped, marker="o", ls="none", ms=5.0,
                        color=P.WARN, mec=P.PANEL, mew=1.0, zorder=6)
    ax_snr.set_xlim(1.0, 512.0)
    ax_snr.set_ylim(15.0, 118.0)
    ax_snr.legend(loc="upper left", ncol=1)
    _head(ax_snr, "In-band SNR: what the shaping bought, and only in band",
          "same 4-bit quantiser, same step - only the noise transfer differs")
    P.tidy(ax_snr, xlabel="oversampling ratio OSR = fs / (2 B)",
           ylabel="in-band SNR (dB)")

    print("[osr-and-noise-shaping]")
    print("  step q = " + f"{step:.4f}" + " FS, q^2/12 = "
          + f"{total_variance:.6e}" + " FS^2")
    print("  total noise power: flat " + f"{total_flat:.6e}" + " FS^2, shaped "
          + f"{total_shaped:.6e}" + " FS^2 -> ratio "
          + f"{power_ratio:.4f}" + f" ({10.0 * np.log10(power_ratio):+.2f} dB)")
    print(f"  at OSR {mark_osr}: in-band fraction = in-band / total")
    print("    flat:   " + f"{flat_fraction * 100:.4f}" + " %  ("
          + f"{10.0 * np.log10(flat_fraction):.2f}" + " dB)")
    print("    shaped: " + f"{shaped_fraction * 100:.6f}" + " %  ("
          + f"{10.0 * np.log10(shaped_fraction):.2f}" + " dB)")
    print("  total-power penalty of first-order shaping: "
          + f"{10.0 * np.log10(power_ratio):.2f}" + " dB")
    print("  measured slopes (per doubling of OSR, one octave per measurement):")
    print("    unshaped " + f"{flat_typical:.3f}" + " dB  (nominal 3.010, worst "
          + f"deviation {flat_worst:.3f}" + " dB over OSR >= 8)")
    print("    shaped   " + f"{shaped_typical:.3f}" + " dB  (nominal 9.031, worst "
          + f"deviation {shaped_worst:.3f}" + " dB over OSR >= 8)")
    print("    shaped, OSR < 8 (the knee): worst deviation "
          + f"{knee_worst:.3f}" + " dB - a rate, not a slope, down there")
    print("  sampled SNRs (unshaped / shaped), evaluated directly on band edges:")
    for ratio in (1, 2, 4, 16, 64, 256, 512):
        flat_i, shaped_i = snr_at(ratio)
        print(f"    OSR {ratio:4d}  {flat_i:7.2f} dB  {shaped_i:7.2f} dB")
    print("  shaped-only-beats-unshaped crossover at OSR "
          + f"{crossing_osr:.2f}" + f"  ({crossing_value:.2f} dB)")
    return P.render(fig)


FIGURES = {
    "quantization-error-sawtooth": quantization_error_sawtooth,
    "snr-versus-bits": snr_versus_bits,
    "osr-and-noise-shaping": osr_and_noise_shaping,
}
