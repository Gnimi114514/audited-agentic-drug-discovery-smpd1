from pathlib import Path
import json, builtins, contextlib
import numpy as np
root = Path('/mnt/c/Users/Gnimi/.zcode/workspace/default/cognition-drug-discovery')
out = root/'independent-audit/round8-acceptance'
source = root/'scripts/pocket_residence_r7.py'
real_open = builtins.open
def guarded_open(file, mode='r', *args, **kwargs):
    if any(m in mode for m in 'wax+'):
        p = Path(file)
        if p.name not in ('pocket_residence_r7_summary.json', 'pocket_residence_r7_frames.json'):
            raise RuntimeError('Unexpected write: '+str(file))
        file = out/p.name
    return real_open(file, mode, *args, **kwargs)
ns = {'__name__':'__main__'}
with real_open(out/'pocket_stdout.txt','w') as log, contextlib.redirect_stdout(log):
    builtins.open = guarded_open
    try:
        exec(compile(source.read_text(),str(source),'exec'),ns)
    finally:
        builtins.open = real_open
# Independently evaluate distances in native trajectory coordinates, pulling the
# mapped reference center back through each protein fit. This rotates the box
# consistently, unlike imaging fitted vectors with the unrotated cell.
t=ns['t']; bbidx=ns['bb_idx']; ligidx=ns['lig_idx']; pkidx=ns['pocket_atom_idx']
atom_list=list(t.topology.atoms)
counts={r:0 for r in ns['CRYSTAL_POCKET']}; distances=[]; rms=[]; occ={6:0,8:0,10:0}
for frame in t:
    x=frame.xyz[0]*10; L=frame.unitcell_vectors[0]*10; inv=np.linalg.inv(L)
    P=x[bbidx]; Q=ns['ref_bb']; pc=P.mean(0); qc=Q.mean(0)
    u,s,vt=np.linalg.svd((P-pc).T@(Q-qc)); correction=np.eye(3); correction[-1,-1]=np.linalg.det(u@vt)
    rotation=u@correction@vt
    native_center=(ns['PC_ANALYSIS']-qc)@rotation.T+pc
    delta=x[ligidx].mean(0)-native_center; delta=(delta@inv-np.rint(delta@inv))@L
    d=float(np.linalg.norm(delta)); distances.append(d)
    diff=x[ligidx,None,:]-x[None,pkidx,:]; frac=diff@inv
    contacts=np.linalg.norm((frac-np.rint(frac))@L,axis=2)<=4.5
    for rid in counts:
        cols=[i for i,a in enumerate(pkidx) if atom_list[a].residue.index==ns['id2ord'][rid]]
        counts[rid]+=int(contacts[:,cols].any())
    for cutoff in occ: occ[cutoff]+=int(d<=cutoff and contacts.any())
    aligned=(x[ligidx]-pc)@rotation+qc
    rms.append(float(np.sqrt(np.mean(np.sum((aligned-ns['ref_lig'])**2,axis=1)))))
diag={'independent_native_frame_occupancy_counts':occ,'contact_counts':counts,'center_distance_range_A':[min(distances),max(distances)],'producer_vs_native_center_distance_max_error_A':float(np.max(np.abs(np.array(distances)-[r['com_d_A'] for r in ns['rows']]))),'native_fit_ligand_rmsd_A':{'mean':float(np.mean(rms)),'max':max(rms)},'backbone_atom_count':len(bbidx),'backbone_order_names_match':[a.name for a in ns['crystal'].topology.atoms if a.name in ('N','CA','C','O')]==[atom_list[i].name for i in bbidx]}
(out/'independent_geometry.json').write_text(json.dumps(diag,indent=2))
print(json.dumps(ns['summary'],indent=2)); print(json.dumps(diag,indent=2))
