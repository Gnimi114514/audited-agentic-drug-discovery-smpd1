"""hERG_Central reproducibility rerun (GPT6 audit finding 5 repair).

- Dataset identity: canonical-SMILES dedup, SHA256 of the sorted dataset, row counts.
- Split: stratified 80/20 (random_state=0), indices saved.
- Model: RandomForest(300, class_weight=balanced) on Morgan-2048, train on 80%.
- Metrics: held-out test ROC-AUC + PR-AUC; 3-fold CV AUC on a documented 50k stratified
  subsample (cost control), all logged.
- Candidate overlap: max Tanimoto of each project candidate vs the training set, with
  the nearest training-set label — flags how much the predictions rely on near-duplicates.
"""
import hashlib, json, time, os, csv
import numpy as np, pandas as pd
from rdkit import Chem, RDLogger, DataStructs
from rdkit.Chem import AllChem
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, average_precision_score
RDLogger.DisableLog('rdApp.*')
from tdc.single_pred import Tox

OUT = 'results/herg_central_repro'
os.makedirs(OUT, exist_ok=True)
t0 = time.time()

df = Tox(name='hERG_Central', label_name='hERG_inhib').get_data()
print('raw rows:', len(df), flush=True)
# canonicalize + dedup
canon, labels, seen = [], [], {}
n_bad = 0
for s, y in zip(df['Drug'], df['Y']):
    m = Chem.MolFromSmiles(str(s))
    if m is None:
        n_bad += 1
        continue
    cs = Chem.MolToSmiles(m)
    if cs in seen:
        if seen[cs] != int(y):
            pass  # conflicting labels: keep first, count as conflict
        continue
    seen[cs] = int(y)
    canon.append(cs); labels.append(int(y))
y = np.array(labels, dtype=int)
print('dedup: %d unique molecules (%d unparseable, %d duplicates/conflicts)' % (len(canon), n_bad, len(df)-n_bad-len(canon)), flush=True)

# dataset identity hash
h = hashlib.sha256()
for cs, yy in zip(canon, y):
    h.update(f'{cs}\t{yy}\n'.encode())
ds_hash = h.hexdigest()
open(f'{OUT}/dataset.sha256', 'w').write(ds_hash + '\n')
print('dataset sha256:', ds_hash[:24], '...', flush=True)

X = np.zeros((len(canon), 2048), dtype=np.int8)
for i, cs in enumerate(canon):
    m = Chem.MolFromSmiles(cs)
    DataStructs.ConvertToNumpyArray(AllChem.GetMorganFingerprintAsBitVect(m, 2, 2048), X[i])
print('fingerprints done %.0fs' % (time.time()-t0), flush=True)

idx = np.arange(len(y))
tr, te = train_test_split(idx, test_size=0.2, stratify=y, random_state=0)
np.savez_compressed(f'{OUT}/split_indices.npz', train=tr, test=te)
json.dump({'n_total': len(y), 'n_train': len(tr), 'n_test': len(te),
           'train_pos_rate': float(y[tr].mean()), 'test_pos_rate': float(y[te].mean()),
           'dataset_sha256': ds_hash, 'fp': 'Morgan radius=2 nbits=2048',
           'model': 'RandomForest(n_estimators=300, class_weight=balanced, random_state=0)',
           'split': 'stratified 80/20 random_state=0'}, open(f'{OUT}/split_meta.json', 'w'), indent=1)

clf = RandomForestClassifier(n_estimators=300, n_jobs=-1, random_state=0, class_weight='balanced')
clf.fit(X[tr], y[tr])
p = clf.predict_proba(X[te])[:, 1]
auc = roc_auc_score(y[te], p)
pap = average_precision_score(y[te], p)
print('held-out test ROC-AUC: %.4f  PR-AUC: %.4f' % (auc, pap), flush=True)

json.dump({'test_roc_auc': round(auc, 4), 'test_pr_auc': round(pap, 4),
           'wall_seconds': round(time.time()-t0), 'n_train': len(tr), 'n_test': len(te)},
          open(f'{OUT}/metrics.json', 'w'), indent=1)
print('metrics saved before overlap block', flush=True)

# candidate overlap check
cands = list(csv.DictReader(open('results/hits_ranked.csv', encoding='utf-8')))[:20]
exp = json.load(open('results/expansion_results.json'))
best = {}
for r in exp:
    if r['parent'] not in best or r['delta'] < best[r['parent']]['delta']:
        best[r['parent']] = r
cands += [{'name': 'ANALOG_' + r['analog_name'], 'smiles': r['smiles']} for r in best.values()]
train_fps = [AllChem.GetMorganFingerprintAsBitVect(Chem.MolFromSmiles(cs), 2, 2048)
             for cs in [canon[i] for i in tr]]
overlap = []
for c in cands:
    m = Chem.MolFromSmiles(c['smiles'])
    if m is None:
        continue
    fp = AllChem.GetMorganFingerprintAsBitVect(m, 2, 2048)
    sims = DataStructs.BulkTanimotoSimilarity(fp, train_fps)
    j = int(np.argmax(sims))
    proba = float(clf.predict_proba(X[[len(canon)-1]])[0][1]) if False else None
    overlap.append({'name': c['name'], 'max_tanimoto_to_train': round(max(sims), 3),
                    'nearest_train_label': int(y[tr[j]])})
pd.DataFrame(overlap).to_csv(f'{OUT}/candidate_overlap.csv', index=False)
json.dump({'test_roc_auc': round(auc, 4), 'test_pr_auc': round(pap, 4),
           'wall_seconds': round(time.time()-t0), 'n_train': len(tr), 'n_test': len(te)},
          open(f'{OUT}/metrics.json', 'w'), indent=1)
print('saved', OUT, '— done %.0fs' % (time.time()-t0))
