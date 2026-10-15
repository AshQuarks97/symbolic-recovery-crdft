"""Parse the executed KAN notebook and write results/kan_results.json, which the
comparison notebooks read. Every value comes from the notebook's printed output,
so the comparison is traceable to that run.

    python extract_kan_results.py [path/to/notebook.ipynb]
"""
import json, re, sys, os

NB = sys.argv[1] if len(sys.argv) > 1 else "KAN_from_CRDFT_executed.ipynb"
cells = json.load(open(NB, encoding="utf-8"))["cells"]

def outputs_containing(marker):
    for c in cells:
        if c["cell_type"] != "code":
            continue
        txt = "".join("".join(o.get("text", "")) for o in c.get("outputs", []))
        txt = re.sub(r"[^\n]*\r", "", txt)
        if marker in txt:
            return txt
    raise RuntimeError(f"no output containing {marker!r} -- is the notebook executed?")

res = {"source_notebook": os.path.basename(NB), "descriptors": {}}
D = res["descriptors"]
KEY = {"mu": "mu", "chi": "chi", "eta": "eta", "S": "S", "Nmax": "Nmax",
       "omega": "omega", "wplus": "omega_plus", "wminus": "omega_minus"}

# dataset size
m = re.search(r"Molecules: (\d+)", outputs_containing("Molecules:"))
res["n_molecules"] = int(m.group(1))

# affine fits (Cell 4.1): anchor form, spline R2, wall
t = outputs_containing("anchor (linear OLS)")
for name, r2s, wall in re.findall(r"^(mu|chi|eta)\s+ref=.*?KAN spline R2=([\d.]+) \| wall=([\d.]+)s", t, re.M):
    D.setdefault(name, {}).update(r2_spline=float(r2s), wall_s=float(wall))

# log fits (Cells 4.2, 4.4): spline R2 and wall
for marker in ("### S ", "### Nmax"):
    t = outputs_containing(marker)
    for nm, wall, r2s in re.findall(r"### (\w+)\s+\(ref.*?\[wall=([\d.]+)s\].*?KAN spline \(std\., subsample\) = ([\d.]+)", t, re.S):
        k = {"omega_plus": "omega_plus", "omega_minus": "omega_minus"}.get(nm, nm)
        D.setdefault(k, {}).update(r2_spline=float(r2s), wall_s=float(wall))

# network-only closed forms (Cell 4.4c)
t = outputs_containing("The network alone, after rounding")
for line in t.splitlines():
    m = re.match(r"^(mu|chi|eta|S|Nmax|omega|wplus|wminus)\s+(.+?)\s{2,}(\S.*?)\s{2,}(yes|NO)\s+([\d.]+)\s+([\d.]+)\s*$", line)
    if not m:
        continue
    k = KEY[m.group(1)]
    raw = m.group(2).strip()
    nums = [float(x) for x in re.findall(r"[-+]?\d+\.\d+", raw)]
    entry = D.setdefault(k, {})
    entry.update(network_raw=raw, network_closed_form=m.group(3).strip(),
                 network_match=(m.group(4) == "yes"),
                 r2_network_unrounded=float(m.group(5)), r2_network_rounded=float(m.group(6)))
    if k in ("mu", "chi", "eta"):
        entry["network_coefficients"] = {"IP": nums[0], "EA": nums[1], "const": nums[2]}
    else:
        entry["network_exponents"] = nums[:-1]
        entry["network_prefactor"] = nums[-1]
m = re.search(r"recovers (\d)/8", t)
res["network_only_recovered"] = int(m.group(1))

missing = [k for k in KEY.values() if not {"wall_s", "network_closed_form"} <= set(D.get(k, {}))]
if missing:
    raise RuntimeError(f"incomplete extraction for {missing}")
os.makedirs("results", exist_ok=True)
json.dump(res, open("results/kan_results.json", "w"), indent=2)
print(f"wrote results/kan_results.json  (N={res['n_molecules']}, network-only {res['network_only_recovered']}/8)")
