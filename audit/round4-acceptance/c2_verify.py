"""Independent round-four C2: only reads evidence, writes audit-local result."""
from pathlib import Path
import csv, json
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
p = ROOT / 'results/herg_central_repro/models'
z = np.load(p / 'modelB_test_predictions.npz', allow_pickle=False)
y, score, ix = z['y_true'], z['y_prob'], z['test_indices']
# Mann-Whitney AUC with average ranks for tied scores; no producer code imported.
order = np.argsort(score, kind='stable')
s = score[order]
ranks = np.empty(len(s), dtype=float)
start = 0
while start < len(s):
    end = start + 1
    while end < len(s) and s[end] == s[start]:
        end += 1
    ranks[order[start:end]] = (start + 1 + end) / 2
    start = end
n1 = int(np.sum(y == 1)); n0 = int(np.sum(y == 0))
auc = (float(ranks[y == 1].sum()) - n1*(n1+1)/2)/(n1*n0)
split = np.load(ROOT / 'results/herg_central_repro/split_indices.npz')
with (p / 'candidate_predictions_by_model.csv').open() as f:
    reader = csv.DictReader(f); columns = reader.fieldnames; rows = list(reader)
with (ROOT / 'results/herg_karim_predictions.csv').open() as f:
    old = {r['name']: float(r['hERG_Central_prob']) for r in csv.DictReader(f)}
comparison = [{'name': r['name'], 'legacy': old[r['name']],
               'MODEL_A': float(r['MODEL_A_RF500_fulldata_prob']),
               'MODEL_B': float(r['MODEL_B_RF300_split_prob']),
               'legacy_reproduced_at_legacy_precision': abs(float(r['MODEL_A_RF500_fulldata_prob']) - old[r['name']]) <= 0.0005000001}
              for r in rows]
result = {'check': 'C2', 'verdict': 'FAIL',
          'auc_independent_rank_method': auc, 'auc_round4': round(auc,4),
          'npz_keys': list(z.files), 'n_test': len(y), 'n_positive': n1, 'n_negative': n0,
          'finite_scores': bool(np.isfinite(score).all()), 'probability_range': [float(score.min()), float(score.max())],
          'test_indices_equal_saved_split': bool(np.array_equal(ix,split['test'])),
          'test_train_intersection_count': len(np.intersect1d(ix, split['train'])),
          'csv_columns': columns, 'n_candidate_rows': len(rows),
          'legacy_matches_at_legacy_precision': sum(r['legacy_reproduced_at_legacy_precision'] for r in comparison),
          'candidate_comparison': comparison,
          'serialized_estimator_files_under_results': [str(x.relative_to(ROOT)) for x in (ROOT/'results').rglob('*') if x.suffix.lower() in ('.joblib','.pkl','.pickle')],
          'findings': ['AUC and separate model columns pass; legacy reproduction fails for most candidates.',
                       'Producer separation script serializes prediction arrays, not fitted models. MODEL-A training uses deduplication/canonicalization absent from legacy script, so it is not the identical legacy model.']}
out = Path(__file__).with_name('c2_evidence.json')
out.write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps(result, indent=2))
