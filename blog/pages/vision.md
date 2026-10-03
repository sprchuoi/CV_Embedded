> This page is a working document, not a finished statement. I revise it as the work changes. Anything here that reads as a settled position is a position I currently hold, not one I have finished defending.

## The thesis

Most engineers meet signal processing exactly once, in a course that derives the Fourier transform, proves the sampling theorem, and stops. Then they spend a career treating the DSP block in their system as a vendor-supplied black box with a datasheet, and the interesting engineering happens somewhere else.

I think that is a bad trade. The DSP is usually where the hard constraints live — power, latency, word length, tap count — and those constraints are only negotiable if you understand what the algorithm is doing well enough to change it. My aim is to be the kind of engineer who can move the boundary: who can read a link budget, say which equaliser structure it implies, and then go and implement it at rate in fixed point without losing the margin in the implementation.

This blog is the forcing function for that. Writing a chapter is the only reliable test I have found for whether I actually understand something, and drawing a figure is the only reliable test for whether I understand it well enough to explain it.

## What I am working on

Three threads, in rough order of how much of my time they take:

**Signal-processing implementation for optical links.** Equaliser structures and where each one belongs — feed-forward, decision-feedback, frequency-domain. Fixed-point representation and where the binary point goes. FFT architectures and block floating point, because an unscaled transform grows by $\log_2 N$ bits and the converter does not have them to spare. Carrier and timing recovery as control problems rather than as blocks.

**Simulation-driven validation.** Building the model before the hardware exists, so the failure modes are known before bring-up rather than discovered during it. A link model that reproduces dispersion, phase noise and quantisation will tell you the tap count, the word widths and the block size; a testbench will tell you that your model was optimistic. I care a lot about the gap between those two, and about closing it in the direction of the model being *pessimistic*.

**Teaching the material in public.** The chapters here exist because the notes I made for myself were too terse to be useful even to me six months later. If a chapter is not clear enough that someone else can follow it, it is not finished.

## What I am reading and testing

- **Fixed-point and word-length optimisation.** Where the analytic bounds are too loose to be useful, and whether a simulated annealing over word lengths beats the discipline of a scaling schedule.
- **Adaptive equalisation beyond CMA.** Multi-modulus and decision-directed adaptation for higher-order QAM; what genuinely degrades and what only degrades in simulation.
- **Neural equalisers.** Whether a small network earns its area over a well-tuned DFE at the same throughput, and — more usefully — the conditions under which it does not. I am sceptical of the reporting norms here and would like to test them at fixed complexity rather than fixed accuracy.
- **Nonlinearity.** Digital backpropagation costs far more than it returns in most links. I want a clear account of the cases where that stops being true.

## Open questions

These are the ones I do not have answers to, and would like to:

1. **How much of a receiver can be made self-calibrating?** Most of the analogue impairments — I/Q imbalance, ADC skew, bandwidth — are slowly drifting and individually measurable. How much of that can be estimated in the background, in the same datapath that already exists, without the estimator eating the margin it recovers?

2. **Where is the real boundary between equalisation and coding?** Soft-decision FEC and a soft-output equaliser can exchange information, but in shipping silicon they usually do not. What is actually lost by that separation, and is it worth the interface complexity to recover it?

3. **Is the FFT the right primitive?** It is the standard answer for a long static filter. But the transform is a large fraction of the power and almost all of the latency, and the filter it implements is known in advance. Is there a sparse or structured transform that exploits that — and if not, why not?

4. **How do you validate a fixed-point DSP design honestly?** Simulation gives a bit-exact answer for inputs it was given. What is the equivalent of a coverage metric for a datapath, and what does it take to believe a word-length budget rather than merely pass a test vector?

## How I work

Three habits, all of which this site is designed to make visible:

**Measure, do not assert.** Every number in these chapters comes from a figure that computes it. Where a figure models rather than measures, it says so on its own face. Where I could not verify a claim, the chapter says that too, and it is the reason a few of them carry caveats I would rather not need.

**Draw first.** If I cannot draw a concept, I do not understand it well enough to use it. Several chapters only made sense while I was trying to work out what the figure should actually show.

**Keep the arithmetic honest.** An algorithm that is not implementable at rate and within power is not an algorithm, it is a paper. Complexity claims get multiplied out into multiplies per symbol and watts, and they get checked against the sibling chapters, because the easiest way to fool yourself is to change conventions halfway through.

## Why publish at all

Part practical, part selfish. Practical: the notes are more useful to other people than they are sitting in a folder, and engineering that is written down gets reviewed. Selfish: a public claim is a much stronger forcing function than a private one, and being wrong in public is the fastest way I know to stop being wrong.

If something here is incorrect, I would rather hear it than keep it.
