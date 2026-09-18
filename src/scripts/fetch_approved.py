"""Phase 5 prep: fetch ChEMBL approved drugs (max_phase=4) for novelty NN search."""
import json, time
from chembl_webresource_client.new_client import new_client

rows, seen = [], set()
mols = new_client.molecule.filter(max_phase=4).only(
    ['molecule_chembl_id', 'pref_name', 'molecule_structures'])
for m in mols:
    st = m.get('molecule_structures') or {}
    smi = st.get('canonical_smiles')
    if not smi or smi in seen:
        continue
    seen.add(smi)
    rows.append({'chembl_id': m['molecule_chembl_id'], 'name': m.get('pref_name'), 'smiles': smi})

json.dump(rows, open('data/approved_drugs.json', 'w'), indent=0)
print('approved drugs fetched:', len(rows))
