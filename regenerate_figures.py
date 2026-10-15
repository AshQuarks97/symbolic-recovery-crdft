"""Rebuild every figure from the files written by Cell 4.14 of KAN_from_CRDFT.ipynb,
without refitting.

Needs, in the working directory:
    results/figure_inputs.pkl     written by Cell 4.14
    figures/panels/*.png          cached per-network panels, for Figure 1
    reactivity_dataset.csv        only for Figure 3; skipped if absent
    rsc_style.py, figures_rsc.py

    python regenerate_figures.py
"""

from __future__ import annotations

import os
import pickle
import sys

import numpy as np
import sympy as sp

sys.path.insert(0, os.getcwd())
import rsc_style as rsc          # noqa: E402
import figures_rsc as F          # noqa: E402

MIN_FIGURES_RSC = 12


def _load():
    if int(getattr(F, "__version__", "0")) < MIN_FIGURES_RSC:
        raise SystemExit(f"figures_rsc.py is v{F.__version__}; "
                         f"v{MIN_FIGURES_RSC} or newer is required.")
    path = "results/figure_inputs.pkl"
    if not os.path.exists(path):
        raise SystemExit(f"{path} not found. Run Cell 4.14 of the notebook first.")
    with open(path, "rb") as fh:
        return pickle.load(fh)


def _parity_inputs():
    """Rebuild the Figure 3 inputs from the CSV (the pickle stores no bulk arrays)."""
    import pandas as pd

    csv = "reactivity_dataset.csv"
    if not os.path.exists(csv):
        print(f"  Figure 3 skipped: {csv} not in the working directory.")
        return None, None

    df = pd.read_csv(csv)
    df = (df[df["eta"] > 0].replace([np.inf, -np.inf], np.nan)
            .dropna().reset_index(drop=True))
    IP, EA = df["IP"].values, df["EA"].values
    chi, eta = df["chi"].values, df["eta"].values
    Ap, Am = np.abs(IP + 3 * EA), np.abs(3 * IP + EA)

    IP_s, EA_s, chi_s, eta_s, Ap_s, Am_s = sp.symbols(
        "IP EA chi eta A_plus A_minus")
    val = {
        "mu":     (-(IP_s + EA_s) / 2, {IP_s: IP, EA_s: EA}, "mu"),
        "chi":    ((IP_s + EA_s) / 2, {IP_s: IP, EA_s: EA}, "chi"),
        "eta":    (IP_s - EA_s, {IP_s: IP, EA_s: EA}, "eta"),
        "S":      (1 / eta_s, {eta_s: eta}, "S"),
        "Nmax":   (chi_s / eta_s, {chi_s: chi, eta_s: eta}, "Nmax"),
        "omega":  (chi_s ** 2 / (2 * eta_s), {chi_s: chi, eta_s: eta}, "omega"),
        "wplus":  (Ap_s ** 2 / (16 * eta_s), {Ap_s: Ap, eta_s: eta}, "omega_plus"),
        "wminus": (Am_s ** 2 / (16 * eta_s), {Am_s: Am, eta_s: eta}, "omega_minus"),
    }
    return df, val


def main():
    d = _load()
    rsc.use()
    made, skipped = [], []

    def _try(tag, fn, *a):
        try:
            fn(*a)
            made.append(tag)
        except Exception as exc:                      # never let one figure stop the rest
            skipped.append(f"{tag}: {exc}")

    _try("fig01", F.fig01_kan_diagrams, d["affine_out"], d["log_out"])

    # Replay the stored anchor. Use "ols_slopes" (the raw least-squares solution), not
    # "slopes" (the same values snapped to exact rationals): the figure plots the anchor's
    # ~1e-15 deviation, and snapped values deviate by exactly zero.
    def log_ols(feats, ycol):
        key = [k for k, v in d["ycol_of"].items() if v == ycol][0]
        return [float(x) for x in d["log_out"][key]["ols_slopes"]], 0.0

    _try("fig02", F.fig02_exponents, d["log_out"], log_ols,
         d["feat_of"], d["ycol_of"], d["ref_exp"])

    df, val = _parity_inputs()
    if df is not None:
        _try("fig03", F.fig03_parity, df, val)
    else:
        skipped.append("fig03: reactivity_dataset.csv absent")

    _try("fig04", F.fig04_learning_curves, d["affine_out"], d["log_out"])

    opt_hist = {eval(k) if isinstance(k, str) and k.startswith("(") else k: v
                for k, v in d["opt_hist"].items()}
    _try("fig05", F.fig05_optimizer, opt_hist, [tuple(r) for r in d["opt_rows"]])
    _try("fig06", F.fig06_spline_stability, d["gk_rows"])
    if "noise_summary" in d:
        _try("fig07", F.fig07_noise, d["noise_summary"])
    if "size_rows" in d:
        _try("figC1", F.fig_trainsize, d["size_rows"])

    print(f"\nrebuilt: {', '.join(made) if made else 'nothing'}")
    for s in skipped:
        print(f"  not rebuilt -> {s}")
    print(f"output in {rsc.FIGDIR.resolve()}")


if __name__ == "__main__":
    main()
