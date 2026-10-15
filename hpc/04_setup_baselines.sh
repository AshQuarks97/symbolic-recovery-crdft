#!/usr/bin/env bash
# hpc/04_setup_baselines.sh -- build the PySR and SINDy environments. Login node only.
# PySR does not ship Julia: juliapkg downloads it on first import, and compute nodes have
# no outbound network, so that has to happen here.
# Override: PYSR_ENV, SINDY_ENV, JULIA_DEPOT_PATH, MODE=conda|venv, PYVER.
set -euo pipefail

MODE="${MODE:-conda}"
PYVER="${PYVER:-3.11}"
PYSR_ENV="${PYSR_ENV:-$HOME/pysr-env}"
SINDY_ENV="${SINDY_ENV:-$HOME/sindy-env}"
export JULIA_DEPOT_PATH="${JULIA_DEPOT_PATH:-$HOME/.julia}"

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO"

# An environment or a Julia depot under /local, /tmp or /state is invisible to the compute node.
for d in "$PYSR_ENV" "$SINDY_ENV" "$JULIA_DEPOT_PATH"; do
    case "$d" in
        /local/*|/tmp/*|/scratch/local/*|/state/*)
            echo "WARNING: $d looks node-local; compute nodes may not see it." >&2 ;;
    esac
done

# Keep ~/.local and any inherited PYTHONPATH off sys.path.
export PYTHONNOUSERSITE=1
unset PYTHONPATH || true
export CONDA_PKGS_DIRS="${CONDA_PKGS_DIRS:-$HOME/.conda/pkgs}"   # a read-only shared cache fails

build () {                 # build <envdir> <requirements file>
    local env="$1" req="$2"
    echo
    echo "=== building $env from $req (mode=$MODE) ==="
    if [ -x "$env/bin/python" ]; then
        echo "exists; reusing it (delete the directory to rebuild)"
    elif [ "$MODE" = "conda" ]; then
        command -v conda >/dev/null || { echo "conda not found; re-run with MODE=venv" >&2; exit 1; }
        conda create -y -p "$env" "python=$PYVER"
    else
        "python$PYVER" -m venv "$env" 2>/dev/null || python3 -m venv "$env"
    fi
    "$env/bin/python" -m pip install -q --upgrade pip
    "$env/bin/python" -m pip install -q -r "$req"
}

build "$PYSR_ENV"  requirements-pysr.txt
build "$SINDY_ENV" requirements-sindy.txt

for env in "$PYSR_ENV" "$SINDY_ENV"; do
    "$env/bin/python" -m pip install -q jupyter nbconvert ipykernel
done

echo
echo "=== warming up Julia for PySR (this is the step that needs the network) ==="
echo "    JULIA_DEPOT_PATH=$JULIA_DEPOT_PATH"
"$PYSR_ENV/bin/python" - <<'PY'
import os, time
t0 = time.time()
from pysr import PySRRegressor            # triggers the juliapkg install/resolve
from juliacall import Main as jl
print("  julia                ", jl.seval("string(VERSION)"))
print("  SymbolicRegression.jl", jl.seval("using SymbolicRegression; string(pkgversion(SymbolicRegression))"))
print(f"  warm-up took {time.time()-t0:.0f} s")
PY

echo
echo "=== versions, and where each module is imported from ==="
"$PYSR_ENV/bin/python" - <<'PY'
import importlib.metadata as md, importlib, sys
for m in ("pysr","juliacall","sympy","numpy","pandas","matplotlib"):
    mod = importlib.import_module(m)
    print(f"  {m:<12} {md.version(m):<10} {getattr(mod,'__file__','?')}")
bad=[p for p in sys.path if ".local" in p]
print("  FOREIGN sys.path entries:", bad if bad else "none")
PY
"$SINDY_ENV/bin/python" - <<'PY'
import importlib.metadata as md, importlib, sys
for m in ("pysindy","sklearn","sympy","numpy","pandas","matplotlib"):
    mod = importlib.import_module(m)
    name = {"sklearn":"scikit-learn"}.get(m,m)
    print(f"  {m:<12} {md.version(name):<10} {getattr(mod,'__file__','?')}")
bad=[p for p in sys.path if ".local" in p]
print("  FOREIGN sys.path entries:", bad if bad else "none")
PY

echo
echo "Done. Now submit:  sbatch hpc/05_run_baselines.slurm"
echo "Keep JULIA_DEPOT_PATH=$JULIA_DEPOT_PATH -- 05_run_baselines.slurm exports the same value."
