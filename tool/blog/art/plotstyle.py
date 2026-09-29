"""Shared matplotlib styling for the computed figures.

The point of this module is that a reader cannot tell a hand-built block diagram
from a numpy-generated spectrum: same palette, same type scale, same spine and
grid treatment. Every plot module imports from here rather than calling
``plt.subplots`` directly.

Output note: ``svg.fonttype`` is set to ``"path"``. An SVG shown through
``<img src="...">`` is an isolated document that cannot load the page's webfont,
so leaving text as text means the figure renders in whatever the reader's
machine happens to substitute. Converting glyphs to outlines costs file size and
text selectability, and buys figures that look identical everywhere.
"""

from __future__ import annotations

import io

import matplotlib

matplotlib.use("Agg")           # no display needed; build-time rendering only
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.ticker import MaxNLocator  # noqa: E402

# Palette shared with tool/blog/art/svg.py and blog/assets/blog.css.
INK = "#2c3e50"
SOFT = "#5c5c5c"
MUTED = "#767676"
RULE = "#cfd8d4"
RULE_SOFT = "#e4e9e7"
ACCENT = "#54b689"
ACCENT_DARK = "#2f7a58"
NOTE = "#3b7fb5"
WARN = "#d9822b"
OPTICAL = "#7a5cc0"
PANEL = "#ffffff"

SERIES = [ACCENT, NOTE, WARN, OPTICAL, ACCENT_DARK, MUTED]
WIDTH = 8.2                    # inches; ~820 px at dpi=100, matching the diagrams

_configured = False


def setup() -> None:
    """Apply the rcParams once per process."""
    global _configured
    if _configured:
        return
    plt.rcParams.update({
        "svg.fonttype": "path",
        # Deterministic element ids. Without a fixed hashsalt matplotlib derives
        # `id="p3f2a..."` style ids from object identity, so two renders of the
        # same figure differ and CI's "committed figures are up to date" check
        # would fail on every run.
        "svg.hashsalt": "dsp-blog",
        "figure.dpi": 100,
        "savefig.dpi": 100,
        "figure.facecolor": PANEL,
        "savefig.facecolor": PANEL,
        "axes.facecolor": PANEL,
        "font.family": "sans-serif",
        "font.sans-serif": ["DejaVu Sans", "Helvetica", "Arial"],
        "font.size": 9.5,
        "axes.titlesize": 10.5,
        "axes.titleweight": "bold",
        "axes.titlecolor": INK,
        "axes.titlelocation": "left",
        "axes.titlepad": 10,
        "axes.labelsize": 10,
        "axes.labelcolor": SOFT,
        "axes.edgecolor": RULE,
        "axes.linewidth": 1.1,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.color": RULE_SOFT,
        "grid.linewidth": 0.9,
        "xtick.color": MUTED,
        "ytick.color": MUTED,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "xtick.direction": "out",
        "ytick.direction": "out",
        "legend.frameon": False,
        "legend.fontsize": 9,
        "lines.linewidth": 2.0,
        "lines.solid_capstyle": "round",
    })
    _configured = True


def figure(height: float = 3.0, *, width: float = WIDTH, nrows: int = 1,
           ncols: int = 1, sharex: bool = False, sharey: bool = False,
           height_ratios=None, hspace: float = 0.45):
    """A styled figure. Returns ``(fig, axes)``; ``axes`` is an array when the
    grid has more than one cell, matching matplotlib's own convention."""
    setup()
    fig, axes = plt.subplots(
        nrows, ncols, figsize=(width, height), sharex=sharex, sharey=sharey,
        gridspec_kw={"height_ratios": height_ratios, "hspace": hspace}
        if height_ratios else {"hspace": hspace},
    )
    return fig, axes


def title(ax, text: str, *, subtitle: str | None = None) -> None:
    """A left-aligned title with an optional second line beneath it.

    matplotlib draws the title above the axes at ``axes.titlepad``, so the
    subtitle has to be pushed clear of it *and* the title has to be raised:
    putting the subtitle at a bare ``y=1.01`` overlaps the title at the default
    pad.
    """
    if subtitle:
        ax.set_title(text, pad=22)
        ax.text(0, 1.012, subtitle, transform=ax.transAxes, fontsize=9,
                color=MUTED, va="bottom")
    else:
        ax.set_title(text)


def tidy(ax, *, xlabel=None, ylabel=None, yaxis_int=False, xaxis_int=False,
         legend=None, legend_loc="best", ncol=1) -> None:
    """Labels plus the small clean-ups every figure in the article wants."""
    if xlabel:
        ax.set_xlabel(xlabel)
    if ylabel:
        ax.set_ylabel(ylabel)
    if yaxis_int:
        ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    if xaxis_int:
        ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    if legend:
        ax.legend(loc=legend_loc, ncol=ncol)


def rasterise_dense_collections(fig, *, threshold: int = 1500) -> int:
    """Rasterise scatter collections with more than ``threshold`` points.

    A constellation cloud of a few thousand markers becomes a few thousand
    ``<path>`` elements in the SVG -- one figure was 1.8 MB, which is a poor
    thing to hand a phone. Rasterising just those collections embeds one small
    PNG instead, while ideal-constellation markers and every line, axis and
    annotation stay as crisp vectors.

    Returns the number of collections rasterised, so a caller can report it.
    """
    count = 0
    for axes in fig.axes:
        for collection in axes.collections:
            try:
                size = len(collection.get_offsets())
            except (AttributeError, TypeError):
                continue
            if size >= threshold:
                collection.set_rasterized(True)
                count += 1
    return count


def render(fig) -> str:
    """Serialise a figure to an SVG string and close it.

    ``metadata={"Date": None}`` suppresses the wall-clock ``<dc:date>`` stamp
    matplotlib writes by default. Together with ``svg.hashsalt`` above, that
    makes the output byte-stable, which is what lets CI assert that the
    committed SVGs match a fresh build.
    """
    rasterise_dense_collections(fig)
    buffer = io.StringIO()
    fig.savefig(buffer, format="svg", bbox_inches="tight", pad_inches=0.12,
                metadata={"Date": None})
    plt.close(fig)
    return buffer.getvalue()
