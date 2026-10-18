Slug: fourier-series-to-transform
Level: Beginner to Intermediate
Prerequisites: what-is-a-signal, sampling-and-aliasing

<!--
A filled example, for chapter 5. This is what a reviewed brief looks like: the
outcomes are demonstrable, the claims are checkable from this repository, and
the comprehension plan says what each persona is expected to fail on.

It is kept here, not in blog/contracts/, because a brief there would put the
chapter in flight and require an evidence pack for prose that does not exist
yet. When the chapter is actually written, copy this to
blog/contracts/fourier-series-to-transform.md and revise it — a brief that was
not argued with is a form.
-->

# From Fourier Series to the Fourier Transform

The reader arrives knowing that a signal is a function and that sampling makes
its domain discrete. They have met the sinusoid as three numbers. They do not
yet have any reason to believe a square wave is made of sines, and the honest
position of this chapter is that the reason is a picture, not a theorem.

The chapter exists to install one belief — *any* reasonable periodic signal is a
sum of harmonics — and then to take the period away, which is the only step in
the course where a limit is genuinely load-bearing. Everything from the DFT
onward is this chapter with a finite record bolted on.

## Outcomes

- Write the Fourier series of a periodic signal and say, for each coefficient,
  what physical quantity it measures.
- Predict which harmonics a waveform's symmetry removes, for even, odd and
  half-wave symmetry, and check the prediction against a figure.
- Explain what happens to the series as the period grows, name the substitution
  that turns the sum into an integral, and say what breaks if the signal is not
  absolutely integrable.
- Estimate how many harmonics a given edge rate needs, from the rise time, and
  say why the answer is a bandwidth.

## Claims to verify

- A square wave's series contains only odd harmonics, with amplitudes falling as
  1/n — checkable against the partial-sum figure and its printed coefficient
  table.
- The transform pair follows from the series by letting the period go to
  infinity and replacing 1/T0 with df — checkable in the limiting-sum figure,
  which plots the discrete line spectrum at three periods on one axis.
- Gibbs ringing overshoots by about 8.9% of the step, whatever the number of
  terms — checkable in the partial-sum figure, which prints the overshoot for
  N = 5, 51 and 501.
- The harmonic amplitudes of the figure's square wave, summed, converge to the
  signal's power — checkable by Parseval against the time-domain mean square the
  script computes independently.

## Transfer

Work: every compliance measurement on a real link is this decomposition applied
to a captured record — the harmonic content of a drive signal, the spectral
shape of a transmitter, and the noise floor a mask is drawn against. The reader
who does not believe the decomposition cannot read the mask.

Life: the same arithmetic explains the pitch of a cheap inverter, why a mains
hum is one tone plus its harmonics rather than a smear, and why a "pure sine"
inverter is specified by a total harmonic distortion number rather than called
pure.

## Comprehension plan

- engineer: the step that takes the sum to the integral — the 1/T0 → df
  substitution and the passage from a discrete index to a continuous variable —
  must be derivable with the figure in front of them, not accepted. If they
  cannot say where the density came from, the chapter has failed the one thing
  it exists to do.
- newcomer: the opening must make periodicity feel like a trap before any
  integral appears. The expected stall is the phrase "one period of a periodic
  signal" in the first section, which quietly assumes the reader has accepted
  that the record is exactly one period. If the newcomer reaches the integral
  without that, the chapter is fine; if they stall there, the section needs the
  wrap-around picture earlier.
