#!/usr/bin/env python3
"""Check the course-team page contract over the DSP blog.

    python3 tool/check_page_contract.py               # gate: fail on findings
    python3 tool/check_page_contract.py --report      # the full table and the debt
    python3 tool/check_page_contract.py --crossrefs   # resolve every "chapter N"
    python3 tool/check_page_contract.py --json        # machine-readable

The gate is deliberately separate from ``tool/build_blog.py``. The site build is
standard-library-only and standalone so that no content problem can take the
published page down; this check fails a *pull request*, which is where a page is
reviewed, not a deploy. See ``blog/README.md`` and the ``course-team`` skill.

Exit status is 0 when every enforced chapter passes, 1 when something must be
fixed, and 2 when the repository could not be read at all.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tool.blog import contract  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check the page contract.")
    parser.add_argument("--repo-root", type=Path,
                        default=Path(__file__).resolve().parents[1])
    parser.add_argument("--report", action="store_true",
                        help="print the per-chapter table and the legacy debt")
    parser.add_argument("--crossrefs", action="store_true",
                        help="print every numeric chapter reference, resolved")
    parser.add_argument("--json", action="store_true",
                        help="emit the report as JSON instead of prose")
    parser.add_argument("--quiet", action="store_true",
                        help="print nothing when the contract holds")
    parser.add_argument("--review", action="store_true",
                        help="also require a brief and a fresh evidence pack "
                             "(two cold reads, QA, gate) -- the slow mode")
    args = parser.parse_args(argv)

    try:
        report = contract.check(args.repo_root, review=args.review)
    except contract.ContractError as exc:
        print(f"error: cannot check the contract: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(_as_json(report), indent=2, ensure_ascii=False))
    elif args.crossrefs:
        print(contract.render_crossrefs(report))
    elif not (args.quiet and report.ok):
        print(contract.render(report, verbose=args.report))

    return 0 if report.ok else 1


def _as_json(report: contract.Report) -> dict:
    return {
        "ok": report.ok,
        "mode": "review" if report.review else "fast",
        "failures": [
            {"slug": v.slug, "rule": v.rule, "detail": v.detail}
            for v in report.failures
        ],
        "repo": [
            {"slug": v.slug, "rule": v.rule, "detail": v.detail}
            for v in report.repo
        ],
        "chapters": [
            {
                "slug": c.slug,
                "number": c.number,
                "title": c.title,
                "level": c.level,
                "legacy": c.legacy,
                "briefed": c.briefed,
                "metrics": c.metrics,
                "violations": [
                    {"rule": v.rule, "detail": v.detail} for v in c.violations
                ],
            }
            for c in report.chapters
        ],
        "crossrefs": [
            {"from": slug, "chapter": target, "title": title}
            for slug, target, title in report.crossrefs
        ],
        "pages": [
            {
                "slug": p.slug,
                "title": p.title,
                "written": p.written,
                "violations": [
                    {"rule": v.rule, "detail": v.detail} for v in p.violations
                ],
            }
            for p in report.pages
        ],
    }


if __name__ == "__main__":
    raise SystemExit(main())
