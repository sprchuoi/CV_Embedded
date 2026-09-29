#!/usr/bin/env python3
"""Regenerate the blog's figures into docs/blog/assets/.

    # every figure (needs numpy + matplotlib for the plots)
    build_environment/.venv/bin/python tool/build_blog_assets.py

    # only the hand-authored block diagrams - no numeric stack required
    python3 tool/build_blog_assets.py --only diagrams

    # also rasterise PNG copies next to the SVGs, for eyeballing a change
    build_environment/.venv/bin/python tool/build_blog_assets.py --png-dir /tmp/figs

The generated SVGs are committed, and *this* script is deliberately not part of
the site build: the pages job stays pure standard library, so a matplotlib
problem can never take the published site down.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tool.blog.art import FigureError, collect  # noqa: E402


def _looks_like_svg(markup: str) -> bool:
    """True if this is an SVG document.

    matplotlib emits an XML declaration and a DOCTYPE before the root element,
    while the hand-written diagrams start straight at ``<svg``. Both are valid;
    naively checking the first characters rejects every computed figure.
    """
    rest = markup.lstrip()
    while rest.startswith("<?") or rest.startswith("<!"):
        end = rest.find(">")
        if end == -1:
            return False
        rest = rest[end + 1:].lstrip()
    return rest.startswith("<svg")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the blog's SVG figures.")
    parser.add_argument("--repo-root", type=Path,
                        default=Path(__file__).resolve().parents[1])
    parser.add_argument("--only", choices=("diagrams", "plots"), default=None,
                        help="build just one family of figures")
    parser.add_argument("--png-dir", type=Path, default=None,
                        help="also write PNG rasterisations here, for review")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)

    kinds = (args.only,) if args.only else None
    try:
        figures = collect(kinds=kinds)
    except FigureError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    out_root = args.repo_root / "docs" / "blog" / "assets"
    written: list[str] = []

    for figure in figures:
        try:
            markup = figure.builder()
        except Exception as exc:  # a broken figure must name itself
            print(f"error: figure '{figure.name}' failed: {exc!r}", file=sys.stderr)
            return 1
        if not _looks_like_svg(markup):
            print(f"error: figure '{figure.name}' did not return SVG", file=sys.stderr)
            return 1

        target_dir = out_root / figure.kind
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / figure.filename
        target.write_text(markup, encoding="utf-8")
        written.append(str(target.relative_to(args.repo_root)))

        if args.png_dir:
            if _rasterise(markup, args.png_dir / figure.kind / f"{figure.name}.png"):
                written.append(f"(png) {figure.name}")
            else:
                print(f"warning: could not rasterise {figure.name}", file=sys.stderr)

    if not args.quiet:
        print(f"figures: wrote {len([w for w in written if not w.startswith('(png)')])} SVG(s)")
        for path in written:
            print(f"  {path}")
    return 0


def _rasterise(markup: str, target: Path) -> bool:
    """Best-effort SVG -> PNG, only used for human review."""
    try:
        import cairosvg
    except ImportError:
        return False
    target.parent.mkdir(parents=True, exist_ok=True)
    cairosvg.svg2png(bytestring=markup.encode("utf-8"), write_to=str(target), scale=2)
    return True


if __name__ == "__main__":
    raise SystemExit(main())
