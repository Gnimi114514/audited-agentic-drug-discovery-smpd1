import json
from pathlib import Path
import numpy as np
import mdtraj as md
import parmed as pmd
ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
def stats(a):
    a=np.asarray(a);return dict(min=float(a.min()),mean=float(a.mean()),max=float(a.max()),final=float(a[-1]))
pm=pmd.load_file(str(ROOT/'md/complex.prmtop'))
top=md.Topology.from_openmm(pm.topology)
lig=top.select('resname LIG and not element H'); zn=top.select('resname ZN')
protein=np.array(sorted(a.index for a in max(top.find_molecules(),key=len)))
bb=np.array([i for i in protein if top.atom(int(i)).name in ('N','CA','C','O')])
ref=md.load(str(ROOT/'md/bound_ref.pdb'),top=top)
ref.image_molecules(inplace=True,anchor_molecules=[set(top.atom(int(i)) for i in protein)],make_whole=True)
lr=ref.xyz[0,lig].copy();br=ref.xyz[0,bb].copy()
pairs=np.array([(z,l) for z in zn for l in lig])
dist=[];centered=[];fitlig=[];fitbb=[];ligcom=[]
for t in md.iterload(str(ROOT/'md/bound_v2.dcd'),top=top,chunk=40):
    dist.extend(md.compute_distances(t,pairs,periodic=True).min(axis=1)*10)
    t.image_molecules(inplace=True,anchor_molecules=[set(top.atom(int(i)) for i in protein)],make_whole=True)
    for xyz in t.xyz:
        l=xyz[lig];b=xyz[bb]
        lc=l-l.mean(0);rc=lr-lr.mean(0)
        centered.append(np.sqrt(np.mean(np.sum((lc-rc)**2,axis=1)))*10)
        pc=b.mean(0);qc=br.mean(0)
        u,s,vt=np.linalg.svd((b-pc).T@(br-qc))
        rot=u@np.diag([1,1,np.linalg.det(u@vt)])@vt
        la=(l-pc)@rot+qc
        fitlig.append(np.sqrt(np.mean(np.sum((la-lr)**2,axis=1)))*10)
        fitbb.append(np.sqrt(np.mean(np.sum(((b-pc)@rot+qc-br)**2,axis=1)))*10)
        ligcom.append(np.linalg.norm(la.mean(0)-lr.mean(0))*10)
out=dict(frames=len(dist),protein_backbone_atoms=len(bb),protein_selection='largest bonded molecule; backbone names N/CA/C/O; includes modified protein residues',protein_atom_count=len(protein),protein_residue_names=sorted({top.atom(int(i)).residue.name for i in protein}),ligand_heavy_atoms=len(lig),
 zn=[dict(index=a.idx,charge=a.charge,rmin=a.rmin,epsilon=a.epsilon) for a in pm.atoms if a.residue.name=='ZN'],
 min_zn_ligand_A=stats(dist),fraction_min_lt3=float(np.mean(np.array(dist)<3)),
 centered_unrotated_ligand_rmsd_A=stats(centered),protein_fitted_ligand_rmsd_A=stats(fitlig),
 protein_fitted_ligand_centroid_displacement_A=stats(ligcom),protein_backbone_rmsd_A=stats(fitbb),
 logged_frames=[dict(frame=i+1,time_ps=(i+1)*5,min_distance_A=float(dist[i]),
 centered_rmsd_A=float(centered[i]),protein_fit_ligand_A=float(fitlig[i]),backbone_A=float(fitbb[i])) for i in [19,219,419,619]])
# Inspect actual OpenMM forces without starting a simulation.
from openmm import app,unit
sys=pm.createSystem(nonbondedMethod=app.PME,nonbondedCutoff=1*unit.nanometer,constraints=app.HBonds)
out['forces']=[dict(type=type(f).__name__,name=f.getName()) for f in sys.getForces()]
(OUT/'md_v2_results.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
