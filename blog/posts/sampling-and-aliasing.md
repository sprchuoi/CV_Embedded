Sampling looks like the easy part. You have a continuous voltage, you measure it every $T_s$ seconds, and you get a sequence of numbers. Everything after that is arithmetic, and arithmetic is exact.

It is not the easy part. Sampling is the only operation in the entire chain that is **irreversible**, and it is the only one where a mistake cannot be undone by any amount of cleverness downstream. Every filter, every equaliser, every fancy adaptive algorithm operates on the numbers the sampler handed it. If two different physical signals produce the same numbers, no algorithm can tell them apart — because from its point of view there is nothing to tell apart.

This chapter is about that moment, and about the one thing you must do before it.

## The front end, in one picture

![The analogue front end, stage by stage. Each compromise on the left is one the DSP cannot undo.](assets/diagrams/sampling-frontend-chain.svg)

Read that figure from left to right and notice how quickly the compromises accumulate. The anti-alias filter band-limits the signal, which is a deliberate distortion. The track-and-hold freezes a moving target, which is an approximation. The ADC rounds to a finite grid, which is an error. Only the last block — the DSP — is exact.

The rest of this chapter takes the three blocks before the DSP one at a time. This is the one where the decision is permanent.

## What sampling actually does

Take a continuous signal $x(t)$ and multiply it by an impulse train:

$$x_s(t) = x(t) \sum_{n=-\infty}^{\infty} \delta(t - nT_s)$$

That multiplication is the whole of sampling. There is no averaging, no integration, no smoothing — an ideal sampler keeps the value at the instant and throws away everything in between.

The interesting part is what that does in the frequency domain. Multiplication in time is convolution in frequency, and the Fourier transform of an impulse train spaced $T_s$ apart is another impulse train spaced $f_s = 1/T_s$ apart. So the spectrum of the sampled signal is:

$$X_s(f) = f_s \sum_{k=-\infty}^{\infty} X(f - k f_s)$$

::: key The central fact
Sampling does not change the spectrum. It **copies** it, endlessly, at every multiple of the sample rate.

The original spectrum $X(f)$ is still there at $k = 0$. So are exact replicas at $\pm f_s$, $\pm 2f_s$, and so on forever.
:::

Everything that follows is a consequence of that one line.

## Two signals, one set of samples

Here is the uncomfortable demonstration. Sample a 1 Hz sine and an 11 Hz sine at 10 Hz, and look at the numbers you get.

![A 1 Hz and an 11 Hz tone sampled at 10 Hz. The eleven numbers are identical, so the sampled data cannot distinguish them.](assets/diagrams/aliasing-two-tones.svg)

At $n/10$ seconds, the 1 Hz tone has value $\sin(2\pi n/10)$ and the 11 Hz tone has value $\sin(2\pi \cdot 11 n/10)$. But

$$\sin\!\left(2\pi \frac{11n}{10}\right) = \sin\!\left(2\pi n + 2\pi \frac{n}{10}\right) = \sin\!\left(2\pi \frac{n}{10}\right)$$

The extra cycle per sample period is a whole number of turns, so it vanishes. The 11 Hz tone is not *approximately* the same as the 1 Hz tone after sampling. It is exactly the same sequence of numbers.

11 Hz is not a special case. It is what 1 Hz looks like when viewed through a sampler running at 10 Hz.

## The folding rule

The general statement is a fold, and once you have seen it you will never need to look it up again.

![Each Nyquist zone folds back onto the first. A tone at 0.7 fs is indistinguishable from one at 0.3 fs; 1.4 fs behaves like 0.4 fs.](assets/diagrams/nyquist-zones.svg)

The frequency axis is divided into **Nyquist zones**, each $f_s/2$ wide. Zone 1 is $[0, f_s/2]$ and is the only zone the sampler can actually represent. Every other tone is folded into it, and the folding rule is:

$$f_{\text{apparent}} = \left| \left( (f + f_s/2) \bmod f_s \right) - f_s/2 \right|$$

Plot that function and the geometry becomes obvious — it is a triangle wave in frequency, which is why aliasing is sometimes called *frequency folding*.

![The apparent frequency of a tone as a function of its true frequency. The 1 Hz and 11 Hz tones of the earlier figure both land on the same point.](assets/plots/alias-frequency-map.svg)

Two things are worth extracting from this curve.

**Everything above $f_s/2$ is a lie.** Not noise, not attenuation — a lie. A tone at $0.9 f_s$ arrives in Zone 1 pretending to be at $0.1 f_s$, at full amplitude, perfectly coherent. You cannot filter it out afterwards, because afterwards it *is* a legitimate low-frequency signal.

**Only the first zone is unambiguous.** Given the sample rate and the numbers, the only thing you can honestly say is "the true frequency was somewhere in the set $\{f_{\text{apparent}} + k f_s\}$". Choosing among those is a modelling decision, not a signal-processing one.

::: warn The 2× trap
"Nyquist says $f_s > 2B$, so let me run at $2.01B$ and save power."

At exactly $2B$ there is no margin. Real filters have finite roll-off, real clocks drift, and real signals are not perfectly band-limited. The rule in practice is to sample as fast as your converter, power budget and timing recovery allow — not as slowly as the theorem permits.
:::

## What it looks like on a spectrum analyser

The replicate-and-overlap picture is worth seeing directly, because it explains why aliasing is a *sum* rather than a substitution.

![Sampling replicates the spectrum at every multiple of the sample rate. When the signal is wider than fs/2 the replicas overlap and add, corrupting the band you care about.](assets/plots/sampling-spectrum-replication.svg)

In the top panel the signal is band-limited to less than $f_s/2$. The replicas are separate, a filter can isolate the original, and reconstruction is possible.

In the bottom panel the signal is wider than $f_s/2$. The replicas overlap, and inside the overlap region the analyser shows the **sum** of two different parts of the original spectrum. That is the damage: not a missing band, but a band with someone else's energy mixed into it.

## The filter that has to come first

Since everything above $f_s/2$ is going to fold into the band you care about, the obvious fix is to remove it before it gets the chance.

![Without an anti-alias filter the interferer folds into the signal band. With one, it is attenuated before the sampler ever sees it.](assets/diagrams/antialias-before-and-after.svg)

The placement is the whole point. An anti-alias filter must act on the **continuous** signal, before the sampler. After sampling, the interferer and the wanted signal are the same kind of object — numbers in a buffer — and no digital filter can separate them.

This gives the two constraints that actually determine the filter:

| Constraint | What sets it |
|---|---|
| Passband edge $f_p$ | Must pass the entire signal of interest, with acceptable ripple |
| Stopband edge $f_{st}$ | Must start attenuating before $f_s - f_p$, because that is what folds onto $f_p$ |
| Transition width | $\Delta f = f_{st} - f_p$ — the expensive number |
| Stopband attenuation | Set by how much alias energy your system can tolerate |

Note the asymmetry in that table. The stopband has to begin before $f_s - f_p$, not before $f_s/2$. A signal component at $f_s - f_p + \epsilon$ folds to $f_p - \epsilon$, right on top of your highest wanted frequency. This is why the anti-alias filter is always harder than it first appears, and why oversampling is so attractive: doubling $f_s$ doubles the room the filter has to roll off.

::: try Order of operations
If you take one thing from this chapter, make it this. In a real receiver the order is fixed:

**band-limit → sample → quantise → process**

Any architecture that samples first and filters later has already lost. The only question is how much.
:::

## Getting the signal back

Reconstruction is the inverse operation, and the ideal interpolator is a sinc:

$$x(t) = \sum_{n=-\infty}^{\infty} x[n] \, \mathrm{sinc}\!\left(\frac{t - nT_s}{T_s}\right)$$

![Ideal sinc reconstruction reproduces the original signal exactly; a zero-order hold leaves a visible staircase and a measurable error.](assets/plots/sinc-reconstruction.svg)

The sinc is not a practical filter — it is infinite, non-causal, and its impulse response decays as $1/t$. Every real DAC uses a zero-order hold and then cleans up the resulting droop and images with an analogue filter. But the picture is the right mental model: reconstruction is *interpolation*, and the samples are not the signal. They are the coefficients you rebuild it from.

## Quantisation, in one page

Sampling discretises time. Quantisation discretises amplitude, and it is a genuinely different kind of error: unlike aliasing, it is bounded, it is roughly uncorrelated with the signal, and it can be averaged down.

![A 3-bit quantiser and its error, alongside the SNR that an ideal N-bit converter achieves.](assets/plots/quantization-noise.svg)

For an ideal $N$-bit converter with a full-scale sinusoid input, and treating the error as uniform white noise over one least-significant bit, the signal-to-noise ratio works out to:

$$\mathrm{SNR} = 6.02\,N + 1.76 \ \text{dB}$$

The 6 dB per bit is worth internalising. It means one extra bit buys you a factor of two in amplitude, which is exactly the same as halving your noise — and it costs you twice the comparators, twice the power, and often half the speed.

::: note Effective number of bits
The formula describes an *ideal* converter. Real ones have comparator offsets, clock jitter, thermal noise and non-linearity, so the datasheet number is optimistic.

$\mathrm{ENOB} = \dfrac{\mathrm{SINAD} - 1.76}{6.02}$

A converter sold as "8-bit" at 100+ GSa/s typically delivers 5 to 5.5 effective bits. Design to the ENOB, not the label.
:::

## In the optical link

::: optical Where this shows up in a coherent receiver
A 64 GBd coherent link runs its ADCs at **2 samples per symbol** — 128 GSa/s — and that choice is almost entirely about this chapter.

**The anti-alias filter is not a component you specify.** It is the combined response of the transimpedance amplifier, the ADC's input network, and the ADC's own sample-and-hold bandwidth. Nothing else. If that combined bandwidth extends meaningfully past 64 GHz, out-of-band noise and neighbouring channels fold straight into the signal band, and there is no digital fix. A large part of the analogue front-end design effort goes into making that roll-off well-behaved rather than fast.

**Why 2 Sa/symbol and not 1.** At exactly one sample per symbol, the sampler must land precisely on the peak of every pulse. It never does — timing recovery always has residual jitter, and the sampling instant that maximises one symbol is wrong for its neighbours. Two samples per symbol gives the fractionally-spaced equaliser a half-symbol grid, so it can synthesise *any* sampling phase as a weighted combination of the two. The equaliser stops being a filter and starts being an interpolator, and timing recovery stops being a hardware problem.

**What 2 Sa/symbol does not buy.** Doubling the rate does not halve the quantisation noise in band. At 128 GSa/s the converter's Nyquist bandwidth is 64 GHz, which is precisely the signal bandwidth — so there is essentially no oversampling gain, and the full quantisation noise floor lands in band. With 5.5 ENOB that floor sits around 35 dB SNR, which is comfortably below the 15-25 dB OSNR that a real link delivers. Quantisation is not the limit. Aliasing, and the analogue bandwidth that causes it, is.

**And the PAM4 case.** In a directly detected PAM4 link — an active electrical cable, or a short-reach IM-DD module — there is no coherent front end to band-limit anything. The ADC sees whatever the channel and the photodiode deliver. Four-level signalling also means the effective SNR is roughly 9.5 dB worse than NRZ for the same average power, because the levels are three times closer together. That is a system operating much nearer its quantisation floor, and anti-alias filtering stops being a detail and starts being the design.
:::

## What to carry forward

- Sampling **replicates** the spectrum at every multiple of $f_s$. Aliasing is replicas overlapping and adding.
- Frequency content above $f_s/2$ is folded into the first Nyquist zone and is indistinguishable from legitimate in-band signal. It cannot be removed digitally.
- The anti-alias filter acts on the continuous signal, before the sampler. Its stopband must begin before $f_s - f_p$, not $f_s/2$.
- An ideal $N$-bit converter gives $6.02N + 1.76$ dB, and real ones give less. Design to ENOB.
- Reconstruction is sinc interpolation. The samples are coefficients, not the signal.

The next chapter takes the same signal and looks at it from the other side: instead of asking what frequencies are present, it builds the machinery that answers the question exactly — the Fourier transform, the DFT, and the FFT that makes it affordable.
