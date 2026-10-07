"""Hand-authored diagrams for the SerDes-in-a-module chapter.

    module-data-path     the two electrical edges of a module and the channel
                         each one crosses, drawn as one signal path
    retiming-modes       retimed, gearbox and direct-drive architectures side by
                         side, which is the module's first design decision
    module-interfaces    what the host expects, what the line expects, and the
                         lane arithmetic in between

The chapter's claim is that an optical module is an interface problem wearing an
optics hat: the DSP's most constrained resources are the serial lanes it faces,
not the equaliser it contains.
"""

from __future__ import annotations

from . import svg as S


def module_data_path() -> str:
    note = [
        "The host edge and the line edge are different channels with "
        "different specifications, and a module must satisfy both. The host "
        "edge crosses a connector, a cage and tens of millimetres of PCB; the "
        "line edge crosses a few millimetres of flex or a direct die-to-optics "
        "attachment.",
        "Everything between those two edges is the module's own problem. A "
        "retimed module puts the full DSP in the middle; a gearbox module "
        "puts only lane conversion there. The choice sets the module's power, "
        "latency and cost before a single equaliser tap is chosen.",
    ]
    c = S.Canvas(880, int(492 + S.callout_height(808, note, body_size=11.5) + 14),
                 title="A module has two electrical edges")

    # two channel bands
    band_x0, band_x1 = 210, 670
    c.add(S.rect(band_x0, 84, band_x1 - band_x0, 30, fill=S.WARN_WASH,
                 stroke=S.WARN, rx=4, width=1.2, dash="5 4"),
          S.text((band_x0 + band_x1) / 2, 99, "host channel: cage, connector, "
                 "PCB traces", size=10, fill=S.WARN, anchor="middle",
                 weight=600))
    c.add(S.rect(band_x0, 348, band_x1 - band_x0, 30, fill=S.OPTICAL_WASH,
                 stroke=S.OPTICAL, rx=4, width=1.2, dash="5 4"),
          S.text((band_x0 + band_x1) / 2, 363, "line-side attachment: flex, "
                 "via, or direct", size=10, fill=S.OPTICAL, anchor="middle",
                 weight=600))

    # the signal path
    stages = [
        (40, "Host\ntransmitter", "its own SerDes", "plain"),
        (250, "Host edge\nRX + CDR", "equalise, retime", "note"),
        (440, "Module DSP", "FEC, gearbox,\nline coding", "accent"),
        (630, "Optics\ndriver", "EAM / MZM / DML", "optical"),
    ]
    box_w, box_h, by = 140, 96, 168
    centres = []
    for x, title, sub, kind in stages:
        centres.append(x + box_w / 2)
        c.add(S.block(x, by, box_w, box_h, title.replace("\n", " "), kind=kind,
                      title_size=11.5))
        for j, line in enumerate(sub.split("\n")):
            c.add(S.text(x + box_w / 2, by + box_h / 2 + 26 + j * 14, line,
                         size=9.5, fill=S.SOFT, anchor="middle"))

    c.add(S.arrow(184, by + box_h / 2, 246, by + box_h / 2, stroke=S.MUTED,
                  width=1.6),
          S.text(215, by - 12, "100G/lane", size=9,
                 fill=S.MUTED, anchor="middle", family=S.MONO))
    c.add(S.arrow(394, by + box_h / 2, 436, by + box_h / 2, stroke=S.MUTED,
                  width=1.6))
    c.add(S.arrow(584, by + box_h / 2, 626, by + box_h / 2, stroke=S.MUTED,
                  width=1.6))

    # the fibre, leaving the module
    c.add(S.arrow(774, by + box_h / 2, 846, by + box_h / 2, stroke=S.OPTICAL,
                  width=2.0),
          S.text(810, by + box_h / 2 - 18, "fibre", size=10, fill=S.OPTICAL,
                 anchor="middle", weight=700))

    # the module boundary, drawn around the two edges it contains
    c.add(S.rect(224, 146, 566, 138, fill="none", stroke=S.INK, rx=10,
                 width=1.6, dash="8 5"),
          S.text(790, 298, "the module boundary", size=10.5, fill=S.INK,
                 anchor="end", weight=700))

    # the two edges, named inside the boundary and clear of its dashes
    c.add(S.text(centres[1], by - 30, "host edge", size=11.5, fill=S.NOTE_DARK,
                 anchor="middle", weight=700),
          S.line(centres[1], by - 20, centres[1], by - 4, stroke=S.NOTE,
                 width=1.4, dash="3 3"),
          S.text(centres[2], by - 30, "line edge", size=11.5,
                 fill=S.OPTICAL_DARK, anchor="middle", weight=700),
          S.line(centres[2], by - 20, centres[2], by - 4, stroke=S.OPTICAL,
                 width=1.4, dash="3 3"))

    c.add(S.callout(36, 404, 808, "Why the two edges are separate problems",
                    note, kind="accent"))
    return c.render()


def retiming_modes() -> str:
    note = [
        "The three architectures differ in what sits between the two edges. "
        "A retimed module regenerates the signal completely, so host-side "
        "impairments do not reach the optics. A gearbox converts lane count "
        "and rate but not timing. A direct-drive module passes the host's "
        "signal to the optics with analogue shaping only.",
        "The choice is a power and latency trade, and it is made early. Full "
        "retiming costs the most power and adds latency; it also buys the "
        "most margin, which is why long-reach coherent modules are retimed "
        "and short-reach pluggables frequently are not.",
    ]
    c = S.Canvas(880, int(478 + S.callout_height(808, note, body_size=11.5) + 14),
                 title="Three ways to build the middle of a module")

    rows = [
        ("Retimed", ["Host SerDes RX", "CDR + retime", "DSP + FEC", "Optics TX"],
         "accent", "full regeneration", "most power, most margin"),
        ("Gearbox", ["Host SerDes RX", "lane / rate convert", "Optics TX"],
         "note", "no timing regeneration", "medium power, rate adaptation"),
        ("Direct drive", ["Host SerDes RX", "analogue shaping", "Optics TX"],
         "warn", "no retiming at all", "least power, least margin"),
    ]

    y0, dy = 108, 116
    for i, (name, stages, kind, note1, note2) in enumerate(rows):
        y = y0 + i * dy
        c.add(S.rect(36, y, 164, 92, fill=S.PANEL, stroke=S.RULE, rx=8,
                     width=1.3),
              S.text(118, y + 30, name, size=13, fill=S.INK, anchor="middle",
                     weight=700),
              S.text(118, y + 52, note1, size=9.5, fill=S.SOFT,
                     anchor="middle"),
              S.text(118, y + 70, note2, size=9.5, fill=S.MUTED,
                     anchor="middle", style="italic"))

        bw, gap = 156, 18
        x = 224
        for j, label in enumerate(stages):
            c.add(S.block(x, y + 14, bw, 62, label, kind=kind, title_size=11))
            if j < len(stages) - 1:
                c.add(S.arrow(x + bw + 2, y + 45, x + bw + gap - 2, y + 45,
                              stroke=S.MUTED, width=1.4))
            x += bw + gap

        # the fibres leaving each row
        c.add(S.line(x - gap + 2, y + 45, x + 26, y + 45, stroke=S.OPTICAL,
                     width=1.8),
              S.text(x + 32, y + 45, "fibre", size=9.5, fill=S.OPTICAL,
                     weight=600))

    c.add(S.callout(36, 462, 808, "The decision that precedes every other",
                    note, kind="note"))
    return c.render()


def module_interfaces() -> str:
    note = [
        "A module's lane count is an integer constraint on everything else. "
        "400G over 8 electrical lanes at 50G per lane, or 4 lanes at 100G; "
        "800G needs 8 lanes at 100G. The optics side may want a different "
        "split again, and every mismatch has to be resolved somewhere in the "
        "middle.",
        "The arithmetic is worth doing before anything else, because it "
        "decides the SerDes count, the package routing, the crosstalk "
        "environment and the power. Getting it wrong is not a tuning problem, "
        "it is a redesign.",
    ]
    c = S.Canvas(880, int(486 + S.callout_height(808, note, body_size=11.5) + 14),
                 title="The lane arithmetic a module has to resolve")

    # three columns: host interface, conversion, line side
    cols = [
        (52, "host edge", ["8 x 50G NRZ", "8 x 100G PAM4", "4 x 100G PAM4"],
         "note"),
        (352, "what has to change", ["lane count", "baud rate", "modulation",
                                     "FEC framing", "skew and deskew"],
         "accent"),
        (640, "line side", ["1 x 400G PAM4", "1 x 800G PAM4", "2 x 200G PAM4"],
         "optical"),
    ]
    for x, title, items, kind in cols:
        c.add(S.block(x, 92, 188, 40, title, kind=kind, title_size=11.5))
        for j, item in enumerate(items):
            c.add(S.rect(x, 146 + j * 40, 188, 32, fill=S.PANEL,
                         stroke=S.RULE, rx=6, width=1.1),
                  S.text(x + 94, 162 + j * 40, item, size=10.5, fill=S.INK,
                         anchor="middle", family=S.MONO))

    c.add(S.arrow(244, 112, 348, 112, stroke=S.MUTED, width=1.6),
          S.arrow(544, 112, 636, 112, stroke=S.MUTED, width=1.6))

    # the total, worked once
    c.add(S.rect(52, 372, 776, 54, fill=S.ACCENT_WASH, stroke=S.ACCENT,
                 rx=6, width=1.2),
          S.text(72, 390, "800G module, worked once:", size=11,
                 fill=S.ACCENT_DARK, weight=700),
          S.text(72, 410, "8 lanes x 106.25 GBd PAM4 = 850 Gbit/s raw -> 800G "
                 "after FEC and framing overhead", size=11,
                 fill=S.INK, family=S.MONO))

    c.add(S.callout(36, 446, 808, "Why the middle column is the hard one",
                    note, kind="accent"))
    return c.render()


FIGURES = {
    "module-data-path": module_data_path,
    "retiming-modes": retiming_modes,
    "module-interfaces": module_interfaces,
}
