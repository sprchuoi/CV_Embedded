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
from dataclasses import dataclass
from typing import Callable

# kind -> module names, resolved lazily so that importing the diagram
# toolchain does not require numpy.
MODULES: dict[str, tuple[str, ...]] = {
    "diagrams": (
        "diagrams_sampling",
        "diagrams_fir",
        "diagrams_coherent",
    ),
    "plots": (
        "plots_sampling",
        "plots_fir",
        "plots_coherent",
    ),
}


class FigureError(RuntimeError):
    """Raised when a figure module is missing, broken, or duplicated."""


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
            except ImportError as exc:  # pragma: no cover - environment problem
                if module_name.startswith("plots"):
                    raise FigureError(
                        f"cannot import {dotted} ({exc}). Plot figures need numpy and "
                        "matplotlib -- run this with build_environment/.venv/bin/python."
                    ) from exc
                raise

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
