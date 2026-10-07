"""Computed figures for the SerDes anatomy chapter.

    serdes-pulse-response   the pulse that arrives, the eye it produces, and the
                            post-cursor the DFE has to remove
    ctle-response           what the continuous-time equaliser does to the
                            channel's response, and to its noise

The pulse response is the single most useful picture in a SerDes: every
equaliser in the chain is defined by what it does to one of its samples.
"""

from __future__ import annotations

import numpy as np
from matplotlib.collections import LineCollection

from . import plotstyle as P

RNG = np.random.default_rng(7391)

OS = 32
SPAN = 20
NSYM = 2000
N_TRACES = 120
DRAW_POINTS = 41


def _channel(ui_taps: np.ndarray, os: int, span: int,
             rolloff: float = 0.5) -> np.ndarray:
    """A channel as a symbol-spaced tap set, interpolated onto a fine grid.

    ``ui_taps`` is the channel's response sampled at the symbol rate, which is
    what a SerDes characterisation actually measures. A raised-cosine kernel
    turns those samples into a continuous impulse response -- the interpolation
    every characterisation tool performs -- so the figure's pulse is the same
    object the taps describe.
    """
    taps = np.asarray(ui_taps, dtype=float)
    # Anchor the *main cursor* (the largest tap) at the grid's centre. Using
    # the array's midpoint instead puts a pre-cursor where the main cursor
    # belongs, which shifts every later sample by one symbol.
    centre = int(np.argmax(taps))
    latency = span * os                     # room for the kernel's own tail
    fine = np.zeros(2 * latency + 1)
    for i, tap in enumerate(taps):
        idx = latency + (i - centre) * os
        if 0 <= idx < len(fine):
            fine[idx] += tap

    n = np.arange(-span * os, span * os + 1) / os
    h = np.zeros_like(n)
    for i, t in enumerate(n):
        if abs(t) < 1e-12:
            h[i] = 1.0
        elif rolloff > 0 and abs(abs(t) - 1.0 / (2.0 * rolloff)) < 1e-9:
            h[i] = (np.pi / 4.0) * np.sinc(1.0 / (2.0 * rolloff))
        else:
            h[i] = np.sinc(t) * np.cos(np.pi * rolloff * t) / (
                1.0 - (2.0 * rolloff * t) ** 2)

    # "same" returns the kernel-centred part, so the main cursor stays at
    # index ``latency``. Slicing the *full* convolution instead would keep only
    # the first half -- which, for a symmetric kernel, is the part before the
    # response starts, and the function would return numerical noise.
    out = np.convolve(fine, h, mode="same")
    peak = np.max(np.abs(out))
    return out / peak if peak else out


def _rc_kernel(u: float, rolloff: float) -> float:
    """The raised-cosine interpolation kernel at one offset.

    Written with explicit branches rather than array masks: the kernel has two
    removable singularities (u = 0 and u = +/- 1 / (2a)) and evaluating the
    general expression there produces a divide-by-zero that NumPy's ``where``
    does not rescue -- both branches of a ``where`` are evaluated, so the
    singular value poisons the result.
    """
    if abs(u) < 1e-9:
        return 1.0
    if rolloff > 0 and abs(abs(u) - 1.0 / (2.0 * rolloff)) < 1e-9:
        return float((np.pi / 4.0) * np.sinc(1.0 / (2.0 * rolloff)))
    return float(np.sinc(u) * np.cos(np.pi * rolloff * u)
                 / (1.0 - (2.0 * rolloff * u) ** 2))


def _sample_pulse(taps: dict, t: np.ndarray,
                  rolloff: float = 0.5) -> np.ndarray:
    """The impulse response reconstructed from symbol offset -> tap.

    Band-limited interpolation with a raised-cosine kernel, written so the taps
    *are* the response: at every integer symbol offset the result is exactly
    ``taps``. That property is what lets the eye below be derived from the same
    numbers the figure prints, rather than from a separately filtered waveform
    that may not agree with it.

    The mapping is a dict precisely so the offsets cannot be paired with the
    wrong taps. Written as two parallel lists this is a one-line bug that
    silently returns a plausible but wrong pulse.
    """
    return np.array([
        sum(tap * _rc_kernel(float(tt - kj), rolloff)
            for kj, tap in taps.items())
        for tt in t])


def serdes_pulse_response() -> str:
    """The pulse response, and the eye it produces before any equalisation.

    The eye is not drawn from a separately-simulated waveform. For a linear
    channel the received sample at any instant is the symbol stream convolved
    with the pulse, and this figure evaluates exactly that sum:

        y(t + kT) = sum_j  a[k-j] * h(t + jT)

    so a sample at t = 0 *is* the main cursor and the terms at j != 0 *are* the
    ISI. The two panels therefore cannot disagree: the eye is the pulse above
    it, summed over every symbol pattern the sequence happens to contain.
    """
    import math

    # The channel, as symbol offset -> tap. These numbers *are* the response;
    # the eye and the stem plot below are both derived from them.
    # A representative 26 GHz lane at the slicer, before receive equalisation:
    # a small pre-cursor, a post-cursor tail that decays over about six
    # symbols, and a total ISI whose worst case is about 11 dB below the main
    # cursor -- which is what leaves an eye worth equalising.
    pulse = {-3: 0.004, -2: 0.012, -1: 0.045, 0: 1.000,
             1: 0.260, 2: 0.120, 3: 0.060, 4: 0.030, 5: 0.015,
             6: 0.008, 7: 0.004}
    k = np.array(sorted(pulse))
    taps = np.array([pulse[kj] for kj in k])
    main = int(np.where(k == 0)[0][0])         # index of h[0] within ``k``

    rng = np.random.default_rng(11)
    levels = np.array([-1.0, 1.0])
    sym = rng.choice(levels, size=NSYM)

    # Sample times within one unit interval, relative to the symbol instant.
    t_ui = np.linspace(-0.5, 0.5, OS + 1)
    trace_idx = rng.integers(SPAN, NSYM - SPAN, size=N_TRACES)
    keep = np.unique(np.linspace(0, len(t_ui) - 1,
                                 DRAW_POINTS).round().astype(int))

    # y((m + u)T) = sum_j a[m + j] * h(u - j). ``_sample_pulse`` returns a
    # *time series* per tap, so the result is transposed into (tap x time)
    # before it multiplies the symbol vector. Without the transpose the eye is
    # the mirror image of the truth and never opens.
    # ``_sample_pulse`` returns one time series per tap, giving (tap, time);
    # the symbol vector multiplies from the left, so no transpose is needed
    # here -- the matrix is already in the orientation the product wants.
    shift_grid = np.stack([_sample_pulse(pulse, t_ui - kj)
                           for kj in k])

    traces = []
    for centre in trace_idx:
        vals = sym[centre + k] @ shift_grid
        traces.append(vals + rng.normal(0.0, 0.03, vals.shape))
    traces = np.array(traces)

    fig, axes = P.figure(height=4.6, nrows=2, height_ratios=[1.0, 1.6])
    ax_top, ax_eye = axes

    # --- top: the pulse response ---
    markerline, stemlines, baseline = ax_top.stem(k, taps, basefmt=" ")
    markerline.set_color(P.ACCENT)
    markerline.set_markersize(6)
    stemlines.set_color(P.ACCENT)
    stemlines.set_linewidth(2.0)
    baseline.set_visible(False)
    ax_top.axhline(0, color=P.RULE, lw=1.0)
    ax_top.axvline(0, color=P.OPTICAL, lw=1.3, ls=(0, (5, 4)))
    ax_top.annotate("main cursor h[0]", xy=(0, taps[main]), xytext=(10, 6),
                    textcoords="offset points", fontsize=8.6,
                    color=P.OPTICAL_DARK, weight="bold")
    ax_top.annotate("post-cursor h[1], h[2], ...", xy=(1, taps[main + 1]),
                    xytext=(16, -4), textcoords="offset points", fontsize=8.6,
                    color=P.WARN, weight="bold")
    P.title(ax_top, "The pulse response a SerDes characterises",
            subtitle="samples at the symbol rate; the tail is what every "
                     "receive equaliser exists to remove")
    P.tidy(ax_top, xlabel="symbol index", ylabel="amplitude")
    ax_top.set_xlim(-4.5, 8.5)
    ax_top.set_ylim(-0.1, 1.15)

    # --- bottom: the eye that pulse produces ---
    segments = np.stack([np.column_stack([t_ui[keep], seg[keep]])
                         for seg in traces])
    ax_eye.add_collection(LineCollection(segments, colors=P.ACCENT,
                                         linewidths=0.5, alpha=0.16, zorder=2))

    at_centre = traces[:, len(t_ui) // 2]
    upper = at_centre[at_centre > 0]
    lower = at_centre[at_centre <= 0]
    eye_h = float(np.percentile(upper, 1) - np.percentile(lower, 99))
    isi = float(np.sum(np.abs(taps)) - abs(taps[main]))

    ax_eye.axvline(0, color=P.OPTICAL, lw=1.3, ls=(0, (5, 4)), zorder=6)
    ax_eye.axhline(0, color=P.RULE, lw=1.0)
    ax_eye.text(0.012, 0.95,
                f"measured eye height {eye_h:.2f} of a nominal 2.00 "
                f"({20 * np.log10(max(eye_h, 1e-6) / 2.0):.1f} dB)\n"
                f"total post-cursor ISI {isi:.2f}, "
                f"{20 * np.log10(max(isi, 1e-6)):.1f} dB",
                transform=ax_eye.transAxes, fontsize=8.4, color=P.SOFT,
                va="top", family="monospace",
                bbox=dict(boxstyle="round,pad=0.4", facecolor=P.PANEL,
                          edgecolor=P.RULE_SOFT, linewidth=1.0))
    P.title(ax_eye, "The eye it produces, before any receive equalisation")
    P.tidy(ax_eye, xlabel="time (unit intervals)", ylabel="amplitude")
    ax_eye.set_xlim(-0.5, 0.5)
    ax_eye.set_ylim(-1.5, 1.5)
    ax_eye.grid(axis="x", color=P.RULE_SOFT)
    return P.render(fig)


def ctle_response() -> str:
    fig, axes = P.figure(height=3.9, ncols=2)
    ax0, ax1 = axes

    f = np.linspace(0.05, 30.0, 700)

    # channel: a low-pass, -28 dB at 26 GHz
    channel_db = -28.0 * np.sqrt(f / 26.0)
    # CTLE: a shelf that boosts high frequencies, with a finite peak
    # A CTLE is a shelf: unity at DC, rising to a peak around fp, with a zero
    # at fz that sets where the boost starts. Normalised so the peak is exactly
    # peak_db, which is the number a datasheet quotes.
    peak_db = 12.0
    fz, fp = 3.0, 20.0
    ctle_db = peak_db + 10.0 * np.log10(
        (1.0 + (f / fz) ** 2) / (1.0 + (f / fp) ** 2)
        * (1.0 + (fp / fz) ** 2))

    combined = channel_db + ctle_db

    ax0.plot(f, ctle_db, color=P.ACCENT, lw=2.4, label="CTLE")
    ax0.plot(f, -channel_db, color=P.WARN, lw=2.4, ls=(0, (6, 4)),
             label="channel loss (mirrored)")
    ax0.plot(f, combined, color=P.OPTICAL, lw=2.6, label="cascade")
    ax0.axhline(0, color=P.RULE, lw=1.0)
    P.title(ax0, "What the CTLE has to cancel",
            subtitle="the shelf is set to flatten the cascade at the band edge")
    P.tidy(ax0, xlabel="frequency (GHz)", ylabel="gain (dB)", legend=True,
           legend_loc="upper left")
    ax0.set_xlim(0, 30)
    ax0.set_ylim(-32, 20)

    # --- right: the noise cost ---
    # Peaking at high frequency amplifies the noise there. The noise gain is
    # the integral of |H|^2 against a flat noise floor, normalised to the DC
    # gain, which is what makes a CTLE cost signal-to-noise ratio.
    noise_gain = np.sqrt(np.trapezoid((10 ** (ctle_db / 20.0)) ** 2, f)
                         / np.trapezoid(np.ones_like(f), f))
    ax1.bar(["flat\n(no CTLE)", "this CTLE"],
            [0.0, 20 * np.log10(noise_gain)],
            color=[P.MUTED, P.ACCENT], width=0.5, zorder=3)
    ax1.axhline(0, color=P.RULE, lw=1.0)
    ax1.text(1, 20 * np.log10(noise_gain) + 0.3,
             f"+{20*np.log10(noise_gain):.1f} dB\nintegrated noise",
             ha="center", fontsize=9, color=P.ACCENT_DARK, weight="bold")
    P.title(ax1, "The noise the peaking buys",
            subtitle="noise gain, integrated over the band")
    P.tidy(ax1, ylabel="noise gain (dB)")
    ax1.set_ylim(0, max(3.0, 20 * np.log10(noise_gain) * 1.6))
    ax1.grid(axis="x", visible=False)
    return P.render(fig)


FIGURES = {
    "serdes-pulse-response": serdes_pulse_response,
    "ctle-response": ctle_response,
}
