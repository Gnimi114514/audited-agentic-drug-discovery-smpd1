"""Fail-closed reference admission from frozen raw ChEMBL records.

This is a coordinator stage, not a complete scheduler or potency calibration.
Policy belongs to the coordinator; individual records cannot weaken it.
"""
import argparse
import hashlib
import json
from pathlib import Path
from chembl_evidence_gate import verify


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def run(config_path, output):
    config_raw = config_path.read_bytes()
    config = json.loads(config_raw)
    policy = config['policy']
    for key in ('target', 'taxon', 'accession', 'endpoint'):
        if not isinstance(policy[key], str) or not policy[key].strip():
            raise ValueError('invalid policy ' + key)
    records = config['records']
    if not isinstance(records, list) or not records:
        raise ValueError('reference set cannot be empty')
    ids = [str(r['activity_id']) for r in records]
    if len(set(ids)) != len(ids):
        raise ValueError('duplicate activity IDs')
    output.mkdir(parents=True, exist_ok=False)
    (output / 'request.json').write_bytes(config_raw)
    for name in ('admit_reference_batch.py', 'chembl_evidence_gate.py'):
        (output / name).write_bytes(Path(__file__).with_name(name).read_bytes())
    outcomes, admitted = [], []
    for i, record in enumerate(records):
        item = {'activity_id': str(record['activity_id']), 'status': 'UNVERIFIABLE'}
        try:
            saved = output / 'inputs' / str(i)
            saved.mkdir(parents=True)
            source = (config_path.parent / record['directory']).resolve()
            evidence = {}
            for kind in ('activity', 'assay', 'target'):
                raw = (source / (kind + '.json')).read_bytes()
                if sha(raw) != record['sha256'][kind]:
                    raise ValueError('input identity changed: ' + kind)
                (saved / (kind + '.json')).write_bytes(raw)
                evidence[kind] = json.loads(raw)
            expected = dict(policy, activity_id=str(record['activity_id']), molecule=record['molecule'],
                            assay_taxon=policy['taxon'], assignment_relationship='D')
            result = verify(evidence['activity'], evidence['assay'], evidence['target'], expected)
            item.update(result)
            if result['status'] == 'PASS':
                measurement = result['measurement']
                duplicate = evidence['activity'].get('potential_duplicate')
                if type(duplicate) is not int or duplicate not in (0, 1):
                    item.update(status='UNVERIFIABLE', admission_reason='missing or malformed duplicate annotation')
                elif duplicate == 1:
                    item.update(status='DEFECT', admission_reason='potential duplicate requires separate adjudication')
                elif 'data_validity_comment' not in evidence['activity']:
                    item.update(status='UNVERIFIABLE', admission_reason='missing data validity annotation')
                elif measurement['data_validity_comment'] is not None and (
                        not isinstance(measurement['data_validity_comment'], str)
                        or not measurement['data_validity_comment'].strip()):
                    item.update(status='UNVERIFIABLE', admission_reason='malformed data validity annotation')
                elif measurement['relation'] != '=' or measurement['data_validity_comment'] is not None:
                    item.update(status='DEFECT', admission_reason='not an unflagged exact endpoint')
                else:
                    admitted.append({'activity_id': record['activity_id'], 'molecule': record['molecule'],
                                     'measurement': measurement, 'input_sha256': record['sha256']})
        except (OSError, ValueError, KeyError, TypeError) as exc:
            item.update(status='UNVERIFIABLE', error=str(exc))
        outcomes.append(item)
    passed = all(o['status'] == 'PASS' for o in outcomes)
    result = {'status': 'PASS' if passed else 'BLOCKED', 'records': outcomes,
              'admitted_count': len(admitted) if passed else 0,
              'request_sha256': sha(config_raw),
              'scope': 'direct same-species reference admission only; assay comparability and calibration not established'}
    (output / 'gate.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    if passed:
        (output / 'admitted_references.json').write_text(json.dumps(admitted, indent=2), encoding='utf-8')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = run(args.request.resolve(), args.output)
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result['status'] == 'PASS' else 2)
