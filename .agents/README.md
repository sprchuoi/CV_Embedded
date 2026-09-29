# Embedded AI Harness — bridged

The skills in `.agents/skills` are not stored here. They are a symlink to the
canonical clone:

    ../../Embedded-AI-Harness/.claude/skills
    (~/sandboxes/Embedded-AI-Harness/.claude/skills, two levels up from .agents/)

`.claude/skills` points back at `.agents/skills`, so DeepSeek Harness
(`.agents/skills`), Claude Code (`.claude/skills`) and the skill scripts that
hardcode a `.claude/skills/...` path all resolve to the same files.

To update the harness, pull the canonical clone — every bridged repo sees the
change at once. Nothing to re-copy.

To rebuild these links after a fresh clone, from `~/sandboxes`:

    ./eah-bridge.sh $(basename "$PWD")
