Reviewed-hash: 045938cfd54f07cf89d24c8bb71151f4ac8e226c
Persona: newcomer
Verdict: partial

## Reproduced

The page's own test is: rebuild a square out of sines in my head, and say why
the terms shrink, with the page closed. I can do that. I can also carry most of
the arithmetic, and I write it out here so a different reader can check me.

- **The square out of sines.** A ±1 square of period $T_0$ is
  $\frac{4}{\pi}\left[\sin(2\pi f_0t) + \tfrac13\sin(6\pi f_0t) +
  \tfrac15\sin(10\pi f_0t) + \cdots\right]$ — fundamental plus odd multiples
  only, the $n$th term carrying $4/(n\pi)$. The numbers are 1.2732, 0.4244,
  0.2546, 0.1819, 0.1415 for $n = 1, 3, 5, 7, 9$. I can check it at
  $t = T_0/4$: the odd terms are alternately $+1, -1, +1$, so the bracket is
  $1 - \tfrac13 + \tfrac15 - \cdots = \pi/4$ and the whole thing is 1, which is
  where the square is at that instant.
- **Why the terms shrink.** The $n$th harmonic completes $n$ cycles per period,
  so it has $n$ times as many lobes as the fundamental and each lobe is $1/n$ as
  wide; the area each lobe collects from a waveform that is ±1 scales with its
  width, hence $1/n$. The page's own check: multiply any $b_n$ by its own $n$
  and 1.2732 comes back.
- **Why only odd harmonics, two ways.** (i) An even harmonic repeats after half
  a period while the square flips sign, so the two half-sums cancel term by
  term. (ii) The square negates itself every half period,
  $x(t + T_0/2) = -x(t)$, and that relation deletes the even harmonics. Both
  arguments are on the page and I can give both.
- **The symmetry rules, with the page's own numbers.** Odd signal → sines only
  (the ±1 square: $b_1 = 1.2732$, $b_3 = 0.4244$, $b_5 = 0.2546$, everything
  else at the grid's floor). Even signal → cosines only (the square advanced a
  quarter period: $a_1 = 1.2732$, $a_3 = -0.4244$ — only the third flips sign —
  and the sine column at $9.5\times10^{-18}$). $|\sin|$, which repeats every
  half period, has a mean level $a_0 = 0.6366$ and even harmonics only,
  $a_2 = -0.4244$, $a_4 = -0.0849$. And the version textbooks call half-wave
  symmetry, $x(t + T_0/2) = -x(t)$, deletes the even ones instead — one sign
  apart, opposite conclusion.
- **What a coefficient measures.** Multiply the signal by one harmonic, average
  the product over one period, divide by the harmonic's own mean square — the
  area of a unit sinusoid squared over one period, $T_0/2 = 0.5$. The
  $2/T_0$ in front of the integral is that division upside down. Every other
  harmonic averages to zero against the one being measured, which is why
  orthogonality is what makes the measurement possible. The two numbers I can
  redo: $\int (\sin\cdot\sin) = 0.5000$ over one period, and the square against
  the third harmonic gives 0.2122, and $0.2122/0.5 = 0.4244 = b_3$.
- **Truncation.** Rise time times bandwidth is a constant: 0.4458 for an ideal
  band-limited (brick-wall, ringing) step, 0.35 for a monotone one-pole edge,
  and the two are 27% apart. The overshoot does not shrink with $K$: 8.95% of
  the jump of 2, which is 17.9% of the ±1 level, and those are the same peak
  with two denominators. The first ringing peak sits $0.5/B$ from the jump, and
  $K \approx 0.45/(t_r f_0)$ — 45 harmonics for a 1 GHz square with a 10 ps
  edge, 22 if the period halves.
- **The periodicity trap.** The coefficients are integrated over one period, so
  the object they rebuild is the infinite repetition of the record, not the
  record. Butt-joint a 1 s record of $e^{-t/0.2}$ and the seam invents a jump
  of 0.9933 (from 0.0067 up to 1.0). The $K = 101$ rebuild lands at 0.5011
  against a midpoint of 0.5034, and rings $-0.0817$ below the low side (8.90%
  of the jump) and $1.0652$ above the high side (6.56%), with 3.4 parts in a
  thousand as the worst interior error. That seam is leakage.
- **Taking the period away.** The invariant is $c_n T_0$: for a 0.25 s pulse at
  1 Hz it reads 0.22508, 0.22508, 0.22509 as $T_0$ goes 1, 2, 4 s, while the
  lines crowd (1, 0.5, 0.25 Hz apart) and the stems fall (0.22508, 0.11254,
  0.05627). The curve they stay on is the single pulse's transform,
  $X(f) = \tau\,\mathrm{sinc}(\tau f)$: peak $\tau$, first zero $1/\tau$,
  product exactly 1.
- **rect ↔ sinc.** Peak 0.25, 1, 2 and first zero 4, 1, 0.5 Hz for
  $\tau = 0.25, 1, 2$ s; energy 0.2500 computed in time and 0.2500 in frequency
  for the 0.25 s pulse, 90.3% of it inside the first lobe. A constant has a
  spike of unit area, not a curve. Ordinary transforms need
  $\int|x|\,\mathrm{d}t < \infty$, and finite area is sufficient where finite
  energy is not.
- **The scope recipe.** A 1 MHz square puts lines at 1, 3, 5, 7 MHz; the ratios
  $0.4244/1.2732$ and $0.2546/1.2732$ are $1/3$ and $1/5$, i.e. 9.5 dB and
  14 dB down. A 20 MHz limit keeps harmonics to the 19th, so $B = 19$ MHz, and
  the predicted 10–90% rise is 23.5 ns for a brick wall or 18.4 ns for a
  one-pole edge.

## Stalls

- **Opening paragraph**, "The sampling chapter convolved one with an impulse
  train to explain aliasing": "convolved" and "impulse train" are not explained
  anywhere on this page, and the paragraph refers to four earlier chapters
  (sampling, decibel, quantisation, the first) before it says what this chapter
  is for. I stopped to decide whether I was supposed to have read them.
- **Section 1**, "every number in this chapter is on that scale": I took that
  literally, and a thousand words later the worked example is a 1 GHz square
  and the callouts are in gigahertz. I stopped to work out which numbers the
  promise covered.
- **Section 1**, "it peaks a quarter period late": late with respect to what?
  The square has no peak for the sine to be late against. I had to supply "the
  jump at $t = 0$" myself; the sentence does not name it.
- **Section 1**, "The sine column is the square, and the cosine column is
  nothing": on first read it sounds like an equation between two columns of a
  table. It means the sine coefficients are what rebuild the square. I re-read
  the sentence.
- **Section 1**, the table under "It prints": the rows are $n =$ 1, 2, 3, 4, 5,
  7, 9. Six and eight are missing, though the table printed inside Figure 1 has
  every $n$ from 0 to 9. I stopped to decide whether the omitted rows meant
  something about those harmonics.
- **Section 1**, "two jumps each leave one sample unpaired, the residual is
  $4/N$": I can follow "the grid's floor" and I can see that $4/400{,}002 =
  1.0\times10^{-5}$, the number printed, but I cannot reproduce why the
  unpaired sample gives $4/N$.
- **Section 2**, "Four-two rather than three-three is the tangency ... the
  sequence runs $+,-,+,+,-,+$ rather than alternating": "three-three" names an
  expectation I was never given, and "touches zero there without crossing" is a
  claim about the product that I could only check by leaning on the figure. I
  did not get it from the sentence.
- **Section 2**, "The other convention writes $a_0/2$ in front of the constant
  and doubles the number": the page raises a second convention at the exact
  moment it defines its own, and I could not tell which one I am supposed to
  carry.
- **Section 4**, "the first chapter's $0.35/B$ is the rise time of a one-pole
  edge: a single real pole": "pole" is not a word I have. I got through on
  "monotone, no overshoot, the shape an RC or a first-order amplifier
  produces", which is three more things I am taking on trust.
- **Section 4**, "It is 9.12% at $K = 9$, 8.95% at $K = 101$": this is the same
  overshoot that Section 1 called "18.2% of the ±1 level at $K = 9$, 17.9% from
  $K = 101$ on". Two numbers for one phenomenon, a factor of two apart, and I
  had to hold both while reading a table of a third set of numbers.
- **Section 5**, "the midpoint of the two sides is 0.5034, so the series misses
  it by 0.0023 — inside the $3.4\times10^{-3}$ the interior fit already
  carries": I did not know why a series should meet a jump at its midpoint at
  all, and $3.4\times10^{-3}$ is used a sentence before the sentence that
  defines it.
- **Section 6**, "$c_n = \tfrac12(a_n - j b_n)$ ... $e^{j2\pi ft}$ and
  $e^{-j2\pi ft}$ are the two counter-rotating halves of a cosine": these are
  the chapter's first complex numbers, and "counter-rotating" assumes I picture
  a rotating point. I do not; I see an exponential.
- **Section 6 callout**, "a sum of density times spacing is a Riemann sum for an
  integral": the chapter's central transition — series to transform — is one
  clause, and it is the only step in the chapter I could not check against a
  picture.
- **Section 6**, "let the width go to zero: the pulse becomes $\delta(t)$":
  $\delta(t)$ arrives with no definition. The nearest thing on the page is
  "impulse train" in the opening paragraph, which was itself unexplained.
- **Section 6**, "the two classes are not nested: a sinc has finite energy and
  infinite area and needs the weaker mean-square sense, while $t^{-1/2}$ on
  $(0,1]$ has finite area and infinite energy": "classes", "nested",
  "mean-square sense" — this is the hardest sentence in the chapter and I left
  it without knowing which class any signal I care about is in.
- **Optical callout**, "A 53 GBd PAM4 lane is specified at 26.6 GHz ...": PAM4,
  GBd, lane, Mach-Zehnder, hybrid, mask, eye. I could not follow the second
  paragraph at all, and it is the only place on the page addressed to the work
  I do.
- **Figures 4 and 5**, the tables printed inside the plots: at the page's column
  width the four $K$ rows in Figure 4 are small enough that I checked 0.4454
  against 0.4414 by eye twice and then against the prose table rather than
  trusting the figure. A human should confirm this one on a real screen; I
  cannot see the page as a browser draws it.

## Dispositions

- [accepted] Chapter references: this is one chapter of a numbered course (it
  names chapter 6 and chapter 8), and convolution and the impulse belong to the
  sampling chapter that owns them. Redefining them here would be the wrong fix.
  The cost is real for a reader who lands on this page first, and the first
  paragraph spends most of its length on chapters I do not have open.
- [rejected] On the second read the sentence sets the unit for the chapter's own
  numbers, and every later example arrives with its own period stated in the
  sentence that introduces it. I had read a local convention as a promise about
  every figure.
- [accepted] The referent is the jump at $t = 0$, which is the only event in the
  square and is on the figure the sentence is describing; it costs a second,
  not a re-read of the section.
- [accepted] The next sentence disambiguates it immediately ("Every $b_n$ is
  the fundamental's value divided by n"), and the sentence is a heading in
  miniature rather than a claim.
- [accepted] The table's job is two even rows at exactly zero and the odd
  ladder; six and eight would add two more zeros and no information, and the
  figure keeps every row for anyone who wants to check. I stopped because the
  rhythm broke, not because I was missing a fact.
- [accepted] A numerical floor of $1.0\times10^{-5}$ is not load-bearing for
  anything the chapter asks me to do, and the page is explicit that it is the
  grid rather than a physical number.
- [accepted] I did resolve it from the figure, and the sentence is the only
  place the count is named; the picture cannot say "+,-,+,+,-,+" on its own.
  It is the densest paragraph in the chapter and it is dense rather than wrong.
- [accepted] A reader will meet the other convention within a page of any
  handbook, and the page prints both numbers (0.6366 and 1.2732) so the two are
  tied together. Better here than in the wild.
- [accepted] The gloss "monotone, no overshoot, the shape an RC or a first-order
  amplifier produces" is the operational content, and the chapter is not the
  place to teach what a pole is.
- [accepted] Both percentages are in circulation in real specifications, the
  section prints both columns side by side, and the paragraph exists precisely
  to make the reader hold both. The distance between the two sightings is the
  chapter's own structure — the jump is drawn in Section 1 and measured in
  Section 4 — and a note in Section 1 would be the only thing that shortens it.
- [accepted] The figure prints the series value and the midpoint side by side,
  so the midpoint is checked rather than asserted; the $3.4\times10^{-3}$ one
  sentence early costs a re-read and nothing more.
- [rejected] On the second read the identity
  $\cos = \tfrac12(e^{j2\pi ft} + e^{-j2\pi ft})$ is written out in full and the
  stem symmetry follows from $c_{-n} = \overline{c_n}$ alone; the rotating
  picture is decoration, not a step. My stall was thinking it was load-bearing.
- [accepted] It really is a calculus step and the callout says so ("a reading of
  the picture, not a separate act of faith") rather than pretending the figure
  proves it. The honesty is why I can accept it and still not be able to redo
  it.
- [accepted] The impulse is a chapter-2 object — the opening paragraph names the
  impulse train — and $\delta(t)$ is its notation. This page is not where it
  should be defined.
- [accepted] The chapter needs the boundary stated somewhere or "a constant has
  a spectrum that is a spike" is unearned, and the two examples are the shortest
  honest version of it. The cost is that the vocabulary is three terms deep in
  one sentence.
- [accepted] The optical chapters own PAM4, GBd and the Mach-Zehnder, and this
  callout is a forward pointer for a reader who will meet them. See Notes for
  what that costs the transfer.
- [accepted] Every number in those printed tables is repeated in the prose table
  or the takeaway list, so no claim in the chapter depends on reading the small
  type. The figure is a convenience here, not the only copy.

## Notes

**The sentence this role is for:** I could follow the Riemann-sum step while I
was reading it and I cannot reproduce it afterwards. The same is true of the
finite-area paragraph: while reading I nodded, and with the page closed I can
state its conclusion and not give its argument. Everything up to and including
the truncation section, I can rebuild; the two sections after it I can
paraphrase.

**What the page actually delivered me.** The design target — a square out of
sines, and why the terms shrink — is met, and met with a picture rather than a
quotation. The secondary target — is the transfer something I could use — is
only half met: the scope recipe is the one thing I could do on Monday morning,
and the optical callout, which is the page's only address to my own work, is
written for someone who already has the optical vocabulary. A product manager
would close this page able to explain Gibbs to a colleague and unable to say
what a lane is.

**A warning about the numbers.** There are so many of them, printed to six and
seven figures and mutually consistent, that they did my trusting for me. I did
not check a single one against a figure until this transcript asked me to. The
authority of the chapter is carried by decimal places; that is a compliment and
also the thing that would hide an error from a reader like me.

**On the shape of the difficulty.** The page gets harder as it goes: Sections 1
to 3 are pictures with numbers attached, Section 4 is a table, and Sections 5
and 6 introduce complex numbers, the delta, and two classes of functions in the
last thousand words. A reader whose attention is finite — mine is — spends it
in the right place and runs out exactly where the chapter's title promises the
payoff. I would have read a one-paragraph summary of Section 6 twice, and I read
the tangency paragraph in Section 2 three times.
