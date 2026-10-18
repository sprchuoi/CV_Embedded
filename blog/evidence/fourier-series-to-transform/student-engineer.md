Reviewed-hash: 045938cfd54f07cf89d24c8bb71151f4ac8e226c
Persona: engineer
Verdict: understood

## Reproduced

With the page closed, I can state and defend:

- The ±1 square at `T0 = 1` s is sines only, `4/(nπ)`: 1.2732, 0.4244, 0.2546, 0.1819, and the fundamental is larger than the square it builds. I re-measured this myself by rectangle-integrating the sampled waveform at `N = 400,002` and got 1.273239545, 0.424413181, 0.254647909, 0.141471060 for `n = 1, 3, 5, 9`, with the odd `a_n` at 1.000e-5 and the even ones at 5e-17. I also reproduced the exact rectangle-sum identity `(4/N)cot(πn/N)` by the geometric sum, and `(4/N)cot(π·9/N) − 4/(9π) = −2.36e-10`.
- The projection recipe: multiply by the harmonic, average over a period, divide by the harmonic's own mean square `T0/2`; the `2/T0` in front of the integral is that division; `a0` is the mean with no factor of 2, which is why the rectified sine prints 0.6366 and not 1.2732.
- The four symmetry sentences, and that `|sin|` has `a0 = 0.6366`, `a2 = -0.4244`, `a4 = -0.0849` with odd coefficients at 7e-18; that the quarter-advanced square moves the same amplitudes into the cosine column with `a3 = -0.4244` (I re-derived `a3 = (2/3π)(sin(3π/2) − sin(9π/2)) = -4/(3π)`).
- Truncation. `t_r·B = 0.446` for a brick wall (I solved `Si(±1.4006) = ±1.2566` and got 0.44582), 0.4007 / 0.4414 / 0.4454 at `K = 9 / 101 / 1001`, overshoot 9.12% → 8.95% of a jump of 2, i.e. 17.9% of ±1, peak 1.1790 at `T0/2K`; and 0.35/B for a one-pole edge, which I checked from `1 − e^{-t/τ}` (2.197τ × 1/2π). The 27% between the constants is real.
- The periodic-extension argument and its five numbers, all of which I recomputed from the 400,002-sample record at `K = 101`: seam 0.9933, series 0.5011 against a midpoint of 0.5034, undershoot −0.0817 (0.0884 below, 8.90%), overshoot 1.0652 (0.0652 above, 6.56%), interior error 3.37e-3. The two percentages differ because the high side is a steep decay and the low side a flat tail.
- `c_n = ½(a_n − j b_n)`; `c_n = X(nf0)/T0`, so the lines crowd and shrink by `1/T0` while `c_n·T0` stays at 0.22508 (0.11254 at `T0 = 2`, 0.05627 at `T0 = 4`); rect ↔ `τ sinc(τf)`, peak `τ`, first zero `1/τ`, product 1, energy 0.2500 both ways with 90.3% in the first lobe; and why an ordinary transform needs finite area and not finite energy, with the sinc and `t^{-1/2}` counter-examples.
- The two calls I would now make on a scope: a bandwidth gives `K = 0.446/(t_r f0)` (a 1 GHz square with 10 ps rise needs K ≈ 45), and an overshoot spec is a mask line, not a bandwidth shortfall.

## Stalls

- §1, "At `K = 1` there is no fringe at all, because the sum is a single sine and it peaks 27% above the square." 27% is the largest overshoot in the chapter; the sentence calls it no fringe. I stopped and re-read the paragraph twice.
- §1, "two jumps each leave one sample unpaired, the residual is `4/N`". The number is right; the mechanism as written is not what produces it. With samples at `j/N` and the first half +1, the jump at `t = 0` falls *between* samples `j = N−1` and `j = 0`; only the `T0/2` jump lands on a sample (`j = N/2`), and that one contested sample carries the whole 4/N — set it to +1 and the 4/N moves into the even column. I could not get there from "two jumps".
- §4, the ideal band-limited step's 0.4458 is printed with no working. I tried to re-derive it from memory and got 0.486, then found my Si table was wrong: `Si(1.4006) = 1.2566`, not `Si(1.527)`.
- §4, "The rise time is set by the bandwidth, not by the shape", four paragraphs before "Same `1/B` law, different constant" and "the 27% between them": the word "shape" is doing two jobs.
- §4, "the 27% between them is the difference between a rise time you can meet and one you cannot": which constant is the meetable one is not stated. `0.446/B` is the slower (easier) number; `0.35/B` is the faster one.
- §6, "a coefficient is the transform multiplied by the line spacing, `c_n = X(nf0)/T0`": the load-bearing step of the whole transition, asserted. The missing line is that the integral over one period of the train equals the integral over the single pulse, which is `X`.
- §6, Figure 6: the drawn envelope never crosses zero, but `X(f) = 0.25 sinc(0.25f)` is negative beyond 4 Hz. At 4.5 Hz the curve reads +0.024 where the formula gives −0.0271; at 5.5 Hz +0.052 against −0.0535; the rings sit at the magnitudes. The axis is labelled "rings `X(f)`" and the text says "a ring is `c_nT0`".
- §6, "every number in this chapter is on that scale" (`T0 = 1` s): the section I had just read uses `T0 = 1, 2` and `4` s.

## Dispositions

- [rejected] "no fringe at all": "fringe" was defined two sentences earlier as the ringing at each jump, not as any overshoot. At `K = 1` the error is global rather than local, and the 27% is printed in the same clause, so I was not misled about the size — I misread the word.
- [accepted] "the residual is `4/N`": the measured value is correct and the point (the grid's floor is not physics) survives it; the exact account is a quadrature term — `(4/N)·Σ_{j<N/2} cos(2πnj/N) = 4/N` for odd `n` — which the sentence gestures at rather than derives, and nothing downstream depends on the factor. The count of unpaired samples is wrong; the number is not.
- [accepted] 0.4458 with no working: it is an Si evaluation, a page of its own, and the middle panel measures the convergence to it rather than asserting it. Leaving it as a printed constant is defensible; it is also the one number in the chapter a reader cannot check in place.
- [rejected] "not by the shape": the first "shape" is the waveform's (a square rather than anything else) and the second is the filter's edge kind. The next paragraph says "Same `1/B` law, different constant" and I read both uses as one word.
- [accepted] "a rise time you can meet and one you cannot": the try-it callout assigns each constant to a limiter — 0.446 to a brick wall, 0.35 to a one-pole — and tells you to measure which you have. The flourish is resolved, though eight paragraphs later.
- [accepted] `c_n = X(nf0)/T0` asserted: it is one line from the definition already given (the train's integral over one period is one pulse's integral, which is `X`), and Figure 6's rings test it at three periods.
- [accepted] Figure 6's sign: the sign carries no argument here — the section is about crowd and shrink, and a stem height can only be compared with a magnitude — so the figure is a magnitude plot on an axis labelled `X(f)`. Every value I read off it agrees with `|X|` and none with `X`. The stall stands: a reader who checks the page's own formula at 5 Hz finds a sign the figure does not show.
- [rejected] "every number on that scale": I read "scale" as "`T0 = 1` for everything"; the figure in that section labels `T0 = 1, 2, 4` s and the text gives each. "Scale" means seconds and hertz, not one period.

## Notes

- The arithmetic is the strongest part of the page. Every number I checked — about thirty — reproduced, two of them (0.4414, 0.5002) to my own grid resolution rather than to the last digit: `4/π`, the coefficient table, 81.06 / 90.06 / 95.96 / 99.59%, 0.4007 / 0.4414 / 0.4454 / 0.4458, 9.12 / 8.95%, 1.1790, 0.9933 / 0.5011 / 0.5034 / −0.0817 / 1.0652 / 3.4e-3, 0.22508 / 0.11254 / 0.05627, 90.3%, 23.5 / 18.4 ns, 14 ps / 15.6 ps, 9.54 / 13.98 dB. My stalls are not numerical. They are figure labelling and compression.
- The sentence this transcript exists for: I could follow the 4/N paragraph while reading and could not reproduce it afterwards. Same shape for 0.4458, except that one I did reproduce once I trusted my own arithmetic over my memory of a special function.
- "Understood" is the honest label because every stated outcome survived the closed-page test. If the verdict were about the page's *routes* rather than its outcomes, it would be partial: two constants are used, not derived, and one of them (4/N) is explained by a mechanism I do not believe.
- Figure 1's caption says K = 1, 3, 9 and 99; §4 measures K = 9, 101, 1001. Both are true of their own figure, and the two 17.9% readings are both the limit, but a reader has to check that the two sections are not disagreeing about the same number.
- The try-it spreadsheet line `sin(2πt) + sin(6πt)/3 + sin(10πt)/5` is a square of amplitude `π/4 = 0.785`, not ±1. The callout only asks for ratios and the ratios are right (1/3, 1/5), but a reader who compares the spreadsheet's peak with the chapter's 1.2732 will be a factor 4/π out and will not know why.
- One claim I would not defend as written: the optical callout's "a linear equaliser has no coefficient for what the drift lets through". An equaliser has a coefficient at every frequency the drift produces; what it cannot do is separate drift-induced distortion from the data. The paragraph's point survives, the sentence overstates it.
- I could not check rendering, and I am not pretending to. I rasterised the seven committed SVGs at 2× and read them; whether `$…$` renders rather than showing as literal text, and whether the figures are legible at the page's column width, needs a human with a browser.
