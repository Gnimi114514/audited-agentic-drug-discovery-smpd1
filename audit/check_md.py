import json
from pathlib import Path
import numpy as np
import mdtraj as md
import parmed as pmd

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent
def stats(x):
    x=np.asarray(x)
    return dict(min=float(x.min()),max=float(x.max()),mean=float(x.mean()),final=float(x[-1]))
pm=pmd.load_file(str(ROOT/'md/complex.prmtop'),xyz=str(ROOT/'md/complex.inpcrd'))
top=md.Topology.from_openmm(pm.topology)
lig=top.select('resname LIG and not element H')
zn=top.select('resname ZN')
protein=top.select('protein')
bb=top.select('backbone')
pairs=np.array([(int(z),int(l)) for z in zn for l in lig])
dist=[]
ligxyz=[]
bbxyz=[]
times=[]
for t in md.iterload(str(ROOT/'md/bound.dcd'),top=top,chunk=50):
    dist.extend(md.compute_distances(t,pairs,periodic=True).min(axis=1)*10)
    # Reconstruct each bonded molecule before a protein-frame fit.
    t.image_molecules(inplace=True,anchor_molecules=[set(top.atom(i) for i in protein)],make_whole=True)
    ligxyz.append(t.xyz[:,lig].copy())
    bbxyz.append(t.xyz[:,bb].copy())
    times.extend(t.time.tolist())
lx=np.concatenate(ligxyz); bx=np.concatenate(bbxyz)
# Use imaged first saved frame, not the unavailable minimized x0, as reference.
ref=bx[0]; aligned=[]; fittedbb=[]; internal=[]
for b,l in zip(bx,lx):
    pc=b.mean(0); qc=ref.mean(0)
    u,s,vt=np.linalg.svd((b-pc).T@(ref-qc))
    rot=u@np.diag([1,1,np.linalg.det(u@vt)])@vt
    aligned.append(np.sqrt(np.mean(np.sum(((l-pc)@rot+qc-lx[0])**2,axis=1)))*10)
    fittedbb.append(np.sqrt(np.mean(np.sum(((b-pc)@rot+qc-ref)**2,axis=1)))*10)
    lc=l-l.mean(0); lr=lx[0]-lx[0].mean(0)
    u,s,vt=np.linalg.svd(lc.T@lr)
    rot=u@np.diag([1,1,np.linalg.det(u@vt)])@vt
    internal.append(np.sqrt(np.mean(np.sum((lc@rot-lr)**2,axis=1)))*10)
ions=[dict(index=a.idx,name=a.name,type=a.type,charge=a.charge,rmin=a.rmin,epsilon=a.epsilon) for a in pm.atoms if a.residue.name=='ZN']
out=dict(bound_frames=len(dist),lig_heavy=len(lig),zn_count=len(zn),
    bound_dcd_time_ps=dict(first=times[0],last=times[-1]),
    min_zn_ligand_A=stats(dist),fraction_min_distance_in_1p9_2p1=float(np.mean((np.array(dist)>=1.9)&(np.array(dist)<=2.1))),
    ligand_rmsd_A_protein_backbone_fit_first_saved_frame=stats(aligned),
    backbone_rmsd_A_first_saved_frame=stats(fittedbb),
    ligand_internal_rmsd_A_self_fit=stats(internal),zn_parameters=ions)
apo_top=md.load_topology(str(ROOT/'md/solvated.pdb'))
apo_bb=apo_top.select('backbone'); apo_rms=[]; apo_frames=0; apo_times=[]; reference=None
for t in md.iterload(str(ROOT/'md/prod.dcd'),top=apo_top,chunk=30):
    apo_frames+=len(t); apo_times.extend(t.time.tolist())
    if reference is None: reference=t[0]
    apo_rms.extend(md.rmsd(t,reference,atom_indices=apo_bb)*10)
out['apo']=dict(frames=apo_frames,protein_atoms=len(apo_top.select('protein')),backbone_rmsd_A=stats(apo_rms),dcd_time_ps=dict(first=apo_times[0],last=apo_times[-1]))
(OUT/'md_results.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2),flush=True)
