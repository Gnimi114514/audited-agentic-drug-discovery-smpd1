"""Phase 3: redocking validation of phosphocholine into 5I85 ASM active site."""
import subprocess, math, itertools, re

VINA = 'bin/vina.exe'
CENTER = (-13.710, -34.100, -28.720)
SIZE = (18, 18, 18)

cmd = [VINA,
       '--receptor', 'structures/5i85_recA_ZN_prep.pdbqt',
       '--ligand', 'structures/PC_ref.pdbqt',
       '--center_x', str(CENTER[0]), '--center_y', str(CENTER[1]), '--center_z', str(CENTER[2]),
       '--size_x', str(SIZE[0]), '--size_y', str(SIZE[1]), '--size_z', str(SIZE[2]),
       '--exhaustiveness', '32', '--seed', '42', '--num_modes', '9',
       '--out', 'docking/redock_PC_out.pdbqt', '--log', 'docking/redock_PC.log']
r = subprocess.run(cmd, capture_output=True, text=True)
print(r.stdout[-1500:] if r.stdout else r.stderr[-1500:])

# parse crystal PC heavy atoms (PDB, element column)
def pdb_atoms(path, only_heavy=True):
    ats = []
    for l in open(path):
        if l.startswith(('ATOM', 'HETATM')):
            el = l[76:78].strip() or l[12:16].strip()[0]
            if only_heavy and el == 'H':
                continue
            ats.append((el, float(l[30:38]), float(l[38:46]), float(l[46:54])))
    return ats

def pdbqt_atoms(path, model_idx=0):
    ats, mi = [], 0
    for l in open(path):
        if l.startswith('MODEL'):
            mi = int(l[5:]) - 1
        if mi == model_idx and l.startswith(('ATOM', 'HETATM')):
            el = re.split(r'\s+', l.strip())[-1]
            el = re.sub(r'[^A-Za-z]', '', el)
            if el == 'HD':
                continue
            ats.append((el, float(l[30:38]), float(l[38:46]), float(l[46:54])))
    return ats

cryst = pdb_atoms('structures/5i85_PC.pdb')
best = pdbqt_atoms('docking/redock_PC_out.pdbqt', model_idx=0)
print('crystal atoms:', len(cryst), ' docked atoms:', len(best))

def rmsd_optimal(A, B):
    # element-wise optimal assignment (symmetric RMSD for equivalent phosphate O)
    tot, n = 0.0, 0
    for el in {a[0] for a in A}:
        X = [a for a in A if a[0] == el]
        Y = [b for b in B if b[0] == el]
        if len(X) != len(Y):
            print('count mismatch for', el, len(X), len(Y)); return None
        if len(X) <= 4:
            best_ = min(math.dist(a[1:], b[1:])**2 for a in X for b in Y) if len(X) == 1 else None
        import numpy as np
        D = np.array([[math.dist(a[1:], b[1:])**2 for b in Y] for a in X])
        try:
            from scipy.optimize import linear_sum_assignment
            ri, ci = linear_sum_assignment(D)
        except ImportError:
            ri, ci = list(range(len(X))), list(range(len(Y)))  # assume same order fallback
        tot += D[ri, ci].sum(); n += len(X)
    return math.sqrt(tot / n)

val = rmsd_optimal(cryst, best)
print('REDOCK RMSD (mode 1, heavy atoms, optimal assignment):', round(val, 2), 'A')

# also parse vina energies from log
for l in open('docking/redock_PC.log'):
    if l.strip().startswith('1') and '|' in l:
        print('log line:', l.rstrip())
        break
