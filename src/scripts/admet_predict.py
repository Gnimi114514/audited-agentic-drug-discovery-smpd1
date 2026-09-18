"""Round-1 continuation: DeepPurpose ADMET predictions for top hits (all PREDICTED)."""
import pandas as pd, pickle, os, csv, json
from DeepPurpose import CompoundPred as models
from DeepPurpose import utils as dpu

MODEL_DIRS = {
    'BBB_penetration': 'save_folder/pretrained_models/BBB_MolNet_Morgan_model',
    'Pgp_inhibitor': 'save_folder/pretrained_models/Pgp_inhibitor_Morgan_model',
    'CYP3A4_inhibitor': 'save_folder/pretrained_models/CYP3A4_Morgan_model',
    'CYP2D6_inhibitor': 'save_folder/pretrained_models/CYP2D6_Morgan_model',
    'Caco2_permeability': 'save_folder/pretrained_models/Caco2_Morgan_model',
    'HIA_absorbed': 'save_folder/pretrained_models/HIA_Morgan_model',
    'ClinTox_toxic': 'save_folder/pretrained_models/ClinTox_Morgan_model',
}

hits = list(csv.DictReader(open('results/hits_ranked.csv', encoding='utf-8')))[:20]
smiles = [h['smiles'] for h in hits]
names = [h['name'] for h in hits]

out = pd.DataFrame({'name': names, 'smiles': smiles})
for task, mdir in MODEL_DIRS.items():
    try:
        config = pickle.load(open(os.path.join(mdir, 'config.pkl'), 'rb'))
        enc = config['drug_encoding']
        train, val, test = dpu.data_process(smiles, None, [0.0]*len(smiles), enc,
                                            split_method='random', frac=[1.0, 0.0, 0.0],
                                            random_seed=1)
        model = models.Property_Prediction(**config)
        model.load_pretrained(os.path.join(mdir, 'model.pt'))
        res = model.predict(train, verbose=False)
        if isinstance(res, list):
            vals = res
        else:
            col = [c for c in res.columns if c in ('Score', 'Prediction', 'score')]
            vals = res[col[0]].values if col else res.iloc[:, -1].values
        out[task] = vals
        print(task, 'ok  sample:', [round(float(v), 3) for v in vals[:4]])
    except Exception as e:
        print(task, 'FAILED:', str(e)[:140])
        out[task] = None

os.makedirs('results', exist_ok=True)
out.to_csv('results/admet_predictions.csv', index=False)
print('saved results/admet_predictions.csv')
