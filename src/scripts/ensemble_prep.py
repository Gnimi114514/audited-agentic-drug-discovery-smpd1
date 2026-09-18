"""Big item 1: ensemble receptors — superpose 5I81 & 5JG8 chain A onto the 5I85 frame
(Ca-Kabsch by residue number), verify Zn overlap, prep rigid PDBQTs."""
import numpy as np, subprocess, os

OB = r'C:/ProgramData/anaconda3/envs/ob/Library/bin/obabel.exe'

def read_pdb_atoms(path, chain='A'):
    prot, zn = [], []
    for l in open(path):
        rec = l[:6].strip()
        if rec == 'ATOM' and l[21] == chain:
            prot.append(l)
        elif rec == 'HETATM' and l[21] == chain and l[17:20].strip() == 'ZN':
            zn.append(l)
    return prot, zn

def kabsch(P, Q):
    """Return rotation R, translation t minimizing |P R + t - Q|^2."""
    p_mean = P.mean(axis=0); q_mean = Q.mean(axis=0)
    Pc, Qc = P - p_mean, Q - q_mean
    H = Pc.T @ Qc
    U, S, Vt = np.linalg.svd(H)
    d = np.sign(np.linalg.det(Vt.T @ U.T))
    D = np.diag([1, 1, d])
    R = Vt.T @ D @ U.T
    t = q_mean - R @ p_mean
    return R, t

def transform_lines(lines, R, t):
    out = []
    for l in lines:
        x, y, z = float(l[30:38]), float(l[38:46]), float(l[46:54])
        v = R @ np.array([x, y, z]) + t
        out.append(l[:30] + f'{v[0]:8.3f}{v[1]:8.3f}{v[2]:8.3f}' + l[54:])
    return out

# reference: 5I85 chain A Ca + Zn
ref_prot, ref_zn = read_pdb_atoms('structures/5i85.pdb', 'A')
ref_ca = {int(l[22:26]): (float(l[30:38]), float(l[38:46]), float(l[46:54]))
          for l in ref_prot if l[12:16].strip() == 'CA'}
ref_zn_xyz = np.array([[float(l[30:38]), float(l[38:46]), float(l[46:54])] for l in ref_zn])

for pid in ['5i81', '5jg8']:
    prot, zn = read_pdb_atoms(f'structures/{pid}.pdb', 'A')
    ca = {int(l[22:26]): (float(l[30:38]), float(l[38:46]), float(l[46:54]))
          for l in prot if l[12:16].strip() == 'CA'}
    common = sorted(set(ref_ca) & set(ca))
    P = np.array([ca[r] for r in common]); Q = np.array([ref_ca[r] for r in common])
    R, t = kabsch(P, Q)
    rmsd_ca = np.sqrt((((P @ R.T + t) - Q) ** 2).sum(axis=1).mean())
    zn_xyz = np.array([[float(l[30:38]), float(l[38:46]), float(l[46:54])] for l in zn])
    zn_t = zn_xyz @ R.T + t if len(zn_xyz) else None
    zn_rmsd = (np.sqrt((((zn_t - ref_zn_xyz) ** 2).sum(axis=1).mean()))
               if zn_t is not None and len(zn_t) == len(ref_zn_xyz) else float('nan'))
    print(f'{pid}: {len(common)} matched Ca, superpose Ca-RMSD={rmsd_ca:.2f} A, Zn-RMSD={zn_rmsd:.2f} A')
    # write aligned raw pdb (protein + Zn)
    with open(f'structures/{pid}_recA_ZN_aln.pdb', 'w') as f:
        f.writelines(transform_lines(prot, R, t))
        f.writelines(transform_lines(zn, R, t))
        f.write('TER\nEND\n')
    # prep: add H at pH 7.4 -> pdbqt -> strip torsion records
    r1 = subprocess.run([OB, f'structures/{pid}_recA_ZN_aln.pdb',
                         '-O', f'structures/{pid}_prep.pdbqt', '-h', '-p', '7.4'],
                        capture_output=True, text=True)
    keep = [l for l in open(f'structures/{pid}_prep.pdbqt')
            if l.startswith(('ATOM', 'HETATM', 'TER', 'END'))]
    open(f'structures/{pid}_rigid.pdbqt', 'w').writelines(keep)
    print(f'  {pid}_rigid.pdbqt: {len(keep)} lines (obabel rc={r1.returncode})')
print('done')
