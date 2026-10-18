# Evidence packs

One directory per chapter: `blog/evidence/<slug>/`, holding the record that the
chapter was *reviewed*, not merely written. It is what turns "I think this is
clear" into something a second party can check.

```
blog/evidence/<slug>/
  student-engineer.md   a cold read by the maths-rusty working engineer
  student-newcomer.md   a cold read by the numerate non-specialist
  qa-findings.md        every claim in the brief, checked, with a disposition
  gate.md               the verdict, from a checker that saw only the repo
```

Templates for all four are in
[`.dsh/skills/course-team/templates/`](../../.dsh/skills/course-team/templates/);
the role charters that produce them are in
[`.dsh/skills/course-team/references/roles.md`](../../.dsh/skills/course-team/references/roles.md).

## The one rule that makes this evidence rather than paperwork

Every file carries `Reviewed-hash: <sha1 of blog/posts/<slug>.md>`. The contract
check recomputes it, and a mismatch is `evidence-stale`:

```sh
sha1sum blog/posts/<slug>.md
```

**Evidence is valid for exactly one revision — the one it reviewed.** Edit a
sentence and all four files are stale, the check says so, and the cold read, the
QA pass and the gate run again. That is deliberate: it is the only mechanism
here that stops a review performed once from vouching for prose written
afterwards.

The independence rule matters as much as the hash. The Student roles read the
*rendered* page with the brief withheld, and the Checker gets the repository and
`references/gate-checks.md` and nothing else. An agent that has seen the brief
reads the page as the author intended rather than as written, and an agent that
knows what changed reads for confirmation.

## What is enforced, and what is not

Enforced, and failing a pull request: the four files exist; every file cites the
current revision; every stall has a tagged disposition with a reason; no QA
finding is left `[open]`; the gate verdict is `PASS`, names its checker and
records its commands; a transcript is not an empty file.

**Not** enforced, and not pretendable: whether a transcript is honest, whether a
disposition was earned, or whether the gate was run by a genuinely fresh
session. The 150-word floor blocks an empty file and nothing more. Evidence packs
are self-authored, so a single agent can rubber-stamp them — the only real
defences against that are the independence rule above and a reviewer who reads
the transcripts rather than counting them.

This directory is empty until the first chapter is delivered under the contract.
An existing chapter needs a brief in `blog/contracts/` and a pack here before its
line can be removed from `blog/contracts/legacy.txt`; `python3
tool/check_page_contract.py --report` prints which chapters are ready for that.
