#!/usr/bin/env bash
# 03_run_local.sh -- run the notebook without a scheduler (workstation, or srun).
# Options: KAN_THREADS=<n>, DRY=1 (smoke test, not the paper's numbers), ENVDIR=<path>.
# The interpreter is called by absolute path: a virtualenv built on a node-local Python
# breaks on compute nodes, so keep the environment on shared storage.
set -euo pipefail

ENVDIR="${ENVDIR:-${VENV:-$HOME/kan-env}}"
PY="$ENVDIR/bin/python"
JUPYTER="$ENVDIR/bin/jupyter"

if [ ! -x "$PY" ] || ! "$PY" -c "pass" 2>/dev/null; then
    echo "ERROR: $PY is missing or not runnable on this host ($(hostname))." >&2
    echo >&2
    if [ -f "$ENVDIR/pyvenv.cfg" ]; then
        echo "It is a virtualenv built on:" >&2
        grep -E "^home" "$ENVDIR/pyvenv.cfg" >&2 || true
        echo "If that path is node-local (e.g. under /local/), the interpreter does not exist" >&2
        echo "here. Rebuild the environment on shared storage -- see hpc/GUIDE.md." >&2
    fi
    exit 1
fi
if [ ! -x "$JUPYTER" ]; then
    echo "ERROR: $JUPYTER not found. Install jupyter into $ENVDIR." >&2
    exit 1
fi

# SHELL: IPython's "!" escape goes through $SHELL, and zsh is often absent on compute nodes.
# PYTHONNOUSERSITE: keeps ~/.local from shadowing a pinned package.
export SHELL=/bin/bash
export PYTHONNOUSERSITE=1
unset PYTHONPATH
export KAN_THREADS="${KAN_THREADS:-$(nproc)}"
export OMP_NUM_THREADS="$KAN_THREADS" MKL_NUM_THREADS="$KAN_THREADS"
export OPENBLAS_NUM_THREADS="$KAN_THREADS" NUMEXPR_NUM_THREADS="$KAN_THREADS"
export MPLBACKEND=Agg
export PATH="$ENVDIR/bin:$PATH"       # so the notebook's own shell escapes find the right pip

"$PY" hpc/01_node_check.py
echo "=== running (KAN_THREADS=$KAN_THREADS, DRY=${DRY:-0}) ==="
time "$JUPYTER" nbconvert --to notebook --execute KAN_from_CRDFT.ipynb \
     --output KAN_from_CRDFT_executed.ipynb --ExecutePreprocessor.timeout=-1
echo "done -> KAN_from_CRDFT_executed.ipynb"
