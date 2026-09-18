"""Big item 3: local hERG + DILI classifiers (TDC datasets, Morgan+RandomForest, 5-fold CV)
then predict top hits + best expansion analogs. Self-trained models — CV AUC is the
honesty metric; treat outputs as weak predictions, not authoritative ADMET."""
import numpy as np, pandas as pd, json, csv
from rdkit import Chem, RDLogger, DataStructs
from rdkit.Chem import AllChem
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score, StratifiedKFold
RDLogger.DisableLog('rdApp.*')
from tdc.single_pred import Tox

def morgan(smiles, radius=2, nbits=2048):
    fps = []
    for s in smiles:
        m = Chem.MolFromSmiles(s)
        fps.append(AllChem.GetMorganFingerprintAsBitVect(m, radius, nbits) if m else None)
    return fps

def to_arr(fps):
    a = np.zeros((len(fps), 2048), dtype=np.int8)
    for i, f in enumerate(fps):
        if f is not None:
            DataStructs.ConvertToNumpyArray(f, a[i])
    return a

def build(task_name, getter):
    data = getter('FDA' if task_name == 'DILI' else 'hERG')
    # Tox('hERG') / Tox('DILI')
    df = data.get_data()
    return df['Drug'].tolist(), df['Y'].values.astype(int)

datasets = {}
for name, getter in [('hERG', lambda s: Tox(name='hERG')), ('DILI', lambda s: Tox(name='DILI'))]:
    try:
        X, y = build(name, getter)
        print(name, len(X), 'molecules, positive rate', round(y.mean(), 3))
        fps = to_arr(morgan(X))
        clf = RandomForestClassifier(n_estimators=500, n_jobs=-1, random_state=0,
                                     class_weight='balanced')
        cv = StratifiedKFold(5, shuffle=True, random_state=0)
        aucs = cross_val_score(clf, fps, y, cv=cv, scoring='roc_auc', n_jobs=-1)
        print(f'  5-fold CV ROC-AUC: {aucs.mean():.3f} ± {aucs.std():.3f}')
        clf.fit(fps, y)
        datasets[name] = clf
    except Exception as e:
        print(name, 'FAILED:', str(e)[:150])

# predict on top-20 hits + best expansion analogs
targets = list(csv.DictReader(open('results/hits_ranked.csv', encoding='utf-8')))[:20]
exp = json.load(open('results/expansion_results.json'))
best_by_parent = {}
for r in exp:
    if r['parent'] not in best_by_parent or r['delta'] < best_by_parent[r['parent']]['delta']:
        best_by_parent[r['parent']] = r
rows = [{'name': t['name'], 'smiles': t['smiles'], 'kind': 'hit'} for t in targets]
rows += [{'name': 'ANALOG_' + r['analog_name'], 'smiles': r['smiles'], 'kind': 'expansion'}
         for r in best_by_parent.values()]
fps = to_arr(morgan([r['smiles'] for r in rows]))
out = []
for name, clf in datasets.items():
    proba = clf.predict_proba(fps)[:, 1]
    for r, p in zip(rows, proba):
        out.append({'name': r['name'], 'kind': r['kind'], 'model': name,
                    'prob_positive': round(float(p), 3)})
pd.DataFrame(out).pivot_table(index=['name', 'kind'], columns='model',
                              values='prob_positive').reset_index() \
  .to_csv('results/herg_dili_predictions.csv', index=False)
print('\nsaved results/herg_dili_predictions.csv')
print(pd.read_csv('results/herg_dili_predictions.csv').to_string(index=False))
