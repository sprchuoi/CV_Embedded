Slug: <slug>
Level: <level exactly as the curriculum declares it>
Prerequisites: <comma-separated earlier chapter slugs, or: none>

<!--
Copy to blog/contracts/<slug>.md and fill in. This file is written BEFORE the
prose and is checked on its own: `python3 tool/check_page_contract.py` validates
it from the moment it exists, and a briefed chapter with no prose is "in flight"
rather than a finding.

The header lines must come before the first `##`. Delete these comments.
-->

# <The chapter title, as the curriculum declares it>

One paragraph of design intent: what the reader arrives believing, and what this
chapter is for. Not a summary of the chapter — the reason it exists. The Curator
writes this.

## Outcomes

What the reader can **do** afterwards, not what they will "understand". Each one
must be attemptable by a Student with the page closed.

- <Verb> the <thing> and say which term dominates.
- Estimate the <number> for a link you have, from first principles.
- Explain to a colleague why the obvious answer is wrong.

## Claims to verify

The specific, checkable claims QA will audit. A claim that cannot be checked
from this repository does not belong here — it belongs in the prose with its
uncertainty stated.

- <The claim> — checkable in figure <n> / <the script that computes it>.
- <The claim> — checkable in figure <n>.

## Transfer

Where this touches work, and where it touches an ordinary week.

Work: <the block, standard or budget line where this is a real decision>
Life: <something the reader owns or does that this explains>

## Comprehension plan

What each persona is expected to struggle with, and what that would tell you.
Name both.

- engineer: <the step that must be derivable, not asserted>
- newcomer: <the sentence or figure the opening must earn>
