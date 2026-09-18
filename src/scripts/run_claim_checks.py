"""Run unlabeled cases first; score an explicitly separate label file afterwards."""
import argparse
import hashlib
import json
from pathlib import Path
from audit_claim_checks import evaluate


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cases', type=Path, required=True)
    parser.add_argument('--labels', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    cases = json.loads(args.cases.read_text(encoding='utf-8'))
    if not cases or len({c['id'] for c in cases}) != len(cases):
        raise ValueError('cases must be nonempty with unique IDs')
    if any(set(c) != {'id', 'record'} for c in cases):
        raise ValueError('case envelope must contain only id and record')
    args.output.mkdir(parents=True, exist_ok=False)
    predictions = {c['id']: evaluate(c['record'], args.cases.parent) for c in cases}
    pred_path = args.output / 'predictions.json'
    pred_path.write_text(json.dumps(predictions, indent=2), encoding='utf-8')
    # The detector has completed before the evaluator reads any labels.
    labels = json.loads(args.labels.read_text(encoding='utf-8'))
    if set(labels) != set(predictions) or any(v not in ('PASS', 'DEFECT', 'UNVERIFIABLE') for v in labels.values()):
        raise ValueError('labels must cover cases exactly with known statuses')
    matrix = {s: {p: 0 for p in ('PASS', 'DEFECT', 'UNVERIFIABLE')}
              for s in ('PASS', 'DEFECT', 'UNVERIFIABLE')}
    for cid, expected in labels.items():
        matrix[expected][predictions[cid]['status']] += 1
    summary = {'scope': 'development regression; not blinded, held-out, or agent-performance evidence',
               'cases': len(cases), 'confusion_matrix_expected_by_predicted': matrix,
               'mismatches': [i for i in labels if labels[i] != predictions[i]['status']],
               'sha256': {'cases': digest(args.cases), 'labels': digest(args.labels),
                          'predictions': digest(pred_path), 'runner': digest(Path(__file__)),
                          'checker': digest(Path(__file__).with_name('audit_claim_checks.py'))}}
    (args.output / 'summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(json.dumps(summary, indent=2))
    return bool(summary['mismatches'])


if __name__ == '__main__':
    raise SystemExit(main())
