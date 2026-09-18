"""Phase 4: build CNS-friendly drug-like screening library from ChEMBL."""
import json, time
from chembl_webresource_client.new_client import new_client

TARGET_N = 50000
props = dict(
    molecule_properties__full_mwt__range=[250, 450],
    molecule_properties__psa__lte=90,
    molecule_properties__hbd__lte=2,
    molecule_properties__alogp__range=[1.5, 4.5],
    molecule_structures__isnull=False,
)

mols = new_client.molecule.filter(**props).only(
    ['molecule_chembl_id', 'molecule_structures', 'molecule_properties'])
out, seen = [], set()
t0 = time.time()
for m in mols:
    st = m.get('molecule_structures') or {}
    smi = st.get('canonical_smiles')
    if not smi or '.' in smi:   # skip salts/mixtures
        continue
    if smi in seen:
        continue
    seen.add(smi)
    p = m.get('molecule_properties') or {}
    out.append({'chembl_id': m['molecule_chembl_id'], 'smiles': smi,
                'mw': p.get('full_mwt'), 'alogp': p.get('alogp'),
                'psa': p.get('psa'), 'hbd': p.get('hbd')})
    if len(out) >= TARGET_N:
        break
    if len(out) % 5000 == 0:
        print(f'{len(out)} mols, {time.time()-t0:.0f}s', flush=True)

json.dump(out, open('data/chembl_library.json', 'w'), indent=0)
print('DONE:', len(out), 'molecules in', round(time.time()-t0), 's')
