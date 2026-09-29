"""Hand-authored diagrams for the coherent optical DSP chapter.

    coherent-receiver-dsp-chain   the whole receiver, optical front end to FEC
    ninety-degree-hybrid          how optics produces a complex baseband signal
    fde-overlap-save              the frequency-domain equaliser, and why it wins
    cma-butterfly                 the 2x2 adaptive equaliser that untangles polarization
"""

from __future__ import annotations

from . import svg as S


# --------------------------------------------------------------------------- #
# 1. the receiver DSP chain
# --------------------------------------------------------------------------- #


def coherent_receiver_dsp_chain() -> str:
    c = S.Canvas(920, 486, title="The coherent optical receiver, from hybrid to FEC")
    c.heading("Every chapter of this blog, in series, at 64 GBd")

    # ---------------- optical front end ------------------------------------
    front = [
        ("Signal + LO", "1550 nm, one carrier", "plain"),
        ("90\u00b0 hybrid", "4 optical outputs", "optical"),
        ("Balanced PDs", "I and Q photocurrents", "optical"),
        ("ADC", "2 Sa/symbol, 8-9 bit", "accent"),
    ]
    fw, fgap, fy, fh = 170, 40, 96, 62
    fx0 = (920 - (len(front) * fw + (len(front) - 1) * fgap)) / 2
    for i, (title, subtitle, kind) in enumerate(front):
        bx = fx0 + i * (fw + fgap)
        c.add(S.block(bx, fy, fw, fh, title, subtitle, kind=kind))
        if i < len(front) - 1:
            c.add(S.arrow(bx + fw + 6, fy + fh / 2, bx + fw + fgap - 6, fy + fh / 2,
                          stroke=S.MUTED, width=1.6))

    # ---------------- the hand-off -----------------------------------------
    drop_x = fx0 + 3 * (fw + fgap) + fw / 2
    c.add(S.arrow_path([(drop_x, fy + fh + 4), (drop_x, 216), (85, 216), (85, 286)],
                       stroke=S.ACCENT, width=2.0),
          S.tag(drop_x - 66, 196, "complex samples, I + jQ", kind="accent", size=9.5))

    # ---------------- DSP chain --------------------------------------------
    dsp = [
        ("I/Q imbalance", "Gram-Schmidt", "note"),
        ("CD equaliser", "overlap-save FDE", "accent"),
        ("Timing recovery", "Gardner + interp.", "accent"),
        ("Adaptive equal.", "butterfly CMA/MMA", "accent"),
        ("Carrier phase", "BPS / Viterbi-Viterbi", "accent"),
        ("Decision + FEC", "SD-FEC, ~25% overhead", "optical"),
    ]
    dw, dgap, dy, dh = 124, 26, 286, 74
    dx0 = (920 - (len(dsp) * dw + (len(dsp) - 1) * dgap)) / 2
    for i, (title, subtitle, kind) in enumerate(dsp):
        bx = dx0 + i * (dw + dgap)
        c.add(S.block(bx, dy, dw, dh, title, subtitle, kind=kind, title_size=12,
                      subtitle_size=9.5))
        if i < len(dsp) - 1:
            c.add(S.arrow(bx + dw + 3, dy + dh / 2, bx + dw + dgap - 3, dy + dh / 2,
                          stroke=S.MUTED, width=1.5))

    # group the four equalisers that do not decide anything
    eq_x0 = dx0 + dw + dgap
    eq_x1 = dx0 + 4 * (dw + dgap) - dgap
    c.add(S.line(eq_x0, dy + dh + 12, eq_x1, dy + dh + 12, stroke=S.ACCENT,
                 width=1.4),
          S.line(eq_x0, dy + dh + 7, eq_x0, dy + dh + 17, stroke=S.ACCENT, width=1.4),
          S.line(eq_x1, dy + dh + 7, eq_x1, dy + dh + 17, stroke=S.ACCENT, width=1.4),
          S.text((eq_x0 + eq_x1) / 2, dy + dh + 30,
                 "four equalisers in series - no decision anywhere in here",
                 size=10, fill=S.ACCENT_DARK, anchor="middle", weight=600))

    c.add(S.tag(dx0 + 5 * (dw + dgap) + dw / 2, dy + dh + 30,
                "the only decision", kind="optical", size=9.5))

    c.add(S.callout(40, 408, 840, "What the block count hides",
                    ["Every output sample costs one multiply per tap per equaliser, at the "
                     "full sample rate.",
                     "A 2x2 butterfly CMA with 20 taps is 80 complex multiply-accumulates "
                     "per symbol - 320 real multiplies, at 64 GBd, forever."],
                    kind="accent"))
    return c.render()


# --------------------------------------------------------------------------- #
# 2. the 90-degree hybrid
# --------------------------------------------------------------------------- #


def ninety_degree_hybrid() -> str:
    c = S.Canvas(880, 400, title="The 90-degree hybrid and balanced detection")
    c.heading("Optics hands the DSP a complex number, not two real ones")

    hx, hy, hw, hh = 300, 96, 250, 210
    ports = [
        (170, "E~s~ + E~LO~"),
        (212, "E~s~ \u2212 E~LO~"),
        (254, "E~s~ + jE~LO~"),
        (296, "E~s~ \u2212 jE~LO~"),
    ]

    c.add(S.rect(hx, hy, hw, hh, fill=S.OPTICAL_WASH, stroke=S.OPTICAL, rx=10,
                 width=1.8),
          S.text(hx + hw / 2, hy + 22, "90\u00b0 hybrid", size=13, fill=S.OPTICAL,
                 anchor="middle", weight=700),
          S.text(hx + hw / 2, hy + 40, "one LO arm is delayed by \u03bb/4",
                 size=9.5, fill=S.MUTED, anchor="middle"))

    # inputs
    c.add(S.arrow(40, 170, hx - 6, 170, stroke=S.INK, width=1.8),
          S.text(40, 150, "E~s~   signal", size=11, fill=S.INK, weight=700),
          S.arrow(40, 296, hx - 6, 296, stroke=S.INK, width=1.8),
          S.text(40, 276, "E~LO~   local oscillator", size=11, fill=S.INK, weight=700))

    # the four output ports, labelled inside the block
    for py, label in ports:
        c.add(S.text(hx + hw - 12, py, label, size=10.5, fill=S.OPTICAL_DARK,
                     anchor="end", weight=600),
              S.line(hx + hw + 2, py, 578, py, stroke=S.INK, width=1.5))

    # balanced detectors
    for cy, pair, out_label in ((191, (170, 212), "I(t)"), (275, (254, 296), "Q(t)")):
        for py in pair:
            c.add(S.path(f"M 578 {S.num(py)} L 630 {S.num(cy)}", stroke=S.INK,
                         width=1.5, marker_end="url(#arrow)"))
        c.add(S.circle(654, cy, 22, fill=S.NOTE_WASH, stroke=S.NOTE, width=1.8),
              S.text(654, cy - 1, "\u2212", size=15, fill=S.NOTE, anchor="middle",
                     weight=700),
              S.text(624, pair[0] + 12, "+", size=13, fill=S.MUTED, anchor="end"),
              S.text(624, pair[1] - 12, "\u2212", size=13, fill=S.MUTED, anchor="end"),
              S.arrow(676, cy, 786, cy, stroke=S.INK, width=1.8),
              S.text(792, cy, out_label, size=12.5, fill=S.INK, weight=700),
              S.text(654, cy + 40, "balanced pair", size=9, fill=S.MUTED,
                     anchor="middle"))

    c.add(S.text(40, 344, "I(t) \u221d Re{ E~s~ E~LO~* }      "
                          "Q(t) \u221d Im{ E~s~ E~LO~* }", size=12, fill=S.INK,
                 weight=700),
          S.text(40, 372, "Subtracting each pair cancels the LO's own intensity noise; "
                          "the \u03bb/4 arm is what puts Q a quarter cycle out of phase.",
                 size=10.5, fill=S.SOFT, style="italic"))
    return c.render()


# --------------------------------------------------------------------------- #
# 3. overlap-save FDE
# --------------------------------------------------------------------------- #


def fde_overlap_save() -> str:
    c = S.Canvas(880, 430, title="Frequency-domain equalisation by overlap-save")
    c.heading("Why dispersion is equalised with an FFT, not a long FIR")

    blocks = [
        ("Buffer", "N/2 new + N/2 old"),
        ("FFT", "size N"),
        ("\u00d7 H[k]", "one complex MAC per bin"),
        ("IFFT", "size N"),
        ("Discard", "first N/2 out"),
    ]
    bw, bgap, by, bh = 124, 30, 92, 62
    bx0 = (880 - (len(blocks) * bw + (len(blocks) - 1) * bgap)) / 2
    for i, (title, subtitle) in enumerate(blocks):
        bx = bx0 + i * (bw + bgap)
        kind = "accent" if i in (1, 3) else ("note" if i == 2 else "plain")
        c.add(S.block(bx, by, bw, bh, title, subtitle, kind=kind, title_size=12.5,
                      subtitle_size=9.5))
        if i < len(blocks) - 1:
            c.add(S.arrow(bx + bw + 3, by + bh / 2, bx + bw + bgap - 3, by + bh / 2,
                          stroke=S.MUTED, width=1.5))

    c.add(S.arrow(30, by + bh / 2, bx0 - 6, by + bh / 2, stroke=S.INK, width=1.8),
          S.text(30, by + 30, "x[n]", size=11.5, fill=S.INK, weight=700),
          S.arrow(bx0 + len(blocks) * bw + (len(blocks) - 1) * bgap + 4, by + bh / 2,
                  866, by + bh / 2, stroke=S.INK, width=1.8),
          S.text(868, by + 30, "y[n]", size=11.5, fill=S.INK, anchor="end",
                 weight=700))

    c.add(S.text(bx0, by + bh + 26,
                 "The FFT makes an N-tap convolution cost N log N instead of N\u00b2 - "
                 "and dispersion needs hundreds of taps.",
                 size=10.5, fill=S.SOFT, style="italic"))

    # --- what overlap-save actually does in time ---------------------------
    c.add(S.text(40, 226, "The same four blocks of input, processed with 50% overlap",
                 size=11, fill=S.INK, weight=700))

    keep_x0, block_w, half = 60, 304, 152
    for row in range(4):
        start = keep_x0 + row * half
        y = 244 + row * 34
        c.add(S.rect(start, y, half, 26, fill=S.WARN_WASH, stroke=S.WARN, rx=3,
                     width=1.3, opacity=0.9),
              S.rect(start + half, y, half, 26, fill=S.ACCENT_WASH, stroke=S.ACCENT,
                     rx=3, width=1.3),
              S.text(start + half / 2, y + 13, "discard", size=9.5, fill=S.WARN,
                     anchor="middle", weight=600),
              S.text(start + half * 1.5, y + 13, "keep", size=9.5,
                     fill=S.ACCENT_DARK, anchor="middle", weight=600))

    c.add(S.text(keep_x0, 244 + 4 * 34 + 8,
                 "The first half of every IFFT is circular-convolution garbage. "
                 "Overlap-save does not fix it - it throws it away.",
                 size=10.5, fill=S.SOFT, style="italic"))
    return c.render()


# --------------------------------------------------------------------------- #
# 4. the CMA butterfly
# --------------------------------------------------------------------------- #


def cma_butterfly() -> str:
    c = S.Canvas(880, 548, title="The 2x2 butterfly equaliser with CMA adaptation")
    c.heading("Two mixed signals, four filters, one blind cost function")

    rows = [
        ("w~xx~", 82, "h", S.ACCENT),
        ("w~xy~", 172, "v", S.NOTE),
        ("w~yx~", 292, "h", S.ACCENT),
        ("w~yy~", 382, "v", S.NOTE),
    ]
    bx, bw, bh = 210, 120, 52
    rail_h, rail_v = 110, 160

    def centre(y):
        return y + bh / 2

    # --- the two input rails ------------------------------------------------
    c.add(S.arrow(30, centre(82), rail_h - 4, centre(82), stroke=S.INK, width=1.8),
          S.text(30, centre(82) - 22, "x~h~[n]", size=12, fill=S.INK, weight=700),
          S.arrow(30, centre(382), rail_v - 4, centre(382), stroke=S.INK, width=1.8),
          S.text(30, centre(382) - 22, "x~v~[n]", size=12, fill=S.INK, weight=700))

    c.add(S.line(rail_h, centre(82), rail_h, centre(292), stroke=S.ACCENT, width=1.6),
          S.line(rail_v, centre(172), rail_v, centre(382), stroke=S.NOTE, width=1.6))

    for label, y, source, color in rows:
        rail = rail_h if source == "h" else rail_v
        c.add(S.line(rail, centre(y), bx, centre(y), stroke=color, width=1.5),
              S.dot(rail, centre(y), r=3.6, fill=color),
              S.block(bx, y, bw, bh, label, None, kind="plain", title_size=13),
              S.line(bx + bw, centre(y), 452, centre(y), stroke=S.RULE, width=1.5))

    # One line crosses the other. Without a junction dot they are not connected,
    # which is exactly what a butterfly diagram relies on -- so it is labelled.
    c.add(S.text(152, 300, "crossing, not a junction", size=9, fill=S.MUTED,
                 anchor="middle", style="italic"))

    # --- output summers -----------------------------------------------------
    groups = (
        (153, (82, 172), "y~h~[n]", S.ACCENT_DARK, S.ACCENT_WASH, "blind error",
         "e = 1 \u2212 |y|^2^", "no training sequence", 107),
        (363, (292, 382), "y~v~[n]", S.NOTE, S.NOTE_WASH, "tap update",
         "w \u2190 w + \u03bc e x*", "all four filters, every symbol", 317),
    )
    for cy, pair, name, color, wash, box_title, box_line, box_note, box_y in groups:
        y_a, y_b = centre(pair[0]), centre(pair[1])
        c.add(S.line(452, y_a, 486, y_a, stroke=S.RULE, width=1.5),
              S.line(452, y_b, 486, y_b, stroke=S.RULE, width=1.5),
              S.line(486, y_a, 486, y_b, stroke=S.RULE, width=1.5),
              S.dot(486, y_a, r=3.4, fill=S.RULE),
              S.dot(486, y_b, r=3.4, fill=S.RULE),
              S.line(486, cy, 512, cy, stroke=S.RULE, width=1.5),
              S.circle(534, cy, 21, fill=wash, stroke=color, width=1.8),
              S.text(534, cy, "\u03a3", size=14, fill=color, anchor="middle",
                     weight=700),
              S.arrow(555, cy, 640, cy, stroke=S.INK, width=1.8),
              # The label sits above the arrow: at this width the boxes to the
              # right would otherwise run straight over it.
              S.text(598, cy - 20, name, size=12, fill=S.INK, anchor="middle",
                     weight=700),
              S.rect(660, box_y, 200, 92, fill=S.WARN_WASH, stroke=S.WARN, rx=8,
                     width=1.5),
              S.text(760, box_y + 24, box_title, size=11.5, fill=S.WARN,
                     anchor="middle", weight=700),
              S.text(760, box_y + 46, box_line, size=12, fill=S.INK,
                     anchor="middle"),
              S.text(760, box_y + 70, box_note, size=9.5, fill=S.MUTED,
                     anchor="middle"))

    c.add(S.callout(40, 452, 800, "Why it works without a training sequence",
                    ["CMA only asks that the output modulus stay constant, so it can adapt "
                     "before any decision is trustworthy.",
                     "That is exactly the situation after 1700 ps/nm of dispersion - which "
                     "is why blind adaptation comes before carrier recovery."],
                    kind="note"))
    return c.render()


FIGURES = {
    "coherent-receiver-dsp-chain": coherent_receiver_dsp_chain,
    "ninety-degree-hybrid": ninety_degree_hybrid,
    "fde-overlap-save": fde_overlap_save,
    "cma-butterfly": cma_butterfly,
}
