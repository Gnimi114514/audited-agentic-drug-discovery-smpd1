from pathlib import Path
import json
import numpy as np
root = Path('/mnt/c/Users/Gnimi/.zcode/workspace/default/cognition-drug-discovery')
out = root/'independent-audit/round7-acceptance'
src = (root/'scripts/pocket_residence_r5fix.py').read_text()
src = src.replace("f'{WORK}/runs/audit-20260913/tasks/sim-02/attempt-1/pocket_residence_r5fix_summary.json'", repr(str(out/'pocket_rerun.json')))
ns = {}
exec(compile(src, str(root/'scripts/pocket_residence_r5fix.py'), 'exec'), ns)
def val(x): return np.asarray(x).tolist()
ref_bb=ns['ref_bb']; dcd0=ns['dcd0_bb']; offset=ns['offset']
crystal=[]
for line in (root/'structures/5i85_recA_ZN.pdb').read_text().splitlines():
    if line.startswith('ATOM') and line[12:16].strip() in ('N','CA','C','O'):
        crystal.append([float(line[30:38]),float(line[38:46]),float(line[46:54])])
crystal=np.array(crystal)
R,t=ns['kabsch'](crystal,ref_bb)
correct_center=ns['POCKET_CENTER_CRYSTAL']@R.T+t
diag={'backbone_atoms':len(crystal),'ref_backbone_centroid_A':val(ref_bb.mean(0)), 'dcd0_backbone_centroid_A':val(dcd0.mean(0)), 'offset_A':val(offset), 'offset_per_atom_std_A':val((dcd0-ref_bb).std(0)), 'crystal_to_ref_backbone_fit_rmsd_A':float(np.sqrt(np.mean(np.sum((crystal@R.T+t-ref_bb)**2,axis=1)))), 'producer_center_A':val(ns['POCKET_CENTER_DCD0']), 'independent_crystal_center_in_analysis_ref_A':val(correct_center),'center_error_A':float(np.linalg.norm(correct_center-ns['POCKET_CENTER_DCD0'])), 'occupied_frames':sum(r['pocket_occupied'] for r in ns['rows'])}
(out/'frame_diagnostics.json').write_text(json.dumps(diag,indent=2))
print(json.dumps(diag,indent=2))
