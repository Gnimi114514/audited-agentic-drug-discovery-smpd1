import json, hashlib
from pathlib import Path
import numpy as np
import mdtraj as md

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
top=md.load_prmtop(str(ROOT/'md/complex.prmtop'))
protein=max(top.find_molecules(),key=len)
pi=sorted(a.index for a in protein)
bb=np.array([i for i in pi if top.atom(i).name in ('N','CA','C','O')])
li=np.array([a.index for a in top.atoms if a.residue.name=='LIG' and a.element.symbol!='H'])
ph=np.array([i for i in pi if top.atom(i).element.symbol!='H'])
anchor=[protein]
ref=md.load(str(ROOT/'md/bound_ref.pdb'),top=top)
ref.image_molecules(inplace=True,anchor_molecules=anchor,make_whole=True)
refxyz=ref.xyz[0].astype(float)

def transform(p,q):
    pc=p.mean(0);qc=q.mean(0)
    u,s,v=np.linalg.svd((p-pc).T@(q-qc))
    r=u@np.diag([1,1,np.linalg.det(u@v)])@v
    return r,qc-pc@r

crystal=[]; ids=[]; cbb={}
for line in (ROOT/'structures/5i85_recA_ZN.pdb').read_text().splitlines():
    if line.startswith('ATOM'):
        rid=int(line[22:26])
        if rid not in ids: ids.append(rid)
        cbb[(rid,line[12:16].strip())]=np.array([float(line[30:38]),float(line[38:46]),float(line[46:54])])/10
pres=sorted({top.atom(i).residue.index for i in pi})
assert len(pres)==len(ids)
mapping=dict(zip(pres,ids))
cat=[206,208,278,282,318,319,425,457,458,459,488]
cp=[];rp=[]
for i in bb:
    a=top.atom(int(i));key=(mapping[a.residue.index],a.name)
    if key in cbb: cp.append(cbb[key]);rp.append(refxyz[i])
r,shift=transform(np.array(cp),np.array(rp))
pc=np.array([[float(l[30:38]),float(l[38:46]),float(l[46:54])] for l in (ROOT/'structures/5i85_PC.pdb').read_text().splitlines() if l.startswith('HETATM')])/10
center=pc.mean(0)@r+shift
heavy_crystal=np.array([mapping[top.atom(int(i)).residue.index] for i in ph])
catmask=np.isin(heavy_crystal,cat)
pairs=np.array([(i,j) for i in li for j in ph])
mass=np.array([top.atom(int(i)).element.mass for i in li])
rows=[];touched=set();cat_touched=set();cats_counts={str(i):0 for i in cat}
for t in md.iterload(str(ROOT/'md/bound_v2.dcd'),top=top,chunk=10):
    # Actual minimum-image distances in nm, before fitting; all protein heavy atoms.
    ds=md.compute_distances(t,pairs,periodic=True).reshape(t.n_frames,len(li),len(ph))*10
    t.image_molecules(inplace=True,anchor_molecules=anchor,make_whole=True)
    for xyz,d in zip(t.xyz,ds):
        r,shift=transform(xyz[bb].astype(float),refxyz[bb])
        fitted=xyz[li]@r+shift
        rmsd=np.sqrt(np.mean(np.sum((fitted-refxyz[li])**2,axis=1)))*10
        hit=set(heavy_crystal[(d<=4.5).any(0)].tolist())
        hc=hit.intersection(cat);touched.update(hit);cat_touched.update(hc)
        for c in hc:cats_counts[str(c)]+=1
        dc=float(np.linalg.norm(fitted.mean(0)-center)*10)
        dm=float(np.linalg.norm(np.average(fitted,axis=0,weights=mass)-center)*10)
        rows.append(dict(frame=len(rows),ligand_protein_frame_rmsd_A=float(rmsd),crystal_centroid_distance_A=dc,mass_com_crystal_distance_A=dm,contact_crystal_residues=sorted(hit),catalytic_contacts=sorted(hc),min_catalytic_distance_A=float(d[:,catmask].min()),occupied_centroid_6A=bool(dc<=6 and hc),occupied_mass_com_6A=bool(dm<=6 and hc)))
    print('frames',len(rows),flush=True)

def stats(key):
    a=np.array([x[key] for x in rows]);return dict(mean=float(a.mean()),min=float(a.min()),max=float(a.max()),final=float(a[-1]))
producer=json.loads((ROOT/'runs/audit-20260913/tasks/sim-02/attempt-1/pocket_residence.json').read_text())
pro_contact=sorted(set(c for f in producer['metrics'] for c in f['contact_residues']))
summary=dict(frames=len(rows),protein_atoms=len(pi),backbone_atoms=len(bb),ligand_heavy_atoms=len(li),crystal_alignment_atoms=len(cp),residue_mapping=[dict(topology_residue_index=k,topology_resSeq=top.residue(k).resSeq,crystal_residue=v) for k,v in mapping.items() if v in cat],ligand_protein_frame_rmsd_A=stats('ligand_protein_frame_rmsd_A'),crystal_centroid_distance_A=stats('crystal_centroid_distance_A'),mass_com_crystal_distance_A=stats('mass_com_crystal_distance_A'),min_catalytic_distance_A=stats('min_catalytic_distance_A'),occupancy_centroid_6A=float(np.mean([x['occupied_centroid_6A'] for x in rows])),occupancy_mass_com_6A=float(np.mean([x['occupied_mass_com_6A'] for x in rows])),fraction_any_catalytic_contact=float(np.mean([bool(x['catalytic_contacts']) for x in rows])),contact_crystal_residues=sorted(touched),catalytic_residues_ever_touched=sorted(cat_touched),catalytic_frame_counts=cats_counts,producer_summary=producer['summary'],producer_contact_residue_labels=pro_contact,producer_contact_labels_mapped_to_crystal={str(n):mapping[top.atom(next(i for i in pi if top.atom(i).residue.resSeq==n)).residue.index] for n in pro_contact},method='MDTraj make_whole + protein-anchor image_molecules in nm; backbone Kabsch fit applied to ligand; minimized reference identically imaged; crystal PC centroid transformed by crystal-to-reference backbone fit; heavy contacts <=4.5 A using periodic distances; 6 A center AND >=1 catalytic contact occupancy')
summary['occupancy_centroid_radius_sensitivity']={str(radius):float(np.mean([x['crystal_centroid_distance_A']<=radius and bool(x['catalytic_contacts']) for x in rows])) for radius in [6,8,10]}
summary['mdtraj_version']=md.__version__
summary['catalytic_names_in_topology']={str(mapping[top.atom(int(i)).residue.index]):top.atom(int(i)).residue.name for i in pi if mapping[top.atom(int(i)).residue.index] in cat}
(OUT/'c1_evidence.json').write_text(json.dumps(dict(summary=summary,frames=rows),indent=2))
print(json.dumps(summary,indent=2))
