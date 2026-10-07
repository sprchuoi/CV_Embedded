"""Hand-authored diagrams for the BERT, BER and FEC chapter.

    bert-setup          the measurement loop: pattern generator, channel, error
                        detector, and the two things that make it honest
    bert-prbs-patterns  which PRBS order stresses what, and why the pattern is
                        part of the result
    fec-exchange        pre-FEC BER in, post-FEC BER out, and the waterfall in
                        between -- the contract a link is signed on

The chapter's job is to make BER a measured quantity rather than a formula, and
to explain why a link that "works" still needs a maximum error ratio written
next to it.
"""

from __future__ import annotations

import math

from . import svg as S

# (name, length, stresses, note)
PATTERNS = [
    ("PRBS7", "2^7 \u2212 1 = 127", "short-run balance", "clock recovery only"),
    ("PRBS9", "511", "PCIe, 8B/10B links", "legacy compliance"),
    ("PRBS13", "8191", "jitter, crosstalk", "10GBASE-KR"),
    ("PRBS15", "32767", "long runs, baseline wander", "1000BASE-T, 10GBASE-T"),
    ("PRBS23", "8.4 M", "low-frequency content", "10GBASE-KR, 25G"),
    ("PRBS31", "2.1 G", "worst-case run length", "highest confidence, slowest"),
]


def bert_setup() -> str:
    note = [
        "The pattern generator and the error detector share a clock, so the "
        "measurement compares a known sequence bit by bit. That is why BERT "
        "can count one error in 10^15 while an eye diagram can only show you "
        "a probability.",
        "Two things make the number honest. The pattern must be long enough "
        "to contain the run lengths the link will see, and the count must "
        "include the errors that FEC will later repair -- a post-FEC number "
        "alone tells you the link passed, not how much margin is left.",
    ]
    c = S.Canvas(880, int(452 + S.callout_height(808, note, body_size=11.5) + 14),
                 title="The bit error ratio test loop")

    blocks = [
        ("Pattern\ngenerator", "PRBS-N,\nknown bits", "note"),
        ("Transmitter", "TX equaliser,\ndrive", "plain"),
        ("Channel", "cable or\nbackplane", "warn"),
        ("Receiver", "AGC, FFE/DFE,\nslicer", "accent"),
        ("Error\ndetector", "compare, count,\nBER", "optical"),
    ]
    box_w, gap, by, bh = 152, 22, 148, 96
    x0 = (880 - (len(blocks) * box_w + (len(blocks) - 1) * gap)) / 2
    centres = []
    for i, (title, sub, kind) in enumerate(blocks):
        bx = x0 + i * (box_w + gap)
        centres.append(bx + box_w / 2)
        c.add(S.block(bx, by, box_w, bh, title.split("\n")[0], kind=kind,
                      title_size=11.5))
        for j, line in enumerate(sub.split("\n")):
            c.add(S.text(bx + box_w / 2, by + bh / 2 + 34 + j * 14, line,
                         size=9.5, fill=S.SOFT, anchor="middle"))
        if i < len(blocks) - 1:
            c.add(S.arrow(bx + box_w + 2, by + bh / 2, bx + box_w + gap - 2,
                          by + bh / 2, stroke=S.MUTED, width=1.5))

    # the shared clock, drawn as a bus under the first and last blocks
    clk_y = by + bh + 46
    c.add(S.arrow_path([(centres[0], by + bh), (centres[0], clk_y),
                        (centres[4], clk_y), (centres[4], by + bh)],
                       stroke=S.OPTICAL, width=1.5, head=False),
          S.text((centres[0] + centres[4]) / 2, clk_y + 18,
                 "shared clock and known pattern: this is what makes it a "
                 "measurement, not an estimate", size=10, fill=S.OPTICAL_DARK,
                 anchor="middle", weight=600))

    # the two annotations that matter
    c.add(S.text(centres[1], by - 22, "TX", size=10, fill=S.MUTED,
                 anchor="middle"),
          S.text(centres[3], by - 22, "RX", size=10, fill=S.MUTED,
                 anchor="middle"))

    c.add(S.callout(36, clk_y + 38, 808, "What BERT gives you that an eye cannot",
                    note, kind="accent"))
    return c.render()


def bert_prbs_patterns() -> str:
    note = [
        "A PRBS-N is a shift register with feedback, so it produces every "
        "run length up to N bits with the right statistics -- but only up to "
        "N. A pattern that is too short never exercises the long runs that "
        "charge a coupling capacitor and wander the baseline.",
        "The cost of a longer pattern is time: errors accumulate at the "
        "link's own rate, so proving 10^-12 with confidence takes longer "
        "than proving 10^-9. A compliance suite quotes the pattern *and* the "
        "duration, because neither number means anything alone.",
    ]
    c = S.Canvas(880, int(436 + S.callout_height(808, note, body_size=11.5) + 14),
                 title="The PRBS patterns, and what each one stresses")

    x_name, x_len, x_stress, x_note = 40, 168, 350, 590
    y0, dy = 108, 46
    c.add(S.text(x_name, y0 - 24, "pattern", size=10.5, fill=S.MUTED,
                 weight=700),
          S.text(x_len, y0 - 24, "sequence length", size=10.5, fill=S.MUTED,
                 weight=700),
          S.text(x_stress, y0 - 24, "what it stresses", size=10.5, fill=S.MUTED,
                 weight=700),
          S.text(x_note, y0 - 24, "where it is specified", size=10.5,
                 fill=S.MUTED, weight=700))

    for i, (name, length, stresses, note) in enumerate(PATTERNS):
        y = y0 + i * dy
        colour = S.ACCENT if i < 2 else (S.NOTE if i < 4 else S.OPTICAL)
        c.add(S.rect(x_name - 8, y - 12, 104, 24, fill=colour, stroke=None,
                     rx=12, opacity=0.14),
              S.text(x_name + 44, y, name, size=11, fill=colour, anchor="middle",
                     weight=700, family=S.MONO),
              S.text(x_len, y, length, size=10.5, fill=S.INK, family=S.MONO),
              S.text(x_stress, y, stresses, size=10.5, fill=S.SOFT),
              S.text(x_note, y, note, size=10.5, fill=S.MUTED))

    c.add(S.line(x_name - 8, y0 + 6 * dy - 26, 840, y0 + 6 * dy - 26,
                 stroke=S.RULE, width=1))
    c.add(S.text(40, y0 + 6 * dy - 8, "longer pattern \u2192 more confidence, "
                 "more time", size=10.5, fill=S.WARN, weight=600))

    c.add(S.callout(36, 348, 808, "Choosing a pattern is choosing what to miss",
                    note, kind="note"))
    return c.render()


def fec_exchange() -> str:
    note = [
        "FEC is a contract, not a rescue. The code is designed to correct up "
        "to a stated number of errors per codeword; below the knee it "
        "corrects essentially all of them, above it essentially none.",
        "That cliff is why the pre-FEC numbers are the ones engineers track. "
        "A link running at 10^-5 pre-FEC has margin; the same link at "
        "10^-4 is one temperature rise away from the cliff, even though both "
        "report a post-FEC error ratio of zero.",
    ]
    c = S.Canvas(880, int(452 + S.callout_height(808, note, body_size=11.5) + 14),
                 title="The FEC exchange: what goes in, what must come out")

    # left: pre-FEC target, right: post-FEC target, middle: the code
    box_y, box_h = 132, 118
    c.add(S.block(52, box_y, 216, box_h, "pre-FEC", kind="warn",
                  title_size=13),
          S.text(160, box_y + 62, "the raw BER the slicer produces",
                 size=9.5, fill=S.SOFT, anchor="middle"),
          S.text(160, box_y + 82, "\u2264 2.4 \u00d7 10\u207b\u2074", size=15,
                 fill=S.WARN, anchor="middle", weight=700, family=S.MONO),
          S.text(160, box_y + 102, "for RS(544,514) at 100G/lane", size=9,
                 fill=S.MUTED, anchor="middle"))

    c.add(S.block(612, box_y, 216, box_h, "post-FEC", kind="accent",
                  title_size=13),
          S.text(720, box_y + 62, "the BER the MAC is allowed to see",
                 size=9.5, fill=S.SOFT, anchor="middle"),
          S.text(720, box_y + 82, "< 10\u207b\u00b9\u00b3", size=15,
                 fill=S.ACCENT_DARK, anchor="middle", weight=700,
                 family=S.MONO),
          S.text(720, box_y + 102, "typically 10\u207b\u00b9\u2075 and "
                 "better", size=9, fill=S.MUTED, anchor="middle"))

    # middle: the code
    c.add(S.block(308, box_y - 14, 264, box_h + 28,
                  "Reed-Solomon / BCH", kind="optical", title_size=13),
          S.text(440, box_y + 46, "adds redundancy bits to every", size=9.5,
                 fill=S.SOFT, anchor="middle"),
          S.text(440, box_y + 61, "codeword, and corrects up to a", size=9.5,
                 fill=S.SOFT, anchor="middle"),
          S.text(440, box_y + 76, "fixed number of symbol errors", size=9.5,
                 fill=S.SOFT, anchor="middle"),
          S.text(440, box_y + 100, "coding gain \u2248 6 dB", size=11,
                 fill=S.OPTICAL_DARK, anchor="middle", weight=700))

    c.add(S.arrow(276, box_y + box_h / 2, 302, box_y + box_h / 2,
                  stroke=S.WARN, width=2),
          S.arrow(578, box_y + box_h / 2, 606, box_y + box_h / 2,
                  stroke=S.ACCENT, width=2))

    # the waterfall, sketched: post-FEC BER against pre-FEC BER
    wx0, wx1 = 96, 800
    wy0, wy1 = 356, 300
    c.add(S.axis(wx0, wy0, wx1, wy0 - 46, xlabel="pre-FEC BER", ylabel=None,
                 xticks=[(wx0, "10\u207b\u2076"), (wx0 + (wx1 - wx0) * 0.5, "10\u207b\u2074"),
                         (wx1, "10\u207b\u00b3")],
                 yticks=[(wy0 - 8, "10\u207b\u00b9\u2075"), (wy0 - 30, "10\u207b\u2079"),
                         (wy0 - 44, "10\u207b\u00b3")]))
    waterfall = []
    for i in range(121):
        u = i / 120
        # a cliff: low and flat until the knee at 0.72, then straight up
        v = 0.05 + 0.95 * (1.0 / (1.0 + math.exp(-(u - 0.72) * 120.0)))
        waterfall.append((wx0 + 6 + u * (wx1 - wx0 - 12), wy0 - 4 - v * 40))
    c.add(S.polyline(waterfall, stroke=S.OPTICAL, width=2.6),
          S.text(wx0 + (wx1 - wx0) * 0.52, wy0 - 52, "the FEC waterfall: "
                 "corrects until it does not", size=10, fill=S.OPTICAL_DARK,
                 anchor="middle", weight=600))
    c.add(S.line(wx0 + (wx1 - wx0) * 0.72, wy0 - 4, wx0 + (wx1 - wx0) * 0.72,
                 wy0 - 44, stroke=S.WARN, width=1.5, dash="4 4"),
          S.text(wx0 + (wx1 - wx0) * 0.72 + 8, wy0 - 40, "the knee", size=9.5,
                 fill=S.WARN, weight=600))

    c.add(S.callout(36, 380, 808, "Why the cliff, and why margin is pre-FEC",
                    note, kind="optical"))
    return c.render()


FIGURES = {
    "bert-setup": bert_setup,
    "bert-prbs-patterns": bert_prbs_patterns,
    "fec-exchange": fec_exchange,
}
