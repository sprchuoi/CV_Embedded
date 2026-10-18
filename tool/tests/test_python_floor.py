"""The Python 3.11 floor, enforced on the machine that does not have it.

CI byte-compiles ``tool/`` on 3.11 and 3.12 (``.github/workflows/python-app.yml``),
which is how a 3.12-only construct is caught before it reaches ``main``. That
step has one blind spot: the laptop is 3.12, so the construct compiles locally
and the failure appears only after a push. It happened once — an escape sequence
inside an f-string replacement field, PEP 701 — and the unit tests said nothing.

This test closes the gap for the construct that actually bit: it re-reads every
module under ``tool/`` and flags a backslash inside an f-string *expression*,
which 3.11 rejects as a ``SyntaxError``. The check runs only where the syntax
exists in the first place (3.12 and later); on 3.11 such a file cannot compile,
so there is nothing left for the test to find.

The detector is itself tested against a synthetic file, so a regex that stops
matching fails the suite instead of passing it silently.
"""

from __future__ import annotations

import io
import tempfile
import tokenize
import unittest
from pathlib import Path

TOOL = Path(__file__).resolve().parents[1]


def fstring_expression_backslashes(source: bytes) -> list[tuple[int, str]]:
    """``(line, token)`` for every backslash inside an f-string expression.

    In the 3.12 tokenizer an f-string is ``FSTRING_START`` … ``FSTRING_END``,
    with the literal parts as ``FSTRING_MIDDLE`` and the replacement fields as
    ordinary tokens between ``{`` and ``}``. A backslash is legal in the middle
    (it is just text) and illegal in the field, which is exactly the distinction
    3.11 makes.
    """
    found: list[tuple[int, str]] = []
    depth = 0
    for token in tokenize.tokenize(io.BytesIO(source).readline):
        if token.type == tokenize.FSTRING_START:
            depth += 1
        elif token.type == tokenize.FSTRING_END:
            depth -= 1
        elif (depth and token.type != tokenize.FSTRING_MIDDLE
              and "\\" in token.string):
            found.append((token.start[0], token.string))
    return found


@unittest.skipUnless(hasattr(tokenize, "FSTRING_START"),
                     "Python < 3.12 cannot produce PEP 701 syntax")
class TestPythonFloor(unittest.TestCase):
    def test_a_backslash_inside_an_fstring_field_is_detected(self):
        bad = b'x = f"{\'a\\u2099\':<10s}"\n'
        self.assertEqual(fstring_expression_backslashes(bad),
                         [(1, "'a\\u2099'")])

    def test_a_backslash_in_the_literal_part_is_allowed(self):
        # "a\nb" is text, not an expression: legal on every version.
        self.assertEqual(fstring_expression_backslashes(b'x = f"a\\nb {n}"\n'), [])

    def test_an_ordinary_fstring_is_clean(self):
        self.assertEqual(fstring_expression_backslashes(b'x = f"{n:3d} {a}"\n'), [])

    def test_no_module_under_tool_uses_pep701_backslashes(self):
        offenders: list[str] = []
        for path in sorted(TOOL.rglob("*.py")):
            for line, text in fstring_expression_backslashes(path.read_bytes()):
                offenders.append(f"{path.relative_to(TOOL)}:{line}: {text!r}")
        self.assertEqual(
            offenders, [],
            "3.12-only f-string syntax; Python 3.11 rejects this. Bind the "
            "escaped value to a name outside the f-string:\n  "
            + "\n  ".join(offenders))


if __name__ == "__main__":
    unittest.main()
