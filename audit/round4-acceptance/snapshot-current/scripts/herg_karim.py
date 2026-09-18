"""hERG model v2: train on the larger hERG_Central dataset (8.3k) with Morgan+RF.
Compare CV AUC against the 655-molecule model, then re-predict top candidates."""
import numpy as np, pandas as pd, json, csv
from rdkit import Chem, RDLogger, DataStructs
from rdkit.Chem import AllChem
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score, StratifiedKFold
RDLogger.DisableLog('rdApp.*')
from tdc.single_pred import Tox

def morgan_arr(smiles):
    X = np.zeros((len(smiles), 2048), dtype=np.int8)
    for i, s in enumerate(smiles):
        m = Chem.MolFromSmiles(s)
        if m is not None:
            DataStructs.ConvertToNumpyArray(AllChem.GetMorganFingerprintAsBitVect(m, 2, 2048), X[i])
    return X

data = Tox(name='hERG_Central', label_name='hERG_inhib')
df = data.get_data()
print('hERG_Central:', len(df), 'molecules, positive rate', round(df['Y'].mean(), 3))
X = morgan_arr(df['Drug'].tolist())
y = df['Y'].values.astype(int)
clf = RandomForestClassifier(n_estimators=500, n_jobs=-1, random_state=0, class_weight='balanced')
cv = StratifiedKFold(5, shuffle=True, random_state=0)
aucs = cross_val_score(clf, X, y, cv=cv, scoring='roc_auc', n_jobs=-1)
print('5-fold CV ROC-AUC: %.3f ± %.3f' % (aucs.mean(), aucs.std()))
clf.fit(X, y)

targets = list(csv.DictReader(open('results/hits_ranked.csv', encoding='utf-8')))[:20]
rows = [{'name': t['name'], 'smiles': t['smiles'], 'kind': 'hit'} for t in targets]
exp = json.load(open('results/expansion_results.json'))
best = {}
for r in exp:
    if r['parent'] not in best or r['delta'] < best[r['parent']]['delta']:
        best[r['parent']] = r
rows += [{'name': 'ANALOG_' + r['analog_name'], 'smiles': r['smiles'], 'kind': 'expansion'}
         for r in best.values()]
Xp = morgan_arr([r['smiles'] for r in rows])
proba = clf.predict_proba(Xp)[:, 1]
out = pd.DataFrame({'name': [r['name'] for r in rows], 'kind': [r['kind'] for r in rows],
                    'hERG_Central_prob': np.round(proba, 3)})
out.to_csv('results/herg_karim_predictions.csv', index=False)
print(out.sort_values('hERG_Central_prob').to_string(index=False))
