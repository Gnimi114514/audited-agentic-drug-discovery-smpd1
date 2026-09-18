"""Phase 2: ChEMBL novelty verification for the three finalists."""
import json, time
from chembl_webresource_client.new_client import new_client

FINALISTS = ['PLCG2', 'INPP5D', 'SMPD1']
out = {}
for gene in FINALISTS:
    rec = {}
    ts = list(new_client.target.search(gene))
    match = None
    for t in ts:
        if gene in (t.get('target_pref_name') or '') or gene in [x.split('_')[0] for x in (t.get('target_synonyms') or [])]:
            match = t
            break
    if match is None and ts:
        match = ts[0]
    if match is None:
        print(gene, 'NOT FOUND in ChEMBL'); continue
    tid = match['target_chembl_id']
    rec['chembl_id'] = tid
    rec['pref_name'] = match.get('target_pref_name')
    rec['target_type'] = match.get('target_type')
    # activities
    acts = new_client.activity.filter(target_chembl_id=tid, pchembl_value__isnull=False)
    rows = list(acts[:15])
    n = len(rows)
    rec['n_activities'] = n
    rec['examples'] = [{'assay': a.get('assay_chembl_id'), 'type': a.get('standard_type'),
                        'value': a.get('standard_value'), 'unit': a.get('standard_units'),
                        'pchembl': a.get('pchembl_value'), 'mol': a.get('molecule_chembl_id'),
                        'doc': a.get('document_chembl_id')} for a in rows]
    # max phase for compounds recorded against this target
    mech = list(new_client.mechanism.filter(target_chembl_id=tid))
    rec['mechanisms'] = [{'mol': m.get('molecule_chembl_id'), 'moa': m.get('mechanism_of_action'),
                          'max_phase': m.get('max_phase')} for m in mech[:20]]
    print(gene, tid, rec['pref_name'], 'activities:', n, 'mech rows:', len(rec['mechanisms']))
    out[gene] = rec
    time.sleep(1)

json.dump(out, open('data/chembl_finalists.json', 'w'), indent=1)
print('saved data/chembl_finalists.json')
