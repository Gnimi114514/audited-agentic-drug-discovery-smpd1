"""MD-ensemble docking: dock top hits + best analogs into 5 MD snapshots of apo ASM.

Snapshots (md/snapshot_{1..5}ns.pdb) come from the frozen-pocket 5 ns MD. The catalytic
pocket was frozen at crystal positions, so the 5I85-anchored docking box applies to all
snapshots. Output: results/md_ensemble_docking.csv (per-snapshot Vina scores, mean±SD)
compared against the static 5I85 scores.
"""
import os, subprocess, csv, json, time, re
from concurrent.futures import ThreadPoolExecutor, as_completed

OB = r'C:/ProgramData/anaconda3/envs/ob/Library/bin/obabel.exe'
VINA = 'bin/vina.exe'
MD_DIR = 'md'
OUT = 'docking/md_snap'
os.makedirs(OUT, exist_ok=True)
CENTER = (-13.710, -34.100, -28.720)
SIZE = 24

LIGANDS = {  # name -> existing pdbqt path (static-campaign prepped)
    'CHEMBL7385': 'docking/pdbqt/CHEMBL7385.pdbqt',
    'CHEMBL24974': 'docking/pdbqt/CHEMBL24974.pdbqt',
    'CHEMBL48767': 'docking/pdbqt/CHEMBL48767.pdbqt',
    'CHEMBL6729': 'docking/pdbqt/CHEMBL6729.pdbqt',
    'EXP_CHEMBL7385_CF3': 'docking/pdbqt_exp/EXP_CHEMBL7385_C(F)(F)F_C19.pdbqt',
    'EXP_CHEMBL24974_CF3': 'docking/pdbqt_exp/EXP_CHEMBL24974_C(F)(F)F_C27.pdbqt',
}
static_scores = {}
for r in csv.DictReader(open('results/hits_ranked.csv', encoding='utf-8')):
    if r['name'] in LIGANDS:
        static_scores[r['name']] = float(r['vina_best'])
exp = {r['analog_name']: r['analog_vina'] for r in json.load(open('results/expansion_results.json'))}
static_scores['EXP_CHEMBL7385_CF3'] = exp.get('EXP_CHEMBL7385_C(F)(F)F_C19')
static_scores['EXP_CHEMBL24974_CF3'] = exp.get('EXP_CHEMBL24974_C(F)(F)F_C27')

# --- prep snapshot receptors (pre-aligned to crystal frame in WSL: md/snapshot_{ns}ns_al.pdb) ---
def prep_receptor(ns):
    src = f'{MD_DIR}/snapshot_{ns}ns_al.pdb'
    pdbqt = f'{OUT}/rec_{ns}ns.pdbqt'
    r = subprocess.run([OB, src, '-O', pdbqt, '-h', '-p', '7.4'], capture_output=True, text=True)
    keep = [l for l in open(pdbqt) if l.startswith(('ATOM', 'HETATM', 'TER', 'END'))]
    open(pdbqt, 'w').writelines(keep)
    return pdbqt, len(keep)

receptors = {}
for ns in (1, 2, 3, 4, 5):
    pdbqt, nlines = prep_receptor(ns)
    receptors[ns] = pdbqt
    print(f'snapshot {ns}ns receptor: {nlines} lines', flush=True)

def run(lig_name, lig_path, ns):
    tag = f'{lig_name}_{ns}ns'
    outp = f'{OUT}/{tag}.out.pdbqt'
    cfg = (f'receptor = {receptors[ns]}\nligand = {lig_path}\n'
           f'center_x = {CENTER[0]}\ncenter_y = {CENTER[1]}\ncenter_z = {CENTER[2]}\n'
           f'size_x = {SIZE}\nsize_y = {SIZE}\nsize_z = {SIZE}\n'
           f'exhaustiveness = 8\nseed = 42\nnum_modes = 5\ncpu = 1\nout = {outp}\n')
    cfgf = f'{OUT}/{tag}.cfg'
    open(cfgf, 'w').write(cfg)
    r = subprocess.run([VINA, '--config', cfgf], capture_output=True, text=True, timeout=900)
    if r.returncode != 0 or not os.path.exists(outp):
        return lig_name, ns, None
    for l in open(outp):
        if 'VINA RESULT' in l:
            return lig_name, ns, float(l.split()[3])
    return lig_name, ns, None

jobs = [(name, path, ns) for name, path in LIGANDS.items() for ns in (1, 2, 3, 4, 5)]
print('jobs:', len(jobs), flush=True)
t0 = time.time()
scores = {}
with ThreadPoolExecutor(max_workers=20) as ex:
    futs = [ex.submit(run, *j) for j in jobs]
    for f in as_completed(futs):
        name, ns, sc = f.result()
        scores[(name, ns)] = sc
print('docked in %.0fs' % (time.time() - t0), flush=True)

rows = []
import statistics
for name in LIGANDS:
    per_ns = [scores.get((name, ns)) for ns in (1, 2, 3, 4, 5)]
    ok = [s for s in per_ns if s is not None]
    rows.append({'ligand': name,
                 'static_5I85': static_scores.get(name),
                 'md_1ns': per_ns[0], 'md_2ns': per_ns[1], 'md_3ns': per_ns[2],
                 'md_4ns': per_ns[3], 'md_5ns': per_ns[4],
                 'mean': round(statistics.mean(ok), 2) if ok else None,
                 'sd': round(statistics.stdev(ok), 2) if len(ok) > 1 else None})
with open('results/md_ensemble_docking.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader(); w.writerows(rows)
for r in rows:
    print(r)
print('saved results/md_ensemble_docking.csv')
