"""Controlled reference preparation: admission -> molecular parsing -> grouped CSV.

No docking score calibration is inferred. Outputs retain assay-specific observations.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
from rdkit import Chem, rdBase
from admit_reference_batch import run


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / 'reference_pipeline.py').write_bytes(Path(__file__).read_bytes())
    gate = run(args.request.resolve(), args.output / 'gate')
    summary = {'stage': 'reference_preparation', 'rdkit_version': rdBase.rdkitVersion,
               'status': 'BLOCKED', 'scope': 'assay-grouped enzyme-inhibition references; no binding or scoring calibration claim'}
    if gate['status'] != 'PASS':
        summary['reason'] = 'reference admission failed'
    else:
        request = json.loads((args.output / 'gate/request.json').read_bytes())
        rows, identities, problems = [], {}, []
        for index, record in enumerate(request['records']):
            source = args.output / 'gate/inputs' / str(index) / 'activity.json'
            activity = json.loads(source.read_bytes())
            smiles = activity.get('canonical_smiles')
            mol = Chem.MolFromSmiles(smiles) if isinstance(smiles, str) and smiles.strip() else None
            if mol is None or mol.GetNumAtoms() == 0:
                problems.append({'activity_id': record['activity_id'], 'reason': 'unparseable molecular structure'})
                continue
            canonical = Chem.MolToSmiles(mol, isomericSmiles=True)
            mid = record['molecule']
            if mid in identities and identities[mid] != canonical:
                problems.append({'molecule': mid, 'reason': 'conflicting structures for molecule ID'})
            identities[mid] = canonical
            measurement = gate['records'][index]['measurement']
            rows.append({'activity_id': record['activity_id'], 'molecule_id': mid,
                         'assay_id': activity['assay_chembl_id'], 'smiles': canonical,
                         'IC50_nM': measurement['value_nM'], 'relation': measurement['relation'],
                         'document_id': measurement['document'],
                         'source_activity_sha256': hashlib.sha256(source.read_bytes()).hexdigest()})
        if problems:
            summary['problems'] = problems
        else:
            grouped = args.output / 'assay_controls'
            grouped.mkdir()
            for assay_id in sorted({r['assay_id'] for r in rows}):
                subset = [r for r in rows if r['assay_id'] == assay_id]
                with (grouped / (assay_id + '.csv')).open('x', newline='', encoding='utf-8') as handle:
                    writer = csv.DictWriter(handle, fieldnames=list(subset[0]))
                    writer.writeheader()
                    writer.writerows(subset)
            summary.update(status='PASS', observations=len(rows), distinct_molecule_ids=len(identities),
                           assay_groups=sorted({r['assay_id'] for r in rows}),
                           limitations=['No salt stripping, tautomer standardization or stereochemistry invention',
                                        'Cross-assay observations not pooled; duplicate flag exclusion is not complete study deduplication',
                                        'Assay conditions and full primary reports require review before scoring calibration'])
    (args.output / 'result.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(json.dumps(summary, indent=2))
    return 0 if summary['status'] == 'PASS' else 2


if __name__ == '__main__':
    raise SystemExit(main())
