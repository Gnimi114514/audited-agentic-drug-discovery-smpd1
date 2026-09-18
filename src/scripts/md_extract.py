"""Extract protein-only snapshots at 1..5 ns from the MD trajectory,
compute backbone RMSD + pocket geometry stats, and write per-snapshot PDBs
for the docking-ensemble analysis."""
import mdtraj as md
import numpy as np

WORK = '/mnt/c/Users/Gnimi/.zcode/workspace/default/cognition-drug-discovery'
MD_DIR = f'{WORK}/md'
POCKET_ORDINALS = None

traj = md.load(f'{MD_DIR}/prod.dcd', top=f'{MD_DIR}/solvated.pdb')
print('frames:', traj.n_frames, 'atoms:', traj.n_atoms, flush=True)
prot = traj.topology.select('protein')
traj_p = traj.atom_slice(prot)
print('protein atoms:', traj_p.n_atoms, flush=True)

# pocket residue ordinals within the protein (residue order as in md_run)
POCKET_IDS = {206, 208, 278, 282, 318, 319, 425, 457, 458, 459, 488}
crystal_ids, seen = [], set()
for l in open(f'{WORK}/structures/5i85_recA_ZN.pdb'):
    if l.startswith('ATOM'):
        rid = int(l[22:26])
        if rid not in seen:
            seen.add(rid); crystal_ids.append(rid)
id2ord = {rid: i for i, rid in enumerate(crystal_ids)}
pocket_ord = {id2ord[i] for i in POCKET_IDS}
pocket_res = [r for r in traj_p.topology.residues if r.index in pocket_ord]
pocket_atom_idx = [a.index for r in pocket_res for a in r.atoms if a.element.symbol != 'H']
print('pocket residues found:', [r.resSeq for r in pocket_res], flush=True)

# reference = first frame; report backbone RMSD (global fit) and pocket deviation (no fit — frozen)
ref = traj_p[0]
bb = traj_p.topology.select('backbone')
bb_rmsd = md.rmsd(traj_p, ref, frame=0, atom_indices=bb)
pocket_dev = np.sqrt((((traj_p.xyz[:, pocket_atom_idx] - traj_p.xyz[0][pocket_atom_idx])**2).sum(axis=2)).mean(axis=1))

for ns in (1, 2, 3, 4, 5):
    frame = ns * 200 - 1          # 5 ps/frame -> 200 frames per ns
    traj_p[frame].save_pdb(f'{MD_DIR}/snapshot_{ns}ns.pdb')
    print(f'{ns} ns: backbone-RMSD {bb_rmsd[frame]*10:.2f} A, pocket-dev {pocket_dev[frame]*10:.2f} A', flush=True)

print('\nsummary: backbone-RMSD mean/max = %.2f/%.2f A | pocket-dev mean/max = %.2f/%.2f A'
      % (bb_rmsd.mean()*10, bb_rmsd.max()*10, pocket_dev.mean()*10, pocket_dev.max()*10), flush=True)
with open(f'{MD_DIR}/md_summary.txt', 'w') as f:
    f.write('frames=%d protein_atoms=%d\n' % (traj.n_frames, traj_p.n_atoms))
    f.write('backbone_rmsd_A mean=%.3f max=%.3f final=%.3f\n' % (bb_rmsd.mean()*10, bb_rmsd.max()*10, bb_rmsd[-1]*10))
    f.write('pocket_dev_A mean=%.3f max=%.3f final=%.3f\n' % (pocket_dev.mean()*10, pocket_dev.max()*10, pocket_dev[-1]*10))
print('snapshots written', flush=True)
