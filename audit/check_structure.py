import csv
import itertools
import json
from pathlib import Path
import numpy as np
from scipy.optimize import linear_sum_assignment
ROOT=Path(__file__).resolve().parents[1]
OUT=Path(__file__).resolve().parent
def atoms(path):
    rows=[]
    for l in path.read_text().splitlines():
        if l.startswith('ENDMDL'): break
        if l.startswith(('ATOM','HETATM')):
            name=l[12:16].strip()
            if name.startswith('H'):continue
            rows.append((name,np.array([float(l[30:38]),float(l[38:46]),float(l[46:54])]),l.split()[-1]))
    return rows
a=atoms(ROOT/'structures/5i85_PC.pdb')
b=atoms(ROOT/'docking/redock_PC_out.pdbqt')
bd={n:x for n,x,_ in b}
direct=np.sqrt(np.mean([np.sum((x-bd[n])**2) for n,x,_ in a]))
# Allow all three terminal phosphate oxygens and trimethylammonium methyls.
# Bridging O2 and backbone carbons stay fixed, preserving ligand connectivity.
best=direct
for oxy in itertools.permutations(['O1','O3','O4']):
    for methyl in itertools.permutations(['C3','C4','C5']):
        mapping=dict(zip(['O1','O3','O4','C3','C4','C5'],[*oxy,*methyl]))
        best=min(best,np.sqrt(np.mean([np.sum((x-bd[mapping.get(n,n)])**2) for n,x,_ in a])))
lower=0
for el in set(n[0] for n,_,_ in a):
    x=np.array([x for n,x,_ in a if n[0]==el]);y=np.array([x for n,x,_ in b if n[0]==el])
    d=((x[:,None]-y[None,:])**2).sum(-1)
    i,j=linear_sum_assignment(d);lower+=d[i,j].sum()
with (ROOT/'data/library_filtered.csv').open() as f:
    rows=list(csv.DictReader(f))
clean=sum(not r.get('error') and not r.get('alerts') and abs(int(r['charge']))<=1 for r in rows)
mol2=(ROOT/'md/leader.mol2').read_text().split('@<TRIPOS>ATOM')[1].split('@<TRIPOS>')[0].strip().splitlines()
out=dict(redock_heavy_atoms=len(a),name_matched_rmsd_A=float(direct),restricted_symmetry_rmsd_A=float(best),element_assignment_lower_bound_A=float(np.sqrt(lower/len(a))),clean_library_rows=clean,ligand_mol2_atoms=len(mol2),mol2_total_charge=sum(float(l.split()[-1]) for l in mol2))
(OUT/'structure_results.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
