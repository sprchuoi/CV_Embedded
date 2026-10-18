"""Computed figures for the Fourier series chapter.

Seven figures, in the order the article uses them:

    fourier-square-partial-sums     partial sums rebuilding a ±1 square, and the
                                    coefficient table they were rebuilt from
    fourier-coefficient-projection  three product curves and their signed areas
    fourier-symmetry-harmonics      three shapes, their stems, their coefficients
    fourier-truncated-edge          the edge at K = 9, 101, 1001: tr·B, overshoot
    fourier-periodic-extension      the record, its copies, the invented seam
    fourier-limit-to-transform      the same pulse train at T₀ = 1, 2, 4 s
    fourier-rect-sinc-pair          rect ↔ sinc: width, X(0), zeros, energy

Nothing here asserts a coefficient. Every number the chapter quotes is measured
from a sampled waveform on a stated grid, printed on the figure, and printed
again to stdout with the figure's name so a build log can be audited against the
page.

Measurement conventions, stated once and used throughout:

* **One period, sampled.** ``GRID`` samples of one period, ``t_j = j·T₀/N``,
  with the integral taken as the sampled sum ``Σ x_j·basis_j·Δt`` — the
  trapezoid every plotting script already has, and the reason a coefficient
  computed this way carries a floor rather than an exact zero at a jump.
* **The (2/T₀) convention, and the one exception.** For ``n ≥ 1``, ``a_n`` and
  ``b_n`` are the coefficients of ``x(t) = a₀ + Σ a_n cos(2πnt/T₀) +
  b_n sin(2πnt/T₀)``, each twice the mean product. The constant term ``a₀`` is
  the plain mean *level*: the ``n = 0`` case carries no factor of 2, so the
  table's ``a₀`` is the level and not the ``a₀`` of the ``a₀/2`` convention,
  which is twice it. ``c_n`` is the complex coefficient of the exponential
  series; the two are related by ``c_n = (a_n - j·b_n)/2``, which the last
  figure shows as the two-sided stem pair rather than stating.
* **A step of 2.** The square runs ±1, so its jump is 2 and its ringing is
  quoted both ways: percent of the jump of 2 and percent of the ±1 level. The
  two differ by a factor of two and the figure prints both, because the chapter
  turns on which one a reader means.

Every figure is deterministic: no randomness is used anywhere in this module, so
a figure does not depend on the order the module is built in.
"""

from __future__ import annotations

import numpy as np

from . import plotstyle as P

# --------------------------------------------------------------------------- #
# shared conventions
# --------------------------------------------------------------------------- #

T0 = 1.0                    # the period every waveform is built on, in seconds
GRID = 400_002              # samples per period: even, and not a multiple of 4

# figure 1: the partial sums and the table they come from
PARTIAL_KS = (1, 3, 9, 99)
TABLE_N = 9                 # coefficients printed in the table

# figure 2: the three projections, and the harmonic order each factor carries
PROJECTION_N = ((1, 1), (1, 3), (1, 3))   # fundamental × itself,
                                          # fundamental × 3rd, square × 3rd

# figure 3: symmetry
SYM_N = 8                   # harmonics drawn as stems
SYM_LISTED = 5              # the surviving coefficients written out, n = 0 … 5

# figure 4: the edge
EDGE_KS = (9, 101, 1001)
EDGE_SWEEP = (5, 7, 9, 15, 25, 51, 101, 201, 501, 1001)
EDGE_M = 1 << 18            # dense grid one partial sum is evaluated on
EDGE_WINDOW = 3.0           # plotted window, in units of 1/B either side
ONE_POLE = 0.350            # chapter 1's one-pole edge: 0.35/B, for contrast

# figure 5: the periodic extension
SEAM_TAU = 0.2              # decay constant of the record, seconds
SEAM_K = 101                # the series rebuilt at the seam
SEAM_INTERIOR = 0.15        # the record's middle, clear of both seams

# figure 6: the limit
PULSE_WIDTH = 0.25          # the rectangular pulse's width, seconds
PERIODS = (1.0, 2.0, 4.0)   # T₀, so the line spacing is 1/T₀
LIMIT_BAND = 6.0            # two-sided stem plot spans ±6 Hz

# figure 7: rect and sinc
RECT_WIDTHS = (0.25, 1.0, 2.0)
LIMIT_WIDTHS = (0.25, 0.10, 0.02)
ENERGY_BAND = 1.0e5         # Hz either side, wide enough to hold the tail


# --------------------------------------------------------------------------- #
# local helpers: sampling, coefficients, and the partial sum
# --------------------------------------------------------------------------- #


def _grid(n: int = GRID, t0: float = T0) -> tuple[np.ndarray, float]:
    """One period sampled at ``n`` points, and the sample spacing."""
    return np.linspace(0.0, t0, n, endpoint=False), t0 / n


def _square(t: np.ndarray, t0: float = T0) -> np.ndarray:
    """±1 square, +1 on the first half of the period, −1 on the second."""
    return np.where(np.mod(t, t0) < 0.5 * t0, 1.0, -1.0)


def _square_shifted(t: np.ndarray, t0: float = T0) -> np.ndarray:
    """The same square *advanced* by a quarter period: even about t = 0.

    ``_square(t + T₀/4)`` moves the +1 half-period back to [−T₀/4, T₀/4], so the
    shifted shape is +1 in the middle of a period and −1 at both ends, and its
    cosine coefficients come out +1.2732 and −0.4244. A delay instead,
    ``_square(t − T₀/4)``, would put +1 on [T₀/4, 3T₀/4] and flip both signs.
    """
    return np.where(np.mod(t + 0.25 * t0, t0) < 0.5 * t0, 1.0, -1.0)


def _rectified_sine(t: np.ndarray, t0: float = T0) -> np.ndarray:
    """|sin| of one period: every half cycle is the same, so it is half-wave."""
    return np.abs(np.sin(2.0 * np.pi * t / t0))


def _pulse_train(t: np.ndarray, t0: float, width: float = PULSE_WIDTH) -> np.ndarray:
    """A 1-high rectangular pulse of ``width`` seconds, repeated every ``t0``."""
    u = np.mod(t + 0.5 * t0, t0) - 0.5 * t0        # centred on t = 0
    return np.where(np.abs(u) < 0.5 * width, 1.0, 0.0)


def _coefficients(x: np.ndarray, dt: float,
                  n_max: int) -> tuple[np.ndarray, np.ndarray]:
    """``(a_n, b_n)`` for n = 0 … n_max, measured from the sampled waveform.

    The sum ``(2/T₀)·Σ x_j·cos(2πnj/N)·Δt`` is the real half of one FFT bin, so
    the whole table costs one transform instead of ``n_max`` loops — the same
    arithmetic, and it keeps the jump's floor visible in every coefficient.
    """
    n = x.size
    spectrum = np.fft.fft(x) / n
    a = 2.0 * spectrum.real[:n_max + 1]
    b = -2.0 * spectrum.imag[:n_max + 1]
    a[0] *= 0.5                       # a₀/2 is the mean, not twice the mean
    b[0] = 0.0
    return a, b


def _mean(x: np.ndarray, dt: float, t0: float = T0) -> float:
    """The signal's own average, which is the coefficient a₀/2."""
    return float(np.sum(x) * dt / t0)


def _partial_sum(t: np.ndarray, a: np.ndarray, b: np.ndarray, k: int,
                 t0: float = T0) -> np.ndarray:
    """``a₀ + Σ_{n=1..k} a_n cos + b_n sin`` evaluated on ``t``.

    ``a[0]`` is the mean level itself (see the module docstring's convention),
    so it enters the sum unscaled; the ``a₀/2`` form is the other bookkeeping.
    """
    out = np.full(np.shape(t), a[0])
    for n in range(1, k + 1):
        arg = 2.0 * np.pi * n * t / t0
        out = out + a[n] * np.cos(arg) + b[n] * np.sin(arg)
    return out


def _partial_square_dense(b: np.ndarray, k: int, m: int = EDGE_M
                          ) -> tuple[np.ndarray, np.ndarray]:
    """One partial sum of the square on a dense uniform grid, via the inverse FFT.

    ``S(t_j) = Σ_n c_n e^{j2πnj/m}`` is exactly an inverse transform of the
    truncated coefficient spectrum, so a 262144-point grid costs one ``ifft``
    rather than K multiplies per point. The result is returned rolled to
    ``t ∈ [−T₀/2, T₀/2)``, which puts the rising edge at the centre.
    """
    spectrum = np.zeros(m, dtype=complex)
    odd = np.arange(1, k + 1, 2)
    spectrum[odd] = -1j * b[odd] / 2.0        # c_n = (a_n − j·b_n)/2, a_n = 0 here
    spectrum[-odd] = 1j * b[odd] / 2.0
    values = np.fft.ifft(spectrum).real * float(m)   # ifft carries a 1/m
    values = np.roll(values, m // 2)
    t = (np.arange(m) - m // 2) * (T0 / m)
    return t, values


def _si(x: np.ndarray | float) -> np.ndarray | float:
    """The sine integral Si(x) = ∫₀ˣ sin(u)/u du, by the trapezoid on a fine grid.

    Used for the *ideal* band-limited step — the K → ∞ limit the truncated
    square converges on — so that the 0.446 the chapter quotes is computed here
    rather than copied from a table.
    """
    scalar = np.isscalar(x)
    targets = np.atleast_1d(np.asarray(x, dtype=float))
    limit = float(np.max(np.abs(targets))) if targets.size else 0.0
    u = np.linspace(0.0, max(limit, 1.0) * 1.000001, 400_001)
    integrand = np.ones_like(u)
    integrand[1:] = np.sin(u[1:]) / u[1:]
    cumulative = np.concatenate(([0.0], np.cumsum(0.5 * (integrand[1:] + integrand[:-1])
                                                  * np.diff(u))))
    # Si is odd, so one tabulation of |x| serves both signs
    out = np.sign(targets) * np.interp(np.abs(targets), u, cumulative)
    return float(out[0]) if scalar else out


def _ideal_step(x: np.ndarray) -> np.ndarray:
    """The band-limited step from −1 to +1, ``x`` measured in units of 1/B."""
    return (2.0 / np.pi) * _si(2.0 * np.pi * np.asarray(x, dtype=float))


def _crossing(x: np.ndarray, y: np.ndarray, level: float) -> float:
    """First ascending crossing of ``level``, linearly interpolated."""
    hits = np.where((y[:-1] < level) & (y[1:] >= level))[0]
    i = hits[0]
    return float(x[i] + (level - y[i]) * (x[i + 1] - x[i]) / (y[i + 1] - y[i]))


def _edge_measure(k: int, b: np.ndarray, span: float | None = None
                  ) -> tuple[float, float, float]:
    """``(tr·B, overshoot, first-peak position)`` for K = ``k`` harmonics.

    The time axis is in units of 1/B with B = K/T₀, so an edge that takes a
    transition time ``tr`` shows it as ``tr·B`` directly — the number the
    chapter compares against 0.446 and 0.350. The overshoot is the height of
    the first ringing peak above the top of the step of 2.
    """
    # one period spans k units of 1/B, so the window has to stay inside it
    if span is None:
        span = min(2.5, 0.45 * k)
    t, values = _partial_square_dense(b, k)
    x = t * (k / T0)
    window = np.abs(x) <= span
    xw, yw = x[window], values[window]
    order = np.argsort(xw)
    xw, yw = xw[order], yw[order]
    high = _crossing(xw, yw, 0.8)
    transition = high - _crossing(xw, yw, -0.8)
    after = xw > high                 # the rise is over; what follows is ringing
    peak = float(np.max(yw[after]))
    position = float(xw[after][int(np.argmax(yw[after]))])
    return transition, peak - 1.0, position


def _lobe_areas(p: np.ndarray, dt: float, t0: float = T0,
                zeros: np.ndarray | None = None
                ) -> tuple[list[float], list[float]]:
    """Signed areas of the lobes of a sampled product, split at its zeros.

    Used to show *why* an orthogonal product's signed area is zero: the lobes
    are not equal, and the sample values do not cancel pairwise, but the
    positive lobes sum to exactly the negative ones. A lobe is the interval
    between two neighbouring zeros, so ``zeros`` — the times where either
    factor vanishes — is what splits a tangency (a zero without a change of
    sign) into the two lobes it bounds. Without ``zeros`` the split falls back
    to the sign changes of the samples, which merges a tangency.
    """
    if zeros is not None:
        index = np.round(np.asarray(zeros, dtype=float) / dt).astype(int)
        breaks = np.unique(np.clip(index, 0, p.size - 1))
    else:
        breaks = np.where(np.diff(np.sign(p)) != 0.0)[0] + 1
    edges = np.unique(np.concatenate(([0], breaks, [p.size])))
    positive, negative = [], []
    for start, stop in zip(edges[:-1], edges[1:]):
        area = float(np.sum(p[start:stop]) * dt / t0)
        # the zero at t = T₀ is the same boundary as the zero at 0, so the last
        # interval can be a single sample wide; a lobe of no width is not a lobe
        if area > 1.0e-9:
            positive.append(area)
        elif area < -1.0e-9:
            negative.append(area)
    return positive, negative


def _thin(x: np.ndarray, y: np.ndarray, limit: int = 4001
          ) -> tuple[np.ndarray, np.ndarray]:
    """Decimate a dense measurement grid down to something an SVG can hold.

    The measurement is never thinned — only the plot is. A 262144-point partial
    sum is right for finding a crossing to four decimals and wrong for a path
    element, so the figure draws every sixtieth sample of it.
    """
    if x.size <= limit:
        return x, y
    step = int(np.ceil(x.size / limit))
    return x[::step], y[::step]


def _num(value: float, width: int = 10) -> str:
    """A coefficient in a fixed-width column: decimals, or a floor in scientific."""
    if value == 0.0:
        return f"{0.0:>{width}.6f}"
    if abs(value) < 1.0e-3:
        return f"{value:>{width}.1e}"
    return f"{value:>{width}.6f}"


def _sci(value: float, digits: int = 2) -> str:
    """Mathtext scientific notation, for an axis-side annotation."""
    exponent = int(np.floor(np.log10(abs(value))))
    mantissa = value / 10.0 ** exponent
    return f"${mantissa:.{digits}f}\\times10^{{{exponent}}}$"


def _footnote(ax, x: float, y: float, text: str, *, colour: str = P.INK,
              size: float = 8.6, ha: str = "left", va: str = "top") -> None:
    """A round-cornered note inside the axes, the way every figure here does it."""
    ax.text(x, y, text, color=colour, fontsize=size, ha=ha, va=va, zorder=7,
            bbox=dict(boxstyle="round,pad=0.42", facecolor=P.PANEL,
                      edgecolor=P.RULE_SOFT, linewidth=1.0))


# --------------------------------------------------------------------------- #
# 1. a square wave is a sum of sines
# --------------------------------------------------------------------------- #


def fourier_square_partial_sums() -> str:
    """The ±1 square against four partial sums, with the table they came from."""
    t, dt = _grid()
    x = _square(t)
    a, b = _coefficients(x, dt, max(PARTIAL_KS))     # the table prints the first

    # the time-domain mean square, computed from the summed waveform itself
    total = float(np.sum(x * x) * dt / T0)
    carried = {}
    for k in PARTIAL_KS:
        summed = _partial_sum(t, a, b, k)
        carried[k] = float(np.sum(summed * summed) * dt / T0)

    # two periods, so a partial sum's periodicity is visible as well as its shape
    tp = np.linspace(0.0, 2.0 * T0, 4001)
    ideal = _square(tp)

    fig, axes = P.figure(height=9.4, nrows=3, hspace=0.55,
                         height_ratios=[1.0, 1.0, 1.45])
    ax1, ax2, ax3 = axes

    # --- top: the first two terms -------------------------------------------
    ax1.plot(tp, ideal, color=P.RULE, lw=3.4, zorder=1,
             label="the square: ±1, period $T_0$")
    ax1.plot(tp, _partial_sum(tp, a, b, 1), color=P.WARN, lw=1.9, zorder=4,
             label="K = 1")
    ax1.plot(tp, _partial_sum(tp, a, b, 3), color=P.NOTE, lw=1.7, zorder=5,
             label="K = 3")
    ax1.text(0.04, 1.60, "K = 1: one sine — round, and a quarter period late",
             color=P.WARN, fontsize=8.8, ha="left", va="center")
    ax1.text(0.04, -1.60, "K = 3: the third harmonic carves the corners, and "
                          "adds a wobble", color=P.NOTE, fontsize=8.8,
             ha="left", va="center")
    ax1.set_xlim(-0.05, 2.05)
    ax1.set_ylim(-1.85, 1.85)
    ax1.set_yticks([-1, 0, 1])
    ax1.set_xticks([0, 0.5, 1, 1.5, 2])
    ax1.set_xticklabels(["0", "$T_0/2$", "$T_0$", "$3T_0/2$", "$2T_0$"])
    P.tidy(ax1, ylabel="value", legend=["the square: ±1, period $T_0$",
                                       "K = 1", "K = 3"],
           legend_loc="upper right", ncol=1)
    P.title(ax1, "Stop the series after K harmonics and the square is still a sum",
            subtitle=f"{GRID:,} samples of one period, coefficients integrated "
                     "from the sampled waveform — not from 4/nπ")

    # --- middle: nearly there ------------------------------------------------
    ax2.plot(tp, ideal, color=P.RULE, lw=3.4, zorder=1)
    ax2.plot(tp, _partial_sum(tp, a, b, 9), color=P.ACCENT, lw=1.6, zorder=4,
             label="K = 9")
    ax2.plot(tp, _partial_sum(tp, a, b, 99), color=P.OPTICAL, lw=1.3, zorder=5,
             label="K = 99")
    ax2.annotate("K = 99 is the square to the eye;\nthe overshoot at each jump "
                 "is not shrinking",
                 xy=(1.5, 1.09), xytext=(1.28, -1.56), color=P.OPTICAL,
                 fontsize=8.8, ha="left", va="center", zorder=7,
                 arrowprops=dict(arrowstyle="->", color=P.OPTICAL, linewidth=1.1,
                                 shrinkA=2, shrinkB=2))
    ax2.set_xlim(-0.05, 2.05)
    ax2.set_ylim(-1.95, 2.35)
    ax2.set_yticks([-1, 0, 1])
    ax2.set_xticks([0, 0.5, 1, 1.5, 2])
    ax2.set_xticklabels(["0", "$T_0/2$", "$T_0$", "$3T_0/2$", "$2T_0$"])
    P.tidy(ax2, ylabel="value", legend=["K = 9", "K = 99"],
           legend_loc="upper left", ncol=1)
    P.title(ax2, "The same sum, stopping at K = 9 and at K = 99",
            subtitle="the two periods are the point: every term has period "
                     "$T_0$ or a submultiple of it — and the ringing at each "
                     "jump does not shrink")

    # --- bottom: the table, and the power it carries -------------------------
    ax3.axis("off")
    # the header carries subscript n as one monospace character (DejaVu Sans
    # Mono has U+2099), so the columns stay aligned and the label is not a
    # literal underscore
    rows = [f"{'n':>3s}   {'a\u2099':<10s}   {'b\u2099':<10s}"]
    for n in range(TABLE_N + 1):
        rows.append(f"{n:3d}   {_num(a[n])}   {_num(b[n])}")
    ax3.text(0.010, 0.97, "\n".join(rows), transform=ax3.transAxes,
             family="monospace", fontsize=9.2, color=P.INK, ha="left", va="top",
             linespacing=1.22)

    power = [f"{'partial sum':>13s}  {'mean square':>11s}  {'of 1.0000':>9s}"]
    for k in PARTIAL_KS:
        power.append(f"{'K = ' + str(k):>13s}  {carried[k]:>11.4f}  "
                     f"{100.0 * carried[k] / total:>8.2f}%")
    ax3.text(0.415, 0.97, "\n".join(power), transform=ax3.transAxes,
             family="monospace", fontsize=9.0, color=P.NOTE, ha="left", va="top",
             linespacing=1.28)
    ax3.text(0.415, 0.56,
             "the square's own $\\langle x^2\\rangle$ = 1.0000 on these same "
             "samples.\n"
             "The column above is the mean square of the summed\n"
             "waveform, not a sum of coefficients, and the two\n"
             "agree — so the missing 4% at K = 9 is the ringing at\n"
             "the edge, not an error in the series.\n"
             "\n"
             "Every even coefficient is exactly zero. Every odd\n"
             "$a_n$ is at the grid's floor: two jumps, each leaving\n"
             "one sample unpaired, give $4/N$ = "
             f"{4.0 / GRID:.1e} on $N$ = {GRID:,} samples.",
             transform=ax3.transAxes, fontsize=9.0, color=P.MUTED,
             ha="left", va="top", linespacing=1.34)

    print(f"[fourier-square-partial-sums] grid {GRID:,} samples/period; "
          "coefficients a_n, b_n of x(t) = a0 + Σ a_n cos + b_n sin, a0 the "
          "mean level (no factor 2):")
    for n in range(TABLE_N + 1):
        print(f"[fourier-square-partial-sums]   n = {n}:  a = {a[n]:+.4e}   "
              f"b = {b[n]:+.6f}")
    print(f"[fourier-square-partial-sums] square mean square = {total:.4f}")
    for k in PARTIAL_KS:
        print(f"[fourier-square-partial-sums]   K = {k:3d}: mean square "
              f"{carried[k]:.4f} = {100.0 * carried[k] / total:.2f}% of it")
    return P.render(fig)


# --------------------------------------------------------------------------- #
# 2. what each coefficient measures
# --------------------------------------------------------------------------- #


def fourier_coefficient_projection() -> str:
    """Three products, three signed areas, and the divisor read off the first."""
    t, dt = _grid()
    square = _square(t)
    fundamental = np.sin(2.0 * np.pi * t / T0)
    third = np.sin(2.0 * np.pi * 3.0 * t / T0)

    # the drawing grid: 3001 points for the path, 400002 for the integral
    tp = np.linspace(0.0, T0, 1601)
    drawn = (
        (np.sin(2.0 * np.pi * tp / T0), np.sin(2.0 * np.pi * tp / T0)),
        (np.sin(2.0 * np.pi * tp / T0), np.sin(2.0 * np.pi * 3.0 * tp / T0)),
        (_square(tp), np.sin(2.0 * np.pi * 3.0 * tp / T0)),
    )

    # the harmonic order each factor carries, so the lobe boundaries can be
    # taken from the zeros of either factor rather than from the sign changes
    # of the samples: the second product touches zero at t = T₀/2 without
    # crossing it, and a sign-change split would merge the two lobes there.
    products = (
        (fundamental, fundamental, PROJECTION_N[0], "fundamental × fundamental",
         "the product is a sine squared: positive everywhere,\n"
         "so nothing cancels"),
        (fundamental, third, PROJECTION_N[1], "fundamental × third harmonic",
         "the lobes change sign, and the signed area is zero"),
        (square, third, PROJECTION_N[2], "square × third harmonic",
         "the square is mostly −1 where the\n"
         "third harmonic is negative"),
    )
    areas = [float(np.sum(p * q) * dt / T0) for p, q, _, _, _ in products]
    divisor = 0.5 * T0

    # every panel's lobes, counted and measured: the point of the second is
    # that they are unequal, so the exact zero is a cancellation of totals
    # rather than of equal lobes; the point of the third is the opposite, that
    # six equal lobes leave a residue because of their count alone.
    lobes = []
    for p, q, (n_p, n_q), _, _ in products:
        zeros = np.unique(np.concatenate((
            np.arange(0, 2 * n_p + 1) / (2.0 * n_p),
            np.arange(0, 2 * n_q + 1) / (2.0 * n_q),
        )))
        lobes.append(_lobe_areas(p * q, dt, zeros=zeros))
    positive_lobes, negative_lobes = lobes[1]

    fig, axes = P.figure(height=7.6, nrows=3, hspace=0.66,
                         height_ratios=[1.0, 1.0, 1.05])
    for row, (ax, (p, q, _, name, note)) in enumerate(zip(axes, products)):
        ps, qs = drawn[row]
        ax.axhline(0.0, color=P.SOFT, lw=1.0, zorder=2)
        ax.fill_between(tp, 0.0, ps * qs, where=(ps * qs) >= 0.0, color=P.ACCENT,
                        alpha=0.30, linewidth=0.0, zorder=1)
        ax.fill_between(tp, 0.0, ps * qs, where=(ps * qs) < 0.0, color=P.WARN,
                        alpha=0.34, linewidth=0.0, zorder=1)
        ax.plot(tp, ps * qs, color=P.INK, lw=1.3, zorder=4)
        ax.plot(tp, qs, color=P.NOTE, lw=1.0, ls=(0, (4, 3)), zorder=3)
        ax.plot(tp, ps, color=P.RULE, lw=2.6, zorder=2)
        ax.set_xlim(0.0, 1.0)
        # the headroom keeps every annotation clear of both humps: the product
        # never leaves ±1, so everything above 1.05 is free on all three panels
        ax.set_ylim(-1.50, 2.55)
        ax.set_xticks([0, 0.25, 0.5, 0.75, 1.0])
        ax.set_xticklabels(["0", "$T_0/4$", "$T_0/2$", "$3T_0/4$", "$T_0$"])

        area = areas[row]
        positives, negatives = lobes[row]
        if row == 0:
            reading = (f"$\\frac{{1}}{{T_0}}\\int$ product $dt$ = {area:.4f}\n"
                       f"{len(positives)} humps of {positives[0]:.4f}: "
                       "the reference")
            colour = P.ACCENT
        elif row == 1:
            reading = (f"$\\frac{{1}}{{T_0}}\\int$ product $dt$ = {area:+.1e}\n"
                       f"{len(positive_lobes)} positive lobes of "
                       f"{np.mean(positive_lobes):.4f},\n"
                       f"{len(negative_lobes)} negative of "
                       f"{np.mean(negative_lobes):.4f}: totals cancel")
            colour = P.MUTED
        else:
            coefficient = area / divisor
            reading = (f"$\\frac{{1}}{{T_0}}\\int$ product $dt$ = {area:.4f}\n"
                       f"divide by the reference {divisor:.4f}: "
                       f"$b_3$ = {coefficient:+.4f}\n"
                       f"{len(positives)} positive lobes, "
                       f"{len(negatives)} negative, each "
                       f"{positives[0]:.4f}")
            colour = P.NOTE
        ax.text(0.985, 0.945, reading, transform=ax.transAxes, fontsize=9.8,
                color=colour, ha="right", va="top", zorder=7, linespacing=1.45,
                bbox=dict(boxstyle="round,pad=0.34", facecolor=P.PANEL,
                          edgecolor=P.RULE_SOFT, linewidth=1.0))
        if row == 0:
            # the name is not in the title on the first panel, so it goes here,
            # and the note goes along the floor where nothing is drawn
            ax.text(0.015, 0.985, name, transform=ax.transAxes, fontsize=10.0,
                    color=P.INK, ha="left", va="top", zorder=7)
            ax.text(0.015, 0.035, note, transform=ax.transAxes, fontsize=9.4,
                    color=P.MUTED, ha="left", va="bottom", zorder=7,
                    linespacing=1.35)
        else:
            ax.text(0.015, 0.985, note, transform=ax.transAxes, fontsize=9.4,
                    color=P.MUTED, ha="left", va="top", zorder=7,
                    linespacing=1.35)
        P.tidy(ax, ylabel="product")
        if row == 0:
            P.title(ax, "A coefficient is an average of the signal against "
                        "one harmonic",
                    subtitle="the shaded area is the integral; the dashed curve "
                             "is the harmonic; the thick grey curve is the signal")
        else:
            P.title(ax, name)
        if row == 2:
            P.tidy(ax, xlabel="time, one period — every shaded lobe is a "
                              "region where the product has one sign")

    print(f"[fourier-coefficient-projection] (1/T0)·∫ f·g dt over one period, "
          f"{GRID:,} samples:")
    for (_, _, _, name, _), area in zip(products, areas):
        print(f"[fourier-coefficient-projection]   {name}: signed area "
              f"{area:+.6e}")
    print("[fourier-coefficient-projection]   the multiplier is 2/T0 = "
          f"{2.0 / T0:.1f} per second; the divisor is T0/2 = {divisor:.1f} s; "
          f"area/(T0/2) = b_3 {areas[2] / divisor:+.6f}, "
          f"fundamental against itself {areas[0] / divisor:+.6f}")
    for (_, _, _, name, _), (positives, negatives) in zip(products, lobes):
        print(f"[fourier-coefficient-projection]   {name} lobes: "
              f"{[f'{v:+.6f}' for v in positives]} positive, "
              f"{[f'{v:+.6f}' for v in negatives]} negative")
    return P.render(fig)


# --------------------------------------------------------------------------- #
# 3. symmetry decides which harmonics survive
# --------------------------------------------------------------------------- #


def fourier_symmetry_harmonics() -> str:
    """Three shapes, three symmetry classes, and the coefficients each allows."""
    t, dt = _grid()
    # exactly one period, centred on t = 0: the window the prose describes, and
    # the one the parity of each shape is read off. Half-open, so the far end is
    # not sampled twice and the right edge is not a second jump.
    low, high = -0.5 * T0, 0.5 * T0
    tt = np.linspace(low, high, 4001, endpoint=False)
    shapes = (
        (_square(t), _square(tt), "odd square", "odd: $x(-t) = -x(t)$",
         P.NOTE, (-2.75, 1.45)),
        (_square_shifted(t), _square_shifted(tt), "quarter-shifted square",
         "even: $x(-t) = x(t)$", P.ACCENT, (-2.75, 1.45)),
        (_rectified_sine(t), _rectified_sine(tt), "full-wave rectified sine",
         "$x(t + T_0/2) = +x(t)$: the period is really half of it",
         P.OPTICAL, (-1.55, 1.45)),
    )

    fig, axes = P.figure(height=9.4, nrows=3, ncols=2, hspace=0.62)
    # the left column carries the written coefficients, so it gets the width
    axes[0, 0].get_gridspec().set_width_ratios([1.45, 1.0])
    fig.subplots_adjust(wspace=0.26)
    measured = []
    for row, (x, wave, name, symmetry, colour, limits) in enumerate(shapes):
        a, b = _coefficients(x, dt, SYM_N)
        measured.append((a, b))
        ax_time, ax_stem = axes[row]

        # --- left: the drawing that decides ---------------------------------
        ax_time.plot(tt, wave, color=colour, lw=2.0)
        ax_time.axhline(0.0, color=P.RULE, lw=1.0, zorder=0)
        ax_time.axvline(0.0, color=P.SOFT, lw=0.9, ls=(0, (1.0, 3.0)), zorder=0)
        ax_time.set_xlim(low, high)
        ax_time.set_xticks([low, 0.0, high])
        ax_time.set_xticklabels(["$-T_0/2$", "0", "$T_0/2$"])

        # the coefficients that survive, n = 0 … SYM_LISTED, written out at a
        # size that survives the page's column: this listing is the panel's
        # evidence, so it is type, not a monospace grid the width cannot hold
        listed = [f"${symbol}_{n}$ {value:+.4f}".replace("-", "\u2212")
                  for n in range(SYM_LISTED + 1)
                  for symbol, value in (("a", a[n]), ("b", b[n]))
                  if abs(value) >= 1.0e-4]
        if name == "odd square":
            floor = (f"every $a_n$ and even $b_n$ ≤ "
                     f"{max(abs(a[k]) for k in range(1, SYM_N + 1)):.1e}")
        elif name == "quarter-shifted square":
            floor = (f"every $b_n$ ≤ "
                     f"{max(abs(b[k]) for k in range(1, SYM_N + 1)):.1e}")
        else:
            floor = (f"every odd $a_n$ ≤ "
                     f"{max(abs(a[k]) for k in (1, 3, 5, 7)):.1e}")
        ax_time.text(0.012, 0.035, "   ".join(listed) + "\n" + floor,
                     transform=ax_time.transAxes, fontsize=10.6, color=P.INK,
                     ha="left", va="bottom", linespacing=1.55, zorder=7)
        ax_time.set_ylim(*limits)
        ax_time.set_yticks([0, 1] if name == "full-wave rectified sine"
                           else [-1, 0, 1])
        P.tidy(ax_time, ylabel="value")
        P.title(ax_time, name, subtitle=symmetry)

        # --- right: the stems the drawing predicts --------------------------
        n = np.arange(0, SYM_N + 1)
        ax_stem.axhline(0.0, color=P.SOFT, lw=1.0, zorder=1)
        ax_stem.vlines(n - 0.09, 0.0, a, color=P.NOTE, lw=1.6, zorder=3)
        ax_stem.plot(n - 0.09, a, "o", ms=4.4, color=P.NOTE, mec=P.PANEL,
                     mew=0.8, ls="none", zorder=4)
        ax_stem.vlines(n + 0.09, 0.0, b, color=P.ACCENT, lw=1.6, zorder=3)
        ax_stem.plot(n + 0.09, b, "s", ms=4.0, color=P.ACCENT, mec=P.PANEL,
                     mew=0.8, ls="none", zorder=4)
        ax_stem.plot([], [], "o", ms=4.4, color=P.NOTE, ls="none",
                     label="$a_n$ (cosine)")
        ax_stem.plot([], [], "s", ms=4.0, color=P.ACCENT, ls="none",
                     label="$b_n$ (sine)")
        ax_stem.set_xlim(-0.6, SYM_N + 0.6)
        ax_stem.set_ylim(-1.55, 1.55)
        ax_stem.set_xticks(n)
        P.tidy(ax_stem, ylabel="coefficient",
               legend=["$a_n$ (cosine)", "$b_n$ (sine)"],
               legend_loc="lower right", ncol=2)
        P.title(ax_stem, "The stems the drawing promises",
                subtitle=f"n = 0 … {SYM_N}; $a_0$ is the mean level")

    print("[fourier-symmetry-harmonics] three shapes, n = 0 … "
          f"{SYM_N}, (2/T0) convention:")
    for (_, _, name, _, _, _), (a, b) in zip(shapes, measured):
        odd = [int(n) for n in range(1, SYM_N + 1, 2)]
        even = [int(n) for n in range(2, SYM_N + 1, 2)]
        print(f"[fourier-symmetry-harmonics]   {name}: a = "
              f"{[f'{v:+.2e}' for v in a]}")
        print(f"[fourier-symmetry-harmonics]   {name}: b = "
              f"{[f'{v:+.2e}' for v in b]}")
        print(f"[fourier-symmetry-harmonics]     odd harmonics a: "
              f"max |a| = {max(abs(a[n]) for n in odd):.2e};  even b: "
              f"max |b| = {max(abs(b[n]) for n in even):.2e}")
    return P.render(fig)


# --------------------------------------------------------------------------- #
# 4. what truncation does to an edge
# --------------------------------------------------------------------------- #


def fourier_truncated_edge() -> str:
    """The zoomed edge, the transition time, and the overshoot that never leaves."""
    t, dt = _grid()
    a, b = _coefficients(_square(t), dt, max(EDGE_KS))

    edges = {k: _edge_measure(k, b) for k in EDGE_KS}

    # the ideal band-limited step: measured here, not quoted
    grid = np.linspace(-4.0, 4.0, 200_001)
    ideal = _ideal_step(grid)
    ideal_high = _crossing(grid, ideal, 0.8)
    ideal_transition = ideal_high - _crossing(grid, ideal, -0.8)
    ideal_after = grid > ideal_high
    ideal_overshoot = float(np.max(ideal[ideal_after])) - 1.0
    ideal_position = float(grid[ideal_after][int(np.argmax(ideal[ideal_after]))])

    sweep = {k: _edge_measure(k, b) for k in EDGE_SWEEP}
    ks = np.array(EDGE_SWEEP)
    colours = dict(zip(EDGE_KS, (P.WARN, P.ACCENT, P.OPTICAL)))

    fig, axes = P.figure(height=8.6, nrows=3, hspace=0.72,
                         height_ratios=[1.15, 1.0, 1.0])
    ax_edge, ax_tr, ax_over = axes

    # --- top: the three edges, on one axis of 1/B ---------------------------
    for k in EDGE_KS:
        t_k, values = _partial_square_dense(b, k)
        x_k = t_k * (k / T0)
        window = np.abs(x_k) <= EDGE_WINDOW
        xs, ys = _thin(x_k[window], values[window])
        ax_edge.plot(xs, ys, color=colours[k], lw=1.6, zorder=4)
    ax_edge.axhline(1.0, color=P.RULE, lw=1.0, ls=(0, (4, 3)), zorder=1)
    ax_edge.axhline(-1.0, color=P.RULE, lw=1.0, ls=(0, (4, 3)), zorder=1)
    ax_edge.axhline(0.0, color=P.SOFT, lw=1.0, zorder=1)
    ax_edge.axvline(0.0, color=P.SOFT, lw=1.0, zorder=1)
    # the three peaks are within 0.002 of each other, so one leader serves all
    # three markers and no leader crosses the curves
    for k in EDGE_KS:
        transition, overshoot, position = edges[k]
        ax_edge.plot([position], [1.0 + overshoot], "o", ms=5.0, color=colours[k],
                     mec=P.PANEL, mew=1.0, zorder=6)
    peak_k = EDGE_KS[1]
    ax_edge.annotate(
        f"the first ringing peak: {100.0 * edges[EDGE_KS[0]][1] / 2.0:.2f}% of "
        f"the jump\nat K = {EDGE_KS[0]}, "
        f"{100.0 * edges[peak_k][1] / 2.0:.2f}% from K = {peak_k} on",
        xy=(edges[EDGE_KS[0]][2], 1.0 + edges[EDGE_KS[0]][1]),
        xytext=(0.72, 2.02), color=P.INK, fontsize=9.0, ha="left", va="top",
        zorder=7, linespacing=1.35,
        arrowprops=dict(arrowstyle="->", color=P.MUTED, linewidth=1.0,
                        shrinkA=2, shrinkB=3))

    # the 10-90% measurement drawn, not just quoted: the two levels, the two
    # crossings on the K = 9 edge, and the bracket between them. _crossing is
    # the same routine the printed t_r comes from, so the marks and the number
    # cannot drift apart.
    t9, v9 = _partial_square_dense(b, EDGE_KS[0])
    x9 = t9 * (EDGE_KS[0] / T0)
    inside = np.abs(x9) <= 2.5
    x9, y9 = x9[inside], v9[inside]
    order = np.argsort(x9)
    x9, y9 = x9[order], y9[order]
    ten, ninety = _crossing(x9, y9, -0.8), _crossing(x9, y9, 0.8)
    level_left, level_right = ten - 0.30, ninety + 0.55
    for level, mark in ((-0.8, ten), (0.8, ninety)):
        ax_edge.plot([level_left, level_right], [level, level], color=P.WARN,
                     lw=0.9, ls=(0, (1.4, 2.6)), zorder=5)
        ax_edge.plot([mark], [level], "o", ms=6.0, mfc=P.PANEL, mec=P.WARN,
                     mew=1.4, zorder=7)
    ax_edge.annotate("", xy=(ten, 0.8), xytext=(ten, -0.8),
                     arrowprops=dict(arrowstyle="<->", color=P.WARN,
                                     linewidth=1.2, shrinkA=0, shrinkB=0),
                     zorder=7)
    ax_edge.text(ten - 0.10, 0.0,
                 "$t_r\\cdot B$\n= " f"{edges[EDGE_KS[0]][0]:.4f}",
                 color=P.WARN, fontsize=9.2, ha="right", va="center", zorder=7,
                 linespacing=1.3)
    ax_edge.text(-EDGE_WINDOW + 0.10, -1.20,
                 "the 10% and 90% levels of the jump, and the two crossings they "
                 "cut on the\nK = 9 edge: $t_r$ is the gap between them, and it "
                 "is what the middle panel plots",
                 color=P.MUTED, fontsize=9.0, ha="left", va="top", zorder=7,
                 linespacing=1.45)
    ax_edge.set_xlim(-EDGE_WINDOW, EDGE_WINDOW)
    ax_edge.set_ylim(-1.95, 2.15)
    ax_edge.set_yticks([-1, 0, 1])
    P.tidy(ax_edge, ylabel="value")
    P.title(ax_edge, "The same edge, three bandwidths — time measured in 1/B",
            subtitle="$B = K/T_0$; a curve taking $t_r$ seconds shows it as "
                     "$t_r\\cdot B$ directly. The three colours are the three "
                     "curves in both panels below.")

    # --- middle: the transition time, as a product --------------------------
    transitions = np.array([sweep[k][0] for k in EDGE_SWEEP])
    ax_tr.plot(ks, transitions, color=P.MUTED, marker="o", ms=4.0,
               mec=P.PANEL, mew=0.8, zorder=4)
    ax_tr.axhline(ideal_transition, color=P.NOTE, lw=1.4, ls=(0, (5, 3)),
                  zorder=3)
    ax_tr.text(1.06, ideal_transition + 0.004,
               f"ideal band-limited step: {ideal_transition:.4f}",
               color=P.NOTE, fontsize=9.2, ha="left", va="bottom")
    ax_tr.axhline(ONE_POLE, color=P.WARN, lw=1.4, ls=(0, (1.5, 2.5)), zorder=3)
    ax_tr.text(1250.0, ONE_POLE + 0.006,
               f"the first chapter's one-pole edge: {ONE_POLE:.3f}",
               color=P.WARN, fontsize=9.2, ha="right", va="bottom")
    for k in EDGE_KS:
        ax_tr.plot([k], [edges[k][0]], "o", ms=7.0, color=colours[k],
                   mec=P.PANEL, mew=1.1, zorder=6)
    ax_tr.set_xscale("log")
    ax_tr.set_xlim(0.9, 1400.0)
    ax_tr.set_ylim(0.34, 0.48)
    ax_tr.set_xticks([1, 3, 9, 25, 101, 501, 1001])
    ax_tr.set_xticklabels(["1", "3", "9", "25", "101", "501", "1001"])
    P.tidy(ax_tr, xlabel="harmonics kept, K  (the bandwidth is $B = K/T_0$)",
           ylabel="$t_r\\cdot B$")
    P.title(ax_tr, "Truncation buys a slope: the product settles on 0.446",
            subtitle="0.350 is a one-pole edge and 0.446 is a ringing one: the "
                     "same $1/B$ law, a different constant")

    # --- bottom: the overshoot, and the table -------------------------------
    overshoots = np.array([100.0 * sweep[k][1] / 2.0 for k in EDGE_SWEEP])
    ax_over.plot(ks, overshoots, color=P.MUTED, marker="o", ms=4.0,
                 mec=P.PANEL, mew=0.8, zorder=4)
    for k in EDGE_KS:
        ax_over.plot([k], [100.0 * edges[k][1] / 2.0], "o", ms=7.0,
                     color=colours[k], mec=P.PANEL, mew=1.1, zorder=6)
    ax_over.axhline(100.0 * ideal_overshoot / 2.0, color=P.NOTE, lw=1.4,
                    ls=(0, (5, 3)), zorder=3)
    ax_over.text(1.06, 8.862,
                 f"the ideal step: {100.0 * ideal_overshoot / 2.0:.3f}% of the "
                 "jump of 2", color=P.NOTE, fontsize=9.2, ha="left", va="bottom")
    ax_over.set_xscale("log")
    ax_over.set_xlim(0.9, 1400.0)
    ax_over.set_ylim(8.84, 9.55)
    ax_over.set_xticks([1, 3, 9, 25, 101, 501, 1001])
    ax_over.set_xticklabels(["1", "3", "9", "25", "101", "501", "1001"])
    rows = [f"{'K':>5s}  {'tr·B':>7s}  {'overshoot':>10s}  {'of ±1':>7s}  "
            f"{'peak at':>8s}"]
    for k in EDGE_KS:
        transition, overshoot, position = edges[k]
        rows.append(f"{k:5d}  {transition:>7.4f}  {100.0 * overshoot / 2.0:>9.3f}%  "
                    f"{100.0 * overshoot:>6.2f}%  {position:>8.4f}")
    rows.append(f"{'ideal':>5s}  {ideal_transition:>7.4f}  "
                f"{100.0 * ideal_overshoot / 2.0:>9.3f}%  "
                f"{100.0 * ideal_overshoot:>6.2f}%  {ideal_position:>8.4f}")
    ax_over.text(1330.0, 9.50, "\n".join(rows), family="monospace", fontsize=8.8,
                 color=P.INK, ha="right", va="top", linespacing=1.30,
                 bbox=dict(boxstyle="round,pad=0.42", facecolor=P.PANEL,
                           edgecolor=P.RULE_SOFT, linewidth=1.0), zorder=8)
    P.tidy(ax_over, xlabel="harmonics kept, K  (a log axis, so K = 1 has no "
                           "point: there is no edge to measure)",
           ylabel="overshoot, % of the jump of 2")
    P.title(ax_over, "The overshoot does not shrink: it tends to "
                     f"{100.0 * ideal_overshoot / 2.0:.2f}% of the jump of 2",
            subtitle=f"{100.0 * edges[EDGE_KS[0]][1] / 2.0:.2f}% at "
                     f"K = {EDGE_KS[0]}, {100.0 * ideal_overshoot / 2.0:.2f}% "
                     f"from K = {EDGE_KS[1]} on; 'peak at' is the first "
                     "maximum's position in units of 1/B, i.e. $T_0/2K$ from "
                     "the jump")

    print(f"[fourier-truncated-edge] B = K/T0, edge measured on a {EDGE_M:,}-"
          "point partial sum, 10-90% crossings interpolated:")
    for k in EDGE_KS:
        transition, overshoot, position = edges[k]
        print(f"[fourier-truncated-edge]   K = {k:4d}: tr*B = {transition:.4f}, "
              f"overshoot {100.0 * overshoot / 2.0:.3f}% of the step of 2 = "
              f"{100.0 * overshoot:.3f}% of the +/-1 level, first peak at "
              f"{position:.4f}/B")
    print(f"[fourier-truncated-edge]   ideal band-limited step: tr*B = "
          f"{ideal_transition:.4f}, overshoot "
          f"{100.0 * ideal_overshoot / 2.0:.3f}% of the step of 2 = "
          f"{100.0 * ideal_overshoot:.3f}% of +/-1")
    print(f"[fourier-truncated-edge]   the first chapter's one-pole edge is "
          f"0.350, for contrast: {ideal_transition / ONE_POLE:.3f}x the ringing "
          "edge's constant")
    return P.render(fig)


# --------------------------------------------------------------------------- #
# 5. the sum only knows the repetition
# --------------------------------------------------------------------------- #


def fourier_periodic_extension() -> str:
    """A 1 s record, its butt-jointed copies, and the jump the series invents."""
    t, dt = _grid()
    record = np.exp(-t / SEAM_TAU)
    spectrum = np.fft.fft(record) / record.size
    last = float(record[-1])

    def extension(times: np.ndarray) -> np.ndarray:
        return np.exp(-np.mod(times, T0) / SEAM_TAU)

    def rebuild(times: np.ndarray, k: int = SEAM_K) -> np.ndarray:
        out = np.full(np.shape(times), spectrum[0].real)
        for n in range(1, k + 1):
            out = out + 2.0 * np.real(spectrum[n]
                                      * np.exp(2j * np.pi * n * times / T0))
        return out

    jump = 1.0 - last
    two_sides = (1.0 + last) / 2.0

    # --- the seam, measured --------------------------------------------------
    near = np.linspace(1.0 - 0.2, 1.0 + 0.2, 120_001)
    rebuilt = rebuild(near)
    at_seam = float(rebuild(np.array([1.0]))[0])
    undershoot = float(rebuilt[near < 1.0].min())
    overshoot = float(rebuilt[near > 1.0].max())
    interior = np.linspace(SEAM_INTERIOR, 1.0 - SEAM_INTERIOR, 80_001)
    interior_error = float(np.max(np.abs(rebuild(interior)
                                         - extension(interior))))

    fig, axes = P.figure(height=9.6, nrows=3, hspace=0.62,
                         height_ratios=[0.95, 1.10, 1.15])
    ax_copies, ax_seam, ax_note = axes

    # --- top: three copies, butt-jointed ------------------------------------
    tt = np.linspace(-0.5, 2.6, 30_001)
    ax_copies.plot(tt, extension(tt), color=P.ACCENT, lw=1.9, zorder=4)
    for seam in (1.0, 2.0):
        ax_copies.axvline(seam, color=P.WARN, lw=1.2, ls=(0, (2, 2)), zorder=2)
    ax_copies.annotate("", xy=(1.0, 1.0), xytext=(1.0, last),
                       arrowprops=dict(arrowstyle="<->", color=P.WARN,
                                       linewidth=1.4, shrinkA=0, shrinkB=0))
    ax_copies.text(1.12, 0.97,
                   f"the seam: {1.0:.4f} down to {last:.4f} —\n"
                   f"a jump of {jump:.4f} the record never had",
                   color=P.WARN, fontsize=9.2, ha="left", va="top", zorder=7,
                   linespacing=1.45)
    ax_copies.text(-0.45, 1.06, "one captured record", color=P.ACCENT,
                   fontsize=9.2, ha="left", va="bottom")
    ax_copies.text(0.42, 1.06, "a copy, glued on", color=P.MUTED, fontsize=9.2,
                   ha="left", va="bottom")
    ax_copies.set_xlim(-0.5, 2.6)
    ax_copies.set_ylim(-0.18, 1.20)
    ax_copies.set_xticks([0.0, 1.0, 2.0])
    ax_copies.set_xticklabels(["0", "$T_0$", "$2T_0$"])
    P.tidy(ax_copies, ylabel="value")
    P.title(ax_copies, "The series rebuilds the repetition, not the record",
            subtitle="every harmonic in the sum has period $T_0$ or a "
                     "submultiple, so the sum cannot be anything but periodic")

    # --- middle: the zoom, and the ringing ----------------------------------
    near_x, near_y = _thin(near, extension(near))
    _, rebuilt_y = _thin(near, rebuilt)
    ax_seam.plot(near_x, near_y, color=P.RULE, lw=3.6, zorder=1,
                 label="the periodic extension")
    ax_seam.plot(near_x, rebuilt_y, color=P.ACCENT, lw=1.6, zorder=4,
                 label=f"K = {SEAM_K} rebuild")
    ax_seam.axhline(two_sides, color=P.NOTE, lw=1.1, ls=(0, (4, 3)), zorder=2)
    ax_seam.axvline(1.0, color=P.SOFT, lw=1.0, zorder=2)
    ax_seam.plot([1.0], [at_seam], "o", ms=6.0, color=P.ACCENT, mec=P.PANEL,
                 mew=1.2, zorder=6)
    ax_seam.annotate(f"at the seam: {at_seam:.4f}\n"
                     f"midpoint: {two_sides:.4f}\n"
                     f"sides: {1.0:.4f}, {last:.4f}",
                     xy=(1.0, at_seam), xytext=(0.795, 1.28), color=P.ACCENT,
                     fontsize=9.0, ha="left", va="top", zorder=7, linespacing=1.40,
                     arrowprops=dict(arrowstyle="->", color=P.ACCENT,
                                     linewidth=1.0, shrinkA=2, shrinkB=3))
    ax_seam.plot([1.0 + 0.035], [overshoot], "^", ms=6.0, color=P.OPTICAL,
                 mec=P.PANEL, mew=1.0, zorder=6)
    ax_seam.annotate(f"{overshoot:.4f}", xy=(1.0 + 0.035, overshoot),
                     xytext=(1.070, 1.24), color=P.OPTICAL, fontsize=9.2,
                     ha="left", va="center", zorder=7,
                     arrowprops=dict(arrowstyle="->", color=P.OPTICAL,
                                     linewidth=1.0, shrinkA=2, shrinkB=3))
    ax_seam.plot([1.0 - 0.035], [undershoot], "v", ms=6.0, color=P.WARN,
                 mec=P.PANEL, mew=1.0, zorder=6)
    ax_seam.annotate(f"{undershoot:.4f}", xy=(1.0 - 0.035, undershoot),
                     xytext=(0.810, -0.32), color=P.WARN, fontsize=9.2,
                     ha="left", va="center", zorder=7,
                     arrowprops=dict(arrowstyle="->", color=P.WARN, linewidth=1.0,
                                     shrinkA=2, shrinkB=3))
    ax_seam.set_xlim(0.8, 1.2)
    ax_seam.set_ylim(-0.45, 1.32)
    ax_seam.set_xticks([0.8, 0.9, 1.0, 1.1, 1.2])
    ax_seam.set_xticklabels(["$T_0-0.2$", "$T_0-0.1$", "$T_0$", "$T_0+0.1$",
                             "$T_0+0.2$"])
    P.tidy(ax_seam, ylabel="value", legend=["the periodic extension",
                                            f"K = {SEAM_K} rebuild"],
           legend_loc="lower right")
    P.title(ax_seam, "A jump is a step, and a truncated series rings around it",
            subtitle=f"the overshoot is {100.0 * (overshoot - 1.0) / jump:.2f}% "
                     f"of the jump above the top and "
                     f"{100.0 * (last - undershoot) / jump:.2f}% below the bottom")

    # --- bottom: the four numbers -------------------------------------------
    ax_note.axis("off")
    seam_label = f"K = {SEAM_K} series at the seam"
    below = last - undershoot
    above = overshoot - 1.0
    rows = [
        f"{'seam jump the copies invent':<32s}{jump:8.4f}",
        f"{seam_label:<32s}{at_seam:8.4f}"
        f"   (midpoint {two_sides:.4f})",
        f"{'undershoot, below the low side':<32s}{undershoot:8.4f}"
        f"   {below:.4f} below = {100.0 * below / jump:.2f}%",
        f"{'overshoot, above the high side':<32s}{overshoot:8.4f}"
        f"   {above:.4f} above = {100.0 * above / jump:.2f}%",
        f"{'worst error, |t - seam| > 0.15':<32s}{interior_error:8.1e}",
    ]
    ax_note.text(0.010, 0.95, "\n".join(rows), transform=ax_note.transAxes,
                 family="monospace", fontsize=9.2, color=P.INK, ha="left",
                 va="top", linespacing=1.38)
    ax_note.text(0.010, 0.40,
                 "The record was a decaying exponential, and nothing in it "
                 "repeats. The series is not wrong\n"
                 "about it: it answers a different question, namely what "
                 "periodic signal has this record\n"
                 "as its one period. Everything inside the record is fitted to "
                 "about three parts in a\n"
                 "thousand; the cost is a discontinuity at every seam.",
                 transform=ax_note.transAxes, fontsize=9.2, color=P.MUTED,
                 ha="left", va="top", linespacing=1.45)

    print(f"[fourier-periodic-extension] 1 s record e^(-t/0.2), {GRID:,} samples:")
    print(f"[fourier-periodic-extension]   seam jump = {jump:.4f}; "
          f"midpoint of the two sides = {two_sides:.4f}")
    print(f"[fourier-periodic-extension]   K = {SEAM_K} series at the seam = "
          f"{at_seam:.4f}")
    print(f"[fourier-periodic-extension]   rings to {undershoot:.4f} "
          f"({100.0 * (last - undershoot) / jump:.2f}% of the jump) "
          f"and {overshoot:.4f} "
          f"({100.0 * (overshoot - 1.0) / jump:.2f}% of the jump)")
    print(f"[fourier-periodic-extension]   interior |t-seam| > "
          f"{SEAM_INTERIOR}: max error {interior_error:.1e}")
    return P.render(fig)


# --------------------------------------------------------------------------- #
# 6. taking the period away
# --------------------------------------------------------------------------- #


def fourier_limit_to_transform() -> str:
    """One pulse, three periods: the lines crowd and shrink, the envelope stays."""
    fig, axes = P.figure(height=9.2, nrows=3, hspace=0.72)
    measured = []
    for row, (ax, period) in enumerate(zip(axes, PERIODS)):
        n = 200_002
        t = np.linspace(-0.5 * period, 0.5 * period, n, endpoint=False)
        train = _pulse_train(t, period)
        spectrum = np.fft.fft(train) / n               # c_n, n = 0 … N−1
        f0 = 1.0 / period
        n_max = int(np.floor(LIMIT_BAND / f0))
        index = np.arange(-n_max, n_max + 1)
        c = spectrum[np.mod(index, n)]
        frequencies = index * f0

        at_one = int(np.argmin(np.abs(frequencies - 1.0)))
        c_at_one = float(np.abs(c[at_one]))

        envelope_f = np.linspace(-LIMIT_BAND, LIMIT_BAND, 4001)
        envelope = PULSE_WIDTH * np.sinc(PULSE_WIDTH * envelope_f)

        ax.vlines(frequencies, 0.0, np.abs(c), color=P.ACCENT, lw=1.2, zorder=3)
        ax.plot(frequencies, np.abs(c), "o", ms=2.6, color=P.ACCENT, ls="none",
                zorder=4)
        ax.plot(envelope_f, np.abs(envelope), color=P.NOTE, lw=1.6, zorder=5)
        # c_n·T₀, which is X(nf₀): the rings land on the curve the stems sit under
        ax.plot(frequencies, np.abs(c) * period, "o", ms=3.4, color=P.WARN,
                mfc=P.PANEL, mew=1.1, ls="none", zorder=6)
        ax.plot([1.0], [c_at_one], "o", ms=7.0, color=P.WARN, mec=P.PANEL,
                mew=1.2, zorder=7)
        ax.axvline(1.0, color=P.WARN, lw=1.0, ls=(0, (2, 3)), zorder=2)
        ax.annotate(f"$c_n$ at 1 Hz = {c_at_one:.5f}",
                    xy=(1.0, c_at_one), xytext=(1.30, 0.30), color=P.WARN,
                    fontsize=9.2, ha="left", va="center", zorder=8,
                    arrowprops=dict(arrowstyle="->", color=P.WARN, linewidth=1.0,
                                    shrinkA=2, shrinkB=3))
        ax.text(-LIMIT_BAND + 0.15, 0.355,
                "the curve $X(f)$, the same at every period",
                color=P.NOTE, fontsize=9.2, ha="left", va="top", zorder=7,
                family="sans-serif")
        _footnote(ax, -LIMIT_BAND + 0.15, 0.300,
                  f"$T_0$ = {period:g} s,  $f_0$ = {f0:g} Hz\n"
                  f"$c_n$ at 1 Hz = {c_at_one:.5f} — the stem\n"
                  f"$c_n T_0$ = {c_at_one * period:.5f} — the ring, on $X(f)$",
                  size=9.2, va="top")
        ax.set_xlim(-LIMIT_BAND, LIMIT_BAND)
        ax.set_ylim(0.0, 0.40)
        ax.set_xticks([-6, -4, -2, 0, 2, 4, 6])
        # the axis carries two quantities in their own units, so it is named for
        # both: a stem is |c_n|, a ring is c_n·T₀ = X(nf₀). The factor between the
        # two scales is T₀, and the note at the foot of the figure says so.
        P.tidy(ax, ylabel="stems $|c_n|$\nrings $X(f)$")
        if row == 0:
            P.title(ax, "Taking the period away: the lines crowd and shrink",
                    subtitle=f"$T_0$ = {period:g} s, spacing {f0:g} Hz — the stem "
                             "at −f mirrors the one at +f, and the envelope is "
                             "the same curve at every period")
        else:
            P.title(ax, f"$T_0$ = {period:g} s: spacing {f0:g} Hz, "
                        f"stems at {c_at_one:.5f}",
                    subtitle="the same 0.25 s pulse, repeated less often")
        measured.append((period, f0, c_at_one, c_at_one * period))

    P.tidy(axes[-1], xlabel="frequency  f  (Hz)")

    fig.subplots_adjust(bottom=0.165)
    fig.text(0.012, 0.010,
             "Two quantities share each axis, and each is read at its own value: "
             "a stem is $|c_n|$ and a ring is that same\n"
             "coefficient multiplied by the line spacing, $c_nT_0 = X(nf_0)$ — "
             "which is why every ring lands on the curve $X(f)$\n"
             "and stands $T_0$ above the stem it marks: four times above it at "
             "$T_0$ = 4 s.",
             fontsize=8.7, color=P.MUTED, ha="left", va="bottom", linespacing=1.5)

    print("[fourier-limit-to-transform] 0.25 s pulse, height 1, period T0:")
    for period, f0, c_at_one, product in measured:
        print(f"[fourier-limit-to-transform]   T0 = {period:g} s: f0 = {f0:g} Hz, "
              f"c_n at 1 Hz = {c_at_one:.5f}, c_n*T0 = {product:.5f}")
    products = [p for _, _, _, p in measured]
    print(f"[fourier-limit-to-transform]   X(1 Hz) = "
          f"{PULSE_WIDTH * np.sinc(PULSE_WIDTH * 1.0):.5f}; spread of c_n*T0 = "
          f"{max(products) - min(products):.1e}; the stems are "
          "|X(nf0)|/T0 and the rings are that product")
    return P.render(fig)


# --------------------------------------------------------------------------- #
# 7. rect and sinc: the pair, and the limit that is not a curve
# --------------------------------------------------------------------------- #


def fourier_rect_sinc_pair() -> str:
    """Width against height, X(0) against the first zero, energy by both books."""
    fig, axes = P.figure(height=7.6, nrows=2, ncols=2, hspace=0.70)
    fig.subplots_adjust(wspace=0.30, bottom=0.14)
    ax_time, ax_freq = axes[0]
    ax_limit, ax_spike = axes[1]

    # --- energy, both books, before anything that prints it -----------------
    band = np.linspace(-ENERGY_BAND, ENERGY_BAND, 4_000_001)
    spectrum = RECT_WIDTHS[0] * np.sinc(RECT_WIDTHS[0] * band)
    energy_frequency = float(np.trapezoid(spectrum ** 2, band))
    inside = np.abs(band) < 1.0 / RECT_WIDTHS[0]
    energy_lobe = float(np.trapezoid((spectrum ** 2)[inside], band[inside]))
    grid = np.linspace(-0.5, 0.5, GRID, endpoint=False)
    pulse = np.where(np.abs(grid) < 0.5 * RECT_WIDTHS[0], 1.0, 0.0)
    energy_time = float(np.sum(pulse ** 2) * (T0 / GRID))

    # --- top left: three rects of height 1 ----------------------------------
    t = np.linspace(-1.6, 1.6, 6001)
    colours = dict(zip(RECT_WIDTHS, (P.WARN, P.ACCENT, P.OPTICAL)))
    for width in RECT_WIDTHS:
        ax_time.plot(t, np.where(np.abs(t) < 0.5 * width, 1.0, 0.0),
                     color=colours[width], lw=1.9,
                     label=f"$\\tau$ = {width:g} s")
    ax_time.set_xlim(-1.6, 1.6)
    ax_time.set_ylim(-0.12, 1.48)
    P.tidy(ax_time, xlabel="time  t  (s)", ylabel="value",
           legend=[f"$\\tau$ = {w:g} s" for w in RECT_WIDTHS],
           legend_loc="upper right")
    P.title(ax_time, "One number decides the pulse",
            subtitle="height 1, width $\\tau$: the area is $\\tau$")

    # --- top right: the three transforms ------------------------------------
    f = np.linspace(-8.0, 8.0, 16_001)
    for width in RECT_WIDTHS:
        ax_freq.plot(f, width * np.sinc(width * f), color=colours[width], lw=1.7,
                     label=f"$\\tau$ = {width:g} s")
        ax_freq.plot([0.0], [width], "o", ms=5.0, color=colours[width],
                     mec=P.PANEL, mew=1.0, zorder=6)
        ax_freq.plot([1.0 / width], [0.0], "v", ms=5.0, color=colours[width],
                     mec=P.PANEL, mew=1.0, zorder=6)
    ax_freq.axhline(0.0, color=P.SOFT, lw=1.0, zorder=2)
    ax_freq.annotate("$X(0) = \\tau$", xy=(0.0, 2.0), xytext=(-3.4, 2.10),
                     color=P.OPTICAL, fontsize=8.8, ha="left", va="center",
                     zorder=7,
                     arrowprops=dict(arrowstyle="->", color=P.OPTICAL,
                                     linewidth=1.0, shrinkA=2, shrinkB=4))
    ax_freq.annotate("first zero at $1/\\tau$", xy=(0.5, 0.0), xytext=(1.6, 0.55),
                     color=P.OPTICAL, fontsize=8.8, ha="left", va="center",
                     zorder=7,
                     arrowprops=dict(arrowstyle="->", color=P.OPTICAL,
                                     linewidth=1.0, shrinkA=2, shrinkB=4))
    ax_freq.set_xlim(-8.0, 8.0)
    ax_freq.set_ylim(-0.75, 2.52)
    ax_freq.set_xticks([-8, -4, -2, 0, 2, 4, 8])
    P.tidy(ax_freq, xlabel="frequency  f  (Hz)", ylabel="$X(f)$",
           legend=[f"$\\tau$ = {w:g} s" for w in RECT_WIDTHS],
           legend_loc="upper right")
    P.title(ax_freq, "$X(f) = \\tau\\,\\mathrm{sinc}(\\tau f)$",
            subtitle="$X(0)\\times$ first zero = 1 for every $\\tau$")

    # --- bottom left: the unit-area pulses, narrowing -----------------------
    t2 = np.linspace(-0.30, 0.30, 24_001)
    limit_colours = dict(zip(LIMIT_WIDTHS, (P.ACCENT, P.NOTE, P.OPTICAL)))
    for width in LIMIT_WIDTHS:
        ax_limit.plot(t2, np.where(np.abs(t2) < 0.5 * width, 1.0 / width, 0.0),
                      color=limit_colours[width], lw=1.7,
                      label=f"$\\tau$ = {width:g} s: height {1.0 / width:g}")
    ax_limit.text(-0.29, 68.0,
                  "height × width = 1 at every width:\n"
                  "4 × 0.25 = 10 × 0.1 = 50 × 0.02",
                  fontsize=8.8, color=P.MUTED, ha="left", va="top",
                  linespacing=1.4)
    ax_limit.set_xlim(-0.30, 0.30)
    ax_limit.set_ylim(0.0, 72.0)
    ax_limit.set_xticks([-0.25, 0.0, 0.25])
    P.tidy(ax_limit, xlabel="time  t  (s)", ylabel="value",
           legend=[f"$\\tau$ = {w:g} s: height {1.0 / w:g}" for w in LIMIT_WIDTHS],
           legend_loc="center right")
    P.title(ax_limit, "Run the width to zero and keep the area",
            subtitle="the pulse becomes $\\delta(t)$: no width left to draw")

    # --- bottom right: the flattening spectrum, then the spike --------------
    for width in LIMIT_WIDTHS:
        ax_spike.plot(f, np.sinc(width * f), color=limit_colours[width], lw=1.7,
                      label=f"$\\tau$ = {width:g} s")
    ax_spike.axhline(1.0, color=P.RULE, lw=1.0, ls=(0, (4, 3)), zorder=2)
    ax_spike.annotate("", xy=(0.0, 1.12), xytext=(0.0, 0.0),
                      arrowprops=dict(arrowstyle="-|>", color=P.WARN,
                                      linewidth=2.4, shrinkA=0, shrinkB=0))
    ax_spike.text(-7.7, 1.56,
                  "$\\delta(f)$: unit area at one point — an arrow, not a curve.\n"
                  "Run the other way, a constant's transform is that spike,\n"
                  "which is why it has no curve you can plot.",
                  color=P.WARN, fontsize=8.4, ha="left", va="top", zorder=7,
                  linespacing=1.45)
    ax_spike.set_xlim(-8.0, 8.0)
    ax_spike.set_ylim(-0.32, 1.62)
    ax_spike.set_xticks([-8, -4, 0, 4, 8])
    P.tidy(ax_spike, xlabel="frequency  f  (Hz)", ylabel="$X(f)$",
           legend=[f"$\\tau$ = {w:g} s" for w in LIMIT_WIDTHS],
           legend_loc="lower right")
    P.title(ax_spike, "The limit of the same scaling, then a spike",
            subtitle="unit-area pulse: $X(f) \\to 1$ for every f")

    fig.text(0.012, 0.012,
             "numbers on this figure, all computed.\n"
             "widths: "
             + "; ".join(f"$\\tau$ = {w:g} s → $X(0)$ = {w:g}, first zero at "
                         f"{1.0 / w:g} Hz, product {w * (1.0 / w):g}"
                         for w in RECT_WIDTHS)
             + f".\nEnergy of the 0.25 s pulse, both books: $\\int x^2 dt$ = "
             f"{energy_time:.4f} and $\\int |X|^2 df$ = {energy_frequency:.4f} "
             f"over ±{ENERGY_BAND:.0e} Hz; "
             f"{100.0 * energy_lobe / energy_frequency:.1f}% of it inside the "
             f"first lobe, $|f| < {1.0 / RECT_WIDTHS[0]:g}$ Hz.",
             fontsize=7.9, color=P.SOFT, ha="left", va="bottom", linespacing=1.55)

    print("[fourier-rect-sinc-pair] rect of height 1, width tau:")
    for width in RECT_WIDTHS:
        print(f"[fourier-rect-sinc-pair]   tau = {width:g} s: X(0) = {width:.4f}, "
              f"first zero at {1.0 / width:g} Hz, X(0)*zero = "
              f"{width * (1.0 / width):.4f}")
    print(f"[fourier-rect-sinc-pair]   energy both books (tau = 0.25 s): time "
          f"{energy_time:.4f}, frequency {energy_frequency:.4f}, "
          f"{100.0 * energy_lobe / energy_frequency:.2f}% inside |f| < 4 Hz")
    print("[fourier-rect-sinc-pair]   unit-area limit: X(f) = sinc(tau f) -> 1 for "
          "every f as tau -> 0; the constant's transform is an impulse of unit "
          "area, which has no width to draw")
    return P.render(fig)


FIGURES = {
    "fourier-square-partial-sums": fourier_square_partial_sums,
    "fourier-coefficient-projection": fourier_coefficient_projection,
    "fourier-symmetry-harmonics": fourier_symmetry_harmonics,
    "fourier-truncated-edge": fourier_truncated_edge,
    "fourier-periodic-extension": fourier_periodic_extension,
    "fourier-limit-to-transform": fourier_limit_to_transform,
    "fourier-rect-sinc-pair": fourier_rect_sinc_pair,
}
