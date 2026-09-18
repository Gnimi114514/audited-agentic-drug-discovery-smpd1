"""Align MD snapshots back to the crystal frame via frozen-pocket CA Kabsch fit (WSL/mdtraj)."""
import mdtraj as md
import numpy as np

WORK = '/mnt/c/Users/Gnimi/.zcode/workspace/default/cognition-drug-discovery'
MD_DIR = f'{WORK}/md'
POCKET_IDS = {206, 208, 278, 282, 318, 319, 425, 457, 458, 459, 488}

crystal_ids, seen = [], set()
for l in open(f'{WORK}/structures/5i85_recA_ZN.pdb'):
    if l.startswith('ATOM'):
        rid = int(l[22:26])
        if rid not in seen:
            seen.add(rid); crystal_ids.append(rid)
id2ord = {rid: i for i, rid in enumerate(crystal_ids)}
POCKET_ORD = sorted(id2ord[i] for i in POCKET_IDS)

# crystal pocket CA coordinates in pocket-ordinal order
want_ords = set(POCKET_ORD)
res_ord_of_crystal = {id2ord[rid]: rid for rid in crystal_ids}
crystal_ca = {}
seen_res = set()
for l in open(f'{WORK}/structures/5i85_recA_ZN.pdb'):
    if l.startswith('ATOM'):
        rid = int(l[22:26])
        if rid in seen_res:
            continue
        seen_res.add(rid)
        o = id2ord[rid]
        if o in want_ords:
            # next CA line for this residue
            crystal_ca[o] = None
# simpler: second pass, collect CA per residue
res_order = []
seen = set()
resmap = {}
for l in open(f'{WORK}/structures/5i85_recA_ZN.pdb'):
    if l.startswith('ATOM'):
        rid = int(l[22:26])
        if rid not in seen:
            seen.add(rid); resmap[rid] = len(res_order); res_order.append(rid)
crystal_ca = {}
seen = set()
for l in open(f'{WORK}/structures/5i85_recA_ZN.pdb'):
    if l.startswith('ATOM') and l[12:16].strip() == 'CA':
        rid = int(l[22:26])
        if rid in id2ord and id2ord[rid] in want_ords and rid not in seen:
            seen.add(rid)
            crystal_ca[id2ord[rid]] = np.array([float(l[30:38]), float(l[38:46]), float(l[46:54])])
Q = np.array([crystal_ca[o] for o in POCKET_ORD])

def kabsch(P, Q):
    p_mean = P.mean(axis=0); q_mean = Q.mean(axis=0)
    H = (P - p_mean).T @ (Q - q_mean)
    U, S, Vt = np.linalg.svd(H)
    d = np.sign(np.linalg.det(Vt.T @ U.T))
    R = Vt.T @ np.diag([1, 1, d]) @ U.T
    t = q_mean - R @ p_mean
    return R, t

for ns in (1, 2, 3, 4, 5):
    t = md.load(f'{MD_DIR}/snapshot_{ns}ns.pdb')
    snap_ca = {}
    for r in t.topology.residues:
        if r.index in POCKET_ORD:
            for a in r.atoms:
                if a.name == 'CA':
                    snap_ca[r.index] = t.xyz[0][a.index] * 10
    P = np.array([snap_ca[o] for o in POCKET_ORD])
    R, tt = kabsch(P, Q)
    fit_rms = float(np.sqrt((((P @ R.T + tt) - Q) ** 2).sum(axis=1).mean()))
    t.xyz[0] = ((t.xyz[0] * 10) @ R.T + tt) / 10
    t.save_pdb(f'{MD_DIR}/snapshot_{ns}ns_al.pdb')
    print(f'{ns} ns aligned, pocket fit RMSD {fit_rms:.3f} A', flush=True)
print('done')
