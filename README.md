# Symbolic recovery of CRDFT reactivity descriptors

Code and results for the paper *Symbolic recovery of CRDFT reactivity descriptors: a controlled benchmark of Kolmogorov-Arnold networks, sparse identification and genetic programming*, submitted to *Digital Discovery*.

The eight global CRDFT descriptors are exact algebraic functions of the vertical
ionization potential and electron affinity, so the target of the regression is
known to machine precision. That makes them a benchmark on which three symbolic
regression methods can be compared without ambiguity about what counts as the
right answer. The three notebooks here run that comparison on 131,375 molecules.

## Authors

Ashley Acosta-García (bryan.acosta@cinvestav.mx) and Alberto Vela
(avela@cinvestav.mx), Departamento de Química, Cinvestav-Zacatenco, Mexico City.

## Contents

| File | What it does |
|---|---|
| `KAN_from_CRDFT.ipynb` | KAN study: direct fits, the logarithmic route, symbolic export, and the seed, spline, noise and training-size sweeps |
| `PySR_from_CRDFT.ipynb` | PySR baseline: raw and pruned expressions, seed study, operator ablation |
| `SINDy_from_CRDFT.ipynb` | SINDy (STLSQ) baseline: affine and log-space fits, threshold sweep, four-method comparison |
| `rsc_style.py`, `figures_rsc.py` | journal-format figures |
| `regenerate_figures.py` | rebuilds every figure from `results/`, without refitting |
| `extract_kan_results.py` | pulls the KAN numbers out of the executed notebook into JSON |
| `results/` | the numbers behind the tables, as JSON, plus the figure inputs |
| `figures/` | vector PDFs of every figure in the paper (`fig01`–`fig07`) and the SI (`figC1`–`figC4`) |
| `hpc/` | environment setup and job scripts for a cluster |

Run the KAN notebook first: PySR reads its results, and SINDy reads both.

## Data

`reactivity_dataset.csv` is **not** in this repository. It is deposited at
<https://doi.org/10.5281/zenodo.23402219> and must sit in the working directory
before anything runs.

It was built from QM9 (133,888 molecules of H, C, N, O and F). Structures were
generated from SMILES with RDKit, pre-optimized with MMFF94, then reoptimized
with AIMNet2-NSE. Single-point energies of the neutral, cationic and anionic
states at the neutral geometry give the vertical IP and EA, from which the eight
descriptors follow by their finite-difference definitions. Molecules with
non-finite descriptors or non-positive hardness were dropped, leaving 131,375.

Every notebook prints the SHA-256 of the file it loads and stops if the molecule
count is not 131,375, so two runs cannot be compared across different versions
of the data by accident.

```
sha256 = f03f5f28e46a6cdf660100bbfd1ee5b1825d3bdb17ddd255231155cd16e752b3
```

## Running

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
jupyter lab KAN_from_CRDFT.ipynb
```

`requirements-pysr.txt` and `requirements-sindy.txt` cover the two baselines.
`rsc_style.py` and `figures_rsc.py` are part of this repository, not PyPI
packages, and must sit next to the notebooks. A full KAN run takes 45–60 minutes
on CPU for the headline fits alone, and about two and a half hours including the
seed, spline, noise and training-size sweeps; `DRY=1` exercises every code path in
about two minutes on tiny budgets.

On a cluster, use `hpc/` instead. See `hpc/GUIDE.md`.

## Reproducibility

Every run archived here was made on one node of a shared cluster (two Intel Xeon
E5-2683 v4, AVX2) with the thread count pinned to one, so the three methods
share a machine and their wall-clock times compare directly. Cell 3.1 sets the
count through `KAN_THREADS` before importing PyTorch.

Single-threaded execution removes reduction-order non-determinism, but it does
not make the pipeline bit-reproducible. Repeating the whole study on the same
node, at the same thread count, library versions and input checksum, returns all
eight closed forms again and the same rounded exponents, while the unrounded
slopes move by up to 3.9e-3, largest for omega-plus and below 6e-5 for every
other descriptor. Moving to a node with a different vector instruction set moves
them by about as much. Higher precision does not help: what varies is where the
optimizer stops along a flat direction of the objective, not the accuracy of any
one step. Both fitting functions reseed the global generators before each fit,
so a fit does not depend on how many draws the fits before it made.

What is stable across every run we have made is what the conclusions rest on:
the recovered closed forms, the least-squares anchor, and every R². The drift
stays three orders of magnitude inside the rounding tolerance that recovery
depends on.

PySR's post-processing uses a scale-relative rule: an additive term is dropped
when its root-mean-square contribution over all molecules falls below 1e-6 of
that of the sum containing it, and the test is repeated after the surviving
constants are snapped to rationals. A fixed absolute threshold on numeric
literals is unit-dependent and, applied before snapping, lets two nearly
cancelling constants be rationalized into a residue it can no longer see; the
notebook reports what that simpler rule returns, for comparison.

## Figures

`regenerate_figures.py` rebuilds all the figures from `results/` in seconds,
without refitting. Figure 1 is recomposited from the cached panels in
`figures/panels/`, so keep that folder. Each figure is written as a vector PDF
and a 600 dpi TIFF; only the PDFs are committed.

## Citation

Please cite the paper and the archived release:

> A. Acosta-García and A. Vela, *Symbolic recovery of CRDFT reactivity descriptors: a controlled benchmark of Kolmogorov--Arnold networks, sparse identification and genetic programming*, submitted.

Code DOI: []

Cite the concept DOI to refer to the project as a whole, and the version DOI of a
release to refer to the exact code that produced a given result.

## License

MIT, see `LICENSE`.
