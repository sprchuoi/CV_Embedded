"""Hand-authored diagrams for the eye-diagram chapter.

    eye-diagram-anatomy   one UI of an NRZ eye with every parameter labelled, so
                          the vocabulary is attached to a position on a picture
    eye-histogram-view    how the two measurements that matter are extracted:
                          a vertical histogram for height, a horizontal for jitter
    pam4-eye-levels       the same channel carrying four levels: three eyes,
                          one third the height, and the two that close first

The chapter is about reading a picture, not deriving one. These figures put the
names on the picture first; the computed eye diagrams in ``plots_eth_eye`` then
show the same picture with real ISI in it.
"""

from __future__ import annotations

from . import svg as S


def _eye_outline(c, x0, x1, y0, y1, *, level=0.0, colour=S.ACCENT,
                 opening_top=None, opening_bot=None, width=2.4):
    """An idealised NRZ eye outline: two crossing arcs, drawn as bezier paths.

    ``opening_top`` / ``opening_bot`` are the y coordinates of the eye opening;
    when omitted they default to a generous 45% of the box.
    """
    mid = (y0 + y1) / 2
    top = opening_top if opening_top is not None else mid - (mid - y0) * 0.45
    bot = opening_bot if opening_bot is not None else mid + (mid - y0) * 0.45
    span = x1 - x0
    # upper arc: from the left at the top rail, dipping to the eye top and back
    c.add(S.path(
        f"M {x0} {y0} C {x0 + span * 0.28} {y0}, {x0 + span * 0.30} {top}, "
        f"{x0 + span * 0.5} {top} "
        f"C {x0 + span * 0.70} {top}, {x0 + span * 0.72} {y0}, {x1} {y0}",
        stroke=colour, width=width, fill="none"))
    # lower arc: the mirror
    c.add(S.path(
        f"M {x0} {y1} C {x0 + span * 0.28} {y1}, {x0 + span * 0.30} {bot}, "
        f"{x0 + span * 0.5} {bot} "
        f"C {x0 + span * 0.70} {bot}, {x0 + span * 0.72} {y1}, {x1} {y1}",
        stroke=colour, width=width, fill="none"))
    return top, bot


def eye_diagram_anatomy() -> str:
    note = [
        "Eye height is a voltage margin; eye width is a time margin. Both "
        "are quoted at the sampling instant and with the mask's own "
        "definition of where the eye starts and stops -- change the "
        "definition and the number moves without the link changing.",
        "The crossing points are where the two rails meet, and the jitter "
        "around them is what closes the eye horizontally. Noise opens the "
        "eye vertically only in the sense that it blurs the rails: the "
        "opening is what survives.",
    ]
    c = S.Canvas(880, int(566 + S.callout_height(808, note, body_size=11.5) + 14),
                 title="One unit interval of an NRZ eye, fully labelled")

    x0, x1 = 150, 700
    y0, y1 = 110, 340
    mid = (y0 + y1) / 2
    top, bot = _eye_outline(c, x0, x1, y0, y1)

    # rails
    c.add(S.line(x0 - 26, y0, x1 + 26, y0, stroke=S.RULE, width=1.2, dash="4 4"),
          S.line(x0 - 26, y1, x1 + 26, y1, stroke=S.RULE, width=1.2, dash="4 4"),
          S.text(x0 - 34, y0, "logic 1", size=10, fill=S.MUTED, anchor="end"),
          S.text(x0 - 34, y1, "logic 0", size=10, fill=S.MUTED, anchor="end"))

    # eye height: a vertical arrow left of the sampling line, with its label
    # parked further left so neither collides with the crossing labels.
    cxm = (x0 + x1) / 2
    hx = x0 + (x1 - x0) * 0.26
    c.add(S.line(hx, y0, hx, top, stroke=S.RULE_SOFT, width=2, dash="3 3"),
          S.arrow(hx, top, hx, bot, stroke=S.NOTE, width=1.8),
          S.arrow(hx, bot, hx, top, stroke=S.NOTE, width=1.8),
          S.text(hx + 14, mid - 12, "eye height", size=11, fill=S.NOTE_DARK,
                 weight=700),
          S.text(hx + 14, mid + 3, "voltage margin", size=9.5, fill=S.MUTED))

    # eye width: a horizontal arrow across the opening, left of the sampling line
    opening_left = x0 + (x1 - x0) * 0.30
    opening_right = x0 + (x1 - x0) * 0.70
    wline_y = mid - 66
    c.add(S.line(opening_left, wline_y, opening_right, wline_y,
                 stroke=S.ACCENT, width=1.8),
          S.dot(opening_left, wline_y, r=4, fill=S.ACCENT),
          S.dot(opening_right, wline_y, r=4, fill=S.ACCENT),
          S.text(opening_left - 12, wline_y, "eye width", size=11,
                 fill=S.ACCENT_DARK, anchor="end", weight=700))

    # sampling instant
    c.add(S.line(cxm, y0 - 26, cxm, y1 + 26, stroke=S.OPTICAL, width=1.6,
                 dash="6 4"),
          S.text(cxm, y1 + 46, "sampling instant", size=10.5, fill=S.OPTICAL,
                 anchor="middle", weight=700))

    # crossing points and the jitter around them
    for xc in (opening_left, opening_right):
        c.add(S.dot(xc, mid - 20, r=4.5, fill=S.WARN),
              S.line(xc - 16, mid - 20, xc + 16, mid - 20, stroke=S.WARN,
                     width=1.2, dash="3 3"))
    c.add(S.text(opening_left - 22, mid - 20, "crossing", size=10,
                 fill=S.WARN, anchor="end", weight=700),
          S.text(opening_right + 22, mid - 20, "crossing", size=10,
                 fill=S.WARN, anchor="start", weight=700),
          S.text(cxm + 20, mid + 88, "jitter around the crossing", size=10,
                 fill=S.WARN, anchor="start", weight=700))

    # unit interval bracket, kept clear of the callout below
    c.add(S.line(x0, y1 + 86, x1, y1 + 86, stroke=S.MUTED, width=1.4),
          S.line(x0, y1 + 80, x0, y1 + 92, stroke=S.MUTED, width=1.4),
          S.line(x1, y1 + 80, x1, y1 + 92, stroke=S.MUTED, width=1.4),
          S.text((x0 + x1) / 2, y1 + 104,
                 "one unit interval (UI) = 1 / baud rate", size=10.5,
                 fill=S.MUTED, anchor="middle"))

    c.add(S.callout(36, 492, 808, "Height and width are different currencies",
                    note, kind="accent"))
    return c.render()


def eye_histogram_view() -> str:
    note = [
        "A scope does not measure an eye, it measures a histogram of it. The "
        "vertical histogram inside the opening gives height; the horizontal "
        "histogram at the crossing gives jitter; BER is the area of the "
        "histogram tails beyond the slicer threshold.",
        "That last sentence is the bridge to the BERT chapter: an eye "
        "measurement and a BER measurement are two views of the same "
        "distribution, and the bathtub curve is the horizontal histogram "
        "redrawn as a function of where you put the sampling clock.",
    ]
    c = S.Canvas(880, int(452 + S.callout_height(808, note, body_size=11.5) + 14),
                 title="Where the numbers come from: two histograms")

    # left: eye with a vertical slice
    x0, x1 = 96, 470
    y0, y1 = 104, 316
    mid = (y0 + y1) / 2
    top, bot = _eye_outline(c, x0, x1, y0, y1)
    cxm = (x0 + x1) / 2
    c.add(S.rect(cxm - 26, top, 52, bot - top, fill=S.NOTE, stroke=S.NOTE,
                 rx=3, opacity=0.10, width=1.2))
    c.add(S.text((x0 + x1) / 2, y1 + 30, "vertical slice at the sampling "
                 "instant", size=10, fill=S.NOTE_DARK, anchor="middle",
                 weight=600))
    # the histogram that slice produces
    hx = x1 + 34
    c.add(S.axis(hx, y1, hx + 118, y0, xlabel="counts", ylabel=None,
                 xticks=[], yticks=[(y0, "1"), (y1, "0")]))
    for label, yc, colour in (("logic 1 rail", y0 + 8, S.ACCENT),
                              ("logic 0 rail", y1 - 8, S.WARN)):
        for i in range(9):
            h = 6 + (8 - abs(i - 4)) * 7
            yy = yc - 4 + i
            c.add(S.line(hx + 2, yy, hx + 2 + h, yy, stroke=colour, width=1.6))
        c.add(S.text(hx + 126, yc, label, size=9.5, fill=colour, weight=600))
    c.add(S.line(hx + 2, mid - 9, hx + 2, mid + 9, stroke=S.OPTICAL, width=1.6,
                 dash="3 3"),
          S.text(hx + 126, mid, "threshold", size=9.5, fill=S.OPTICAL,
                 weight=600))

    # right: eye with a horizontal slice, and the bathtub it produces
    bx0, bx1 = 470, 844
    by0, by1 = 104, 316
    bmid = (by0 + by1) / 2
    _eye_outline(c, bx0, bx1, by0, by1, colour=S.RULE)
    c.add(S.line(bx0, bmid, bx1, bmid, stroke=S.WARN, width=1.6, dash="5 4"),
          S.text(bx0, by0 - 16, "horizontal slice at the threshold", size=10,
                 fill=S.WARN, weight=600))
    # bathtub: BER against phase, drawn in the lower half of the right panel
    tub_y0, tub_y1 = by0 + 40, by1 - 10
    pts = []
    for i in range(61):
        u = i / 60
        # two walls: high in the middle, falling at both edges
        d = min(abs(u - 0.32), abs(u - 0.68))
        v = 1.0 - min(1.0, d / 0.30)
        pts.append((bx0 + 20 + u * (bx1 - bx0 - 40),
                    tub_y1 - (v ** 2.2) * (tub_y1 - tub_y0)))
    c.add(S.polyline(pts, stroke=S.OPTICAL, width=2.4),
          S.text((bx0 + bx1) / 2, tub_y0 - 8, "BER against sampling phase "
                 "(the bathtub)", size=10, fill=S.OPTICAL_DARK,
                 anchor="middle", weight=600),
          S.text(bx0 + 24, tub_y1 - 6, "left edge", size=9, fill=S.MUTED),
          S.text(bx1 - 24, tub_y1 - 6, "right edge", size=9, fill=S.MUTED,
                 anchor="end"))

    c.add(S.callout(36, 378, 808, "The two chapters in one picture", note,
                    kind="note"))
    return c.render()


def pam4_eye_levels() -> str:
    note = [
        "PAM4 spends the same voltage range on three eyes instead of one, so "
        "each eye is a third the height: an ideal 6 dB penalty in amplitude "
        "margin, paid for one extra bit per symbol. That is the whole trade, "
        "and it is why PAM4 arrived with FEC rather than instead of it.",
        "The top and bottom eyes are the survivors -- they are bounded by a "
        "rail on one side. The middle eye is bounded by two transitions and "
        "closes first, so it is where a real receiver starts making errors.",
    ]
    c = S.Canvas(880, int(486 + S.callout_height(808, note, body_size=11.5) + 14),
                 title="Same channel, four levels, three eyes")

    x0, x1 = 128, 800
    base, top = 344, 92
    levels = [0.0, 1 / 3, 2 / 3, 1.0]

    c.add(S.text(x0 - 14, top - 22, "level 3", size=10, fill=S.MUTED,
                 anchor="end"),
          S.text(x0 - 14, base + 4, "level 0", size=10, fill=S.MUTED,
                 anchor="end"))

    # the three eyes, stacked. Deliberately idealised: the computed figure
    # (plots_eth_eye) is where the real closure lives.
    span = x1 - x0
    for i in range(3):
        y_hi = base - (levels[i + 1]) * (base - top)
        y_lo = base - (levels[i]) * (base - top)
        colour = S.ACCENT if i == 1 else S.NOTE
        _eye_outline(c, x0, x1, y_hi, y_lo, colour=colour, width=2.0)
        c.add(S.text(x1 + 14, (y_hi + y_lo) / 2, f"eye {i}", size=10.5,
                     fill=colour, weight=700))

    # level separators and the level-spacing arrows
    arrow_x = x0 - 40
    for i, lv in enumerate(levels):
        y = base - lv * (base - top)
        c.add(S.line(x0 - 20, y, x1 + 20, y, stroke=S.RULE, width=1.1,
                     dash="4 4"))
        c.add(S.text(arrow_x - 6, y, f"L{i}", size=10, fill=S.INK,
                     anchor="end", family=S.MONO))
    for i in range(3):
        y_hi = base - levels[i + 1] * (base - top)
        y_lo = base - levels[i] * (base - top)
        c.add(S.arrow(arrow_x, y_lo, arrow_x, y_hi, stroke=S.WARN, width=1.6))

    c.add(S.text(x0 - 74, (top + base) / 2, "one third of the swing per eye",
                 size=10, fill=S.WARN, anchor="middle", rotate=-90, weight=600))

    # the middle eye's extra penalty
    c.add(S.text((x0 + x1) / 2, base + 40,
                 "6 dB amplitude penalty for 2x the bits  \u2192  FEC pays it "
                 "back", size=11, fill=S.OPTICAL_DARK, anchor="middle",
                 weight=700))

    c.add(S.callout(36, 412, 808, "Why the middle eye is the one that fails",
                    note, kind="optical"))
    return c.render()


FIGURES = {
    "eye-diagram-anatomy": eye_diagram_anatomy,
    "eye-histogram-view": eye_histogram_view,
    "pam4-eye-levels": pam4_eye_levels,
}
