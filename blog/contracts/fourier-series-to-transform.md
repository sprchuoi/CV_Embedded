Slug: fourier-series-to-transform
Level: Beginner to Intermediate
Prerequisites: what-is-a-signal, sampling-and-aliasing, decibels-and-dynamic-range

# From Fourier Series to the Fourier Transform

The reader arrives believing in a spectrum. Sampling already convolved one with
an impulse train to explain aliasing, and the decibel chapter taught them to
read it on a log axis, so a spectrum is already a place they can be wrong in —
but the belief is borrowed. Nobody has shown them a square wave built out of
sines; the sinusoid arrived as the first of six elementary shapes, and the
transform is the one instrument this course uses before it has derived. The
chapter exists to pay that loan. It makes *a periodic signal is its harmonics*
something the reader has seen rather than been told, it turns the periodic
assumption from an unexamined convenience into a trap they cannot stop noticing
once a finite record is involved, and it takes the period away so that a signal
that never repeats — one pulse, one captured record of a link — has a spectrum
too. Everything from the DFT onward is this chapter with a finite record bolted
on.

## Outcomes

- Write the Fourier series of a square wave and of a rectangular pulse train in
  both conventions — sine and cosine amplitudes, and complex-exponential
  coefficients — and state the factor between a coefficient's magnitude and the
  peak amplitude of that harmonic.
- List the coefficients that must vanish and name the first harmonic that does
  not, from a waveform's symmetry class alone — even, odd or half-wave — without
  computing an integral.
- Take a record that is not a whole number of periods and state which two
  signals its coefficients cannot distinguish, then name where in the spectrum
  the difference between them appears.
- Take the period of a rectangular pulse train to infinity and produce the
  substitution that turns the sum into an integral: the line spacing, the
  density that survives the limit, and the condition the signal must satisfy for
  that limit to exist.
- Estimate, from a waveform's rise time and its period, the highest harmonic
  that carries significant energy, and say which of those two numbers set it.

## Claims to verify


- The square wave is odd-harmonic and falls as 1/n: the coefficient table the script integrates prints b₁ = 1.2732, b₃ = 0.4244, b₅ = 0.2546, with b₂ and b₄ below 10⁻⁹ and every cosine coefficient at the grid's own floor (10⁻⁵ at the two jumps) — checkable in `fourier-square-partial-sums`, which extracts each coefficient by integrating the plotted ±1 signal against cos and sin over one period rather than evaluating 4/nπ.

- A coefficient is a measurement, not a definition: the product curves have signed area 0.5000 for the fundamental with itself, −9×10⁻¹⁶ for the fundamental with the third harmonic, and 0.2122 for the square wave with the third harmonic — which is b₃/2, the number the 2/T₀ divisor turns into b₃ — checkable in `fourier-coefficient-projection`, which computes all three integrals and shades the lobes that cancel.

- Symmetry deletes harmonics without arithmetic: the quarter-period-shifted square is cosine-only with a₁ = +1.2732 and a₃ = −0.4244 while its sine coefficients print 3×10⁻¹⁶, and the full-wave rectified sine has DC = 0.6366 and only even harmonics (a₂ = −0.4244, a₄ = −0.0849, every odd harmonic at 10⁻¹⁵) — checkable in `fourier-symmetry-harmonics`, which integrates the three plotted shapes and prints both coefficient sets.

- Truncation buys a slope, never a corner: the edge's 10–90% transition time × B is 0.400, 0.442 and 0.445 at K = 9, 101 and 1001 (K the highest harmonic kept, B = K/T₀), converging on the 0.446 of an ideal band-limited step against the 0.350 of chapter 1's one-pole edge; and the overshoot at the jump stays at 9.12%, 8.95% and 8.949% of a step of 2 at those same K, with the first ringing peak approaching T₀/2K from the jump — checkable in `fourier-truncated-edge`, whose two panels measure the transition and find the extremum. The example brief's "8.9% of the step" survives only if the figure labels which step: the full jump of 2, not the ±1 level, where it is 17.9%.

- The series does not know your record, only its repetition: on a 1 s record of e^{−t/0.2} the periodic extension has a 0.993 jump at the seam, the K = 101 series returns 0.5004 there — the midpoint of the two sides — and rings to −0.0817 and +1.065 either side (8.9% and 6.6% of the jump) while fitting the interior to 3.4×10⁻³ — checkable in `fourier-periodic-extension`, which builds the extension from the plotted record and prints all four numbers.

- The lines crowd and shrink while the envelope stays: at 1 Hz the script prints c_n = 0.22508, 0.11254 and 0.05627 for T₀ = 1, 2 and 4 s with spacings of 1, 0.5 and 0.25 Hz, so c_n·T₀ = 0.2251 every time (the three agree to 10⁻⁵), and that product equals the continuous transform at the same frequency — checkable in `fourier-limit-to-transform`, which integrates the pulse train at each period and multiplies by the period to show the invariant. This replaces the example brief's "replace 1/T₀ with df", which is a substitution no figure can check; what the figure checks is that the same number survives the change of period.

- Power is the sum of the lines: the ±1 square's mean square is 1.0000 and the first K harmonics carry 81.06%, 90.06%, 95.96% and 99.59% of it at K = 1, 3, 9 and 99, so the missing 4% at K = 9 is the ringing and not an error in the series — checkable in `fourier-square-partial-sums`, which computes the time-domain mean square independently of the coefficients.

- Widening the pulse trades height for width and nothing else: X(0) = 0.25, 1 and 2 with first zeros at 4, 1 and 0.5 Hz for τ = 0.25, 1 and 2 s, so X(0) × first zero = 1 in every case; the 0.25 s pulse's energy books both ways (∫x²dt = ∫|X|²df = 0.2500) with 90.3% of it inside the first lobe |f| < 4 Hz; and run to the limit the same scaling is a spike of unit area rather than a curve, which is why the constant has no transform you can draw — checkable in `fourier-rect-sinc-pair`, which computes the pair, the energy both ways, and the widths.

## Transfer

Work: The frequency a lane's insertion-loss figure is quoted at — 26.6 GHz on a 53.125 GBd PAM4 lane (26.5625 GHz, rounded), 32 GHz on a 64 GBd coherent one — and, more usefully, why it is that number. Half the baud rate is the fundamental of the fastest pattern the lane can carry: alternate every symbol and the data is a square at R/2, whose odd ladder sits at 3R/2, 5R/2 and beyond, and nothing above R/2 is required of the transmitter or passed by the channel. The fastest pattern therefore arrives as K = 1 — one sine, round, no corners — so the budget inverts the channel up to exactly one frequency and the equaliser's gain is specified there and nowhere else. What the transmitter still emits above it is a mask and crosstalk line: it is bought in driver power and charged again to the neighbouring pair's margin, and the mask caps it because the bill is not paid in your own eye — and the coupling that carries it rises with frequency exactly where the mask makes it expensive.

Life: The buzz of a cheap inverter or a UPS. Its output is a stepped square at 50 Hz, so its harmonics land at 150, 250 and 350 Hz at 1/3, 1/5 and 1/7 of the fundamental, and a full square's total harmonic distortion — those terms in RMS against the fundamental — is 48%. The "pure sine" version of the same product is sold on a THD under 3%; that number, not the adjective, is the difference between the two products, and it is exactly the harmonics someone paid to remove.

## Section outline


- **A square wave is a sum of sines** — adds: a periodic shape is a fundamental plus its integer multiples, and the rebuild is visible on an axis before any coefficient is written down. Carries: figure "fourier-square-partial-sums". Reader must already accept: a sinusoid is three numbers and summing signals means adding their values at each instant — established in what-is-a-signal, "The elementary signals" and "Four ways to write the same thing"; and that a periodic signal has a period T₀ with fundamental f₀ = 1/T₀ — established in what-is-a-signal, "Periodicity and symmetry". Intuition lands first and hardest here: the figure is the section, the coefficient table is its caption, and the formula waits for section 2.

- **What each coefficient measures** — adds: a coefficient is an average of the signal multiplied by one harmonic, and every other harmonic averages to zero, so the number that survives is that harmonic's share. Carries: figure "fourier-coefficient-projection". Reader must already accept: that two signals can be multiplied point by point and the product averaged over a period, and that equal positive and negative areas cancel — established in what-is-a-signal, "Energy and power", where energy is already written as the integral of a signal against itself. Intuition lands in the three shaded product curves; the 2/T₀ divisor is read off the picture (the fundamental's own area is T₀/2), and the formula is the section's last line.

- **Symmetry decides which harmonics survive** — adds: the drawing decides the spectrum — even gives cosines only, odd gives sines only, half-wave gives no even harmonics — so the spectrum is predictable before any integral is done. Carries: figure "fourier-symmetry-harmonics". Reader must already accept: the even/odd decomposition, which is also where what-is-a-signal, "Periodicity and symmetry" promised that "a real even signal has only cosine terms"; this section is where that promise is paid. Intuition is the shape, then the stems, then the printed coefficient sets as the check — three drawings before three tables.

- **What truncation does to an edge** — adds: keeping K harmonics gives an edge a transition time reciprocal to K, which is why the answer is a bandwidth, and an overshoot at the corner of 8.9% that no K removes. Carries: figure "fourier-truncated-edge". Reader must already accept: that a partial sum is what you have when you stop (section 1), and that a rise time is a measured 10–90% transition with the rule of thumb 0.35/B — established in what-is-a-signal, "The elementary signals". Intuition is the zoomed edge; the two printed products (tr·B and the overshoot) are the evidence, and the estimate K ≈ 0.45/(tr·f₀) is read off the figure, not asserted — the section must also say why its 0.45 is not chapter 1's 0.35 (a ringing edge is not a one-pole edge).

- **The sum only knows the repetition** — adds: a sum of period-T₀ harmonics is itself periodic, so the series rebuilds the butt-jointed infinite copy of the record, inventing a jump at the seam when the ends do not meet and splitting that jump down the middle. Carries: figure "fourier-periodic-extension". Reader must already accept: every harmonic in the sum has period T₀ or a submultiple (section 1); a jump is a step (what-is-a-signal, "The elementary signals"); and a captured record is not by itself periodic (what-is-a-signal, "Periodicity and symmetry", the wrap-around warning; sampling-and-aliasing, "What it looks like on a spectrum analyser", where the replicas are a modelling choice). Intuition is the three butt-jointed copies and the marked seam before any coefficient is discussed; no integral appears in this section at all.

- **Taking the period away, and what it costs** — adds: as T₀ grows the lines crowd by 1/T₀ and shrink by 1/T₀ while the envelope they trace stays fixed, so 1/T₀ is a bandwidth element df, the coefficients become a density, and the envelope is the transform — defined only for signals with finite area, so the constant's limit is a spike rather than a curve. Carries: figures "fourier-limit-to-transform" and "fourier-rect-sinc-pair". Reader must already accept: the coefficient is an amplitude and the spacing is 1/T₀ (sections 1 and 5); only signals with finite area — absolute integrability, which is not the same as finite energy — have an ordinary transform, periodic ones being power signals (what-is-a-signal, "Energy and power"); and an impulse is defined by what it does in a sum (what-is-a-signal, "The elementary signals"). Intuition lands before formalism twice: the reader should predict the halving of the stem height before the page turns, and the substitution is written as a reading of that picture; the section opens by packing (a_n, b_n) into one complex coefficient with the figure's two-sided stems drawn and labelled as the mirror, so that even the notation change is a picture. The closing paragraph hands the finite record to the next chapter without defining the DFT. (All seven figures are computed plots; none needs a hand-drawn SVG, and the seam is stronger measured than drawn.)

## Comprehension plan


- engineer: the density is the step that must be derivable, not asserted: why each line carries a 1/T₀ that the transform does not, and why X(f) is an amplitude per hertz while c_n is an amplitude. The figure has to let them do it — read the stem at 1 Hz (0.2251), read it again at T₀ = 2 (0.1125), multiply each by its own period, get the same number. The observable test is not "can they say where the density came from" but "can they predict the halving before it is drawn": an engineer who can is through, and one who cannot will recite the pair from memory and still be unable to say what the 1/T₀ became — the failure is invisible until they are asked for the units.

- newcomer: the sentence the opening must earn is "the square wave on the scope is a sum of sines, and this picture shows it" — no formula, no integral, no coefficient table standing between the reader and the figure. The expected stall is the upper limit of the coefficient integral at the end of section 2: the newcomer reads "over one period" and asks why the rest of the signal is not in the answer. That is the right question and section 5 is its answer, so the chapter must let it stand rather than answer it with "because the signal is periodic, of course" — which states the trap as a premise and spends it. This is where I part from the example brief: the trap cannot be made to "feel" real before the series is built and used, because a trap you have nothing to lose to is only a warning; it bites in section 5, after symmetry and the edge budget have made the series worth having.
