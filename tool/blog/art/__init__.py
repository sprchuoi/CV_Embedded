"""Figure generators for the blog.

Two families, both writing plain ``.svg`` files into ``docs/blog/assets/``:

``diagrams_*``
    Hand-authored block diagrams, built with :mod:`tool.blog.art.svg`. Every
    box and arrow is placed deliberately; there is no data behind them.

``plots_*``
    Real signal plots computed with numpy/matplotlib. These need the numeric
    stack, which is why they live behind the ``plots`` family and are built by
    ``tool/build_blog_assets.py`` rather than by the site build.

Figure names are globally unique and become the file names, so an article
references ``assets/plots/alias-frequency-map.svg`` and the ownership is
obvious. Adding a figure means adding it to a module's ``FIGURES`` mapping;
:func:`collect` rejects duplicates rather than silently overwriting one.
"""

from __future__ import annotations

import importlib
import re
from dataclasses import dataclass
from typing import Callable

# kind -> module names, resolved lazily so that importing the diagram
# toolchain does not require numpy.
MODULES: dict[str, tuple[str, ...]] = {
    "diagrams": (
        "diagrams_signals",
        "diagrams_quantization",
        "diagrams_decibels",
        "diagrams_sampling",
        "diagrams_fft",
        "diagrams_fir",
        "diagrams_convolution",
        "diagrams_coherent",
        "diagrams_dispersion",
        "diagrams_eth_history",
        "diagrams_eth_budget",
        "diagrams_eth_eye",
        "diagrams_eth_bert",
        "diagrams_eth_dft",
        "diagrams_eth_lab",
        "diagrams_serdes_module",
        "diagrams_serdes_anatomy",
        "diagrams_serdes_channel",
        "diagrams_serdes_equalisation",
        "diagrams_serdes_cdr",
        "diagrams_serdes_fec",
    ),
    "plots": (
        "plots_signals",
        "plots_quantization",
        "plots_decibels",
        "plots_sampling",
        "plots_fft",
        "plots_dft",
        "plots_windows",
        "plots_ztransform",
        "plots_fourier",
        "plots_fir",
        "plots_convolution",
        "plots_coherent",
        "plots_dispersion",
        "plots_eth_budget",
        "plots_eth_eye",
        "plots_eth_bert",
        "plots_eth_dft",
        "plots_eth_lab",
        "plots_serdes_module",
        "plots_serdes_anatomy",
        "plots_serdes_channel",
        "plots_serdes_equalisation",
        "plots_serdes_cdr",
        "plots_serdes_fec",
    ),
}


class FigureError(RuntimeError):
    """Raised when a figure module is missing, broken, or duplicated."""


# matplotlib derives some element ids from a hash of the artist's geometry,
# salted with ``svg.hashsalt``. The salt is fixed (plotstyle sets one), but the
# hash input is a float rendering of the clip path, so the same figure can come
# out with a different id on a different Python build and be byte-identical
# everywhere else. The committed SVGs are checked by regenerating them in CI, so
# one drifting id fails the build for no visual reason. Renaming the derived ids
# to a sequence number, in order of first appearance, leaves the output
# depending on the drawing alone.
_HASHED_ID = re.compile(r"^[pm][0-9a-f]{10}$")


def normalise_ids(markup: str) -> str:
    """Replace matplotlib's hash-derived element ids with stable ones.

    Only ids that look derived (``p`` or ``m`` followed by ten hex digits) are
    touched. The readable ones matplotlib also emits -- ``figure_1``,
    ``axes_1`` -- are left alone, so a diff of a figure still shows what
    changed.
    """
    mapping: dict[str, str] = {}
    counters: dict[str, int] = {}
    for ident in re.findall(r'\bid="([^"]+)"', markup):
        if _HASHED_ID.match(ident) and ident not in mapping:
            prefix = ident[0]
            counters[prefix] = counters.get(prefix, 0) + 1
            mapping[ident] = f"{prefix}{counters[prefix]}"
    for old, new in mapping.items():
        markup = markup.replace(f'id="{old}"', f'id="{new}"')
        markup = markup.replace(f"url(#{old})", f"url(#{new})")
        markup = markup.replace(f'href="#{old}"', f'href="#{new}"')
    return markup


@dataclass(frozen=True)
class Figure:
    name: str
    kind: str          # "diagrams" | "plots"
    builder: Callable[[], str]

    @property
    def filename(self) -> str:
        return f"{self.name}.svg"

    @property
    def relpath(self) -> str:
        return f"assets/{self.kind}/{self.filename}"


def collect(*, kinds: tuple[str, ...] | None = None) -> list[Figure]:
    """Import the requested figure modules and return every figure they expose."""
    wanted = kinds or tuple(MODULES)
    figures: list[Figure] = []
    seen: dict[str, str] = {}

    for kind in wanted:
        if kind not in MODULES:
            raise FigureError(f"unknown figure kind '{kind}'")
        for module_name in MODULES[kind]:
            dotted = f"{__name__}.{module_name}"
            try:
                module = importlib.import_module(dotted)
            except ModuleNotFoundError as exc:
                # Distinguish "the numeric stack is not installed" from "the
                # module itself is missing": both raise, but the fix is
                # completely different and the old message blamed numpy for
                # a typo in MODULES.
                if (exc.name or "").split(".")[0] in ("numpy", "matplotlib",
                                                      "scipy", "PIL"):
                    raise FigureError(
                        f"cannot import {dotted}: {exc}. Plot figures need numpy "
                        "and matplotlib -- run this with "
                        "build_environment/.venv/bin/python."
                    ) from exc
                raise FigureError(
                    f"{dotted} does not exist, but {kind} MODULES lists it. "
                    "Add the module or remove it from the list."
                ) from exc
            except ImportError as exc:  # pragma: no cover - broken module
                raise FigureError(f"cannot import {dotted}: {exc}") from exc

            registry = getattr(module, "FIGURES", None)
            if not isinstance(registry, dict) or not registry:
                raise FigureError(f"{dotted} defines no FIGURES mapping")

            for name, builder in registry.items():
                if name in seen:
                    raise FigureError(
                        f"duplicate figure '{name}' in {dotted} (already in {seen[name]})"
                    )
                seen[name] = dotted
                figures.append(Figure(name=name, kind=kind, builder=builder))

    names = [f.name for f in figures]
    if len(names) != len(set(names)):
        raise FigureError("duplicate figure names across modules")
    return sorted(figures, key=lambda f: (f.kind, f.name))
