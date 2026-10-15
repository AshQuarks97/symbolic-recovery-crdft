#!/usr/bin/env bash
#SBATCH --job-name=kan-crdft
#SBATCH --output=kan-crdft-%j.out
#SBATCH --error=kan-crdft-%j.err
#SBATCH --time=04:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=16G
#SBATCH --partition=dell256       # <-- SET THIS. The default partition is rarely the right one.
# #SBATCH --nodelist=node48       # <-- strongest option: always the same physical node
# #SBATCH --constraint=<feature>  # only if your site defines node features
#
# Runs KAN_from_CRDFT.ipynb headless and writes the executed notebook, outputs included.
# For the numbers to repeat, fix KAN_THREADS (set from --cpus-per-task) and the node type.
set -euo pipefail

ENVDIR="${ENVDIR:-${VENV:-$HOME/kan-env}}"
export PATH="$ENVDIR/bin:$PATH"

# The thread count must be fixed and exported before python starts.
# SHELL: IPython's "!" escape goes through $SHELL, and zsh is often absent on compute nodes.
# PYTHONNOUSERSITE: keeps ~/.local from shadowing a pinned package.
export SHELL=/bin/bash
export PYTHONNOUSERSITE=1
unset PYTHONPATH
export KAN_THREADS="${SLURM_CPUS_PER_TASK:-1}"
export OMP_NUM_THREADS="$KAN_THREADS"
export MKL_NUM_THREADS="$KAN_THREADS"
export OPENBLAS_NUM_THREADS="$KAN_THREADS"
export NUMEXPR_NUM_THREADS="$KAN_THREADS"
export MPLBACKEND=Agg                 # no display on a compute node

cd "${SLURM_SUBMIT_DIR:-$PWD}"

echo "=== node check ==="
"$ENVDIR/bin/python" hpc/01_node_check.py

echo
echo "=== running (KAN_THREADS=$KAN_THREADS) ==="
START=$(date +%s)
"$ENVDIR/bin/jupyter" nbconvert \
    --to notebook --execute KAN_from_CRDFT.ipynb \
    --output "KAN_from_CRDFT_executed.ipynb" \
    --ExecutePreprocessor.timeout=-1 \
    --ExecutePreprocessor.kernel_name=python3
echo "=== finished in $(( $(date +%s) - START )) s ==="

echo
echo "Artifacts to keep:"
ls -la KAN_from_CRDFT_executed.ipynb results/ figures/ 2>/dev/null || true
echo
echo "Download KAN_from_CRDFT_executed.ipynb, the whole results/ folder and the whole"
echo "figures/ folder (including figures/panels/, which Figure 1 is recomposited from)."
