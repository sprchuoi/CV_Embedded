"""Computed figures for the windows and leakage chapter.

Seven figures, in the order the article uses them:

    windows-the-three           the same off-bin tone under three windows, with
                                the seam its repetition produces marked and
                                measured — the record is already tapered, and
                                the taper is the only thing that changes
    windows-kernels-db          each window's own transform in dB, with the four
                                numbers that describe a window measured on every
                                one of them: null-to-null width, first sidelobe,
                                roll-off, equivalent noise bandwidth
    windows-tradeoff            peak sidelobe against main-lobe width for the
                                standard family and a swept Kaiser parameter —
                                no point sits near the origin, and the trade can
                                be made continuous
    windows-off-bin             one off-bin tone under rectangular and Hann, then
                                a second tone 40 dB down: the rectangular skirt
                                buries it and the Hann skirt does not
    windows-scalloping          the amplitude read from a peak bin against the
                                tone's offset from that bin, one curve per
                                window, with each window's worst case marked
    windows-noise-floor         a noise record under three windows, and the two
                                corrections a window forces: the coherent gain
                                that fixes a tone, and the noise bandwidth that
                                lifts the floor
    windows-periodic-record      a record that is exactly one period: the
                                rectangular window returns one exact line, and a
                                Hann taper turns it into three bins

Nothing here asserts a transform. Every number the chapter prints is measured
from samples built in this module, printed on the figure (or in its footnote
box), and printed again to stdout under the figure's name so a build log can be
audited against the page.

Measurement conventions, stated once and used throughout:

* **Periodic windows.** ``w[n] = 0.5 − 0.5·cos(2πn/N)`` for ``n = 0 … N−1`` — the
  DFT-even Hann, not the symmetric ``N−1`` form — because that is the sequence
  a record is multiplied by. Every window here is periodic, so the taper is one
  period of a periodic function and its transform is the sum of shifted
  Dirichlet kernels with no half-sample offset. This matters: the symmetric form
  has slightly different coefficients and slightly different numbers, and the
  hand calculation in the chapter's ``try`` box uses this form.
* **Everything in bins.** Widths, offsets and noise bandwidths are measured in
  bins of the record that carries the window, so they transfer to any ``N``.
  The kernels are computed from 1024-sample windows so that the skirt has two
  decades of offset to fall through; a 64-point record has only 32 bins and
  cannot show a −18 dB/octave skirt falling for a decade.
* **The transform of a window.** ``W(f)`` is the DTFT of the window samples,
  evaluated by zero-padding the window to ``N·512`` points, so the curve is the
  window's own transform and not the record's. ``|W|`` is normalised to
  ``|W(0)|``, which is what makes the numbers comparable between windows.
* **The roll-off** is the slope of the sidelobe envelope, measured as the
  maximum of ``|W|`` inside each one-bin annulus and fitted end to end over
  16–256 bins of offset. It is quoted in dB per octave of offset, because that
  is what decides whether a weak tone ten bins out is visible.
* **Determinism.** No wall-clock measurement is printed. The one noise record
  is drawn from ``numpy.random.RandomState(7)``, whose stream is frozen by
  numpy's own compatibility guarantee, so two builds of the same commit produce
  the same SVG.

The optical footnote in :func:`windows_noise_floor` computes the same
noise-bandwidth correction at the coherent receiver's working point — a
512-point block on the 128 GSa/s front end of a 64 GBd link, 250 MHz per bin —
so the number quoted in the closing callout is arithmetic done here rather than
a remembered constant.
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
TONE_BIN = 8.5              # the off-bin tone: exactly between bins 8 and 9
WEAK_BIN = 14.5             # the weak tone of the two-tone figure, six bins away
WEAK_AMP = 0.01             # −40 dB: the level the try box asks the reader for

KERNEL_N = 1024             # window length used to measure the skirt
KERNEL_OVERSAMPLE = 512     # zero-padding of the window's own transform
ENVELOPE_TO = 256           # offset, in bins, the roll-off is fitted out to
NOISE_BLOCKS = 2048         # records averaged in the noise-floor figure
NOISE_SEED = 7              # frozen RandomState seed: see the module docstring

# the five standard windows, in the order the chapter introduces them
FAMILY = ("rectangular", "Hann", "Hamming", "Blackman", "Blackman-Harris")
FAMILY_KEY = ("rect", "hann", "hamming", "blackman", "bh4")
FAMILY_COLOUR = (P.WARN, P.ACCENT, P.NOTE, P.OPTICAL, P.ACCENT_DARK)

# the optical landing place, quoted so the closing callout is computed:
# a 512-point block on the 128 GSa/s front end of a 64 GBd link
FDE_N = 512
FDE_FS = 128.0e9
OSNR_BAND_HZ = 12.5e9       # the reference band a 0.1 nm OSNR is quoted in


# --------------------------------------------------------------------------- #
# windows, and the measurements the chapter prints
# --------------------------------------------------------------------------- #


def _window(key: str, n_samples: int = N) -> np.ndarray:
    """One period of the named window, ``n = 0 … N−1``."""
    n = np.arange(n_samples)
    theta = 2.0 * np.pi * n / n_samples
    if key == "rect":
        return np.ones(n_samples)
    if key == "hann":
        return 0.5 - 0.5 * np.cos(theta)
    if key == "hamming":
        return 0.54 - 0.46 * np.cos(theta)
    if key == "blackman":
        return 0.42 - 0.5 * np.cos(theta) + 0.08 * np.cos(2.0 * theta)
    if key == "bh4":
        return (0.35875 - 0.48829 * np.cos(theta) + 0.14128 * np.cos(2.0 * theta)
                - 0.01168 * np.cos(3.0 * theta))
    raise KeyError(key)


def _kaiser(beta: float, n_samples: int = KERNEL_N) -> np.ndarray:
    """The Kaiser window at one parameter value: the trade made continuous."""
    n = np.arange(n_samples)
    alpha = (n_samples - 1) / 2.0
    r = (n - alpha) / alpha
    return np.i0(beta * np.sqrt(np.clip(1.0 - r * r, 0.0, None))) / np.i0(beta)


def _kernel(w: np.ndarray, oversample: int = KERNEL_OVERSAMPLE):
    """``(offset_in_bins, |W|/|W(0)|)`` — the window's own transform, symmetric."""
    n = len(w)
    nfft = n * oversample
    magnitude = np.abs(np.fft.fft(w, nfft))
    magnitude = np.fft.fftshift(magnitude)
    offset = (np.arange(nfft) - nfft // 2) / nfft * n
    return offset, magnitude / magnitude[nfft // 2]


def _envelope(w: np.ndarray, oversample: int = 64) -> np.ndarray:
    """The sidelobe envelope: ``|W|`` maximised inside each one-bin annulus.

    The envelope, not the curve, is what a skirt is: the curve crosses zero
    between lobes, and the depth of a null says nothing about how far down the
    skirt has fallen. ``out[k−1]`` covers offsets ``k ± 0.5`` bins, so the
    roll-off and the crossings below are read off the lobe peaks.
    """
    offset, magnitude = _kernel(w, oversample)
    limit = len(w) // 2 - 1
    return np.array([magnitude[(offset >= k - 0.5) & (offset < k + 0.5)].max()
                     for k in range(1, limit + 1)])


def _describe(w: np.ndarray) -> dict:
    """The four numbers, plus the envelope, for one window."""
    n = len(w)
    offset, magnitude = _kernel(w)
    centre = len(magnitude) // 2

    # first null: walk out from the peak until the curve turns back up
    i = centre + 2
    while not (magnitude[i] <= magnitude[i - 1] and magnitude[i] < magnitude[i + 1]):
        i += 1
    half_width = float(offset[i])

    # first sidelobe: the highest point of the lobe beyond that null
    band = (offset >= half_width) & (offset <= 2.0 * half_width)
    first_sidelobe = float(20.0 * np.log10(magnitude[band].max()))
    first_sidelobe_at = float(offset[band][np.argmax(magnitude[band])])

    envelope = _envelope(w)
    envelope_db = 20.0 * np.log10(envelope)
    low, high = 16, min(ENVELOPE_TO, len(envelope_db))
    slope = float((envelope_db[high - 1] - envelope_db[low - 1])
                  / np.log2(high / low))

    enbw = n * np.sum(w * w) / np.sum(w) ** 2
    return {
        "width": 2.0 * half_width,
        "first_sidelobe": first_sidelobe,
        "first_sidelobe_at": first_sidelobe_at,
        "slope": slope,
        "enbw": float(enbw),
        "enbw_db": float(10.0 * np.log10(enbw)),
        "coherent_gain": float(np.sum(w) / n),
        "cg_db": float(20.0 * np.log10(np.sum(w) / n)),
        "envelope_db": envelope_db,
        "offset": offset,
        "magnitude": magnitude,
    }


def _crossing(envelope_db: np.ndarray, level: float) -> int | None:
    """First offset whose envelope is below ``level`` dB, in bins."""
    for k in range(1, len(envelope_db) + 1):
        if envelope_db[k - 1] < level:
            return k
    return None


def _db(value: float) -> float:
    return float(20.0 * np.log10(max(value, 1e-30)))


def _footnote(ax, x: float, y: float, text: str, *, colour: str = P.INK,
              size: float = 8.6, ha: str = "left", va: str = "top",
              mono: bool = False) -> None:
    """A round-cornered note inside the axes, the way every figure here does it."""
    ax.text(x, y, text, transform=ax.transAxes, color=colour, fontsize=size,
            ha=ha, va=va, zorder=9,
            family="monospace" if mono else "sans-serif", linespacing=1.35,
            bbox=dict(boxstyle="round,pad=0.38", facecolor=P.PANEL,
                      edgecolor=P.RULE_SOFT, linewidth=1.0))


def _table(ax, x: float, y: float, rows: list[str], *, size: float = 7.8,
           colour: str = P.INK, ha: str = "left", va: str = "top") -> None:
    """A monospace table on the axes, or on the figure, with the numbers aligned.

    ``ax`` may be an axes or a figure. A figure-level call must not pass a
    ``transform``: passing ``None`` resets the artist's transform to identity,
    which puts the table in the bottom-left corner of the canvas in pixels.
    """
    text = "\n".join(rows)
    if hasattr(ax, "transAxes"):
        ax.text(x, y, text, transform=ax.transAxes, color=colour, fontsize=size,
                ha=ha, va=va, zorder=9, family="monospace", linespacing=1.45,
                bbox=dict(boxstyle="round,pad=0.42", facecolor=P.PANEL,
                          edgecolor=P.RULE_SOFT, linewidth=1.0))
    else:
        ax.text(x, y, text, color=colour, fontsize=size, ha=ha, va=va,
                zorder=9, family="monospace", linespacing=1.45)


# --------------------------------------------------------------------------- #
# 1. the record is already windowed, and the taper is the seam
# --------------------------------------------------------------------------- #


def windows_the_three() -> str:
    """The same off-bin tone under three windows, and the seam each leaves."""
    n = np.arange(N)
    tone = np.cos(2.0 * np.pi * TONE_BIN * n / N)
    rows = (
        ("rect", "rectangular: no taper at all", P.WARN,
         "the dashed envelope is flat at ±1, and the record jumps at the seam"),
        ("hann", "Hann: $0.5 - 0.5\\cos(2\\pi n/N)$", P.ACCENT,
         "the taper is the dashed envelope, and it takes the record to zero"),
        ("bh4", "Blackman-Harris, four terms", P.OPTICAL,
         "the same, four terms deep: 0.0001 is what is left at the ends"),
    )

    fig, axes = P.figure(height=8.6, nrows=3, hspace=0.82)
    jumps = {}
    for ax, (key, heading, colour, subtitle) in zip(axes, rows):
        w = _window(key)
        y = tone * w
        jump = abs(float(y[0] - y[-1]))
        jumps[key] = (float(y[0]), float(y[-1]), jump)

        # the repetition the probes see: two copies, one either side
        grid = np.arange(-16, N + 16)
        ax.plot(grid, tone[np.mod(grid, N)] * w[np.mod(grid, N)],
                color=P.RULE, lw=2.6, zorder=1)
        ax.plot(n, w, color=P.MUTED, lw=1.0, ls=(0, (3, 2)), zorder=3)
        ax.plot(n, -w, color=P.MUTED, lw=1.0, ls=(0, (3, 2)), zorder=3)
        ax.plot(n, y, color=colour, lw=1.2, marker="o", ms=2.6, mec=P.PANEL,
                mew=0.0, zorder=4)
        for seam in (0, N):
            ax.axvline(seam, color=P.RULE, lw=1.0, ls=(0, (2, 2)), zorder=2)
        ax.annotate("", xy=(N, float(y[0])), xytext=(N, float(y[-1])),
                    arrowprops=dict(arrowstyle="<->", color=P.WARN,
                                    linewidth=1.3, shrinkA=0, shrinkB=0),
                    zorder=8)
        ax.text(N + 1.5, 0.5 * (float(y[0]) + float(y[-1])),
                f"seam {jump:.4f}", color=P.WARN, fontsize=8.8, ha="left",
                va="center", zorder=9)
        ax.set_xlim(-16.0, N + 18.0)
        ax.set_ylim(-1.3, 1.3)
        ax.set_yticks([-1, 0, 1])
        ax.set_xticks([0, 16, 32, 48, 64])
        P.tidy(ax, ylabel="value")
        P.title(ax, heading, subtitle=subtitle)

    P.tidy(axes[-1], xlabel="sample index  n  (one sample = 0.125 ms)",
           ylabel="value")

    print(f"[windows-the-three] one 1 kHz tone at {TONE_BIN * BIN:g} Hz in a "
          f"{1000.0 * N / FS:.1f} ms record at {FS:g} Hz: bin {TONE_BIN}, "
          f"half a bin off")
    for key, (first, last, jump) in jumps.items():
        print(f"[windows-the-three] {key:9s}: record starts {first:+.4f}, ends "
              f"{last:+.4f}; the repetition jumps by {jump:.4f}")
    print(f"[windows-the-three] the taper multiplies that jump by "
          f"{jumps['hann'][2] / jumps['rect'][2]:.1e} (Hann) and "
          f"{jumps['bh4'][2] / jumps['rect'][2]:.1e} (Blackman-Harris)")
    return P.render(fig)


# --------------------------------------------------------------------------- #
# 2. what a taper buys, and the four numbers it costs
# --------------------------------------------------------------------------- #


def windows_kernels_db() -> str:
    """Each window's own transform: main lobe, sidelobes, and the numbers."""
    stats = {key: _describe(_window(key, KERNEL_N)) for key in FAMILY_KEY}

    fig, axes = P.figure(height=9.0, nrows=2, hspace=0.46,
                         height_ratios=[0.80, 1.0])
    fig.subplots_adjust(bottom=0.20)
    ax_lin, ax_db = axes

    # --- top: the main lobe, linear, with every null where it belongs -------
    for key, name, colour in zip(FAMILY_KEY, FAMILY, FAMILY_COLOUR):
        d = stats[key]
        sel = (d["offset"] >= 0.0) & (d["offset"] <= 5.0)
        ax_lin.plot(d["offset"][sel], d["magnitude"][sel], color=colour, lw=1.7,
                    zorder=4, label=f"{name}: {d['width']:.0f} bins")
    for null in (1, 2, 3, 4):
        ax_lin.axvline(null, color=P.RULE, lw=0.9, ls=(0, (2, 3)), zorder=2)
    ax_lin.set_xlim(0.0, 5.0)
    ax_lin.set_ylim(-0.06, 1.06)
    P.tidy(ax_lin, xlabel="offset from the window's centre, in bins",
           ylabel="$|W(f)|\\,/\\,|W(0)|$",
           legend=[f"{name}: {stats[key]['width']:.0f} bins"
                   for key, name in zip(FAMILY_KEY, FAMILY)],
           legend_loc="upper right", ncol=1)
    P.title(ax_lin, "Widen the main lobe and you have bought the sidelobes",
            subtitle="each window's own transform, from its own samples: every "
                     "one peaks at 1.000, and the width is twice the first null")

    # --- bottom: the same in dB, the half of it that carries the skirt ------
    for key, name, colour in zip(FAMILY_KEY, FAMILY, FAMILY_COLOUR):
        d = stats[key]
        sel = (d["offset"] >= 0.0) & (d["offset"] <= 12.0)
        curve = 20.0 * np.log10(np.maximum(d["magnitude"][sel], 1e-14))
        ax_db.plot(d["offset"][sel], curve, color=colour, lw=1.0, zorder=4)
        # the first sidelobe, marked rather than annotated: the table has the number
        ax_db.plot([d["first_sidelobe_at"]], [d["first_sidelobe"]], "o", ms=5.0,
                   color=colour, mec=P.PANEL, mew=1.0, zorder=7)
    ax_db.axhline(-40.0, color=P.RULE, lw=1.0, ls=(0, (4, 3)), zorder=2)
    ax_db.set_xlim(0.0, 12.0)
    ax_db.set_ylim(-130.0, 4.0)
    ax_db.set_yticks([0, -20, -40, -60, -80, -100, -120])
    P.tidy(ax_db, xlabel="offset from the window's centre, in bins, positive half",
           ylabel="$|W(f)|\\,/\\,|W(0)|$  (dB)")
    P.title(ax_db, "Four numbers describe a window, and the table is the whole trade",
            subtitle="the lobe, the first sidelobe, the slope of the skirt, and "
                     "the noise bandwidth a quiet record occupies")

    short = ("rectangular", "Hann", "Hamming", "Blackman", "BH4")
    header = ("window", "width", "1st sl", "roll", "ENBW", "@8", "@64", "@256")
    rows = [f"{header[0]:<13}{header[1]:>6}{header[2]:>8}{header[3]:>7}"
            f"{header[4]:>8}{header[5]:>7}{header[6]:>7}{header[7]:>7}"]
    for key, name in zip(FAMILY_KEY, short):
        d = stats[key]
        rows.append(f"{name:<13}{d['width']:>6.0f}{d['first_sidelobe']:>8.1f}"
                    f"{d['slope']:>7.1f}{d['enbw']:>8.2f}"
                    f"{d['envelope_db'][7]:>7.1f}{d['envelope_db'][63]:>7.1f}"
                    f"{d['envelope_db'][255]:>7.1f}")
    # a panel-coloured speck at the left edge, so that the tight bounding box
    # leaves the table a margin instead of starting at the table itself
    fig.text(0.012, 0.30, ".", color=P.PANEL, fontsize=6.0, ha="left",
             va="center")
    _table(fig, 0.045, 0.014, rows, size=7.5, va="bottom")
    fig.text(0.985, 0.014,
             "width in bins, sidelobe in dB re the peak,\n"
             "roll-off in dB/octave, ENBW in bins; the dots\n"
             "are the first sidelobes. Hann's skirt falls\n"
             "below BH4's (Blackman-Harris) at 81 bins.",
             color=P.MUTED, fontsize=7.8, ha="right", va="bottom",
             linespacing=1.45)

    print(f"[windows-kernels-db] windows of {KERNEL_N} samples, transform "
          f"zero-padded ×{KERNEL_OVERSAMPLE}; roll-off fitted over 16–"
          f"{ENVELOPE_TO} bins")
    for key, name in zip(FAMILY_KEY, FAMILY):
        d = stats[key]
        print(f"[windows-kernels-db] {name:16s} width {d['width']:4.0f} bins, "
              f"first sidelobe {d['first_sidelobe']:7.2f} dB at "
              f"{d['first_sidelobe_at']:.2f} bins, roll-off {d['slope']:6.2f} "
              f"dB/octave, ENBW {d['enbw']:.4f} bins ({d['enbw_db']:.2f} dB), "
              f"coherent gain {d['cg_db']:.2f} dB")
    hann, bh4 = stats["hann"], stats["bh4"]
    start = int(max(stats[key]["width"] for key in FAMILY_KEY))
    cross = next((k for k in range(start, len(hann["envelope_db"]) + 1)
                  if hann["envelope_db"][k - 1] < bh4["envelope_db"][k - 1]),
                 None)
    print(f"[windows-kernels-db] envelope at 4/8/16/32/64/128/256 bins — "
          f"rectangular: "
          + " ".join(f"{stats['rect']['envelope_db'][k - 1]:.1f}"
                     for k in (4, 8, 16, 32, 64, 128, 256)))
    print(f"[windows-kernels-db] the same for Hann:      "
          + " ".join(f"{hann['envelope_db'][k - 1]:.1f}"
                     for k in (4, 8, 16, 32, 64, 128, 256)))
    print(f"[windows-kernels-db] Hamming:                "
          + " ".join(f"{stats['hamming']['envelope_db'][k - 1]:.1f}"
                     for k in (4, 8, 16, 32, 64, 128, 256)))
    print(f"[windows-kernels-db] Blackman-Harris:        "
          + " ".join(f"{bh4['envelope_db'][k - 1]:.1f}"
                     for k in (4, 8, 16, 32, 64, 128, 256)))
    print(f"[windows-kernels-db] Hann's skirt falls below Blackman-Harris's at "
          f"{cross} bins of offset")
    for level in (-40.0, -60.0, -80.0):
        print(f"[windows-kernels-db] first offset below {level:+.0f} dB — "
              + ", ".join(f"{name}: {_crossing(stats[key]['envelope_db'], level)}"
                          for key, name in zip(FAMILY_KEY, FAMILY)))
    print(f"[windows-kernels-db] the four-term coefficients sum to "
          f"{0.35875 - 0.48829 + 0.14128 - 0.01168:+.5f}, not zero")
    return P.render(fig)


# --------------------------------------------------------------------------- #
# 3. no window wins both
# --------------------------------------------------------------------------- #


def windows_tradeoff() -> str:
    """Peak sidelobe against main-lobe width, with the Kaiser trade swept."""
    betas = np.arange(0.0, 15.01, 0.5)
    kaiser = []
    for beta in betas:
        d = _describe(_kaiser(float(beta)))
        kaiser.append((d["width"], d["first_sidelobe"], float(beta)))
    stats = {key: _describe(_window(key, KERNEL_N)) for key in FAMILY_KEY}

    fig, ax = P.figure(height=5.4)
    ax.fill_between([1.25, 3.5], -118.0, -42.0, color=P.RULE_SOFT, zorder=0,
                    linewidth=0.0)
    ax.text(1.45, -104.0, "narrow and deep:\nno window here", color=P.MUTED,
            fontsize=9.0, ha="left", va="center", zorder=7, linespacing=1.4)

    ax.plot([k[0] for k in kaiser], [k[1] for k in kaiser], color=P.NOTE,
            lw=1.3, ls=(0, (4, 2)), zorder=3,
            label="Kaiser, $\\beta$ = 0 … 15")
    ax.plot([k[0] for k in kaiser], [k[1] for k in kaiser], "o", ms=3.0,
            color=P.NOTE, mfc=P.PANEL, mew=0.9, ls="none", zorder=4)

    placed = (
        ("rect", (0.16, 3.4, "left", "bottom")),
        ("hann", (0.16, 3.4, "left", "bottom")),
        ("hamming", (-0.22, 0.0, "right", "center")),
        ("blackman", (0.16, 3.4, "left", "bottom")),
        ("bh4", (0.16, 3.4, "left", "bottom")),
    )
    for key, (dx, dy, ha, va) in placed:
        colour = FAMILY_COLOUR[FAMILY_KEY.index(key)]
        d = stats[key]
        ax.plot([d["width"]], [d["first_sidelobe"]], "o", ms=8.0, color=colour,
                mec=P.PANEL, mew=1.2, zorder=8)
        ax.text(d["width"] + dx, d["first_sidelobe"] + dy,
                f"{FAMILY[FAMILY_KEY.index(key)]}\n"
                f"{d['width']:.0f} bins, {d['first_sidelobe']:.1f} dB",
                color=colour, fontsize=8.6, ha=ha, va=va, zorder=9,
                linespacing=1.3)

    ax.set_xlim(1.25, 11.2)
    ax.set_ylim(-118.0, -4.0)
    ax.set_yticks([-20, -40, -60, -80, -100])
    ax.set_xticks([2, 3, 4, 5, 6, 7, 8, 9, 10, 11])
    P.tidy(ax, xlabel="main-lobe width, null to null, in bins",
           ylabel="first sidelobe  (dB re the peak)")
    P.title(ax, "The trade is resolution against dynamic range, and nobody wins it twice",
            subtitle="the standard family is a staircase; the dashed Kaiser curve "
                     "($\\beta$ = 0 … 15) turns the same staircase into a dial")

    print("[windows-tradeoff] window           width(bins)  first sidelobe(dB)")
    for key, name in zip(FAMILY_KEY, FAMILY):
        d = stats[key]
        print(f"[windows-tradeoff] {name:18s}{d['width']:>8.0f}{d['first_sidelobe']:>18.1f}")
    print("[windows-tradeoff] Kaiser sweep, beta 0 to 15 in 0.5 steps: width "
          f"{kaiser[0][0]:.2f} to {kaiser[-1][0]:.2f} bins, sidelobe "
          f"{kaiser[0][1]:.1f} to {kaiser[-1][1]:.1f} dB")
    for beta in (0.0, 3.0, 4.25, 6.0, 9.0, 12.0, 15.0):
        match = min(kaiser, key=lambda k: abs(k[2] - beta))
        print(f"[windows-tradeoff] Kaiser beta = {match[2]:4.2f}: width "
              f"{match[0]:.2f} bins, first sidelobe {match[1]:.1f} dB")
    closest = min(kaiser, key=lambda k: abs(k[1] - stats["hann"]["first_sidelobe"]))
    hann_k = _describe(_kaiser(closest[2]))
    print(f"[windows-tradeoff] at Hann's sidelobe ({stats['hann']['first_sidelobe']:.1f} "
          f"dB) Kaiser beta = {closest[2]:.2f} gives width {closest[0]:.2f} bins "
          f"and ENBW {hann_k['enbw']:.2f} bins, against Hann's "
          f"{stats['hann']['enbw']:.2f} bins")
    return P.render(fig)


# --------------------------------------------------------------------------- #
# 4. one tone off a bin, and a weak tone next to a strong one
# --------------------------------------------------------------------------- #


def windows_off_bin() -> str:
    """The tone's skirt under two windows, then a 40 dB weaker tone beside it."""
    n = np.arange(N)
    bins = np.arange(N // 2 + 1)
    strong = np.cos(2.0 * np.pi * TONE_BIN * n / N)
    weak = WEAK_AMP * np.cos(2.0 * np.pi * WEAK_BIN * n / N)
    pair = strong + weak

    measured = {}
    for key in ("rect", "hann"):
        w = _window(key)
        single = np.abs(np.fft.fft(strong * w))[:N // 2 + 1]
        both = np.abs(np.fft.fft(pair * w))[:N // 2 + 1]
        peak = float(single.max())
        measured[key] = {
            "single_db": 20.0 * np.log10(np.maximum(single / peak, 1e-20)),
            "both_db": 20.0 * np.log10(np.maximum(both / both.max(), 1e-20)),
            "peak": peak,
            "peak_at": int(np.argmax(single)),
            "scallop": _db(2.0 * peak / np.sum(w)),
            "at_six": float(20.0 * np.log10(single[14] / peak)),
            "weak_pair": float(20.0 * np.log10(both[14:16].max() / both.max())),
            "weak_bins": (float(20.0 * np.log10(both[14] / both.max())),
                          float(20.0 * np.log10(both[15] / both.max()))),
        }

    fig, axes = P.figure(height=7.8, nrows=2, hspace=0.56)
    fig.subplots_adjust(bottom=0.125)
    ax_one, ax_two = axes

    # --- top: one tone, two skirts -----------------------------------------
    for key, name, colour in (("rect", "rectangular", P.WARN),
                              ("hann", "Hann", P.ACCENT)):
        ax_one.plot(bins, measured[key]["single_db"], color=colour, lw=1.5,
                    zorder=4,
                    label=f"{name}: peak bin reads {measured[key]['scallop']:+.2f} dB")
    ax_one.axhline(-40.0, color=P.RULE, lw=1.0, ls=(0, (4, 3)), zorder=2)
    ax_one.text(24.0, -38.2, "−40 dB", color=P.MUTED, fontsize=8.6, ha="right",
                va="bottom", zorder=7)
    ax_one.set_xlim(-0.5, 24.5)
    ax_one.set_ylim(-90.0, 3.0)
    ax_one.set_yticks([0, -20, -40, -60, -80])
    P.tidy(ax_one, ylabel="$|X[k]|$  (dB re the peak)",
           legend=[f"rectangular: peak bin reads {measured['rect']['scallop']:+.2f} dB",
                   f"Hann: peak bin reads {measured['hann']['scallop']:+.2f} dB"],
           legend_loc="upper right")
    P.title(ax_one, "One tone half a bin off: the skirt is the window's transform",
            subtitle=f"{TONE_BIN * BIN:g} Hz in a {1000.0 * N / FS:.1f} ms record — "
                     "the same tone, two windows, two skirts")

    # --- bottom: a second tone 40 dB down ----------------------------------
    for key, name, colour in (("rect", "rectangular", P.WARN),
                              ("hann", "Hann", P.ACCENT)):
        ax_two.plot(bins, measured[key]["both_db"], color=colour, lw=1.5,
                    zorder=4)
        ax_two.plot([14, 15], [measured[key]["weak_pair"]] * 2, "o", ms=5.0,
                    color=colour, mfc=P.PANEL, mew=1.2, ls="none", zorder=6)
    ax_two.axhline(-40.0, color=P.RULE, lw=1.0, ls=(0, (4, 3)), zorder=2)
    ax_two.annotate("the tone 40 dB down, at bin 14.5",
                    xy=(14.6, measured["hann"]["weak_pair"]),
                    xytext=(17.4, -30.0), color=P.ACCENT, fontsize=8.8, ha="left",
                    va="center", zorder=9,
                    arrowprops=dict(arrowstyle="->", color=P.ACCENT,
                                    linewidth=1.0, shrinkA=2, shrinkB=5))
    ax_two.set_xlim(-0.5, 24.5)
    ax_two.set_ylim(-90.0, 3.0)
    ax_two.set_yticks([0, -20, -40, -60, -80])
    P.tidy(ax_two, xlabel="bin index  k", ylabel="$|X[k]|$  (dB re the peak)",
           legend=[f"rectangular: the same tone reads "
                   f"{measured['rect']['weak_pair']:.1f} dB",
                   f"Hann: it reads {measured['hann']['weak_pair']:.1f} dB"],
           legend_loc="lower left")
    P.title(ax_two, "A tone 40 dB down is visible under one window and not the other",
            subtitle=f"amplitude {WEAK_AMP:g} at {WEAK_BIN * BIN:g} Hz, six bins "
                     "from a tone of amplitude 1")

    fig.text(0.030, 0.010,
             "bins 14 and 15, re the peak: rectangular "
             f"{measured['rect']['weak_bins'][0]:.1f} and "
             f"{measured['rect']['weak_bins'][1]:.1f} dB, Hann "
             f"{measured['hann']['weak_bins'][0]:.1f} and "
             f"{measured['hann']['weak_bins'][1]:.1f} dB.\n"
             f"With no second tone the rectangular skirt at bin 14 is "
             f"{measured['rect']['at_six']:.1f} dB and Hann's is "
             f"{measured['hann']['at_six']:.1f} dB: the weak tone stands "
             f"{measured['hann']['weak_pair'] - measured['hann']['at_six']:.1f} dB "
             "above Hann's skirt and is buried in the rectangle's.",
             color=P.MUTED, fontsize=7.9, ha="left", va="bottom", linespacing=1.5)

    print(f"[windows-off-bin] one tone at {TONE_BIN} bins (amplitude 1), N = {N}")
    for key, name in (("rect", "rectangular"), ("hann", "Hann")):
        m = measured[key]
        print(f"[windows-off-bin] {name:12s}: peak bin {m['peak_at']} reads "
              f"{m['scallop']:+.2f} dB of the true amplitude; |X[14]| = "
              f"{m['at_six']:.2f} dB re the peak, six bins out")
    print(f"[windows-off-bin] two tones at {TONE_BIN} and {WEAK_BIN} bins, "
          f"amplitudes 1 and {WEAK_AMP:g} (−40 dB)")
    for key, name in (("rect", "rectangular"), ("hann", "Hann")):
        m = measured[key]
        print(f"[windows-off-bin] {name:12s}: bins 14 and 15 read "
              f"{m['weak_bins'][0]:.2f} and {m['weak_bins'][1]:.2f} dB re the "
              f"peak; the weak tone's best bin {m['weak_pair']:.2f} dB")
    print(f"[windows-off-bin] the rectangular skirt at bin 14 alone is "
          f"{measured['rect']['at_six']:.2f} dB; adding the weak tone lifts it to "
          f"{measured['rect']['weak_bins'][0]:.2f} dB, a ripple of "
          f"{measured['rect']['weak_bins'][0] - measured['rect']['at_six']:.2f} dB")
    print(f"[windows-off-bin] Hann's skirt at bin 14 alone is "
          f"{measured['hann']['at_six']:.2f} dB; the weak tone stands "
          f"{measured['hann']['weak_pair'] - measured['hann']['at_six']:.2f} dB "
          f"above it")
    return P.render(fig)


# --------------------------------------------------------------------------- #
# 5. the peak of a lobe is not the amplitude
# --------------------------------------------------------------------------- #


def windows_scalloping() -> str:
    """The amplitude read off a peak bin, against the tone's offset from it."""
    offsets = np.linspace(0.0, 0.5, 201)
    n = np.arange(N)
    curves = {}
    for key in FAMILY_KEY:
        w = _window(key)
        errors = []
        for delta in offsets:
            x = np.cos(2.0 * np.pi * (8.0 + delta) * n / N)
            spectrum = np.abs(np.fft.fft(x * w))[:N // 2 + 1]
            errors.append(_db(2.0 * spectrum.max() / np.sum(w)))
        curves[key] = np.array(errors)

    fig, ax = P.figure(height=4.9)
    for key, name, colour in zip(FAMILY_KEY, FAMILY, FAMILY_COLOUR):
        worst = int(np.argmin(curves[key]))
        ax.plot(offsets, curves[key], color=colour, lw=1.6, zorder=4,
                label=f"{name}: worst {curves[key].min():.2f} dB, "
                      f"{curves[key][-1]:.2f} at half a bin")
        ax.plot([offsets[worst]], [curves[key][worst]], "o", ms=5.5, color=colour,
                mfc=P.PANEL, mew=1.3, ls="none", zorder=6)
    ax.axhline(0.0, color=P.SOFT, lw=0.9, zorder=2)
    ax.axvline(0.5, color=P.RULE, lw=1.0, ls=(0, (4, 3)), zorder=2)
    ax.text(0.018, 0.26,
            "the rectangular worst lands at 0.49 bins, not 0.50:\n"
            "the mirror image is still adding to the low side",
            transform=ax.transAxes, color=P.WARN, fontsize=8.4, ha="left",
            va="top", zorder=9, linespacing=1.35)
    _footnote(ax, 0.985, 0.94,
              "read as $2\\max|X|/\\sum w$: the correction that\n"
              "makes an on-bin tone exact, applied to an off-bin one",
              ha="right", size=8.4)
    ax.set_xlim(0.0, 0.515)
    ax.set_ylim(-4.2, 0.25)
    ax.set_xticks([0.0, 0.1, 0.2, 0.3, 0.4, 0.5])
    P.tidy(ax, xlabel="offset of the tone from the nearest bin  (bins)",
           ylabel="amplitude error  (dB)",
           legend=[f"{name}: worst {curves[key].min():.2f} dB, "
                   f"{curves[key][-1]:.2f} at half a bin"
                   for key in FAMILY_KEY],
           legend_loc="center left")
    P.title(ax, "Scalloping is the amplitude you lose for not landing on a bin",
            subtitle="one tone, one record, swept across half a bin: the peak bin "
                     "is not the amplitude, and the window decides how far off it is")

    print(f"[windows-scalloping] worst amplitude error over a half-bin sweep, "
          f"N = {N}")
    for key, name in zip(FAMILY_KEY, FAMILY):
        worst = int(np.argmin(curves[key]))
        print(f"[windows-scalloping] {name:18s} {curves[key][worst]:+.2f} dB at "
              f"{offsets[worst]:.3f} bins from the tone; at half a bin "
              f"{curves[key][-1]:+.2f} dB")
    return P.render(fig)


# --------------------------------------------------------------------------- #
# 6. what a window does to the floor
# --------------------------------------------------------------------------- #


def windows_noise_floor() -> str:
    """A noise record under three windows: the floor, and the two corrections."""
    stats = {key: _describe(_window(key, KERNEL_N)) for key in FAMILY_KEY}
    rng = np.random.RandomState(NOISE_SEED)
    noise = rng.standard_normal((NOISE_BLOCKS, N))
    bins = np.arange(1, N // 2)

    floors = {}
    for key in ("rect", "hann", "bh4"):
        w = _window(key)
        power = np.abs(np.fft.fft(noise * w, axis=1))[:, 1:N // 2] ** 2
        # the mean over blocks and bins, after the coherent-gain correction that
        # makes a tone read its own amplitude
        floors[key] = 10.0 * np.log10(np.mean(power) / np.sum(w) ** 2)

    reference = floors["rect"]
    at_fde = 10.0 * np.log10(OSNR_BAND_HZ / (FDE_FS / FDE_N))
    at_fde_hann = 10.0 * np.log10(OSNR_BAND_HZ
                                  / (FDE_FS / FDE_N * stats["hann"]["enbw"]))
    fig, axes = P.figure(height=7.4, nrows=2, hspace=0.60,
                         height_ratios=[1.0, 0.9])
    fig.subplots_adjust(bottom=0.135)
    ax_floor, ax_bars = axes

    # --- top: three floors, measured and predicted --------------------------
    for key, name, colour in (("rect", "rectangular", P.WARN),
                              ("hann", "Hann", P.ACCENT),
                              ("bh4", "Blackman-Harris", P.OPTICAL)):
        w = _window(key)
        power = np.abs(np.fft.fft(noise * w, axis=1))[:, 1:N // 2] ** 2
        power = power / np.sum(w) ** 2
        trace = 10.0 * np.log10(power.mean(axis=0)) - reference
        ax_floor.plot(bins, trace, color=colour, lw=1.3, zorder=4)
        ax_floor.axhline(stats[key]["enbw_db"], color=colour, lw=1.0,
                         ls=(0, (5, 3)), zorder=2)
        ax_floor.text(N // 2 - 0.8, stats[key]["enbw_db"] + 0.13,
                      f"{name}: {floors[key] - reference:+.2f} dB measured, "
                      f"{stats[key]['enbw_db']:+.2f} predicted",
                      color=colour, fontsize=8.4, ha="right", va="bottom",
                      zorder=9)
    ax_floor.set_xlim(0.5, N // 2 - 0.5)
    ax_floor.set_ylim(-1.6, 4.6)
    P.tidy(ax_floor, xlabel="bin index  k",
           ylabel="mean floor  (dB re rectangular)")
    P.title(ax_floor, "Windows a quiet record too, and the floor comes up with it",
            subtitle=f"{NOISE_BLOCKS:,} records averaged, each divided by "
                     f"$(\\sum w)^2$: the lift is 10·log₁₀(ENBW)")

    # --- bottom: the two corrections, side by side --------------------------
    positions = np.arange(len(FAMILY_KEY))
    cg = [-stats[key]["cg_db"] for key in FAMILY_KEY]
    enbw = [stats[key]["enbw_db"] for key in FAMILY_KEY]
    ax_bars.bar(positions - 0.19, cg, width=0.36, color=P.NOTE, zorder=4,
                label="tone correction: $-20\\log_{10}(\\sum w/N)$")
    ax_bars.bar(positions + 0.19, enbw, width=0.36, color=P.OPTICAL, zorder=4,
                label="floor lift: $10\\log_{10}(\\mathrm{ENBW})$")
    for x, value in zip(positions - 0.19, cg):
        ax_bars.text(x, value + 0.12, f"{value:.2f}", color=P.NOTE_DARK,
                     fontsize=8.4, ha="center", va="bottom", zorder=9)
    for x, value in zip(positions + 0.19, enbw):
        ax_bars.text(x, value + 0.12, f"{value:.2f}", color=P.OPTICAL_DARK,
                     fontsize=8.4, ha="center", va="bottom", zorder=9)
    ax_bars.set_xticks(positions)
    ax_bars.set_xticklabels(FAMILY)
    ax_bars.set_xlim(-0.6, len(FAMILY_KEY) - 0.4)
    ax_bars.set_ylim(0.0, 10.6)
    P.tidy(ax_bars, ylabel="decibels, relative to rectangular",
           legend=["tone correction: $-20\\log_{10}(\\sum w/N)$",
                   "floor lift: $10\\log_{10}(\\mathrm{ENBW})$"],
           legend_loc="upper left")
    P.title(ax_bars, "The correction is not the error: 6.02 dB of amplitude buys 1.76 dB of floor",
            subtitle="a window costs a constant scale factor and a real change in "
                     "signal-to-noise, and only the second one is a trade")

    fig.text(0.030, 0.012,
             f"At the coherent receiver's working point — {FDE_N} points at "
             f"{FDE_FS / 1e9:.0f} GSa/s, {FDE_FS / FDE_N / 1e6:.0f} MHz per bin — one "
             f"bin of noise is\n{at_fde:.2f} dB below the "
             f"{OSNR_BAND_HZ / 1e9:.1f} GHz reference band with a rectangular "
             f"window and {at_fde_hann:.2f} dB below it with Hann: a difference of "
             f"{at_fde - at_fde_hann:.2f} dB in the reported OSNR.",
             color=P.MUTED, fontsize=7.9, ha="left", va="bottom", linespacing=1.5)

    print(f"[windows-noise-floor] {NOISE_BLOCKS} blocks of unit white noise, "
          f"RandomState({NOISE_SEED}); mean floor after the coherent-gain "
          f"correction, relative to rectangular:")
    for key, name in zip(FAMILY_KEY, FAMILY):
        print(f"[windows-noise-floor] {name:18s} coherent gain "
              f"{stats[key]['cg_db']:+7.2f} dB -> correction "
              f"{-stats[key]['cg_db']:5.2f} dB; ENBW {stats[key]['enbw']:.4f} bins, "
              f"floor lift {stats[key]['enbw_db']:5.2f} dB")
    for key, name in (("rect", "rectangular"), ("hann", "Hann"), ("bh4", "Blackman-Harris")):
        print(f"[windows-noise-floor] measured floor shift for {name}: "
              f"{floors[key] - reference:+.3f} dB against a predicted "
              f"{stats[key]['enbw_db']:+.3f} dB")
    print(f"[windows-noise-floor] {OSNR_BAND_HZ / 1e9:.1f} GHz reference band at "
          f"{FDE_FS / 1e9:.0f} GSa/s over {FDE_N} points: "
          f"{FDE_FS / FDE_N / 1e6:.0f} MHz per bin, so one bin of noise is "
          f"{at_fde:.2f} dB below the band with a rectangular window and "
          f"{at_fde_hann:.2f} dB below it with Hann — a difference of "
          f"{at_fde - at_fde_hann:.2f} dB in the reported OSNR")
    return P.render(fig)


# --------------------------------------------------------------------------- #
# 7. when the record is exactly one period
# --------------------------------------------------------------------------- #


def windows_periodic_record() -> str:
    """A record that is one period exactly: the rectangle is the correct window."""
    n = np.arange(N)
    bins = np.arange(0, 17)
    tone = np.cos(2.0 * np.pi * 8 * n / N)
    floor_db = -130.0

    fig, axes = P.figure(height=5.2, nrows=1, ncols=2, sharey=True)
    ax_rect, ax_hann = axes
    panels = (("rect", "rectangular: one exact line", P.WARN, ax_rect),
              ("hann", "Hann: three bins, half the height", P.ACCENT, ax_hann))

    measured = {}
    for key, heading, colour, ax in panels:
        w = _window(key)
        spectrum = np.abs(np.fft.fft(tone * w))[:N // 2 + 1]
        peak = float(spectrum[8])
        db = np.maximum(20.0 * np.log10(np.maximum(spectrum / peak, 1e-17)),
                        floor_db)
        measured[key] = {"peak": peak, "db": db,
                         "others": float(np.max(np.delete(spectrum, [7, 8, 9]))),
                         "amp": float(2.0 * peak / np.sum(w)),
                         "sum_w": float(np.sum(w))}
        # the bins that carry something are drawn as stems; the rest are one
        # row of dots at the computation's floor, where nothing is
        live = db[bins] > floor_db + 1.0
        ax.vlines(bins[live], floor_db, db[bins][live], color=colour, lw=1.4,
                  zorder=4)
        ax.plot(bins[live], db[bins][live], "o", ms=5.4, color=colour,
                mec=P.PANEL, mew=1.0, ls="none", zorder=6)
        ax.plot(bins[~live], db[bins][~live], "o", ms=3.6, color=P.RULE,
                mec=P.PANEL, mew=0.0, ls="none", zorder=5)
        ax.axhline(0.0, color=P.SOFT, lw=0.8, zorder=2)
        ax.set_xlim(-0.6, 16.6)
        ax.set_ylim(-140.0, 12.0)
        ax.set_yticks([0, -20, -40, -60, -80, -100, -120])
        ax.set_xticks([0, 4, 8, 12, 16])
        P.tidy(ax, xlabel="bin index  k")
        P.title(ax, heading)

    ax_rect.annotate(f"bin 8: {measured['rect']['peak']:.3f}\n"
                     f"= {N}/2, the whole tone",
                     xy=(8.0, 0.0), xytext=(9.4, -34.0), color=P.WARN,
                     fontsize=8.8, ha="left", va="center", zorder=9,
                     linespacing=1.3,
                     arrowprops=dict(arrowstyle="->", color=P.WARN,
                                     linewidth=1.0, shrinkA=2, shrinkB=5))
    ax_rect.text(0.2, -76.0,
                 "no seam, no skirt: the record is one\n"
                 "period of a periodic signal, so the\n"
                 "repetition is the signal itself",
                 color=P.MUTED, fontsize=8.6, ha="left", va="top",
                 linespacing=1.4, zorder=9)
    ax_rect.text(0.2, -136.0,
                 f"every other bin: {measured['rect']['others']:.1e}",
                 color=P.MUTED, fontsize=8.2, ha="left", va="bottom", zorder=9)
    ax_hann.annotate(f"bins 7 and 9: {measured['hann']['peak'] / 2:.3f} each,\n"
                     f"{20.0 * np.log10(0.5):.2f} dB down",
                     xy=(7.0, 20.0 * np.log10(0.5)), xytext=(9.4, -30.0),
                     color=P.ACCENT, fontsize=8.8, ha="left", va="center",
                     zorder=9, linespacing=1.3,
                     arrowprops=dict(arrowstyle="->", color=P.ACCENT,
                                     linewidth=1.0, shrinkA=2, shrinkB=5))
    ax_hann.text(0.2, -76.0,
                 f"$\\sum w$ = {measured['hann']['sum_w']:.0f} instead of "
                 f"{N}, so the peak\nis half and the correction is "
                 f"+{20.0 * np.log10(N / measured['hann']['sum_w']):.2f} dB; "
                 "what\nit cannot correct is the three-bin lobe",
                 color=P.MUTED, fontsize=8.6, ha="left", va="top",
                 linespacing=1.4, zorder=9)
    ax_hann.text(0.2, -136.0,
                 f"every other bin: {measured['hann']['others']:.1e}",
                 color=P.MUTED, fontsize=8.2, ha="left", va="bottom", zorder=9)
    P.tidy(ax_rect, ylabel="$|X[k]|$  (dB re the peak)")

    print(f"[windows-periodic-record] one period of a {8 * BIN:g} Hz tone in a "
          f"{1000.0 * N / FS:.1f} ms record: exactly bin 8, no seam")
    for key, name in (("rect", "rectangular"), ("hann", "Hann")):
        m = measured[key]
        print(f"[windows-periodic-record] {name:12s}: peak {m['peak']:.4f}, "
              f"largest other bin {m['others']:.2e}, sum(w) {m['sum_w']:.0f}, "
              f"amplitude after the correction {m['amp']:.4f}")
    print(f"[windows-periodic-record] Hann puts {measured['hann']['peak'] / 2:.3f} "
          f"in each neighbour, {20.0 * np.log10(0.5):.2f} dB down; the rectangular "
          f"window's neighbour is {measured['rect']['others']:.1e}")
    return P.render(fig)


FIGURES = {
    "windows-the-three": windows_the_three,
    "windows-kernels-db": windows_kernels_db,
    "windows-tradeoff": windows_tradeoff,
    "windows-off-bin": windows_off_bin,
    "windows-scalloping": windows_scalloping,
    "windows-noise-floor": windows_noise_floor,
    "windows-periodic-record": windows_periodic_record,
}
