# The voice

What this course sounds like, measured from `blog/posts/*.md` — 21 chapters,
51,656 whitespace-separated words (`wc -w`), 52,457 tokens matching `[\w'-]+`.
Every count below is a word-boundary match over that text, not an impression.
Reproduce any of them with:

```sh
python3 - <<'PY'
import pathlib, re
text = "\n".join(p.read_text(encoding="utf-8")
                 for p in sorted(pathlib.Path("blog/posts").glob("*.md")))
for token in ("you", "I", "we", "just", "simply", "obviously"):
    print(token, len(re.findall(rf"\b{token}\b", text, re.I)))
print("em dashes", text.count("\u2014"))
PY
```

## The measurements

| Token | Occurrences | Reading |
|---|---|---|
| `you` | 211 | direct address is the default |
| `I` | 23 | first person singular, sparingly, for positions |
| `we` | **0** | never. There is one author and one reader |
| `obviously`, `clearly`, `of course` | **0** | nothing is obvious to the reader |
| `it is important to note` | **0** | if it were not important it would not be here |
| `in today's …`, `delve`, `leverage` | **0** | no marketing register |
| exclamation marks | **0** | of 133 raw `!`, 116 are `![` figure embeds and 17 are LaTeX `\!` spacing |
| em dashes | 212 | the house punctuation for an aside |
| bold lead-ins | 129 paragraphs, 157 list items | a claim opens the paragraph, or the bullet |
| `just` | 11 | only ever in the sense of *merely*; never as a hedge |
| `simply` | 5 | the same |

`just` and `simply` are not banned. They are banned as hedges: a sentence where
*simply* is doing the work of an explanation is a sentence that explains nothing.

*(An earlier version of this table said 13 for `just` and 53,390 words. Those
were a substring count that included "justify" and "adjusts", and a total from a
different tokenisation. Both are corrected and now reproducible from the snippet
above — the numbers are a claim about the corpus and have to survive being
re-derived.)*

## The register

**Numbers, or an explicit admission.** Every quantity traces to a figure that
computes it. Where a figure models rather than measures, its caption says so.
Where a claim could not be verified, the chapter says that too, and accepts the
caveat rather than dropping the claim quietly.

**Positions are taken.** Twenty-three first-person singulars in 51,656 words,
and most of them are a judgement: *"My position: keep the bulk coefficients
static and track a residual."* The course is allowed to conclude. It is not
allowed to conclude without showing the arithmetic.

**Concrete before abstract.** A photodiode's load voltage, 128 GSa/s, 15.6 ps
per symbol, a 90 km span entered as 100. The abstraction arrives after the
instance that motivates it, not before.

**Honest about cost.** "The DSP team is buying nanoseconds with multiplies, and
nanoseconds are the harder currency." Complexity claims get multiplied out into
multiplies per symbol and watts.

## Rules for an Editor

1. **No `we`.** The author writes `I`; the reader is `you`. `we` is a
   conference talk, not this course.
2. **No exclamation marks, in any language.**
3. **Delete `obviously`, `clearly`, `of course`, `trivially`, `it is easy to
   see`.** If a step is easy, the sentence does not need the reassurance; if it
   is hard, the reassurance is a lie.
4. **`simply` and `just` only in the sense of *merely*.** If the word is
   standing in for an explanation, restore the explanation or cut the claim.
5. **A bold lead-in on a list item states the claim.** `- **Report the margin,
   not just the verdict.**` then the reason. Not `- **Margins:**` then a
   fragment.
6. **No marketing verbs** — leverage, unlock, empower, delve, dive into,
   seamless, robust (unless a measured property).
7. **Em dash for the aside**, sparingly enough that it still reads as one.
8. **Terminology is fixed by the course, not by the chapter.** Check the
   neighbouring chapters before introducing a synonym. If the course says
   *tap*, a chapter does not get to say *coefficient* for the same object.

## Rules for a Translator

The Vietnamese tree follows the English one and is not a paraphrase.

- **The plan may not drift.** `blog/vi/curriculum.json` must declare the same
  parts, chapters and page slugs, in the same order, as English. The build's
  `check_parity` enforces it. New chapter in English means an entry in every
  language on the same commit.
- **The prose may lag as far behind as it likes.** A chapter written in English
  and not yet translated is marked "English only" and links to the English page.
  It is never shown as "Planned", which would be a lie, and never hidden, which
  would be a dead end.
- **Figures are shared and stay English.** They are language-neutral SVGs in one
  `docs/blog/assets/` tree; labels inside them are not translated.
- **Technical terms stay English** in the prose, as they do in the English one.
- **Chrome is not prose.** No user-visible string belongs in `theme.py`,
  `site.py` or a template — it goes in `tool/blog/i18n.py`.
- **Translate a frozen revision.** A moving English draft wastes the
  translation, so the Editor refuses one.

## A worked contrast

The corpus's own version, from `convolution-and-lti.md`:

> Nothing fails; the eye simply closes a little and the centre tap sits off
> centre for the life of the link.

*Simply* here is doing real work — it is contrasting "nothing fails" with the
degradation, which is the point of the sentence. Compare the same fact written
as the rules forbid:

> Obviously, this is just a minor degradation, and it's important to note that
> the link will still work — we simply lose a little margin in today's
> high-speed systems!

Three banned words, a `we`, an exclamation mark, and no claim. The first
sentence is shorter and says more.
