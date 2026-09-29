"""Hand-authored diagrams for the FFT chapter.

    fft-radix2-tree    the recursive decimation, drawn as the tree it is
    fft-butterfly      the one operation every FFT is built from
    fft-bit-reversal   why the input ends up in a strange order
"""

from __future__ import annotations

from . import svg as S


def _bit_reverse(index: int, bits: int) -> int:
    result = 0
    for _ in range(bits):
        result = (result << 1) | (index & 1)
        index >>= 1
    return result


# --------------------------------------------------------------------------- #
# 1. the decimation tree
# --------------------------------------------------------------------------- #


def fft_radix2_tree() -> str:
    c = S.Canvas(880, 480, title="Radix-2 decimation in time for N = 8")
    c.heading("Halve the problem, twice, and the N-squared term disappears")

    levels = [
        (56, [("DFT~8~", "all 8 inputs", "accent")]),
        (256, [("DFT~4~", "x[0] x[2] x[4] x[6]", "note"),
               ("DFT~4~", "x[1] x[3] x[5] x[7]", "note")]),
        (456, [("DFT~2~", "pairs", "plain")] * 4),
    ]
    box_w, box_h = 152, 54
    centres = {
        0: [232],
        1: [138, 326],
        2: [92, 188, 284, 380],
    }
    edges = [
        (0, 0, 1, 0), (0, 0, 1, 1),
        (1, 0, 2, 0), (1, 0, 2, 1),
        (1, 1, 2, 2), (1, 1, 2, 3),
    ]

    # The final level is a brace: drawing eight size-1 DFTs adds nothing.
    c.add(S.line(648, 66, 648, 406, stroke=S.RULE, width=1.4),
          S.line(648, 66, 660, 66, stroke=S.RULE, width=1.4),
          S.line(648, 406, 660, 406, stroke=S.RULE, width=1.4),
          S.text(672, 236, "8 DFTs of size 1", size=11, fill=S.MUTED, weight=700),
          S.text(672, 256, "not worth computing", size=9.5, fill=S.MUTED,
                 style="italic"))

    for level, (x, definitions) in enumerate(levels):
        level_centres = centres[level]
        c.add(S.text(x, 42, f"stage {level + 1}" if level else "start",
                     size=9.5, fill=S.MUTED, weight=700))
        for (title, subtitle, kind), cy in zip(definitions, level_centres):
            c.add(S.block(x, cy - box_h / 2, box_w, box_h, title, subtitle,
                          kind=kind, title_size=12.5, subtitle_size=9))

    # Fan-out between successive stages, as smooth curves so the tree reads as
    # a tree rather than a plate of spaghetti.
    for src_level, src_box, dst_level, dst_box in edges:
        sx = levels[src_level][0] + box_w
        sy = centres[src_level][src_box]
        dx = levels[dst_level][0]
        dy = centres[dst_level][dst_box]
        c.add(S.path(f"M {S.num(sx)} {S.num(sy)} C {S.num(sx + 30)} {S.num(sy)} "
                     f"{S.num(dx - 30)} {S.num(dy)} {S.num(dx - 4)} {S.num(dy)}",
                     stroke=S.RULE, width=1.5))

    # Each size-2 DFT feeds two of the eight trivial ones.
    last_x = levels[2][0] + box_w
    for index, cy in enumerate(centres[2]):
        for offset in (-1, 1):
            target = 236 + (index * 2 - 3.5 + (0 if offset < 0 else 1)) * 22
            c.add(S.path(f"M {S.num(last_x)} {S.num(cy)} "
                         f"C {S.num(last_x + 34)} {S.num(cy)} 620 {S.num(target)} "
                         f"644 {S.num(target)}", stroke=S.RULE, width=1.2))

    c.add(S.callout(56, 420, 790, "The cost falls out of the tree",
                    ["Each stage performs N/2 = 4 butterflies, and there are "
                     "log\u2082N = 3 stages: 12 complex multiplies.",
                     "The direct DFT needs N\u00b2 = 64. The ratio grows as N/log\u2082N, "
                     "which is why every large transform in the world is an FFT."],
                    kind="accent"))
    return c.render()


# --------------------------------------------------------------------------- #
# 2. the butterfly
# --------------------------------------------------------------------------- #


def fft_butterfly() -> str:
    c = S.Canvas(880, 360, title="The radix-2 butterfly")
    c.heading("Every FFT is this, N/2 times per stage")

    left, right = 120, 720
    top, bottom = 128, 258

    # inputs
    for y, label, color in ((top, "a", S.ACCENT_DARK), (bottom, "b", S.NOTE)):
        c.add(S.dot(left, y, r=4.4, fill=color),
              S.text(left - 18, y, f"{label}[n]", size=12, fill=color,
                     anchor="end", weight=700))

    # a goes straight to the sum, and down to the difference
    c.add(S.line(left, top, right, top, stroke=S.ACCENT_DARK, width=1.9))
    c.add(S.line(left, bottom, left + 168, bottom, stroke=S.NOTE, width=1.9))

    # the twiddle multiply on the b branch
    c.add(S.path(f"M {S.num(left + 168)} {S.num(bottom - 20)} "
                 f"L {S.num(left + 168)} {S.num(bottom + 20)} "
                 f"L {S.num(left + 232)} {S.num(bottom)} Z",
                 fill=S.NOTE_WASH, stroke=S.NOTE, width=1.7),
          S.text(left + 214, bottom, "W~N~^k^", size=12, fill=S.NOTE,
                 anchor="middle", weight=700))
    c.add(S.line(left + 232, bottom, right, bottom, stroke=S.NOTE, width=1.9))

    # the crossing diagonals
    c.add(S.dot(left + 232, bottom, r=4, fill=S.NOTE),
          S.path(f"M {S.num(left + 232)} {S.num(bottom)} L {S.num(right)} {S.num(top)}",
                 stroke=S.NOTE, width=1.9),
          S.dot(left + 300, top, r=4, fill=S.ACCENT_DARK),
          S.path(f"M {S.num(left + 300)} {S.num(top)} L {S.num(right)} {S.num(bottom)}",
                 stroke=S.ACCENT_DARK, width=1.9))

    # the -1 on the lower path
    c.add(S.circle(576, (top + bottom) / 2, 15, fill=S.WARN_WASH, stroke=S.WARN,
                   width=1.6),
          S.text(576, (top + bottom) / 2, "\u22121", size=11, fill=S.WARN,
                 anchor="middle", weight=700))

    # outputs
    c.add(S.dot(right, top, r=5, fill=S.INK), S.dot(right, bottom, r=5, fill=S.INK),
          S.text(right + 18, top, "a + W~N~^k^ b", size=12.5, fill=S.INK,
                 weight=700),
          S.text(right + 18, bottom, "a \u2212 W~N~^k^ b", size=12.5, fill=S.INK,
                 weight=700))

    c.add(S.text(left - 18, 66, "one complex multiply, two complex adds",
                 size=10.5, fill=S.MUTED, style="italic"),
          S.text(left - 18, 328,
                 "The same two inputs produce both outputs, which is why a "
                 "butterfly costs one multiply and not two.",
                 size=11, fill=S.SOFT, style="italic"))
    return c.render()


# --------------------------------------------------------------------------- #
# 3. bit reversal
# --------------------------------------------------------------------------- #


def fft_bit_reversal() -> str:
    c = S.Canvas(880, 420, title="Bit-reversal permutation of the FFT input, N = 8")
    c.heading("Why the input ends up in an order nobody would choose")

    bits = 3
    rows = 8
    box_w, box_h = 168, 28
    left_x, right_x = 96, 560
    top = 62
    step = 38

    def row_y(index):
        return top + index * step

    c.add(S.text(left_x, 44, "the order you have", size=10, fill=S.MUTED,
                 weight=700),
          S.text(right_x, 44, "the order the butterflies want", size=10,
                 fill=S.MUTED, weight=700))

    for n in range(rows):
        y = row_y(n)
        c.add(S.rect(left_x, y, box_w, box_h, fill=S.ACCENT_WASH, stroke=S.ACCENT,
                     rx=4, width=1.3),
              S.text(left_x + 14, y + box_h / 2, f"x[{n}]", size=10.5,
                     fill=S.ACCENT_DARK, weight=700),
              S.text(left_x + box_w - 14, y + box_h / 2,
                     format(n, f"0{bits}b"), size=10.5, fill=S.MUTED,
                     anchor="end", family=S.MONO))

        reversed_index = _bit_reverse(n, bits)
        ry = row_y(reversed_index)
        c.add(S.rect(right_x, ry, box_w, box_h, fill=S.NOTE_WASH, stroke=S.NOTE,
                     rx=4, width=1.3),
              S.text(right_x + 14, ry + box_h / 2,
                     format(reversed_index, f"0{bits}b"), size=10.5,
                     fill=S.MUTED, family=S.MONO),
              S.text(right_x + box_w - 14, ry + box_h / 2,
                     f"x[{n}]", size=10.5, fill=S.NOTE, anchor="end",
                     weight=700))

        # route the arrow down the middle, offset per source so crossings read.
        mid = 300 + n * 26
        c.add(S.path(f"M {S.num(left_x + box_w)} {S.num(y + box_h / 2)} "
                     f"L {S.num(mid)} {S.num(y + box_h / 2)} "
                     f"L {S.num(mid)} {S.num(ry + box_h / 2)} "
                     f"L {S.num(right_x - 4)} {S.num(ry + box_h / 2)}",
                     stroke=S.ACCENT, width=1.4, opacity=0.75))

    c.add(S.text(96, 390,
                 "A butterfly only ever combines neighbours, so the inputs must "
                 "arrive bit-reversed. Decimate in", size=11, fill=S.SOFT,
                 style="italic"),
          S.text(96, 406,
                 "frequency instead and the same permutation moves to the output. "
                 "It never disappears.", size=11, fill=S.SOFT, style="italic"))
    return c.render()


FIGURES = {
    "fft-radix2-tree": fft_radix2_tree,
    "fft-butterfly": fft_butterfly,
    "fft-bit-reversal": fft_bit_reversal,
}
