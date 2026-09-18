"""Big item 1b: cross-crystal PC validation + top-20 ensemble docking into 5I81 & 5JG8."""
import math, os, subprocess, csv, json, time
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed

VINA = 'bin/vina.exe'
OUT = 'docking/ensemble'
os.makedirs(OUT, exist_ok=True)

def read_zn(path):
    z = []
    for l in open(path):
        if l.startswith(('ATOM', 'HETATM')) and l[17:20].strip() == 'ZN':
            z.append([float(l[30:38]), float(l[38:46]), float(l[46:54])])
    return np.array(z)

ref_zn = read_zn('structures/5i85.pdb')
PC_CENTER = np.array([-13.710, -34.100, -28.720])

from scipy.optimize import linear_sum_assignment
RECEPTORS = {}
for pid, path in [('5I81', 'structures/5i81_rigid.pdbqt'), ('5JG8', 'structures/5jg8_rigid.pdbqt')]:
    zn = read_zn(path)
    D = np.linalg.norm(zn[:, None, :] - ref_zn[None, :, :], axis=2)
    ri, ci = linear_sum_assignment(D)
    deltas = zn[ri] - ref_zn[ci]
    delta = deltas.mean(axis=0)   # matched-pair mean displacement (robust to Zn file ordering)
    zn_rmsd = float(np.sqrt((deltas ** 2).sum(axis=1).mean()))
    center = PC_CENTER + delta
    RECEPTORS[pid] = {'path': path, 'center': center, 'delta': delta}
    print(pid, 'Zn matched-RMSD:', round(zn_rmsd, 2), 'box center:', [round(c, 2) for c in center])

def run(receptor, ligand, tag, center, exhaustiveness=8):
    outp = f'{OUT}/{tag}.out.pdbqt'
    cfg = (f'receptor = {receptor}\nligand = {ligand}\n'
           f'center_x = {center[0]:.3f}\ncenter_y = {center[1]:.3f}\ncenter_z = {center[2]:.3f}\n'
           f'size_x = 24\nsize_y = 24\nsize_z = 24\n'
           f'exhaustiveness = {exhaustiveness}\nseed = 42\nnum_modes = 5\ncpu = 1\nout = {outp}\n')
    cfgf = f'{OUT}/{tag}.cfg'
    open(cfgf, 'w').write(cfg)
    r = subprocess.run([VINA, '--config', cfgf], capture_output=True, text=True, timeout=900)
    if r.returncode != 0 or not os.path.exists(outp):
        return tag, None, None
    score, atoms = None, []
    mi = -1
    for l in open(outp):
        if l.startswith('MODEL'):
            mi = int(l.split()[1])
        if mi == 1 and l.startswith(('ATOM', 'HETATM')):
            el = AD2EL.get(l.strip().split()[-1], '?')
            atoms.append((el, float(l[30:38]), float(l[38:46]), float(l[46:54])))
        if 'VINA RESULT' in l and score is None:
            score = float(l.split()[3])
    return tag, score, atoms

# --- 1) cross-crystal redocking of PC ---
jobs = []
for pid, rec in RECEPTORS.items():
    jobs.append((rec['path'], 'structures/PC_ref.pdbqt', f'PC_{pid}', rec['center'], 32))
AD2EL = {'OA':'O','O':'O','NA':'N','N':'N','A':'C','C':'C','P':'P','Zn':'Zn'}
def rmsd_sym(A, B):
    from scipy.optimize import linear_sum_assignment
    tot, n = 0.0, 0
    for el in sorted({a[0] for a in A}):
        X = [a for a in A if a[0] == el]; Y = [b for b in B if b[0] == el]
        if len(X) != len(Y): return None
        D = np.array([[math.dist(a[1:], b[1:])**2 for b in Y] for a in X])
        ri, ci = linear_sum_assignment(D)
        tot += D[ri, ci].sum(); n += len(X)
    return math.sqrt(tot/n)

cryst_pc = [(AD2EL.get(l.strip().split()[-1],'?'), float(l[30:38]), float(l[38:46]), float(l[46:54]))
            for l in open('structures/5i85_PC.pdb') if l.startswith('HETATM')]
for pid, rec in RECEPTORS.items():
    tag, score, atoms = run(rec['path'], 'structures/PC_ref.pdbqt', f'PC_{pid}', rec['center'], 32)
    if atoms:
        shift = rec['delta']
        ref_pos = [(e, x + shift[0], y + shift[1], z + shift[2]) for e, x, y, z in cryst_pc]
        r = rmsd_sym(ref_pos, atoms)
        print(f'cross-redock {pid}: vina={score}  RMSD={r and round(r,2)} A')

# --- 2) top-20 ensemble docking ---
top20 = list(csv.DictReader(open('results/hits_ranked.csv', encoding='utf-8')))[:20]
jobs = []
for pid, rec in RECEPTORS.items():
    for h in top20:
        lig = f"docking/out/{h['name']}.out.pdbqt"
        jobs.append((rec['path'], f"docking/pdbqt/{h['name']}.pdbqt", f"{h['name']}_{pid}", rec['center'], 8))
print('ensemble docking jobs:', len(jobs))
results = {}
t0 = time.time()
with ThreadPoolExecutor(max_workers=20) as ex:
    futs = {ex.submit(run, *j): j[2] for j in jobs}
    for f in as_completed(futs):
        tag, score, atoms = f.result()
        results[tag] = score
        if len(results) % 10 == 0:
            print(f'{len(results)}/{len(jobs)} in {time.time()-t0:.0f}s', flush=True)

rows = []
for h in top20:
    n = h['name']
    rows.append({'name': n,
                 'vina_5I85': h['vina_best'],
                 'vina_5I81': results.get(f'{n}_5I81'),
                 'vina_5JG8': results.get(f'{n}_5JG8')})
with open('results/ensemble_scores.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=['name', 'vina_5I85', 'vina_5I81', 'vina_5JG8'])
    w.writeheader(); w.writerows(rows)
import statistics
diffs = [abs(float(r['vina_5I85']) - r['vina_5I81']) for r in rows if r['vina_5I81'] is not None]
print(f"5I85 vs 5I81 |Δ| median={statistics.median(diffs):.2f} max={max(diffs):.2f}")
for r in rows:
    print(r)
print('saved results/ensemble_scores.csv')
