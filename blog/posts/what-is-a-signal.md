Ask ten engineers what a signal is and most will name a physical quantity: a voltage, a current, the light in a fibre. Those answers aim at the wrong object. A signal is not the voltage; it is the *description* of how the voltage changes.

Formally, a signal is a function, and a function has two parts. The **domain** is what varies. The **range** is what is measured. Write $x(t)$ and you have not written a voltage; you have written a rule that returns a number for every instant $t$ you ask about.

I write DSP for coherent optical receivers, where the quantity being described is the optical field and the description is eight-bit numbers arriving at 128 GSa/s. Both get called "the signal" in the same meeting; keeping them apart is the first useful habit this course can give you.

This chapter is the vocabulary, and it is deliberately easy. Everything after it is a variation on it.

## The domain and the range

Change the domain and the signal changes, even when the rule underneath is identical.

The domain is usually time, but it need not be. A photograph is a signal whose domain is two spatial dimensions. A spectrum is a signal whose domain is frequency. The samples in a processor have a domain that is the integer index $n$. The range is whatever the measurement produced.

| Description | Domain | Range |
|---|---|---|
| Photodiode current | time | amperes |
| Spectrum analyser trace | frequency | power per hertz |
| Stored samples | integer index $n$ | converter codes |

Two consequences save time later.

A **waveform** is a drawing; the **signal** is the function it depicts. One drawing can describe a function with no physical quantity behind it at all, which is what a simulation is.

And the description is not the quantity. A clipped ADC output is a bad description; it does not follow that the light was bad. The reverse holds too — when a link misbehaves, ask first which of the two is broken.

::: key Start every argument here
Name the domain and the range before you argue about a signal.
Most disagreements about DSP are two people naming different objects.
:::

## Two questions, four worlds

There are two independent questions here, and beginners routinely collapse them into one.

1. Is the **domain** continuous or discrete? Continuous time means a value at every instant; discrete time means values only at integer indices $n$.
2. Is the **range** continuous or discrete? A continuous range can take any value in an interval; a discrete range is restricted to a finite set of levels.

Two questions, two answers each: four kinds of signal. Figure 1 draws one of each.

![The four-way classification. Sampling makes the domain discrete, quantising makes the range discrete, and the two decisions are independent.](assets/diagrams/signal-four-domains.svg)

- **Continuous time, continuous amplitude** — an *analogue* signal. The physical world: a photodiode's load voltage, the field in a fibre.
- **Discrete time, continuous amplitude** — a *sampled* signal. A sample-and-hold output, or the samples at an ADC input before they are rounded. Times on a grid; values not.
- **Continuous time, discrete amplitude** — a *quantised analogue* signal. A PWM laser drive, or a PAM waveform in the analogue domain: every instant has a value, but only a few.
- **Discrete time, discrete amplitude** — a *digital* signal. Both axes are on a grid, and this is the only combination a processor can hold.

::: warn Digital is not a synonym for sampled
A sampled signal can still take any value, and arithmetic on it can be exact.
Round it to a code and you have added a second, quite different kind of error.
:::

An 8-bit ADC at 128 GSa/s has a digital output; its input, and the sample-and-hold feeding it, are analogue.

## The elementary signals

Six shapes cover most of the vocabulary. Figure 2 draws them with the numbers that pin each one down.

![The elementary waveforms with the numbers that define them. The impulse is the one shape missing, because it has no width to draw.](assets/plots/signal-elementary-waveforms.svg)

**The sinusoid** is three numbers: an amplitude $A$, a frequency $f_0$ and a phase $\phi$.

$$x(t) = A\sin(2\pi f_0 t + \phi)$$

The figure's sinusoid has $A = 1$, $f_0 = 0.5$ Hz and a period of 2 s; its phase of $\pi/3$ means it arrives 0.33 s early. Two traps live here. The angular frequency $\omega = 2\pi f$ is not the frequency $f$, and mixing the two is a factor-of-$2\pi$ bug that survives review because the plot still looks right. And amplitude is a peak, not an RMS value: a 1 V sine delivers $A^2/2 = 0.5$ W into 1 Ω, not 1 W.

**The complex exponential** $e^{j\omega t}$ is one signal, not two. It is a point rotating about the origin at a constant rate; the two curves in the figure are its coordinates — the shadows it casts on the real and imaginary axes.

$$e^{j\omega t} = \cos\omega t + j\sin\omega t$$

Calling it "a cosine and a sine" is what makes I/Q confusing later: it invites you to treat two views of one object as two.

**The step** $u(t)$ separates two values at a single instant. An ideal step has infinite bandwidth, so a real one has a rise time; that rise time is about $0.35/B$, often the first bandwidth number a link budget needs.

**The rectangular pulse** is two numbers, a height and a width. The figure's is 1.0 high and 1.5 s wide, so its energy is $1.0^2 \times 1.5 = 1.5$ — the height alone tells you nothing.

**The decaying exponential** has exactly one number, the time constant $\tau$. With $\tau = 0.6$ s, one time constant later the value is $1/e = 0.368$ of where it started, and by $5\tau = 3$ s it is done. Every switch-on transient has this shape.

**The impulse** is the one shape the figure cannot draw, because it has no width. In discrete time it is the easiest signal here: 1 at $n = 0$, 0 everywhere else. It is defined by what it does in a sum, where it picks out one term and discards the rest — the basis of the impulse-sum view, and of convolution in chapter 10.

The last panel adds a **chirp**: a sinusoid whose frequency climbs.

::: try Reading a datasheet
Take the next converter datasheet you open: sample rate and bits place its output in exactly one of Figure 1's four worlds.
:::

## The same signal, written down twice

Notation does real work in Figure 3. Round brackets, as in $x(t)$, mean a continuous domain. Square brackets, as in $x[n]$, mean the integer index $n$.

![One two-tone signal, written twice: a curve with a value at every instant, and the 16 or 64 numbers a sampler would keep.](assets/plots/signal-continuous-vs-discrete.svg)

The figure takes one signal — a 2 Hz sine plus a 5 Hz sine at half the amplitude, over one second — and shows it both ways. At 16 samples per second there are sixteen numbers; at 64 there are sixty-four. The list is not a worse drawing of the curve. It is a different kind of object, and the values in between are simply not in it.

That gap is the whole business of the next chapter. Anything you claim about the signal between samples is an assumption you brought with you, not a measurement you made; the assumption that makes reconstruction possible is band-limitedness.

One practical warning, because it costs people weeks. The index $n$ carries no seconds. A frequency axis built from $n$ alone is wrong by exactly the sample rate, and more spectra have shipped with the wrong axis than anyone would like to admit.

## Four ways to write the same thing

Take four numbers: 2.0, 3.0, 1.0 and 0.5. Figure 4 shows four descriptions of the signal they define.

![Four descriptions of the same four numbers: a graph, a table, a vector, and a sum of scaled impulses.](assets/diagrams/signal-four-views.svg)

1. **A graph** — what a human reads.
2. **A table** — what goes in a lab notebook, with an index column.
3. **A vector** — what a processor holds. $x = [2.0,\ 3.0,\ 1.0,\ 0.5]^{\mathsf{T}}$, four numbers, fixed length. The object has no time axis; the sample period lives in a register beside it.
4. **A sum of scaled impulses** — what the mathematics uses. $x[n] = 2\delta[n] + 3\delta[n-1] + 1\delta[n-2] + 0.5\delta[n-3]$.

These are not four approximations but one object in four notations, each making a different question easy.

The fourth view looks like notation for its own sake until you ask what a linear system does to it. If the response to one impulse is known, linearity and time invariance give the response to every scaled, shifted copy, and the whole response is the sum of those. That is convolution, and it is chapter 10.

The third view is the one that ships. A vector is subject to everything a computer does to vectors: finite word length, fixed buffers, an index that runs off the end. Most catastrophic DSP bugs are not mathematical but a vector of the wrong length or the wrong scaling.

## Deterministic and random

Some signals can be written down. Hand the sinusoid a time and it returns $x(t)$ with no room for argument. Call those deterministic.

Others cannot. Thermal noise in a transimpedance amplifier, ASE beat noise in a coherent receiver, the jitter that smears an eye diagram — no formula predicts the next sample. They can still be described, but statistically: a distribution, a mean, an autocorrelation, a power spectral density. One captured record is a *realisation*, not the signal.

This matters, because the machinery of the next sixteen chapters is deterministic. Fourier transforms, convolution and the z-transform are stated for functions in the ordinary sense, and they still apply to random signals — but on average, in the mean-square sense, not sample by sample. A finite noise record has a DFT; its periodogram does not settle. Random signals get their own theorems in chapter 18.

The honest other half: the deterministic case is not a toy. Every receiver block is designed and tested on deterministic inputs, and much of the engineering is keeping noise small enough that the description stays useful.

## Energy and power

Two quantities decide which theorems you may use, and the difference between them is the difference between a pulse and a carrier.

::: math The two definitions
$$E = \int_{-\infty}^{\infty} |x(t)|^2\,dt \qquad \text{or} \qquad E = \sum_{n=-\infty}^{\infty} |x[n]|^2$$
$$P = \lim_{T\to\infty} \frac{1}{2T}\int_{-T}^{T} |x(t)|^2\,dt \qquad \text{or} \qquad P = \lim_{N\to\infty} \frac{1}{2N+1}\sum_{n=-N}^{N} |x[n]|^2$$
:::

A signal with finite, non-zero energy is an **energy signal**. Finite energy spread over infinite time averages to zero, so every energy signal has $P = 0$. A signal whose energy grows without limit but whose average rate does not is a **power signal**. The classes do not overlap: a finite-energy signal has zero average power, and a finite-power signal has infinite energy.

Figure 5 shows one of each. The Gaussian pulse above starts and ends, and its running integral settles on 1.2533. The sine below is still running at $t = 20$ s: its running energy has reached 10, while energy divided by elapsed time settles on 0.5000 — $A^2/2$ for unit amplitude.

![An energy signal above a power signal. The pulse's running energy settles; the sine's keeps climbing while its average settles.](assets/plots/signal-energy-vs-power.svg)

| Signal | Energy | Average power | Class |
|---|---|---|---|
| Impulse $\delta[n]$ | 1 | 0 | energy |
| Rectangular pulse, height 1, width 1.5 s | 1.5 | 0 | energy |
| Decaying exponential $e^{-t/\tau}u(t)$ | $\tau/2$ | 0 | energy |
| Sinusoid, amplitude $A$ | infinite | $A^2/2$ | power |
| Unit step | infinite | $1/2$ | power |
| Zero-mean stationary noise | infinite | variance | power |

Why care? Because the theorems differ. Energy signals have a Fourier transform in the ordinary sense and obey Parseval's theorem: energy computed in time equals energy computed in frequency. Power signals do not — the transform integral diverges — so they are characterised by an autocorrelation and a power spectral density instead, which is where chapter 18 begins. Apply an energy theorem to a power signal and the spectrum never settles.

A practical sting in the same tail: a spectrum analyser measures power, while the FFT of a finite record measures something energy-like. That is why transform amplitudes need normalising and the window changes the number you read.

## Periodicity and symmetry

Two structural properties appear in almost every frequency-domain result, so they are worth naming now.

A signal is **periodic** with period $T_0$ if $x(t) = x(t + T_0)$ for every $t$; the smallest such $T_0$ is *the* period, and $f_0 = 1/T_0$ is the fundamental. A periodic signal that is not identically zero has infinite energy and finite average power, so it is always a power signal.

A signal is **even** if $x[-n] = x[n]$ and **odd** if $x[-n] = -x[n]$, and every signal is the sum of one of each:

$$x_e[n] = \frac{x[n] + x[-n]}{2}, \qquad x_o[n] = \frac{x[n] - x[-n]}{2}$$

Cosine is even, sine is odd, and a sinusoid with a phase shift is a mixture — which is precisely what a phase shift is. A real even signal has only cosine terms in its Fourier series; a real odd signal only sine terms. For any real signal, the spectrum is conjugate-symmetric, $X[-k] = \overline{X[k]}$, so half the bins are redundant: a factor of two in work and memory, free.

One warning belongs with periodicity. The DFT assumes its record is one period of a periodic signal. If the record holds 100.5 periods, the wrap-around discontinuity has energy at every frequency and every bin is contaminated. That is leakage, chapter 8.

## What to carry forward

- A signal is a function. Name its domain and its range before you name anything else.
- Two independent questions — continuous or discrete in time, and in amplitude — give four kinds of signal; only discrete/discrete is digital, and only discrete/discrete is what a processor holds.
- The elementary signals: a sinusoid (three numbers), a complex exponential (one point, two views), a step, an impulse, a rectangular pulse, a decaying exponential.
- Deterministic signals can be written down; random ones are described statistically, with their own theorems in chapter 18.
- Finite energy means zero average power; finite power means infinite energy. The theorems differ, so know which class you are in.
- The same signal is a graph, a table, a vector and a sum of impulses; the vector runs, the impulse sum enables convolution in chapter 10.

::: optical Where this shows up in an optical link
**The receiver chain is the four-way classification, made physical.**
Light in the fibre is continuous in time and amplitude — quadrant one.
The photodiode turns it into a photocurrent, still continuous in both.
The sample-and-hold makes time discrete and leaves amplitude on a continuum.
It looks continuous on a scope; the information is a list of samples.
The ADC rounds each sample to a code, and the signal is discrete in both.
Everything after that is arithmetic.

**That conversion is the last point at which a mistake is recoverable.**
An impairment present in the photocurrent can still be argued with.
Once it is a code, it is indistinguishable from signal.
Sample rate, full scale and word length are decisions you do not get to revisit.
That is the motivation for this first part of the course.

**And here signal-versus-description stops being philosophical.**
64 GBd PAM4 is not the light; it is a description of the light's intensity.
Recovering that description is the receiver's whole job.
At two samples per symbol that is 128 GSa/s, and at eight bits 128 GB/s per polarisation.
Two polarisations put roughly a quarter of a terabyte per second into the DSP.

**Every impairment the later chapters attack is a transformation of that function.**
Dispersion is a convolution of the field with a channel response.
Carrier phase noise is a multiplication by a slowly turning phasor.
Quantisation is a staircase applied to the range.
They are coupled, and that is what makes the domain hard.
The equaliser that undoes dispersion also rotates the constellation it adapts on.
The phase estimator wants a constellation that is not dispersing.
Untangling the two is chapters 29 to 32.
:::
