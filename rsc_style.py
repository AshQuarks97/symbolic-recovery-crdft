"""
Matplotlib styling helpers for Royal Society of Chemistry figures.

RSC artwork specification: single-column width 8.3 cm, double-column width
17.1 cm, maximum height 23.3 cm, raster resolution at least 600 dpi.
Accepted formats are TIFF (preferred for production), EPS, PDF, PNG, JPEG.
"""

from __future__ import annotations

import os
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt

__all__ = [
    "use", "figure", "subplots", "save", "finish", "panel_label",
    "SINGLE", "DOUBLE", "MAX_HEIGHT", "C", "CYCLE", "FIGDIR",
]

# Canvas geometry in inches, converted from the RSC specification in cm.
CM = 1.0 / 2.54
SINGLE = 8.3 * CM
ONE_HALF = 12.7 * CM     # intermediate width, not part of the RSC spec
DOUBLE = 17.1 * CM
MAX_HEIGHT = 23.3 * CM

FIGDIR = Path(os.environ.get("RSC_FIGDIR", "figures"))

# Okabe and Ito color-blind-safe palette.
C = {
    "black":     "#000000",
    "orange":    "#E69F00",
    "skyblue":   "#56B4E9",
    "green":     "#009E73",
    "yellow":    "#F0E442",
    "blue":      "#0072B2",
    "vermilion": "#D55E00",
    "purple":    "#CC79A7",
    "grey":      "#7F7F7F",
}

CYCLE = [C["blue"], C["vermilion"], C["green"], C["orange"],
         C["purple"], C["skyblue"], C["black"], C["yellow"]]


def use(base_fontsize: float = 7.0, serif: bool = False) -> None:
    """Apply RSC-compatible rcParams globally.

    `base_fontsize` is in points at the final printed size; 7 pt is the
    practical floor for legibility.
    """
    family = "serif" if serif else "sans-serif"

    mpl.rcParams.update({
        "font.family": family,
        "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans",
                            "Liberation Sans", "sans-serif"],
        "font.serif": ["Times New Roman", "DejaVu Serif", "serif"],
        "font.size": base_fontsize,
        "axes.labelsize": base_fontsize,
        "axes.titlesize": base_fontsize,
        "xtick.labelsize": base_fontsize - 0.5,
        "ytick.labelsize": base_fontsize - 0.5,
        "legend.fontsize": base_fontsize - 0.5,
        "figure.titlesize": base_fontsize + 1,

        "mathtext.fontset": "dejavusans" if not serif else "dejavuserif",
        "mathtext.default": "regular",

        "figure.figsize": (SINGLE, SINGLE * 0.75),
        "figure.dpi": 150,          # screen preview only
        "savefig.dpi": 600,         # RSC minimum for raster output
        "figure.constrained_layout.use": True,
        "figure.constrained_layout.h_pad": 0.02,
        "figure.constrained_layout.w_pad": 0.02,
        "figure.constrained_layout.hspace": 0.03,
        "figure.constrained_layout.wspace": 0.03,

        "lines.linewidth": 1.0,
        "lines.markersize": 3.0,
        "lines.markeredgewidth": 0.6,
        "patch.linewidth": 0.6,
        "errorbar.capsize": 1.8,

        "axes.linewidth": 0.6,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": False,
        "axes.axisbelow": True,
        "axes.prop_cycle": mpl.cycler(color=CYCLE),
        "axes.labelpad": 2.0,
        "axes.titlepad": 3.0,

        "xtick.direction": "out",
        "ytick.direction": "out",
        "xtick.major.width": 0.6,
        "ytick.major.width": 0.6,
        "xtick.minor.width": 0.45,
        "ytick.minor.width": 0.45,
        "xtick.major.size": 2.5,
        "ytick.major.size": 2.5,
        "xtick.minor.size": 1.4,
        "ytick.minor.size": 1.4,
        "xtick.major.pad": 2.0,
        "ytick.major.pad": 2.0,

        # grid (off by default)
        "grid.color": "#D9D9D9",
        "grid.linewidth": 0.4,
        "grid.alpha": 1.0,

        "legend.frameon": False,
        "legend.handlelength": 1.6,
        "legend.handletextpad": 0.5,
        "legend.columnspacing": 1.0,
        "legend.labelspacing": 0.3,
        "legend.borderaxespad": 0.3,

        # output. Must stay None: bbox="tight" re-crops the canvas and changes
        # the final width away from the exact RSC column.
        "savefig.bbox": None,
        "savefig.pad_inches": 0.0,
        "savefig.transparent": False,
        "savefig.facecolor": "white",
        # 42 embeds TrueType fonts rather than converting text to paths
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "svg.fonttype": "none",
    })


def _resolve_width(width) -> float:
    """Map 'single'/'onehalf'/'double' or a number in cm to inches."""
    if isinstance(width, str):
        key = width.lower().replace("-", "").replace("_", "")
        table = {"single": SINGLE, "1": SINGLE,
                 "onehalf": ONE_HALF, "1.5": ONE_HALF,
                 "double": DOUBLE, "2": DOUBLE, "full": DOUBLE}
        if key not in table:
            raise ValueError(f"unknown width {width!r}; use single/onehalf/double")
        return table[key]
    return float(width) * CM          # a number is read as cm


def figure(width="single", height=6.0, **kwargs):
    """Return (fig, ax) sized to an RSC column.

    `width` is 'single' | 'onehalf' | 'double' or a number in cm. `height` is
    in cm and is clipped to the RSC maximum of 23.3 cm.
    """
    w = _resolve_width(width)
    h = min(float(height) * CM, MAX_HEIGHT)
    return plt.subplots(figsize=(w, h), **kwargs)


def subplots(nrows=1, ncols=1, width="double", height=6.0, **kwargs):
    """Return (fig, axes) for a grid of panels; widths and heights as in figure()."""
    w = _resolve_width(width)
    h = min(float(height) * CM, MAX_HEIGHT)
    return plt.subplots(nrows, ncols, figsize=(w, h), **kwargs)


def panel_label(ax, letter, x=-0.02, y=1.03, **kwargs):
    """Add a bold panel label; x and y are in axes coordinates."""
    opts = dict(fontsize=mpl.rcParams["font.size"] + 1, fontweight="bold",
                ha="right", va="bottom", transform=ax.transAxes)
    opts.update(kwargs)
    return ax.text(x, y, f"({letter})", **opts)


def finish(fig, tight=False):
    """Return `fig` with spine widths reset to the rcParam value."""
    for ax in fig.get_axes():
        for spine in ax.spines.values():
            spine.set_linewidth(mpl.rcParams["axes.linewidth"])
    if tight:
        fig.set_layout_engine("tight")
    return fig


def save(fig, stem, formats=("pdf", "tiff"), dpi=600, outdir=None,
         close=False, verbose=True):
    """Write `fig` to `outdir/stem.<ext>` per format and return the paths.

    PDF is the vector master. RSC production wants TIFF at 600 dpi with LZW
    compression.
    """
    outdir = Path(outdir) if outdir is not None else FIGDIR
    outdir.mkdir(parents=True, exist_ok=True)

    written = []
    for ext in formats:
        path = outdir / f"{stem}.{ext}"
        kw = {"dpi": dpi, "bbox_inches": None}
        if ext in ("tif", "tiff"):
            kw["pil_kwargs"] = {"compression": "tiff_lzw"}
        fig.savefig(path, **kw)
        written.append(path)

    if verbose:
        w_in, h_in = fig.get_size_inches()
        print(f"  saved {stem}: {w_in * 2.54:.1f} x {h_in * 2.54:.1f} cm  ->  "
              + ", ".join(p.name for p in written))
    if close:
        plt.close(fig)
    return written


def check(fig, width="double"):
    """Return True if `fig` fits the RSC size envelope, printing any violation."""
    w_in, h_in = fig.get_size_inches()
    target = _resolve_width(width)
    msgs = []
    if abs(w_in - target) > 0.02:
        msgs.append(f"width {w_in*2.54:.2f} cm != {target*2.54:.2f} cm target")
    if h_in > MAX_HEIGHT + 1e-6:
        msgs.append(f"height {h_in*2.54:.2f} cm exceeds 23.3 cm maximum")
    if msgs:
        print("  [RSC check] " + "; ".join(msgs))
    return not msgs
