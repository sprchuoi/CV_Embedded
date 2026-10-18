Reviewed-hash: 045938cfd54f07cf89d24c8bb71151f4ac8e226c

## Findings

- [fixed] **Claim 1 — the square is odd-harmonic and falls as 1/n.** `build_environment/.venv/bin/python tool/build_blog_assets.py --only plots` prints `n = 1: a = +1.0000e-05 b = +1.273240`, `n = 2: a = +0.0000e+00 b = -0.000000`, `n = 3: a = +1.0000e-05 b = +0.424413`, `n = 5: b = +0.254648`, `n = 7: b = +0.181891`, `n = 9: b = +0.141471`, with every even row zero; the figure's own in-figure table (n = 0 … 9) and the page's seven rows (n = 1, 2, 3, 4, 5, 7, 9) carry the same digits at the same precision. Hand check: 4/π = 1.2732395, 4/(3π) = 0.4244132, 4/(5π) = 0.2546479, 4/(7π) = 0.1818914, 4/(9π) = 0.1414711; every odd a_n = 4/N = 9.99995×10⁻⁶ (the module returns 9.999950000252171e-06) and the even a_n are exactly `0.0`, the even b_n exactly `-0.0`. The brief's "every cosine coefficient at the grid's own floor (10⁻⁵ at the two jumps)" is looser than the figure — only the odd a_n are at 10⁻⁵, the even ones are exactly zero — and the page says exactly that. **The page states the figure's measurement.**

- [fixed] **Claim 2 — a coefficient is a measurement, not a definition.** stdout: `fundamental × fundamental: signed area +5.000000e-01`, `fundamental × third harmonic: signed area +0.000000e+00`, `square × third harmonic: signed area +2.122066e-01`; `area/(T0/2) = b_3 +0.424413, fundamental against itself +1.000000`; lobes `['+0.051687']×4` positive and `['-0.103374']×2` negative; `['+0.106103']×4` and `['-0.106103']×2`. The page's 0.5000, "exactly zero rather than nearly so", 0.2122, 0.4244, the 4×0.0517 = 2×0.1034 cancellation, the six equal 0.1061 lobes, the 4-positive/2-negative count and the 0.5 divisor all match. The in-figure box prints `+0.0e+00`, not a small residual. Hand check: ∫₀¹ sin²(2πt) dt = 0.5; ∫₀¹ sin(2πt)sin(6πt) dt = 0; ∫₀¹ s(t)sin(6πt) dt = 2/(3π) = 0.212207; 0.212207/0.5 = 0.424413; the positive lobe is 1/(6π)×... = 0.051687 and the negative 0.103374 = 2×0.051687. The brief's "−9×10⁻¹⁶" is stale: the sampled product is exactly orthogonal on this grid and the figure returns exactly +0.0e+00, which is what the page now states. **The page states the figure's measurement, not the brief's stale value.**

- [fixed] **Claim 3 — symmetry deletes harmonics without arithmetic.** stdout: the odd square prints `b = [0, +1.27, 0, +4.24e-01, 0, +2.55e-01, 0, +1.82e-01, 0]`; the quarter-shifted square prints `a = [0, +1.27, 0, -4.24e-01, 0, +2.55e-01, 0, -1.82e-01, 0]` with `b` entries −1.41e-18 … −9.49e-18 (max |b| = 9.49e-18, and the figure's floor line reads `every $b_n$ ≤ 9.5e-18`); the rectified sine prints `a0 = +6.37e-01`, `a2 = -4.24e-01`, `a4 = -8.49e-02`, max odd |a| = 7.14e-18 (figure floor line `every odd $a_n$ ≤ 7.1e-18`). The page's +1.2732, −0.4244, 9.5×10⁻¹⁸, 0.6366, −0.4244, −0.0849 and 7×10⁻¹⁸ are those values at the page's precision. The brief's "3×10⁻¹⁶" and "10⁻¹⁵" are stale by two orders of magnitude; the page prints the figure's 9.5e-18 and 7e-18. Hand check: advancing the square by T₀/4 multiplies each coefficient by sin(πn/2), so a₁ = +b₁ = 4/π, a₃ = −b₃ = −4/(3π) = −0.4244132, a₅ = +b₅; the rectified sine's a₀ = 2/π = 0.6366198, a₂ = −4/(3π) = −0.4244132, a₄ = −4/(15π) = −0.0848826. Re-measured on the figure's own grid: a₁ − b₁ = 3.9×10⁻¹¹, a₃ + b₃ = −1.2×10⁻¹⁰, i.e. the shift's amplitudes equal the sine column's to the quadrature floor the page names in section 1, and the figure prints both as 1.2732 / 0.4244. **The page states the figure's measurement, not the brief's stale values.**

- [fixed] **Claim 4 — truncation buys a slope, never a corner.** stdout: `K = 9: tr*B = 0.4007, overshoot 9.116% of the step of 2 = 18.233% of the +/-1 level, first peak at 0.4500/B`; `K = 101: 0.4414, 8.951%, 17.901%, 0.4951/B`; `K = 1001: 0.4454, 8.949%, 17.897%, 0.5002/B`; `ideal band-limited step: 0.4458, 8.949%, 17.898%`; `the first chapter's one-pole edge is 0.350 ... 1.274x the ringing edge's constant`. The page's table (K, t_r·B, % of the jump of 2, % of ±1), its 9.12/8.95/8.95/8.95% and 18.23/17.90/17.90/17.90% and its 0.4007/0.4414/0.4454/0.4458 are the figure's numbers at its printed precision, as are the in-figure table and the two subtitles. Hand checks: (0.4458−0.4007)/0.4007 = 11.26% ("an 11% variation"); 0.446/0.350 = 1.2743 ("27%"); 1 + 2×0.08949 = 1.17898 → "1.1790"; T₀/2K = 0.5/B, and the figure's "peak at" column is in units of 1/B; 0.446/(10 ps × 1 GHz) = 44.6 → 45, 0.446/(10 ps × 2 GHz) = 22.3 → 22 (the page's exact constant is 0.446; the displayed 0.45 is marked ≈). The brief's "0.400/0.442/0.445" is the same sequence to three decimals, and its "8.9% of the step" is resolved the way the brief's last sentence asked: the page labels both denominators, 8.95% of the jump of 2 and 17.9% of the ±1 level, and the figure prints both columns. **The page states the figure's measurement.**

- [fixed] **Claim 5 — the series does not know the record, only its repetition.** stdout: `seam jump = 0.9933; midpoint of the two sides = 0.5034`; `K = 101 series at the seam = 0.5011`; `rings to -0.0817 (8.90% of the jump) and 1.0652 (6.56% of the jump)`; `interior |t-seam| > 0.15: max error 3.4e-03`. The page's 0.9933, 0.5011, 0.5034, 0.0023, −0.0817/0.0884/8.90%, 1.0652/0.0652/6.56%, 3.4×10⁻³ and "middle 70%" all match, as do the in-figure rows. Hand checks: 1 − e⁻⁵ = 0.9932621; (1 + e⁻⁵)/2 = 0.5033690; 0.5034 − 0.5011 = 0.0023; 0.0884/0.9933 = 8.90%; 0.0652/0.9933 = 6.56%; [0.15, 0.85] is 70% of the record. The brief's "0.5004 — the midpoint of the two sides" is stale twice: the figure returns 0.5011 for the series and 0.5034 for the midpoint; the page states both correctly. **The page states the figure's measurement, not the brief's stale value.**

- [fixed] **Claim 6 — the lines crowd and shrink while the envelope stays.** stdout: `T0 = 1 s: f0 = 1 Hz, c_n at 1 Hz = 0.22508, c_n*T0 = 0.22508`; `T0 = 2 s: f0 = 0.5 Hz, c_n at 1 Hz = 0.11254, c_n*T0 = 0.22508`; `T0 = 4 s: f0 = 0.25 Hz, c_n at 1 Hz = 0.05627, c_n*T0 = 0.22509`; `X(1 Hz) = 0.22508; spread of c_n*T0 = 1.1e-05`. The page's three c_n values, the 1/0.5/0.25 Hz spacings, the three products, "the spread is 1.1×10⁻⁵" and the takeaway's 0.2251 all match, as do the in-figure footnotes (`$c_n$ at 1 Hz = … — the stem`, `$c_n T_0$ = … — the ring, on $X(f)$`). Hand check: 0.25·sinc(0.25) = 0.2250791; /2 = 0.1125395; /4 = 0.0562698. The figure draws the same X(f) = τ sinc(τf) in all three panels and plots the rings at |c_n|T₀, so the page's "every one of them lies on X(f)" is what the figure draws. **The page states the figure's measurement.**

- [fixed] **Claim 7 — power is the sum of the lines.** stdout: `square mean square = 1.0000`; `K = 1: mean square 0.8106 = 81.06%`; `K = 3: 0.9006 = 90.06%`; `K = 9: 0.9596 = 95.96%`; `K = 99: 0.9959 = 99.59%`. The page's four percentages, "4% still missing at K = 9" (100 − 95.96 = 4.04) and the term counts (K = 3 two terms, K = 9 five, K = 99 fifty) all match. Hand check: ½Σb_n² over the odd harmonics gives 0.8105695, 0.9006327, 0.9596048, 0.9959473 — the same four numbers by the other route, so the page's ½Σb_n² claim checks independently of the figure's time-domain route. **The page states the figure's measurement.**

- [fixed] **Claim 8 — widening the pulse trades height for width and nothing else.** stdout: `tau = 0.25 s: X(0) = 0.2500, first zero at 4 Hz, X(0)*zero = 1.0000`; `tau = 1 s: 1.0000, 1 Hz, 1.0000`; `tau = 2 s: 2.0000, 0.5 Hz, 1.0000`; `energy both books (tau = 0.25 s): time 0.2500, frequency 0.2500, 90.28% inside |f| < 4 Hz`. The page's 0.25/1/2, 4/1/0.5 Hz, product 1, 0.2500 both ways and 90.3% match. Hand checks: 2∫₀¹ sinc²(u) du = 0.902823 → 90.28%; ∫|X|² df = τ = 0.25; the first lobe is |f| < 1/τ = 4 Hz. The figure's bottom-right panel draws the unit-area pulses flattening to a δ(f) arrow, so the page's "which is why the figure draws an arrow" is what the figure does. **The page states the figure's measurement.**

- [fixed] **The `::: try` callout is arithmetically correct and self-consistent.** Item 2 defines B = K/T₀ with a 20 MHz brick wall over a 1 MHz fundamental: the 19th harmonic at 19 MHz passes, the 21st at 21 MHz does not, so K = 19 and B = 19 × 1 MHz. Item 3 then computes at 19 MHz, not 20: 0.446/19 MHz = 23.47 ns → "≈ 23.5 ns", 0.35/19 MHz = 18.42 ns → "18.4 ns". Item 1: 0.4244/1.2732 = 1/3 and 0.2546/1.2732 = 1/5; 20log₁₀(1/3) = −9.54 dB ("9.5 dB") and 20log₁₀(1/5) = −13.98 dB ("14 dB"). The last paragraph's "27% apart" is 0.446/0.350 = 1.274, and the callout's 0.446/19 MHz is the section's own K = 0.446/(t_r f₀) inverted at K = 19. The page establishes what the exercise assumes: B = K/T₀ and the 0.446/0.350 comparison in section 4, 0.35/B in `what-is-a-signal.md:73`, the 1/n ladder in section 1, decibels in chapter 4. The spreadsheet sum sin(2πt) + sin(6πt)/3 + sin(10πt)/5 with t in microseconds gives 1, 3 and 5 MHz and is the square's series scaled by π/4; it claims no amplitude. **No defect.**

- [fixed] **The `::: optical` callout's numbers exist in the repository and none contradicts a published chapter.** `blog/posts/serdes-channels-and-the-link-budget.md:14` — "53 GBd PAM4 has its Nyquist frequency at 26.6 GHz"; `:19`, `:79`, `:88` use the same pair. `blog/posts/coherent-optical-dsp-pipeline.md:79` — "the 32 GHz Nyquist band"; `blog/posts/chromatic-dispersion-and-the-fde.md:15` — "the 32 GHz band"; `coherent-optical-dsp-pipeline.md:55` and `quantization-and-enob.md:173,179` also carry 32 GHz. `coherent-optical-dsp-pipeline.md:177` and `fir-filter-design.md:155` — "a symbol lasts 15.6 ps" at 64 GBd. The exact pair 53.125 GBd / 26.5625 GHz is in the brief (`blog/contracts/fourier-series-to-transform.md:61`); no published chapter uses it, and none contradicts it — the published 53 GBd / 26.6 GHz pair is the rounded name the page says it is. Arithmetic: 53.125/2 = 26.5625; 26.6/53 = 0.5019 ("about half"); 64/2 = 32 exactly ("exactly half on the 64 GBd lane"); 0.446/32 GHz = 13.94 ps → "≈ 14 ps", 89.2% of 15.625 ps ("nearly the whole 15.6 ps symbol"); 0.446/0.35 = 1.274 → "27% apart". The "one-pole" label for chapter 1's 0.35/B is not used in chapter 1 (which says only "about 0.35/B"), but 0.35/B is the single-pole 10–90% value (ln 9 / 2π = 0.3497/B), so the label describes the constant rather than contradicting the chapter. **No defect.**

- [open] **The recipe "average over a period, divide by the harmonic's own area T₀/2" is the chapter's T₀ = 1 in disguise, and the takeaway states it with the symbol T₀.** Section 2 says (line 53) "multiply by the harmonic, average the product over a period, divide by the harmonic's own mean square — the area of the harmonic against itself over one period, $T_0/2 = 0.5$", and the takeaway (line 165) repeats "Multiply by the harmonic, average over a period, divide by the harmonic's own area $T_0/2$. The $2/T_0$ in front of the integral is that division". The harmonic's **mean square** is 1/2, independent of the period; the harmonic's **area** over one period is T₀/2. They are both 0.5 only because this chapter fixes T₀ = 1 s (line 11), so every printed number in the chapter stands and the formula $a_n = (2/T_0)\int$ on line 55 is correct. But the takeaway performs *mean ÷ area*: (∫/T₀)/(T₀/2) = 2∫/T₀², which equals the coefficient only at T₀ = 1 and is low by a factor T₀ for any other period — while its own next clause ("the 2/T₀ … is that division") is correct only if the division acts on the integral, i.e. area ÷ area. Measured at T₀ = 2 s on a signal x = sin(2πt/T₀), where the coefficient must be 1: the area is 1.0000, the mean square 0.5000, the area T₀/2 = 1.0; the page's "average ÷ T₀/2" returns 0.5000, "area ÷ T₀/2" returns 1.0000, "average ÷ mean square" returns 1.0000, and (2/T₀)×area returns 1.0000. This matters because the takeaway is the section for carrying the recipe forward, and the `::: try` callout sets its square at 1 MHz (T₀ = 1 µs) — a period at which the stated recipe returns a coefficient 10⁶ too small. **This blocks publication.** The fix is a wording change in the author's hands: either "divide the product's integral by the harmonic's own area T₀/2", or "average over a period, divide by the harmonic's own mean square 1/2" — not the mixture.

- [fixed] **Another chapter's numeric reference, re-checked after the chapter-5 insertion.** `blog/posts/what-is-a-signal.md:205` now reads "Untangling the two is chapters 35 and 37"; `--crossrefs` resolves 35 → Chromatic Dispersion and the Frequency-Domain Equaliser and 37 → Carrier Phase Estimation, both correct for the dispersion/phase coupling the sentence describes. The old "chapters 29 to 32" (Reading an Eye Diagram, BERT, the FFT in compliance, Compliance Test in Practice) is gone from the prose and from the rendered `docs/blog/what-is-a-signal.html`. Note for the next renumbering review: the table also prints `chapter 36 -> Polarization Demultiplexing with CMA`, which the sentence does not name — `CHAPTER_REF_RE` (`tool/blog/contract.py:94`) treats "and" as a range word and expands "35 and 37" to 35–37. That is the checker's reading, not a reference in the prose, and it is not a page defect. The page's own three references resolve as chapter 6 ×2 → The DFT, Without Magic and chapter 8 ×1 → Windows, Leakage and Resolution.

- [withdrawn] **Nothing found** in the link, cross-reference, EN/VI parity, terminology and figure-caption checks at this revision. All seven `assets/plots/fourier-*.svg` references resolve to files under `docs/blog/assets/plots/`; the rendered `docs/blog/fourier-series-to-transform.html` (built 18:57, after the post's 18:46) carries all seven `src=` paths and the current text (`0.5011`, `0.22509`, `53.125`, `0.446/19`, `23.5`, `1.1790`), and every `href`/`src` in it resolves (`decibels-and-dynamic-range.html`, `the-fft.html`, `index.html`, `vision.html`, `vi/index.html`, `../index.html`, `assets/blog.css`, `assets/blog.js`, `../favicon.ico`). `python3 tool/check_page_contract.py --crossrefs` resolves the page's three numeric references as above; its exit 1 is the evidence lifecycle, not a cross-reference. The EN/VI curricula agree on the 2 page slugs, the 10 part ids, the 48 article slugs in the same order and the same per-part counts, and `python3 tool/build_blog.py --check` (which runs `check_parity`) exits 0. Terminology matches the neighbouring chapters: 0.35/B at `what-is-a-signal.md:73`; "Gibbs" and the ~9% overshoot at `fir-filter-design.md:78,182`; "leakage, chapter 8" and the 100.5-period example at `what-is-a-signal.md:166`; 26.6 GHz/53 GBd at `serdes-channels-and-the-link-budget.md:14`; 32 GHz/64 GBd/15.6 ps at `coherent-optical-dsp-pipeline.md:79,177`; energy signal/power signal as at `what-is-a-signal.md:135,150`. Every caption and in-figure annotation was checked against the script and the drawn data — the coefficient tables, the 2 humps of 0.2500, the 4×0.0517/2×0.1034 cancellation (the machine annotation reads "2 negative of -0.1034", a double negative, not a contradiction), the six 0.1061 lobes, the 10%/90% levels and t_r bracket drawn on the K = 9 edge, the two overshoot columns, the five seam rows, the two axis quantities (stems |c_n| and rings c_nT₀, "four times above it at T₀ = 4 s"), the widths/zeros table and the unit-area spike — and no figure contradicts its caption. The page's "the five measured numbers" is the figure's five-row bottom table. One loose clause that misstates no printed number, recorded for the Editor and not a blocker: "four orders below the cosine column's 1.0×10⁻⁵" compares an absolute residual (2.4×10⁻¹⁰) with an absolute floor, which is 4.6 orders, not four.

## Build

Commands run from the repository root (`/home/sprchuoi/sandboxes/CV_Embedded`); exit codes are the shell's.

```
$ sha1sum blog/posts/fourier-series-to-transform.md
045938cfd54f07cf89d24c8bb71151f4ac8e226c  blog/posts/fourier-series-to-transform.md
(exit 0)
```

```
$ build_environment/.venv/bin/python tool/build_blog_assets.py --only plots
[fourier-coefficient-projection] (1/T0)·∫ f·g dt over one period, 400,002 samples:
[fourier-coefficient-projection]   fundamental × fundamental: signed area +5.000000e-01
[fourier-coefficient-projection]   fundamental × third harmonic: signed area +0.000000e+00
[fourier-coefficient-projection]   square × third harmonic: signed area +2.122066e-01
[fourier-coefficient-projection]   the multiplier is 2/T0 = 2.0 per second; the divisor is T0/2 = 0.5 s; area/(T0/2) = b_3 +0.424413, fundamental against itself +1.000000
[fourier-coefficient-projection]   fundamental × fundamental lobes: ['+0.250000', '+0.250000'] positive, [] negative
[fourier-coefficient-projection]   fundamental × third harmonic lobes: ['+0.051687', '+0.051687', '+0.051687', '+0.051687'] positive, ['-0.103374', '-0.103374'] negative
[fourier-coefficient-projection]   square × third harmonic lobes: ['+0.106103', '+0.106103', '+0.106103', '+0.106103'] positive, ['-0.106103', '-0.106103'] negative
[fourier-limit-to-transform] 0.25 s pulse, height 1, period T0:
[fourier-limit-to-transform]   T0 = 1 s: f0 = 1 Hz, c_n at 1 Hz = 0.22508, c_n*T0 = 0.22508
[fourier-limit-to-transform]   T0 = 2 s: f0 = 0.5 Hz, c_n at 1 Hz = 0.11254, c_n*T0 = 0.22508
[fourier-limit-to-transform]   T0 = 4 s: f0 = 0.25 Hz, c_n at 1 Hz = 0.05627, c_n*T0 = 0.22509
[fourier-limit-to-transform]   X(1 Hz) = 0.22508; spread of c_n*T0 = 1.1e-05; the stems are |X(nf0)|/T0 and the rings are that product
[fourier-periodic-extension] 1 s record e^(-t/0.2), 400,002 samples:
[fourier-periodic-extension]   seam jump = 0.9933; midpoint of the two sides = 0.5034
[fourier-periodic-extension]   K = 101 series at the seam = 0.5011
[fourier-periodic-extension]   rings to -0.0817 (8.90% of the jump) and 1.0652 (6.56% of the jump)
[fourier-periodic-extension]   interior |t-seam| > 0.15: max error 3.4e-03
[fourier-rect-sinc-pair] rect of height 1, width tau:
[fourier-rect-sinc-pair]   tau = 0.25 s: X(0) = 0.2500, first zero at 4 Hz, X(0)*zero = 1.0000
[fourier-rect-sinc-pair]   tau = 1 s: X(0) = 1.0000, first zero at 1 Hz, X(0)*zero = 1.0000
[fourier-rect-sinc-pair]   tau = 2 s: X(0) = 2.0000, first zero at 0.5 Hz, X(0)*zero = 1.0000
[fourier-rect-sinc-pair]   energy both books (tau = 0.25 s): time 0.2500, frequency 0.2500, 90.28% inside |f| < 4 Hz
[fourier-rect-sinc-pair]   unit-area limit: X(f) = sinc(tau f) -> 1 for every f as tau -> 0; the constant's transform is an impulse of unit area, which has no width to draw
[fourier-square-partial-sums] grid 400,002 samples/period; coefficients a_n, b_n of x(t) = a0 + Σ a_n cos + b_n sin, a0 the mean level (no factor 2):
[fourier-square-partial-sums]   n = 0:  a = +0.0000e+00   b = +0.000000
[fourier-square-partial-sums]   n = 1:  a = +1.0000e-05   b = +1.273240
[fourier-square-partial-sums]   n = 2:  a = +0.0000e+00   b = -0.000000
[fourier-square-partial-sums]   n = 3:  a = +1.0000e-05   b = +0.424413
[fourier-square-partial-sums]   n = 4:  a = +0.0000e+00   b = -0.000000
[fourier-square-partial-sums]   n = 5:  a = +1.0000e-05   b = +0.254648
[fourier-square-partial-sums]   n = 6:  a = +0.0000e+00   b = -0.000000
[fourier-square-partial-sums]   n = 7:  a = +1.0000e-05   b = +0.181891
[fourier-square-partial-sums]   n = 8:  a = +0.0000e+00   b = -0.000000
[fourier-square-partial-sums]   n = 9:  a = +1.0000e-05   b = +0.141471
[fourier-square-partial-sums] square mean square = 1.0000
[fourier-square-partial-sums]   K =   1: mean square 0.8106 = 81.06% of it
[fourier-square-partial-sums]   K =   3: mean square 0.9006 = 90.06% of it
[fourier-square-partial-sums]   K =   9: mean square 0.9596 = 95.96% of it
[fourier-square-partial-sums]   K =  99: mean square 0.9959 = 99.59% of it
[fourier-symmetry-harmonics] three shapes, n = 0 … 8, (2/T0) convention:
[fourier-symmetry-harmonics]   odd square: a = ['+0.00e+00', '+1.00e-05', '+0.00e+00', '+1.00e-05', '+0.00e+00', '+1.00e-05', '+0.00e+00', '+1.00e-05', '+0.00e+00']
[fourier-symmetry-harmonics]   odd square: b = ['+0.00e+00', '+1.27e+00', '-0.00e+00', '+4.24e-01', '-0.00e+00', '+2.55e-01', '-0.00e+00', '+1.82e-01', '-0.00e+00']
[fourier-symmetry-harmonics]     odd harmonics a: max |a| = 1.00e-05;  even b: max |b| = 0.00e+00
[fourier-symmetry-harmonics]   quarter-shifted square: a = ['+0.00e+00', '+1.27e+00', '+0.00e+00', '-4.24e-01', '+0.00e+00', '+2.55e-01', '+0.00e+00', '-1.82e-01', '+0.00e+00']
[fourier-symmetry-harmonics]   quarter-shifted square: b = ['+0.00e+00', '-1.41e-18', '-0.00e+00', '+1.46e-18', '-0.00e+00', '-9.49e-18', '-0.00e+00', '+1.20e-19', '-0.00e+00']
[fourier-symmetry-harmonics]     odd harmonics a: max |a| = 1.27e+00;  even b: max |b| = 0.00e+00
[fourier-symmetry-harmonics]   full-wave rectified sine: a = ['+6.37e-01', '+7.14e-18', '-4.24e-01', '-2.20e-20', '-8.49e-02', '+8.23e-20', '-3.64e-02', '-7.69e-21', '-2.02e-02']
[fourier-symmetry-harmonics]   full-wave rectified sine: b = ['+0.00e+00', '-4.83e-20', '-1.97e-17', '+4.08e-20', '-1.58e-17', '+1.53e-20', '-3.75e-18', '-2.94e-20', '-1.17e-17']
[fourier-symmetry-harmonics]     odd harmonics a: max |a| = 7.14e-18;  even b: max |b| = 1.97e-17
[fourier-truncated-edge] B = K/T0, edge measured on a 262,144-point partial sum, 10-90% crossings interpolated:
[fourier-truncated-edge]   K =    9: tr*B = 0.4007, overshoot 9.116% of the step of 2 = 18.233% of the +/-1 level, first peak at 0.4500/B
[fourier-truncated-edge]   K =  101: tr*B = 0.4414, overshoot 8.951% of the step of 2 = 17.901% of the +/-1 level, first peak at 0.4951/B
[fourier-truncated-edge]   K = 1001: tr*B = 0.4454, overshoot 8.949% of the step of 2 = 17.897% of the +/-1 level, first peak at 0.5002/B
[fourier-truncated-edge]   ideal band-limited step: tr*B = 0.4458, overshoot 8.949% of the step of 2 = 17.898% of +/-1
[fourier-truncated-edge]   the first chapter's one-pole edge is 0.350, for contrast: 1.274x the ringing edge's constant
figures: wrote 62 SVG(s)
(exit 0)
```

The build rewrites all 62 SVGs. A second `--only plots` run left this chapter's seven byte-identical, and no tracked asset was modified:

```
$ sha1sum docs/blog/assets/plots/fourier-*.svg > /tmp/final_before.sha1
$ build_environment/.venv/bin/python tool/build_blog_assets.py --only plots
(exit 0)
$ sha1sum -c /tmp/final_before.sha1
docs/blog/assets/plots/fourier-coefficient-projection.svg: OK
docs/blog/assets/plots/fourier-limit-to-transform.svg: OK
docs/blog/assets/plots/fourier-periodic-extension.svg: OK
docs/blog/assets/plots/fourier-rect-sinc-pair.svg: OK
docs/blog/assets/plots/fourier-square-partial-sums.svg: OK
docs/blog/assets/plots/fourier-symmetry-harmonics.svg: OK
docs/blog/assets/plots/fourier-truncated-edge.svg: OK
(exit 0)
```

```
$ git status --porcelain docs/blog/assets
?? docs/blog/assets/plots/fourier-coefficient-projection.svg
?? docs/blog/assets/plots/fourier-limit-to-transform.svg
?? docs/blog/assets/plots/fourier-periodic-extension.svg
?? docs/blog/assets/plots/fourier-rect-sinc-pair.svg
?? docs/blog/assets/plots/fourier-square-partial-sums.svg
?? docs/blog/assets/plots/fourier-symmetry-harmonics.svg
?? docs/blog/assets/plots/fourier-truncated-edge.svg
(exit 0)
```

The seven are this chapter's new, untracked figures; there is no ` M ` line under `docs/blog/assets`, so the asset build churned nothing tracked.

```
$ python3 tool/build_blog.py --check
blog: curriculum and figures are consistent
(exit 0)
```

```
$ python3 tool/check_page_contract.py --crossrefs
numeric chapter references, resolved against the curriculum:

  fourier-series-to-transform
      chapter  6 -> The DFT, Without Magic
      chapter  6 -> The DFT, Without Magic
      chapter  8 -> Windows, Leakage and Resolution
  what-is-a-signal
      chapter  8 -> Windows, Leakage and Resolution
      chapter 10 -> Convolution, and Why Every DSP Block Is One
      chapter 10 -> Convolution, and Why Every DSP Block Is One
      chapter 10 -> Convolution, and Why Every DSP Block Is One
      chapter 18 -> Random Signals, Autocorrelation and PSD
      chapter 18 -> Random Signals, Autocorrelation and PSD
      chapter 18 -> Random Signals, Autocorrelation and PSD
      chapter 35 -> Chromatic Dispersion and the Frequency-Domain Equaliser
      chapter 36 -> Polarization Demultiplexing with CMA
      chapter 37 -> Carrier Phase Estimation
(exit 1)
```

Exit 1 is `report.ok` false, not an unresolved cross-reference: the resolution is complete and every title is the curriculum's.

```
$ python3 tool/check_page_contract.py
contract: 22 published chapter(s), 0 in flight, 4 promotable, 17 carry debt, 2 standalone page(s)
...
FAIL -- 3 finding(s) block the pull request:
  fourier-series-to-transform: [evidence-qa-open] QA finding still open: '[open] **The recipe "average over a period, divide by the harmonic's own area T₀'
  fourier-series-to-transform: [evidence-stale] gate.md reviewed ac9daff6a73b, the post is now 045938cfd54f -- re-run the review
  fourier-series-to-transform: [evidence-gate] gate verdict is SHUT, not PASS
(exit 1)
```

The first line is this file's `[open]` finding, which the harness is meant to honour; the other two are the separate Checker's `gate.md`, not QA findings.

```
$ python3 -m unittest discover -s tool/tests -t .
Ran 202 tests in 3.200s
FAILED (failures=2, skipped=1)
(exit 1)
```

The two failures are `TestAgainstTheRealCorpus.test_the_contract_holds` and `TestTheReport.test_the_report_states_that_the_contract_holds`, both because the contract is not ok — this file's `[open]` plus the Checker's gate. No other test failed, and one is skipped. The only non-green items are on the evidence lifecycle, which is the expected state.

The two hand checks the line-31 and recipe findings rest on:

```
$ build_environment/.venv/bin/python -c "import numpy as np; N=400002; n=9; v=(4/N)/np.tan(np.pi*n/N); e=4/(n*np.pi); print(repr(v), repr(e), v-e, (v-e)/e)"
0.1414710602905121 0.1414710605261292 -2.3561710915664946e-10 -1.665479203169837e-09
(exit 0)
```

```
$ build_environment/.venv/bin/python  # T0 = 2 s, x = sin(2 pi t / T0): the coefficient must be 1
T0 = 2.0
area of the product            = 1.0000000000000002
average of the product          = 0.5000000000000001
harmonic mean square (1/T0 int) = 0.5000000000000001
harmonic area over one period   = 1.0000000000000002   T0/2 = 1.0
page recipe: average / T0/2     = 0.5000000000000001   (should be 1)
correct: area / (T0/2)          = 1.0000000000000002
correct: average / mean square  = 1.0
correct formula 2/T0 * area     = 1.0000000000000002
(exit 0)
```

The other independent arithmetic checks (4/(nπ), 4/N, ½Σb_n², ∫sin², ∫sin·sin, 2/(3π), 2∫sinc², 1 − e⁻⁵, (1+e⁻⁵)/2, 0.0884/0.9933, 0.0652/0.9933, 0.446/0.350, 0.446/19 MHz, 0.35/19 MHz, 0.446/32 GHz, 15.625 ps, 1 + 2×0.08949, 53.125/2, 64/2, 26.6/53, 20log₁₀(1/3), 20log₁₀(1/5), 0.446/(10 ps × 1 GHz) = 44.6 and 0.446/(10 ps × 2 GHz) = 22.3) were run in `build_environment/.venv/bin/python` and are quoted in the findings.

## Checks performed

- [x] every number in the prose traced to the figure that computes it — all seven `fourier-*` stdout blocks, the three in-figure tables, the two overshoot columns, the five seam rows, the stems/rings pair and the widths/zeros table match the page at the printed precision
- [x] arithmetic re-derived independently of the figure script (4/(nπ), 4/N, (4/N)cot(πn/N) against 4/(9π), ½Σb_n², ∫sin², ∫sin·sin, 2/(3π), 2∫sinc², 1 − e⁻⁵, (1+e⁻⁵)/2, 0.0884/0.9933, 0.0652/0.9933, 0.446/0.350, 0.446/19 MHz, 0.35/19 MHz, 0.446/32 GHz, 15.625 ps, 1 + 2×0.08949 = 1.1790, 53.125/2, 64/2, 26.6/53, 20log₁₀(1/3), 20log₁₀(1/5), K = 44.6 → 45 and 22.3 → 22)
- [x] relative links resolved against `docs/blog/` (the seven `assets/plots/fourier-*.svg` files exist; the rendered HTML references all seven; every `href`/`src` in the rendered page resolves)
- [x] `--crossrefs` read after the chapter-5 insertion (the page's chapter 6 ×2 and chapter 8 ×1 resolve; what-is-a-signal's 8/10/18 resolve; 35 and 37 resolve and 36 is the checker's "and"-as-range reading)
- [x] EN/VI curriculum parity (2 page slugs, 10 part ids, 48 article slugs in the same order and counts; `build_blog.py --check` exit 0)
- [x] terminology matches the neighbouring chapters (0.35/B; "Gibbs"; "leakage, chapter 8" and the 100.5-period example; 26.6 GHz/53 GBd; 32 GHz/64 GBd/15.6 ps; energy/power signal); the page's "one-pole" label for 0.35/B is correct for the constant (ln 9 / 2π = 0.3497/B) though chapter 1 does not use the word
- [x] no figure contradicts its caption (all seven captions and the in-figure notes, tables, ticks, leader lines and percentage denominators checked against the scripts and the drawn data)
- [x] the `::: try` callout arithmetic and the assumptions it uses (19 MHz, 23.47 ns, 18.42 ns, 9.54 dB, 13.98 dB, 27%; B = K/T₀ and the 0.446/0.350 constants established in section 4; 0.35/B in chapter 1)
- [x] the `::: optical` numbers grepped against the published chapters (26.6 GHz/53 GBd, 32 GHz/64 GBd, 15.6 ps, 14 ps, 8.95%, 53.125/26.5625) — no contradiction; the exact pair exists in the brief and refines, rather than contradicts, the published rounded pair
- [x] the figure build is deterministic (a second `--only plots` run produced byte-identical fourier SVGs) and churns no tracked asset
- [x] the `## Build` section records the exact commands and their exit codes
