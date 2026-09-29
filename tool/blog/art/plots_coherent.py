"""Computed figures for the coherent optical receiver chapter.

Four numpy/matplotlib figures for the chapter on the coherent receiver DSP
chain. Everything here is a simulation of the impairment, not an artist's
impression of one:

    coherent-constellations     QPSK / 16-QAM / 64-QAM at unit average energy
    cd-frequency-response       the all-pass that chromatic dispersion is
    cd-constellation-recovery   16-QAM through 1700 ps/nm, with and without H*
    phase-noise-rings           one SNR, three laser linewidths

Modelling notes, because every number the figures annotate is derived here:

* Chromatic dispersion is the all-pass ``H(f) = exp(j*pi*D*lambda^2*L*f^2/c)``
  with ``D`` in ps/(nm*km) converted as ``D * 1e-6`` s/m^2 and ``L`` in metres.
  1700 ps/nm of accumulated dispersion is therefore 1.7 s/m, the SI form used
  throughout (and the reason the figure labels carry both).
* The transmitter pulse is a raised cosine applied in the frequency domain, so
  it is exactly Nyquist: the back-to-back constellation has no ISI of its own
  and every smear in the figures is dispersion, never pulse shaping.
* The dispersive channel is realised as a frequency-domain all-pass whose
  impulse response is the band-limited chirp. Sampling H(f) on the DFT grid of
  the whole record band-limits it to +/-f_s/2 = +/-64 GHz, which spreads the
  pulse over +/-|D*L|*lambda^2*f_s/(2c) = +/-56 symbol periods -- the "tens of
  symbols" the chapter claims, and a number measured here rather than asserted.
* That chirp is symmetric about t = 0, so the all-pass is given a bulk delay of
  BULK_DELAY = 256 samples (128 symbol periods at 2 samples/symbol) to make it
  causal. Symbol *k* is read at output sample 256 + 2k: the delay is
  compensated explicitly, and the figure says so.
* The equaliser is the literal thing the chapter claims -- one multiplication by
  H*(f) in the frequency domain, zero phase, no adaptive taps. The residual it
  leaves is the receiver noise added in front of it, which is not undone.
* Laser phase noise is a Wiener process on the carrier phase: each symbol takes
  an increment from N(0, 2*pi*Delta_nu*Ts) radians, accumulated with cumsum.
  All three linewidth panels share the same symbols and the same noise draw, so
  the linewidth is the only thing that changes between them.
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
BAUD = 64e9                    # Bd: every figure that has a symbol rate uses this
DISPERSION = 17.0              # ps/(nm*km), a typical single-mode figure
SPS = 2                        # samples per symbol in the dispersion simulation
BETA = 0.1                     # raised-cosine roll-off
N_SYMBOLS = 8000               # 16-QAM symbols sent through the fibre
PAD_SYMBOLS = 256              # zero symbols either side, so no wrap reaches data
BULK_DELAY = 256               # samples of bulk delay; 128 symbol periods at SPS=2
SNR_DB = 26.0                  # receiver noise floor for the recovery figure
CD_PS_PER_NM = 1700.0          # the case worked through the chapter


def dl_si(ps_per_nm: float) -> float:
    """Accumulated dispersion in s/m. ``1 ps/nm`` is exactly ``1e-3 s/m``."""
    return ps_per_nm * 1e-3


def cd_phase(f, ps_per_nm: float):
    """Quadratic spectral phase of chromatic dispersion, in radians.

    ``f`` may be a scalar or an array; the result has the same shape.
    """
    return np.pi * dl_si(ps_per_nm) * LAMBDA ** 2 * f ** 2 / C_LIGHT


def cd_group_delay(f, ps_per_nm: float):
    """Group delay ``-dphi/domega`` in seconds (the sign is a convention)."""
    return -dl_si(ps_per_nm) * LAMBDA ** 2 * f / C_LIGHT


def cd_spread_symbols(ps_per_nm: float, baud: float = BAUD) -> float:
    """Pulse broadening in symbol periods over the occupied optical band."""
    d_lambda = LAMBDA ** 2 / C_LIGHT * baud * (1.0 + BETA)
    return abs(dl_si(ps_per_nm)) * d_lambda * baud


# --------------------------------------------------------------------------- #
# constellations
# --------------------------------------------------------------------------- #


def qam_levels(m: int) -> np.ndarray:
    """One axis of an ``m``-QAM grid, scaled to unit *average symbol* energy."""
    side = int(round(m ** 0.5))
    raw = np.arange(-(side - 1), side, 2, dtype=float)
    return raw / np.sqrt(2.0 * np.mean(raw ** 2))


def ideal_points(m: int) -> np.ndarray:
    """The ``m`` ideal symbols as a complex vector, mean energy 1."""
    lv = qam_levels(m)
    return (lv[:, None] + 1j * lv[None, :]).ravel()


def min_distance(m: int) -> float:
    """Minimum Euclidean distance at unit average symbol energy."""
    lv = qam_levels(m)
    return float(lv[1] - lv[0])


def random_qam(m: int, count: int, rng: np.random.Generator) -> np.ndarray:
    lv = qam_levels(m)
    side = lv.size
    return lv[rng.integers(0, side, count)] + 1j * lv[rng.integers(0, side, count)]


def _square(ax, limit: float) -> None:
    """A constellation panel: equal aspect, symmetric limits, no tick labels.

    The four spines are kept (drawn in the rule colour) so the panel still reads
    as a square; the numbers are shape, not scale.
    """
    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_color(P.RULE)
    ax.set_aspect("equal")
    ax.set_xlim(-limit, limit)
    ax.set_ylim(-limit, limit)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.grid(False)


def _evm_db(measured: np.ndarray, reference: np.ndarray) -> float:
    error = measured - reference
    return float(20.0 * np.log10(np.sqrt(np.mean(np.abs(error) ** 2))
                                 / np.sqrt(np.mean(np.abs(reference) ** 2))))


def _footnote(fig, text: str, *, width: int = 112) -> None:
    """The italic caption line the handwritten diagrams close with.

    Wrapped by hand: ``bbox_inches="tight"`` grows to fit whatever it is given,
    so a single long line silently stretches the whole figure past 8.2 inches
    and shrinks every label relative to it.
    """
    fig.text(0.0, -0.02, textwrap.fill(text, width), fontsize=9, color=P.SOFT,
             style="italic", va="top")


def _note(ax, text: str, *, color: str, fontsize: float = 8.5):
    """A corner note over a dense constellation, on a white wash so it reads."""
    return ax.text(0.03, 0.97, text, transform=ax.transAxes, fontsize=fontsize,
                   color=color, ha="left", va="top",
                   bbox=dict(facecolor=P.PANEL, edgecolor="none", alpha=0.82,
                             pad=2.0))


# --------------------------------------------------------------------------- #
# the dispersive link
# --------------------------------------------------------------------------- #


def _rc_spectrum(f, baud: float = BAUD, beta: float = BETA):
    """Raised-cosine spectrum, exactly zero outside ``+/-(1+beta)*baud/2``."""
    a = np.abs(f)
    h = np.zeros(a.shape, dtype=float)
    flat = a <= (1.0 - beta) * baud / 2.0
    h[flat] = 1.0
    roll = (a > (1.0 - beta) * baud / 2.0) & (a < (1.0 + beta) * baud / 2.0)
    if np.any(roll):
        x = (a[roll] - (1.0 - beta) * baud / 2.0) / (beta * baud)
        h[roll] = 0.5 * (1.0 + np.cos(np.pi * x))
    return h


def _link(tx: np.ndarray, ps_per_nm: float, *, rng=None, snr_db=None,
          pad: int = PAD_SYMBOLS):
    """Push symbols through the whole chain and return the received records.

    Returns ``(rx, eq)`` at ``SPS`` samples per symbol, both on the same time
    base: symbol *k* of the input sits at output sample ``BULK_DELAY + 2k`` in
    each, so the two constellations are read at identical instants. ``rx`` is
    the dispersed signal (plus noise, if asked for); ``eq`` is the same record
    multiplied by ``H*(f)``.
    """
    n_sym = tx.size
    n_total = n_sym + 2 * pad
    fs = SPS * BAUD

    symbols = np.zeros(n_total, dtype=complex)
    symbols[pad:pad + n_sym] = tx
    wave = np.zeros(n_total * SPS, dtype=complex)
    wave[::SPS] = symbols

    # The SPS factor is the interpolation gain of zero-insertion: a train with
    # one nonzero sample in SPS carries SPS times less power than the symbol
    # stream, so the pulse-shaping filter needs a DC gain of SPS for the
    # symbol-instant samples to come back out as the symbols themselves.
    f = np.fft.fftfreq(wave.size, d=1.0 / fs)
    shaped = np.fft.ifft(np.fft.fft(wave) * SPS * _rc_spectrum(f))

    disp = np.exp(1j * cd_phase(f, ps_per_nm)) * np.exp(-2j * np.pi * f * (BULK_DELAY / fs))
    rx = np.fft.ifft(np.fft.fft(shaped) * disp)

    if snr_db is not None:
        if rng is None:
            raise ValueError("snr_db needs an rng to draw the noise from")
        sigma = np.sqrt(10.0 ** (-snr_db / 10.0) / 2.0)
        rx = rx + sigma * (rng.standard_normal(rx.size)
                           + 1j * rng.standard_normal(rx.size))

    eq = np.fft.ifft(np.fft.fft(rx) * np.exp(-1j * cd_phase(f, ps_per_nm)))
    return rx, eq


def _sample(record: np.ndarray, positions: np.ndarray) -> np.ndarray:
    return record[BULK_DELAY + SPS * positions]


def _discrete_channel(ps_per_nm: float, half: int = 120, pad: int = 400):
    """The symbol-spaced channel seen by one isolated symbol.

    An impulse in, the decimated symbol-rate response out: this is the honest
    way to count ISI symbols, and it is what the recovery figure quotes.
    """
    tx = np.zeros(1, dtype=complex)
    tx[0] = 1.0
    rx, _ = _link(tx, ps_per_nm, rng=None, snr_db=None, pad=pad)
    taps = _sample(rx, pad + np.arange(-half, half + 1))
    return taps


# --------------------------------------------------------------------------- #
# 1. the reference constellations
# --------------------------------------------------------------------------- #


def coherent_constellations() -> str:
    fig, axes = P.figure(height=3.0, nrows=1, ncols=3)
    limit = 1.32

    for index, (ax, (name, order, bits)) in enumerate(zip(
            axes, (("QPSK", 4, 2), ("16-QAM", 16, 4), ("64-QAM", 64, 6)))):
        pts = ideal_points(order)
        lv = qam_levels(order)

        ax.scatter(pts.real, pts.imag, s=30, color=P.ACCENT, linewidths=0,
                   zorder=3)

        # The minimum distance, drawn between two neighbours rather than
        # asserted in a caption.
        if order == 4:
            a, b = lv[1] + 1j * lv[1], lv[1] + 1j * lv[0]
            label_x, label_y, ha = a.real + 0.07, 0.0, "left"
        else:
            mid = lv.size // 2
            a, b = lv[mid] + 1j * lv[mid], lv[mid + 1] + 1j * lv[mid]
            label_x, label_y, ha = (a.real + b.real) / 2.0, a.imag + 0.10, "center"
        ax.plot([a.real, b.real], [a.imag, b.imag], color=P.NOTE,
                linewidth=1.4, zorder=2)
        ax.text(label_x, label_y, r"$d_{\min}$", color=P.NOTE, fontsize=8,
                ha=ha, va="bottom")

        P.title(ax, name, subtitle=f"{bits} bits/symbol  ·  "
                                   f"$d_{{\\min}}$ = {min_distance(order):.3f}")
        P.tidy(ax, xlabel="in-phase",
               ylabel="quadrature" if index == 0 else None)
        _square(ax, limit)

    _footnote(fig,
              "Ideal symbols, no noise, average symbol energy normalised to 1 on "
              "every panel and one shared axis: packing more bits into the same "
              "energy shrinks the distance a decision has to resolve.")
    return P.render(fig)


# --------------------------------------------------------------------------- #
# 2. what dispersion looks like in the frequency domain
# --------------------------------------------------------------------------- #


def cd_frequency_response() -> str:
    fig, axes = P.figure(height=5.6, nrows=3, ncols=1, sharex=True,
                         height_ratios=[0.85, 1.45, 0.95], hspace=0.3)
    ax_mag, ax_ph, ax_gd = axes

    f = np.linspace(-35e9, 35e9, 1401)
    f_ghz = f / 1e9
    cases = ((0.0, P.MUTED, "D·L = 0 (back-to-back)"),
             (850.0, P.NOTE, "850 ps/nm"),
             (1700.0, P.OPTICAL, "1700 ps/nm"))

    # --- magnitude: the whole point of doing this in the frequency domain ----
    ax_mag.plot(f_ghz, np.zeros_like(f_ghz), color=P.ACCENT, zorder=3)
    ax_mag.set_ylim(-30, 6)
    ax_mag.set_yticks([-20, -10, 0])
    ax_mag.text(0.0, -11, "all-pass: |H(f)| = 1, so the eye closes without any "
                          "loss of energy",
                fontsize=9.5, color=P.ACCENT_DARK, ha="center", va="center")
    ax_mag.text(0.0, -22, "flat for any amount of fibre: all three D·L curves "
                          "lie on this one line",
                fontsize=8.5, color=P.MUTED, ha="center", va="center")
    P.tidy(ax_mag, ylabel="magnitude  [dB]")

    # --- phase: a parabola, and the excursion that does the damage ----------
    for ps_per_nm, colour, label in cases:
        ax_ph.plot(f_ghz, cd_phase(f, ps_per_nm), color=colour, label=label,
                   linestyle="--" if ps_per_nm == 0 else "-")
    phi_nyq = float(cd_phase(32e9, 1700.0))
    phi_edge = float(cd_phase(35e9, 1700.0))
    ax_ph.set_ylim(-62, 62)
    ax_ph.text(0.0, 56, f"1700 ps/nm swings ±{phi_nyq:.1f} rad (±{phi_nyq / np.pi:.1f}π) "
                        f"at the ±32 GHz Nyquist edge\n"
                        f"and ±{phi_edge:.1f} rad (±{phi_edge / np.pi:.1f}π) at ±35 GHz",
               fontsize=8.5, color=P.OPTICAL, ha="center", va="center")
    ax_ph.text(0.0, 36, "quadratic in f:  $\\varphi \\propto D\\,L\\,f^{2}$, "
                        "no linear term",
               fontsize=9.5, color=P.INK, ha="center", va="center")
    P.tidy(ax_ph, ylabel="phase  [rad]", legend=[c[2] for c in cases],
           legend_loc="lower center", ncol=3)

    # --- group delay: linear in f, which is exactly a chirp -----------------
    for ps_per_nm, colour, _ in cases:
        ax_gd.plot(f_ghz, cd_group_delay(f, ps_per_nm) * 1e12, color=colour,
                   linestyle="--" if ps_per_nm == 0 else "-")
    spread_ps = 2 * abs(float(cd_group_delay(35e9, 1700.0))) * 1e12
    ax_gd.set_ylim(-560, 560)
    ax_gd.text(16, 320,
               f"−dφ/dω is linear in f: one slope, {spread_ps:.0f} ps of walk\n"
               f"across the band = {spread_ps * 1e-12 * BAUD:.0f} symbol periods "
               f"at 64 GBd",
               fontsize=8.5, color=P.INK, ha="center", va="center")
    P.tidy(ax_gd, xlabel="frequency offset from the carrier  [GHz]",
           ylabel="group delay  [ps]")

    _footnote(fig,
              "Same filter, three amounts of fibre. The magnitude never moves and "
              "the delay is perfectly linear, so equalising it is a single complex "
              "multiply per frequency bin — the hard part is knowing D·L, not "
              "undoing it.")
    return P.render(fig)


# --------------------------------------------------------------------------- #
# 3. the money figure: 16-QAM through 1700 ps/nm
# --------------------------------------------------------------------------- #


def cd_constellation_recovery() -> str:
    rng = np.random.default_rng(0)
    tx = random_qam(16, N_SYMBOLS, rng)
    rx, eq = _link(tx, CD_PS_PER_NM, rng=rng, snr_db=SNR_DB)

    positions = PAD_SYMBOLS + np.arange(N_SYMBOLS)
    rx_sym = _sample(rx, positions)
    eq_sym = _sample(eq, positions)

    evm_before = _evm_db(rx_sym, tx)
    evm_after = _evm_db(eq_sym, tx)

    taps = _discrete_channel(CD_PS_PER_NM)
    peak = int(np.argmax(np.abs(taps)))
    span = int(np.sum(np.abs(taps) > 0.01 * np.abs(taps[peak])))
    isi_db = float(10.0 * np.log10(
        (np.sum(np.abs(taps) ** 2) - abs(taps[peak]) ** 2) / abs(taps[peak]) ** 2))

    limit = float(np.ceil(1.15 * max(np.abs(rx_sym).max(), np.abs(eq_sym).max()) * 2) / 2)
    limit = max(limit, 1.5)

    fig, axes = P.figure(height=3.7, nrows=1, ncols=2)
    ideal = ideal_points(16)

    for ax, (title, stall, data, accent, note) in zip(axes, (
            ("Before: 1700 ps/nm, no equaliser",
             "16-QAM  ·  64 GBd  ·  2 samples/symbol",
             rx_sym, P.WARN,
             f"EVM = +{evm_before:.1f} dB  ({10 ** (evm_before / 20) * 100:.0f} %)\n"
             f"channel spans {span} symbols, ISI {isi_db:+.1f} dB"),
            ("After: one multiplication by $H^{*}(f)$",
             "same symbols, same noise, same scale",
             eq_sym, P.ACCENT_DARK,
             f"EVM = {evm_after:.1f} dB  ({10 ** (evm_after / 20) * 100:.1f} %)\n"
             f"= the {SNR_DB:.0f} dB receiver noise floor"))):
        ax.scatter(data.real, data.imag, s=6, alpha=0.5, linewidths=0,
                   color=P.ACCENT, zorder=2)
        ax.scatter(ideal.real, ideal.imag, s=30, color=P.INK, linewidths=0,
                   alpha=0.85, zorder=3)
        _note(ax, note, color=accent)
        P.title(ax, title, subtitle=stall)
        P.tidy(ax, xlabel="in-phase",
               ylabel="quadrature" if ax is axes[0] else None)
        _square(ax, limit)

    _footnote(fig,
              f"The all-pass carries a {BULK_DELAY} sample "
              f"({BULK_DELAY // SPS} symbol) bulk delay; symbol k is read at "
              f"output sample {BULK_DELAY} + 2k on both panels, so the only "
              f"difference between them is H*(f). Dispersion moves no energy: the "
              f"loss here ({isi_db:+.1f} dB of ISI against the main tap) is purely "
              f"phase, and one complex multiply per frequency bin recovers it.")
    return P.render(fig)


# --------------------------------------------------------------------------- #
# 4. linewidth: rotation, not translation
# --------------------------------------------------------------------------- #


def phase_noise_rings() -> str:
    order = 16
    count = 3000
    snr_db = 20.0
    rng = np.random.default_rng(0)

    tx = random_qam(order, count, rng)
    sigma = np.sqrt(10.0 ** (-snr_db / 10.0) / 2.0)
    noise = sigma * (rng.standard_normal(count) + 1j * rng.standard_normal(count))

    # One driving realisation for all three panels, scaled by each panel's
    # increment: the linewidth is then the only thing the figure varies. (The
    # RMS excursion of a Wiener path is itself a random variable with a wide
    # spread, so this draw is deliberately a typical one -- its path RMS is
    # within a few percent of the ensemble mean -- rather than a lucky outlier.)
    drive = np.random.default_rng(1).standard_normal(count)

    lv = qam_levels(order)
    radii = np.unique(np.round(np.abs(lv[:, None] + 1j * lv[None, :]), 9))
    theta = np.linspace(0.0, 2.0 * np.pi, 241)

    fig, axes = P.figure(height=3.0, nrows=1, ncols=3)
    notes = (
        ("100 kHz", "intact: the drift is far slower\nthan the symbol rate"),
        ("1 MHz", "arcs: the points rotate away\nfrom where they started"),
        ("10 MHz", "rings: a rotation about the\norigin, not an added cloud"),
    )

    for index, (ax, linewidth, (label, note)) in enumerate(zip(
            axes, (100e3, 1e6, 10e6), notes)):
        step = np.sqrt(2.0 * np.pi * linewidth / BAUD)
        phase = np.cumsum(drive) * step
        rx = tx * np.exp(1j * phase) + noise
        rms_deg = float(np.degrees(np.sqrt(np.mean(phase ** 2))))
        peak_deg = float(np.degrees(np.abs(phase).max()))

        for radius in radii:
            ax.plot(radius * np.cos(theta), radius * np.sin(theta),
                    color=P.RULE, linewidth=0.9, linestyle=(0, (3, 3)), zorder=1)
        ax.scatter(rx.real, rx.imag, s=6, alpha=0.5, linewidths=0,
                   color=P.ACCENT, zorder=2)
        _note(ax, f"RMS drift {rms_deg:.0f}°, peak {peak_deg:.0f}°\n{note}",
              color=P.WARN if linewidth > 1e6 else P.MUTED)
        P.title(ax, f"$\\Delta\\nu$ = {label}",
                subtitle=f"{np.degrees(step):.2f}°/symbol  ·  20 dB SNR")
        P.tidy(ax, xlabel="in-phase",
               ylabel="quadrature" if index == 0 else None)
        # 1.5 clears the outermost amplitude ring (|s| = 1.342 for 16-QAM) so the
        # guide circles are not clipped by the box.
        _square(ax, 1.5)

    _footnote(fig,
              "16-QAM, 3000 symbols, 64 GBd, 20 dB SNR, and the same symbols and "
              "noise draw in all three panels — only the combined "
              "transmitter + LO linewidth changes. Additive noise grows a round "
              "cloud about each ideal point; phase noise is a rotation, so it "
              "carves arcs and rings about the origin instead, over the dashed "
              "amplitude rings the symbols were sent on.")
    return P.render(fig)


FIGURES = {
    "coherent-constellations": coherent_constellations,
    "cd-frequency-response": cd_frequency_response,
    "cd-constellation-recovery": cd_constellation_recovery,
    "phase-noise-rings": phase_noise_rings,
}


# --------------------------------------------------------------------------- #
# the numbers the figures annotate, printed on demand
# --------------------------------------------------------------------------- #


def _diagnostics() -> None:
    """Print every number a figure claims, so the annotations can be audited."""
    print("link: baud = 64 GBd, D = 17 ps/(nm.km), SPS = 2, "
          f"raised-cosine beta = {BETA}")
    print(f"1700 ps/nm = {dl_si(1700.0):.3f} s/m of accumulated dispersion "
          f"(D*L, L = 100 km)")
    for f_hz in (32e9, 35e9):
        print(f"  phase at +/-{f_hz / 1e9:.0f} GHz, 1700 ps/nm: "
              f"{cd_phase(f_hz, 1700.0):.3f} rad = "
              f"{cd_phase(f_hz, 1700.0) / np.pi:.3f} pi")
    print(f"  phase at +/-35 GHz,  850 ps/nm: {cd_phase(35e9, 850.0):.3f} rad")
    f_band = np.linspace(-35e9, 35e9, 1401)
    ripple = float(np.max(np.abs(np.abs(np.exp(1j * cd_phase(f_band, 1700.0))) - 1.0)))
    print(f"  deviation of |H(f)| from 1 over the plotted band: {ripple:.2e} "
          f"({20 * np.log10(ripple):.0f} dB, i.e. flat to machine precision)")
    print(f"  group delay at +/-35 GHz, 1700 ps/nm: "
          f"{cd_group_delay(35e9, 1700.0) * 1e12:.1f} ps "
          f"-> {2 * cd_group_delay(35e9, 1700.0) * 1e12:.1f} ps of walk "
          f"= {2 * abs(cd_group_delay(35e9, 1700.0)) * BAUD:.1f} symbol periods")
    print(f"  pulse broadening 1700 ps/nm over a {BAUD / 1e9 * (1 + BETA):.1f} GHz "
          f"band: {cd_spread_symbols(1700.0):.1f} symbol periods "
          f"(+/-{cd_spread_symbols(1700.0) / 2:.1f})")

    f = np.linspace(-64e9, 64e9, 2001)
    span = 2 * abs(float(cd_group_delay(64e9, 1700.0))) * SPS * BAUD
    print(f"  band-limited chirp of the all-pass (to f_s/2 = 64 GHz): "
          f"+/-{span / 2:.0f} samples = +/-{span / 2 / SPS:.1f} symbol periods; "
          f"bulk delay {BULK_DELAY} samples = {BULK_DELAY / SPS} symbols")

    for order in (4, 16, 64):
        print(f"{order:>2}-QAM: d_min = {min_distance(order):.4f} at unit average "
              f"symbol energy")

    rng = np.random.default_rng(0)
    tx = random_qam(16, N_SYMBOLS, rng)
    rx, eq = _link(tx, CD_PS_PER_NM, rng=rng, snr_db=SNR_DB)
    pos = PAD_SYMBOLS + np.arange(N_SYMBOLS)
    rx_sym, eq_sym = _sample(rx, pos), _sample(eq, pos)
    print(f"recovery, {N_SYMBOLS} symbols, SNR = {SNR_DB:.0f} dB:")
    print(f"  EVM before equalisation: {_evm_db(rx_sym, tx):+.2f} dB "
          f"({10 ** (_evm_db(rx_sym, tx) / 20) * 100:.0f} %)  "
          f"max |y| = {np.abs(rx_sym).max():.2f}")
    print(f"  EVM after  H*(f):        {_evm_db(eq_sym, tx):+.2f} dB "
          f"({10 ** (_evm_db(eq_sym, tx) / 20) * 100:.2f} %)  "
          f"max |y| = {np.abs(eq_sym).max():.2f}")
    taps = _discrete_channel(CD_PS_PER_NM)
    peak = int(np.argmax(np.abs(taps)))
    span = int(np.sum(np.abs(taps) > 0.01 * np.abs(taps[peak])))
    isi_db = 10.0 * np.log10((np.sum(np.abs(taps) ** 2) - abs(taps[peak]) ** 2)
                             / abs(taps[peak]) ** 2)
    print(f"  symbol-spaced channel: {span} taps above -40 dB, "
          f"ISI-to-main-tap energy {isi_db:+.2f} dB, "
          f"main tap |c| = {abs(taps[peak]):.3f}")

    print("phase noise, 64 GBd, 20 dB SNR, 3000 symbols (one shared drive):")
    drive = np.random.default_rng(1).standard_normal(3000)
    print(f"  driving realisation: RMS(cumsum z) = "
          f"{np.sqrt(np.mean(np.cumsum(drive) ** 2)):.2f} normalised units, "
          f"against an ensemble mean of 2*sqrt(N/2) = {np.sqrt(3000 / 2):.1f}")
    for linewidth in (100e3, 1e6, 10e6):
        step = np.sqrt(2.0 * np.pi * linewidth / BAUD)
        phase = np.cumsum(drive) * step
        print(f"  {linewidth / 1e6:>5.1f} MHz: increment sigma = "
              f"{np.degrees(step):.3f} deg/symbol, measured drift RMS = "
              f"{np.degrees(np.sqrt(np.mean(phase ** 2))):.1f} deg, "
              f"peak |phase| = {np.degrees(np.abs(phase).max()):.0f} deg")


if __name__ == "__main__":
    _diagnostics()
