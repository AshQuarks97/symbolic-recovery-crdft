#!/usr/bin/env bash
# 00_setup_env.sh -- build the environment. Run this on a login node (it needs network).
# MODE=conda (the default) or MODE=venv. Conda is preferred: a virtualenv only links to the
# interpreter that built it, so one built on node-local storage is invisible to compute nodes.
set -euo pipefail

# Install with the run scripts' isolation, or pip resolves against ~/.local and skips
# installing dependencies into the environment.
export PYTHONNOUSERSITE=1
unset PYTHONPATH

MODE="${MODE:-conda}"
ENVDIR="${ENVDIR:-$HOME/kan-env}"
PYVER="${PYVER:-3.11}"

echo "== target: $ENVDIR  (mode=$MODE, python=$PYVER) =="
case "$ENVDIR" in
    /local/*|/tmp/*|/scratch/*)
        echo "WARNING: $ENVDIR looks node-local. Compute nodes may not see it." >&2 ;;
esac

if [ "$MODE" = "conda" ]; then
    command -v conda >/dev/null || { echo "conda not found. Use MODE=venv, or load conda first." >&2; exit 1; }
    # A conda install on node-local storage often has an unwritable package cache.
    export CONDA_PKGS_DIRS="${CONDA_PKGS_DIRS:-$HOME/.conda/pkgs}"
    mkdir -p "$CONDA_PKGS_DIRS"
    echo "   package cache: $CONDA_PKGS_DIRS"
    conda create -y -p "$ENVDIR" "python=$PYVER"
    PIP="$ENVDIR/bin/pip"
else
    PYTHON="${PYTHON:-python3}"
    "$PYTHON" -m venv "$ENVDIR"
    PIP="$ENVDIR/bin/pip"
fi

"$PIP" install -q --upgrade pip wheel
echo "== installing pinned requirements =="
"$PIP" install -q -r requirements.txt
"$PIP" install -q jupyter nbconvert nbclient ipykernel

echo "== verifying the environment is self-contained =="
"$ENVDIR/bin/python" - <<'PY'
import importlib, sys
missing = [m for m in ("numpy", "pandas", "torch", "kan", "sympy", "sklearn", "matplotlib",
                       "jinja2", "nbconvert", "nbclient", "jupyter_client", "IPython")
           if not importlib.util.find_spec(m)]
if missing:
    sys.exit("MISSING from the environment: " + ", ".join(missing))
print("  all required modules import from inside the environment")
PY
# The two baselines, only if you intend to run them:
#   "$PIP" install -q -r requirements-pysr.txt     # also downloads Julia on first import
#   "$PIP" install -q -r requirements-sindy.txt

echo "== versions =="
"$ENVDIR/bin/python" - <<'PY'
import importlib.metadata as md, sys
print(f"  python         {sys.version.split()[0]}  ({sys.executable})")
for p in ("torch","pykan","sympy","numpy","pandas","scikit-learn","matplotlib","nbconvert"):
    try: print(f"  {p:<14} {md.version(p)}")
    except Exception: print(f"  {p:<14} NOT INSTALLED")
PY

echo
echo "Done. The scripts find it automatically if it is at \$HOME/kan-env;"
echo "otherwise pass ENVDIR=$ENVDIR to them."
