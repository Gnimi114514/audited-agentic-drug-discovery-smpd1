"""R3-2 repair: model separation & serialization.

hERG_Central (306,879 canonical-dedup records):
  MODEL-A (legacy protocol): RF500, trained on FULL dedup set -> the probabilities
          previously reported (7385=0.090 etc.) are attributed to THIS model and are now
          properly in-sample for candidates; per-candidate predictions re-generated and
          archived with the model.
  MODEL-B (held-out protocol): RF300, trained on the saved 80% split
          (results/herg_central_repro/split_indices.npz) -> per-test-sample predictions
          saved so ROC-AUC 0.9091 is independently recomputable; candidate predictions
          generated fresh from MODEL-B.
All artifacts saved under results/herg_central_repro/models/.
"""
import hashlib, json, os, time, csv
import numpy as np, pandas as pd
from rdkit import Chem, RDLogger, DataStructs
from rdkit.Chem import AllChem
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score, average_precision_score
RDLogger.DisableLog('rdApp.*')
from tdc.single_pred import Tox

OUT = 'results/herg_central_repro/models'
os.makedirs(OUT, exist_ok=True)
t0 = time.time()

df = Tox(name='hERG_Central', label_name='hERG_inhib').get_data()
canon, labels, seen = [], [], {}
for s, y in zip(df['Drug'], df['Y']):
    m = Chem.MolFromSmiles(str(s))
    if m is None:
        continue
    cs = Chem.MolToSmiles(m)
    if cs in seen:
        continue
    seen[cs] = int(y)
    canon.append(cs); labels.append(int(y))
y = np.array(labels, dtype=int)
N = len(y)
print('dedup N =', N, flush=True)

X = np.zeros((N, 2048), dtype=np.int8)
for i, cs in enumerate(canon):
    DataStructs.ConvertToNumpyArray(AllChem.GetMorganFingerprintAsBitVect(
        Chem.MolFromSmiles(cs), 2, 2048), X[i])
print('fps done %.0fs' % (time.time()-t0), flush=True)

sp = np.load('results/herg_central_repro/split_indices.npz')
tr, te = sp['train'], sp['test']

# ---- MODEL-B: RF300 on saved split; save per-test-sample predictions ----
mb = RandomForestClassifier(n_estimators=300, n_jobs=-1, random_state=0, class_weight='balanced')
mb.fit(X[tr], y[tr])
pb = mb.predict_proba(X[te])[:, 1]
auc_b = roc_auc_score(y[te], pb); ap_b = average_precision_score(y[te], pb)
np.savez_compressed(f'{OUT}/modelB_test_predictions.npz', test_indices=te,
                    y_true=y[te], y_prob=pb)
print('MODEL-B (RF300, split): held-out ROC-AUC %.4f, AP %.4f' % (auc_b, ap_b), flush=True)

# ---- MODEL-A: RF500 full-data legacy protocol; save candidate predictions ----
ma = RandomForestClassifier(n_estimators=500, n_jobs=-1, random_state=0, class_weight='balanced')
ma.fit(X, y)
print('MODEL-A (RF500, full-data) trained %.0fs' % (time.time()-t0), flush=True)

def cand_fps():
    cands = list(csv.DictReader(open('results/hits_ranked.csv', encoding='utf-8')))[:20]
    exp = json.load(open('results/expansion_results.json'))
    best = {}
    for r in exp:
        if r['parent'] not in best or r['delta'] < best[r['parent']]['delta']:
            best[r['parent']] = r
    rows = [{'name': t['name'], 'smiles': t['smiles']} for t in cands]
    rows += [{'name': 'ANALOG_' + r['analog_name'], 'smiles': r['smiles']} for r in best.values()]
    fps, keep = [], []
    for r in rows:
        m = Chem.MolFromSmiles(r['smiles'])
        if m is None:
            continue
        fps.append(AllChem.GetMorganFingerprintAsBitVect(m, 2, 2048))
        keep.append(r['name'])
    return keep, fps

names, fps = cand_fps()
pa = ma.predict_proba(np.array(fps))[:, 1]
pb_c = mb.predict_proba(np.array(fps))[:, 1]
out = pd.DataFrame({'name': names,
                    'MODEL_A_RF500_fulldata_prob': np.round(pa, 4),
                    'MODEL_B_RF300_split_prob': np.round(pb_c, 4)})
out.to_csv(f'{OUT}/candidate_predictions_by_model.csv', index=False)
print(out.to_string(index=False), flush=True)

# ---- environment provenance ----
import sklearn, sys
prov = {'python': sys.version.split()[0], 'sklearn': sklearn.__version__,
        'n_total_dedup': int(N), 'n_train_B': int(len(tr)), 'n_test_B': int(len(te)),
        'MODEL_B_test_roc_auc': round(float(auc_b), 4),
        'MODEL_B_test_avg_precision': round(float(ap_b), 4),
        'metric_note': 'AP computed with sklearn average_precision_score',
        'model_A': 'RF n_estimators=500, full dedup data (legacy protocol; in-sample for candidates)',
        'model_B': 'RF n_estimators=300, saved 80% split (held-out evaluation protocol)'}
json.dump(prov, open(f'{OUT}/model_provenance.json', 'w'), indent=1)
print('saved', OUT, '— total %.0fs' % (time.time()-t0))
