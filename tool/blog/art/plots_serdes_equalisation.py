"""Computed figures for the SerDes equalisation chapter.

    serdes-equaliser-response   channel, CTLE, FFE and their cascade on one set
                                of axes, which is what a real lane look like
    dfe-removes-postcursor      the pulse response before and after a DFE, so
                                the mechanism is a subtraction rather than a
                                sentence

The first figure is the design picture for a whole lane: four filters, one
target, and a residual that is what the eye actually sees.
"""

from __future__ import annotations

import numpy as np

from . import plotstyle as P

# The channel, as symbol-spaced taps. This is the array every curve below is
# derived from, so the residual is measured rather than asserted.
CHANNEL_TAPS = np.array([0.02, 0.06, 0.18, 0.52, 1.00, 0.36, 0.18, 0.09, 0.05,
                         0.03, 0.015, 0.008])
TAP_INDEX = np.arange(len(CHANNEL_TAPS)) - 4          # h[-4] .. h[7]


def serdes_equaliser_response() -> str:
    """Channel, CTLE, FFE and their cascade on one frequency axis.

    Every curve is the *true* decibel response of its block, not a version
    normalised to 0 dB at DC. That matters for the figure's argument: if each
    curve were normalised separately, a CTLE shelf would cancel to a flat line
    (its zero-frequency gain is 1, so dividing by it removes the shelf), and
    the cascade would no longer be the sum of what is drawn.
    """
    fig, ax = P.figure(height=4.0)
    P.title(ax, "One lane, four filters, one target",
            subtitle="a linear equaliser flattens the channel but cannot "
                     "invert it; the residual is what the DFE or MLSE must "
                     "still remove")

    # Plotted to Nyquist only: above half the baud rate the channel's response
    # is an image of itself, and drawing it there invites a misreading.
    BAUD = 28.0                       # GBd
    f = np.linspace(0.05, BAUD / 2.0, 800)

    taps = CHANNEL_TAPS
    k = TAP_INDEX
    # the main cursor is the largest tap; keep the causal part for a low-pass
    main = int(np.argmax(taps))

    def tap_response_db(taps, k, f, baud, *, normalise_at_dc=True):
        z = np.exp(-2j * np.pi * f / baud)
        resp = np.zeros(len(f), dtype=complex)
        for tap, kj in zip(taps, k):
            resp += tap * z ** (-kj)
        gain = np.abs(resp)
        ref = gain[0] if normalise_at_dc else 1.0
        return 20.0 * np.log10(np.maximum(gain / max(ref, 1e-9), 1e-9))

    channel_db = tap_response_db(taps, k, f, BAUD)

    # A CTLE shelf: unity at DC, rising with a zero at fz, flattening after a
    # pole at fp. Not normalised, so the shelf survives.
    peak_db = 16.0
    fz, fp = 3.0, 12.0
    ctle_db = peak_db + 10.0 * np.log10(
        (1.0 + (f / fz) ** 2) / (1.0 + (f / fp) ** 2)
        * (1.0 + (fp / fz) ** 2))
    ctle_db = ctle_db - ctle_db[0]

    # A four-tap receive FFE, chosen as the shape a real link uses.
    ffe_taps = np.array([-0.08, -0.15, 0.50, 1.00])
    ffe_k = np.array([-3, -2, -1, 0])
    ffe_db = tap_response_db(ffe_taps, ffe_k, f, BAUD)

    # In linear gain the cascade is the product; in decibels it is the sum.
    cascade_db = channel_db + ctle_db + ffe_db

    ax.plot(f, channel_db, color=P.WARN, lw=2.4, label="channel")
    ax.plot(f, ctle_db, color=P.ACCENT, lw=2.4, ls=(0, (6, 3)), label="CTLE")
    ax.plot(f, ffe_db, color=P.NOTE, lw=2.4, ls=(0, (2, 3)),
            label="receive FFE")
    ax.plot(f, cascade_db, color=P.OPTICAL, lw=2.8, label="cascade (residual)")

    ax.axhline(0, color=P.RULE, lw=1.0)
    ax.axvline(BAUD / 2.0, color=P.MUTED, lw=1.2, ls=(0, (5, 4)), zorder=2)
    ax.text(BAUD / 2.0, ax.get_ylim()[1] * 0.92, " Nyquist", fontsize=8.4,
            color=P.MUTED, va="top", weight="bold")

    residual = float(np.interp(BAUD / 2.0, f, cascade_db))
    ax.annotate(f"residual at Nyquist: {residual:+.1f} dB",
                xy=(BAUD / 2.0, residual), xytext=(-12, 22),
                textcoords="offset points", fontsize=9, color=P.OPTICAL_DARK,
                weight="bold", ha="right",
                bbox=dict(boxstyle="round,pad=0.35", facecolor=P.PANEL,
                          edgecolor=P.RULE_SOFT, linewidth=1.0))

    P.tidy(ax, xlabel="frequency (GHz)", ylabel="gain (dB)", legend=True,
           legend_loc="lower left")
    ax.set_xlim(0, BAUD / 2.0)
    return P.render(fig)


def dfe_removes_postcursor() -> str:
    fig, axes = P.figure(height=3.9, ncols=2)
    ax0, ax1 = axes

    taps = CHANNEL_TAPS
    k = TAP_INDEX

    markerline, stemlines, baseline = ax0.stem(k, taps, basefmt=" ")
    markerline.set_color(P.WARN)
    stemlines.set_color(P.WARN)
    stemlines.set_linewidth(2.2)
    baseline.set_visible(False)
    ax0.axhline(0, color=P.RULE, lw=1.0)
    ax0.axvline(0, color=P.OPTICAL, lw=1.2, ls=(0, (5, 4)))
    P.title(ax0, "Before the DFE",
            subtitle="main cursor at h[0], post-cursor tail behind it")
    P.tidy(ax0, xlabel="symbol offset", ylabel="amplitude")
    ax0.set_xlim(-4.6, 7.6)
    ax0.set_ylim(-0.05, 1.15)

    # the DFE subtracts weighted decided bits: the same taps, negated
    dfe_taps = np.zeros_like(taps)
    for i in range(len(taps)):
        if k[i] > 0:
            dfe_taps[i] = -taps[i]
    residual = taps + dfe_taps

    markerline, stemlines, baseline = ax1.stem(k, residual, basefmt=" ")
    markerline.set_color(P.ACCENT)
    stemlines.set_color(P.ACCENT)
    stemlines.set_linewidth(2.2)
    baseline.set_visible(False)
    ax1.axhline(0, color=P.RULE, lw=1.0)
    ax1.axvline(0, color=P.OPTICAL, lw=1.2, ls=(0, (5, 4)))
    P.title(ax1, "After the DFE",
            subtitle="every post-cursor set to zero; the main cursor is "
                     "untouched")
    P.tidy(ax1, xlabel="symbol offset", ylabel="amplitude")
    ax1.set_xlim(-4.6, 7.6)
    ax1.set_ylim(-0.05, 1.15)

    before = float(np.sum(np.abs(taps)) - abs(taps[4]))
    after = float(np.sum(np.abs(residual)) - abs(residual[4]))
    fig.text(0.5, 0.015,
             f"total post-cursor ISI: {before:.3f} before, {after:.3f} after "
             f"({20*np.log10(before/max(after,1e-9)):.0f} dB better)",
             ha="center", fontsize=8.6, color=P.SOFT)
    return P.render(fig)


FIGURES = {
    "serdes-equaliser-response": serdes_equaliser_response,
    "dfe-removes-postcursor": dfe_removes_postcursor,
}
