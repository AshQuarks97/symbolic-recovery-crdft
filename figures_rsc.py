"""
Manuscript figures for `KAN_from_CRDFT.ipynb`, styled to the RSC artwork
specification (see `rsc_style.py`).

Each function takes objects the notebook has already computed, writes
`figures/figNN_*.pdf` and a 600 dpi TIFF, and returns the figure. Nothing here
re-fits a model.
"""

from __future__ import annotations

__version__ = "12"   # checked by the notebook's bootstrap cell

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import sympy as sp

import rsc_style as rsc

PANELS = "abcdefghijklmnop"

# Descriptor key -> LaTeX label used in the manuscript.
TEX = {
    "mu": r"$\mu$",
    "chi": r"$\chi$",
    "eta": r"$\eta$",
    "S": r"$S$",
    "Nmax": r"$\Delta N_{\max}$",
    "omega": r"$\omega$",
    "wplus": r"$\omega^{+}$",
    "omega_plus": r"$\omega^{+}$",
    "wminus": r"$\omega^{-}$",
    "omega_minus": r"$\omega^{-}$",
}


# Figure 1: pruned, symbolic KAN diagrams (8 panels)
def fig01_kan_diagrams(affine_out, log_out, panel_dpi=600, stem="fig01_kan_diagrams"):
    """Return a 2x4 composite of the pruned KAN diagrams.

    pykan draws onto the current figure, so each network is first rasterized to
    its own PNG at `panel_dpi` and the panels are then composited.
    """
    # Input and output node labels per descriptor.
    LAB = {
        "mu":     ([r"$IP$", r"$EA$"], [r"$\mu$"]),
        "chi":    ([r"$IP$", r"$EA$"], [r"$\chi$"]),
        "eta":    ([r"$IP$", r"$EA$"], [r"$\eta$"]),
        "S":      ([r"$\ln\eta$"], [r"$\ln S$"]),
        "Nmax":   ([r"$\ln\chi$", r"$\ln\eta$"], [r"$\ln\Delta N_{\max}$"]),
        "omega":  ([r"$\ln\chi$", r"$\ln\eta$"], [r"$\ln\omega$"]),
        # A^+ = |IP+3EA| and A^- = |3IP+EA|; define both in the caption.
        "wplus":  ([r"$\ln A^{+}$", r"$\ln\eta$"], [r"$\ln\omega^{+}$"]),
        "wminus": ([r"$\ln A^{-}$", r"$\ln\eta$"], [r"$\ln\omega^{-}$"]),
    }
    order = [
        ("mu", affine_out["mu"], False),
        ("chi", affine_out["chi"], False),
        ("eta", affine_out["eta"], False),
        ("S", log_out["S"], True),
        ("Nmax", log_out["Nmax"], True),
        ("omega", log_out["omega"], True),
        ("wplus", log_out["wplus"], True),
        ("wminus", log_out["wminus"], True),
    ]

    tmp = rsc.FIGDIR / "panels"
    tmp.mkdir(parents=True, exist_ok=True)

    paths = []
    for name, res, _ in order:
        p_cached = tmp / f"{stem}_{name}.png"
        if "model" not in res:
            # Fall back to panels cached by an earlier run.
            if p_cached.exists():
                paths.append(p_cached)
                continue
            raise KeyError(
                f"{name}: no pruned model stored and no cached panel at {p_cached}. "
                "Re-run the fits with return_model=True, or restore the figures/panels/ "
                "folder written by the original run.")
        iv, ov = LAB[name]
        try:
            res["model"].plot(in_vars=iv, out_vars=ov, varscale=0.45)
        except TypeError:                 # pykan versions without in_vars/out_vars
            res["model"].plot()
        panel = plt.gcf()
        panel.set_size_inches(rsc.DOUBLE / 4, rsc.DOUBLE / 4)
        p = tmp / f"{stem}_{name}.png"
        panel.savefig(p, dpi=panel_dpi, bbox_inches="tight", pad_inches=0.06,
                      facecolor="white")
        plt.close(panel)
        paths.append(p)

    fig, axes = rsc.subplots(2, 4, width="double", height=9.0)
    for k, ((name, _res, is_log), path, ax) in enumerate(
            zip(order, paths, axes.ravel())):
        ax.imshow(plt.imread(path), interpolation="none")
        ax.set_axis_off()

        rsc.panel_label(ax, PANELS[k], x=0.02, y=0.94, ha="left", va="top")

    rsc.finish(fig)
    rsc.check(fig, "double")
    rsc.save(fig, stem)
    return fig


# Figure 2: recovered vs reference exponents, with the log-OLS anchor
def fig02_exponents(log_out, log_ols, feat_of, ycol_of, ref_exp,
                    stem="fig02_exponents", scale="log"):
    """Bar chart of each recovered exponent minus its exact reference value.

    The KAN slopes plotted are the raw, un-snapped ones. `scale="log"`
    delegates to `_fig02_log`.
    """
    keys = ["S", "Nmax", "omega", "wplus", "wminus"]
    labels = [TEX[k] for k in keys]
    kan_n, ols_n, kan_d, ols_d = [], [], [], []

    for key in keys:
        feats = feat_of[key]
        ols_s, _ = log_ols(feats, ycol_of[key])
        res = log_out[key]

        if len(feats) == 2:                     # (numerator feature, eta)
            rn = ref_exp[key][0]
            kan_n.append(res["raw_slopes"][0] - rn)
            ols_n.append(float(ols_s[0]) - rn)
            rd = ref_exp[key][1]
            kan_d.append(res["raw_slopes"][1] - rd)
            ols_d.append(float(ols_s[1]) - rd)
        else:                                   # univariate S: eta alone
            kan_n.append(np.nan); ols_n.append(np.nan)
            rd = ref_exp[key][1]
            kan_d.append(res["raw_slopes"][0] - rd)
            ols_d.append(float(ols_s[0]) - rd)

    missing = [labels[i] for i, v in enumerate(kan_d) if not np.isfinite(v)]
    if missing:
        print(f"  [fig02] raw KAN slope unavailable (NaN) for: {missing}")

    fig, axes = rsc.subplots(1, 2, width="double", height=5.4)
    x = np.arange(len(keys))
    w = 0.34

    if scale == "log":
        return _fig02_log(fig, axes, keys, labels, x, w,
                          kan_n, ols_n, kan_d, ols_d, stem)

    for ax, kan, ols, title in [
            (axes[0], kan_n, ols_n, "numerator feature"),
            (axes[1], kan_d, ols_d, r"$\eta$")]:
        ax.bar(x - w / 2, kan, w, label="KAN (raw slope)",
               color=rsc.C["skyblue"], edgecolor=rsc.C["blue"], linewidth=0.5)
        # Anchor deviations are ~1e-15 on an axis spanning ~1e-4, so these bars
        # have no visible height and the legend label says so.
        ax.bar(x + w / 2, ols, w,
               label=r"log-OLS anchor ($|\Delta|\sim10^{-15}$: too small to see)",
               color=rsc.C["orange"], edgecolor=rsc.C["vermilion"], linewidth=0.5)
        ax.axhline(0, color=rsc.C["black"], linewidth=0.8, zorder=3)

        # Annotation offsets below are in points, not data units.
        for xi, v in zip(x, kan):
            if not np.isfinite(v):
                ax.annotate("n/a", (xi - w / 2, 0), xytext=(0, 3),
                            textcoords="offset points", ha="center", va="bottom",
                            fontsize=5, color=rsc.C["grey"], annotation_clip=False)
                continue
            lab = f"{v:+.3f}" if abs(v) >= 0.01 else f"{v:+.1e}".replace("e-0", "e-")
            ax.annotate(lab, (xi - w / 2, v), xytext=(0, -2 if v < 0 else 2),
                        textcoords="offset points", ha="center",
                        va="top" if v < 0 else "bottom", fontsize=5, color=rsc.C["blue"])
        ax.set_xticks(x)
        ax.set_xticklabels(labels)
        ax.set_ylabel("recovered $-$ reference")
        ax.set_title(f"Exponent of {title}")
        ax.margins(y=0.25)
        ax.ticklabel_format(axis="y", style="sci", scilimits=(-2, 2), useMathText=True)

    rsc.panel_label(axes[0], "a", x=-0.13)   # clear of the y-axis offset text
    rsc.panel_label(axes[1], "b", x=-0.13)
    # "outside lower center" makes constrained_layout reserve a strip for the legend.
    _h, _l = axes[0].get_legend_handles_labels()
    fig.legend(_h, _l, loc="outside lower center", ncol=2, frameon=False)

    rsc.finish(fig)
    rsc.check(fig, "double")
    rsc.save(fig, stem)
    return fig


def _fig02_log(fig, axes, keys, labels, x, w, kan_n, ols_n, kan_d, ols_d, stem):
    """Variant of fig02_exponents with |deviation| on a logarithmic axis.

    Signs are dropped here; the signed values are listed in Table 3.
    """
    FLOOR = 1e-16          # exact zeros would be at -inf on a log axis

    for k, (ax, kan, ols, title) in enumerate([
            (axes[0], kan_n, ols_n, "numerator feature"),
            (axes[1], kan_d, ols_d, r"$\eta$")]):
        kb = [FLOOR if not np.isfinite(v) else max(abs(v), FLOOR) for v in kan]
        ob = [FLOOR if not np.isfinite(v) else max(abs(v), FLOOR) for v in ols]
        ax.bar(x - w / 2, kb, w, bottom=FLOOR, label="KAN (raw slope)",
               color=rsc.C["skyblue"], edgecolor=rsc.C["blue"], linewidth=0.5)
        ax.bar(x + w / 2, ob, w, bottom=FLOOR, label="log-OLS anchor",
               color=rsc.C["orange"], edgecolor=rsc.C["vermilion"], linewidth=0.5)
        ax.set_yscale("log")
        ax.set_ylim(FLOOR, 1e-2)
        ax.axhline(0.25, ls=":", lw=0.6, color=rsc.C["grey"])
        for xi, v in zip(x, kan):
            if not np.isfinite(v):
                ax.annotate("n/a", (xi - w / 2, FLOOR), xytext=(0, 3),
                            textcoords="offset points", ha="center", va="bottom",
                            fontsize=5, color=rsc.C["grey"], annotation_clip=False)
        ax.set_xticks(x)
        ax.set_xticklabels(labels)
        ax.set_ylabel(r"$|$recovered $-$ reference$|$")
        ax.set_title(f"Exponent of {title}")
        rsc.panel_label(ax, PANELS[k], x=-0.13)

    _h, _l = axes[0].get_legend_handles_labels()
    fig.legend(_h, _l, loc="outside lower center", ncol=2, frameon=False)
    rsc.finish(fig)
    rsc.check(fig, "double")
    rsc.save(fig, stem)
    return fig


# Figure 3: parity plots for the eight recovered closed forms
def fig03_parity(df, val, max_points=8000, rng_seed=0, stem="fig03_parity"):
    """Eight parity panels, one per recovered closed form.

    `max_points` caps the scatter at a random subsample to keep the vector file
    small. The reported R^2 is computed on the full set.
    """
    rng = np.random.default_rng(rng_seed)
    fig, axes = rsc.subplots(2, 4, width="double", height=9.0)

    for k, (ax, (name, (expr, sub, col))) in enumerate(zip(axes.ravel(), val.items())):
        f = sp.lambdify(list(sub.keys()), expr, "numpy")
        ref = df[col].values.astype(float)
        pred = np.broadcast_to(f(*sub.values()), ref.shape).astype(float)

        r2 = 1.0 - np.var(ref - pred) / np.var(ref)

        n = len(ref)
        idx = rng.choice(n, size=min(max_points, n), replace=False)
        ax.scatter(ref[idx], pred[idx], s=1.5, alpha=0.25, linewidths=0,
                   color=rsc.C["blue"], rasterized=True)

        # Several descriptors are heavy-tailed, so strictly positive quantities
        # get logarithmic axes.
        positive = float(min(ref.min(), pred.min())) > 0
        if positive:
            ax.set_xscale("log")
            ax.set_yscale("log")
        lo = float(min(ref.min(), pred.min()))
        hi = float(max(ref.max(), pred.max()))
        ax.plot([lo, hi], [lo, hi], ls="--", lw=0.7, color=rsc.C["black"])
        ax.set_xlim(lo, hi)
        ax.set_ylim(lo, hi)
        ax.set_aspect("equal", adjustable="box")
        if positive:
            # Minor tick labels collide at 6.5 pt on a narrow log range.
            ax.xaxis.set_minor_formatter(mpl.ticker.NullFormatter())
            ax.yaxis.set_minor_formatter(mpl.ticker.NullFormatter())

        ax.set_title(f"{TEX[name]}   $R^2 = {r2:.6f}$")
        if k >= 4:
            ax.set_xlabel("reference")
        if k % 4 == 0:
            ax.set_ylabel("recovered")
        rsc.panel_label(ax, PANELS[k])

    rsc.finish(fig)
    rsc.check(fig, "double")
    rsc.save(fig, stem)
    return fig


# Figure 4: learning curves for the headline fits
def fig04_learning_curves(affine_out, log_out, stem="fig04_learning_curves"):
    curves = [("mu", affine_out["mu"]), ("chi", affine_out["chi"]),
              ("eta", affine_out["eta"]), ("S", log_out["S"]),
              ("Nmax", log_out["Nmax"]), ("omega", log_out["omega"]),
              ("wplus", log_out["wplus"]), ("wminus", log_out["wminus"])]

    fig, axes = rsc.subplots(2, 4, width="double", height=7.5, sharex=True)

    for k, (ax, (name, res)) in enumerate(zip(axes.ravel(), curves)):
        h = res["hist"]
        ax.semilogy(h["train_loss"], color=rsc.C["blue"], label="train")
        ax.semilogy(h["test_loss"], color=rsc.C["vermilion"], ls="--",
                    label="test")
        ax.set_title(TEX[name])
        if k >= 4:
            ax.set_xlabel("L-BFGS step")
        if k % 4 == 0:
            ax.set_ylabel("RMSE")
        rsc.panel_label(ax, PANELS[k])

    axes.ravel()[0].legend(loc="upper right")
    rsc.finish(fig)
    rsc.check(fig, "double")
    rsc.save(fig, stem)
    return fig


# Figure 5: optimizer study
def fig05_optimizer(opt_hist, opt_rows, stem="fig05_optimizer"):
    """Convergence for two descriptors (panels a, b) and wall-clock cost (panel c).

    `opt_hist` is keyed by (descriptor, optimizer, budget). Each row of
    `opt_rows` is (descriptor, optimizer, budget, _, wall_clock_seconds).
    """
    descs = sorted({k[0] for k in opt_hist})
    style = {"LBFGS": dict(color=rsc.C["blue"], ls="-"),
             "Adam": dict(color=rsc.C["vermilion"], ls="--")}

    fig, axes = rsc.subplots(1, 3, width="double", height=4.8)

    for k, (ax, desc) in enumerate(zip(axes[:2], descs)):
        for (d, opt, budget), h in sorted(opt_hist.items()):
            if d != desc:
                continue
            kw = dict(style.get(opt, {}))
            if opt == "Adam" and budget > min(b for (dd, oo, b) in opt_hist
                                              if dd == d and oo == "Adam"):
                kw["ls"] = ":"
            ax.semilogy(h["test_loss"], label=f"{opt}, {budget} steps",
                        linewidth=0.9, **kw)
        ax.set_title(TEX.get(desc, desc))
        ax.set_xlabel("optimizer step")
        ax.set_ylabel("test RMSE")
        ax.legend(loc="upper right")
        rsc.panel_label(ax, PANELS[k])

    ax = axes[2]
    lbl = [f"{TEX.get(r[0], r[0])}\n{r[1]} {r[2]}" for r in opt_rows]
    wall = [r[4] for r in opt_rows]
    colors = [style.get(r[1], {}).get("color", rsc.C["grey"]) for r in opt_rows]
    ax.barh(np.arange(len(wall)), wall, color=colors, edgecolor="none")
    ax.set_yticks(np.arange(len(wall)))
    ax.set_yticklabels(lbl)
    ax.invert_yaxis()
    ax.set_xlabel("wall-clock / s")
    ax.set_title("Cost")
    rsc.panel_label(ax, PANELS[2])

    rsc.finish(fig)
    rsc.check(fig, "double")
    rsc.save(fig, stem)
    return fig


# Figure 6: spline grid and order sensitivity
def fig06_spline_stability(gk_rows, stem="fig06_spline_stability"):
    """Raw KAN exponents across spline (grid, k), with the spline R^2 on a twin axis.

    Each row must be the 8-field tuple from PATCH_GRIDK_STUDY in `patches.py`:
        (grid, k, p_chi_ols, p_eta_ols, prefactor, r2_log, raw_chi, raw_eta)
    with an optional 9th field, the symbolic read-out R^2. The raw per-network
    slopes are plotted; the log-OLS `slopes` are constant in (grid, k).
    """
    if any(len(r) < 8 for r in gk_rows):
        raise ValueError(
            "gk_rows is in the legacy 6-field format, whose exponent columns are "
            "the log-OLS anchor and are constant by construction. Re-run Cell "
            "4.10 with PATCH_GRIDK_STUDY from patches.py so raw KAN slopes are "
            "recorded, then rebuild this figure.")

    fig, ax = rsc.figure(width="single", height=6.8)
    xs = [f"g{g}\nk{k}" for g, k, *_ in gk_rows]
    x = np.arange(len(gk_rows))

    ax.axhline(2, ls=":", lw=0.6, color=rsc.C["grey"])
    ax.axhline(-1, ls=":", lw=0.6, color=rsc.C["grey"])
    ax.plot(x, [r[6] for r in gk_rows], "o-", color=rsc.C["blue"],
            label=r"$p_\chi$ from KAN")
    ax.plot(x, [r[7] for r in gk_rows], "s-", color=rsc.C["vermilion"],
            label=r"$p_\eta$ from KAN")
    ax.set_xticks(x)
    ax.set_xticklabels(xs)
    ax.set_ylabel("recovered exponent")
    ax.set_xlabel("spline grid / order")
    ax.set_ylim(-2.2, 3.2)

    ax2 = ax.twinx()
    ax2.spines["right"].set_visible(True)
    r2s = [r[5] for r in gk_rows]
    ax2.plot(x, r2s, "^--", color=rsc.C["green"],
             markersize=2.6, label=r"spline $R^2$")
    lo = min(r2s)
    if all(len(r) >= 9 for r in gk_rows):          # symbolic read-out R^2
        r2r = [r[8] for r in gk_rows]
        ax2.plot(x, r2r, "v:", color=rsc.C["purple"], markersize=2.6,
                 label=r"symbolic read-out $R^2$")
        lo = min(lo, np.nanmin(r2r))
    ax2.set_ylabel(r"$R^2$", color=rsc.C["green"])
    ax2.tick_params(axis="y", colors=rsc.C["green"])
    ax2.set_ylim(min(0.6, lo - 0.05), 1.02)

    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, loc="lower center", bbox_to_anchor=(0.5, 1.01),
              ncol=2, borderaxespad=0.0)

    rsc.finish(fig)
    rsc.check(fig, "single")
    rsc.save(fig, stem)
    return fig


# Figure 7: robustness to multiplicative noise
def fig07_noise(noise_summary, stem="fig07_noise"):
    """One panel per descriptor of recovered exponent against noise sigma.

    `noise_summary` maps descriptor -> dict with keys sigmas, num_mean,
    num_std, eta_mean, eta_std, num_ref, eta_ref.
    """
    names = list(noise_summary)
    fig, axes = rsc.subplots(1, len(names), width="double", height=5.0,
                             sharey=True)
    axes = np.atleast_1d(axes)

    for k, (ax, name) in enumerate(zip(axes, names)):
        d = noise_summary[name]
        s = np.asarray(d["sigmas"])
        ax.errorbar(s, d["num_mean"], yerr=d["num_std"], marker="o",
                    color=rsc.C["blue"], label="numerator exponent")
        ax.errorbar(s, d["eta_mean"], yerr=d["eta_std"], marker="s",
                    color=rsc.C["vermilion"], label=r"$\eta$ exponent")
        ax.axhline(d["num_ref"], ls=":", lw=0.6, color=rsc.C["grey"])
        ax.axhline(d["eta_ref"], ls=":", lw=0.6, color=rsc.C["grey"])
        ax.set_xlabel(r"log-space noise $\sigma$")
        ax.set_title(TEX.get(name, name))
        if k == 0:
            ax.set_ylabel("recovered exponent")
            ax.legend(loc="center left")
        rsc.panel_label(ax, PANELS[k])

    rsc.finish(fig)
    rsc.check(fig, "double")
    rsc.save(fig, stem)
    return fig


def fig_trainsize(rows, stem="figC1_trainsize"):
    """Exponent error (panel a) and wall-clock cost (panel b) against training size.

    `rows` is a list of dicts with keys name, n_fit (training-set size), p_num,
    p_eta, num_ref, eta_ref (exact values) and wall (seconds).
    """
    names = sorted({r["name"] for r in rows}, key=lambda z: str(z))
    fig, axes = rsc.subplots(1, 2, width="double", height=5.4)

    ax = axes[0]
    marks = ["o", "s", "^", "D"]
    floor = 1e-6          # deviations below this are plotted at the floor
    for j, name in enumerate(names):
        rs = sorted((r for r in rows if r["name"] == name), key=lambda r: r["n_fit"])
        n = [r["n_fit"] for r in rs]
        dn = [max(abs(r["p_num"] - r["num_ref"]), floor) for r in rs]
        de = [max(abs(r["p_eta"] - r["eta_ref"]), floor) for r in rs]
        _c = rsc.CYCLE[j % len(rsc.CYCLE)]      # one color per descriptor
        ax.plot(n, dn, marker=marks[j % len(marks)], color=_c, ls="-",
                label=f"{TEX.get(name, name)}: numerator")
        ax.plot(n, de, marker=marks[j % len(marks)], color=_c, ls="--", alpha=0.65,
                label=f"{TEX.get(name, name)}: " + r"$\eta$")
    ax.axhline(0.25, ls=":", lw=0.7, color=rsc.C["grey"])
    ax.annotate("half-integer rounding tolerance", xy=(n[0], 0.25),
                xytext=(2, 3), textcoords="offset points",
                fontsize=plt.rcParams["font.size"] - 1.5, color=rsc.C["grey"])
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("training-set size")
    ax.set_ylabel("|exponent $-$ exact|")
    ax.legend(loc="center left", bbox_to_anchor=(1.02, 0.5), borderaxespad=0.0,
              fontsize=plt.rcParams["font.size"] - 1.5)
    rsc.panel_label(ax, "a")

    ax = axes[1]
    for j, name in enumerate(names):
        rs = sorted((r for r in rows if r["name"] == name), key=lambda r: r["n_fit"])
        ax.plot([r["n_fit"] for r in rs], [r["wall"] for r in rs],
                marker=marks[j % len(marks)], color=rsc.CYCLE[j % len(rsc.CYCLE)],
                label=TEX.get(name, name))
    # Linear-scaling guide, anchored on the second point: the first fit of the
    # sweep carries one-off warm-up cost.
    rs0 = sorted((r for r in rows if r["name"] == names[0]), key=lambda r: r["n_fit"])
    _a = rs0[1] if len(rs0) > 1 else rs0[0]
    n0, w0 = _a["n_fit"], _a["wall"]
    nn = np.array([r["n_fit"] for r in rs0], dtype=float)
    ax.plot(nn, w0 * nn / n0, ls=":", lw=0.7, color=rsc.C["grey"],
            label="linear in size")
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("training-set size")
    ax.set_ylabel("wall-clock / s")
    ax.legend(loc="upper left")
    rsc.panel_label(ax, "b")

    rsc.finish(fig)
    rsc.check(fig, "double")
    rsc.save(fig, stem)
    return fig

def build_all(ns):
    """Rebuild every figure from a namespace dict (e.g. `globals()`)."""
    rsc.use()
    out = {}
    out["fig01"] = fig01_kan_diagrams(ns["affine_out"], ns["log_out"])
    out["fig02"] = fig02_exponents(ns["log_out"], ns["log_ols"], ns["feat_of"],
                                   ns["ycol_of"], ns["ref_exp"])
    out["fig03"] = fig03_parity(ns["df"], ns["val"])
    out["fig04"] = fig04_learning_curves(ns["affine_out"], ns["log_out"])
    out["fig05"] = fig05_optimizer(ns["opt_hist"], ns["opt_rows"])
    out["fig06"] = fig06_spline_stability(ns["gk_rows"])
    if "noise_summary" in ns:
        out["fig07"] = fig07_noise(ns["noise_summary"])
    if "size_rows" in ns:
        out["figC1"] = fig_trainsize(ns["size_rows"])
    print(f"\nAll figures written to {rsc.FIGDIR.resolve()}")
    return out


# Companion notebooks: method comparison (anchor / KAN / PySR / SINDy)
METHOD_STYLE = {
    "anchor": dict(color=rsc.C["black"], label="log-OLS anchor"),
    "KAN":    dict(color=rsc.C["blue"], label="KAN (network alone)"),
    "PySR":   dict(color=rsc.C["vermilion"], label="PySR"),
    "SINDy":  dict(color=rsc.C["green"], label="SINDy"),
}


def fig_method_comparison(rows, methods=("anchor", "KAN", "PySR"),
                          stem="figC1_method_comparison"):
    """Wall-clock (panel a) and SymPy operation count (panel b) per descriptor.

    `rows` is a list of dicts with keys name, wall_<method>, ops_canonical and
    ops_raw_<method>. A method with no raw count is skipped in panel b.
    """
    names = [TEX.get(r["name"], r["name"]) for r in rows]
    x = np.arange(len(rows))
    fig, axes = rsc.subplots(1, 2, width="double", height=5.6)

    ax = axes[0]
    w = 0.8 / len(methods)
    for j, mth in enumerate(methods):
        vals = [r.get(f"wall_{mth}", np.nan) for r in rows]
        ax.bar(x + (j - (len(methods) - 1) / 2) * w, vals, w,
               color=METHOD_STYLE[mth]["color"], label=METHOD_STYLE[mth]["label"])
    ax.set_yscale("log")
    ax.set_xticks(x); ax.set_xticklabels(names)
    ax.set_ylabel("wall-clock / s")
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.01), ncol=len(methods),
              fontsize=5.5, borderaxespad=0.0)
    rsc.panel_label(ax, "a", x=-0.13)

    ax = axes[1]
    raw_methods = [m for m in methods if any(f"ops_raw_{m}" in r for r in rows)]
    groups = ["canonical"] + raw_methods
    w = 0.8 / len(groups)
    for j, g in enumerate(groups):
        key = "ops_canonical" if g == "canonical" else f"ops_raw_{g}"
        vals = [r.get(key, np.nan) for r in rows]
        col = rsc.C["grey"] if g == "canonical" else METHOD_STYLE[g]["color"]
        lab = "canonical form" if g == "canonical" else f"{METHOD_STYLE[g]['label']} (raw)"
        ax.bar(x + (j - (len(groups) - 1) / 2) * w, vals, w, color=col, label=lab)
    ax.set_xticks(x); ax.set_xticklabels(names)
    ax.set_ylabel("SymPy operations")
    ax.yaxis.get_major_locator().set_params(integer=True)
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.01), ncol=len(groups),
              fontsize=5.5, borderaxespad=0.0)
    rsc.panel_label(ax, "b", x=-0.13)

    rsc.finish(fig)
    rsc.check(fig, "double")
    rsc.save(fig, stem)
    return fig


def fig_sindy_threshold(sweeps, thresholds, atom_labels, stem="figC2_sindy_threshold"):
    """Exponent of every library feature against the STLSQ threshold.

    `sweeps` maps descriptor name -> {feature: [coefficient at each threshold]},
    one coefficient per entry of `thresholds`.
    """
    names = list(sweeps)
    fig, axes = rsc.subplots(1, len(names), width="double", height=5.4, sharey=True)
    axes = np.atleast_1d(axes)
    cols = [rsc.C["blue"], rsc.C["vermilion"], rsc.C["green"], rsc.C["purple"]]
    marks = ["o", "s", "^", "v"]
    for k, (ax, name) in enumerate(zip(axes, names)):
        for j, (atom, vals) in enumerate(sweeps[name].items()):
            ax.plot(thresholds, vals, marker=marks[j % 4], color=cols[j % 4],
                    label=atom_labels.get(atom, atom), markersize=2.6)
        ax.axhline(0, color=rsc.C["grey"], lw=0.5)
        ax.set_xscale("log")
        ax.set_xlabel("STLSQ threshold")
        ax.set_title(TEX.get(name, name))
        if k == 0:
            ax.set_ylabel("exponent")
        rsc.panel_label(ax, PANELS[k])
    axes[0].legend(loc="lower center", bbox_to_anchor=(1.0 if len(names) > 1 else 0.5, 1.08),
                   ncol=len(atom_labels), fontsize=5.5, borderaxespad=0.0)
    rsc.finish(fig)
    rsc.check(fig, "double")
    rsc.save(fig, stem)
    return fig
