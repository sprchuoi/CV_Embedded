Chapter 5 ended twice. Once with a transform of everything — an integral over all time, a spectrum that exists at every frequency — and once with a warning that a captured record has neither the period the series wants nor the whole signal the transform wants. What is left is the thing you actually have: a column of numbers off an ADC, finite, and known only inside the window.

The transform of that column is the **discrete Fourier transform**, and it is the smallest piece of mathematics in this course. N numbers in, N numbers out, one product per input-output pair and a running sum, no calculus anywhere. The reason it feels like magic is not the arithmetic; it is the order in which the three questions are usually answered. Which frequency does bin 7 mean? Why is the second half of the spectrum a copy of the first? Why does one pure tone come out as a smear? Every one of them falls out of a single picture — the probe — and each answer changes how you read a spectrum for the rest of your career.

This chapter builds that picture and stops there. It does not make the transform fast; chapter 7 does that, and it assumes the cheap version you are about to meet. It does not teach you to choose a window; chapter 8 does that, and it assumes the leakage you are about to see. What this chapter does is let you take a record, say which frequency each output number belongs to, and — the part that is worth more than the rest — say what the transform did **not** tell you.

## A record is N numbers

![One tone as 64 numbers: the record, the 64 output numbers it is transformed into, and the same 64 outputs read on two different sample-rate rulers.](assets/plots/dft-bin-mapping.svg)

Everything in this chapter happens to the 64 samples in the top panel of that figure: 8 ms of a 1 kHz cosine at 8 kHz, drawn with every sample visible. That is the whole input. Not the signal behind it, not the shape the eye interpolates between the dots, not what happened between two samples — nothing that is not one of those 64 numbers can reach the answer.

The transform is a bank of measurements run on those numbers. For each output index $k$ there is one **probe**: a sequence of N complex numbers that turns $k$ times as you walk across the record,

$$b_k[n] = e^{-j2\pi kn/N}, \qquad n = 0, 1, \dots, N-1$$

and the output is the record multiplied by that probe and summed:

$$X[k] = \sum_{n=0}^{N-1} x[n]\,e^{-j2\pi kn/N}, \qquad k = 0, 1, \dots, N-1$$

Read that as a correlation and nothing more. $X[k]$ is the inner product of the record with a unit-amplitude thing that spins $k$ times; it measures how much of that particular spin the record contains. Do it for every probe and you have N numbers, for N² complex multiplies — a count with its own section, because it is the reason the next chapter exists.

Why this probe and not some other? Because the probes are orthogonal, and orthogonality is what makes each output mean exactly one thing. The figure prints both measurements: the probe at bin 8 against itself sums to **64.000**, and the probe at bin 8 against the probe at bin 9 sums to **0.000**. A tone that matches probe 8 lands entirely in bin 8's sum and contributes nothing to bin 9's. That is the whole trick, and it is a property of the probes rather than of the signal.

The divisor is the probe's own sum of squares, which is N. Divide the sum by N and you have an average product rather than a raw sum, and an average product is what an amplitude can be read from. For the 1 kHz tone of the figure the peak comes out at $|X[8]| = 32.000$, which is $N/2$ rather than N, because a real cosine is two counter-rotating phasors of amplitude one half — chapter 5's $c_n = \tfrac12(a_n - jb_n)$ seen from the other side. So the amplitude is $2|X[k]|/N$, and the figure prints both the raw 32.000 and the 1.000 it converts to.

::: key One output number, one probe
$X[k]$ is the record correlated against $e^{-j2\pi kn/N}$ and divided by the probe's own sum of squares, N. The probes are orthogonal, so each output measures one spin and ignores the rest — and nothing in the definition knows what a hertz is.
:::

Which is the problem the next section fixes.

## Bin k is a frequency: k·fs/N

A probe turns $k$ times across one record. A record is $N$ samples at $f_s$ samples per second, so it lasts $T = N/f_s$ seconds. One turn per record is therefore one cycle per $T$ seconds, and $k$ turns per record is

$$f_k = \frac{k}{T} = k\,\frac{f_s}{N} \quad \text{Hz}, \qquad \Delta f = \frac{f_s}{N} = \frac{1}{T}$$

Two ways of writing one identity: cycles per record times records per second. It is the one piece of arithmetic here you have to do in your head, so here it is on the figure's own numbers. The record is 8 ms, so one turn per record is $1/0.008 = 125$ Hz. The bin spacing is $8000/64 = 125$ Hz. The tone is at 1000 Hz, which is $1000/125 = 8$ turns per record, which is bin 8 — and bin 8 is where the single stem stands.

That is the mapping, and it barely involves the transform. The transform returned 64 numbers without being told $f_s$ — it cannot be told, because $f_s$ is not in the sum. The bottom panel hangs the same numbers on a second ruler: at 16 kHz the spacing is 250 Hz, the record 4 ms, and the same stem at bin 8 is 2000 Hz. The heights are identical because the numbers are; only the label moved.

That is why **the peak is at bin 8 in both readings**. A bin is a count of cycles per record, and a record is a length of time; a frequency is the ratio of the two. Eight cycles in 8 ms is 1 kHz. Eight cycles in 4 ms is 2 kHz. The transform counted the eights; you supplied the time.

Three consequences, and the third is the one that catches people:

- **The spacing is $f_s/N$; the period is $f_s$ wide.** Bins 0 to N−1 step from DC across one whole period of the spectrum, which the next section explains. Here they are 125 Hz apart.
- **The last distinct bin is $f_s/2$, bin $N/2$.** At 8 kHz that is bin 32, 4000 Hz: the fastest thing 64 samples can hold, a level alternating sign every sample. The mirror section gives it its own paragraph.
- **Only a longer record narrows the spacing.** Doubling N at the same $f_s$ halves $\Delta f$ and leaves the top of the span where it was. Resolution is observation time, $1/T$, and here that sentence is a definition rather than a claim.

::: warn A spectrum without a sample rate is not a spectrum
The same 64 numbers are a 1 kHz tone at 8 kHz and a 2 kHz tone at 16 kHz. A spectrum exported with no $f_s$ and no N is a list, and its axis was typed by somebody.
:::

So far the record has been one period of a 1 kHz tone that happens to fit exactly. The claim was in the mapping rather than in the tone — but every one of those 64 numbers is being treated as a period of something, and the next section says what.

## The record is one period

![A record that does not repeat, its butt-jointed copies, and the spectrum of the same record repeating every fs.](assets/plots/dft-record-is-one-period.svg)

Every probe has period N samples: $e^{-j2\pi k(n+N)/N}$ is $e^{-j2\pi kn/N}$. A sum of N terms cannot distinguish $x[n]$ from $x[n+N]$, because the same numbers presented again contribute the same products. So the object the transform describes is not the record; it is the **infinite repetition of the record**, end to start, with whatever discontinuity that glue invents at every seam.

Chapter 5 found this seam the hard way, rebuilding a decaying exponential out of harmonics and watching it ring at a join the record never had. Here it is not a discovery but the definition, visible in the first line — and not a defect: it is what makes a finite transform exact.

The figure's record is a burst, $e^{-n/6}$, that starts at 1.0000 and is 0.0000 by its last sample. Butt-joined, it is a train of spikes at every 64 samples, and each seam is a jump of **1.0000** — the full height of the record. The transform of those 64 numbers is, exactly and with no approximation anywhere, the spectrum of that spike train.

Which is the good news and the bad news in one sentence. If the record **is** one period of a periodic signal — a clock, a PRBS, a test tone chosen to fit — the transform is exact and there is no truncation error to argue about, which is what a bench measurement usually tries to arrange. If the record is one look at something that started before it and continues after it, the transform is still exact but about the wrong object: it answers "what periodic signal has this record as its period", which is not the question you asked. The seam's energy lands in every bin, and the leakage section is that bill arriving.

Turn the fact around and the frequency side appears. The spectrum of the record repeats every $f_s$, and the figure measures it: the curve is the same at $f$ and at $f + f_s$ to within $7.9\times10^{-14}$ over 18,001 grid points, which is $1.2\times10^{-14}$ of the peak 6.514 — round-off, not structure. This is chapter 2's picture, the one that explained aliasing: sample in time and the spectrum is replicated every $f_s$, forever. The DFT does not add a second periodicity; it **samples the first one** — sixty-four bins, 125 Hz apart, one period of 8 kHz.

The two statements together make the transform self-consistent:

- **In time**, N samples are one period, and the object repeats every N samples.
- **In frequency**, N bins are one period, and the object repeats every $f_s$ hertz.
- The number of samples in one time period equals the number of bins in one frequency period, which is why the transform of N numbers is N numbers and why it can be inverted at all.

That is what makes the DFT a closed world: nothing outside the record exists in the answer, so nothing has to be recovered from outside, and a transform that had to infer what lay beyond the window would be lossy instead of invertible.

## Negative frequency is the mirror

![The magnitude and phase of a real record's spectrum, two-sided, with mirror pairs marked and the Nyquist bin singled out.](assets/plots/dft-conjugate-mirror.svg)

Now put a real record in. Any record off one ADC channel is real, and a real record has a spectrum with a mirror in it:

$$X[N-k] = \overline{X[k]}$$

The reason is one line of algebra. The probe at $N-k$ is $e^{+j2\pi kn/N}$, the complex conjugate of the probe at $k$; the record is real, so the sum of the conjugates is the conjugate of the sum, and the two outputs carry the same numbers with one sign flipped. The figure measures it on a record with four components: the largest difference across all 64 bins is $3.6\times10^{-15}$.

Read it twice, because a conjugate pair is two numbers in four places. The **magnitude** is even: 64.000 at DC, 32.000 at bins 3 and 61, 16.000 at bins 7 and 57. The **phase** is odd: $+0.300$ rad at bin 3 and $-0.300$ at bin 61, $-1.000$ at bin 7 and $+1.000$ at bin 57. Thirty-three of the 64 numbers are new, and the other thirty-one are determined by them.

So half of the spectrum you compute for a real signal is bookkeeping — chapter 5's $c_{-n} = \overline{c_n}$, now on bin indices. Negative frequency is not a second signal travelling backwards; it is the other half of the cosine: $\cos(2\pi ft) = \tfrac12(e^{j2\pi ft} + e^{-j2\pi ft})$, two counter-rotating phasors, one at $+f$ and one at $-f$, which is exactly why an on-bin real tone puts $N/2$ in bin $k$ and another $N/2$ in bin $N-k$.

Two bins have no partner.

**Bin 0** is its own mirror and holds the record's mean: the figure's DC level of 1.0 puts 64.000 there, and the amplitude is $|X[0]|/N$, with no factor of two.

**Bin $N/2$** — bin 32, 4 kHz, $f_s/2$ — is also its own mirror, since $N - N/2 = N/2$. A number equal to its own conjugate is real, so the Nyquist bin can have a magnitude and a sign but not an angle: the figure's $\pm0.25$ alternating term puts **16.000 + 0.000j** there. It is not an accident of the example: a tone at exactly $f_s/2$ samples as $+A, -A, +A, -A$, and its phase is only the sign of the first sample.

::: key Real input, half the work
$X[N-k] = \overline{X[k]}$ for any real record: magnitude even, phase odd, $N/2+1$ independent bins out of N, and bins 0 and $N/2$ real. Size the output buffer at $N/2$ and you drop Nyquist; size it at N and you carry a copy.
:::

One habit worth taking from this section: when a two-sided spectrum of a real signal does not mirror, you are looking at a complex signal or at a bug, and both are worth ruling out before you interpret the shape.

## Off a bin is leakage

![The same tone on a bin and half a bin off it: one stem against a skirt that reaches every bin, with the two dominant bins' values and their sum.](assets/plots/dft-on-and-off-bin.svg)

Everything so far put the tone exactly on a bin, because 1000 Hz is eight whole cycles of an 8 ms record. Move it half a bin, to 1062.5 Hz, and the same tone becomes a smear.

The figure shows both. On the bin, one stem of **32.000** and every other bin at **0.000** to the last bit. Half a bin off, two stems of **19.917** and **20.823** and a skirt in every other bin, still at **1.330** eleven and a half bins away.

**The two neighbours are not equal.** They are 4.5% apart, and the difference is the mirror of the previous section leaning on the lower one: the tone's negative-frequency image is 17 bins away, not infinitely far, and its skirt tilts the pair. On a long record they converge; on 64 samples they do not.

**Neither neighbour is the amplitude.** The pair reads 28.815 where the line read 32.000 — **0.900** of it, which is a 0.9 dB under-read of a tone that is comfortably above the noise. Summing the two magnitudes is no better: 40.740, which is 1.27 times the true line. Neither the peak, nor the pair, nor their sum is the amplitude, because the amplitude is not in any one bin.

**What the pair does hold is power.** $19.917^2 + 20.823^2 = 830.280$, which is **81.08%** of the 1024 that the on-bin tone put in its single bin. The other 19% is in the remaining 62 bins, decaying slowly, which is why the skirt at bin 20 is still visible at 1.330.

The skirt is the previous section's seam. A 1062.5 Hz cosine in an 8 ms record does not complete a whole number of cycles: it starts at one phase and stops at another, so the repetition has a corner at every join, and a corner has energy at every frequency. Said precisely, the transform of the record is the tone's line **convolved with the transform of the rectangle that cut it out** — a tall central lobe and a slowly falling skirt, stamped around the tone. Windows, in chapter 8, change the rectangle for a shape whose skirt falls faster and charge you a wider lobe for it.

What leakage is not: not noise, not an error, and not something a longer transform fixes. The spacing is 125 Hz, the tone is 62.5 Hz from either bin, and no care with the same 8 ms will put it on a bin. If you can choose the record length, choose one that lands the tone on a bin — that is the whole art of measuring a single tone. If you cannot, you need a window, and you will trade main-lobe width against skirt height for the rest of your life.

![Two records, their energy computed in the time domain and in the frequency domain: an on-bin record whose energy sits in seven bins, and the half-bin record whose energy is in all sixty-four.](assets/plots/dft-parseval.svg)

The last figure keeps this from being a story about loss. Record A is three tones on bins plus a level: $\sum x^2 = 56.6400$ and $\sum |X[k]|^2/N = 56.6400$, in seven bins, identical in exact arithmetic. Record B is the half-bin tone: 32.0000 and 32.0000, differing by $1.4\times10^{-14}$, in all sixty-four bins.

That is Parseval's theorem, and it is why leakage is a redistribution rather than a loss. A leaky spectrum is still a correct budget of the record's power; what leakage costs is **position** — the energy that belonged to one bin is spread across many, so a peak under-reads and an empty neighbour reads as if it were not. Chapter 5 checked the identity on a square wave's harmonics; here it holds for any record at all, including one with nothing periodic in it.

## What it costs

![N² multiplies against the count the FFT will reach, and the N×N twiddle matrix the vectorised route materialises next to the record it transforms.](assets/plots/dft-cost.svg)

One output is a sum of N products and there are N outputs, so the definition costs N² complex multiplies exactly: **4,096** at N = 64 and **1,048,576** at N = 1024.

There is a way to make that look cheap, and you have probably used it: build the N×N matrix whose row $k$ is probe $k$ and multiply it into the record. The count does not change — one entry per input-output pair is N² entries — but the constant does, because the inner loop moves into optimised code. What it really changes is in the second panel: at N = 1024 the twiddle matrix is **16.78 MB** of constants against **16.4 kB** of record, a factor of **1024**. You did not avoid the multiplies; you materialised every one of them as a number in memory.

The ratio to the count chapter 7 will reach is $2N/\log_2 N$: **21.3×** at N = 64, **113.8×** at N = 512, **204.8×** at N = 1024, growing without a knee. The figure checks the obvious escape route and closes it: over the swept sizes the ratio is smallest at the smallest N — **5.33×** at N = 8 — so the curves never cross, and there is no size at which the definition is the cheaper algorithm. There are sizes at which the constant saves you anyway, and a library's matrix multiply really can beat its FFT at N = 8; nobody cares, because at N = 8 both are free.

What matters is the shape of the cost, not its size. **Doubling the record quadruples the work.** The one thing you most want from a spectrum is to resolve two close tones, and resolution is observation time, so you want a longer record — and the price rises as its square. That is the wall this chapter hands over. Chapter 7 does not change the answer: it computes the same N numbers in a different order, for $(N/2)\log_2 N$ multiplies instead of N², out of exactly the probe of this chapter, $W_N = e^{-j2\pi/N}$, the twiddle factor. Everything here stays true when it arrives. Only the price changes.

## What to carry forward

- **The DFT is N correlations, not magic.** $X[k]$ is the record against the probe $e^{-j2\pi kn/N}$, divided by the probe's own sum of squares, N. The probes are orthogonal: 64.000 against itself, 0.000 against its neighbour.
- **Bin $k$ is $k\,f_s/N$ hertz, spacing $f_s/N = 1/T$.** 64 points at 8 kHz is 125 Hz per bin and 8 ms; the same numbers at 16 kHz are 250 Hz per bin and 4 ms, with the peak at bin 8 both times, because a bin counts cycles per record.
- **The record is one period, assumed repeated; the spectrum is one period, repeated every $f_s$** — measured exact to $7.9\times10^{-14}$. If the record is one period of something the transform is exact; if it is not, it is exact about the repetition.
- **A real record has a mirror half.** $X[N-k] = \overline{X[k]}$ to $3.6\times10^{-15}$: magnitude even, phase odd, 33 of 64 bins new. Bins 0 and $N/2$ are real and unpaired — Nyquist holds a sign, not an angle.
- **A tone between bins is a skirt in every bin.** Half a bin off: 19.917 and 20.823, an amplitude read 0.900 of the truth, 81.08% of the power in the pair, and 1.330 still at bin 20. Chapter 8 fixes the shape; a record length that lands the tone on a bin fixes the position.
- **Leakage redistributes energy; it does not lose it.** 56.6400 both ways on a bin, 32.0000 both ways half a bin off, differing by $1.4\times10^{-14}$: a spectrum is always a correct budget and not always a correct position.
- **The cost is N², and it is quadratic in the record length.** 4,096 multiplies at N = 64, 1,048,576 at N = 1024, 204.8× the FFT's 5,120, and the twiddle matrix is 1024× the data. That exponent is what chapter 7 removes.

::: try One tone, one bin, one multiplication
No lab and no licence: a spreadsheet and your phone's tone generator will do, or the tone generator alone if it has a spectrum display.

1. **Type the record.** Put 0 to 63 in column A. In column B write `=COS(2*PI()*8*A2/64)` and fill down. That is 64 samples of a 1 kHz tone at 8 kHz — the record of the first figure, made by hand.
2. **Correlate by hand.** In column C write `=B2*COS(2*PI()*8*A2/64)`, in column D `=-B2*SIN(2*PI()*8*A2/64)`. Sum each column. C comes to **32.000** and D to **0.000**, and that pair is $X[8]$: magnitude 32, phase zero. Then $2|X|/N = 2 \times 32/64$ is the amplitude, 1.000.
3. **Move the probe, not the signal.** Change the 8 in C and D to 9 and the sum collapses to about $10^{-14}$. That is orthogonality, measured at your desk, and it is why one output means one frequency.
4. **Then do the arithmetic the chapter asks for.** Record 1 s of a 1 kHz tone — a phone app, or a piano note — at whatever rate the app reports, and open it in any spectrum viewer. Read the peak bin off the screen and compute $k\cdot f_s/N$ by hand. Trim the record to 0.9 s and repeat: the bin width changes, the peak leaves the bin, and the skirt of the fifth section appears in front of you.
5. **Check the two neighbours.** When the tone sits between bins, the two values should be within a few percent of each other, each about 0.9 of the on-bin reading, and their squares should add to about 81% of it. If they do, the axis is right. If they do not, look at the axis before you look at the signal.
:::

::: optical Where the bins are in a real receiver
**The frequency-domain equaliser is a DFT with a job, and its bin grid is this chapter's mapping.** In a 64 GBd coherent receiver the ADC runs at 2 samples per symbol, a 128 GSa/s stream ([The Coherent Optical Receiver: A DSP Pipeline Tour](coherent-optical-dsp-pipeline.html)), and the dispersion equaliser works on 512-point blocks. So the bin spacing is $128\ \mathrm{GSa/s}/512$ = **250 MHz**, and that one number is the whole frequency axis of the block — the first figure prints it beside the 125 Hz of the bench example, from the same line of arithmetic.

**The phase curve lives in a hundred and twenty-eight bins.** The dispersion chapter's fibre imposes 43.8 rad of quadratic phase across the 32 GHz band ([Chromatic Dispersion and the Frequency-Domain Equaliser](chromatic-dispersion-and-the-fde.html)), and at 250 MHz per bin the band edge is bin 128 of 512. Bin 256 is 64 GHz, which is $f_s/2$ — the Nyquist bin of this chapter, its own mirror, real. The coefficient word is 6 bits of phase, 5.625° per bin, a quantisation of the curve *at this grid*: a bigger block samples the curve more finely, a smaller one writes the same 43.8 rad in fewer, larger steps.

**There is no mirror half to throw away.** The equaliser's input is complex — I and Q are separate photocurrents, not one real record — so the conjugate symmetry does not hold and all 512 bins are independent. The same transform on a real record would return 257 useful bins, and half the coefficient ROM would be a copy. That is why the FDE multiplies all 512 and a real-input spectrum analyser does not.

And the leakage trade-off is not the FDE's, because the FDE is a filter and not an estimator. Its block length is set by the channel memory it must hold — 223 samples of dispersion memory inside 256 usable samples — not by a resolution target, and it does not need a narrow main lobe; it needs the whole chirp inside the block. Which is the thing to carry into chapter 8: leakage and resolution are properties of an *estimate* of a spectrum, and a filter told the answer in advance is not estimating.
:::
