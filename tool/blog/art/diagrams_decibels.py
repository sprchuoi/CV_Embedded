"""Hand-authored diagrams for chapter 04, "Decibels and Dynamic Range".

    decibel-ladder        the references, on one axis, so dBm/dBW/dBFS stop
                          being interchangeable in the reader's head
    dynamic-range-budget  where the ceiling and the floor come from in a chain
"""

from __future__ import annotations

from . import svg as S

# (label, level in dBm, kind) -- a receive chain from a strong local signal down
# to the thermal floor. dBm is the common currency here, and the figure says so.
LADDER = [
    ("+30 dBm", 30, "warn", "a few watts - transmitter output"),
    ("+10 dBm", 10, "warn", "10 mW - a strong local signal"),
    ("0 dBm", 0, "accent", "1 mW - the reference, by definition"),
    ("\u221230 dBm", -30, "note", "1 \u00b5W - a normal received level"),
    ("\u221260 dBm", -60, "note", "1 nW - a weak but usable signal"),
    ("\u2212100 dBm", -100, "optical", "10 pW - near the thermal floor"),
    ("\u2212174 dBm", -174, "optical", "kT in 1 Hz at 290 K"),
]


# --------------------------------------------------------------------------- #
# 1. the reference ladder
# --------------------------------------------------------------------------- #


def decibel_ladder() -> str:
    c = S.Canvas(880, 440, title="The decibel is a ratio; the suffix is the reference")
    c.heading("One axis, seven landmarks, and the references that name them")

    axis_x = 196
    top, bottom = 78, 336
    lo, hi = -180.0, 40.0

    def py(dbm):
        return bottom - (dbm - lo) / (hi - lo) * (bottom - top)

    c.add(S.line(axis_x, top, axis_x, bottom, stroke=S.INK, width=1.6),
          S.text(axis_x - 12, top - 14, "power", size=10, fill=S.MUTED,
                 anchor="middle", weight=700))

    # decade gridlines
    for dbm in range(-180, 41, 20):
        y = py(dbm)
        c.add(S.line(axis_x - 6, y, axis_x + 6, y, stroke=S.INK, width=1.1))
        if dbm % 40 == 0:
            c.add(S.line(axis_x - 6, y, 840, y, stroke=S.RULE_SOFT, width=1))

    for label, dbm, kind, note in LADDER:
        y = py(dbm)
        colour = {"warn": S.WARN, "accent": S.ACCENT, "note": S.NOTE,
                  "optical": S.OPTICAL}[kind]
        c.add(S.dot(axis_x, y, r=5, fill=colour),
              S.line(axis_x, y, 262, y, stroke=colour, width=1.6),
              S.text(272, y - 1, label, size=12, fill=colour, weight=700,
                     family=S.MONO),
              S.text(272 + len(label) * 7.6 + 14, y - 1, note, size=10,
                     fill=S.SOFT))

    c.add(S.text(axis_x - 12, bottom + 18, "\u2212174", size=9, fill=S.MUTED,
                 anchor="middle"),
          S.text(36, 62, "dBm  =  dB relative to 1 milliwatt", size=11,
                 fill=S.INK, weight=700),
          S.text(36, 400,
                 "Every one of these is a ratio to the same reference. "
                 "Change the reference and the whole axis shifts - which is the",
                 size=11, fill=S.SOFT, style="italic"),
          S.text(36, 418,
                 "mistake that makes dBFS, dBc and dBm/0.1 nm easy to confuse.",
                 size=11, fill=S.SOFT, style="italic"))
    return c.render()


# --------------------------------------------------------------------------- #
# 2. the dynamic range budget
# --------------------------------------------------------------------------- #


def dynamic_range_budget() -> str:
    note = ["The floor is dominated by the first stage that has gain, "
            "and no later block can lower it.",
            "An LNA after a lossy component inherits that component's noise "
            "floor - which is Friis, drawn as a picture."]
    c = S.Canvas(880, int(396 + S.callout_height(808, note, body_size=11.5) + 14),
                 title="Where a receiver's dynamic range comes from")
    c.heading("A ceiling set by the largest signal, a floor set by the smallest")

    stages = [
        ("Input", "any level", "plain"),
        ("LNA", "gain, noise", "accent"),
        ("Filter", "band-limit", "plain"),
        ("ADC", "5.5 ENOB", "optical"),
        ("DSP", "no OSNR added", "note"),
    ]
    box_w, gap, by, bh = 120, 30, 210, 66
    x0 = (880 - (len(stages) * box_w + (len(stages) - 1) * gap)) / 2
    for i, (title, subtitle, kind) in enumerate(stages):
        bx = x0 + i * (box_w + gap)
        c.add(S.block(bx, by, box_w, bh, title, subtitle, kind=kind,
                      title_size=12.5, subtitle_size=9.5))
        if i < len(stages) - 1:
            c.add(S.arrow(bx + box_w + 4, by + bh / 2, bx + box_w + gap - 4,
                          by + bh / 2, stroke=S.MUTED, width=1.5))

    # --- ceiling and floor bars --------------------------------------------
    left, right = 92, 800
    ceil_y, floor_y = 118, 330

    c.add(S.line(left, ceil_y, right, ceil_y, stroke=S.WARN, width=2.4),
          S.text(left, ceil_y - 18, "CEILING - the largest signal the chain "
                                    "handles before it clips or compresses",
                 size=10.5, fill=S.WARN, weight=700),
          S.line(left, floor_y, right, floor_y, stroke=S.NOTE, width=2.4),
          S.text(left, floor_y + 26, "FLOOR - the sum of every noise source: "
                                     "thermal, quantisation, LO RIN",
                 size=10.5, fill=S.NOTE, weight=700))

    # The dynamic range itself, drawn in the right margin clear of the blocks.
    marker = 838
    c.add(S.line(marker, ceil_y, marker, floor_y, stroke=S.ACCENT, width=2.4),
          S.line(marker - 7, ceil_y, marker + 7, ceil_y, stroke=S.ACCENT, width=2),
          S.line(marker - 7, floor_y, marker + 7, floor_y, stroke=S.ACCENT, width=2),
          S.text(marker - 14, (ceil_y + floor_y) / 2, "dynamic range", size=11.5,
                 fill=S.ACCENT_DARK, weight=700, rotate=-90))

    # where each end comes from
    c.add(S.text(92, 88, "set by: ADC full scale, TIA saturation, "
                         "photodiode overload", size=9.5, fill=S.MUTED),
          S.text(92, 370, "set by: TIA noise, ADC quantisation, "
                          "LO relative intensity noise", size=9.5, fill=S.MUTED))

    c.add(S.callout(36, 396, 808, "Why the order of the blocks matters", note,
                    kind="accent"))
    return c.render()


FIGURES = {
    "decibel-ladder": decibel_ladder,
    "dynamic-range-budget": dynamic_range_budget,
}
