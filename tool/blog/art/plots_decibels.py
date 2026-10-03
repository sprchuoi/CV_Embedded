"""Computed figures for the decibels and dynamic range chapter.

Three numpy/matplotlib figures, in the order the article uses them:

    db-linear-vs-log           one amplifier spectrum: linear axis, then dB axis
    cascade-noise-figure       Friis, and which stage of a chain owns the noise
    dynamic-range-by-format    word length against usable dynamic range

The chapter's argument is that dB arithmetic is not decoration. Figure 1 draws a
single array twice, so the reader sees how much of a spectrum a linear axis
flattens. Figure 2 multiplies noise factors and gains as *linear power ratios*
and takes ``10 log10`` only to label an axis -- doing that arithmetic in dB is
the mistake the figure exists to warn about, and the annotation says so.
Figure 3 puts the formulas and the silicon on one scale, so the gap between them
is a length rather than a sentence.

Every number an annotation quotes is measured on the array its curve is drawn
from, and :func:`_diagnostics` prints all of them. The only stochastic
ingredient is figure 1's seeded analyser ripple; rebuilds are reproducible.
"""

from __future__ import annotations

import numpy as np

from . import plotstyle as P

# Rebuilds must be reproducible; see the module docstring.
RNG = np.random.default_rng(0)


# --------------------------------------------------------------------------- #
# local helpers
# --------------------------------------------------------------------------- #


def _head(ax, title, subtitle=None):
    """Title plus a subtitle that clears it (see ``plots_sampling._head``)."""
    if subtitle is None:
        P.title(ax, title)
        return
    ax.set_title(title, pad=22)
    ax.text(0.0, 1.012, subtitle, transform=ax.transAxes, fontsize=9,
            color=P.MUTED, va="bottom")


def _numbers(ax, rows, x, y, *, colour=P.SOFT, size=8.0, ha="left", va="top"):
    """A monospace box for numbers, parked in space no curve occupies."""
    ax.text(x, y, "\n".join(rows), family="monospace", fontsize=size,
            color=colour, ha=ha, va=va, zorder=8,
            bbox=dict(boxstyle="round,pad=0.45", facecolor=P.PANEL,
                      edgecolor=P.RULE_SOFT, linewidth=1.0))


def _chip(ax, x, y, text, colour, *, size=8.4, ha="left", va="center"):
    """A label that has to sit on a filled band: opaque, no edge."""
    return ax.text(x, y, text, color=colour, fontsize=size, ha=ha, va=va,
                   zorder=9,
                   bbox=dict(boxstyle="round,pad=0.30", facecolor=P.PANEL,
                             edgecolor="none"))


def _rule(ax, x, *, colour=P.RULE, lw=1.1):
    ax.axvline(x, color=colour, lw=lw, ls=(0, (3, 3)), zorder=1)


# --------------------------------------------------------------------------- #
# 1. the same spectrum on a linear axis, then on a dB axis
# --------------------------------------------------------------------------- #

SPAN_MHZ = 12.0                 # half-span of the sweep
SWEEP_POINTS = 6001             # 4 kHz per point
TONE_OFFSET_MHZ = 2.5           # the two tones straddle the carrier
TONE_DBC = (0.0, -0.5)          # equal-ish drive: the classic two-tone test
IM3_DBC = (-55.0, -55.4)        # third-order products, set explicitly
PEDESTAL_DBC = -80.0            # in-band input-noise pedestal
FILTER_HALF_MHZ = 4.0           # input bandpass: half width at the 3 dB point
FILTER_ORDER = 4
LINE_HALF_MHZ = 0.4             # resolution bandwidth: how wide a line is drawn
SPUR_OFFSET_MHZ = 3.0 * TONE_OFFSET_MHZ       # 2*f2 - f1 = +7.5 MHz, and mirror

# The analyser ripple is drawn once, here, rather than inside the builder: a
# module-level generator that is advanced on every call would make a second
# render in the same process differ from the first, and CI compares the
# committed SVG with a fresh one byte for byte.
RIPPLE = 10.0 ** (RNG.normal(0.0, 0.30, SWEEP_POINTS) / 20.0)


def _dbc_to_power(dbc):
    """dBc -> linear power ratio. These are the only dB conversions in figure 1."""
    return 10.0 ** (np.asarray(dbc, dtype=float) / 10.0)


def _line(f, centre, half_width):
    """A raised cosine of unit height: one resolution-bandwidth-wide line."""
    out = np.zeros_like(f)
    inside = np.abs(f - centre) <= half_width
    out[inside] = 0.5 * (1.0 + np.cos(np.pi * (f[inside] - centre) / half_width))
    return out


def _two_tone_spectrum():
    """The output trace, plus every level the annotations on figure 1 quote.

    The tones and the intermodulation products are set explicitly rather than
    grown from a polynomial: the figure's subject is the *scale* the spurs live
    on, and fitting a coefficient would only put arithmetic between the reader
    and that. The input bandpass shapes the noise; the spurs are generated in
    the output stage, downstream of the filter, so they keep their set levels.
    """
    f = np.linspace(-SPAN_MHZ, SPAN_MHZ, SWEEP_POINTS)

    # A 4th-order skirt is 38 dB down by the edge of the sweep -- which is what
    # makes it the convincing half of this figure's argument.
    skirt = 1.0 / (1.0 + (np.abs(f) / FILTER_HALF_MHZ) ** (2 * FILTER_ORDER))

    # Seeded analyser ripple, on the pedestal only: the tones are coherent.
    amplitude = np.sqrt(_dbc_to_power(PEDESTAL_DBC) * skirt) * RIPPLE

    for centre, dbc in ((-TONE_OFFSET_MHZ, TONE_DBC[0]),
                        (TONE_OFFSET_MHZ, TONE_DBC[1])):
        amplitude = amplitude + np.sqrt(_dbc_to_power(dbc)) * _line(
            f, centre, LINE_HALF_MHZ)
    for centre, dbc in ((-SPUR_OFFSET_MHZ, IM3_DBC[0]),
                        (SPUR_OFFSET_MHZ, IM3_DBC[1])):
        amplitude = amplitude + np.sqrt(_dbc_to_power(dbc)) * _line(
            f, centre, LINE_HALF_MHZ)

    db = 20.0 * np.log10(np.maximum(amplitude, 1e-12))

    def at(mhz):
        return float(db[int(np.argmin(np.abs(f - mhz)))])

    in_band = np.abs(f) <= 1.5          # the flat pedestal, clear of both tones
    readings = {
        "tone": (at(-TONE_OFFSET_MHZ), at(TONE_OFFSET_MHZ)),
        "im3": (at(-SPUR_OFFSET_MHZ), at(SPUR_OFFSET_MHZ)),
        "pedestal": float(np.median(db[in_band])),
        "skirt": at(SPAN_MHZ),
        "peak": float(amplitude.max()),
    }
    return f, amplitude, readings


def db_linear_vs_log() -> str:
    """One amplifier output spectrum: invisible on a linear axis, obvious in dB."""
    f, amplitude, readings = _two_tone_spectrum()
    db = 20.0 * np.log10(np.maximum(amplitude, 1e-12))
    tone_left, tone_right = readings["tone"]
    im3_left, im3_right = readings["im3"]
    pedestal_db = readings["pedestal"]
    skirt_db = readings["skirt"]

    fig, axes = P.figure(height=5.2, nrows=2, sharex=True, hspace=0.50,
                         height_ratios=[1.0, 1.3])
    top, bottom = axes

    # --- top: everything is here, and almost none of it can be seen ---------
    top.plot(f, amplitude, color=P.ACCENT, lw=1.5, zorder=4)
    top.set_xlim(-13.0, 19.0)
    top.set_ylim(0.0, 1.22)
    top.set_yticks([0.0, 0.25, 0.50, 0.75, 1.00])

    top.text(-12.6, 1.19, "visible: the two tones", color=P.INK, fontsize=8.6,
             ha="left", va="top")
    top.text(-12.6, 1.05, "drawn, invisible:", color=P.SOFT, fontsize=8.4,
             ha="left", va="top")
    top.text(-12.6, 0.93,
             "IM3 spurs      " + f"{im3_left:.1f} dBc",
             family="monospace", color=P.NOTE, fontsize=7.8, ha="left", va="top")
    top.text(-12.6, 0.82,
             "pedestal       " + f"{pedestal_db:.1f} dBc",
             family="monospace", color=P.NOTE, fontsize=7.8, ha="left", va="top")
    top.text(-12.6, 0.71,
             "skirt          " + f"{skirt_db:.1f} dBc",
             family="monospace", color=P.NOTE, fontsize=7.8, ha="left", va="top")
    top.annotate("", xy=(-8.6, 0.004), xytext=(-7.0, 0.60),
                 arrowprops=dict(arrowstyle="->", color=P.INK, lw=1.0,
                                 shrinkA=2, shrinkB=1))
    top.text(-6.4, 0.34, "not zero here", color=P.INK, fontsize=8.4,
             ha="left", va="center")

    _head(top, "The same spectrum on a linear magnitude axis",
          "two tones at " + f"+/-{TONE_OFFSET_MHZ:.1f} MHz"
          " through a mildly nonlinear amplifier")
    P.tidy(top, ylabel="amplitude relative to the peak tone")

    # --- bottom: the identical array, in dB ---------------------------------
    bottom.plot(f, db, color=P.ACCENT, lw=1.4, zorder=4)
    bottom.set_ylim(-130.0, 14.0)
    bottom.set_yticks(np.arange(-120.0, 1.0, 20.0))

    bottom.annotate("two tones: " + f"{tone_left:.1f} and {tone_right:.1f} dBc",
                    xy=(TONE_OFFSET_MHZ, 0.5), xytext=(0.0, 7.0),
                    ha="center", va="bottom", color=P.NOTE, fontsize=8.8,
                    arrowprops=dict(arrowstyle="->", color=P.NOTE, lw=1.0,
                                    shrinkA=2, shrinkB=2))
    bottom.annotate("", xy=(-TONE_OFFSET_MHZ, 0.5), xytext=(0.0, 7.0),
                    arrowprops=dict(arrowstyle="->", color=P.NOTE, lw=1.0,
                                    shrinkA=2, shrinkB=2))

    # The pedestal label sits to the left, where the leader can reach the flat
    # part of the trace without crossing either the tones or the IM3 spurs.
    bottom.annotate("noise pedestal\n" + f"{pedestal_db:.1f} dBc in band",
                    xy=(-4.0, -83.0), xytext=(-12.8, -44.0),
                    ha="left", va="center", color=P.MUTED, fontsize=8.4,
                    arrowprops=dict(arrowstyle="->", color=P.MUTED, lw=1.0,
                                    shrinkA=3, shrinkB=2))

    margin = [
        ("IM3 spurs", f"{im3_left:.1f} and {im3_right:.1f} dBc",
         (SPUR_OFFSET_MHZ, im3_right), P.WARN, -34.0),
        ("stopband skirt", f"{skirt_db:.1f} dB at the edge",
         (10.4, -113.0), P.OPTICAL, -102.0),
    ]
    for name, value, xy, colour, y in margin:
        bottom.annotate(name + "\n" + value, xy=xy, xytext=(13.0, y),
                        ha="left", va="center", color=colour, fontsize=8.2,
                        arrowprops=dict(arrowstyle="->", color=colour, lw=1.0,
                                        shrinkA=3, shrinkB=2))

    _head(bottom, "The identical data on a dB axis",
          "the same array, 20 log10 -- "
          + f"{tone_left - skirt_db:.0f} dB of range the linear axis flattened")
    P.tidy(bottom, xlabel="frequency offset from the carrier (MHz)",
           ylabel="output level (dBc)")
    return P.render(fig)


# --------------------------------------------------------------------------- #
# 2. Friis: which stage of the chain owns the noise
# --------------------------------------------------------------------------- #

NF_LATER_DB = 10.0            # stages 2 and 3
G2_DB = 10.0                  # inter-stage gain, used by the Friis terms
G3_DB = 10.0                  # stated for completeness; the NF does not use it
G1_DB = np.linspace(0.0, 30.0, 601)
DOMINANCE_DB = 0.5            # "the first stage dominates" means within this


def _lin(db):
    """dB -> linear power ratio. The only dB conversion in figure 2."""
    return 10.0 ** (np.asarray(db, dtype=float) / 10.0)


def _friis_terms(g1_db, nf1_db):
    """The three Friis terms of the cascade noise factor, in linear power.

    ``F = F1 + (F2-1)/G1 + (F3-1)/(G1*G2)``, every quantity a power ratio.
    """
    g1 = _lin(g1_db)
    f1 = float(_lin(nf1_db))
    f2 = float(_lin(NF_LATER_DB))
    f3 = float(_lin(NF_LATER_DB))
    g2 = float(_lin(G2_DB))
    return (np.full_like(g1, f1), (f2 - 1.0) / g1, (f3 - 1.0) / (g1 * g2))


def _friis_total(g1_db, nf1_db):
    terms = _friis_terms(g1_db, nf1_db)
    return sum(terms), terms


def _dominance_gain_db(nf1_db):
    """First-stage gain at which the cascade NF is within 0.5 dB of ``nf1_db``.

    The two later terms are ``(F2-1)/G1 + (F3-1)/(G1*G2) = 9.9/G1`` for the
    numbers used here, so the crossing solves in closed form.
    """
    f1 = float(_lin(nf1_db))
    allowed = float(_lin(nf1_db + DOMINANCE_DB)) - f1
    rest = (float(_lin(NF_LATER_DB)) - 1.0) * (1.0 + 1.0 / float(_lin(G2_DB)))
    return 10.0 * np.log10(rest / allowed)


def cascade_noise_figure() -> str:
    """A three-stage receiver: cascade NF against first-stage gain, in dB."""
    cases = ((1.0, P.ACCENT, "first stage NF = 1 dB"),
             (6.0, P.WARN, "first stage NF = 6 dB"))

    fig, axes = P.figure(height=5.9, nrows=2, sharex=True, hspace=0.55,
                         height_ratios=[1.2, 1.0])
    top, bottom = axes

    ends = {}
    for nf1_db, colour, label in cases:
        total, _ = _friis_total(G1_DB, nf1_db)
        nf_db = 10.0 * np.log10(total)
        ends[nf1_db] = (float(nf_db[0]), float(nf_db[-1]))

        top.plot(G1_DB, nf_db, color=colour, lw=2.1, zorder=4, label=label)
        top.axhline(nf1_db, color=colour, lw=1.0, ls=(0, (2, 3)), zorder=1)
        gain_db = _dominance_gain_db(nf1_db)
        _rule(top, gain_db, colour=P.RULE, lw=1.0)
        top.plot([gain_db], [nf1_db + DOMINANCE_DB], marker="o", ls="none",
                 ms=6.5, color=colour, mec=P.PANEL, mew=1.4, zorder=6)

    top.set_xlim(0.0, 30.0)
    top.set_ylim(0.0, 13.8)
    top.set_yticks([0, 2, 4, 6, 8, 10, 12])

    # Each curve is labelled along its own asymptote rather than through a
    # legend box: the only corner a legend would fit in is the lower left, which
    # is exactly where the 1 dB curve dives through.
    top.text(29.5, 1.9, "first stage NF = 1 dB", color=P.ACCENT, fontsize=8.8,
             ha="right", va="bottom")
    top.text(29.5, 7.4, "first stage NF = 6 dB", color=P.WARN, fontsize=8.8,
             ha="right", va="bottom")

    low0, low1 = ends[1.0]
    bad0, bad1 = ends[6.0]
    gain_low = _dominance_gain_db(1.0)
    gain_bad = _dominance_gain_db(6.0)
    owned = 100.0 * float(_lin(1.0)) / float(_lin(1.0 + DOMINANCE_DB))

    # The number boxes go where the two curves leave space: the corner above
    # both of them, and the corner below the 1 dB curve before it dives.
    _numbers(top, [
        "within 0.5 dB of its own NF:",
        "  NF1 = 1 dB at G1 = " + f"{gain_low:.1f} dB",
        "  NF1 = 6 dB at G1 = " + f"{gain_bad:.1f} dB",
    ], 29.2, 13.5, colour=P.INK, ha="right")

    _numbers(top, [
        "computed in linear power ratios:",
        "  NF1 = 1 dB: " + f"{low0:.1f} -> {low1:.2f} dB",
        "  NF1 = 6 dB: " + f"{bad0:.1f} -> {bad1:.2f} dB",
    ], 0.6, 2.9, colour=P.SOFT, ha="left")

    _head(top, "A cascade's noise figure is set by its first stage",
          "stages 2 and 3: NF = " + f"{NF_LATER_DB:.0f} dB, "
          "G2 = " + f"{G2_DB:.0f} dB, G3 = " + f"{G3_DB:.0f} dB"
          " - all arithmetic in linear power ratios")
    P.tidy(top, ylabel="cascade noise figure (dB)")

    # --- bottom: who actually contributes that noise -------------------------
    total, terms = _friis_total(G1_DB, 1.0)
    shares = [100.0 * t / total for t in terms]
    c1, c2 = shares[0], shares[0] + shares[1]
    bottom.fill_between(G1_DB, 0.0, c1, color=P.ACCENT, alpha=0.35, lw=0,
                        zorder=2)
    bottom.fill_between(G1_DB, c1, c2, color=P.NOTE, alpha=0.35, lw=0, zorder=2)
    bottom.fill_between(G1_DB, c2, 100.0, color=P.WARN, alpha=0.35, lw=0,
                        zorder=2)
    for curve, colour in ((c1, P.ACCENT), (c2, P.NOTE)):
        bottom.plot(G1_DB, curve, color=colour, lw=1.8, zorder=4)

    total_bad, terms_bad = _friis_total(G1_DB, 6.0)
    share_bad = 100.0 * terms_bad[0] / total_bad
    bottom.plot(G1_DB, share_bad, color=P.OPTICAL, lw=1.6, ls=(0, (5, 3)),
                zorder=5)

    for gain_db in (gain_low, gain_bad):
        _rule(bottom, gain_db, colour=P.RULE, lw=1.0)

    bottom.set_ylim(0.0, 114.0)
    bottom.set_yticks([0, 25, 50, 75, 100])

    _chip(bottom, 20.0, 22.0, "stage 1 - NF = 1 dB", P.ACCENT)
    _chip(bottom, 1.0, 62.0, "stage 2 - NF = 10 dB", P.NOTE)
    _chip(bottom, 1.0, 96.0, "stage 3 - NF = 10 dB", P.WARN)
    _chip(bottom, 29.6, 92.0, "stage 1 if NF1 = 6 dB", P.OPTICAL, ha="right")
    _chip(bottom, gain_bad - 0.5, 106.0, f"{gain_bad:.1f} dB", P.MUTED,
          ha="right")
    _chip(bottom, gain_low + 0.5, 106.0, f"{gain_low:.1f} dB", P.MUTED,
          ha="left")

    _head(bottom, "Who contributes the noise",
          "shares of the output noise power - at " + f"{gain_low:.1f} dB the first"
          " stage owns " + f"{owned:.0f}% of it")
    P.tidy(bottom, xlabel="gain of the first stage  G1 (dB)",
           ylabel="share of the output noise (%)")
    return P.render(fig)


# --------------------------------------------------------------------------- #
# 3. what each format can actually represent
# --------------------------------------------------------------------------- #

PER_BIT_DB = 6.02             # the ideal-quantiser slope
OFFSET_DB = 1.76              # its intercept: a full-scale sine, error <= 1/2 LSB
FLOAT_SIGNIFICAND_BITS = 24   # IEEE 754 binary32: 23 stored + 1 implicit
FLOAT_MAX = 3.4028235e38
FLOAT_MIN_NORMAL = 1.1754944e-38
FLOAT_EXPONENT_DB = float(20.0 * np.log10(FLOAT_MAX / FLOAT_MIN_NORMAL))
ENOB_OPTICAL = 5.5            # the chapter's realistic optical front end
SAMPLE_RATE_GSPS = 128.0
MEASURED_16_DB = 96.0         # the number every audio engineer quotes
MEASURED_24_DB = 100.0        # a good converter, per the chapter


def _ideal_snr(bits):
    """Ideal SNR of a full-scale sine through a uniform ``bits``-bit quantiser."""
    return PER_BIT_DB * bits + OFFSET_DB


def _format_rows():
    """``(label, ideal dB, measured dB or None, colour)`` for figure 3."""
    return [
        (f"{ENOB_OPTICAL:.1f} ENOB, {SAMPLE_RATE_GSPS:.0f} GSa/s",
         _ideal_snr(ENOB_OPTICAL), None, P.OPTICAL),
        ("8-bit integer ADC", _ideal_snr(8), None, P.ACCENT),
        ("12-bit integer ADC", _ideal_snr(12), None, P.ACCENT),
        ("16-bit audio", _ideal_snr(16), MEASURED_16_DB, P.NOTE),
        ("24-bit audio", _ideal_snr(24), MEASURED_24_DB, P.NOTE),
        ("32-bit float (IEEE 754)", _ideal_snr(FLOAT_SIGNIFICAND_BITS), None,
         P.MUTED),
    ]


def dynamic_range_by_format() -> str:
    """Horizontal bars: the formula's dynamic range against the usable one."""
    rows = _format_rows()
    fig, ax = P.figure(height=5.4)

    labels = []
    for index, (label, ideal, measured, colour) in enumerate(rows):
        y = float(len(rows) - 1 - index)
        labels.append(label)
        ax.barh(y, ideal, height=0.46, color=colour,
                alpha=(0.26 if measured is not None else 1.0), lw=0, zorder=2)
        if measured is not None:
            ax.barh(y, measured, height=0.46, color=P.WARN, lw=0, zorder=3)
            ax.text(measured - 3.0, y, f"{measured:.1f} dB measured",
                    color=P.PANEL, fontsize=8.4, ha="right", va="center",
                    zorder=6)
            ax.annotate("", xy=(ideal, y), xytext=(measured, y),
                        arrowprops=dict(arrowstyle="<->", color=P.INK, lw=1.0,
                                        shrinkA=1, shrinkB=1), zorder=5)
            ax.text(0.5 * (ideal + measured), y + 0.30,
                    f"{ideal - measured:.1f} dB", color=P.INK, fontsize=8.2,
                    ha="center", va="bottom", zorder=6)
        suffix = " ideal" if measured is not None else ""
        ax.text(ideal + 3.0, y, f"{ideal:.1f} dB" + suffix, color=P.INK,
                fontsize=8.6, ha="left", va="center", zorder=6)

    ax.set_yticks([float(len(rows) - 1 - i) for i in range(len(rows))],
                  labels=labels)
    ax.set_xlim(0.0, 215.0)
    ax.set_ylim(-0.7, 6.7)
    ax.tick_params(axis="y", labelsize=9)

    ax.text(2.0, 5.42, "the realistic optical case, on real silicon",
            color=P.OPTICAL, fontsize=8.4, ha="left", va="bottom")

    _numbers(ax, [
        "how each number is defined",
        "ideal N-bit: SNR = 6.02 N + 1.76 dB, full-scale",
        "   sine, quantiser error <= 1/2 LSB",
        "16-bit audio: the usual 96 dB is 16 x 6 dB",
        "24-bit audio: the formula's 146 dB needs a front",
        "   end that the thermal and clock noise floor of",
        "   real silicon stops near 100 dB",
        "32-bit float: a 24-bit significand gives 146 dB",
        "   of relative precision; its "
        + f"{FLOAT_EXPONENT_DB:.0f} dB exponent span",
        "   is range, not resolution",
        "pale bar = the formula, solid = the usable value",
        "the arrow spans measured-to-ideal on a row",
    ], 100.0, 6.55, colour=P.SOFT, size=8.0, ha="left", va="top")

    _head(ax, "Usable dynamic range is not word length",
          "ideal SNR = 6.02 N + 1.76 dB for a full-scale sine; "
          "measured values are the chapter's own")
    P.tidy(ax, xlabel="dynamic range (dB)")
    return P.render(fig)


FIGURES = {
    "db-linear-vs-log": db_linear_vs_log,
    "cascade-noise-figure": cascade_noise_figure,
    "dynamic-range-by-format": dynamic_range_by_format,
}


# --------------------------------------------------------------------------- #
# diagnostics
# --------------------------------------------------------------------------- #


def _diagnostics() -> None:
    """Print every number this module annotates, straight from the arrays."""
    _f, amplitude, readings = _two_tone_spectrum()
    print("db-linear-vs-log")
    print(f"  peak amplitude          {readings['peak']:.4f}"
          f"  -> {20 * np.log10(readings['peak']):+.3f} dBc")
    print(f"  tone left / right       {readings['tone'][0]:.2f} / "
          f"{readings['tone'][1]:.2f} dBc (set {TONE_DBC[0]:.1f} / "
          f"{TONE_DBC[1]:.1f})")
    print(f"  IM3  left / right       {readings['im3'][0]:.2f} / "
          f"{readings['im3'][1]:.2f} dBc (set {IM3_DBC[0]:.1f} / "
          f"{IM3_DBC[1]:.1f})")
    print(f"  pedestal in band        {readings['pedestal']:.2f} dBc "
          f"(set {PEDESTAL_DBC:.1f}, +-0.3 dB seeded ripple)")
    print(f"  skirt at +/-{SPAN_MHZ:.0f} MHz     {readings['skirt']:.2f} dBc"
          f"  => {10 ** (readings['skirt'] / 20):.2e} of the peak amplitude")
    print(f"  IM3 as a fraction       "
          f"{10 ** (readings['im3'][0] / 20):.2e} of the peak amplitude")
    print(f"  range on the dB axis    "
          f"{readings['tone'][0] - readings['skirt']:.0f} dB")
    print(f"  linear panel ylim       0 to 1.22; the pedestal is "
          f"{10 ** (readings['pedestal'] / 20):.2e} of the peak amplitude, "
          f"the skirt {10 ** (readings['skirt'] / 20):.2e}")

    print("cascade-noise-figure")
    print(f"  later stages            NF = {NF_LATER_DB:.0f} dB each, "
          f"G2 = {G2_DB:.0f} dB, G3 = {G3_DB:.0f} dB")
    for nf1_db in (1.0, 6.0):
        total, terms = _friis_total(G1_DB, nf1_db)
        nf_db = 10.0 * np.log10(total)
        share = [100.0 * t / total for t in terms]
        gain = _dominance_gain_db(nf1_db)
        owned = 100.0 * float(_lin(nf1_db)) / float(_lin(nf1_db + DOMINANCE_DB))
        print(f"  NF1 = {nf1_db:.0f} dB: G1 =  0 dB -> {nf_db[0]:6.2f} dB, "
              f"G1 = 30 dB -> {nf_db[-1]:5.2f} dB, "
              f"asymptote {nf1_db:.2f} dB")
        print(f"      shares at G1 =  0 dB  {share[0][0]:5.1f}% / "
              f"{share[1][0]:5.1f}% / {share[2][0]:4.1f}%")
        print(f"      shares at G1 = 30 dB  {share[0][-1]:5.2f}% / "
              f"{share[1][-1]:5.2f}% / {share[2][-1]:4.2f}%")
        print(f"      within {DOMINANCE_DB:.1f} dB of NF1 at G1 = {gain:.2f} dB, "
              f"where stage 1 owns {owned:.1f}% of the noise")

    print("dynamic-range-by-format")
    for label, ideal, measured, _colour in _format_rows():
        if measured is None:
            print(f"  {label:<26} {ideal:7.2f} dB ideal")
        else:
            print(f"  {label:<26} {ideal:7.2f} dB ideal, {measured:6.2f} dB "
                  f"measured, gap {ideal - measured:5.2f} dB")
    print(f"  32-bit float exponent span  {FLOAT_EXPONENT_DB:.1f} dB of "
          f"magnitude vs {_ideal_snr(FLOAT_SIGNIFICAND_BITS):.1f} dB of "
          "relative precision")


if __name__ == "__main__":                          # pragma: no cover
    _diagnostics()
