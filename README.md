# Symbolic recovery of CRDFT reactivity descriptors

Code and results for the paper *Symbolic recovery of CRDFT reactivity descriptors: a controlled benchmark of Kolmogorov--Arnold networks, sparse identification and genetic programming*, submitted to *Digital Discovery*.

The eight global CDFT descriptors are exact algebraic functions of the vertical
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
| `*_executed.ipynb` | the same notebooks as run for the paper, outputs included |
| `rsc_style.py`, `figures_rsc.py` | journal-format figures |
| `regenerate_figures.py` | rebuilds every figure from `results/`, without refitting |
| `extract_kan_results.py` | pulls the KAN numbers out of the executed notebook into JSON |
| `results/` | the numbers behind the tables, as JSON, plus the figure inputs |
| `figures/` | vector PDFs of every figure in the paper and the SI |
| `hpc/` | environment setup and job scripts for a cluster |

Run the KAN notebook first: PySR reads its results, and SINDy reads both.

## Data

`reactivity_dataset.csv` is **not** in this repository. It is deposited at
[DOI] and must sit in the working directory before anything runs.

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
on CPU; `DRY=1` exercises every code path in about two minutes on tiny budgets.

On a cluster, use `hpc/` instead. See `hpc/GUIDE.md`.

## Reproducibility

The fits are full-batch and multithreaded, so the order in which the reductions
are summed depends on the thread count, and floating-point addition is not
associative. Changing only the thread count moves the network's unrounded
exponents in the fourth decimal. Cell 3.1 pins it through `KAN_THREADS` before
importing PyTorch; what matters is that the value is fixed, not that it is 1.
With it fixed, a given machine reproduces itself bit for bit. Higher precision
does not help, since what varies is where the optimizer stops along a flat
direction of the objective, not the accuracy of each step.

The runs archived here used one node for the KAN (8 threads) and another of the
same cluster for the baselines (single-threaded). The recovered closed forms,
the least-squares anchor and every R² are identical across all runs we made.

## Figures

`regenerate_figures.py` rebuilds all the figures from `results/` in seconds,
without refitting. Figure 1 is recomposited from the cached panels in
`figures/panels/`, so keep that folder. Each figure is written as a vector PDF
and a 600 dpi TIFF; only the PDFs are committed.

## Citation

Please cite the paper and the archived release:

> A. Acosta-García and A. Vela, *Symbolic recovery of CRDFT reactivity descriptors: a controlled benchmark of Kolmogorov--Arnold networks, sparse identification and genetic programming*, submitted.

Code DOI: []

## License

MIT, see `LICENSE`.
