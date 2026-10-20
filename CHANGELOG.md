# Changelog

## v1.1.0

Everything in the paper now comes from a single machine, and the PySR
post-processing rule was replaced.

### One machine, one thread

The KAN run and the two baselines were previously executed on different nodes of
the cluster, which made the cost column an order-of-magnitude comparison rather
than a calibrated one. All three now run on the same node with the thread count
pinned to one. Single-threaded execution also removes reduction-order
non-determinism, so each method is deterministic given its seeds.

### PySR: a scale-relative pruning rule

The previous rule zeroed numeric literals below a fixed absolute threshold of
1e-5. That test depends on the units of each descriptor, and it ran before the
surviving constants were snapped to rationals, so two nearly cancelling
constants could be rationalized into a fresh residue the rule never saw. On this
node that happened to `omega` and `omega_minus`, which came out as
`5836452*chi**2/(11672904*eta - 1)` and a quartic in `A_minus`, leaving six of
eight canonical.

A term is now dropped when its root-mean-square contribution over the 131,375
molecules falls below 1e-6 of that of the sum containing it, and the test is
repeated after snapping. The criterion is dimensionless and applied identically
to all 24 fits. The largest relative contribution it discards anywhere is
1.05e-8. All eight forms are canonical again, in each of three seeds and in the
`square`-for-all ablation. The notebook also reports what the old absolute rule
returns, so the difference stays visible.

### Reproducibility, measured rather than assumed

Repeating the whole study on the same node, at the same thread count and library
versions, reproduces every closed form but not every digit: the unrounded slopes
move by up to 3.9e-3. The README and the paper now say so. Both KAN fitting
functions reseed the global generators before each fit.

### Figures

`figures_rsc.py` is v13. Axes now carry between two and three labelled major
ticks on every panel. A log axis spanning less than a decade previously received
no major tick at all, which left panels bare, and shared axes hid the tick
labels of every panel but one.

`figC1_pysr_comparison` is renamed `figC4_pysr_comparison`; it collided with
`figC1_trainsize`.

### Cluster scripts

`04_setup_baselines.sh` and `05_run_baselines.slurm` set
`PYTHON_JULIAPKG_PROJECT` under `$HOME`. juliapkg otherwise places its project
inside the Python environment, and a conda installation on node-local disk is
invisible to the compute node, so the job dies trying to download Julia.
`05_run_baselines.slurm` also exports `PYTHON_JULIAPKG_OFFLINE=yes` and requests
one CPU, and both scripts document that `PYSR_ENV` and `SINDY_ENV` may name the
same directory.

## v1.0.0

First release.
