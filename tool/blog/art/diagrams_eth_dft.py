"""Hand-authored diagrams for the FFT/DFT-in-Ethernet chapter.

    dft-bins-to-hertz     one worked example, from a scope's sample rate to the
                          frequency a bin index means -- the arithmetic that is
                          wrong more often than any other in this course
    dft-resolution-tradeoff  record length against resolution and against the
                          noise floor, the two costs of a longer FFT

This chapter is where the frequency-domain part of the course stops being
theory: a compliance measurement *is* a DFT, and the bin spacing is a
specification number.
"""

from __future__ import annotations

from . import svg as S


def dft_bins_to_hertz() -> str:
    note = [
        "The rule is one line: bin k is at k times the sample rate divided by "
        "the record length. Everything else in a spectrum measurement -- "
        "resolution, noise floor, whether you can see a spur at all -- "
        "follows from choosing those three numbers.",
        "The trap is that the *sample rate* sets the span and the *record "
        "length* sets the resolution, and they are independent. Doubling the "
        "sample rate doubles the span and doubles the hertz per bin; it buys "
        "no extra resolution at all.",
    ]
    c = S.Canvas(880, int(500 + S.callout_height(808, note, body_size=11.5) + 14),
                 title="From a scope's settings to the hertz of one bin")

    # the three input numbers
    inputs = [
        ("sample rate", "f~s~", "20 GS/s"),
        ("record length", "N", "2000 samples"),
        ("bin spacing", "10\u2077 Hz", "10 MHz"),
    ]
    for i, (label, symbol, value) in enumerate(inputs):
        bx = 52 + i * 264
        c.add(S.rect(bx, 88, 240, 78, fill=S.NOTE_WASH, stroke=S.NOTE, rx=6),
              S.text(bx + 120, 112, label, size=10, fill=S.MUTED,
                     anchor="middle"),
              S.text(bx + 120, 136, value, size=15, fill=S.NOTE_DARK,
                     anchor="middle", weight=700, family=S.MONO),
              S.text(bx + 120, 156, symbol, size=10.5, fill=S.NOTE,
                     anchor="middle", weight=700))

    # the derived numbers
    c.add(S.rect(52, 192, 392, 82, fill=S.ACCENT_WASH, stroke=S.ACCENT, rx=6),
          S.text(248, 216, "bin k sits at  k \u00b7 (f~s~ \u00f7 N)", size=11.5,
                 fill=S.ACCENT_DARK, anchor="middle", weight=700),
          S.text(248, 244, "41 \u00d7 10 MHz  =  410 MHz", size=13.5,
                 fill=S.ACCENT_DARK, anchor="middle", weight=700,
                 family=S.MONO),
          S.text(248, 262, "the only arithmetic in this chapter", size=10,
                 fill=S.SOFT, anchor="middle"))

    c.add(S.rect(476, 192, 352, 82, fill=S.OPTICAL_WASH, stroke=S.OPTICAL,
                 rx=6),
          S.text(652, 216, "resolving for a frequency you want", size=11.5,
                 fill=S.OPTICAL_DARK, anchor="middle", weight=700),
          S.text(652, 246, "k = f \u00b7 N / f~s~", size=14,
                 fill=S.OPTICAL_DARK, anchor="middle", weight=700,
                 family=S.MONO),
          S.text(652, 264, "which bin does 410 MHz land in?", size=10,
                 fill=S.SOFT, anchor="middle"))

    # the bin ruler: 0 to 1 GHz, bin spacing 10 MHz
    rx0, rx1, ry = 104, 804, 362
    span_mhz = 1000.0
    c.add(S.line(rx0, ry, rx1, ry, stroke=S.INK, width=1.6))
    for mhz in range(0, 1001, 100):
        x = rx0 + mhz / span_mhz * (rx1 - rx0)
        c.add(S.line(x, ry, x, ry + 6, stroke=S.RULE, width=1.1),
              S.text(x, ry + 20, str(mhz), size=9, fill=S.MUTED,
                     anchor="middle", family=S.MONO))
    c.add(S.text((rx0 + rx1) / 2, ry + 42,
                 "frequency (MHz)  \u2014  1000 bins, one per 10 MHz, "
                 "covering DC to half the 20 GS/s sample rate", size=10.5,
                 fill=S.SOFT, anchor="middle", weight=600))

    mark_x = rx0 + 410 / span_mhz * (rx1 - rx0)
    c.add(S.line(mark_x, ry - 30, mark_x, ry + 7, stroke=S.ACCENT, width=2),
          S.dot(mark_x, ry, r=5, fill=S.ACCENT),
          S.text(mark_x + 10, ry - 34, "bin 41 = 410 MHz", size=10.5,
                 fill=S.ACCENT_DARK, weight=700))

    c.add(S.callout(36, 420, 808, "Why this arithmetic is a compliance "
                    "requirement", note, kind="accent"))
    return c.render()


def dft_resolution_tradeoff() -> str:
    note = [
        "A longer record resolves closer tones and lowers the noise floor, "
        "because averaging more samples of noise buys processing gain. Both "
        "improvements are real, both are paid for in capture time, and both "
        "are plotted downward here because lower is better for each.",
        "In a compliance measurement the capture time is not free: an "
        "Ethernet link is a live system whose channel drifts, and a record "
        "long enough to resolve 1 MHz may also be long enough for the "
        "channel to have changed underneath it.",
    ]
    c = S.Canvas(880, int(462 + S.callout_height(808, note, body_size=11.5) + 14),
                 title="What a longer record buys, and what it costs")

    left, right = 128, 786
    base, top = 312, 106

    def px(log_n):
        # 1000 samples (log 3) through 1e6 samples (log 6)
        return left + (log_n - 3.0) / 3.0 * (right - left)

    def py(v):
        return base - v * (base - top)

    c.add(S.axis(left, base, right, top, xlabel="record length N (samples)",
                 ylabel=None,
                 xticks=[(px(3), "1 k"), (px(4), "10 k"), (px(5), "100 k"),
                         (px(6), "1 M")],
                 yticks=[(py(1.0), "better"), (py(0.0), "worse")]))

    # bin spacing falls as 1/N: a straight line on a log axis
    res, noise, time = [], [], []
    for i in range(61):
        log_n = 3.0 + i / 60 * 3.0
        res.append((px(log_n), py(0.88 - (log_n - 3.0) / 3.0 * 0.62)))
        noise.append((px(log_n), py(0.52 - (log_n - 3.0) / 3.0 * 0.34)))
        time.append((px(log_n), py((log_n - 3.0) / 3.0 * 0.78)))

    c.add(S.polyline(res, stroke=S.ACCENT, width=2.6),
          S.polyline(noise, stroke=S.NOTE, width=2.6, dash="7 4"),
          S.polyline(time, stroke=S.WARN, width=2.6),
          S.text(px(4.35), py(0.40), "bin spacing (resolution)", size=10.5,
                 fill=S.ACCENT_DARK, weight=700),
          S.text(px(4.35), py(0.30), "noise floor", size=10.5,
                 fill=S.NOTE_DARK, weight=700),
          S.text(px(3.08), py(0.72), "capture time \u2014 and how much the "
                 "channel drifts during it", size=10.5, fill=S.WARN,
                 weight=700))

    c.add(S.line(px(4.3), top, px(4.3), base, stroke=S.RULE, width=1.3,
                 dash="4 4"),
          S.text(px(4.3), base + 36, "the usual compromise", size=10,
                 fill=S.MUTED, anchor="middle", weight=600))

    c.add(S.callout(36, 358, 808, "The two costs, named", note, kind="note"))
    return c.render()


FIGURES = {
    "dft-bins-to-hertz": dft_bins_to_hertz,
    "dft-resolution-tradeoff": dft_resolution_tradeoff,
}
