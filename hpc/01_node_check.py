#!/usr/bin/env python3
"""
01_node_check.py -- record the node and the environment before a long run.

A fixed thread count reproduces bit for bit on one CPU model, but another model may
dispatch different vector kernels. Use the same node type for every run.
"""
import os, platform, subprocess, sys

def sh(cmd):
    try:
        return subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout.strip()
    except Exception:
        return ""

print("=" * 70)
print("NODE")
print("=" * 70)
print(f"  hostname        {platform.node()}")
print(f"  kernel          {platform.platform()}")
# lscpu is not installed on every compute node; /proc/cpuinfo always is.
model = (sh("grep -m1 'model name' /proc/cpuinfo | cut -d: -f2")
         or sh("lscpu 2>/dev/null | grep -i 'model name' | head -1 | cut -d: -f2")
         or "unknown")
print(f"  cpu model       {model.strip()}")
_topo = sh("lscpu 2>/dev/null | grep -E 'Socket|Core|Thread' | head -3")
if _topo:
    for _l in _topo.splitlines():
        print(f"  {_l.strip()}")
else:
    _phys = sh("grep -c '^processor' /proc/cpuinfo")
    print(f"  processors      {_phys or '?'}  (lscpu unavailable)")
print(f"  logical cpus    {os.cpu_count()}")
flags = (sh("grep -m1 '^flags' /proc/cpuinfo")
         or sh("lscpu 2>/dev/null | grep -i '^flags' | head -1"))
for f in ("avx512f", "avx2", "avx", "fma"):
    if f in flags:
        print(f"  vector ISA      {f}  <-- record this; a node without it can give different last digits")
        break
alloc = os.environ.get("SLURM_CPUS_PER_TASK") or os.environ.get("PBS_NCPUS")
print(f"  scheduler alloc {alloc or '(not inside a job)'}")

print()
print("=" * 70)
print("ENVIRONMENT")
print("=" * 70)
print(f"  python          {platform.python_version()}  ({sys.executable})")
for v in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "KAN_THREADS",
          "PYTHONNOUSERSITE", "PYTHONPATH"):
    print(f"  {v:<16}{os.environ.get(v, '(unset)')}")

# Anything on sys.path from outside the environment can shadow a pinned package.
_envroot = os.path.dirname(os.path.dirname(sys.executable))
_foreign = [p for p in sys.path
            if p and not p.startswith(_envroot) and not p.startswith(os.getcwd())]
if _foreign:
    print("  sys.path OUTSIDE the environment  <-- can shadow pinned packages:")
    for _p in _foreign:
        print(f"      {_p}")
else:
    print("  sys.path        clean (nothing outside the environment)")

import importlib.metadata as md
for p in ("torch", "pykan", "sympy", "numpy", "pandas", "scikit-learn", "matplotlib"):
    try: print(f"  {p:<16}{md.version(p)}")
    except Exception: print(f"  {p:<16}NOT INSTALLED  <-- fix before running")

try:
    import numpy as np
    cfg = getattr(np, "__config__", None)
    blas = ""
    if cfg and hasattr(cfg, "show"):
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            cfg.show()
        for line in buf.getvalue().splitlines():
            if any(k in line.lower() for k in ("openblas", "mkl", "blis", "accelerate")):
                blas = line.strip(); break
    print(f"  numpy BLAS      {blas or 'could not determine'}")
except Exception as e:
    print(f"  numpy BLAS      query failed: {e!r}")

try:
    import torch
    print(f"  torch threads   {torch.get_num_threads()} intra / {torch.get_num_interop_threads()} inter")
    print(f"  torch cuda      {torch.cuda.is_available()}  (keep this False: a GPU reintroduces"
          " nondeterminism of its own)")
except Exception as e:
    print(f"  torch           import failed: {e!r}")

print()
print("=" * 70)
print("DATA")
print("=" * 70)
csv = "reactivity_dataset.csv"
if os.path.exists(csv):
    import hashlib
    h = hashlib.sha256(open(csv, "rb").read()).hexdigest()
    print(f"  {csv}  sha256 {h}")
    print(f"  {'MATCHES the archived data set' if h.startswith('f03f5f28') else 'DIFFERENT from the archived data set -- the notebook will stop'}")
else:
    print(f"  {csv} NOT FOUND in {os.getcwd()} -- the notebook would fall back to synthetic data")

print()
print("Record this output beside the run. Same node type + same KAN_THREADS = same numbers.")
