"""R3-1 repair: pocket-residence analysis with correct reference frames.

Metrics (pre-specified here, per reviewer's method note):
- largest covalent molecule = protein selection (8,214 atoms incl. HIE etc.)
- backbone = N/CA/C/O within that molecule (2,112 atoms)
- ligand heavy atoms: whole-molecule minimum-image vs MINIMIZED REFERENCE,
  then Kabsch superposition on protein backbone -> ligand RMSD in protein frame
- pocket occupancy: fraction of frames with ligand COM (protein-frame) within 6 A of
  the crystal ligand position AND >=1 heavy atom within 4.5 A of any pocket residue atom
- key-residue contacts: per-frame count of pocket residues (D206/H208/D278/H282/N318/
  H319/H425/H457/T458/H459/Y488 crystal ids) with any ligand heavy atom <= 4.5 A
"""
import json
import numpy as np
import mdtraj as md

WORK = '/mnt/c/Users/Gnimi/.zcode/workspace/default/cognition-drug-discovery'
t = md.load(f'{WORK}/md/bound_v2.dcd', top=f'{WORK}/md/complex.prmtop')
ref = md.load(f'{WORK}/md/bound_ref.pdb')
print('frames:', t.n_frames, flush=True)

# protein = largest covalent molecule (per reviewer)
mols = [(len(m), m) for m in t.topology.find_molecules()]
mols.sort(key=lambda x: -x[0])
prot_mol = mols[0][1]
prot_set = set(prot_mol)
bb_idx = [a.index for a in t.topology.atoms
          if a in prot_set and a.name in ('N', 'CA', 'C', 'O')]
print('protein molecule atoms:', len(prot_mol), 'backbone:', len(bb_idx), flush=True)

lig_idx = [a.index for a in t.topology.atoms if a.residue.name == 'LIG' and a.element.symbol != 'H']
zn_idx = [a.index for a in t.topology.atoms if a.residue.name == 'ZN']
print('LIG heavy:', len(lig_idx), 'ZN:', len(zn_idx), flush=True)

# crystal pocket residues -> fixed-topology residue indices (fixed resids are 1..528 ordinal+1)
CRYSTAL_POCKET = [206, 208, 278, 282, 318, 319, 425, 457, 458, 459, 488]
crystal_ids, seen = [], set()
for l in open(f'{WORK}/structures/5i85_recA_ZN.pdb'):
    if l.startswith('ATOM'):
        rid = int(l[22:26])
        if rid not in seen:
            seen.add(rid); crystal_ids.append(rid)
id2ord = {rid: i for i, rid in enumerate(crystal_ids)}
pocket_ords = {id2ord[r] + 1 for r in CRYSTAL_POCKET}
# residue-mapping audit note (R4 review): fixed-resSeq = crystal-resSeq - 83
# (verified: crystal CA resid 84 -> fixed resid 1). The mapping below therefore yields
# fixed resSeq equal to the crystal numbering offset; contacted fixed resSeqs are
# translated back to crystal numbering in the summary.
pocket_atom_idx = [a.index for a in t.topology.atoms
                   if a.residue.resSeq in pocket_ords and a.element.symbol != 'H']
pocket_res_ids = sorted({a.residue.resSeq for a in t.topology.atoms if a.residue.resSeq in pocket_ords})
print('pocket atoms:', len(pocket_atom_idx), 'residues:', pocket_res_ids, flush=True)

# reference positions (minimized, crystal frame)
ref_lig = ref.xyz[0][lig_idx] * 10     # A
ref_bb = ref.xyz[0][bb_idx] * 10
ref_pocket = ref.xyz[0][pocket_atom_idx] * 10
# crystal PC centroid = pocket center proxy (from structures/5i85_PC.pdb)
pc = []
for l in open(f'{WORK}/structures/5i85_PC.pdb'):
    if l.startswith('HETATM'):
        pc.append([float(l[30:38]), float(l[38:46]), float(l[46:54])])
POCKET_CENTER = np.mean(pc, axis=0)  # A, crystal frame

def kabsch_fit_moveto_ref(P, Q):
    """Return P transformed onto Q (both (n,3) A)."""
    pm_, qm_ = P.mean(axis=0), Q.mean(axis=0)
    H = (P - pm_).T @ (Q - qm_)
    U, S, Vt = np.linalg.svd(H)
    d = np.sign(np.linalg.det(Vt.T @ U.T))
    R = Vt.T @ np.diag([1, 1, d]) @ U.T
    return (P - pm_) @ R.T + qm_

out = {'n_frames': t.n_frames, 'metrics': []}
occ_frames = 0
for fi in range(t.n_frames):
    # box vectors from mdtraj are in NANOMETERS; all analysis below is in ANGSTROM.
    # Scale the box by 10 once so fractional imaging operates in A-space consistently.
    L = np.array(t.unitcell_vectors[fi]) * 10.0
    Linv = np.linalg.inv(L)
    # whole-molecule imaging of ligand & pocket relative to frame-0 COM (A-space)
    x = t.xyz[fi] * 10
    x0 = t.xyz[0] * 10
    def image_group_A(idx):
        com = x[idx].mean(axis=0); com0 = x0[idx].mean(axis=0)
        dcom = com - com0
        frac = dcom @ Linv; frac -= np.round(frac)
        return dcom - (frac @ L)
    sh_l = image_group_A(lig_idx)
    sh_p = image_group_A(bb_idx)
    sh_k = image_group_A(pocket_atom_idx)
    xlig = x[lig_idx] - sh_l
    xbb = x[bb_idx] - sh_p
    xpk = x[pocket_atom_idx] - sh_k
    # protein-frame: fit backbone onto reference backbone, apply to ligand & pocket
    bb_fit = kabsch_fit_moveto_ref(xbb, ref_bb)
    # transform = (xbb -> ref_bb); apply same rigid transform to ligand
    pm_, qm_ = xbb.mean(axis=0), ref_bb.mean(axis=0)
    H = (xbb - pm_).T @ (ref_bb - qm_)
    U, S, Vt = np.linalg.svd(H)
    d = np.sign(np.linalg.det(Vt.T @ U.T))
    R = Vt.T @ np.diag([1, 1, d]) @ U.T
    tt = qm_ - R @ pm_
    lig_in_prot = xlig @ R.T + tt
    pk_in_prot = xpk @ R.T + tt
    lig_rmsd = float(np.sqrt(((lig_in_prot - ref_lig)**2).sum(axis=1).mean()))
    # contacts: ligand-in-prot vs pocket-in-prot (both imaged to frame0 then protein-fitted)
    n_res_contact = 0
    contact_res = set()
    # vectorized: distance matrix ligand x pocket
    D = np.linalg.norm(lig_in_prot[:, None, :] - pk_in_prot[None, :, :], axis=2)
    touched = (D <= 4.5).any(axis=0)
    # map pocket atom idx -> residue ordinal
    touched_res = set()
    ai = 0
    res_of_atom = []
    for a in t.topology.atoms:
        if a.index in set(pocket_atom_idx):
            res_of_atom.append((a.index, a.residue.resSeq))
    resseq_by_pos = {}
    for pos, (aidx, rseq) in enumerate(res_of_atom):
        resseq_by_pos.setdefault(rseq, []).append(pos)
    for rseq, positions in resseq_by_pos.items():
        if touched[positions].any():
            n_res_contact += 1
            contact_res.add(rseq)
    com_disp = float(np.linalg.norm(lig_in_prot.mean(axis=0) - ref_lig.mean(axis=0)))
    # occupancy: COM within 6 A of crystal PC center AND >=1 contact
    near_center = np.linalg.norm(lig_in_prot.mean(axis=0) - POCKET_CENTER) <= 6.0
    is_occ = bool(near_center and n_res_contact >= 1)
    occ_frames += is_occ
    out['metrics'].append({'frame': fi, 'ligand_protein_frame_rmsd_A': round(lig_rmsd, 3),
                           'com_disp_A': round(com_disp, 3), 'pocket_contacts': n_res_contact,
                           'contact_residues': sorted(contact_res), 'pocket_occupied': is_occ})
    if fi % 100 == 0:
        print(fi, 'ligRMSD %.2f comDisp %.2f contacts %d' % (lig_rmsd, com_disp, n_res_contact), flush=True)

lr = [m['ligand_protein_frame_rmsd_A'] for m in out['metrics']]
cc = [m['pocket_contacts'] for m in out['metrics']]
ord2crystal = {id2ord[r]: r for r in CRYSTAL_POCKET}   # fixed ordinal (1-based resSeq) -> crystal resSeq
crystal_touched, nonpocket_touched = [], []
for m in out['metrics']:
    for rseq in m['contact_residues']:
        key = int(rseq)
        if key in ord2crystal:
            crystal_touched.append(ord2crystal[key])
        else:
            nonpocket_touched.append(key)   # contact-boundary neighbors outside the 11 catalytic residues
crystal_touched = sorted(set(crystal_touched))
cat_touched_crystal = sorted(set(crystal_touched) & set(CRYSTAL_POCKET))
out['summary'] = {
    'ligand_protein_frame_rmsd_A': {'mean': round(float(np.mean(lr)), 3),
                                     'max': round(float(np.max(lr)), 3),
                                     'final': lr[-1]},
    'pocket_contacts_mean': round(float(np.mean(cc)), 2),
    'pocket_occupancy_fraction': round(occ_frames / t.n_frames, 3),
    'definition': 'occupied = ligand COM (protein frame) within 6 A of crystal PC centroid AND >=1 pocket residue heavy atom within 4.5 A',
    'contacted_catalytic_residues_crystal_numbering': crystal_touched,
    'contacted_nonpocket_residues_fixed_numbering': sorted(set(nonpocket_touched)),
    'catalytic_residues_ever_contacted_crystal_numbering': cat_touched_crystal,
    'units_note': 'box vectors scaled nm->A before imaging; all distances reported in A',
}
json.dump(out, open(f'{WORK}/independent-audit/round5-acceptance/pocket_rerun.json', 'w'), indent=1)
print('SUMMARY:', json.dumps(out['summary'], indent=1), flush=True)
