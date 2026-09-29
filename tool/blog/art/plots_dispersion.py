"""Computed figures for the chromatic-dispersion / FDE chapter.

Five numpy/matplotlib figures for the chapter on chromatic dispersion and the
frequency-domain equaliser. They are simulations, not sketches, and every number
annotated on a figure is measured in this module:

    dispersion-chirp                 one pulse in, one linear chirp out
    dispersion-time-domain-taps      the T-spaced FIR that would be needed instead
    fde-residual-vs-blocksize        the accuracy/cost/latency curve of the FDE
    dispersion-penalty-vs-reach      what the FDE buys, in dB and in km
    fde-coefficient-quantisation     how many coefficient phase bits are enough

Conventions are lifted from :mod:`tool.blog.art.plots_coherent` so the two
chapters describe the same link:

* ``H(f) = exp(j*pi*D*lambda^2*L*f^2/c)`` with ``D`` in ps/(nm*km) converted as
  ``D * 1e-6`` s/m^2, ``lambda = 1550 nm``, ``c = 2.998e8 m/s``, and ``L`` in
  metres.  1700 ps/nm is 1.7 s/m of accumulated dispersion -- the 100 km case
  the whole blog uses.
* 64 GBd, 2 samples/symbol (128 GSa/s), raised-cosine beta = 0.1, and the same
  256-sample (128 symbol) bulk delay that makes the all-pass causal.  Symbol
  ``k`` is read at output sample ``BULK_DELAY + 2k``.
* The transmitter pulse is a raised-cosine spectrum, so it is exactly Nyquist:
  back-to-back there is no ISI, and everything the figures measure is dispersion.

Modelling notes, because the numbers they produce are the chapter's argument:

* **Dispersion memory.**  Sampling ``H(f)`` on a grid band-limits the inverse
  response to +/-f_s/2, and the band-limited chirp spans
  ``|D*L|*lambda^2*f_s/c`` samples.  At 1700 ps/nm and 128 GSa/s that is 223
  samples = 112 symbol periods = 1.74 ns, and it is the length a block must
  hold.  It is measured here, not quoted.
* **The block FDE** of figures 3 and 4 is a real overlap-save equaliser: an
  FFT of ``B`` samples, 50 % overlap (keep the previous ``B/2``, ingest ``B/2``
  new, emit the last ``B/2``), and coefficients equal to ``H*(f)`` sampled on
  the block's own DFT grid, times a linear phase that puts the (non-causal)
  inverse chirp in the causal half of the block.  The equaliser therefore delays
  by ``B/4`` samples, and every symbol is read back at ``BULK_DELAY + 2k + B/4``.
  What is left over is aliasing of the long chirp into the short block, measured
  as the EVM of the equalised symbols against the transmitted ones.
* **Coefficient quantisation** keeps ``|H*[k]| = 1`` exactly and
  rounds only the phase, uniformly over ``[-pi, pi)``, to ``2**w`` levels.  That
  is a phase-only coefficient word, the representation a designer picks when the
  all-pass is already known to be flat.
* **The penalty model** is a model, not a measurement, and the figure
  says so.  The gain-normalised distortion power ``D`` (the ISI energy outside
  the main tap, over the main tap -- the chapter's "ISI to main tap") is treated
  as additive Gaussian noise against a 20 dB reference link:
  ``penalty = 10*log10(1 + 10**(20/10) * D)``.  A link is called unusable when
  that penalty reaches 3 dB.
* The penalty curve for the practical compensator is *not* invented: it is the
  same block-FDE simulation as the block-size figure, re-run at each reach, with
  a 512-sample block plus the 6-bit coefficient error measured in the quantisation figure.
"""

from __future__ import annotations

import textwrap

import numpy as np

from . import plotstyle as P

# --------------------------------------------------------------------------- #
# the link the figures describe
# --------------------------------------------------------------------------- #

C_LIGHT = 2.998e8              # m/s
LAMBDA = 1550e-9               # m, the C-band carrier
BAUD = 64e9                    # Bd
SPS = 2                        # samples per symbol
FS = SPS * BAUD                # 128 GSa/s
DISPERSION = 17.0              # ps/(nm*km), typical single-mode fibre
CD_PS_PER_NM = 1700.0          # the 100 km reference case
BETA = 0.1                     # raised-cosine roll-off
BULK_DELAY = 256               # samples; the coherent chapter's convention
N_SYMBOLS = 8192               # 16-QAM symbols measured per record
PAD_SYMBOLS = 4096             # zero symbols either side (>= the memory)
RNG_SEED = 0

FDE_BLOCK = 512                # the practical compensator's block, in samples
FDE_PHASE_BITS = 6             # ... and its coefficient phase word
OSNR_REF_DB = 20.0             # reference link OSNR for the penalty model
UNUSABLE_DB = 3.0              # penalty at which a link is called unusable

TAP_LEVELS_DB = (-20.0, -30.0, -40.0)
BLOCK_SWEEP = (32, 64, 128, 256, 512, 1024, 2048, 4096)


# --------------------------------------------------------------------------- #
# physics helpers
# --------------------------------------------------------------------------- #


def dl_si(ps_per_nm: float) -> float:
    """Accumulated dispersion in s/m.  ``1 ps/nm`` is exactly ``1e-3 s/m``."""
    return ps_per_nm * 1e-3


def cd_phase(f, ps_per_nm: float):
    """Quadratic spectral phase of chromatic dispersion, in radians."""
    return np.pi * dl_si(ps_per_nm) * LAMBDA ** 2 * f ** 2 / C_LIGHT


def chirp_rate_ghz_per_ps(ps_per_nm: float = CD_PS_PER_NM) -> float:
    """``|df_inst/dt|`` of the dispersed pulse, in GHz/ps.

    Stationary phase on ``phi(f) = pi*beta*f**2`` with ``beta = D*L*lambda^2/c``
    maps frequency to time as ``t = -beta*f``, so the sweep rate is ``1/beta``.
    """
    beta = dl_si(ps_per_nm) * LAMBDA ** 2 / C_LIGHT
    return 1.0 / beta / 1e9 / 1e12


def dispersion_memory_samples(ps_per_nm: float, fs: float = FS) -> float:
    """Length of the band-limited inverse chirp, in samples at ``fs``.

    The group delay maps the sampled band edge ``fs/2`` to
    ``|D*L|*lambda^2*(fs/2)/c`` seconds, so the full peak-to-peak walk across
    the sampled band is ``|D*L|*lambda^2*fs/c`` seconds -- and that many sample
    periods, which is the memory a block has to hold.
    """
    return dl_si(ps_per_nm) * LAMBDA ** 2 * fs / C_LIGHT * fs


def rc_spectrum(f):
    """Raised-cosine spectrum, exactly zero outside ``+/-(1+beta)*baud/2``."""
    a = np.abs(f)
    h = np.zeros(a.shape, dtype=float)
    h[a <= (1.0 - BETA) * BAUD / 2.0] = 1.0
    roll = (a > (1.0 - BETA) * BAUD / 2.0) & (a < (1.0 + BETA) * BAUD / 2.0)
    if np.any(roll):
        x = (a[roll] - (1.0 - BETA) * BAUD / 2.0) / (BETA * BAUD)
        h[roll] = 0.5 * (1.0 + np.cos(np.pi * x))
    return h


def qam_symbols(count: int, order: int, rng: np.random.Generator) -> np.ndarray:
    """``count`` random ``order``-QAM symbols at unit average symbol energy."""
    side = int(round(order ** 0.5))
    raw = np.arange(-(side - 1), side, 2, dtype=float)
    levels = raw / np.sqrt(2.0 * np.mean(raw ** 2))
    return (levels[rng.integers(0, side, count)]
            + 1j * levels[rng.integers(0, side, count)])


def _link(tx: np.ndarray, ps_per_nm: float, *, pad: int, bulk: int = BULK_DELAY):
    """Shape, disperse and return ``(shaped, dispersed)`` at ``SPS`` samples/symbol.

    The ``SPS`` factor on the shaping filter is the interpolation gain of
    zero-insertion, exactly as in the coherent chapter: without it the
    symbol-instant samples come back ``SPS`` times too small.
    """
    n_total = tx.size + 2 * pad
    symbols = np.zeros(n_total, dtype=complex)
    symbols[pad:pad + tx.size] = tx
    wave = np.zeros(n_total * SPS, dtype=complex)
    wave[::SPS] = symbols

    f = np.fft.fftfreq(wave.size, d=1.0 / FS)
    shaped = np.fft.ifft(np.fft.fft(wave) * SPS * rc_spectrum(f))
    disp = (np.exp(1j * cd_phase(f, ps_per_nm))
            * np.exp(-2j * np.pi * f * (bulk / FS)))
    dispersed = np.fft.ifft(np.fft.fft(shaped) * disp)
    return shaped, dispersed


def _fde_coefficients(f_block, ps_per_nm: float, delay: int,
                      phase_bits: int | None = None):
    """The overlap-save coefficient vector, optionally phase-quantised.

    Magnitude is exactly 1 either way: only the phase word is quantised, which is
    the representation a designer picks for an all-pass that is flat by
    construction.  The chirp and the delay ramp are rounded together, because
    together they are what the coefficient ROM holds.
    """
    phase = (-cd_phase(f_block, ps_per_nm)
             - 2.0 * np.pi * f_block * (delay / FS))
    if phase_bits is None:
        return np.exp(1j * phase)
    step = 2.0 * np.pi / 2 ** phase_bits
    return np.exp(1j * np.round(phase / step) * step)


def _block_fde(x: np.ndarray, ps_per_nm: float, block: int, *,
               phase_bits: int | None = None):
    """Overlap-save FDE of ``x`` with the inverting response sampled on ``block``.

    Returns ``(y, delay)``: ``y`` is the equalised record and ``delay = block/4``
    is the causal shift the coefficients carry, so symbol *k* sits at output
    sample ``BULK_DELAY + 2k + delay``.  With ``phase_bits`` the coefficient
    vector has its phase rounded to that many bits.
    """
    delay = block // 4
    f_block = np.fft.fftfreq(block, d=1.0 / FS)
    coef = _fde_coefficients(f_block, ps_per_nm, delay, phase_bits)
    step = block // 2
    y = np.zeros(x.size, dtype=complex)
    for start in range(0, x.size - block + 1, step):
        y[start + step:start + block] = np.fft.ifft(
            np.fft.fft(x[start:start + block]) * coef)[step:]
    return y, delay


def _evm_power(measured: np.ndarray, reference: np.ndarray) -> float:
    err = measured - reference
    return float(np.mean(np.abs(err) ** 2) / np.mean(np.abs(reference) ** 2))


def _db(power: float) -> float:
    return 10.0 * np.log10(power)


def _record(order: int = 16, n_symbols: int = N_SYMBOLS, pad: int = PAD_SYMBOLS,
            seed: int = RNG_SEED):
    rng = np.random.default_rng(seed)
    return qam_symbols(n_symbols, order, rng)


def _symbol_positions(count: int, pad: int, delay: int = 0) -> np.ndarray:
    return BULK_DELAY + SPS * (pad + np.arange(count)) + delay


def _interior(pos: np.ndarray, size: int, margin: int) -> np.ndarray:
    """Symbols whose sample sits clear of both record edges and the block edges."""
    return (pos >= margin) & (pos <= size - 1 - margin)


def block_residual_power(ps_per_nm: float, block: int = FDE_BLOCK, *,
                         order: int = 16, n_symbols: int = N_SYMBOLS,
                         pad: int = PAD_SYMBOLS, seed: int = RNG_SEED,
                         phase_bits: int | None = None) -> float:
    """EVM power left by a ``block``-sample overlap-save FDE at ``ps_per_nm``.

    The reference is the transmitted symbol sequence, which in this link *is*
    the exactly equalised signal: an all-pass times its own conjugate is flat, so
    back-to-back the decision samples are the symbols themselves.  Edge symbols
    are dropped on both sides.  ``phase_bits`` quantises the coefficient phase.
    """
    tx = _record(order, n_symbols, pad, seed)
    _, dispersed = _link(tx, ps_per_nm, pad=pad)
    y, delay = _block_fde(dispersed, ps_per_nm, block, phase_bits=phase_bits)
    pos = _symbol_positions(n_symbols, pad, delay)
    keep = _interior(pos, y.size, max(block, 8 * SPS))
    return _evm_power(y[pos[keep]], tx[keep])


def quantisation_power(bits: int, ps_per_nm: float = CD_PS_PER_NM, *,
                       block: int = FDE_BLOCK, order: int = 16,
                       n_symbols: int = N_SYMBOLS, pad: int = PAD_SYMBOLS,
                       seed: int = RNG_SEED) -> float:
    """EVM power left by a ``block``-point FDE whose phase word is ``bits`` wide.

    This is the real object: the ``block`` coefficients of the overlap-save FDE
    of figures 3 and 4, with ``|H*[k]| = 1`` and the phase rounded uniformly to
    ``2**bits`` levels.  It therefore includes the block's own aliasing floor.
    """
    return block_residual_power(ps_per_nm, block, order=order,
                                n_symbols=n_symbols, pad=pad, seed=seed,
                                phase_bits=bits)


def penalty_db(distortion_power: float, *, osnr_db: float = OSNR_REF_DB) -> float:
    """OSNR penalty of a distortion treated as additive noise (a model)."""
    return 10.0 * np.log10(1.0 + 10.0 ** (osnr_db / 10.0) * distortion_power)


def channel_taps(ps_per_nm: float, *, pad: int = PAD_SYMBOLS, half: int = 1200):
    """Symbol-spaced channel seen by one isolated symbol (impulse in, taps out)."""
    tx = np.zeros(1, dtype=complex)
    tx[0] = 1.0
    _, dispersed = _link(tx, ps_per_nm, pad=pad)
    pos = BULK_DELAY + SPS * (pad + np.arange(-half, half + 1))
    return dispersed[pos]


def isi_power(taps: np.ndarray) -> float:
    """Gain-normalised distortion power: ISI energy over main-tap energy.

    This is the chapter's "ISI to main tap" figure -- the distortion at the
    decision point after the AGC has scaled the main tap back to unity.
    """
    peak = int(np.argmax(np.abs(taps)))
    main = abs(taps[peak]) ** 2
    return float((np.sum(np.abs(taps) ** 2) - main) / main)


# --------------------------------------------------------------------------- #
# the T-spaced FIR an inverting response would need
# --------------------------------------------------------------------------- #


def _circular_centre_window(h: np.ndarray, ntaps: int) -> np.ndarray:
    """Keep ``ntaps`` taps of a circular impulse response, symmetric about tap 0.

    ``H*(f)`` is even in frequency, so its impulse response is symmetric about
    the tap at index 0 (the equaliser's centre tap) -- its equal maxima sit 21
    taps either side, where the chirp's brightest Fresnel zone lands.  The
    truncation window has to be symmetric about the centre, not about whichever
    of the twin maxima the FFT happened to round up: centring on a maximum cuts
    the other half of the response away and measures a far worse residual.
    """
    n = h.size
    half = ntaps // 2
    idx = np.arange(-half, half + 1) % n
    out = np.zeros(n, dtype=complex)
    out[idx] = h[idx]
    return out


def truncation_residual_power(ps_per_nm: float, ntaps: int, *,
                              n: int = 1 << 13) -> float:
    """Residual ISI power of a symbol-spaced FIR truncated to ``ntaps`` taps.

    Measured, not estimated from a rule of thumb: the truncated equaliser is
    convolved with the channel on the symbol-rate grid and the energy outside the
    main tap of the combined response is the error.
    """
    f = np.fft.fftfreq(n, d=1.0 / BAUD)
    h_eq = np.fft.ifft(np.exp(-1j * cd_phase(f, ps_per_nm)))
    combined = np.fft.ifft(
        np.fft.fft(_circular_centre_window(h_eq, ntaps))
        * np.exp(1j * cd_phase(f, ps_per_nm)))
    main = float(np.max(np.abs(combined)) ** 2)
    return float((np.sum(np.abs(combined) ** 2) - main) / main)


def taps_for_residual(ps_per_nm: float, level_db: float, *,
                      candidates=None) -> int:
    """Smallest odd tap count whose measured residual beats ``level_db``."""
    if candidates is None:
        candidates = list(range(5, 401, 4)) + list(range(401, 3001, 16))
    for ntaps in candidates:
        if _db(truncation_residual_power(ps_per_nm, ntaps)) <= level_db:
            return ntaps
    return candidates[-1]


def td_macs_per_symbol(ntaps: int, polarisations: int = 2) -> float:
    """Real multiplies per symbol for a T-spaced complex FIR (4 per complex MAC)."""
    return 4.0 * ntaps * polarisations


def fde_mults_per_sample(block: int, polarisations: int = 2) -> float:
    """Real multiplies per output sample for an overlap-save block FDE.

    Per block of B outputs and per polarisation: a forward and an inverse
    transform at (B/2)*log2(B) complex butterflies each, plus one complex
    multiply per bin. That is B*(log2 B + 1) complex multiplies per block, i.e.
    log2(B) + 1 per output sample, and 4 real multiplies per complex one.

    For B = 512 and two polarisations this gives 80 real multiplies per output
    sample, which at 2 samples/symbol is 160 real MACs per symbol -- the figure
    the coherent chapter quotes. Getting this wrong by counting a complex
    multiply as one real operation understates the FDE by roughly 2x.
    """
    return 4.0 * (np.log2(block) + 1.0) * polarisations


# --------------------------------------------------------------------------- #
# local plotting helpers
# --------------------------------------------------------------------------- #


def _footnote(fig, text: str, *, width: int = 112) -> None:
    """The italic caption line that closes every figure in the article.

    Wrapped by hand: ``bbox_inches="tight"`` grows to fit whatever it is given,
    so one long line silently stretches the figure past its 8.2 inch width.
    """
    fig.text(0.0, -0.02, textwrap.fill(text, width), fontsize=9, color=P.SOFT,
             style="italic", va="top")


def _right_axis(ax, label: str):
    """A second y axis with the right spine drawn (rcParams hides it)."""
    twin = ax.twinx()
    twin.grid(False)
    twin.spines["right"].set_visible(True)
    twin.spines["right"].set_color(P.RULE)
    twin.spines["top"].set_visible(False)
    twin.tick_params(colors=P.MUTED, labelsize=9)
    twin.set_ylabel(label, color=P.SOFT)
    return twin


def _box(ax, text: str, *, x: float, y: float, ha: str = "left",
         va: str = "top", fontsize: float = 8.4):
    return ax.text(x, y, text, transform=ax.transAxes, family="monospace",
                   fontsize=fontsize, color=P.SOFT, ha=ha, va=va, zorder=6,
                   bbox=dict(boxstyle="round,pad=0.45", facecolor=P.PANEL,
                             edgecolor=P.RULE_SOFT, linewidth=1.0))


def _rms_width(samples: np.ndarray, centre: int, half: int) -> float:
    """RMS width of ``samples`` about ``centre``, in symbol periods."""
    i0, i1 = int(centre) - half * SPS, int(centre) + half * SPS
    energy = np.abs(samples[i0:i1]) ** 2
    t = (np.arange(i0, i1) - centre) / FS
    power = energy.sum()
    mean = (energy * t).sum() / power
    return float(np.sqrt((energy * (t - mean) ** 2).sum() / power) * BAUD)


def _span_99(samples: np.ndarray) -> float:
    """Full width, in symbol periods, holding the middle 99 % of the energy."""
    energy = np.abs(samples) ** 2
    cumulative = np.cumsum(energy) / energy.sum()
    idx = np.where((cumulative > 0.005) & (cumulative < 0.995))[0]
    return float((idx[-1] - idx[0]) / SPS)


# --------------------------------------------------------------------------- #
# 1. one pulse in, one chirp out
# --------------------------------------------------------------------------- #


def dispersion_chirp() -> str:
    """A single raised-cosine pulse through 1700 ps/nm, phase and envelope."""
    n = 8192
    f = np.fft.fftfreq(n, d=1.0 / FS)
    t = np.arange(n) / FS

    burst = np.zeros(n, dtype=complex)
    launch = n // 2 - BULK_DELAY // 2
    burst[launch] = 1.0
    shaped = np.fft.ifft(np.fft.fft(burst) * SPS * rc_spectrum(f))
    disp = (np.exp(1j * cd_phase(f, CD_PS_PER_NM))
            * np.exp(-2j * np.pi * f * (BULK_DELAY / FS)))
    after = np.fft.ifft(np.fft.fft(shaped) * disp)

    # Centre on the *known* arrival time (launch + bulk delay), not on argmax:
    # the dispersed envelope is a chirp with a nearly flat top, so its largest
    # sample lands wherever the Fresnel ripple happens to peak, tens of symbols
    # away from the time that f = 0 actually arrives.
    centre_before = launch
    centre_after = launch + BULK_DELAY
    env_before, env_after = np.abs(shaped), np.abs(after)
    peak = env_after.max()

    # Instantaneous frequency: the derivative of the dispersed waveform's phase.
    inst = np.gradient(np.unwrap(np.angle(after))) / (2.0 * np.pi / FS)
    x_after = (t - t[centre_after]) * BAUD          # symbol periods
    x_before = (t - t[centre_before]) * BAUD
    live = env_after > 0.05 * peak

    fit = live & (np.abs(x_after) <= 20.0)
    slope, intercept = np.polyfit(t[fit] * 1e12, inst[fit] / 1e9, 1)
    analytic = -chirp_rate_ghz_per_ps()
    deviation = 100.0 * (slope - analytic) / analytic

    # The chirp runs out where the pulse runs out of spectrum: the raised-cosine
    # band edge is +/-(1+beta)*baud/2, which the group delay maps to
    # |t| = |D*L|*lambda^2*f_edge/c seconds, i.e. that many symbol periods.
    f_edge = (1.0 + BETA) * BAUD / 2.0
    band_edge = (dl_si(CD_PS_PER_NM) * LAMBDA ** 2 / C_LIGHT * f_edge * BAUD)
    w0 = _rms_width(shaped, centre_before, 64)
    w1 = _rms_width(after, centre_after, 64)
    span = _span_99(after)
    phase_edge = float(cd_phase(32e9, CD_PS_PER_NM))

    fig, axes = P.figure(height=4.5, nrows=2, height_ratios=[1.0, 1.0],
                         sharex=True, hspace=0.28)
    ax_f, ax_e = axes

    # --- top: the chirp, and the two straight lines it sits on --------------
    centered = t - t[centre_after]
    line_window = np.abs(x_after) <= band_edge
    fitted = slope * centered * 1e12 + intercept
    analytic_line = -centered / (dl_si(CD_PS_PER_NM) * LAMBDA ** 2 / C_LIGHT) / 1e9

    inst_plot = np.where(live, inst / 1e9, np.nan)
    ax_f.plot(x_after, inst_plot, color=P.OPTICAL, zorder=3,
              label="measured  d(phase)/dt / 2$\\pi$")
    ax_f.plot(x_after[line_window], fitted[line_window], color=P.WARN,
              linewidth=1.4, zorder=4,
              label="linear fit over the central $\\pm$20 symbols")
    ax_f.plot(x_after[line_window], analytic_line[line_window], color=P.MUTED,
              linewidth=1.2, linestyle=(0, (5, 3)), zorder=2,
              label="analytic  $f = -t/\\beta$")

    ax_f.set_ylim(-46, 46)
    ax_f.set_xlim(-64, 64)
    note = (f"fitted rate {slope:+.4f} GHz/ps\n"
            f"analytic $c/(D\\lambda^2)$ = {analytic:+.4f} GHz/ps  "
            f"({deviation:+.1f} %)\n"
            f"the sweep stops at the pulse's $\\pm$35 GHz edge,\n"
            f"{band_edge:.0f} symbol periods out: the pulse is "
            f"{phase_edge:.0f} rad deep")
    ax_f.text(0.98, 0.96, note, transform=ax_f.transAxes, fontsize=8.6,
              color=P.INK, ha="right", va="top", zorder=6,
              bbox=dict(facecolor=P.PANEL, edgecolor="none", alpha=0.85, pad=2.0))
    ax_f.axhline(0.0, color=P.RULE_SOFT, linewidth=1.0, zorder=1)
    P.tidy(ax_f, ylabel="instantaneous frequency  [GHz]",
           legend=["measured  d(phase)/dt / 2$\\pi$",
                   "linear fit over the central $\\pm$20 symbols",
                   "analytic  $f = -t/\\beta$"], legend_loc="lower left")
    P.title(ax_f, "Dispersion delays each frequency differently",
            subtitle="so a short pulse leaves as a linear chirp  ·  "
                     "1700 ps/nm over 64 GBd")

    # --- bottom: the same pulse, before and after ---------------------------
    window = np.abs(x_after) <= 64
    ax_e.plot(x_after[window], env_after[window] / peak, color=P.OPTICAL,
              label=f"after 1700 ps/nm  ·  RMS {w1:.1f} symbol")
    ax_e.plot(x_before[window], env_before[window] / env_before.max(),
              color=P.ACCENT, zorder=3,
              label=f"launched pulse  ·  RMS {w0:.2f} symbol")
    ax_e.axvline(0.0, color=P.ACCENT, linewidth=1.2, linestyle=(0, (2, 3)),
                 zorder=2)
    # The launched pulse is a needle here, and both curves are normalised, so
    # mark its peak or it hides inside the ripples of the dispersed envelope.
    ax_e.plot([0.0], [1.0], marker="v", markersize=7.0, color=P.ACCENT,
              markeredgecolor=P.PANEL, markeredgewidth=0.8, zorder=5)
    ax_e.text(0.015, 0.99,
              f"one symbol in, {w1 / w0:.1f} wider out: RMS {w0:.2f} "
              f"$\\rightarrow$ {w1:.1f} symbol periods",
              transform=ax_e.transAxes, fontsize=8.8, color=P.ACCENT_DARK,
              ha="left", va="top", zorder=6,
              bbox=dict(facecolor=P.PANEL, edgecolor="none", alpha=0.85, pad=2.0))
    ax_e.text(0.985, 0.99,
              f"spans {span:.0f} symbol periods ($\\pm${span / 2:.0f})\n"
              f"= {span / BAUD * 1e12:.0f} ps at 64 GBd",
              transform=ax_e.transAxes, fontsize=8.8, color=P.INK,
              ha="right", va="top", zorder=6,
              bbox=dict(facecolor=P.PANEL, edgecolor="none", alpha=0.85, pad=2.0))
    ax_e.set_ylim(0.0, 1.16)
    P.tidy(ax_e, xlabel="time, relative to each pulse's own arrival  "
                        "[symbol periods]",
           ylabel="|envelope|  (each normalised)", legend_loc="lower right")

    _footnote(fig,
              f"A single raised-cosine symbol launched into 1700 ps/nm "
              f"(100 km, D = {DISPERSION:.0f} ps/(nm$\\cdot$km)), so its spectrum "
              f"runs out at $\\pm$35 GHz. The all-pass is flat, so no energy is "
              f"lost: the pulse is {w1 / w0:.1f} times wider in RMS and spans "
              f"{span:.0f} of its own symbol periods, because each frequency "
              f"arrives at its own time with a rate of {abs(analytic):.4f} GHz/ps "
              f"-- the {CD_PS_PER_NM:.0f} ps/nm of walk the block equaliser of the "
              f"next figures has to hold. Both envelopes are drawn about their own "
              f"arrival time; the {BULK_DELAY // SPS} symbol bulk delay the all-pass "
              f"carries is not dispersion and is not shown.")
    return P.render(fig)


# --------------------------------------------------------------------------- #
# 2. why nobody does this with a T-spaced FIR
# --------------------------------------------------------------------------- #


def dispersion_time_domain_taps() -> str:
    """The symbol-spaced FIR for H*(f): a flat chirp body and a long skirt."""
    n = 1 << 13                                   # 8192 symbol-rate bins
    f = np.fft.fftfreq(n, d=1.0 / BAUD)
    h = np.fft.fftshift(np.fft.ifft(np.exp(-1j * cd_phase(f, CD_PS_PER_NM))))
    magnitude = np.abs(h)
    index = np.arange(n) - n // 2                 # tap index, centre tap at 0
    centre_tap = float(magnitude[n // 2])
    rel_db = 20.0 * np.log10(magnitude / centre_tap)

    taps = {}
    for level in TAP_LEVELS_DB:
        taps[level] = taps_for_residual(CD_PS_PER_NM, level)

    widest = max(taps.values())
    fde_cost = fde_mults_per_sample(FDE_BLOCK)
    td_cost = td_macs_per_symbol(widest)
    td_tera = td_cost * BAUD / 1e12
    fde_tera = fde_cost * SPS * BAUD / 1e12
    fde_floor = _db(block_residual_power(CD_PS_PER_NM, FDE_BLOCK))
    body = int(np.sum(magnitude > magnitude.max() / np.sqrt(2.0)))
    saving = td_cost / (fde_cost * SPS)

    fig, ax = P.figure(height=3.6)
    view = np.abs(index) <= 320
    ax.plot(index[view], rel_db[view], color=P.OPTICAL, zorder=3)
    ax.set_xlim(-320, 320)
    ax.set_ylim(-92, 4)

    rows = [" taps   residual   MACs/symbol"]
    for level in TAP_LEVELS_DB:
        count = taps[level]
        rows.append(f"  {count:4d}   {level:5.0f} dB   "
                    f"{td_macs_per_symbol(count):8.0f}")
    rows.append(f"   FDE   {fde_floor:5.0f} dB   {fde_cost * SPS:8.0f}")
    _box(ax, "\n".join(rows), x=0.985, y=0.97, ha="right", va="top",
         fontsize=8.3)

    for level, colour in zip(TAP_LEVELS_DB, (P.WARN, P.NOTE, P.OPTICAL)):
        ax.axhline(level, color=colour, linewidth=1.0, linestyle=(0, (1.5, 2.5)),
                   zorder=1)
        count = taps[level]
        ax.text(-318, level + 1.2, f"{count} taps", color=colour, fontsize=8.4,
                ha="left", va="bottom")
        ax.axvline(count / 2.0, color=colour, linewidth=1.0,
                   linestyle=(0, (1.5, 2.5)), zorder=1)
        ax.axvline(-count / 2.0, color=colour, linewidth=1.0,
                   linestyle=(0, (1.5, 2.5)), zorder=1)

    ax.annotate(f"the chirp body: the {body} taps\nwithin $\\pm${body // 2} all "
                f"weigh about the same",
                xy=(-26, -1.0), xytext=(-315, -6.0), color=P.MUTED, fontsize=8.6,
                ha="left", va="center", zorder=6,
                arrowprops=dict(arrowstyle="->", color=P.MUTED, linewidth=1.0,
                                shrinkA=3, shrinkB=3))
    ax.text(0.05, 0.05,
            f"the skirt falls only ~12 dB per doubling of the\n"
            f"tap count: {taps[-20.0]} taps buy -20 dB, "
            f"{taps[-40.0]} buy -40 dB,\n"
            f"and it is still 1/n$^2$ all the way down",
            transform=ax.transAxes, fontsize=8.6, color=P.INK, ha="left",
            va="bottom", zorder=6,
            bbox=dict(facecolor=P.PANEL, edgecolor="none", alpha=0.85, pad=2.0))

    P.tidy(ax, xlabel="tap index, relative to the centre tap",
           ylabel="|tap|  [dB, relative to the centre tap]")

    _footnote(fig,
              f"The IFFT of H*(f) on a symbol-rate grid (8192 bins, "
              f"$\\pm$32 GHz), which is exactly the T-spaced FIR an inverting "
              f"filter would have to be. The response is symmetric about its "
              f"centre tap, with its two equal maxima $\\pm$21 taps either side "
              f"(the chirp's brightest Fresnel zone), so tap 0 is the delay the "
              f"equaliser carries and the truncation is symmetric about it. "
              f"{taps[-40.0]} taps hold the residual below -40 dB, and that is "
              f"{td_tera:.0f} Tera real MAC/s at 64 GBd across two polarisations, "
              f"against {fde_tera:.1f} Tera/s for the {FDE_BLOCK}-point FDE of the "
              f"block-size figure -- a factor {saving:.0f} more arithmetic "
              f"for the same job.")
    return P.render(fig)


# --------------------------------------------------------------------------- #
# 3. the accuracy / cost / latency curve
# --------------------------------------------------------------------------- #


def fde_residual_vs_blocksize() -> str:
    """Overlap-save block size against residual EVM, cost and latency."""
    blocks = np.array(BLOCK_SWEEP)
    powers = np.array([block_residual_power(CD_PS_PER_NM, int(b)) for b in blocks])
    evm_db = 10.0 * np.log10(powers)

    memory = dispersion_memory_samples(CD_PS_PER_NM)
    memory_symbols = memory / SPS
    memory_ns = memory / FS * 1e9

    # The knee: the first power of two whose usable half-block (B/2 samples)
    # exceeds the measured dispersion memory.
    knee = int(blocks[np.argmax(blocks / 2.0 >= memory)])
    knee_evm = float(evm_db[list(blocks).index(knee)])
    before_evm = float(evm_db[list(blocks).index(knee // 2)])

    quant_db = _db(quantisation_power(FDE_PHASE_BITS))
    cost = np.array([fde_mults_per_sample(int(b)) for b in blocks])
    latency = blocks / 2.0

    fig, axes = P.figure(height=4.8, nrows=2, sharex=True, hspace=0.3,
                         height_ratios=[1.15, 1.0])
    ax_e, ax_c = axes

    # --- top: what the block buys ------------------------------------------
    ax_e.semilogx(blocks, evm_db, base=2, marker="o", markersize=4.5,
                  color=P.ACCENT, zorder=4, label="residual EVM after the FDE")
    ax_e.axhline(quant_db, color=P.NOTE, linewidth=1.3, linestyle=(0, (5, 3)),
                 zorder=2)
    ax_e.text(blocks[0] * 1.15, quant_db + 2.0,
              f"{FDE_PHASE_BITS}-bit coefficient phase: {quant_db:.0f} dB",
              color=P.NOTE, fontsize=8.6, ha="left", va="bottom")
    ax_e.axvline(memory, color=P.MUTED, linewidth=1.2, linestyle=(0, (2, 3)),
                 zorder=1)
    ax_e.text(memory * 0.96, -88, f"memory {memory:.0f} samples", color=P.MUTED,
              fontsize=8.4, ha="right", va="bottom", rotation=90)
    ax_e.axvline(knee, color=P.WARN, linewidth=1.6, zorder=3)
    ax_e.annotate(f"knee: B = {knee} samples\n"
                  f"= {knee / 2:.0f} symbols = {knee / FS * 1e9:.1f} ns",
                  xy=(knee, knee_evm), xytext=(620, -18), color=P.WARN,
                  fontsize=9, ha="left", va="center", zorder=7,
                  arrowprops=dict(arrowstyle="->", color=P.WARN, linewidth=1.2,
                                  shrinkA=3, shrinkB=3))
    ax_e.text(0.02, 0.06,
              f"B = {knee // 2}: {before_evm:.0f} dB  ->  B = {knee}: "
              f"{knee_evm:.0f} dB\none doubling, {before_evm - knee_evm:.0f} dB: "
              f"the block finally holds the chirp",
              transform=ax_e.transAxes, fontsize=8.6, color=P.INK, ha="left",
              va="bottom", zorder=6,
              bbox=dict(facecolor=P.PANEL, edgecolor="none", alpha=0.85, pad=2.0))
    ax_e.set_ylim(-95, 12)
    ax_e.set_xlim(blocks[0] * 0.85, blocks[-1] * 1.6)
    P.tidy(ax_e, ylabel="residual EVM  [dB]",
           legend=["residual EVM after the FDE"], legend_loc="upper right")
    P.title(ax_e, "How big a block does 1700 ps/nm need?",
            subtitle="overlap-save FDE, 16-QAM, 64 GBd, 2 samples/symbol")

    # --- bottom: what it costs ---------------------------------------------
    ax_c.semilogx(blocks, cost, base=2, marker="o", markersize=4.5,
                  color=P.OPTICAL, zorder=4)
    ax_c.set_ylim(0, 124)
    ax_lat = _right_axis(ax_c, "block latency  [symbol periods]")
    ax_lat.semilogx(blocks, latency, base=2, color=P.NOTE, linewidth=1.6,
                    linestyle=(0, (5, 3)), zorder=3)
    ax_lat.set_ylim(0, 2300)
    ax_lat.set_yticks([0, 512, 1024, 1536, 2048])
    ax_lat.axhline(knee / 2.0, color=P.RULE, linewidth=1.0, linestyle=(0, (2, 3)))
    ax_c.axvline(knee, color=P.WARN, linewidth=1.6, zorder=3)

    ax_c.text(0.03, 0.92,
              f"cost: $4(\\log_2 B + 1)$ real multiplies per output sample,\n"
              f"times two polarisations  ·  {cost[0]:.0f} -> {cost[-1]:.0f} "
              f"real multiplies: {cost[-1] / cost[0]:.1f}$\\times$ the arithmetic",
              transform=ax_c.transAxes, fontsize=8.6, color=P.OPTICAL, ha="left",
              va="top", zorder=6,
              bbox=dict(facecolor=P.PANEL, edgecolor="none", alpha=0.85, pad=2.0))
    ax_c.text(0.97, 0.10, "dashed: latency = one block = B/2 symbols "
                          "(right axis)",
              transform=ax_c.transAxes, fontsize=8.4, color=P.NOTE, ha="right",
              va="bottom", zorder=6,
              bbox=dict(facecolor=P.PANEL, edgecolor="none", alpha=0.85, pad=2.0))
    P.tidy(ax_c, xlabel="overlap-save block size B  [samples at 2 samples/symbol]",
           ylabel="real multiplies per output sample\n(two polarisations)")
    ax_c.set_xticks(list(blocks))
    ax_c.set_xticklabels([str(b) for b in blocks])
    ax_c.minorticks_off()

    _footnote(fig,
              f"Measured, not estimated: the overlap-save equaliser is run on the "
              f"same 16-QAM record for each block size and the EVM is read at the "
              f"decision instants. The dispersion memory is {memory:.0f} samples = "
              f"{memory_symbols:.0f} symbol periods = {memory_ns:.2f} ns, so a "
              f"50 %-overlap block must hold it in its usable half: "
              f"B/2 > {memory:.0f} samples puts the knee at B = {knee} samples "
              f"({knee / 2:.0f} symbols, {knee / FS * 1e9:.1f} ns). Small blocks "
              f"cannot hold the chirp and fold it onto itself; past the knee the "
              f"residual is already {abs(knee_evm):.0f} dB, below the "
              f"{FDE_PHASE_BITS}-bit coefficient floor, and another doubling of the "
              f"block buys latency and arithmetic for nothing.")
    return P.render(fig)


# --------------------------------------------------------------------------- #
# 4. the engineering trade: penalty against reach
# --------------------------------------------------------------------------- #


def dispersion_penalty_vs_reach() -> str:
    """Uncompensated, ideal and practical FDE against distance."""
    distances = np.unique(np.concatenate([
        np.arange(0.25, 20.0, 0.25),
        np.arange(20.0, 501.0, 10.0),
        np.arange(500.0, 2001.0, 50.0),
    ]))
    dispersions = DISPERSION * distances

    compensation = np.array([
        isi_power(channel_taps(DISPERSION * d)) for d in distances])
    penalty_bare = np.array([penalty_db(c) for c in compensation])

    quant_power = quantisation_power(FDE_PHASE_BITS)
    practical = np.array([
        block_residual_power(DISPERSION * d, FDE_BLOCK) + quant_power
        for d in distances])
    penalty_practical = np.array([penalty_db(p) for p in practical])

    def crossing(penalties, level=UNUSABLE_DB):
        idx = np.where(penalties >= level)[0]
        if idx.size == 0:
            return float(distances[-1])
        i = int(idx[0])
        if i == 0:
            return float(distances[0])
        x0, x1 = distances[i - 1], distances[i]
        y0, y1 = penalties[i - 1], penalties[i]
        return float(x0 + (level - y0) * (x1 - x0) / (y1 - y0))

    reach_bare = crossing(penalty_bare)
    reach_practical = crossing(penalty_practical)

    fig, ax = P.figure(height=3.8)
    ax.plot(distances, penalty_bare, color=P.WARN, zorder=4,
            label="no compensation")
    ax.plot(distances, np.zeros_like(distances), color=P.ACCENT, zorder=4,
            label="ideal FDE (exact $H^{*}$)")
    ax.plot(distances, penalty_practical, color=P.OPTICAL, zorder=4,
            label=f"practical FDE: {FDE_BLOCK}-point, {FDE_PHASE_BITS}-bit")
    ax.axhline(UNUSABLE_DB, color=P.RULE, linewidth=1.2, linestyle=(0, (5, 3)),
               zorder=2)
    ax.text(1990, UNUSABLE_DB - 0.28, f"{UNUSABLE_DB:.0f} dB: no margin left",
            color=P.MUTED, fontsize=8.6, ha="right", va="top")

    for x, colour in ((reach_bare, P.WARN), (reach_practical, P.OPTICAL)):
        ax.axvline(x, color=colour, linewidth=1.1, linestyle=(0, (2, 3)), zorder=2)
    ax.annotate(f"uncompensated: unusable at {reach_bare:.1f} km,\n"
                f"{DISPERSION * reach_bare:.0f} ps/nm of 64 GBd 16-QAM",
                xy=(reach_bare, UNUSABLE_DB), xytext=(22, 2.1), color=P.WARN,
                fontsize=8.8, ha="left", va="center", zorder=7,
                arrowprops=dict(arrowstyle="->", color=P.WARN, linewidth=1.2,
                                shrinkA=3, shrinkB=3))
    ax.annotate(f"practical FDE runs out at {reach_practical:.0f} km:\n"
                f"{FDE_BLOCK // 2} samples of block memory is\n"
                f"{CD_PS_PER_NM:.0f} ps/nm of chirp, and this link\n"
                f"asks for "
                f"{dispersions[list(distances).index(500.0)] / CD_PS_PER_NM:.1f}"
                f"$\\times$ that",
                xy=(reach_practical, UNUSABLE_DB), xytext=(340, 5.7),
                color=P.OPTICAL, fontsize=8.8, ha="left", va="center", zorder=7,
                arrowprops=dict(arrowstyle="->", color=P.OPTICAL, linewidth=1.2,
                                shrinkA=3, shrinkB=3))
    ax.text(0.985, 0.05,
            "model: gain-normalised distortion treated as additive\n"
            f"Gaussian noise on a {OSNR_REF_DB:.0f} dB link, "
            "PEN = 10$\\log_{10}$(1 + 100$\\cdot$D)\n"
            "labels are a model, not a measurement",
            transform=ax.transAxes, fontsize=8.4, color=P.SOFT, ha="right",
            va="bottom", zorder=6,
            bbox=dict(facecolor=P.PANEL, edgecolor=P.RULE_SOFT, linewidth=1.0,
                      pad=2.5))
    ax.set_xlim(0, 2000)
    ax.set_ylim(0, 8)
    ax.set_yticks([0, 2, 4, 6, 8])

    ax_d = _right_axis(ax, "accumulated dispersion  [ps/nm]")
    ax_d.set_ylim(0, 8)
    ax_d.set_yticks([0, 2, 4, 6, 8])
    ax_d.set_yticklabels([f"{int(DISPERSION * 2000 * t / 8):d}" for t in
                          (0, 2, 4, 6, 8)])
    ax_d.axhline(UNUSABLE_DB, color=P.RULE, linewidth=1.2,
                 linestyle=(0, (5, 3)), zorder=1)

    P.tidy(ax, xlabel="fibre length  [km]  at D = 17 ps/(nm$\\cdot$km)",
           ylabel="dispersion penalty  [dB]",
           legend=["no compensation", "ideal FDE (exact $H^{*}$)",
                   f"practical FDE: {FDE_BLOCK}-point, {FDE_PHASE_BITS}-bit"],
           legend_loc="upper right", ncol=1)

    _footnote(fig,
              f"A perfect all-pass inverse costs nothing: |H*| = 1, so the ideal "
              f"curve sits on 0 dB for 2000 km and 34000 ps/nm. That is the "
              f"idealisation, not a budget. The practical curve is the same "
              f"overlap-save simulation as the block-size figure re-run at every reach "
              f"{FDE_BLOCK}-sample block and {FDE_PHASE_BITS}-bit coefficients "
              f"({10 * np.log10(quant_power):.0f} dB of coefficient EVM): it holds "
              f"the link to {reach_practical:.0f} km and then fails as fast as no "
              f"compensation at all, because {FDE_BLOCK // 2} samples of block "
              f"memory is {CD_PS_PER_NM:.0f} ps/nm of chirp. Without either, "
              f"64 GBd 16-QAM dies inside {reach_bare:.1f} km: the distortion has "
              f"already eaten the 3 dB margin.")
    return P.render(fig)


# --------------------------------------------------------------------------- #
# 5. how many coefficient bits?
# --------------------------------------------------------------------------- #


def fde_coefficient_quantisation() -> str:
    """EVM and phase resolution against coefficient phase word width."""
    widths = np.arange(4, 13)
    powers = np.array([quantisation_power(int(w)) for w in widths])
    evm_db = 10.0 * np.log10(powers)

    link_db = -OSNR_REF_DB
    criterion_db = link_db - 20.0 * np.log10(3.0)      # a third of the link EVM
    enough = [int(w) for w, value in zip(widths, evm_db) if value <= criterion_db]
    chosen = enough[0] if enough else int(widths[-1])
    chosen_evm = float(evm_db[list(widths).index(chosen)])
    chosen_penalty = penalty_db(float(powers[list(widths).index(chosen)]))
    steps = 360.0 / 2.0 ** widths

    fig, ax = P.figure(height=3.6)
    ax.plot(widths, evm_db, marker="o", markersize=5.0, color=P.ACCENT, zorder=4,
            label="coefficient EVM (measured)")
    ax.axhline(link_db, color=P.MUTED, linewidth=1.3, linestyle=(0, (5, 3)),
               zorder=2)
    ax.text(4.05, link_db + 1.0, f"the link's own noise: {OSNR_REF_DB:.0f} dB "
                                 f"OSNR = {10 ** (-OSNR_REF_DB / 20) * 100:.0f} % EVM",
            color=P.MUTED, fontsize=8.6, ha="left", va="bottom")
    ax.axhline(criterion_db, color=P.NOTE, linewidth=1.3,
               linestyle=(0, (2, 3)), zorder=2)
    ax.text(chosen + 0.15, criterion_db - 1.0,
            "quantisation no longer limiting: a third of it",
            color=P.NOTE, fontsize=8.6, ha="left", va="top")
    ax.axvline(chosen, color=P.WARN, linewidth=1.6, zorder=3)

    ax.annotate(f"{chosen} bits: {chosen_evm:.1f} dB EVM,\n"
                f"{chosen_penalty:+.2f} dB of link penalty",
                xy=(chosen, chosen_evm), xytext=(chosen + 0.35, -52),
                color=P.WARN, fontsize=9, ha="left", va="center", zorder=7,
                arrowprops=dict(arrowstyle="->", color=P.WARN, linewidth=1.2,
                                shrinkA=3, shrinkB=3))
    ax.text(0.985, 0.95,
            "below 10 bits the phase word sets the error;\nabove it the "
            f"{FDE_BLOCK}-point block does",
            transform=ax.transAxes, fontsize=8.4, color=P.MUTED, ha="right",
            va="top", zorder=6)

    ax_d = _right_axis(ax, "phase resolution  [degrees per bin]")
    ax_d.plot(widths, steps, color=P.NOTE, linewidth=1.6, linestyle=(0, (5, 3)),
              zorder=3)
    ax_d.set_ylim(0, 24)
    ax_d.set_yticks([0, 6, 12, 18, 24])

    ax.set_ylim(-74, -16)
    ax.set_xlim(3.8, 12.4)
    ax.set_xticks(list(widths))
    P.tidy(ax, xlabel="coefficient phase word width  [bits]",
           ylabel="EVM from coefficient quantisation  [dB]",
           legend=["coefficient EVM (measured)"], legend_loc="lower left")

    _footnote(fig,
              f"The coefficients of the {FDE_BLOCK}-point overlap-save equaliser of "
              f"figures 3 and 4, with |H*[k]| = 1 exactly and the phase -- chirp and "
              f"block-delay ramp together, as one ROM word -- quantised uniformly "
              f"over [-$\\pi$, $\\pi$) to $2^w$ levels. At {chosen} bits the step is "
              f"{360.0 / 2 ** chosen:.2f}$^\\circ$ per bin and the quantisation EVM "
              f"measures {chosen_evm:.1f} dB, under a third of the {OSNR_REF_DB:.0f} dB "
              f"link's own {10 ** (-OSNR_REF_DB / 20) * 100:.0f} %: it costs "
              f"{chosen_penalty:.2f} dB and stops being the limit. "
              f"{chosen - 1} bits measures {evm_db[list(widths).index(chosen) - 1]:.1f} dB "
              f"({penalty_db(float(powers[list(widths).index(chosen) - 1])):.2f} dB of "
              f"penalty), and past 10 bits a wider word buys nothing: the curve is "
              f"flat because the block's own aliasing floor is what is left.")
    return P.render(fig)


FIGURES = {
    "dispersion-chirp": dispersion_chirp,
    "dispersion-time-domain-taps": dispersion_time_domain_taps,
    "fde-residual-vs-blocksize": fde_residual_vs_blocksize,
    "dispersion-penalty-vs-reach": dispersion_penalty_vs_reach,
    "fde-coefficient-quantisation": fde_coefficient_quantisation,
}


# --------------------------------------------------------------------------- #
# the numbers the figures annotate, printed on demand
# --------------------------------------------------------------------------- #


def _diagnostics() -> None:
    """Print every number the figures claim, so the annotations can be audited."""
    print(f"link: {BAUD / 1e9:.0f} GBd, SPS = {SPS} ({FS / 1e9:.0f} GSa/s), "
          f"D = {DISPERSION:.0f} ps/(nm.km), lambda = {LAMBDA * 1e9:.0f} nm")
    print(f"reference case: {CD_PS_PER_NM:.0f} ps/nm = "
          f"{dl_si(CD_PS_PER_NM):.1f} s/m = 100 km")
    beta = dl_si(CD_PS_PER_NM) * LAMBDA ** 2 / C_LIGHT
    print(f"  chirp rate 1/beta = {chirp_rate_ghz_per_ps():.5f} GHz/ps "
          f"= {chirp_rate_ghz_per_ps() * 1e3:.1f} GHz/ns")
    memory = dispersion_memory_samples(CD_PS_PER_NM)
    print(f"  dispersion memory (band-limited chirp, +/-f_s/2): {memory:.1f} samples "
          f"= {memory / SPS:.1f} symbol periods = {memory / FS * 1e9:.2f} ns")
    print(f"  phase at 32 GHz: {cd_phase(32e9, CD_PS_PER_NM):.2f} rad "
          f"= {cd_phase(32e9, CD_PS_PER_NM) / np.pi:.1f} pi")

    # --- figure 1 ----------------------------------------------------------
    for name, builder in FIGURES.items():
        svg = builder()
        print(f"{name}: {len(svg)} bytes")


    # --- figure 2 ----------------------------------------------------------
    print("dispersion-time-domain-taps:")
    for level in TAP_LEVELS_DB:
        count = taps_for_residual(CD_PS_PER_NM, level)
        print(f"  {level:5.0f} dB residual: {count} taps "
              f"({count / BAUD * 1e12:.0f} ps)  measured "
              f"{_db(truncation_residual_power(CD_PS_PER_NM, count)):.2f} dB")
    widest = taps_for_residual(CD_PS_PER_NM, TAP_LEVELS_DB[-1])
    print(f"  T-spaced FIR, {widest} taps, two polarisations: "
          f"{td_macs_per_symbol(widest):.0f} real MAC/symbol = "
          f"{td_macs_per_symbol(widest) * BAUD / 1e12:.1f} Tera/s")
    print(f"  FDE, {FDE_BLOCK}-point block, two polarisations: "
          f"{fde_mults_per_sample(FDE_BLOCK):.0f} real multiplies per output sample "
          f"= {fde_mults_per_sample(FDE_BLOCK) * SPS:.0f} per symbol = "
          f"{fde_mults_per_sample(FDE_BLOCK) * SPS * BAUD / 1e12:.2f} Tera/s")
    print(f"  ratio {td_macs_per_symbol(widest) / (fde_mults_per_sample(FDE_BLOCK) * SPS):.1f}x")

    # --- figure 3 ----------------------------------------------------------
    print("fde-residual-vs-blocksize:")
    for block in BLOCK_SWEEP:
        power = block_residual_power(CD_PS_PER_NM, block)
        print(f"  B = {block:5d} samples ({block / 2:5.0f} symbols, "
              f"{block / FS * 1e9:5.2f} ns): EVM {_db(power):8.2f} dB  "
              f"cost {fde_mults_per_sample(block):.0f} real mults/output sample")

    # --- figure 4 ----------------------------------------------------------
    print("dispersion-penalty-vs-reach:")
    quant = quantisation_power(FDE_PHASE_BITS)
    for km in (1.0, 2.0, 5.0, 10.0, 100.0, 200.0, 400.0, 1000.0, 2000.0):
        bare = isi_power(channel_taps(DISPERSION * km))
        pract = block_residual_power(DISPERSION * km, FDE_BLOCK) + quant
        print(f"  {km:6.1f} km: {DISPERSION * km:7.0f} ps/nm  "
              f"uncompensated {_db(bare):6.1f} dB distortion "
              f"({penalty_db(bare):5.2f} dB penalty)  "
              f"practical {_db(pract):6.1f} dB ({penalty_db(pract):5.2f} dB)")
    distances = np.unique(np.concatenate([
        np.arange(0.25, 20.0, 0.25), np.arange(20.0, 501.0, 10.0),
        np.arange(500.0, 2001.0, 50.0)]))
    bare = np.array([penalty_db(isi_power(channel_taps(DISPERSION * d)))
                     for d in distances])
    pract = np.array([penalty_db(block_residual_power(DISPERSION * d, FDE_BLOCK)
                                 + quant) for d in distances])
    for label, curve in (("uncompensated", bare), ("practical FDE", pract)):
        hit = np.where(curve >= UNUSABLE_DB)[0]
        if hit.size:
            i = int(hit[0])
            reach = distances[i] if i == 0 else distances[i - 1] + (
                UNUSABLE_DB - curve[i - 1]) * (distances[i] - distances[i - 1]) / (
                curve[i] - curve[i - 1])
            print(f"  {label}: {UNUSABLE_DB:.0f} dB penalty at {reach:.2f} km "
                  f"({DISPERSION * reach:.0f} ps/nm)")
        else:
            print(f"  {label}: stays under {UNUSABLE_DB:.0f} dB to "
                  f"{distances[-1]:.0f} km")

    # --- figure 5 ----------------------------------------------------------
    print("fde-coefficient-quantisation:")
    for bits in range(4, 13):
        power = quantisation_power(bits)
        print(f"  {bits:2d} bits: {360.0 / 2 ** bits:7.3f} deg/bin  "
              f"EVM {_db(power):7.2f} dB  penalty {penalty_db(power):6.2f} dB")


if __name__ == "__main__":
    _diagnostics()
