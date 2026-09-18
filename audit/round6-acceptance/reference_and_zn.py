from pathlib import Path
import json,numpy as np,mdtraj as md
root=Path('/mnt/c/Users/Gnimi/.zcode/workspace/default/cognition-drug-discovery');out=root/'independent-audit/round6-acceptance'
top=md.load_prmtop(str(root/'md/complex.prmtop'));ref=md.load(str(root/'md/bound_ref.pdb'),top=top)
ids=[];coords={}
for l in (root/'structures/5i85_recA_ZN.pdb').read_text().splitlines():
 if l.startswith('ATOM'):
  rid=int(l[22:26])
  if rid not in ids:ids.append(rid)
  coords[(rid,l[12:16].strip())]=[float(l[a:a+8]) for a in (30,38,46)]
p=[];q=[]
for a in top.atoms:
 if a.residue.index<len(ids) and a.name in ('N','CA','C','O'):
  key=(ids[a.residue.index],a.name)
  if key in coords:p.append(coords[key]);q.append(ref.xyz[0,a.index]*10)
p=np.array(p);q=np.array(q);u,s,v=np.linalg.svd((p-p.mean(0)).T@(q-q.mean(0)));r=u@np.diag([1,1,np.linalg.det(u@v)])@v;shift=q.mean(0)-p.mean(0)@r
pc=np.array([[float(l[a:a+8]) for a in (30,38,46)] for l in (root/'structures/5i85_PC.pdb').read_text().splitlines() if l.startswith('HETATM')]).mean(0)
result={'crystal_center_A':pc.tolist(),'center_in_raw_minimized_reference_A':(pc@r+shift).tolist(),'center_shift_A':float(np.linalg.norm(pc@r+shift-pc)),'matched_backbone_atoms':len(p)}
try:
 import parmed as pm
 t=pm.load_file(str(root/'md/complex.prmtop'));z=next(a for a in t.atoms if a.residue.name=='ZN');idx=z.nb_idx;n=t.parm_data['POINTERS'][1];k=t.parm_data['NONBONDED_PARM_INDEX'][(idx-1)*n+idx-1]-1;A=t.parm_data['LENNARD_JONES_ACOEF'][k];B=t.parm_data['LENNARD_JONES_BCOEF'][k];result['Zn_epsilon_kcal_mol']=B*B/(4*A)
except ImportError as e:result['parmed_error']=str(e)
(out/'reference_and_zn.json').write_text(json.dumps(result,indent=2));print(result)
