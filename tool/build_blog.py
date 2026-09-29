#!/usr/bin/env python3
"""Render the DSP blog into docs/blog/.

    python3 tool/build_blog.py             # build
    python3 tool/build_blog.py --strict    # build, and fail on warnings too
    python3 tool/build_blog.py --check     # validate without writing files

Uses only the standard library, so the CI job that publishes the site never
depends on the numeric stack the figure generators need.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tool.blog import site  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the DSP blog.")
    parser.add_argument("--repo-root", type=Path,
                        default=Path(__file__).resolve().parents[1])
    parser.add_argument("--strict", action="store_true",
                        help="treat warnings (e.g. unreferenced figures) as errors")
    parser.add_argument("--check", action="store_true",
                        help="validate only; do not write any files")
    args = parser.parse_args(argv)

    if args.check:
        # A dry run: build into a scratch copy is overkill for a static site,
        # so validate by loading and rendering without persisting.
        report = site.build(args.repo_root, strict=True)
        for problem in report.errors:
            print(f"error: {problem}", file=sys.stderr)
        for warning in report.warnings:
            print(f"warning: {warning}", file=sys.stderr)
        if report.ok and not report.warnings:
            print("blog: curriculum and figures are consistent")
            return 0
        return 1

    report = site.build(args.repo_root, strict=args.strict)

    for problem in report.errors:
        print(f"error: {problem}", file=sys.stderr)
    for warning in report.warnings:
        print(f"warning: {warning}", file=sys.stderr)

    if report.errors:
        print(f"blog: {len(report.errors)} error(s), nothing written", file=sys.stderr)
        return 1

    print(f"blog: wrote {len(report.pages)} page(s) to docs/blog/")
    for page in report.pages:
        print(f"  {page}")
    if report.warnings and args.strict:
        print(f"blog: {len(report.warnings)} warning(s) with --strict", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
