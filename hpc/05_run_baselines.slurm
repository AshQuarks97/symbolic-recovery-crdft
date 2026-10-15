#!/usr/bin/env bash
#SBATCH --job-name=baselines-crdft
#SBATCH --output=baselines-crdft-%j.out
#SBATCH --error=baselines-crdft-%j.err
#SBATCH --time=02:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --partition=dell256       # <-- the SAME partition as the KAN run, so the
# #SBATCH --nodelist=node48       #     cost column compares like with like
#
# Runs both baselines in one allocation, in the order PySR then SINDy: PySR reads the
# executed KAN notebook, and SINDy reads results/pysr_results.json, which PySR writes.
set -euo pipefail

PYSR_ENV="${PYSR_ENV:-$HOME/pysr-env}"
SINDY_ENV="${SINDY_ENV:-$HOME/sindy-env}"
export JULIA_DEPOT_PATH="${JULIA_DEPOT_PATH:-$HOME/.julia}"   # populated by 04_setup_baselines.sh

export SHELL=/bin/bash          # IPython's `!` escape; /bin/zsh often absent on compute nodes
export PYTHONNOUSERSITE=1       # ignore ~/.local, which can shadow a pinned package
unset PYTHONPATH || true
export MPLBACKEND=Agg           # no display
export SKIP_PIP=1               # the environments are built; never pip from inside a job

# Single-threaded on purpose: PySR for determinism, and to keep the BLAS reduction order constant.
export JULIA_NUM_THREADS=1
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1

cd "${SLURM_SUBMIT_DIR:-$PWD}"

[ -f reactivity_dataset.csv ] || { echo "ERROR: reactivity_dataset.csv not in $PWD" >&2; exit 1; }
if ! ls KAN_from_CRDFT_executed.ipynb >/dev/null 2>&1; then
    echo "ERROR: KAN_from_CRDFT_executed.ipynb not found. Run hpc/02_run_kan.slurm first:" >&2
    echo "       PySR builds its head-to-head table from the executed KAN notebook." >&2
    exit 1
fi

run_nb () {                     # run_nb <envdir> <notebook> <output>
    local env="$1" nb="$2" out="$3"
    echo
    echo "=== $nb ==="
    local start; start=$(date +%s)
    "$env/bin/jupyter" nbconvert \
        --to notebook --execute "$nb" \
        --output "$out" \
        --ExecutePreprocessor.timeout=-1 \
        --ExecutePreprocessor.kernel_name=python3
    echo "=== $out in $(( $(date +%s) - start )) s ==="
}

run_nb "$PYSR_ENV"  PySR_from_CRDFT.ipynb  PySR_from_CRDFT_executed.ipynb
run_nb "$SINDY_ENV" SINDy_from_CRDFT.ipynb SINDy_from_CRDFT_executed.ipynb

echo
echo "Artifacts to keep:"
ls -la PySR_from_CRDFT_executed.ipynb SINDy_from_CRDFT_executed.ipynb results/ figures/ 2>/dev/null || true
echo
echo "Check in the SINDy output that it did NOT print 'PySR results not found'."
