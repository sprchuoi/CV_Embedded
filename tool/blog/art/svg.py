"""A tiny SVG builder for hand-authored technical diagrams.

Why a builder instead of hand-typed SVG files: a block diagram is a dozen boxes,
two dozen arrows and their labels, and every one of them has to agree on the
same palette, stroke width and type scale. Written as a script the *intent* is
reviewable ("FFE feeds the DFE") and the styling cannot drift between figures.

The output is deliberately self-contained -- inline presentation attributes and
one ``<style>`` block, no external fonts -- because an SVG referenced from
``<img src="...">`` is a separate document that inherits nothing from the page.
That also means figures keep their light panel background in dark mode, which is
why every canvas paints its own opaque background rectangle.

Units are user units on a 1:1 canvas; figures are authored around 820 px wide
and scaled by CSS.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field

# --------------------------------------------------------------------------- #
# Palette -- mirrors blog/assets/blog.css so figures sit inside the page
# --------------------------------------------------------------------------- #

INK = "#2c3e50"
SOFT = "#5c5c5c"
MUTED = "#767676"
RULE = "#cfd8d4"
RULE_SOFT = "#e4e9e7"
ACCENT = "#54b689"
ACCENT_DARK = "#2f7a58"
ACCENT_WASH = "#eef7f2"
NOTE = "#3b7fb5"
NOTE_WASH = "#eef5fb"
NOTE_DARK = "#2b5f88"
WARN = "#d9822b"
WARN_WASH = "#fdf4ea"
OPTICAL = "#7a5cc0"
OPTICAL_WASH = "#f4f1fc"
OPTICAL_DARK = "#5b41a0"
PANEL = "#ffffff"
PLOT_BG = "#fbfcfc"

FONT = "Inter, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
MONO = "'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace"

KINDS = {
    "plain": (PANEL, RULE, INK),
    "accent": (ACCENT_WASH, ACCENT, ACCENT_DARK),
    "note": (NOTE_WASH, NOTE, "#2b5f88"),
    "warn": (WARN_WASH, WARN, "#a8621d"),
    "optical": (OPTICAL_WASH, OPTICAL, "#5b41a0"),
    "dark": (INK, INK, "#ffffff"),
}


def esc(text: object) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


# ``f~s~`` renders an f with a subscript s; ``z^-1^`` a superscript. Labels are
# written this way all over the figures (f_s, f_c, T_s, z^-1, x[n]) and doing it
# with unicode is not possible -- there is no subscript "c" or "s" in every font.
_RICH_RE = re.compile(r"~([^~]+)~|\^([^^]+)\^")


def rich(label: object, size: float) -> str:
    """Markup-aware text content: ``~x~`` is a subscript, ``^x^`` a superscript.

    Offsets are emitted as *relative* ``dy`` values on successive ``<tspan>``s,
    because ``dy`` accumulates; each run therefore carries the delta that lands
    it on its target baseline and the next run carries the delta back. That
    keeps the output correct in browsers and in cairosvg alike, which
    ``baseline-shift`` does not.
    """
    raw = str(label)
    if "~" not in raw and "^" not in raw:
        return esc(raw)

    runs: list[tuple[str, str]] = []
    pos = 0
    for match in _RICH_RE.finditer(raw):
        if match.start() > pos:
            runs.append((raw[pos:match.start()], "normal"))
        if match.group(1) is not None:
            runs.append((match.group(1), "sub"))
        else:
            runs.append((match.group(2), "sup"))
        pos = match.end()
    if pos < len(raw):
        runs.append((raw[pos:], "normal"))

    offsets = {"normal": 0.0, "sub": size * 0.30, "sup": size * -0.42}
    sizes = {"normal": size, "sub": size * 0.72, "sup": size * 0.72}

    out: list[str] = []
    current = 0.0
    for content, kind in runs:
        target = offsets[kind]
        dy = target - current
        current = target
        out.append(
            f'<tspan{_attrs(dict(dy=num(round(dy, 2)), font_size=num(round(sizes[kind], 2))))}>'
            f"{esc(content)}</tspan>"
        )
    return "".join(out)


def num(value: float) -> str:
    """Compact number formatting: 12, 12.5, 12.25 -- no trailing zeros."""
    if float(value).is_integer():
        return str(int(value))
    return f"{value:.3f}".rstrip("0").rstrip(".")


def _attrs(pairs: dict[str, object]) -> str:
    out = []
    for key, value in pairs.items():
        if value is None or value is False:
            continue
        key = key.rstrip("_").replace("_", "-")
        if value is True:
            out.append(key)
        else:
            out.append(f'{key}="{esc(value)}"')
    return (" " + " ".join(out)) if out else ""


# --------------------------------------------------------------------------- #
# Elements
# --------------------------------------------------------------------------- #


def rect(x, y, w, h, *, fill=PANEL, stroke=None, width=1.5, rx=8, dash=None,
         opacity=None) -> str:
    attrs = dict(x=num(x), y=num(y), width=num(w), height=num(h), rx=num(rx),
                 fill=fill, stroke=stroke, stroke_width=width,
                 stroke_dasharray=dash, opacity=opacity)
    return f"<rect{_attrs(attrs)}/>"


def line(x1, y1, x2, y2, *, stroke=RULE, width=1.5, dash=None, cap="round") -> str:
    attrs = dict(x1=num(x1), y1=num(y1), x2=num(x2), y2=num(y2),
                 stroke=stroke, stroke_width=width, stroke_dasharray=dash,
                 stroke_linecap=cap)
    return f"<line{_attrs(attrs)}/>"


def circle(cx, cy, r, *, fill=ACCENT, stroke=None, width=1.5) -> str:
    attrs = dict(cx=num(cx), cy=num(cy), r=num(r), fill=fill, stroke=stroke,
                 stroke_width=width)
    return f"<circle{_attrs(attrs)}/>"


def dot(cx, cy, *, r=3.4, fill=ACCENT, stroke=None, width=1.4) -> str:
    return circle(cx, cy, r, fill=fill, stroke=stroke, width=width)


def path(d, *, fill="none", stroke=INK, width=1.8, dash=None, cap="round",
         join="round", marker_end=None, marker_start=None, opacity=None) -> str:
    attrs = dict(d=d, fill=fill, stroke=stroke, stroke_width=width,
                 stroke_dasharray=dash, stroke_linecap=cap, stroke_linejoin=join,
                 marker_end=marker_end, marker_start=marker_start,
                 opacity=opacity)
    return f"<path{_attrs(attrs)}/>"


def text(x, y, label, *, size=13, fill=INK, anchor="start", weight=400,
         family=FONT, baseline="middle", style=None, opacity=None,
         rotate=None) -> str:
    """A text run. ``rotate`` is degrees about ``(x, y)`` -- used for the
    axis-side labels that would otherwise collide with a curve."""
    transform = f"rotate({num(rotate)} {num(x)} {num(y)})" if rotate else None
    attrs = dict(x=num(x), y=num(y), font_family=family, font_size=num(size),
                 fill=fill, text_anchor=anchor, font_weight=weight,
                 dominant_baseline=baseline, font_style=style, opacity=opacity,
                 transform=transform)
    return f"<text{_attrs(attrs)}>{rich(label, size)}</text>"


def polyline(points, *, stroke=ACCENT, width=2.2, fill="none", dash=None,
             marker_end=None) -> str:
    coords = " ".join(f"{num(px)},{num(py)}" for px, py in points)
    attrs = dict(points=coords, fill=fill, stroke=stroke, stroke_width=width,
                 stroke_dasharray=dash, stroke_linejoin="round",
                 stroke_linecap="round", marker_end=marker_end)
    return f"<polyline{_attrs(attrs)}/>"


def arrow(x1, y1, x2, y2, *, stroke=INK, width=1.8, dash=None, head=True) -> str:
    """A straight arrow; the head is a marker so the shaft stays crisp."""
    return path(f"M {num(x1)} {num(y1)} L {num(x2)} {num(y2)}", stroke=stroke,
                width=width, dash=dash, marker_end="url(#arrow)" if head else None)


def arrow_path(points, *, stroke=INK, width=1.8, dash=None, head=True) -> str:
    """A routed arrow through the given corner points (a polyline plus head)."""
    if len(points) < 2:
        return ""
    d = [f"M {num(points[0][0])} {num(points[0][1])}"]
    d.extend(f"L {num(px)} {num(py)}" for px, py in points[1:])
    return path(" ".join(d), stroke=stroke, width=width, dash=dash,
                marker_end="url(#arrow)" if head else None)


def brace(x, y, height, *, side="left", width=10, stroke=RULE, label=None,
          label_size=11, label_fill=MUTED, gap=8) -> str:
    """A curly brace spanning ``height``; used to group stages."""
    s = -1 if side == "left" else 1
    d = (f"M {num(x + s * width)} {num(y)} "
         f"q {num(s * width)} 0 {num(s * width)} {num(width)} "
         f"L {num(x)} {num(y + height / 2 - width)} "
         f"q 0 {num(width)} {num(s * width)} {num(width)} "
         f"q {num(-s * width)} 0 {num(-s * width)} {num(width)} "
         f"L {num(x + s * width)} {num(y + height)} "
         f"q {num(s * width)} 0 {num(s * width)} {num(-width)}")
    out = path(d, stroke=stroke, width=1.3, fill="none")
    if label:
        lx = x - s * (width + gap)
        # Rotated so a long stage name reads bottom-to-top beside the brace.
        attrs = dict(x=num(lx), y=num(y + height / 2), font_family=FONT,
                     font_size=num(label_size), fill=label_fill,
                     text_anchor="middle", font_weight=600,
                     letter_spacing="0.08em",
                     transform=f"rotate(-90 {num(lx)} {num(y + height / 2)})")
        out += f"<text{_attrs(attrs)}>{esc(label)}</text>"
    return out


# --------------------------------------------------------------------------- #
# Composite parts
# --------------------------------------------------------------------------- #


def block(x, y, w, h, title, subtitle=None, *, kind="plain", rx=8, dash=None,
          title_size=13, subtitle_size=10.5) -> str:
    """A labelled stage box. Title is centred; subtitle sits under it."""
    fill, stroke, ink = KINDS[kind]
    out = [rect(x, y, w, h, fill=fill, stroke=stroke, rx=rx, dash=dash)]
    cx = x + w / 2
    if subtitle:
        out.append(text(cx, y + h / 2 - 8, title, size=title_size, fill=ink,
                        anchor="middle", weight=600))
        out.append(text(cx, y + h / 2 + 10, subtitle, size=subtitle_size,
                        fill=SOFT, anchor="middle"))
    else:
        out.append(text(cx, y + h / 2, title, size=title_size, fill=ink,
                        anchor="middle", weight=600))
    return "".join(out)


def tag(x, y, label, *, kind="accent", size=10, pad_x=8, pad_y=4) -> str:
    """A small pill, for signal names along a bus."""
    fill, stroke, ink = KINDS[kind]
    w = len(str(label)) * size * 0.62 + pad_x * 2
    h = size + pad_y * 2
    return (rect(x - w / 2, y - h / 2, w, h, fill=fill, stroke=stroke, rx=h / 2,
                 width=1) +
            text(x, y + 0.5, label, size=size, fill=ink, anchor="middle", weight=600))


def axis(x0, y0, x1, y1, *, xlabel=None, ylabel=None, xticks=(), yticks=(),
         tick_len=4, label_size=10.5, grid=False, grid_n=4) -> str:
    """L-shaped axes with optional ticks. ``xticks``/``yticks`` are
    ``(position, label)`` pairs in canvas coordinates."""
    out = []
    if grid:
        for i in range(1, grid_n + 1):
            gy = y0 + (y1 - y0) * i / (grid_n + 1)
            out.append(line(x0, gy, x1, gy, stroke=RULE_SOFT, width=1))
    out.append(line(x0, y0, x1, y0))
    out.append(line(x0, y0, x0, y1))
    for pos, label in xticks:
        out.append(line(pos, y0, pos, y0 + tick_len, stroke=RULE))
        out.append(text(pos, y0 + 14, label, size=label_size, fill=MUTED, anchor="middle"))
    for pos, label in yticks:
        out.append(line(x0, pos, x0 - tick_len, pos, stroke=RULE))
        out.append(text(x0 - 8, pos, label, size=label_size, fill=MUTED, anchor="end"))
    if xlabel:
        out.append(text((x0 + x1) / 2, y0 + 30, xlabel, size=label_size + 1,
                        fill=SOFT, anchor="middle", weight=600))
    if ylabel:
        cy = (y0 + y1) / 2
        out.append(f'<text{_attrs(dict(x=num(x0 - 42), y=num(cy), font_family=FONT, font_size=num(label_size + 1), fill=SOFT, text_anchor="middle", font_weight=600, transform=f"rotate(-90 {num(x0 - 42)} {num(cy)})"))}>{esc(ylabel)}</text>')
    return "".join(out)


def stems(baseline, points, *, color=ACCENT, width=1.8, r=3.2, label=None,
          labels=(), label_size=9.5) -> str:
    """A stem plot: ``points`` is a sequence of ``(x, y)``; y is the tip."""
    out = []
    for px, py in points:
        out.append(line(px, baseline, px, py, stroke=color, width=width))
        out.append(dot(px, py, r=r, fill=color))
    if labels:
        for (px, _), lab in zip(points, labels):
            out.append(text(px, baseline + 15, lab, size=label_size, fill=MUTED,
                            anchor="middle"))
    if label:
        out.append(text(points[-1][0], baseline, label, size=label_size,
                        fill=MUTED, anchor="start"))
    return "".join(out)


def wave(fn, x0, x1, y_base, *, amplitude=1.0, samples=240, stroke=ACCENT,
         width=2.2, dash=None, scale_y=None, marker_end=None) -> str:
    """Sample ``fn(t)`` across ``[x0, x1]`` and draw it as a polyline.

    ``fn`` takes a normalised position 0..1 and returns -1..1.
    """
    span = x1 - x0
    amp = amplitude if scale_y is None else scale_y
    pts = []
    for i in range(samples + 1):
        u = i / samples
        value = fn(u)
        pts.append((x0 + u * span, y_base - value * amp))
    return polyline(pts, stroke=stroke, width=width, dash=dash,
                    marker_end=marker_end)


def sample_points(fn, x0, x1, count, y_base, *, amplitude=1.0):
    """The ``count`` sample positions of ``fn`` over ``[x0, x1]``."""
    pts = []
    for i in range(count):
        u = i / (count - 1) if count > 1 else 0.5
        pts.append((x0 + u * (x1 - x0), y_base - fn(u) * amplitude))
    return pts


def matrix(x, y, w, h, rows, cols, *, cell_labels=None, row_labels=(),
           col_labels=(), fill=PANEL, stroke=RULE, ink=INK) -> str:
    """A small grid, for filter taps / mixing matrices."""
    out = [rect(x, y, w, h, fill=fill, stroke=stroke, rx=4)]
    cw, ch = w / cols, h / rows
    for c in range(1, cols):
        out.append(line(x + c * cw, y, x + c * cw, y + h, stroke=stroke, width=1))
    for r in range(1, rows):
        out.append(line(x, y + r * ch, x + w, y + r * ch, stroke=stroke, width=1))
    for r, label in enumerate(row_labels):
        out.append(text(x - 10, y + (r + 0.5) * ch, label, size=11, fill=ink,
                        anchor="end", weight=600))
    for c, label in enumerate(col_labels):
        out.append(text(x + (c + 0.5) * cw, y - 12, label, size=11, fill=ink,
                        anchor="middle", weight=600))
    if cell_labels:
        for r in range(rows):
            for c in range(cols):
                label = cell_labels[r][c]
                if label:
                    out.append(text(x + (c + 0.5) * cw, y + (r + 0.5) * ch, label,
                                    size=12, fill=ink, anchor="middle",
                                    family=MONO))
    return "".join(out)


def wrap(text: object, max_chars: int) -> list[str]:
    """Greedy word wrap, so a callout can never spill outside its own box.

    The note boxes are a fixed width with no text engine behind them, so a long
    sentence used to run off the edge of the panel and out of the figure.
    """
    words = str(text).split()
    if not words:
        return [""]
    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        trial = f"{current} {word}"
        if len(trial) <= max_chars:
            current = trial
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def _wrapped_lines(w, body, body_size, pad) -> list[str]:
    # 0.52 em per character is a deliberately conservative average: wrapping a
    # little early is harmless, overflowing the panel is not.
    per_line = max(20, int((w - 2 * pad) / (body_size * 0.52)))
    source = body if isinstance(body, (list, tuple)) else [body]
    lines: list[str] = []
    for entry in source:
        lines.extend(wrap(entry, per_line))
    return lines


def callout_height(w, body, *, body_size=11.5, pad=12) -> float:
    """The height :func:`callout` will occupy, for sizing a canvas around it."""
    count = len(_wrapped_lines(w, body, body_size, pad))
    return pad * 2 + 16 + count * (body_size + 4)


def callout(x, y, w, label, body, *, kind="note", body_size=11.5, pad=12) -> str:
    """An inline explanatory note inside a figure.

    The body is wrapped to the box width and the box height is derived from the
    wrapped result, so the text and the panel always agree.
    """
    fill, stroke, ink = KINDS[kind]
    lines = _wrapped_lines(w, body, body_size, pad)
    h = pad * 2 + 16 + len(lines) * (body_size + 4)
    out = [rect(x, y, w, h, fill=fill, stroke=stroke, rx=6, width=1.2),
           text(x + pad, y + pad + 5, label, size=11, fill=ink, weight=700)]
    for i, entry in enumerate(lines):
        out.append(text(x + pad, y + pad + 24 + i * (body_size + 4), entry,
                        size=body_size, fill=SOFT))
    return "".join(out)


# --------------------------------------------------------------------------- #
# Canvas
# --------------------------------------------------------------------------- #


@dataclass
class Canvas:
    width: int
    height: int
    title: str = ""
    background: str = PANEL
    pad: int = 0
    parts: list[str] = field(default_factory=list)

    def add(self, *markup: str) -> "Canvas":
        self.parts.extend(m for m in markup if m)
        return self

    def heading(self, label, *, x=None, y=24, size=12.5, fill=MUTED) -> "Canvas":
        """A small figure heading. Letter-spaced, not upper-cased -- callers
        pass the exact casing they want (f_s, f_c and dBFS all object to it)."""
        self.parts.append(
            text(self.pad + 4 if x is None else x, y, label, size=size,
                 fill=fill, weight=700)
        )
        return self

    def render(self) -> str:
        """Produce the SVG document, ready to write to a .svg file."""
        bg = rect(0, 0, self.width, self.height, fill=self.background, rx=0)
        style = (
            "<style>"
            f"text{{font-family:{FONT};}}"
            "text, tspan { white-space: pre; }"
            "</style>"
        )
        defs = (
            "<defs>"
            '<marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" '
            'markerWidth="6.5" markerHeight="6.5" orient="auto-start-reverse">'
            f'<path d="M 0 0 L 10 5 L 0 10 z" fill="{INK}"/></marker>'
            '<marker id="arrow-accent" viewBox="0 0 10 10" refX="9" refY="5" '
            'markerWidth="6.5" markerHeight="6.5" orient="auto-start-reverse">'
            f'<path d="M 0 0 L 10 5 L 0 10 z" fill="{ACCENT}"/></marker>'
            "</defs>"
        )
        label = (
            f'<title>{esc(self.title)}</title>' if self.title else ""
        )
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'viewBox="0 0 {self.width} {self.height}" '
            f'width="{self.width}" height="{self.height}" '
            f'role="img" aria-label="{esc(self.title)}">'
            f"{label}{style}{defs}{bg}{''.join(self.parts)}</svg>\n"
        )


def grid_canvas(cols: int, rows: int, *, cell=200, gap=16, margin=22,
                title="") -> Canvas:
    """A canvas sized to hold a ``cols`` x ``rows`` grid, for small multiples."""
    width = margin * 2 + cols * cell + (cols - 1) * gap
    height = margin * 2 + rows * cell + (rows - 1) * gap
    return Canvas(int(width), int(height), title=title, pad=margin)


def cell_box(index: int, cols: int, *, cell=200, gap=16, margin=22):
    """``(x, y)`` of grid cell ``index`` in a :func:`grid_canvas`."""
    col, row = index % cols, index // cols
    return margin + col * (cell + gap), margin + row * (cell + gap)
