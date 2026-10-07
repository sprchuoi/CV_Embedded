"""Hand-authored diagrams for the Ethernet history chapter.

    ethernet-lineage      each generation's data rate against the media it had
                          to cross, so the pattern is visible as one picture
    ethernet-lane-rates   the same total rates, split across lanes: where
                          per-lane baud rate stops and PAM4 begins
    ethernet-dsp-stack    the four steps every generation performs, with the
                          technology each generation reached for

The chapter's claim is that Ethernet did not get faster by inventing modulation
once. Each generation hit a specific limit -- reach, then per-lane baud, then
the Shannon wall -- and every time the fix moved work out of the analogue front
end and into DSP. These three figures are that argument in three resolutions.
"""

from __future__ import annotations

from . import svg as S

# --------------------------------------------------------------------------- #
# 1. the lineage: rate against era, coloured by the media family
# --------------------------------------------------------------------------- #

# (name, total Gbit/s, year, family)
GENERATIONS = [
    ("Ethernet", 0.01, 1983, "coax"),
    ("10BASE-T", 0.01, 1990, "copper"),
    ("100BASE-TX", 0.1, 1995, "copper"),
    ("1000BASE-T", 1.0, 1999, "copper"),
    ("10GBASE-T", 10.0, 2006, "copper"),
    ("40G", 40.0, 2010, "backplane"),
    ("100G", 100.0, 2010, "backplane"),
    ("400G", 400.0, 2017, "backplane"),
    ("800G", 800.0, 2022, "backplane"),
]

FAMILY_COLOUR = {
    "coax": S.WARN,
    "copper": S.ACCENT,
    "backplane": S.OPTICAL,
}

FAMILY_NOTE = {
    "coax": "shared bus, collisions",
    "copper": "dedicated pair, echo cancelling",
    "backplane": "lanes, PAM4, FEC in the PHY",
}


def ethernet_lineage() -> str:
    note = [
        "Read the shape, not the numbers. Each step is roughly a factor of "
        "four to ten, roughly every five years, and the medium never gets "
        "easier -- it gets harder and the DSP takes over.",
        "The 1995-1999 step is where this course begins: 100BASE-TX sent "
        "three levels and lived, 1000BASE-T sent five and needed an echo "
        "canceller, a precoder and four pairs at once.",
    ]
    c = S.Canvas(880, int(470 + S.callout_height(808, note, body_size=11.5) + 14),
                 title="Six generations of Ethernet: rate against media")

    left, right = 104, 812
    base, top = 296, 96
    lo, hi = 0.004, 2000.0          # Gbit/s, log axis

    import math

    def py(rate):
        return base - (math.log10(rate) - math.log10(lo)) / (
            math.log10(hi) - math.log10(lo)) * (base - top)

    # decade gridlines on the rate axis
    for decade in (0.01, 0.1, 1, 10, 100, 1000):
        y = py(decade)
        c.add(S.line(left - 6, y, right, y, stroke=S.RULE_SOFT, width=1),
              S.text(left - 12, y, f"{decade:g}", size=9.5, fill=S.MUTED,
                     anchor="end", family=S.MONO))
    c.add(S.text(left - 12, 74, "Gbit/s", size=10, fill=S.MUTED, anchor="end",
                 weight=700))

    prev = None
    for name, rate, year, family in GENERATIONS:
        x = left + (year - 1981) / (2024 - 1981) * (right - left)
        y = py(rate)
        colour = FAMILY_COLOUR[family]
        if prev is not None:
            c.add(S.line(prev[0], prev[1], x, y, stroke=S.RULE, width=1.4,
                         dash="3 3"))
        c.add(S.dot(x, y, r=5.5, fill=colour))
        prev = (x, y)

    # labels, hand-placed to stop the 2010 cluster and the 1990 baseline from
    # colliding. The 2010 pair is the awkward one: 40G and 100G share a year.
    label_pos = {
        "Ethernet": (10, 0, "start"),
        "10BASE-T": (11, 0, "start"),
        "100BASE-TX": (8, -16, "start"),
        "1000BASE-T": (8, -16, "start"),
        "10GBASE-T": (10, 0, "start"),
        "40G": (-9, 0, "end"),
        "100G": (10, 0, "start"),
        "400G": (10, 0, "start"),
        "800G": (10, 0, "start"),
    }
    for name, rate, year, family in GENERATIONS:
        x = left + (year - 1981) / (2024 - 1981) * (right - left)
        y = py(rate)
        dx, dy, anchor = label_pos[name]
        c.add(S.text(x + dx, y + dy, name, size=11, fill=S.INK, weight=700,
                     anchor=anchor))

    # era axis
    c.add(S.line(left, base, right, base, stroke=S.INK, width=1.6))
    for year in range(1985, 2025, 5):
        x = left + (year - 1981) / (2024 - 1981) * (right - left)
        c.add(S.line(x, base, x, base + 5, stroke=S.RULE, width=1.1),
              S.text(x, base + 18, str(year), size=9.5, fill=S.MUTED,
                     anchor="middle", family=S.MONO))
    c.add(S.text((left + right) / 2, base + 40, "standard ratified", size=11,
                 fill=S.SOFT, anchor="middle", weight=600))

    # legend, in the empty upper-left corner
    for i, (family, colour) in enumerate(FAMILY_COLOUR.items()):
        ly = 62 + i * 0
        lx = 300 + i * 196
        c.add(S.line(lx, 60, lx + 22, 60, stroke=colour, width=3),
              S.dot(lx + 11, 60, r=5.5, fill=colour),
              S.text(lx + 30, 60, FAMILY_NOTE[family], size=9.5, fill=S.SOFT))

    c.add(S.callout(36, 374, 808, "What the vertical axis is telling you", note,
                    kind="accent"))
    return c.render()


# --------------------------------------------------------------------------- #
# 2. per-lane rate: where PAM4 had to start
# --------------------------------------------------------------------------- #


def ethernet_lane_rates() -> str:
    note = [
        "The bars on the left are total rate; the bars on the right are what "
        "one lane has to carry. The right-hand bars flatten beyond 50 G -- "
        "not because standards stopped, but because a copper lane cannot "
        "sensibly signal faster than about 53 GBd.",
        "That flattening is why 400G and 800G are 8 lanes rather than one "
        "heroic lane. Lane count is the escape hatch when baud rate runs "
        "out; modulation order is the other one, and PAM4 is what it buys.",
    ]
    c = S.Canvas(880, int(470 + S.callout_height(808, note, body_size=11.5) + 14),
                 title="Total rate, lane rate, and the two escape hatches")

    # (name, total Gbit/s, lane Gbit/s, lanes, signalling, style)
    rows = [
        ("1000BASE-T", 1.0, 0.25, 4, "PAM5", "plain"),
        ("10GBASE-KR", 10.0, 10.0, 1, "NRZ", "plain"),
        ("25G per lane", 25.0, 25.0, 1, "NRZ", "accent"),
        ("400G", 400.0, 50.0, 8, "PAM4", "accent"),
        ("800G", 800.0, 100.0, 8, "PAM4", "optical"),
    ]

    x_total, x_lane = 150, 470
    y0, dy = 96, 56
    bar_h = 22
    max_total, max_lane = 900.0, 120.0

    c.add(S.text(x_total, 74, "total line rate", size=10.5, fill=S.MUTED,
                 weight=700),
          S.text(x_lane, 74, "rate per lane", size=10.5, fill=S.MUTED,
                 weight=700),
          S.text(700, 74, "what one lane sends", size=10.5, fill=S.MUTED,
                 weight=700))

    for i, (name, total, lane, lanes, kind_s, style) in enumerate(rows):
        y = y0 + i * dy
        colour = {"plain": S.NOTE, "accent": S.ACCENT,
                  "optical": S.OPTICAL}[style]
        total_s = f"{total:g} G"
        lane_s = f"{lane:g} G"
        c.add(S.text(36, y + bar_h / 2, name, size=11, fill=S.INK, weight=700),
              S.text(36, y + bar_h / 2 + 15,
                     f"{lanes} lane{'s' if lanes > 1 else ''}", size=9.5,
                     fill=S.MUTED, family=S.MONO))
        # total bar
        c.add(S.rect(x_total, y, max(4.0, total / max_total * 268), bar_h,
                     fill=colour, stroke=None, rx=4, opacity=0.35),
              S.text(x_total + max(4.0, total / max_total * 268) + 8,
                     y + bar_h / 2, total_s, size=10, fill=colour,
                     weight=700, family=S.MONO))
        # lane bar
        c.add(S.rect(x_lane, y, max(4.0, lane / max_lane * 178), bar_h,
                     fill=colour, stroke=None, rx=4),
              S.text(x_lane + max(4.0, lane / max_lane * 178) + 8,
                     y + bar_h / 2, lane_s, size=10, fill=colour,
                     weight=700, family=S.MONO))
        c.add(S.text(700, y + bar_h / 2, kind_s, size=10.5, fill=S.SOFT))

    # the ceiling line, and the label that explains it
    floor_y = y0 + 4 * dy + bar_h + 6
    c.add(S.line(x_lane + 178, y0 - 6, x_lane + 178, floor_y,
                 stroke=S.WARN, width=1.8, dash="5 4"),
          S.text(x_lane + 170, floor_y + 16,
                 "~100 G per lane: PAM4 at 53 GBd, the practical ceiling",
                 size=9.5, fill=S.WARN, anchor="end", weight=600))

    c.add(S.callout(36, 374, 808, "Why lane count keeps doubling", note,
                    kind="note"))
    return c.render()


# --------------------------------------------------------------------------- #
# 3. the four-step data-processing view
# --------------------------------------------------------------------------- #


def ethernet_dsp_stack() -> str:
    note = [
        "Steps 1 and 4 are analogue and optical; steps 2 and 3 are the ones "
        "this course is about, and they are the only part of the budget that "
        "can be changed after the board is fabricated.",
        "Every generation in the lineage figure bought its next factor of ten "
        "by moving work from step 1 into step 3: a wider band, a higher-"
        "resolution ADC, a longer equaliser, a stronger FEC.",
    ]
    c = S.Canvas(880, int(438 + S.callout_height(808, note, body_size=11.5) + 14),
                 title="The four steps every Ethernet PHY performs")

    steps = [
        ("1. Prepare", "line code, precoder,\ndrive level", "plain",
         "8B/10B, 64B/66B, RS-FEC"),
        ("2. Cross", "the channel adds loss,\nreflection and crosstalk", "warn",
         "cat5e..cat8, PCB, connector"),
        ("3. Recover", "AGC, equalise, time,\nslicer, FEC decode", "accent",
         "FFE / DFE / MLSE"),
        ("4. Decide", "symbols -> bits,\nerror counters", "note",
         "PCS, MAC, BERT"),
    ]

    box_w, gap, by, bh = 186, 26, 122, 130
    x0 = (880 - (len(steps) * box_w + (len(steps) - 1) * gap)) / 2
    centres = []
    for i, (title, sub, kind, extra) in enumerate(steps):
        bx = x0 + i * (box_w + gap)
        centres.append(bx + box_w / 2)
        # block() with no subtitle centres the title in the box; the body lines
        # are hung below that centre by hand so the two cannot collide.
        c.add(S.block(bx, by, box_w, bh, title, kind=kind, title_size=12.5))
        for j, line in enumerate(sub.split("\n")):
            c.add(S.text(bx + box_w / 2, by + bh / 2 + 34 + j * 15, line,
                         size=10, fill=S.SOFT, anchor="middle"))
        c.add(S.text(bx + box_w / 2, by + bh + 22, extra, size=9.5,
                     fill=S.MUTED, anchor="middle", family=S.MONO))
        if i < len(steps) - 1:
            c.add(S.arrow(bx + box_w + 3, by + bh / 2, bx + box_w + gap - 3,
                          by + bh / 2, stroke=S.MUTED, width=1.6))

    # feedback loop under the chain: the equaliser is adapted from the slicer
    loop_y = by + bh + 62
    c.add(S.arrow_path([(centres[3], by + bh), (centres[3], loop_y),
                        (centres[2], loop_y)], stroke=S.ACCENT, width=1.6),
          S.text((centres[2] + centres[3]) / 2, loop_y + 18,
                 "adaptation: slicer error feeds the equaliser", size=10,
                 fill=S.ACCENT_DARK, anchor="middle", weight=600))

    c.add(S.callout(36, loop_y + 38, 808, "The point of the diagram", note,
                    kind="accent"))
    return c.render()


FIGURES = {
    "ethernet-lineage": ethernet_lineage,
    "ethernet-lane-rates": ethernet_lane_rates,
    "ethernet-dsp-stack": ethernet_dsp_stack,
}
