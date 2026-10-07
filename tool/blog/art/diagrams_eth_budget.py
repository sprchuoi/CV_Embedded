"""Hand-authored diagrams for the Ethernet gain and link-budget chapter.

    ethernet-loss-budget   the loss stack from transmitter to slicer, drawn as
                           a waterfall so "gain" is visibly a subtraction
    ethernet-loss-standards insertion loss at Nyquist for the real media, so the
                           numbers stop being abstract
    equaliser-inverts-channel  what the equaliser is for, as a picture

The chapter takes the two words readers arrive with -- "gain" and "loss" -- and
makes them concrete: insertion loss that depends on frequency, a Nyquist
frequency that decides which part of that curve matters, and a margin that is
signed off in decibels.
"""

from __future__ import annotations

from . import svg as S

# (standard, media, reach, insertion loss at Nyquist, Nyquist frequency)
MEDIA = [
    ("100BASE-TX", "cat5 UTP", "100 m", 12.0, "62.5 MHz"),
    ("1000BASE-T", "cat5e UTP", "100 m", 24.5, "125 MHz"),
    ("10GBASE-T", "cat6a UTP", "100 m", 45.0, "400 MHz"),
    ("10GBASE-KR", "backplane", "1 m", 22.0, "5.16 GHz"),
    ("25G / 100G lane", "short copper", "3 m", 26.0, "12.9 GHz"),
]


def ethernet_loss_budget() -> str:
    note = [
        "Read it left to right: the transmitter launches a level, the media "
        "removes most of it before the receiver sees anything, and the "
        "equaliser is what buys the level back -- at the Nyquist frequency, "
        "which is why the number is quoted there and not at DC.",
        "The recovered signal is not the launched signal. The equaliser "
        "restores the shape by boosting high frequencies, and it boosts the "
        "noise that lives there with them. That residue is the whole subject "
        "of the eye diagram and BERT chapters.",
    ]
    c = S.Canvas(880, int(452 + S.callout_height(808, note, body_size=11.5) + 14),
                 title="Where the signal goes, from driver to slicer")

    left, right = 118, 806
    base, top = 318, 96
    lo, hi = -30.0, 4.0            # dBm

    def py(dbm):
        return base - (dbm - lo) / (hi - lo) * (base - top)

    for dbm in (0, -6, -12, -18, -24, -30):
        y = py(dbm)
        c.add(S.line(left - 6, y, right, y, stroke=S.RULE_SOFT, width=1),
              S.text(left - 12, y, f"{dbm}", size=9.5, fill=S.MUTED,
                     anchor="end", family=S.MONO))
    c.add(S.text(left - 12, 74, "dBm", size=10, fill=S.MUTED, anchor="end",
                 weight=700))
    # The reference for every level, parked above the grid so it cannot collide
    # with the step labels that sit under the plot area.
    c.add(S.text(left, 62, "levels referenced to the launched amplitude, "
                           "at the Nyquist frequency, for a 10GBASE-T lane",
                 size=9.5, fill=S.MUTED))

    # (label, level after this step, bar colour, is the level a loss?)
    steps = [
        ("TX drive\nrise time", 0.0, S.NOTE, False),
        ("media\n(45 dB cat6a)", -22.5, S.WARN, True),
        ("connector\n+ reflections", -24.5, S.WARN, True),
        ("crosstalk\n(4 pairs)", -27.0, S.WARN, True),
        ("equaliser\ngain", -6.0, S.ACCENT, False),
        ("slicer\nSNR 21 dB", -6.0, S.OPTICAL, False),
    ]

    step_w = (right - left) / len(steps)
    prev_level = None
    for i, (label, level, colour, is_loss) in enumerate(steps):
        x = left + i * step_w
        # draw the drop from the previous level to this one
        if prev_level is not None:
            c.add(S.rect(x, py(max(prev_level, level)), step_w * 0.62,
                         abs(py(level) - py(prev_level)),
                         fill=colour, stroke=None, rx=3, opacity=0.35))
            c.add(S.line(x, py(prev_level), x + step_w * 0.62, py(prev_level),
                         stroke=colour, width=1.4))
        c.add(S.line(x, py(level), x + step_w * 0.62, py(level), stroke=colour,
                     width=2.4),
              S.dot(x + step_w * 0.31, py(level), r=4.4, fill=colour))
        for j, line in enumerate(label.split("\n")):
            c.add(S.text(x + step_w * 0.31, base + 20 + j * 14, line, size=9.5,
                         fill=colour if j == 0 else S.MUTED, anchor="middle",
                         weight=700 if j == 0 else 400))
        if prev_level is not None and is_loss:
            c.add(S.text(x + step_w * 0.31, py((prev_level + level) / 2) + 2,
                         f"{level - prev_level:.1f} dB", size=9.5,
                         fill=S.WARN, anchor="middle", weight=700,
                         family=S.MONO))
        elif prev_level is not None:
            c.add(S.text(x + step_w * 0.31, py((prev_level + level) / 2) + 2,
                         f"+{level - prev_level:.1f} dB", size=9.5,
                         fill=S.ACCENT_DARK, anchor="middle", weight=700,
                         family=S.MONO))
        prev_level = level

    # the two horizontal lines that make the point: launched vs recovered
    for level, label, colour in ((0.0, "launched", S.NOTE),
                                 (-6.0, "recovered", S.OPTICAL)):
        c.add(S.line(left, py(level), right, py(level), stroke=colour, width=1.3,
                     dash="4 4"),
              S.text(right, py(level) - 11, label, size=9.5, fill=colour,
                     anchor="end", weight=700))

    c.add(S.callout(36, 356, 808, "The one number the room argues about", note,
                    kind="warn"))
    return c.render()


def ethernet_loss_standards() -> str:
    note = [
        "A 100 m UTP link is a low-pass filter with a corner far below its "
        "data rate. 10GBASE-T runs 400 MHz of Nyquist bandwidth through a "
        "cable specified only to 500 MHz, and the standard permits 45 dB of "
        "loss at the top of that band.",
        "A backplane lane is shorter but its loss is far steeper with "
        "frequency. The 10GBASE-KR channel is allowed about 22 dB at "
        "5.16 GHz; at 25G the same board is asked for around 26 dB at "
        "12.9 GHz. Loss that grows with frequency is exactly what an FFE is "
        "for, and exactly what makes it amplify noise.",
    ]
    c = S.Canvas(880, int(430 + S.callout_height(808, note, body_size=11.5) + 14),
                 title="Insertion loss at Nyquist, and the frequency it is quoted at")

    x_name, x_bar = 40, 300
    y0, dy = 104, 52
    bar_h, max_loss = 20, 50.0
    bar_max = 300

    c.add(S.text(x_bar, y0 - 22, "insertion loss at Nyquist (dB)", size=10.5,
                 fill=S.MUTED, weight=700),
          S.text(x_bar + bar_max + 60, y0 - 22, "Nyquist frequency",
                 size=10.5, fill=S.MUTED, weight=700))

    for i, (name, media, reach, loss, nyq) in enumerate(MEDIA):
        y = y0 + i * dy
        c.add(S.text(x_name, y + bar_h / 2, name, size=11.5, fill=S.INK,
                     weight=700),
              S.text(x_name, y + bar_h / 2 + 15, f"{media}, {reach}", size=9.5,
                     fill=S.MUTED))
        w = loss / max_loss * bar_max
        colour = S.ACCENT if loss < 30 else (S.WARN if loss < 40 else S.OPTICAL)
        c.add(S.rect(x_bar, y, w, bar_h, fill=colour, stroke=None, rx=4),
              S.text(x_bar + w + 9, y + bar_h / 2, f"{loss:g} dB", size=10.5,
                     fill=colour, weight=700, family=S.MONO),
              S.text(x_bar + bar_max + 60, y + bar_h / 2, nyq, size=10.5,
                     fill=S.SOFT, family=S.MONO))

    c.add(S.callout(36, 336, 808, "Why the Nyquist column matters as much as the loss",
                    note, kind="note"))
    return c.render()


def equaliser_inverts_channel() -> str:
    note = [
        "Magnitudes multiply and decibels add, so inverting a channel on a "
        "decibel axis is a subtraction. The equaliser is not a filter someone "
        "chose -- its magnitude response is the channel's, reflected.",
        "The shaded gap is the cost. Above the crossing the equaliser is "
        "boosting, and every decibel of boost is a decibel of added noise and "
        "a decibel of extra dynamic range demanded from the ADC.",
    ]
    c = S.Canvas(880, int(438 + S.callout_height(808, note, body_size=11.5) + 14),
                 title="The equaliser's job: invert the channel where it matters")

    left, right = 118, 700
    base, top = 300, 92
    lo, hi = -38.0, 38.0

    def py(db):
        return base - (db - lo) / (hi - lo) * (base - top)

    c.add(S.axis(left, base, right, top, xlabel="frequency", ylabel="gain (dB)",
                 xticks=[(left, "DC"), (left + (right - left) * 0.35, "f"),
                         (right, "f~Nyq~")],
                 yticks=[(py(0), "0"), (py(-20), "\u221220"),
                         (py(-35), "\u221235"), (py(20), "+20"),
                         (py(35), "+35")]))

    # channel: a low-pass that rolls off, drawn as a straight dB line then a
    # knee. It bottoms out at -32 dB so its mirror stays inside the canvas.
    ch = [(left, 0.0), (left + (right - left) * 0.22, -3.0),
          (left + (right - left) * 0.55, -17.0), (right, -32.0)]
    c.add(S.polyline([(x, py(v)) for x, v in ch], stroke=S.WARN, width=2.6),
          S.text(left + 8, py(-30), "channel |H(f)|", size=10.5,
                 fill=S.WARN, weight=700))

    # The equaliser is the channel mirrored about 0 dB: loss becomes gain.
    eq = [(x, -v) for x, v in ch]
    c.add(S.polyline([(x, py(v)) for x, v in eq], stroke=S.ACCENT, width=2.6,
                     dash="7 4"),
          S.text(left + 8, py(30), "equaliser 1/H(f)", size=10.5,
                 fill=S.ACCENT_DARK, weight=700))

    # the shaded boost region between them
    c.add(S.path(
        " ".join([f"M {left:.1f} {py(0):.1f}"] +
                 [f"L {x:.1f} {py(v):.1f}" for x, v in ch]) + " Z",
        fill=S.ACCENT, opacity=0.10, stroke=None),
        # parked low and left, clear of the curve it annotates
        S.text(left + (right - left) * 0.30, py(-8), "the boost the equaliser "
               "must supply", size=10, fill=S.ACCENT_DARK, anchor="middle"))

    c.add(S.line(left, py(0), right, py(0), stroke=S.RULE, width=1.2))
    c.add(S.text(right + 6, py(0), "0 dB", size=9.5, fill=S.MUTED,
                 family=S.MONO),
          S.text(right + 6, py(-17) - 6, "\u221217 dB", size=9.5,
                 fill=S.MUTED, family=S.MONO),
          S.text(right + 6, py(-17) + 8, "channel at f", size=9.5,
                 fill=S.MUTED, family=S.MONO))

    c.add(S.callout(36, 344, 808, "What the boost costs", note, kind="accent"))
    return c.render()


FIGURES = {
    "ethernet-loss-budget": ethernet_loss_budget,
    "ethernet-loss-standards": ethernet_loss_standards,
    "equaliser-inverts-channel": equaliser_inverts_channel,
}
