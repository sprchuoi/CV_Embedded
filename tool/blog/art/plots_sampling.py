"""Computed figures for the sampling and aliasing chapter.

Four numpy/matplotlib figures, in the order the article uses them:

    alias-frequency-map            the folding rule, as a single curve
    sampling-spectrum-replication  what sampling does to a spectrum
    quantization-noise             an ideal 3-bit quantiser, and SNR against bits
    sinc-reconstruction            ideal sinc interpolation against a zero-order hold

Unlike ``diagrams_sampling``, every line here is computed. Nothing in this module
draws random numbers, so every number that reaches the page is identical on each
rebuild. (The SVG bytes themselves still differ: matplotlib stamps ``<dc:date>``
and derives element ids from object identities, which is ``plotstyle.render``'s
business, not this module's.) The seeded generator below is declared anyway, so
that a stochastic figure added later has one obvious, reproducible source.
"""

from __future__ import annotations

import numpy as np

from . import plotstyle as P

# Rebuilds must be reproducible; see the module docstring.
RNG = np.random.default_rng(0)


# --------------------------------------------------------------------------- #
# shared shapes
# --------------------------------------------------------------------------- #


def _lobe(f, half_width):
    """A raised-cosine lobe: 1 at DC, 0 at ``+/-half_width``, zero beyond."""
    out = np.zeros_like(f)
    inside = np.abs(f) <= half_width
    out[inside] = 0.5 * (1.0 + np.cos(np.pi * f[inside] / half_width))
    return out


def _dashed(ax, x0, x1, y0, y1, *, color=P.NOTE):
    ax.plot([x0, x1], [y0, y1], color=color, lw=1.1, ls=(0, (4, 3)), zorder=2)


def _head(ax, title, subtitle=None):
    """Title plus a subtitle that clears it.

    ``P.title`` draws both at the same offset above the axes, so on panels this
    short the second line lands on the first. Lifting the title by a few extra
    points is all the separation the pair needs.
    """
    if subtitle is None:
        P.title(ax, title)
        return
    ax.set_title(title, pad=22)
    ax.text(0.0, 1.012, subtitle, transform=ax.transAxes, fontsize=9,
            color=P.MUTED, va="bottom")


# --------------------------------------------------------------------------- #
# 1. the folding rule as a curve
# --------------------------------------------------------------------------- #


def alias_frequency_map() -> str:
    """Apparent frequency against true frequency: every zone folds onto the first."""
    fs = 10.0
    fig, ax = P.figure(height=3.6)

    f = np.linspace(0.0, 3.5 * fs, 4001)
    apparent = np.abs(np.mod(f + fs / 2.0, fs) - fs / 2.0)

    # Alternate Nyquist zones, so the folds read as bands rather than as noise.
    for k in range(1, 7, 2):
        ax.axvspan(k * fs / 2.0, (k + 1) * fs / 2.0,
                   color=P.RULE_SOFT, lw=0, zorder=0)

    ax.plot(f, apparent, color=P.ACCENT, lw=2.2, zorder=4)

    for i in range(7):
        ax.text((i + 0.5) * fs / 2.0, 5.28, str(i + 1), color=P.MUTED,
                fontsize=8.5, ha="center", va="center")

    # --- the two working points: 1 Hz and 11 Hz land on the same sample values --
    _dashed(ax, 1.0, 1.0, 0.0, 1.0)
    _dashed(ax, 11.0, 11.0, 0.0, 1.0)
    _dashed(ax, 1.0, 11.0, 1.0, 1.0)
    ax.plot([1.0, 11.0], [1.0, 1.0], marker="o", ls="none", ms=6.5,
            color=P.NOTE, mec=P.PANEL, mew=1.3, zorder=6)
    ax.text(1.15, 0.38, "1 Hz tone", color=P.NOTE, fontsize=9.5,
            ha="left", va="bottom")
    ax.text(11.35, 0.38, "11 Hz tone", color=P.NOTE, fontsize=9.5,
            ha="left", va="bottom")
    ax.text(6.0, 1.34, "both appear at 1 Hz", color=P.NOTE, fontsize=9.5,
            ha="center", va="bottom")

    ticks = [k * fs / 2.0 for k in range(8)]
    labels = ["0", "$f_s/2$", "$f_s$", "$3f_s/2$", "$2f_s$",
              "$5f_s/2$", "$3f_s$", "$7f_s/2$"]
    ax.set_xticks(ticks, labels=labels)
    ax.set_xlim(0.0, 3.5 * fs)
    ax.set_ylim(0.0, 5.5)
    ax.set_yticks([0, 1, 2, 3, 4, 5])
    _head(ax, "Aliasing is one curve",
          "every tone above $f_s/2$ folds onto it - $f_s$ = 10 Hz")
    P.tidy(ax, xlabel="true frequency (Hz)",
           ylabel="apparent frequency after sampling (Hz)")
    return P.render(fig)


# --------------------------------------------------------------------------- #
# 2. spectrum replication
# --------------------------------------------------------------------------- #


def _replication_panel(ax, f, fs, half_width, *, shade, grid_label):
    """One spectrum-replication panel: baseband lobe plus its images."""
    stack = [_lobe(f - k * fs, half_width) for k in (-2, -1, 0, 1, 2)]

    grid = None
    for k in (-2, -1, 0, 1, 2):
        line = ax.axvline(k * fs, color=P.RULE, lw=1.1, ls=(0, (1.5, 2.5)),
                          zorder=0)
        if k == 1:
            grid = line

    if shade:
        # The doubly-covered region: where two replicas are both non-zero the
        # heights add, and the overlap is the height of the shorter of the two.
        covered = (np.array(stack) > 1e-9).sum(axis=0)
        second = np.sort(np.array(stack), axis=0)[-2]
        lens = np.where(covered >= 2, second, 0.0)
        ax.fill_between(f, 0.0, lens, where=lens > 0.0, facecolor=P.WARN,
                        alpha=0.20, hatch="///", edgecolor=P.WARN, lw=0.0,
                        zorder=2)

    base, = ax.plot(f, stack[2], color=P.ACCENT, lw=2.1, zorder=4,
                    label="baseband lobe")
    replica = None
    for k in (1, 2, -1, -2):
        line, = ax.plot(f, _lobe(f - k * fs, half_width), color=P.NOTE, lw=1.5,
                        dashes=(5, 3), zorder=3, label="replicas at $k f_s$")
        if replica is None:
            replica = line

    handles = [base, replica]
    names = ["baseband lobe", "replicas at $k f_s$"]
    if shade:
        total, = ax.plot(f, np.sum(stack, axis=0), color=P.OPTICAL, lw=1.3,
                         ls=(0, (1.0, 1.8)), zorder=5, label="sum of replicas")
        handles.append(total)
        names.append("sum of the replicas")
    if grid_label:
        handles.append(grid)
        names.append("$k f_s$ grid")
    ax.set_ylim(0.0, 1.6)
    ax.set_yticks([])
    ax.grid(axis="y", visible=False)
    return handles, names


def sampling_spectrum_replication() -> str:
    """A band-limited and an over-wide spectrum, sampled at the same rate."""
    fs = 10.0
    f = np.linspace(-2.0 * fs, 2.0 * fs, 4001)
    fig, axes = P.figure(height=4.4, nrows=2, sharex=True)
    top, bottom = axes

    handles, names = _replication_panel(top, f, fs, 3.0, shade=False,
                                        grid_label=True)
    handles2, names2 = _replication_panel(bottom, f, fs, 7.0, shade=True,
                                          grid_label=False)

    top.legend(handles, names, loc="upper right", ncol=1)
    bottom.legend(handles2, names2, loc="upper left", ncol=1)

    # Mark the replicas in the clean case: two arrows from one label, both
    # travelling through the empty gap a band-limited signal leaves behind.
    top.annotate("replicas", xy=(10.0, 1.0), xytext=(0.0, 1.33),
                 ha="center", va="center", color=P.NOTE, fontsize=9,
                 arrowprops=dict(arrowstyle="->", color=P.NOTE, lw=1.0,
                                 shrinkA=3, shrinkB=2))
    top.annotate("", xy=(-10.0, 1.0), xytext=(0.0, 1.33),
                 arrowprops=dict(arrowstyle="->", color=P.NOTE, lw=1.0,
                                 shrinkA=3, shrinkB=2))

    bottom.annotate("aliasing —\nthe replicas add", xy=(4.6, 0.10),
                    xytext=(5.0, 1.06), ha="center", va="center",
                    color=P.WARN, fontsize=9,
                    arrowprops=dict(arrowstyle="->", color=P.WARN, lw=1.1,
                                    shrinkA=3, shrinkB=1))

    _head(top, "Band-limited: $f_s > 2B$",
          "B = 3 Hz, $f_s$ = 10 Hz - the images stay clear of the baseband")
    _head(bottom, "Not band-limited: $f_s < 2B$",
          "B = 7 Hz, $f_s$ = 10 Hz - the images reach back into it")
    P.tidy(bottom, xlabel="frequency (Hz)")
    return P.render(fig)


# --------------------------------------------------------------------------- #
# 3. quantisation, and SNR against resolution
# --------------------------------------------------------------------------- #


def quantization_noise() -> str:
    """An ideal 3-bit mid-tread quantiser, then its SNR read against resolution."""
    bits = 3
    step = 2.0 / 2 ** bits                    # full scale spans -1 .. +1
    limit = 1.0 - step / 2.0
    t = np.linspace(0.0, 1.0, 4001)
    x = np.sin(2 * np.pi * 3.0 * t)
    x_q = np.clip(np.round(x / step) * step, -limit, limit)
    error = (x - x_q) / step                  # in LSBs: |error| <= 0.5

    fig, axes = P.figure(height=5.8, nrows=3, hspace=0.75,
                         height_ratios=[1.30, 0.80, 1.20])
    ax, ax_err, ax_snr = axes

    line_x, = ax.plot(t, x, color=P.MUTED, lw=1.2, label="$x(t)$")
    line_q, = ax.plot(t, x_q, color=P.ACCENT, lw=1.8, drawstyle="steps-post",
                      label="$x_q(t)$")
    ax.set_xlim(0.0, 1.0)
    ax.set_ylim(-1.15, 1.5)
    ax.tick_params(labelbottom=False)          # the error panel below carries x
    ax.legend([line_x, line_q], ["$x(t)$", "$x_q(t)$, 3 bits"],
              loc="upper center", ncol=2)
    _head(ax, "An ideal 3-bit quantiser",
          "uniform mid-tread - 8 levels - $q$ = 0.25 FS")
    P.tidy(ax, ylabel="amplitude (FS)")

    # The error gets its own panel: at three periods per second it is far too
    # busy to read as a second curve on top of the staircase.
    ax_err.plot(t, error, color=P.WARN, lw=1.0)
    for bound in (-0.5, 0.5):
        ax_err.axhline(bound, color=P.RULE_SOFT, lw=0.9, ls=(0, (3, 3)))
    ax_err.axhline(0.0, color=P.RULE, lw=0.9)
    ax_err.text(1.0, 0.52, "$\\pm$½ LSB is all an ideal quantiser may take",
                color=P.MUTED, fontsize=8.5, ha="right", va="bottom")
    ax_err.set_xlim(0.0, 1.0)
    ax_err.set_ylim(-0.62, 0.62)
    ax_err.set_yticks([-0.5, 0.0, 0.5])
    _head(ax_err, "Quantisation error")
    P.tidy(ax_err, xlabel="time (s)", ylabel="error (LSB)")

    # --- SNR against resolution ---------------------------------------------
    n = np.arange(1, 19)
    snr = 6.02 * n + 1.76
    ax_snr.plot(n, snr, color=P.ACCENT, lw=2.1)
    for mark in (8, 12, 16):
        value = 6.02 * mark + 1.76
        ax_snr.plot(mark, value, marker="o", ls="none", ms=6.0, color=P.NOTE,
                    mec=P.PANEL, mew=1.2, zorder=5)
        ax_snr.annotate(f"{mark} bits - {value:.1f} dB", xy=(mark, value),
                        xytext=(mark - 0.6, value + 4.5), ha="right",
                        va="bottom", color=P.NOTE, fontsize=9)

    ax_snr.axvline(3.0, color=P.RULE, lw=1.1, ls=(0, (3, 3)), zorder=0)
    ax_snr.text(3.4, 11.0, "the 3-bit quantiser above: 19.8 dB", color=P.MUTED,
                fontsize=8.5, ha="left", va="center")
    ax_snr.text(17.8, 24.0, "SNR = 6.02 N + 1.76 dB", color=P.INK,
                fontsize=10, ha="right", va="center")
    ax_snr.text(17.8, 11.0, "about 6 dB for every extra bit", color=P.MUTED,
                fontsize=8.5, ha="right", va="center")

    ax_snr.set_xlim(0.8, 18.4)
    ax_snr.set_ylim(0.0, 118.0)
    _head(ax_snr, "Resolution buys headroom",
          "full-scale sine, ideal quantiser")
    P.tidy(ax_snr, xlabel="resolution (bits)", ylabel="SNR (dB)")
    return P.render(fig)


# --------------------------------------------------------------------------- #
# 4. sinc reconstruction against a zero-order hold
# --------------------------------------------------------------------------- #


def sinc_reconstruction() -> str:
    """Ideal band-limited interpolation, the hold that replaces it, and the error."""
    fs = 8.0
    ts = 1.0 / fs
    n_samples = 8
    t = np.linspace(0.0, 1.0, 1601)

    def signal(t):
        return (0.8 * np.sin(2 * np.pi * 1.5 * t)
                + 0.35 * np.sin(2 * np.pi * 3.0 * t + 0.6))

    x = signal(t)
    n = np.arange(n_samples)
    t_n = n * ts
    x_n = signal(t_n)

    # Ideal interpolation sums every sample. The window only shows the eight it
    # contains, so the sum reaches well past both edges -- which is exactly what
    # makes it exact in the middle and is why the residual below is truncation
    # and not method error.
    wide = np.arange(-2048, 2049)
    x_sinc = np.sinc((t[:, None] - wide[None, :] * ts) / ts) @ signal(wide * ts)

    hold = np.minimum((t / ts).astype(int), n_samples - 1)
    x_zoh = x_n[hold]

    err_sinc = np.abs(x_sinc - x)
    err_zoh = np.abs(x_zoh - x)

    fig, (ax, ax_err) = P.figure(height=4.8, nrows=2, sharex=True, hspace=0.6,
                                 height_ratios=[1.5, 1.0])

    line_zoh, = ax.plot(t, x_zoh, color=P.WARN, lw=1.6,
                        drawstyle="steps-post", zorder=3,
                        label="zero-order hold")
    line_x, = ax.plot(t, x, color=P.MUTED, lw=1.1, zorder=4,
                      label="$x(t)$, original")
    line_sinc, = ax.plot(t, x_sinc, color=P.ACCENT, lw=1.9, zorder=5,
                         label="ideal sinc reconstruction")
    line_smp, = ax.plot(t_n, x_n, marker="o", ls="none", ms=6.0, color=P.NOTE,
                        mec=P.PANEL, mew=1.1, zorder=6, label="samples")
    ax.legend([line_x, line_sinc, line_zoh, line_smp],
              ["$x(t)$, original", "ideal sinc reconstruction",
               "zero-order hold", "samples"],
              loc="upper center", ncol=4)
    ax.set_xlim(0.0, 1.0)
    ax.set_ylim(-1.25, 1.75)
    _head(ax, "Ideal sinc interpolation vs a zero-order hold",
          "$f_s$ = 8 Hz - the eight in-window samples are marked")
    P.tidy(ax, ylabel="amplitude")

    ax_err.plot(t, err_zoh, color=P.WARN, lw=1.4,
                label=f"zero-order hold (max {err_zoh.max():.2f})")
    ax_err.plot(t, err_sinc, color=P.ACCENT, lw=1.5,
                label=f"ideal sinc (max {err_sinc.max():.0e})")
    ax_err.set_xlim(0.0, 1.0)
    ax_err.set_ylim(0.0, err_zoh.max() * 1.6)
    ax_err.legend(loc="upper left", ncol=1)
    ax_err.text(0.985, 0.9, "the sinc error is numerical zero:\nthe sum is truncated "
                            "at 2048 samples either side",
                transform=ax_err.transAxes, ha="right", va="top",
                color=P.ACCENT_DARK, fontsize=8.5)
    _head(ax_err, "Reconstruction error",
          "the hold leaves a sawtooth; the sinc sum does not")
    P.tidy(ax_err, xlabel="time (s)", ylabel="|error|")
    return P.render(fig)


FIGURES = {
    "alias-frequency-map": alias_frequency_map,
    "sampling-spectrum-replication": sampling_spectrum_replication,
    "quantization-noise": quantization_noise,
    "sinc-reconstruction": sinc_reconstruction,
}
