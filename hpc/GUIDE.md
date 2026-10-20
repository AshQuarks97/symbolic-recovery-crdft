# Running on a cluster

The notebooks run headless through `nbconvert`. There is no need to convert them
to `.py`: the executed `.ipynb`, outputs included, is the artifact we archive.

Run everything on one node with the thread count pinned to one. That makes the
wall-clock times of the three methods comparable and removes reduction-order
non-determinism. It does not make the run bit-reproducible: repeating the study
on the same node still moves the unrounded exponents by up to 4e-3, while the
recovered closed forms do not change. Everything below exists to make the node
and the thread count explicit, so a later run can be matched to this one.

## 1. Look around

```bash
sinfo -s 2>/dev/null || qstat -Q 2>/dev/null     # SLURM or PBS?
python3 --version                                 # 3.10 or newer
quota -s 2>/dev/null || df -h "$HOME"             # the environment needs 4-6 GB
sinfo -o "%20P %10c %10m %30f %N"                 # node types per partition
```

Pick a partition whose nodes are the same CPU model. If `AVAIL_FEATURES` prints
`(null)`, the site has not tagged its nodes and `--constraint` is useless; sample
a few nodes instead, then pin one by name:

```bash
srun -p <partition> -N4 --ntasks-per-node=1 --time=00:02:00 bash -c \
    'hostname; grep -m1 "model name" /proc/cpuinfo; grep -m1 -o "avx512f\|avx2" /proc/cpuinfo'
```

The vector instruction set matters as much as the model. A Broadwell node on
`avx2` and a newer one on `avx512f` dispatch different kernels and can differ in
the last digits.

## 2. Copy the files up

```bash
scp -r SI_KAN_CRDFT_repo reactivity_dataset.csv <user>@<cluster>:~/
ssh <user>@<cluster>
cd ~/SI_KAN_CRDFT_repo
sha256sum reactivity_dataset.csv   # f03f5f28e46a6cdf660100bbfd1ee5b1825d3bdb17ddd255231155cd16e752b3
```

Keep everything on shared storage. An environment built under `/local`, `/tmp`
or `/state` exists only on the node that built it.

## 3. Build the environment, on the login node

```bash
bash hpc/00_setup_env.sh          # creates $HOME/kan-env
```

Compute nodes usually have no outbound network, so this cannot wait until the job.

## 4. Smoke test

```bash
DRY=1 ./hpc/03_run_local.sh       # every code path, tiny budgets, about 2 minutes
```

## 5. Record the node

```bash
srun -p <partition> --time=00:05:00 $HOME/kan-env/bin/python hpc/01_node_check.py | tee node_check.txt
```

Keep that file. It records the CPU model, instruction set, thread settings,
package versions, the BLAS numpy links against, and the checksum of the CSV.

## 6. Submit

Edit two lines of `hpc/02_run_kan.slurm` first: `--cpus-per-task` and the
partition (or uncomment `--nodelist`).

```bash
sbatch hpc/02_run_kan.slurm       # SLURM
qsub   hpc/02b_run_kan.pbs        # PBS
squeue -u $USER
tail -f kan-crdft-*.out
```

## 7. Bring the results back

```bash
scp <user>@<cluster>:~/SI_KAN_CRDFT_repo/KAN_from_CRDFT_executed.ipynb .
scp -r <user>@<cluster>:~/SI_KAN_CRDFT_repo/{results,figures} .
```

Take all of `figures/`, including `figures/panels/`, which Figure 1 is rebuilt from.

## 8. The baselines, in this order

PySR builds its comparison table from the executed KAN notebook, and SINDy needs
`results/pysr_results.json`, which PySR writes.

```bash
bash hpc/04_setup_baselines.sh    # login node: both environments, and Julia for PySR
sbatch hpc/05_run_baselines.slurm
```

SINDy should print `PySR (N=131375): 8/8 recovered after pruning`. If it says
`PySR results not found`, the JSON was not beside it.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `Molecules: ... (source: SYNTHETIC)` | the job ran from the wrong folder; `cd` to the repository and resubmit |
| `RuntimeError: ... gives N molecules ... has 131375` | wrong CSV; re-copy and check the SHA-256 |
| `ImportError: figures_rsc.py is v...` | stale copy of the module; take it from this repository |
| `python: command not found` inside the job | the environment is on node-local disk; rebuild it under `$HOME` |
| `pip` fails or hangs in the job | no network on compute nodes; build on the login node |
| `OSError: "/bin/zsh" shell not found` | the job scripts export `SHELL=/bin/bash`; also set `SKIP_PIP=1` |
| `[juliapkg] ...: no such file or directory` | `JULIA_DEPOT_PATH` is on node-local disk; point it at `$HOME/.julia` |
| juliapkg tries to download Julia inside the job | `PYTHON_JULIAPKG_PROJECT` defaulted into the Python environment, which is node-local; set it under `$HOME` in `04` and `05`, and export `PYTHON_JULIAPKG_OFFLINE=yes` |
| `libgomp: Thread creation failed: Resource temporarily unavailable` | the node refuses extra OpenMP threads; request `--cpus-per-task=1` and keep the single-threaded exports |
| one conda environment for both baselines | point `PYSR_ENV` and `SINDY_ENV` at the same directory; `04` installs both requirement files into it |
| job killed with no message | out of memory or past walltime; raise `--mem` or `--time` |
| numbers differ from a previous run | expected in the fourth decimal even on the same node; the closed forms should not change. Compare `node_check.txt` for the node and thread count |
| `UserWarning: Converting a tensor with requires_grad` | harmless, from SymPy inside pykan |
