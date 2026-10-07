"""Hand-authored diagrams for the SerDes FEC and error-budget chapter.

    fec-interleaving     how a code spreads a burst error across codewords, and
                         what the interleaving depth costs
    error-budget         every error term from the fibre to the host, on one
                         logarithmic axis, ending at the FEC threshold
    serdes-part-map      this part's chapters, and how the whole course stacks

The chapter closes the loop: after five chapters of impairment, this is the
arithmetic that decides whether the sum of them is survivable.
"""

from __future__ import annotations

import math

from . import svg as S

# Superscript digits, so an exponent reads as an exponent. Unicode is safe for
# digits and the minus sign in every font this blog targets, unlike a subscript
# letter, which is why the SVG builder has ~x~ markup for those.
_SUP = {"-": "\u207b", "0": "\u2070", "1": "\u00b9", "2": "\u00b2",
        "3": "\u00b3", "4": "\u2074", "5": "\u2075", "6": "\u2076",
        "7": "\u2077", "8": "\u2078", "9": "\u2079", ".": "\u00b7"}


def _sup(text: str) -> str:
    """Map every character of a number to its superscript form."""
    return "".join(_SUP[c] for c in str(text))


def fec_interleaving() -> str:
    note = [
        "A DFE turns independent errors into bursts, and a Reed-Solomon "
        "decoder corrects a fixed number of symbol errors per codeword. A "
        "burst that lands inside one codeword can exhaust the correction "
        "budget; the same burst spread across many codewords costs each of "
        "them one symbol error.",
        "Interleaving is that spreading, and it is why the depth is quoted "
        "alongside the code. Deeper interleaving repairs longer bursts and "
        "costs latency and memory, which in a module with a strict latency "
        "budget is a real constraint rather than a footnote.",
    ]
    c = S.Canvas(880, int(520 + S.callout_height(808, note, body_size=11.5) + 14),
                 title="Why a burst needs interleaving")

    # top: a burst landing in one codeword
    c.add(S.text(48, 92, "without interleaving: the burst lands in one codeword",
                 size=11, fill=S.WARN, weight=700))
    cw, gap = 200, 12
    for i in range(4):
        x = 48 + i * (cw + gap)
        fill = S.WARN_WASH if i == 1 else S.PANEL
        stroke = S.WARN if i == 1 else S.RULE
        c.add(S.rect(x, 108, cw, 44, fill=fill, stroke=stroke, rx=4, width=1.3),
              S.text(x + cw / 2, 130, f"codeword {i}", size=10, fill=S.INK,
                     anchor="middle"))
    # the burst, as a run of error marks inside codeword 1
    for k in range(6):
        x = 48 + (cw + gap) + 24 + k * 24
        c.add(S.rect(x, 118, 20, 24, fill=S.WARN, stroke=None, rx=2,
                     opacity=0.65))
    c.add(S.text(48 + (cw + gap) + 180, 168, "6 symbols wrong in one codeword "
                 "\u2192 uncorrectable", size=10, fill=S.WARN, weight=600))

    # bottom: interleaved
    c.add(S.text(48, 216, "with interleaving: the same burst spread across all "
                 "of them", size=11, fill=S.ACCENT, weight=700))
    for i in range(4):
        x = 48 + i * (cw + gap)
        c.add(S.rect(x, 232, cw, 44, fill=S.ACCENT_WASH, stroke=S.ACCENT,
                     rx=4, width=1.3),
              S.text(x + cw / 2, 254, f"codeword {i}", size=10, fill=S.INK,
                     anchor="middle"))
    for k in range(6):
        which = k % 4
        x = 48 + which * (cw + gap) + 24 + (k // 4) * 26
        c.add(S.rect(x, 242, 22, 24, fill=S.ACCENT, stroke=None, rx=2,
                     opacity=0.65))
    c.add(S.text(48, 296, "6 symbols wrong, but 1 or 2 per codeword "
                 "\u2192 corrected", size=10, fill=S.ACCENT_DARK, weight=600))

    # the cost, as a small table
    rows = [
        ("interleaving depth", "latency added", "memory", "burst it survives"),
        ("1 (none)", "0", "0", "~1 symbol"),
        ("4", "~4 codewords", "4x", "~4 symbols"),
        ("16", "~16 codewords", "16x", "~16 symbols"),
    ]
    y0 = 336
    for r, row in enumerate(rows):
        for cidx, cell in enumerate(row):
            x = 48 + cidx * 194
            if r == 0:
                c.add(S.text(x, y0, cell, size=10, fill=S.MUTED, weight=700))
            else:
                c.add(S.text(x, y0 + r * 24, cell, size=10,
                             fill=S.INK if cidx == 0 else S.SOFT,
                             weight=700 if cidx == 0 else 400,
                             family=S.MONO if cidx in (1, 2, 3) else S.FONT))

    c.add(S.callout(36, 452, 808, "Latency is a budget, not a detail", note,
                    kind="optical"))
    return c.render()


def error_budget() -> str:
    note = [
        "This is the chapter's real deliverable: every error mechanism in a "
        "module on one axis, converted into an equivalent pre-FEC error ratio "
        "at the decoder, and summed. The sum is compared against the code's "
        "threshold, and what is left is the margin that survives temperature, "
        "ageing and a dirty connector.",
        "The conversion is the work. A jitter number in picoseconds, a "
        "crosstalk number in decibels and a reflection number in decibels all "
        "have to become an error ratio before they can be added, and the "
        "conversion is the Q-factor arithmetic from the BERT chapter. A "
        "budget that adds decibels to picoseconds is not a budget.",
    ]
    c = S.Canvas(880, int(524 + S.callout_height(808, note, body_size=11.5) + 14),
                 title="Every error term, on one axis, ending at the threshold")

    # a horizontal axis of error ratio, log scale
    x0, x1, ax_y = 130, 800, 300
    lo_exp, hi_exp = -18.0, -2.0
    def px(exp):
        return x0 + (exp - lo_exp) / (hi_exp - lo_exp) * (x1 - x0)

    c.add(S.line(x0, ax_y, x1, ax_y, stroke=S.INK, width=1.6))
    for e in range(-18, -1, 2):
        x = px(e)
        c.add(S.line(x, ax_y, x, ax_y + 6, stroke=S.RULE, width=1.1),
              S.text(x, ax_y + 20, "10" + _sup(e), size=9, fill=S.MUTED,
                     anchor="middle", family=S.MONO))
    c.add(S.text((x0 + x1) / 2, ax_y + 42, "equivalent pre-FEC error ratio at "
                 "the decoder", size=10.5, fill=S.SOFT, anchor="middle",
                 weight=600))

    # each contribution, as a span from the axis
    terms = [
        ("fibre and OSNR", -9.0, S.OPTICAL),
        ("transmitter and optics", -10.5, S.OPTICAL),
        ("channel loss and ISI", -8.2, S.WARN),
        ("crosstalk", -11.0, S.WARN),
        ("reflections", -13.0, S.WARN),
        ("CDR jitter", -12.2, S.NOTE),
        ("reference clock", -14.0, S.NOTE),
        ("receiver noise", -13.6, S.ACCENT),
    ]
    y = 120
    for i, (name, exp, colour) in enumerate(terms):
        yy = y + i * 22
        c.add(S.text(x0 - 12, yy, name, size=9.5, fill=S.SOFT, anchor="end"),
              S.line(x0, yy, px(exp), yy, stroke=colour, width=1.3,
                     dash="3 3"),
              S.dot(px(exp), yy, r=3.6, fill=colour),
              S.line(px(exp), yy, px(exp), ax_y, stroke=colour, width=1.0))

    # the sum, and the threshold
    total_exp = -7.6
    c.add(S.line(px(total_exp), 108, px(total_exp), ax_y + 8, stroke=S.ACCENT,
                 width=2.6),
          S.dot(px(total_exp), ax_y, r=6, fill=S.ACCENT),
          S.text(px(total_exp) + 8, 112,
                 "total: 10" + _sup(f"{total_exp:.1f}"),
                 size=10.5, fill=S.ACCENT_DARK, weight=700))
    thr_exp = -3.62          # 2.4e-4, the KP4 threshold
    c.add(S.line(px(thr_exp), 108, px(thr_exp), ax_y + 8, stroke=S.WARN,
                 width=2.6),
          S.dot(px(thr_exp), ax_y, r=6, fill=S.WARN),
          S.text(px(thr_exp), 96, "FEC threshold: 2.4 \u00d7 10\u207b\u2074",
                 size=10.5, fill=S.WARN, anchor="middle", weight=700))

    # the margin bracket
    c.add(S.line(px(total_exp), ax_y + 62, px(thr_exp), ax_y + 62,
                 stroke=S.ACCENT, width=1.8),
          S.line(px(total_exp), ax_y + 56, px(total_exp), ax_y + 68,
                 stroke=S.ACCENT, width=1.4),
          S.line(px(thr_exp), ax_y + 56, px(thr_exp), ax_y + 68, stroke=S.ACCENT,
                 width=1.4),
          S.text((px(total_exp) + px(thr_exp)) / 2, ax_y + 78,
                 "margin: 4 orders of magnitude", size=10.5,
                 fill=S.ACCENT_DARK, anchor="middle", weight=700))

    c.add(S.callout(36, 420, 808, "Why the terms are plotted as spans", note,
                    kind="accent"))
    return c.render()


def serdes_part_map() -> str:
    note = [
        "This is the last map in the course, and it is the whole course. A "
        "coherent optical module is a stack of every part: the DSP theory "
        "supplies the algorithms, the Ethernet part supplies the measurement "
        "discipline, and this part supplies the electrical interfaces that "
        "connect them to the world.",
        "Read it as a build order. Each layer assumes the ones below it, and "
        "a problem at any layer is diagnosed with the chapters at that layer "
        "rather than by re-examining the layer above.",
    ]
    c = S.Canvas(880, int(546 + S.callout_height(808, note, body_size=11.5) + 14),
                 title="The whole course, as one stack")

    layers = [
        ("The optical link", "coherent DSP, dispersion, CMA, carrier phase",
         "optical", "photons to symbols"),
        ("SerDes for optical modules", "this part: channel, equalisation, CDR, "
         "jitter, error budget", "accent", "symbols across a wire"),
        ("IEEE Ethernet, measured", "link budget, eye, BERT, DFT, compliance",
         "note", "what a number means"),
        ("DSP fundamentals", "sampling, quantisation, dB, Fourier, filters, "
         "multirate", "plain", "the mathematics"),
    ]
    y0, dy, bh = 104, 84, 66
    for i, (title, sub, kind, tag) in enumerate(layers):
        y = y0 + i * dy
        c.add(S.block(52, y, 560, bh, title, kind=kind, title_size=12.5))
        c.add(S.text(72, y + bh / 2 + 22, sub, size=9.5, fill=S.SOFT))
        c.add(S.text(636, y + bh / 2, tag, size=10, fill=S.MUTED,
                     weight=600))
        if i < len(layers) - 1:
            c.add(S.arrow(332, y + bh + 2, 332, y + dy - 2, stroke=S.RULE,
                          width=1.5))

    # the diagnosis arrow, showing the direction of troubleshooting
    c.add(S.arrow_path([(836, y0 + 12), (836, y0 + 3 * dy + bh - 12)],
                       stroke=S.OPTICAL, width=1.8, head=True),
          S.text(846, y0 + 1.5 * dy, "diagnose downward", size=10,
                 fill=S.OPTICAL_DARK, anchor="middle", weight=600, rotate=-90))

    c.add(S.callout(36, 470, 808, "Where this part sits, and why", note,
                    kind="optical"))
    return c.render()


FIGURES = {
    "fec-interleaving": fec_interleaving,
    "error-budget": error_budget,
    "serdes-part-map": serdes_part_map,
}
