This site is a course in digital signal processing, written by someone who builds firmware for **optical DSP** products — the chips that turn light in a fibre into bits a network can route.

Most DSP teaching starts with the transform and arrives at the application, if it arrives at all. This one runs the other way. Every chapter begins with a picture, derives only what the picture demands, and then ends in the same place: inside a receiver that has to keep up with a 64 GBd optical link.

## What the domain actually is

An optical link carries data by modulating light. At the far end, a photodiode converts that light back into a current, an ADC converts the current into numbers, and from that moment on the signal is **just a sequence of numbers** — and every remaining impairment has to be undone by arithmetic.

That arithmetic is the domain. Chromatic dispersion smears a pulse across tens of symbol periods, so it is inverted with a frequency-domain equaliser built on FFTs. Polarisation drifts and mixes the two received streams, so a blind adaptive butterfly untangles them. The laser has linewidth, so the constellation rotates and a carrier-phase tracker follows it. Fibre is nonlinear, so the distortion depends on the signal's own power.

The reason this is a satisfying corner of engineering is that **the arithmetic is not free**. A 64 GBd link hands you 15.6 ps per symbol. Every equaliser tap costs real multiplies at 128 GSa/s, every extra FFT stage costs power, and every block of buffering costs latency the protocol can see. Correctness is table stakes; the design question is always which correct algorithm fits.

## How this course is shaped

It is arranged in eight parts, and the ordering is deliberate:

- **Beginner** — what a signal is, how sampling loses information, what quantisation costs, and how engineers count in decibels.
- **Intermediate** — the frequency domain, filter design, and multirate processing: the tools every later chapter assumes.
- **Advanced** — estimation, adaptation, and communications DSP: what to do when the channel is unknown and drifting.
- **Specialist** — the optical link itself, and how to make any of it fit in silicon at rate and within power.

The threads are cumulative. A chapter on the fast Fourier transform is not background reading for the dispersion chapter — it is the thing that makes it affordable.

## Who it is for

Embedded and firmware engineers who need the signal-processing half of their system to stop being a black box. People moving into optical, RF or high-speed serial work from a software background. And anyone who has read a DSP textbook, understood it in the moment, and then been unable to reconstruct any of it a month later — which is the failure mode this course is specifically built to avoid, by drawing first and deriving second.
