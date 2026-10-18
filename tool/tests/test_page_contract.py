"""Tests for the course-team page contract.

The contract is the only thing standing between a chapter and publication, so
these tests aim at both directions: every rule must actually fire when it is
broken, and it must not fire on the corpus the rules were derived from. The last
class pins that second property against the real repository, which is what stops
a future edit from quietly raising the bar above the author's own best work.

Run from the repo root:

    python3 -m unittest discover -s tool/tests -t . -v
"""

import ast
import hashlib
import inspect
import json
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from tool.blog import contract  # noqa: E402
from tool.blog import markdown as md  # noqa: E402

POSTS = REPO / "blog" / "posts"


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #


def valid_body(*, figures: int = 3, crossrefs: tuple[str, ...] = (),
               optical_last: bool = True, try_callout: bool = True,
               takeaways: int = 3, opening: int = 1) -> str:
    """A chapter that satisfies every structural rule.

    Each keyword breaks one rule, so a test names the rule it is exercising and
    reads as the sentence it is testing.
    """
    lines = ["An orientation paragraph that names the problem and why it matters.",
             "A second paragraph, because this course orients before it divides."]
    lines = lines[:opening]
    lines += ["", "## The first idea", "",
              "Prose that explains the idea in words before it reaches for symbols."]
    # `figures` counts the closing figure too, so the total is exactly what the
    # caller asked for rather than one more.
    for index in range(figures):
        caption = ("The closing figure, captioned with its takeaway."
                   if index == figures - 1 else
                   f"Figure {index + 1}, captioned with its takeaway.")
        if index:
            lines += ["", f"## Idea number {index + 1}", ""]
        lines += ["", f"![{caption}](assets/diagrams/f{index + 1}.svg)"]
    if try_callout:
        lines += ["", "::: try Something to do today",
                  "Open the datasheet nearest to hand and find the number.", ":::"]
    lines += ["", "## What to carry forward", ""]
    for index in range(takeaways):
        lines += [f"- Takeaway number {index + 1}, in one sentence."]
    if crossrefs:
        lines += ["", "This is the same operation as " + ", ".join(crossrefs) + "."]
    if optical_last:
        lines += ["", "::: optical Where this shows up in an optical link",
                  "It shows up in the receiver, at rate, in fixed point.", ":::"]
    else:
        lines += ["", "## A trailing section", "",
                  "Prose after the optical callout, which is the defect.", "",
                  "::: optical Where this shows up in an optical link",
                  "It shows up in the receiver.", ":::", "",
                  "## And a section after that", "", "More prose."]
    return "\n".join(lines) + "\n"


def insert_before_optical(body: str, text: str) -> str:
    """Add prose to a valid chapter without moving the closing callout.

    Appending to the end of ``valid_body()`` would break ``optical-last``, which
    would make an unrelated rule the thing under test.
    """
    head, marker, tail = body.partition("::: optical")
    return head + text.rstrip("\n") + "\n\n" + marker + tail


def valid_brief(*, slug: str = "one", level: str = "Beginner",
                prereqs: str = "none") -> str:
    return "\n".join([
        "# A page brief",
        "",
        f"Slug: {slug}",
        f"Level: {level}",
        f"Prerequisites: {prereqs}",
        "",
        "## Outcomes",
        "- Name the two quantities and say which one a datasheet actually reports.",
        "- Work the number out for a link you really have, from first principles.",
        "- Explain to a colleague why the obvious answer is wrong.",
        "",
        "## Claims to verify",
        "- The 6.02 N + 1.76 figure follows from a full-scale sine, not any signal.",
        "- Every value in figure 3 matches the arithmetic shown in this chapter.",
        "",
        "## Transfer",
        "Work: the receiver's converter budget, where this number is a line item.",
        "Life: the same arithmetic sets the noise floor of any recording you make.",
        "",
        "## Comprehension plan",
        "- engineer: can they redo the derivation with the chapter closed?",
        "- newcomer: does the opening paragraph make the problem feel real?",
    ]) + "\n"


TRANSCRIPT_FILLER = (
    "I read the chapter once without notes and then tried to redraw the diagram "
    "from memory, which is the test I use for myself. The opening paragraph did "
    "its job: I knew what problem was being solved before any symbol appeared. "
    "The derivation in the middle section I could follow line by line, but I "
    "could not have produced it, and I still cannot say why the third step is "
    "allowed. The figure captions carried most of the weight for me. What I "
    "would want before this is called finished is one worked number I can check "
    "against my own calculator, because every claim in the chapter is currently "
    "a shape rather than a quantity. The transfer section is the part I will "
    "actually use on Monday."
)


def transcript(digest: str, *, persona: str = "engineer",
               verdict: str = "partial", dispositions: int = 1,
               stalls: int = 1, words: int = 1) -> str:
    body = TRANSCRIPT_FILLER * words
    stalls_text = "\n".join(
        "- At the third step of the derivation in the middle section."
        for _ in range(stalls)
    )
    dispositions_text = "\n".join(
        "- [fixed] The author rewrote the step and added the missing reason."
        for _ in range(dispositions)
    )
    return "\n".join([
        f"Reviewed-hash: {digest}",
        f"Persona: {persona}",
        f"Verdict: {verdict}",
        "",
        "## Reproduced",
        "- The four-way classification, including which quadrant a codec sits in.",
        "- The two rules of thumb, with their conditions.",
        "",
        "## Stalls",
        stalls_text,
        "",
        "## Dispositions",
        dispositions_text,
        "",
        "## Notes",
        body,
    ]) + "\n"


def qa_findings(digest: str, *, disposition: str = "fixed") -> str:
    return "\n".join([
        f"Reviewed-hash: {digest}",
        "",
        "## Findings",
        f"- [{disposition}] Figure 3's y-axis label says volts where the text says "
        "amperes; the figure was regenerated.",
        "",
        "## Build",
        "`python3 tool/build_blog.py` and "
        "`python3 -m unittest discover -s tool/tests -t .` both pass.",
    ]) + "\n"


def gate(digest: str, *, verdict: str = "PASS") -> str:
    return "\n".join([
        f"Reviewed-hash: {digest}",
        f"Verdict: {verdict}",
        "",
        "## Checker",
        "A fresh session given only the repository and the gate checks; it did "
        "not see the author's notes or this session's transcript.",
        "",
        "## Commands",
        "```",
        "python3 tool/check_page_contract.py",
        "python3 tool/build_blog.py --check",
        "```",
    ]) + "\n"


class RepoFixture(unittest.TestCase):
    """A throwaway repository holding only what the contract checker reads."""

    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)

    def build_repo(self, posts: dict[str, str], legacy: list[str], *,
                   briefs: dict[str, str] | None = None,
                   evidence: dict[str, dict[str, str]] | None = None,
                   unwritten: tuple[str, ...] = (),
                   baseline: tuple[str, ...] | None = None) -> Path:
        """Write a throwaway repository and pin the frozen ratchet baseline.

        ``baseline`` defaults to the fixture's own ``legacy`` list -- "these
        slugs are the ones that predate the contract", which is what a fixture
        with synthetic slugs means. Pass ``baseline=()`` to exercise the rule
        that a *new* exemption cannot be added.
        """
        patcher = mock.patch.object(
            contract, "LEGACY_BASELINE",
            frozenset(legacy if baseline is None else baseline))
        patcher.start()
        self.addCleanup(patcher.stop)

        (self.root / "blog" / "posts").mkdir(parents=True)
        (self.root / "blog" / "contracts").mkdir(parents=True)
        curriculum = {
            "title": "T", "tagline": "t", "author": {"name": "A"}, "pages": [],
            "parts": [{
                "id": "p1", "level": "Beginner", "title": "Part one", "blurb": "b",
                "articles": [{"slug": slug, "title": slug.title(), "summary": "s",
                              "tags": []}
                             for slug in list(posts) + list(unwritten)],
            }],
        }
        (self.root / "blog" / "curriculum.json").write_text(
            json.dumps(curriculum), encoding="utf-8")
        for slug, body in posts.items():
            (self.root / "blog" / "posts" / f"{slug}.md").write_text(
                body, encoding="utf-8")
        (self.root / "blog" / "contracts" / "legacy.txt").write_text(
            "\n".join(legacy) + "\n", encoding="utf-8")
        for slug, text in (briefs or {}).items():
            (self.root / "blog" / "contracts" / f"{slug}.md").write_text(
                text, encoding="utf-8")
        for slug, files in (evidence or {}).items():
            self.write_evidence(slug, files)
        return self.root

    def write_evidence(self, slug: str, files: dict[str, str]) -> None:
        """Write an evidence pack. Separate from ``build_repo`` because a pack
        cites the post's hash, so the post has to be on disk first."""
        directory = self.root / "blog" / "evidence" / slug
        directory.mkdir(parents=True, exist_ok=True)
        for name, text in files.items():
            (directory / name).write_text(text, encoding="utf-8")

    def digest(self, slug: str = "one") -> str:
        return hashlib.sha1(
            (self.root / "blog" / "posts" / f"{slug}.md").read_bytes()
        ).hexdigest()

    def full_evidence(self, slug: str = "one") -> dict[str, str]:
        digest = self.digest(slug)
        return {
            "student-engineer.md": transcript(digest, persona="engineer"),
            "student-newcomer.md": transcript(digest, persona="newcomer",
                                              verdict="understood"),
            "qa-findings.md": qa_findings(digest),
            "gate.md": gate(digest),
        }


# --------------------------------------------------------------------------- #
# Structural rules
# --------------------------------------------------------------------------- #


class TestAnatomy(RepoFixture):
    def rules(self, body: str, *, number: int = 1,
              planned: int = 48) -> set[str]:
        violations, _ = contract.check_anatomy(body, slug="one", number=number,
                                               planned=planned)
        return {v.rule for v in violations}

    def test_a_valid_chapter_has_no_findings(self):
        self.assertEqual(self.rules(valid_body()), set())

    def test_too_few_figures(self):
        self.assertIn("figures", self.rules(valid_body(figures=2)))

    def test_no_orientation_paragraph(self):
        self.assertIn("opening", self.rules(valid_body(opening=0)))

    def test_missing_optical_callout(self):
        body = valid_body().replace("::: optical", "::: note")
        self.assertIn("optical-callout", self.rules(body))

    def test_prose_after_the_optical_callout(self):
        self.assertIn("optical-last", self.rules(valid_body(optical_last=False)))

    def test_a_trailing_code_fence_is_not_the_optical_callout(self):
        # A fenced block after the closing callout is still something after it.
        # Masking code used to hide it, which was a real bypass of optical-last.
        body = valid_body() + "\n```sh\necho 'a snippet after the callout'\n```\n"
        self.assertIn("optical-last", self.rules(body))

    def test_a_fence_cannot_invent_an_optical_callout(self):
        # The converse of the exception: callout detection stays masked, so a
        # snippet that merely contains the words is not a callout.
        body = valid_body().replace(
            "::: optical Where this shows up in an optical link",
            "```\n::: optical not a real callout\n```")
        self.assertIn("optical-callout", self.rules(body))

    def test_a_nested_callout_inside_the_optical_callout_is_accepted(self):
        # The renderer counts nesting, so the scanner must too: reading the inner
        # `:::` as the outer close made the rest of the optical callout look like
        # trailing content, rejecting a chapter the site renders happily.
        nested = (
            "::: optical Where this shows up in an optical link\n"
            "It shows up in the receiver.\n"
            "::: note The honest caveat\n"
            "This holds only while the channel is static.\n"
            ":::\n"
            "And the rest of the optical callout.\n"
            ":::"
        )
        body = valid_body().replace(
            "::: optical Where this shows up in an optical link\n"
            "It shows up in the receiver, at rate, in fixed point.\n"
            ":::", nested)
        self.assertIn(nested, body, "the fixture text did not match")
        # The site must render what the contract accepts, or this is a test of
        # two tools disagreeing rather than of the contract being right.
        rendered = md.render(body)
        self.assertIn("callout-optical", rendered.html)
        self.assertEqual(self.rules(body), set())

    def test_missing_try_callout(self):
        self.assertIn("try-callout", self.rules(valid_body(try_callout=False)))

    def test_missing_takeaways(self):
        self.assertIn("takeaways", self.rules(valid_body(takeaways=0)))

    def test_too_few_takeaways(self):
        self.assertIn("takeaways", self.rules(valid_body(takeaways=2)))

    def test_a_differently_named_takeaway_section_is_accepted(self):
        body = valid_body().replace("## What to carry forward", "## Takeaways")
        self.assertEqual(self.rules(body), set())

    def test_placeholder_is_rejected(self):
        body = insert_before_optical(valid_body(), "TODO: finish this section")
        self.assertIn("no-placeholders", self.rules(body))

    def test_placeholder_inside_a_code_fence_is_ignored(self):
        body = insert_before_optical(valid_body(), "```sh\n# TODO: not prose\n```")
        self.assertEqual(self.rules(body), set())

    def test_an_unclosed_callout_after_the_optical_one_takes_the_last_slot(self):
        # A callout opened and never closed is a Markdown error, but the point
        # here is that the check does not mistake it for ordinary prose.
        body = valid_body() + "\n::: note oops\nunclosed\n"
        self.assertIn("optical-last", self.rules(body))

    def test_unbalanced_display_math(self):
        body = insert_before_optical(valid_body(), "$$x = 1")
        self.assertIn("math-balanced", self.rules(body))

    def test_unbalanced_inline_math(self):
        body = insert_before_optical(valid_body(), "the value $x is")
        self.assertIn("math-balanced", self.rules(body))

    def test_balanced_math_is_accepted(self):
        body = insert_before_optical(
            valid_body(), "The value $x = 1$ is fine, and so is $$y = 2$$.")
        self.assertEqual(self.rules(body), set())

    def test_dollar_amounts_are_not_math(self):
        # "$5 and $10" would otherwise look like one balanced pair and pass; the
        # rule only has to stop the unbalanced case, which it does.
        body = insert_before_optical(valid_body(), "It cost $5, then $10, then $3.")
        self.assertIn("math-balanced", self.rules(body))

    def test_cross_reference_out_of_range(self):
        self.assertIn("cross-ref-range", self.rules(valid_body(crossrefs=("chapter 60",))))

    def test_cross_reference_to_itself(self):
        self.assertIn("cross-ref-self",
                      self.rules(valid_body(crossrefs=("chapter 1",)), number=1))

    def test_cross_reference_range_is_checked_at_both_ends(self):
        self.assertIn("cross-ref-range",
                      self.rules(valid_body(crossrefs=("chapters 10 to 99",))))

    def test_a_valid_cross_reference_is_accepted(self):
        self.assertEqual(self.rules(valid_body(crossrefs=("chapter 10",)), number=1),
                         set())

    def test_metrics_are_reported(self):
        _, metrics = contract.check_anatomy(valid_body(figures=5), slug="one",
                                            number=1, planned=48)
        self.assertEqual(metrics["figures"], 5)
        self.assertGreater(metrics["words"], 0)


# --------------------------------------------------------------------------- #
# Briefs
# --------------------------------------------------------------------------- #


class TestBrief(unittest.TestCase):
    def rules(self, text: str, **kwargs) -> set[str]:
        defaults = {"slug": "one", "level": "Beginner", "preceding": {}}
        defaults.update(kwargs)
        return {v.rule for v in contract.check_brief(text, **defaults)}

    def test_a_valid_brief_has_no_findings(self):
        self.assertEqual(self.rules(valid_brief()), set())

    def test_slug_must_match_the_chapter(self):
        self.assertIn("brief-slug", self.rules(valid_brief(slug="two")))

    def test_level_must_match_the_curriculum(self):
        self.assertIn("brief-level",
                      self.rules(valid_brief(level="Specialist")))

    def test_too_few_outcomes(self):
        text = valid_brief().replace(
            "- Explain to a colleague why the obvious answer is wrong.\n", "")
        self.assertIn("brief-outcomes", self.rules(text))

    def test_a_prerequisite_must_be_an_earlier_chapter(self):
        self.assertIn("brief-prerequisites",
                      self.rules(valid_brief(prereqs="sampling-and-aliasing")))

    def test_a_real_earlier_prerequisite_is_accepted(self):
        self.assertEqual(
            self.rules(valid_brief(prereqs="zero"), preceding={"zero": 1}), set())

    def test_none_is_accepted_as_the_prerequisite_list(self):
        self.assertEqual(self.rules(valid_brief(prereqs="None")), set())

    def test_too_few_claims(self):
        text = valid_brief().replace(
            "- Every value in figure 3 matches the arithmetic shown in this "
            "chapter.\n", "")
        self.assertIn("brief-claims", self.rules(text))

    def test_transfer_needs_a_life_line(self):
        text = valid_brief().replace(
            "Life: the same arithmetic sets the noise floor of any recording you "
            "make.\n", "")
        self.assertIn("brief-transfer", self.rules(text))

    def test_transfer_needs_a_work_line(self):
        text = valid_brief().replace(
            "Work: the receiver's converter budget, where this number is a line "
            "item.\n", "")
        self.assertIn("brief-transfer", self.rules(text))

    def test_the_plan_must_name_both_personas(self):
        text = valid_brief().replace(
            "- newcomer: does the opening paragraph make the problem feel real?\n", "")
        self.assertIn("brief-plan", self.rules(text))

    def test_a_claims_table_is_accepted_instead_of_bullets(self):
        text = valid_brief().replace(
            "- The 6.02 N + 1.76 figure follows from a full-scale sine, not any "
            "signal.\n- Every value in figure 3 matches the arithmetic shown in "
            "this chapter.\n",
            "| Claim | Where it is checkable |\n|---|---|\n"
            "| The 6.02 N + 1.76 figure follows from a full-scale sine. | figure 2 |\n"
            "| Figure 3's values match the chapter's arithmetic. | figure 3 |\n")
        self.assertEqual(self.rules(text), set())


# --------------------------------------------------------------------------- #
# Evidence packs
# --------------------------------------------------------------------------- #


class TestEvidence(RepoFixture):
    def setUp(self) -> None:
        super().setUp()
        # The pack is written against this post's hash, so the post has to exist
        # before any transcript can be built.
        self.build_repo({"one": valid_body()}, legacy=[])

    def rules(self, files: dict[str, str]) -> set[str]:
        digest = self.digest()
        directory = self.root / "blog" / "evidence" / "one"
        directory.mkdir(parents=True, exist_ok=True)
        for name, text in files.items():
            (directory / name).write_text(
                text.replace("__DIGEST__", digest), encoding="utf-8")
        violations = contract.check_evidence(
            directory, slug="one", post=self.root / "blog" / "posts" / "one.md")
        return {v.rule for v in violations}

    def test_a_complete_pack_has_no_findings(self):
        self.assertEqual(self.rules(self.full_evidence()), set())

    def test_a_missing_file_is_a_finding(self):
        files = self.full_evidence()
        del files["gate.md"]
        self.assertIn("evidence-missing", self.rules(files))

    def test_a_stale_hash_is_a_finding(self):
        files = self.full_evidence()
        files["student-engineer.md"] = files["student-engineer.md"].replace(
            self.digest(), "0" * 40)
        self.assertIn("evidence-stale", self.rules(files))

    def test_a_thin_transcript_is_a_finding(self):
        files = self.full_evidence()
        digest = self.digest()
        files["student-newcomer.md"] = transcript(digest, persona="newcomer",
                                                  words=0)
        self.assertIn("evidence-thin", self.rules(files))

    def test_an_unknown_verdict_is_a_finding(self):
        files = self.full_evidence()
        files["student-engineer.md"] = files["student-engineer.md"].replace(
            "Verdict: partial", "Verdict: fine")
        self.assertIn("evidence-verdict", self.rules(files))

    def test_every_stall_needs_a_disposition(self):
        files = self.full_evidence()
        digest = self.digest()
        files["student-engineer.md"] = transcript(digest, persona="engineer",
                                                  stalls=3, dispositions=1)
        self.assertIn("evidence-dispositions", self.rules(files))

    def test_a_disposition_must_be_tagged(self):
        files = self.full_evidence()
        files["student-engineer.md"] = files["student-engineer.md"].replace(
            "- [fixed]", "- ")
        self.assertIn("evidence-dispositions", self.rules(files))

    def test_a_disposition_needs_a_reason(self):
        files = self.full_evidence()
        files["student-engineer.md"] = files["student-engineer.md"].replace(
            "- [fixed] The author rewrote the step and added the missing reason.",
            "- [fixed] n/a")
        self.assertIn("evidence-dispositions", self.rules(files))

    def test_an_open_qa_finding_blocks_publication(self):
        files = self.full_evidence()
        digest = self.digest()
        files["qa-findings.md"] = qa_findings(digest, disposition="open")
        self.assertIn("evidence-qa-open", self.rules(files))

    def test_qa_must_record_what_it_ran(self):
        files = self.full_evidence()
        files["qa-findings.md"] = files["qa-findings.md"].replace(
            "## Build", "## Something else")
        self.assertIn("evidence-qa", self.rules(files))

    def test_a_transcript_must_list_what_was_reproduced(self):
        files = self.full_evidence()
        files["student-engineer.md"] = files["student-engineer.md"].replace(
            "## Reproduced", "## Something else")
        self.assertIn("evidence-reproduced", self.rules(files))

    def test_the_gate_must_pass(self):
        files = self.full_evidence()
        digest = self.digest()
        files["gate.md"] = gate(digest, verdict="SHUT")
        self.assertIn("evidence-gate", self.rules(files))

    def test_the_gate_must_name_its_checker(self):
        files = self.full_evidence()
        files["gate.md"] = files["gate.md"].replace("## Checker", "## Notes")
        self.assertIn("evidence-gate", self.rules(files))


# --------------------------------------------------------------------------- #
# The ratchet
# --------------------------------------------------------------------------- #


class TestRatchet(RepoFixture):
    def test_a_clean_chapter_is_accepted_without_paperwork_by_default(self):
        # The fast mode: write it, build it, and the structure is the contract.
        # The user reads the facts; the checker does not insist on a brief.
        self.build_repo({"one": valid_body()}, legacy=[])
        report = contract.check(self.root)
        self.assertTrue(report.ok, [str(v) for v in report.failures])
        self.assertFalse(report.review)

    def test_review_mode_requires_a_brief(self):
        self.build_repo({"one": valid_body()}, legacy=[])
        report = contract.check(self.root, review=True)
        self.assertFalse(report.ok)
        self.assertIn("brief-missing", {v.rule for v in report.failures})

    def test_legacy_exempts_a_chapter_from_the_structural_rules(self):
        # The point of the exemption: a one-word fix to an old chapter is never
        # blocked by a contract written after it.
        self.build_repo({"one": valid_body(optical_last=False, try_callout=False)},
                        legacy=["one"])
        report = contract.check(self.root)
        self.assertTrue(report.ok)
        self.assertEqual(len(report.debt), 1)

    def test_a_briefed_chapter_needs_a_fresh_evidence_pack_in_review_mode(self):
        self.build_repo({"one": valid_body()}, legacy=[],
                        briefs={"one": valid_brief()})
        report = contract.check(self.root, review=True)
        self.assertIn("evidence-missing", {v.rule for v in report.failures})

    def test_a_briefed_chapter_without_evidence_passes_in_fast_mode(self):
        self.build_repo({"one": valid_body()}, legacy=[],
                        briefs={"one": valid_brief()})
        self.assertTrue(contract.check(self.root).ok)

    def test_a_fully_delivered_chapter_passes_review(self):
        self.build_repo({"one": valid_body()}, legacy=[],
                        briefs={"one": valid_brief()})
        self.write_evidence("one", self.full_evidence())
        report = contract.check(self.root, review=True)
        self.assertTrue(report.ok, [str(v) for v in report.failures])

    def test_a_briefed_chapter_that_also_satisfies_the_anatomy_is_not_exempt(self):
        self.build_repo({"one": valid_body()}, legacy=["one"],
                        briefs={"one": valid_brief()})
        self.write_evidence("one", self.full_evidence())
        report = contract.check(self.root)
        self.assertIn("legacy-stale-exemption", {v.rule for v in report.repo})

    def test_a_legacy_chapter_with_a_structural_defect_is_not_a_stale_exemption(self):
        self.build_repo({"one": valid_body(try_callout=False)}, legacy=["one"],
                        briefs={"one": valid_brief()})
        self.write_evidence("one", self.full_evidence())
        report = contract.check(self.root)
        self.assertNotIn("legacy-stale-exemption", {v.rule for v in report.repo})

    def test_an_exempted_slug_that_is_not_a_chapter_is_a_repo_defect(self):
        self.build_repo({"one": valid_body()}, legacy=["one", "ghost"])
        self.assertIn("legacy-unknown",
                      {v.rule for v in contract.check(self.root).repo})

    def test_a_duplicate_exemption_is_a_repo_defect(self):
        self.build_repo({"one": valid_body()}, legacy=["one", "one"])
        self.assertIn("legacy-duplicate",
                      {v.rule for v in contract.check(self.root).repo})

    def test_a_new_exemption_cannot_be_added(self):
        # The hole this closes: one line in legacy.txt used to exempt a
        # brand-new chapter from the anatomy *and* from the brief, after which
        # the gate reported that every enforced chapter was publishable.
        self.build_repo({"one": valid_body(figures=0, optical_last=False,
                                           try_callout=False, takeaways=0)},
                        legacy=["one"], baseline=())
        report = contract.check(self.root)
        self.assertIn("legacy-added", {v.rule for v in report.failures})
        self.assertFalse(report.ok)

    def test_an_exemption_that_predates_the_contract_is_accepted(self):
        self.build_repo({"one": valid_body(figures=0, optical_last=False)},
                        legacy=["one"])
        self.assertTrue(contract.check(self.root).ok)

    def test_an_exempted_chapter_with_no_prose_is_a_repo_defect(self):
        self.build_repo({"one": valid_body()}, legacy=["one", "two"],
                        unwritten=("two",))
        self.assertIn("legacy-unwritten",
                      {v.rule for v in contract.check(self.root).repo})

    def test_a_brief_can_be_written_before_the_prose(self):
        # The design is reviewable on its own; evidence is not demanded until
        # there is a revision to review.
        self.build_repo({"one": valid_body()}, legacy=["one"],
                        briefs={"two": valid_brief(slug="two")},
                        unwritten=("two",))
        report = contract.check(self.root)
        self.assertTrue(report.ok, [str(v) for v in report.failures])
        self.assertEqual([c.slug for c in report.in_flight], ["two"])
        self.assertEqual([c.slug for c in report.published], ["one"])

    def test_an_invalid_brief_for_an_unwritten_chapter_is_a_finding(self):
        self.build_repo({"one": valid_body()}, legacy=["one"],
                        briefs={"two": valid_brief(slug="wrong")},
                        unwritten=("two",))
        report = contract.check(self.root)
        self.assertIn("brief-slug", {v.rule for v in report.failures})

    def test_promotable_and_debt_classify_the_backlog(self):
        self.build_repo({"one": valid_body(), "two": valid_body(try_callout=False)},
                        legacy=["one", "two"])
        report = contract.check(self.root)
        self.assertEqual([c.slug for c in report.promotable], ["one"])
        self.assertEqual([c.slug for c in report.debt], ["two"])

    def test_an_unwritable_curriculum_is_a_contract_error(self):
        (self.root / "blog").mkdir(parents=True)
        with self.assertRaises(contract.ContractError):
            contract.check(self.root)

    def test_a_missing_legacy_file_is_a_repo_defect(self):
        self.build_repo({"one": valid_body()}, legacy=[])
        (self.root / "blog" / "contracts" / "legacy.txt").unlink()
        self.assertIn("legacy-missing",
                      {v.rule for v in contract.check(self.root).repo})


class TestStandalonePages(RepoFixture):
    """Pages get the prose-agnostic rules, and deliberately not the chapter anatomy."""

    def build_with_pages(self, body: str) -> contract.Report:
        self.build_repo({"one": valid_body()}, legacy=["one"])
        curriculum = json.loads(
            (self.root / "blog" / "curriculum.json").read_text(encoding="utf-8"))
        curriculum["pages"] = [{"slug": "vision", "title": "Vision",
                                "summary": "s", "placement": "page"}]
        (self.root / "blog" / "curriculum.json").write_text(
            json.dumps(curriculum), encoding="utf-8")
        pages = self.root / "blog" / "pages"
        pages.mkdir(parents=True, exist_ok=True)
        (pages / "vision.md").write_text(body, encoding="utf-8")
        return contract.check(self.root)

    def test_a_page_needs_no_chapter_anatomy(self):
        # No figures, no callouts, no takeaway list -- and that is correct for
        # the Vision document, which is explicitly a working statement.
        report = self.build_with_pages(
            "A working document, revised as the work changes.\n\n"
            "## The thesis\n\nProse with no figures and no callouts at all.\n")
        self.assertTrue(report.ok, [str(v) for v in report.failures])
        self.assertEqual([p.slug for p in report.pages], ["vision"])

    def test_a_page_placeholder_is_a_finding(self):
        report = self.build_with_pages("TODO: write the thesis.\n")
        self.assertIn("no-placeholders", {v.rule for v in report.failures})

    def test_unbalanced_math_in_a_page_is_a_finding(self):
        report = self.build_with_pages("The transform grows by $\\log_2 N bits.\n")
        self.assertIn("math-balanced", {v.rule for v in report.failures})

    def test_an_unwritten_page_is_not_a_finding(self):
        self.build_repo({"one": valid_body()}, legacy=["one"])
        curriculum = json.loads(
            (self.root / "blog" / "curriculum.json").read_text(encoding="utf-8"))
        curriculum["pages"] = [{"slug": "later", "title": "Later",
                                "summary": "s", "placement": "page"}]
        (self.root / "blog" / "curriculum.json").write_text(
            json.dumps(curriculum), encoding="utf-8")
        report = contract.check(self.root)
        self.assertTrue(report.ok)
        self.assertEqual([p.slug for p in report.pages], ["later"])
        self.assertFalse(report.pages[0].written)


# --------------------------------------------------------------------------- #
# The real corpus
# --------------------------------------------------------------------------- #


class TestAgainstTheRealCorpus(unittest.TestCase):
    """The contract must hold on the repository, and sit below its own floor."""

    @classmethod
    def setUpClass(cls):
        cls.report = contract.check(REPO)
        cls.by_slug = {c.slug: c for c in cls.report.chapters}

    def test_the_contract_holds(self):
        self.assertTrue(self.report.ok, [str(v) for v in self.report.failures])

    def test_every_published_chapter_is_checked(self):
        published = sorted(p.stem for p in POSTS.glob("*.md"))
        checked = sorted(c.slug for c in self.report.published)
        self.assertEqual(checked, published)
        # The corpus pin. It moves when a chapter publishes, deliberately: a
        # new post that the report does not account for is the failure this
        # catches, and bumping a number a reviewer can see in the diff is
        # cheaper than letting the count drift out of agreement with the tree.
        # 25 = the 21 pre-contract chapters plus fourier-series-to-transform,
        # the-dft, windows-and-spectral-leakage and
        # z-transform-and-the-unit-circle, the four chapters written under the
        # contract so far. Counted from the tree, not by incrementing: run
        # `ls blog/posts/*.md | wc -l` before changing this number.
        self.assertEqual(len(published), 25)

    def test_the_rules_are_calibrated_to_the_corpus(self):
        # The rules the whole corpus already satisfies. The optical callout, the
        # try callout and the takeaway list are deliberately NOT asserted here:
        # 15 of 21 chapters break at least one of them, which is the debt the
        # ratchet exists to burn down, and asserting it would only mean deleting
        # this test or editing the exemptions.
        for slug, chapter in self.by_slug.items():
            with self.subTest(chapter=slug):
                failed = {v.rule for v in chapter.structural}
                self.assertNotIn("figures", failed)
                self.assertNotIn("opening", failed)
                self.assertNotIn("math-balanced", failed)
                self.assertNotIn("no-placeholders", failed)
                self.assertNotIn("cross-ref-range", failed)
                self.assertNotIn("cross-ref-self", failed)
                self.assertGreaterEqual(chapter.metrics["figures"],
                                        contract.MIN_FIGURES)

    def test_the_backlog_is_visible(self):
        # The backlog is the grandfathered corpus, not the whole corpus: every
        # chapter exempted in legacy.txt must appear in the report as either
        # debt or promotable, and no chapter that satisfies the contract may be
        # counted as backlog. Before the first contract-compliant chapter
        # existed the two sets were equal, so the weaker `== published` held;
        # it stops holding the moment the ratchet turns, and turning it is the
        # point.
        backlog = {c.slug for c in self.report.debt + self.report.promotable}
        legacy = {c.slug for c in self.report.chapters if c.legacy and c.published}
        self.assertEqual(backlog, legacy)
        self.assertTrue(backlog)                     # an empty backlog means the check is not reading legacy.txt

    def test_every_cross_reference_resolves_to_a_title(self):
        self.assertTrue(self.report.crossrefs)
        for _, _, title in self.report.crossrefs:
            self.assertNotEqual(title, "(out of range)")

    def test_the_standalone_pages_are_checked_too(self):
        self.assertEqual(sorted(p.slug for p in self.report.pages),
                         ["domain", "vision"])
        for page in self.report.pages:
            with self.subTest(page=page.slug):
                self.assertTrue(page.written)
                self.assertEqual(page.violations, [])

    def test_the_frozen_baseline_is_the_pre_contract_corpus(self):
        # The ratchet's teeth: legacy.txt may name a subset of this set, and the
        # set cannot grow. Pinning it means exempting a chapter shows up as an
        # edit to the checker, in a diff a reviewer is already reading.
        self.assertEqual(len(contract.LEGACY_BASELINE), 21)
        for slug in contract.LEGACY_BASELINE:
            with self.subTest(slug=slug):
                self.assertIn(slug, self.by_slug)
                self.assertTrue(self.by_slug[slug].published)

    def test_no_exemption_is_stale(self):
        # Every exempted chapter must still be structurally clean *or* still
        # have debt; a chapter that is clean and briefed must come off the list.
        self.assertNotIn("legacy-stale-exemption",
                         {v.rule for v in self.report.repo})
        self.assertNotIn("legacy-added", {v.rule for v in self.report.repo})


class TestOtherLanguages(RepoFixture):
    """The prose rules apply to every language; the teaching contract does not.

    A `TODO` left in a translated page used to pass silently, because the checker
    only ever loaded the default language.
    """

    def write_language(self, lang: str = "vi", *, page_body: str | None = None,
                       broken: bool = False) -> None:
        base = self.root / "blog" / lang
        (base / "posts").mkdir(parents=True, exist_ok=True)
        if broken:
            (base / "curriculum.json").write_text("{not json", encoding="utf-8")
            return
        data = {
            "title": "T", "tagline": "t", "author": {"name": "A"},
            "pages": [{"slug": "domain", "title": "Domain", "summary": "s",
                       "placement": "index"}],
            "parts": [{"id": "p1", "level": "Beginner", "title": "P", "blurb": "b",
                       "articles": [{"slug": "one", "title": "One",
                                     "summary": "s", "tags": []}]}],
        }
        (base / "curriculum.json").write_text(json.dumps(data), encoding="utf-8")
        if page_body is not None:
            (base / "pages").mkdir(parents=True, exist_ok=True)
            (base / "pages" / "domain.md").write_text(page_body, encoding="utf-8")

    def test_a_placeholder_in_a_translated_page_is_a_finding(self):
        self.build_repo({"one": valid_body()}, legacy=["one"])
        self.write_language(page_body="TODO: translate this page.\n")
        report = contract.check(self.root)
        self.assertIn("vi/domain", {v.slug for v in report.failures})
        self.assertIn("no-placeholders", {v.rule for v in report.failures})

    def test_a_placeholder_in_a_translated_chapter_is_a_finding(self):
        self.build_repo({"one": valid_body()}, legacy=["one"])
        self.write_language()
        (self.root / "blog" / "vi" / "posts" / "one.md").write_text(
            "Bản dịch chưa xong. $$x = 1\n", encoding="utf-8")
        report = contract.check(self.root)
        self.assertIn("vi/one", {v.slug for v in report.failures})

    def test_a_clean_translation_is_not_a_finding(self):
        self.build_repo({"one": valid_body()}, legacy=["one"])
        self.write_language(page_body="Đây là một trang đã được dịch.\n")
        self.assertTrue(contract.check(self.root).ok)

    def test_a_broken_translated_curriculum_is_a_repo_defect(self):
        self.build_repo({"one": valid_body()}, legacy=["one"])
        self.write_language(broken=True)
        self.assertIn("language-unreadable",
                      {v.rule for v in contract.check(self.root).repo})

    def test_a_missing_translation_is_left_to_the_build(self):
        # A declared language with no source is `check_parity`'s error, not this
        # check's; reporting it here too would be the same fault in two voices.
        self.build_repo({"one": valid_body()}, legacy=["one"])
        self.assertNotIn("language-unreadable",
                         {v.rule for v in contract.check(self.root).repo})

    def test_a_translation_without_its_english_source_is_a_finding(self):
        # The fourth check's find: with the slug in both curricula, a chapter
        # published only in translation skipped the anatomy, the brief and the
        # gate entirely, and the English roadmap still showed it as "Planned".
        self.build_repo({}, legacy=[], unwritten=("one",))
        self.write_language()
        (self.root / "blog" / "vi" / "posts" / "one.md").write_text(
            "Bản dịch của một chương chưa hề được viết.\n", encoding="utf-8")
        report = contract.check(self.root)
        self.assertIn("translation-without-source",
                      {v.rule for v in report.failures})

    def test_a_translation_of_a_published_legacy_chapter_is_fine(self):
        self.build_repo({"one": valid_body()}, legacy=["one"])
        self.write_language()
        (self.root / "blog" / "vi" / "posts" / "one.md").write_text(
            "Bản dịch hợp lệ.\n", encoding="utf-8")
        self.assertTrue(contract.check(self.root).ok)


# --------------------------------------------------------------------------- #
# The claims the documentation makes about this suite
# --------------------------------------------------------------------------- #


#: How the suite audits itself. Defined once, at module level, so the guard
#: tests below exercise *this* mechanism rather than a copy of it -- a copy is
#: how the first version of this audit passed while being blind to any rule name
#: carrying a digit.
#:
#: The charset is deliberately wider than today's kebab-case names.
RULE_CALL_RE = r'_v\(\s*[^,]+,\s*"([A-Za-z][A-Za-z0-9_-]*)"'


def rule_names_in(source: str) -> set[str]:
    """Every rule name literal passed to the ``_v`` helper in ``source``."""
    return set(re.findall(RULE_CALL_RE, source))


def operand_count(method_name: str) -> int:
    """How many positional arguments of an ``assert*`` call are operands.

    The message is always the *final* parameter, so its position depends on the
    assertion's arity: ``assertEqual(first, second, msg)`` has two operands,
    ``assertTrue(expr, msg)`` has one. Reading the signatures rather than
    assuming a fixed width is what stops a rule name smuggled in as a message
    from looking like a test -- a fixed ``args[:2]`` counted the message of every
    one-operand assertion.
    """
    method = getattr(unittest.TestCase, method_name, None)
    if method is None:
        return 2
    try:
        parameters = list(inspect.signature(method).parameters)
    except (TypeError, ValueError):
        return 2
    if "msg" not in parameters:
        return max(0, len(parameters) - 1)
    operands = parameters[1:parameters.index("msg")]
    if any(p.kind is inspect.Parameter.VAR_POSITIONAL
           for p in inspect.signature(method).parameters.values()):
        return 2
    return len(operands)


def asserted_text(source: str) -> str:
    """Every string literal used as an assertion *operand*, quoted, one per line.

    Parsed rather than grepped, because three grep-and-regex versions of this
    were defeated in turn: a rule quoted in a comment on its own line, one in a
    *trailing* comment on an assertion line, and one passed as an assertion
    *message*. A comment is not in the parse tree, and the message is the last
    parameter of the call, so the operand count comes from the real signature.

    Values come back quoted so a caller can ask for ``'"figures"'`` and get an
    exact match: a longer literal that merely contains the name is not a test of
    it.
    """
    tree = ast.parse(source)
    found: list[str] = []
    for node in ast.walk(tree):
        if (isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr.startswith("assert")):
            for argument in node.args[:operand_count(node.func.attr)]:
                for inner in ast.walk(argument):
                    if (isinstance(inner, ast.Constant)
                            and isinstance(inner.value, str)):
                        found.append(f'"{inner.value}"')
    return "\n".join(found)


class TestTheRulesAreCovered(unittest.TestCase):
    """`blog/README.md` claims every rule has a test. This is what makes it so.

    An adversarial check found two rules -- `evidence-reproduced` and
    `legacy-unwritten` -- that the suite never executed, so the claim was false
    when it was written. A second check found this audit defeatable by a
    digit-bearing rule name and by a comment quoting the rule. A third found the
    comment hole only half closed: a *trailing* comment on an assertion line
    still counted. The audit now parses the suite instead of grepping it, and
    each of those three attacks has a regression test against the real
    mechanism.

    **What this cannot do, stated rather than implied.** It is a static audit: it
    establishes that each rule's name appears as an assertion operand somewhere.
    It cannot tell a real assertion from a tautology -- a fifth check
    demonstrated that `self.assertEqual("my-new-rule", "my-new-rule")` satisfies
    it, and a rule can then be neutered with no test failing. Closing that would
    need the assertion actually executed against a fixture that triggers the
    rule, which is mutation testing and belongs in a separate, slower tier rather
    than in the suite every push runs. The audit's job is to catch a rule that
    was *forgotten*; a rule that was *faked* is a review finding.
    """

    @staticmethod
    def rule_names() -> set[str]:
        source = (REPO / "tool" / "blog" / "contract.py").read_text(encoding="utf-8")
        return rule_names_in(source) | set(contract.PROSE_RULES)

    def test_the_rule_extraction_actually_finds_the_rules(self):
        # A regex that matched nothing would make the next test vacuously pass.
        self.assertGreaterEqual(len(self.rule_names()), 30)

    def test_the_extraction_catches_a_digit_bearing_rule_name(self):
        synthetic = 'out.append(_v(slug, "min-3-figures", "detail"))'
        self.assertEqual(rule_names_in(synthetic), {"min-3-figures"})

    def test_the_extraction_catches_an_underscore_bearing_rule_name(self):
        synthetic = 'out.append(_v(slug, "evidence_2nd_read", "detail"))'
        self.assertEqual(rule_names_in(synthetic), {"evidence_2nd_read"})

    def test_every_rule_is_asserted_somewhere_in_this_suite(self):
        suite = (REPO / "tool" / "tests" / "test_page_contract.py").read_text(
            encoding="utf-8")
        untested = sorted(n for n in self.rule_names()
                          if f'"{n}"' not in asserted_text(suite))
        self.assertEqual(untested, [], f"rules with no test: {untested}")

    def test_a_rule_named_only_in_its_own_comment_does_not_count(self):
        synthetic = (
            "def test_x(self):\n"
            '    # a note about "brand-new-rule", not a test of it\n'
            "    self.assertEqual(self.rules(body), set())\n"
        )
        self.assertNotIn('"brand-new-rule"', asserted_text(synthetic))

    def test_a_rule_named_in_a_trailing_comment_does_not_count(self):
        # The third check's attack: a trailing comment on an assertion line.
        synthetic = (
            "def test_x(self):\n"
            '    self.assertEqual(1, 1)  # "brand-new-rule" is not tested here\n'
        )
        self.assertNotIn('"brand-new-rule"', asserted_text(synthetic))

    def test_a_rule_named_in_a_docstring_does_not_count(self):
        synthetic = (
            "def test_x(self):\n"
            '    """Mentions "brand-new-rule" in prose only."""\n'
            "    self.assertEqual(1, 1)\n"
        )
        self.assertNotIn('"brand-new-rule"', asserted_text(synthetic))

    def test_a_rule_named_in_a_non_assert_call_does_not_count(self):
        # `self.rules(...)` is a helper, not an assertion: naming the rule only
        # inside it tests nothing.
        synthetic = (
            "def test_x(self):\n"
            '    self.rules("brand-new-rule")\n'
            "    self.assertEqual(1, 1)\n"
        )
        self.assertNotIn('"brand-new-rule"', asserted_text(synthetic))

    def test_a_rule_named_only_as_an_assertion_message_does_not_count(self):
        # The fourth check's attack: the string is genuinely inside an assert
        # call, but as `msg`, where it explains a failure rather than testing
        # anything.
        synthetic = (
            "def test_x(self):\n"
            '    self.assertEqual(1, 1, "no-placeholders")\n'
        )
        self.assertNotIn('"no-placeholders"', asserted_text(synthetic))

    def test_a_rule_named_as_the_message_of_a_one_operand_assertion_does_not_count(self):
        # The fifth check's attack, which a fixed `args[:2]` missed: for
        # assertTrue the message is argument 1, not argument 2.
        synthetic = (
            "def test_x(self):\n"
            '    self.assertTrue(report.ok, "no-placeholders")\n'
        )
        self.assertNotIn('"no-placeholders"', asserted_text(synthetic))

    def test_a_rule_named_as_the_operand_of_a_one_operand_assertion_counts(self):
        synthetic = (
            "def test_x(self):\n"
            '    self.assertTrue("no-placeholders" in failed)\n'
        )
        self.assertIn('"no-placeholders"', asserted_text(synthetic))

    def test_the_operand_count_comes_from_the_real_signatures(self):
        # If this drifts, the guard above stops being arity-aware.
        self.assertEqual(operand_count("assertTrue"), 1)
        self.assertEqual(operand_count("assertFalse"), 1)
        self.assertEqual(operand_count("assertIn"), 2)
        self.assertEqual(operand_count("assertNotIn"), 2)
        self.assertEqual(operand_count("assertEqual"), 2)

    def test_a_keyword_message_does_not_count(self):
        synthetic = (
            "def test_x(self):\n"
            '    self.assertEqual(1, 1, msg="no-placeholders")\n'
        )
        self.assertNotIn('"no-placeholders"', asserted_text(synthetic))

    def test_an_assertion_line_does_count_as_covered(self):
        synthetic = (
            "def test_x(self):\n"
            '    self.assertIn("brand-new-rule", self.rules(body))\n'
        )
        self.assertIn('"brand-new-rule"', asserted_text(synthetic))


class TestTheReport(unittest.TestCase):
    """The report is what CI prints and what a Producer reads. It has to say
    what the documentation says it says."""

    @classmethod
    def setUpClass(cls):
        cls.report = contract.check(REPO)
        cls.text = contract.render(cls.report, verbose=True)
        # The terse form has no per-chapter table, so a slug appearing in it can
        # only have come from the named list. Asserting against the verbose form
        # was vacuous: the table lists every published chapter anyway.
        cls.terse = contract.render(cls.report, verbose=False)

    def test_the_report_names_the_next_act_not_just_counts(self):
        self.assertIn("Promotable:", self.text)
        for chapter in self.report.promotable:
            self.assertIn(chapter.slug, self.terse)

    def test_the_report_lists_the_debt_rule_by_rule(self):
        self.assertIn("Debt (advisory):", self.text)
        for chapter in self.report.debt:
            self.assertIn(chapter.slug, self.text)

    def test_the_report_states_that_the_contract_holds(self):
        self.assertIn("every enforced chapter is publishable", self.text)

    def test_the_report_is_stable_without_verbose(self):
        self.assertNotIn("legacy  contract", contract.render(self.report,
                                                            verbose=False))

    def test_the_crossref_report_resolves_every_reference(self):
        text = contract.render_crossrefs(self.report)
        self.assertIn("what-is-a-signal", text)
        self.assertIn("chapter 10 -> ", text)
        self.assertNotIn("(out of range)", text)

    def test_a_report_with_no_crossrefs_says_so(self):
        self.assertIn("(none)", contract.render_crossrefs(contract.Report()))


if __name__ == "__main__":
    unittest.main()
