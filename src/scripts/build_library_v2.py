"""Phase 4 v2: ChEMBL library fetch via direct REST with checkpointing and backoff."""
import requests, json, time, os

OUT_JSONL = 'data/chembl_library.jsonl'
TARGET_N = 20000
BASE = 'https://www.ebi.ac.uk/chembl/api/data/molecule.json'
PARAMS = {
    'molecule_properties__full_mwt__gte': 250,
    'molecule_properties__full_mwt__lte': 450,
    'molecule_properties__psa__lte': 90,
    'molecule_properties__hbd__lte': 2,
    'molecule_properties__alogp__gte': 1.5,
    'molecule_properties__alogp__lte': 4.5,
    'only': 'molecule_chembl_id,molecule_structures,molecule_properties',
    'limit': 1000,
    'format': 'json',
}

# resume support: count existing lines
done = 0
if os.path.exists(OUT_JSONL):
    with open(OUT_JSONL) as f:
        done = sum(1 for _ in f)
print('resuming at', done)

seen = set()
if os.path.exists('data/chembl_seen.json'):
    seen = set(json.load(open('data/chembl_seen.json')))

t0 = time.time()
with open(OUT_JSONL, 'a', encoding='utf-8') as fh:
    while done < TARGET_N:
        ok = False
        for attempt in range(6):
            try:
                p = dict(PARAMS, offset=done)
                r = requests.get(BASE, params=p, timeout=90,
                                 headers={'Accept': 'application/json'})
                if r.status_code == 200:
                    d = r.json()
                    mols = d.get('molecules', [])
                    if not mols:
                        done = TARGET_N  # exhausted
                        ok = True
                        break
                    n_new = 0
                    for m in mols:
                        smi = (m.get('molecule_structures') or {}).get('canonical_smiles')
                        if not smi or smi in seen or '.' in smi:
                            continue
                        seen.add(smi)
                        pr = m.get('molecule_properties') or {}
                        fh.write(json.dumps({'chembl_id': m['molecule_chembl_id'], 'smiles': smi,
                                             'mw': pr.get('full_mwt'), 'alogp': pr.get('alogp'),
                                             'psa': pr.get('psa'), 'hbd': pr.get('hbd')}) + '\n')
                        n_new += 1
                    done += n_new
                    fh.flush()
                    ok = True
                    break
                else:
                    wait = 5 * 2 ** attempt
                    print(f'HTTP {r.status_code} at offset {done}, retry in {wait}s', flush=True)
                    time.sleep(wait)
            except Exception as e:
                wait = 5 * 2 ** attempt
                print(f'exc at offset {done}: {str(e)[:60]} retry in {wait}s', flush=True)
                time.sleep(wait)
        if not ok:
            print('giving up this offset after retries; stopping with data so far')
            break
        print(f'{done} mols, {time.time()-t0:.0f}s', flush=True)
        if done % 5000 == 0:
            json.dump(sorted(seen), open('data/chembl_seen.json', 'w'))
            print('checkpoint saved', flush=True)

json.dump(sorted(seen), open('data/chembl_seen.json', 'w'))
print('DONE', done, 'mols in', round(time.time()-t0), 's')
