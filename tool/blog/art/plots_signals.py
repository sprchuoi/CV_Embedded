"""Computed figures for chapter 01, "What a Signal Actually Is".

Three numpy/matplotlib figures, in the order the article uses them:

    signal-elementary-waveforms    the shapes a beginner meets first, each one
                                   carrying the numbers that define it
    signal-continuous-vs-discrete  one signal as a curve, and as a list of numbers
    signal-energy-vs-power         which of the two quantities stays finite

Every number written on these figures is measured from the arrays the curves are
drawn from, and the measured values live at module scope so that a test can
print them: the Gaussian's energy is the last value of a ``cumsum``, the sinusoid
average power is that energy divided by the elapsed time, and the sample counts
are ``len()`` of the very arrays that are stemmed. An annotation therefore
cannot drift away from the curve underneath it.

Conventions, shared with the rest of the ``plots_*`` family: the palette comes
from :mod:`plotstyle`, each builder takes no arguments and returns a complete
SVG string, and the axis unit is seconds with amplitude in the article's own
"one" (the peak of the reference sine). The generator below is declared -- and
seeded -- even though nothing here draws random numbers, so that the single
source of randomness has one obvious home if a stochastic figure is added later.
"""

from __future__ import annotations

import numpy as np

from . import plotstyle as P

# Rebuilds must be reproducible; see the module docstring.
RNG = np.random.default_rng(0)


# --------------------------------------------------------------------------- #
# the measured quantities the annotations quote
# --------------------------------------------------------------------------- #

# --- figure 1: the elementary waveforms -------------------------------------
SINE_AMP = 1.0                       # the amplitude the arrows mark
SINE_F = 0.5                         # Hz, so one period spans 2 s
SINE_PHI = np.pi / 3.0               # rad of phase lead
SINE_PERIOD = 1.0 / SINE_F           # 2.0 s
SINE_LEAD = float(SINE_PHI / (2 * np.pi * SINE_F))          # 1/3 s: phi in seconds
SINE_PEAK = float((np.pi / 2 - SINE_PHI) / (2 * np.pi * SINE_F))   # first peak

DECAY_TAU = 0.6                      # s, the time constant
DECAY_AT_TAU = float(np.exp(-1.0))    # 0.3679: the value one time constant later

RECT_T0, RECT_T1, RECT_AMP = 0.4, 1.9, 1.0
RECT_WIDTH = RECT_T1 - RECT_T0       # 1.5 s

COMPLEX_F = 0.5                      # Hz of the complex exponential

CHIRP_F0, CHIRP_F1 = 0.25, 1.25      # Hz at t = -1 and at t = 3
CHIRP_T0, CHIRP_T1 = -1.0, 3.0
CHIRP_K = (CHIRP_F1 - CHIRP_F0) / (CHIRP_T1 - CHIRP_T0)     # 0.25 Hz/s

# --- figure 2: the same signal, two ways ------------------------------------
SAMPLE_RATES = (16, 64)
CONT_F1, CONT_A1 = 2.0, 1.0
CONT_F2, CONT_A2, CONT_PHI2 = 5.0, 0.5, 0.4

# --- figure 3: energy against power -----------------------------------------
# The energy signal: a Gaussian pulse, integrated far enough out that the tails
# have vanished. Its exact energy is sqrt(pi/2) = 1.25331..., so the cumsum can
# be checked against a closed form rather than against itself.
PULSE_TAU = 1.0                      # s
PULSE_T = np.linspace(-5.0, 5.0, 8001)
PULSE_DT = float(PULSE_T[1] - PULSE_T[0])
PULSE_X = np.exp(-(PULSE_T / PULSE_TAU) ** 2)
PULSE_RUNNING = np.cumsum(PULSE_X ** 2) * PULSE_DT
PULSE_TOTAL = float(PULSE_RUNNING[-1])
PULSE_EXACT = float(np.sqrt(np.pi / 2.0))

# The power signal: a unit-amplitude sine, still running at t = 20 s. Its
# running energy is unbounded; energy divided by elapsed time settles on 1/2.
POWER_F = 1.0                        # Hz
POWER_T = np.linspace(0.0, 20.0, 2001)
POWER_DT = float(POWER_T[1] - POWER_T[0])
POWER_X = np.sin(2 * np.pi * POWER_F * POWER_T)
POWER_RUNNING = np.cumsum(POWER_X ** 2) * POWER_DT
POWER_AVG = POWER_RUNNING / np.where(POWER_T > 0.0, POWER_T, np.nan)
POWER_LIMIT = float(POWER_RUNNING[-1] / POWER_T[-1])
POWER_RIPPLE = float(np.nanmax(np.abs(POWER_AVG[POWER_T >= 15.0] - POWER_LIMIT)))


# --------------------------------------------------------------------------- #
# local plotting helpers
# --------------------------------------------------------------------------- #


def _head(ax, title, subtitle=None, *, size=9):
    """Title plus a subtitle that clears it.

    ``P.title`` does exactly this for a full-width figure; the small panels of
    the 2x3 grid need the same layout at a smaller type size.
    """
    if subtitle is None:
        P.title(ax, title)
        return
    ax.set_title(title, pad=22)
    ax.text(0.0, 1.012, subtitle, transform=ax.transAxes, fontsize=size,
            color=P.MUTED, va="bottom")


def _dashed(ax, x0, x1, y0, y1, *, color=P.NOTE, lw=1.0):
    ax.plot([x0, x1], [y0, y1], color=color, lw=lw, ls=(0, (4, 3)), zorder=3)


def _measure(ax, x0, y0, x1, y1, *, color=P.SOFT, lw=1.0):
    """A double-headed arrow: a distance marked on the figure, not described."""
    ax.annotate("", xy=(x1, y1), xytext=(x0, y0), zorder=6,
                arrowprops=dict(arrowstyle="<->", color=color, lw=lw,
                                shrinkA=0, shrinkB=0, mutation_scale=9))


def _stem(ax, n, values, colour, *, markersize=4.2, width=1.2, zorder=5):
    """A stem plot in the house palette; matplotlib's defaults are too loud."""
    markerline, stemlines, baseline = ax.stem(n, values)
    markerline.set_color(colour)
    markerline.set_markersize(markersize)
    markerline.set_zorder(zorder)
    stemlines.set_color(colour)
    stemlines.set_linewidth(width)
    stemlines.set_zorder(zorder - 1)
    baseline.set_color(P.RULE_SOFT)
    baseline.set_linewidth(1.0)
    baseline.set_zorder(1)
    return markerline, stemlines, baseline


def _right_axis(ax, label: str):
    """A second y axis with the right spine drawn (rcParams hides it)."""
    twin = ax.twinx()
    twin.grid(False)
    twin.spines["right"].set_visible(True)
    twin.spines["right"].set_color(P.RULE)
    twin.spines["top"].set_visible(False)
    twin.tick_params(colors=P.MUTED, labelsize=9)
    twin.set_ylabel(label, color=P.SOFT)
    return twin


# --------------------------------------------------------------------------- #
# 1. the elementary waveforms
# --------------------------------------------------------------------------- #


def signal_elementary_waveforms() -> str:
    """Six panels: the shapes themselves, with the numbers that pin them down."""
    t = np.linspace(-1.0, 3.0, 4001)
    fig, axes = P.figure(height=4.6, nrows=2, ncols=3, hspace=0.80)

    # --- 1. a real sinusoid, with amplitude, period and phase marked ---------
    ax = axes[0][0]
    ax.plot(t, SINE_AMP * np.sin(2 * np.pi * SINE_F * t), color=P.RULE, lw=1.0,
            ls=(0, (4, 3)), zorder=3)
    ax.plot(t, SINE_AMP * np.sin(2 * np.pi * SINE_F * t + SINE_PHI),
            color=P.ACCENT, lw=2.0, zorder=4)

    # amplitude: a vertical arrow from the axis to the first peak
    _measure(ax, SINE_PEAK, 0.0, SINE_PEAK, SINE_AMP, color=P.ACCENT_DARK)
    ax.text(SINE_PEAK + 0.07, SINE_AMP + 0.03, f"amplitude {SINE_AMP:g}",
            color=P.ACCENT_DARK, fontsize=8, ha="left", va="bottom")

    # period: peak to peak, marked up in the space the wave never reaches
    _measure(ax, SINE_PEAK, 1.62, SINE_PEAK + SINE_PERIOD, 1.62,
             color=P.ACCENT_DARK)
    ax.text(SINE_PEAK + SINE_PERIOD / 2, 1.70, f"period {SINE_PERIOD:g} s",
            color=P.ACCENT_DARK, fontsize=8, ha="center", va="bottom")

    # phase: the horizontal distance between this wave and the dashed reference,
    # drawn from the two zero crossings down into the empty lower band
    for crossing in (0.0, -SINE_LEAD):
        _dashed(ax, crossing, crossing, 0.0, -1.62)
    _measure(ax, -SINE_LEAD, -1.62, 0.0, -1.62, color=P.NOTE)
    ax.text(0.10, -1.78, f"phase $\\pi/3$: {SINE_LEAD:.2f} s ahead",
            color=P.NOTE, fontsize=8, ha="left", va="top")

    ax.set_xlim(-1.0, 3.0)
    ax.set_ylim(-2.45, 2.05)
    _head(ax, "A real sinusoid", "dashed: no phase shift", size=8)
    P.tidy(ax, ylabel="amplitude")

    # --- 2. a decaying exponential, with the time constant marked ------------
    ax = axes[0][1]
    ax.plot(t, np.where(t >= 0.0, np.exp(-np.maximum(t, 0.0) / DECAY_TAU), 0.0),
            color=P.ACCENT, lw=2.0, zorder=4)
    _dashed(ax, DECAY_TAU, DECAY_TAU, 0.0, DECAY_AT_TAU, color=P.NOTE)
    _measure(ax, 0.0, DECAY_AT_TAU, DECAY_TAU, DECAY_AT_TAU, color=P.NOTE)
    ax.text(DECAY_TAU / 2, DECAY_AT_TAU + 0.03, "T", color=P.NOTE, fontsize=8.5,
            ha="center", va="bottom")
    ax.plot([DECAY_TAU], [DECAY_AT_TAU], marker="o", ls="none", ms=5.0,
            color=P.ACCENT_DARK, mec=P.PANEL, mew=1.1, zorder=6)
    # The value one time constant later lives well above the decaying tail, so
    # the label hangs there and a leader line carries it down to the marker.
    ax.annotate(f"1/e = {DECAY_AT_TAU:.3f}", xy=(DECAY_TAU, DECAY_AT_TAU),
                xytext=(1.15, 0.72), ha="left", va="center",
                color=P.ACCENT_DARK, fontsize=8,
                arrowprops=dict(arrowstyle="->", color=P.ACCENT_DARK, lw=0.9,
                                shrinkA=2, shrinkB=3))
    ax.text(-0.90, 0.10, "zero until the switch-on", color=P.MUTED, fontsize=8,
            ha="left", va="bottom")

    ax.set_xlim(-1.0, 3.0)
    ax.set_ylim(-0.18, 1.28)
    _head(ax, "A decaying exponential", f"T = {DECAY_TAU:g} s, the 1/e point",
          size=8)

    # --- 3. a unit step, discontinuity drawn honestly ------------------------
    ax = axes[0][2]
    ax.plot([-1.0, 0.0, 0.0, 3.0], [0.0, 0.0, 1.0, 1.0], color=P.ACCENT,
            lw=2.0, zorder=4)
    ax.plot([0.0], [1.0], marker="o", ls="none", ms=5.0, color=P.ACCENT,
            mec=P.PANEL, mew=1.2, zorder=6)
    ax.plot([0.0], [0.0], marker="o", ls="none", ms=5.0, mfc=P.PANEL,
            mec=P.ACCENT, mew=1.2, zorder=6)
    ax.text(-0.92, 0.09, "0 for every t < 0", color=P.MUTED, fontsize=8,
            ha="left", va="bottom")
    ax.text(0.12, 1.06, "1 for every t > 0", color=P.MUTED, fontsize=8,
            ha="left", va="bottom")
    ax.text(2.92, 0.72, "the riser is a drawing\nconvention, not a value",
            color=P.NOTE, fontsize=8, ha="right", va="center")

    ax.set_xlim(-1.0, 3.0)
    ax.set_ylim(-0.22, 1.42)
    _head(ax, "A unit step", "two values, one jump", size=8)

    # --- 4. a rectangular pulse, width and height marked ---------------------
    ax = axes[1][0]
    ax.plot([-1.0, RECT_T0, RECT_T0, RECT_T1, RECT_T1, 3.0],
            [0.0, 0.0, RECT_AMP, RECT_AMP, 0.0, 0.0], color=P.ACCENT, lw=2.0,
            zorder=4)
    _measure(ax, 0.18, 0.0, 0.18, RECT_AMP, color=P.ACCENT_DARK)
    ax.text(0.10, RECT_AMP / 2, f"height {RECT_AMP:g}", color=P.ACCENT_DARK,
            fontsize=8, ha="right", va="center")
    for edge in (RECT_T0, RECT_T1):
        _dashed(ax, edge, edge, 0.0, -0.30, color=P.NOTE)
    _measure(ax, RECT_T0, -0.30, RECT_T1, -0.30, color=P.NOTE)
    ax.text((RECT_T0 + RECT_T1) / 2, -0.38, f"width {RECT_WIDTH:g} s",
            color=P.NOTE, fontsize=8, ha="center", va="top")

    ax.set_xlim(-1.0, 3.0)
    ax.set_ylim(-0.80, 1.38)
    _head(ax, "A rectangular pulse", "width and height", size=8)
    P.tidy(ax, xlabel="time (s)", ylabel="amplitude")

    # --- 5. a complex exponential: real and imaginary parts ------------------
    ax = axes[1][1]
    ax.plot(t, np.cos(2 * np.pi * COMPLEX_F * t), color=P.ACCENT, lw=2.0,
            zorder=4, label="real part")
    ax.plot(t, np.sin(2 * np.pi * COMPLEX_F * t), color=P.OPTICAL, lw=1.7,
            ls=(0, (5, 3)), zorder=5, label="imaginary part")
    ax.text(1.0, 1.28, "one signal, not two", color=P.INK, fontsize=8.5,
            ha="center", va="center")

    ax.set_xlim(-1.0, 3.0)
    ax.set_ylim(-2.20, 1.60)
    _head(ax, "A complex exponential", "seen from two axes", size=8)
    P.tidy(ax, xlabel="time (s)", legend=["real part", "imaginary part"],
           legend_loc="lower center", ncol=2)

    # --- 6. a linear chirp, instantaneous frequency at both ends -------------
    ax = axes[1][2]
    u = t - CHIRP_T0                                   # 0 .. 4
    phase = 2 * np.pi * (CHIRP_F0 * u + 0.5 * CHIRP_K * u ** 2)
    ax.plot(t, np.cos(phase), color=P.ACCENT, lw=2.0, zorder=4)
    ax.text(-0.92, -1.36, f"f = {CHIRP_F0:g} Hz", color=P.NOTE,
            fontsize=8, ha="left", va="center")
    ax.text(2.92, -1.36, f"f = {CHIRP_F1:g} Hz", color=P.NOTE, fontsize=8,
            ha="right", va="center")

    ax.set_xlim(-1.0, 3.0)
    ax.set_ylim(-1.70, 1.45)
    _head(ax, "A linear chirp", "frequency climbs", size=8)
    P.tidy(ax, xlabel="time (s)")

    return P.render(fig)


# --------------------------------------------------------------------------- #
# 2. continuous against discrete
# --------------------------------------------------------------------------- #


def _two_tone(t):
    """The chapter's running signal: two sinusoids, so it is not a plain sine."""
    return (CONT_A1 * np.sin(2 * np.pi * CONT_F1 * t)
            + CONT_A2 * np.sin(2 * np.pi * CONT_F2 * t + CONT_PHI2))


def signal_continuous_vs_discrete() -> str:
    """One signal drawn densely, then listed at 16 and at 64 samples."""
    dense_t = np.linspace(0.0, 1.0, 4001)
    counts = SAMPLE_RATES
    sampled = []
    for fs in counts:
        ts = np.arange(fs) / float(fs)
        sampled.append((ts, _two_tone(ts)))

    fig, (top, bottom) = P.figure(height=5.0, nrows=2, sharex=True, hspace=0.55,
                                  height_ratios=[1.0, 1.25])

    # --- top: the continuous-time view --------------------------------------
    top.plot(dense_t, _two_tone(dense_t), color=P.ACCENT, lw=1.8, zorder=4)
    top.set_xlim(0.0, 1.0)
    top.set_ylim(-2.5, 2.5)
    top.text(0.015, 2.02, "a continuum of values", color=P.INK, fontsize=9.5,
             ha="left", va="center")
    top.text(0.985, 2.02, "one value at every instant", color=P.MUTED,
             fontsize=8.5, ha="right", va="center")
    _head(top, "Continuous time",
          "x(t) exists at every instant, with nothing in between")

    # --- bottom: the same signal, sampled twice over -------------------------
    m16, _, _ = _stem(bottom, sampled[0][0], sampled[0][1], P.ACCENT,
                      markersize=4.6, width=1.5, zorder=5)
    m64, _, _ = _stem(bottom, sampled[1][0], sampled[1][1], P.OPTICAL,
                      markersize=3.0, width=0.9, zorder=7)

    bottom.set_xlim(0.0, 1.0)
    bottom.set_ylim(-2.5, 2.5)
    bottom.legend([m16, m64],
                  [f"$f_s$ = {counts[0]} Hz - {counts[0]} numbers",
                   f"$f_s$ = {counts[1]} Hz - {counts[1]} numbers"],
                  loc="upper center", ncol=2)
    _head(bottom, "Discrete time",
          "the same x(t), sampled - a list of numbers, and a longer list if you "
          "look more often")
    P.tidy(bottom, xlabel="time (s)", ylabel="amplitude")

    return P.render(fig)


# --------------------------------------------------------------------------- #
# 3. energy signals against power signals
# --------------------------------------------------------------------------- #


def signal_energy_vs_power() -> str:
    """A finite-energy pulse above a sine whose energy never stops growing."""
    fig, axes = P.figure(height=5.4, nrows=2, hspace=0.62)
    top, bottom = axes

    # --- top: an energy signal ----------------------------------------------
    top.plot(PULSE_T, PULSE_X, color=P.ACCENT, lw=2.0, zorder=4)
    top.text(-4.8, 0.58, "the pulse dies away, so the\nrunning sum settles",
             color=P.MUTED, fontsize=8.5, ha="left", va="center")

    energy_axis = _right_axis(top, "running energy  (amplitude$^2$ $\\cdot$ s)")
    energy_axis.plot(PULSE_T, PULSE_RUNNING, color=P.NOTE, lw=1.9, zorder=5)
    energy_axis.axhline(PULSE_TOTAL, color=P.NOTE, lw=1.0, ls=(0, (4, 3)),
                        zorder=3)
    energy_axis.text(4.8, PULSE_TOTAL * 1.10,
                     f"total energy = {PULSE_TOTAL:.4f} - finite",
                     color=P.NOTE, fontsize=9, ha="right", va="bottom")
    energy_axis.set_ylim(0.0, PULSE_TOTAL * 1.40)

    top.set_xlim(-5.0, 5.0)
    top.set_ylim(-0.14, 1.22)
    _head(top, "An energy signal",
          "a Gaussian pulse: it starts, it ends, and its energy adds up to a "
          "number")
    P.tidy(top, xlabel="time (s)", ylabel="amplitude  $x(t)$")

    # --- bottom: a power signal ---------------------------------------------
    valid = POWER_T > 0.0
    bottom.plot(POWER_T[valid], POWER_AVG[valid], color=P.ACCENT, lw=2.2,
                zorder=5)
    bottom.axhline(POWER_LIMIT, color=P.RULE, lw=1.0, ls=(0, (4, 3)), zorder=3)
    bottom.text(19.6, 0.398,
                "average power = energy $\\div$ time $\\to$ "
                f"{POWER_LIMIT:.4f} - finite,\n"
                f"within {POWER_RIPPLE:.4f} of it after t = 15 s",
                color=P.ACCENT_DARK, fontsize=8.5, ha="right", va="center",
                linespacing=1.5)

    energy_axis = _right_axis(bottom, "running energy  (amplitude$^2$ $\\cdot$ s)")
    energy_axis.plot(POWER_T, POWER_RUNNING, color=P.WARN, lw=2.0, zorder=5)
    energy_axis.text(0.5, 13.0,
                     "running energy: no limit - it climbs "
                     f"{POWER_LIMIT:.4f} every second",
                     color=P.WARN, fontsize=9, ha="left", va="top")
    energy_axis.text(19.6, 13.0,
                     f"{POWER_RUNNING[-1]:.2f} after 20 s, still rising",
                     color=P.WARN, fontsize=9, ha="right", va="top")
    energy_axis.set_ylim(0.0, 14.0)

    bottom.set_xlim(0.0, 20.0)
    bottom.set_ylim(0.35, 0.65)
    _head(bottom, "A power signal",
          "x(t) = sin 2$\\pi$t, still going at t = 20 s: the sum has no limit, "
          "but its rate does")
    P.tidy(bottom, xlabel="time (s)",
           ylabel="average power  (energy $\\div$ elapsed time)")

    return P.render(fig)


FIGURES = {
    "signal-elementary-waveforms": signal_elementary_waveforms,
    "signal-continuous-vs-discrete": signal_continuous_vs_discrete,
    "signal-energy-vs-power": signal_energy_vs_power,
}
