"""Phase 5: triage & ranking — vina scores + properties + CNS-appropriateness + novelty.

Inputs: docking/vina_scores.csv, library_filtered.csv properties, approved_drugs.json.
Output: results/hits_ranked.csv with composite ranking and novelty flags.
"""
import csv, json, os
from rdkit import Chem, DataStructs, RDLogger
from rdkit.Chem import AllChem, Descriptors, Crippen, Lipinski, rdMolDescriptors
from rdkit.Contrib.SA_Score import sascorer

RDLogger.DisableLog('rdApp.*')

# ---- load vina results ----
scores = {}
for r in csv.DictReader(open('docking/vina_scores.csv')):
    scores[r['ligand']] = float(r['vina_best'])

# ---- load properties from bundled-filter output ----
props = {}
for r in csv.DictReader(open('data/library_filtered.csv')):
    if r.get('error'):
        continue
    props[r['name']] = r

# ---- approved-drug fingerprints for novelty NN ----
approved = json.load(open('data/approved_drugs.json'))
fp_approved = []
for m in approved:
    mol = Chem.MolFromSmiles(m['smiles'])
    if mol is not None:
        fp_approved.append((m, AllChem.GetMorganFingerprintAsBitVect(mol, 2, 2048)))
print(f'approved-drug FP set: {len(fp_approved)}')

refs = json.load(open('data/asm_reference_inhibitors.json'))
fp_refs = []
for m in refs:
    mol = Chem.MolFromSmiles(m['smiles'])
    if mol is not None:
        fp_refs.append((m, AllChem.GetMorganFingerprintAsBitVect(mol, 2, 2048)))

def novelty_check(smi):
    mol = Chem.MolFromSmiles(smi)
    if mol is None:
        return None, None, None
    fp = AllChem.GetMorganFingerprintAsBitVect(mol, 2, 2048)
    best_drug, best_s = 0.0, None
    for m, f in fp_approved:
        t = DataStructs.TanimotoSimilarity(fp, f)
        if t > best_drug:
            best_drug, best_s = t, m
    best_ref = max((DataStructs.TanimotoSimilarity(fp, f) for _, f in fp_refs), default=0.0)
    return best_drug, best_s, best_ref

def cns_mpo_lite(mw, clogp, tpsa, hbd):
    """6-descriptor CNS MPO without pKa (pKa not computable here; noted). Each 0-1."""
    s_mw = 1.0 - abs(mw - 360) / 110
    s_logp = 1.0 - abs(clogp - 2.7) / 1.8
    s_tpsa = 1.0 - abs(tpsa - 65) / 45
    s_hbd = 1.0 if hbd <= 0 else 0.6 if hbd == 1 else 0.2
    return max(0, min(1, s_mw)) + max(0, min(1, s_logp)) + max(0, min(1, s_tpsa)) + max(0, min(1, s_hbd))

rows = []
for name, vina in scores.items():
    p = props.get(name)
    if not p:
        continue
    smi = p['smiles']
    mol = Chem.MolFromSmiles(smi)
    if mol is None:
        continue
    mw = float(p['MW']); clogp = float(p['cLogP']); tpsa = float(p['TPSA'])
    hbd = int(p['HBD']); hba = int(p['HBA']); rotb = int(p['rotb'])
    sa = float(p['SA']); qed = float(p['QED'])
    charge = int(p['charge'])
    drug_nn, drug_s, ref_nn = novelty_check(smi)
    mpo = cns_mpo_lite(mw, clogp, tpsa, hbd)  # 0-4 (4 descriptors without pKa)
    # composite: docking-dominant, penalize SA>6 and novelty overlap
    composite = (-vina) + 0.35 * (mpo - 2.4) + (-0.3 if sa > 6 else 0) + (-0.5 if (drug_nn or 0) >= 0.85 else 0)
    rows.append({
        'name': name, 'smiles': smi, 'vina_best': round(vina, 2),
        'MW': mw, 'cLogP': clogp, 'TPSA': tpsa, 'HBD': hbd, 'HBA': hba, 'rotb': rotb,
        'SA': sa, 'QED': qed, 'charge': charge, 'CNS_MPO_4d': round(mpo, 2),
        'Tanimoto_NN_approved': round(drug_nn, 3) if drug_nn is not None else '',
        'NN_approved_drug': (drug_s['name'] or drug_s['chembl_id']) if drug_nn is not None else '',
        'Tanimoto_NN_ASMref': round(ref_nn, 3) if ref_nn is not None else '',
        'novelty_flag': ('likely-known-drug-chemistry' if (drug_nn or 0) >= 0.85 else
                         ('known-ASM-chemotype' if ref_nn >= 0.6 else 'novel')),
        'composite': round(composite, 3),
    })

rows.sort(key=lambda r: r['composite'], reverse=True)
os.makedirs('results', exist_ok=True)
with open('results/hits_ranked.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)
print(f'{len(rows)} candidates ranked -> results/hits_ranked.csv')
top = rows[:10]
for r in top:
    print(f"{r['name']} vina={r['vina_best']} mpo={r['CNS_MPO_4d']} SA={r['SA']} "
          f"nnAppr={r['Tanimoto_NN_approved']} flag={r['novelty_flag']} comp={r['composite']}")
json.dump(rows[:50], open('results/top50.json', 'w'), indent=1)
