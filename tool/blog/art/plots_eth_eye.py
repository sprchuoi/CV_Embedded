"""Computed figures for the eye-diagram chapter.

    ethernet-eye-diagram   a real NRZ eye: many filtered traces, with the eye
                           height and width measured off the same array
    pam4-eye-diagram       the same channel carrying four levels

Model
-----
The transmit pulse is a root-raised-cosine of ``SPAN`` symbols; the channel is
a one-pole low-pass; the receiver is a matched filter. The path is *not*
equalised -- the point of the chapter is what the channel does before the
equaliser, so the closure visible here is the ISI an FFE has to remove.

Normalisation is by the cascade's DC gain, not by the realised peak: dividing
by the peak of one realisation would make the figure depend on how many
symbols that realisation happened to contain.
"""

from __future__ import annotations

import numpy as np
from matplotlib.collections import LineCollection
from scipy.special import erfc

from . import plotstyle as P

SPAN = 24                # symbols in the pulse and the channel model
OS = 32                  # samples per symbol on the model grid
NSYM = 3000              # symbols simulated
ROLLOFF = 0.5            # raised-cosine excess bandwidth

# The channel's corner, in cycles per sample: a 4th-order Butterworth at
# 0.042 * f_sample, which is about 1.34 * the symbol rate. Narrower than this
# and the eye shuts completely; wider and the closure is invisible.
CHANNEL_FC = 0.042

# Drawn traces and drawn points per trace. Every trace is a stroked path in the
# SVG, so the drawn point count decides the file size: 800 traces at full grid
# resolution produced a 2.1 MB figure.
N_TRACES = 140
DRAW_POINTS = 41


def _rrc(span: int, os: int, rolloff: float) -> np.ndarray:
    """Raised-cosine impulse response on an ``os``-oversampled grid.

    A raised cosine, not a root-raised cosine. Its samples at every non-zero
    symbol offset are exactly zero, so with an ideal channel the eye here would
    be perfectly open and *any* closure in the figures is unambiguously the
    channel's doing. A root-raised cosine has substantial sidelobes at the
    symbol offsets -- about -20 dB at +/-1 symbol -- which fold to almost
    nothing but make the intermediate arithmetic confusing to read.
    """
    n = np.arange(-span * os // 2, span * os // 2 + 1) / os
    h = np.zeros_like(n, dtype=float)
    for i, t in enumerate(n):
        if abs(t) < 1e-12:
            h[i] = 1.0
        elif rolloff > 0 and abs(abs(t) - 1.0 / (2.0 * rolloff)) < 1e-9:
            h[i] = (np.pi / 4.0) * np.sinc(1.0 / (2.0 * rolloff))
        else:
            num = np.sinc(t) * np.cos(np.pi * rolloff * t)
            den = 1.0 - (2.0 * rolloff * t) ** 2
            h[i] = num / den
    return h / h.max()


def _butterworth_lp(fc: float, order: int = 4):
    """A Butterworth low-pass at ``fc`` in cycles/sample, for the channel.

    A flat-amplitude, sharp-cutoff channel. Both properties matter to the
    figure: a gentle one-pole rolloff leaves the folded taps almost unchanged,
    which is not the lesson the chapter is teaching.
    """
    from scipy import signal
    return signal.butter(order, fc, btype="low", output="ba")


def _one_pole(fc: float, span: int, os: int) -> np.ndarray:
    """A one-pole low-pass channel on the same grid, unit DC gain.

    ``fc`` is the pole position per sample: 0.52 means the response decays to
    52% each sample, which is a corner at roughly a quarter of the sample rate.
    """
    n = np.arange(0, span * os + 1)
    h = fc ** n
    return h / h.sum()


def _cascade_peak(fc: float, span: int, os: int):
    """The transmit pulse through the channel, and the index of its peak.

    Deliberately *not* followed by a matched filter. A matched receiver would
    restore the Nyquist property and the eye would open perfectly, which is
    exactly the thing this chapter is not showing: the figures are the
    unequalised link an FFE is asked to fix.
    """
    from scipy import signal

    tx = _rrc(span, os, ROLLOFF)
    b, a = _butterworth_lp(fc)
    h = signal.lfilter(b, a, tx)
    delay = int(np.argmax(h))
    return h, delay


def _link(symbols: np.ndarray, fc: float, span: int, os: int):
    """Symbols through the pulse and the channel, at the oversampled rate.

    Normalised by the peak of the combined response, so a long run of equal
    symbols settles at that symbol's amplitude and the residual at the
    neighbouring sampling instants is the ISI the equaliser has to remove.
    """
    h, delay = _cascade_peak(fc, span, os)
    h = h / h[delay]

    up = np.zeros(len(symbols) * os + span * os + 1)
    up[:len(symbols) * os:os] = symbols
    y = np.convolve(up, h)[:len(up)]
    return y, delay


def _eye_panels(levels: np.ndarray, fc: float, noise: float, n_traces: int,
                title: str, subtitle: str, *, seed: int):
    rng = np.random.default_rng(seed)
    symbols = rng.choice(levels, size=NSYM)
    rx, delay = _link(symbols, fc, SPAN, OS)

    half = OS // 2
    # The slicer samples at the cascade peak, so symbol k lands at k*OS + delay.
    centres = np.arange(SPAN * OS, len(symbols) * OS - SPAN * OS, OS) + delay

    traces = []
    for c in centres[:n_traces]:
        seg = rx[c - half:c + half + 1]
        if len(seg) == 2 * half + 1:
            traces.append(seg + rng.normal(0.0, noise, seg.shape))
    traces = np.array(traces)
    t_ui = np.linspace(-0.5, 0.5, traces.shape[1])

    fig, ax_eye = P.figure(height=5.4)
    P.setup()
    # one wide axes for the eye, two narrower ones beneath it: a vertical
    # histogram of the opening, and the bathtub. Placed explicitly because the
    # eye has to span the full width above both, and the gap is sized so the
    # eye's own x-label clears the two titles below it.
    ax_eye.set_position([0.075, 0.43, 0.90, 0.44])
    ax_h = fig.add_axes([0.075, 0.12, 0.34, 0.18])
    ax_t = fig.add_axes([0.56, 0.12, 0.41, 0.18])

    # One LineCollection rather than n_traces separate plot calls, so the whole
    # family is a single vector path instead of hundreds of them.
    keep = np.unique(np.linspace(0, traces.shape[1] - 1,
                                 DRAW_POINTS).round().astype(int))
    segments = np.stack([np.column_stack([t_ui[keep], seg[keep]])
                         for seg in traces])
    ax_eye.add_collection(LineCollection(segments, colors=P.ACCENT,
                                         linewidths=0.5, alpha=0.16, zorder=2))

    # measure the eye at the sampling instant, using the usual 1%/99% points
    at_centre = traces[:, traces.shape[1] // 2]
    open_levels = np.sort(np.unique(levels))
    gaps = []
    for lo, hi in zip(open_levels[:-1], open_levels[1:]):
        mid = (lo + hi) / 2.0
        upper = at_centre[at_centre > mid]
        lower = at_centre[at_centre <= mid]
        if len(upper) > 5 and len(lower) > 5:
            gaps.append(float(np.percentile(upper, 1)
                              - np.percentile(lower, 99)))
    eye_h = min(gaps) if gaps else 0.0

    nominal = float(open_levels[1] - open_levels[0])
    ax_eye.axvline(0, color=P.OPTICAL, lw=1.2, ls=(0, (6, 4)), zorder=6)
    for lv in open_levels:
        ax_eye.axhline(lv, color=P.RULE, lw=0.9, ls=(0, (3, 4)), zorder=1)
    ax_eye.text(0.012, 0.96,
                f"measured eye height {eye_h:.2f} of a nominal {nominal:.2f} "
                f"({20 * np.log10(max(eye_h, 1e-6) / nominal):.1f} dB)",
                transform=ax_eye.transAxes, fontsize=8.4, color=P.SOFT,
                va="top", family="monospace",
                bbox=dict(boxstyle="round,pad=0.4", facecolor=P.PANEL,
                          edgecolor=P.RULE_SOFT, linewidth=1.0))
    P.title(ax_eye, title, subtitle=subtitle)
    P.tidy(ax_eye, xlabel="time (unit intervals)", ylabel="amplitude")
    ax_eye.set_xlim(-0.5, 0.5)
    top = float(np.max(open_levels)) * 1.35
    ax_eye.set_ylim(-top, top)
    ax_eye.grid(axis="x", color=P.RULE_SOFT)

    # vertical histogram inside the opening
    ax_h.hist(at_centre, bins=48, orientation="horizontal", color=P.NOTE,
              alpha=0.75, zorder=3)
    P.title(ax_h, "vertical slice at t = 0")
    P.tidy(ax_h, xlabel="counts")
    ax_h.set_ylim(-top, top)
    ax_h.grid(axis="y", visible=False)

    # the bathtub: an estimated BER against sampling phase. The estimate treats
    # the residual ISI as Gaussian, which is the usual engineering
    # approximation and is optimistic at the eye edges -- the text says so.
    phases = np.linspace(-0.5, 0.5, 121)
    errors = []
    for ph in phases:
        idx = int(round((ph + 0.5) * OS)) + traces.shape[1] // 2 - OS // 2
        idx = min(max(idx, 0), traces.shape[1] - 1)
        col = traces[:, idx]
        d = np.min(np.abs(col[:, None] - open_levels[None, :]), axis=1)
        isi = float(np.sqrt(np.mean(d ** 2)))
        q = (0.5 * nominal - d.mean()) / max(
            np.sqrt(noise ** 2 + isi ** 2), 1e-9)
        errors.append(0.5 * float(erfc(max(q, 0.0) / np.sqrt(2))))
    errors = np.maximum(np.array(errors), 1e-18)

    ax_t.semilogy(phases, errors, color=P.OPTICAL, lw=2.2, zorder=4)
    for lvl, label in ((1e-4, "10\u207b\u2074"),
                       (1e-12, "10\u207b\u00b9\u00b2")):
        ax_t.axhline(lvl, color=P.RULE, lw=1.1, ls=(0, (4, 4)), zorder=2)
        ax_t.text(0.5, lvl, f" {label}", fontsize=8, color=P.MUTED,
                  va="bottom", ha="left")
    P.title(ax_t, "bathtub: estimated BER against sampling phase")
    P.tidy(ax_t, xlabel="sampling phase (UI)", ylabel="BER")
    ax_t.set_xlim(-0.5, 0.5)
    ax_t.grid(which="minor", visible=False)
    return P.render(fig)


def ethernet_eye_diagram() -> str:
    return _eye_panels(
        np.array([-1.0, 1.0]), CHANNEL_FC, 0.075, N_TRACES,
        "A real NRZ eye through a bandwidth-limited channel",
        f"{N_TRACES} traces; the closure at the crossings is inter-symbol "
        "interference, the blur along the rails is noise",
        seed=1)


def pam4_eye_diagram() -> str:
    return _eye_panels(
        np.array([-1.0, -1 / 3, 1 / 3, 1.0]), CHANNEL_FC, 0.045, N_TRACES,
        "The same channel carrying PAM4",
        "three eyes, a third the height each; the middle eye closes first "
        "because it is bounded by two transitions",
        seed=2)


FIGURES = {
    "ethernet-eye-diagram": ethernet_eye_diagram,
    "pam4-eye-diagram": pam4_eye_diagram,
}
