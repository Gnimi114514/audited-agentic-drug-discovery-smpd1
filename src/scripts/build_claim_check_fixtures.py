"""Create disclosed development fixtures; never call these independent holdouts."""
import argparse
import copy
import hashlib
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    out = parser.parse_args().output
    out.mkdir(parents=True, exist_ok=False)
    (out / 'evidence.txt').write_bytes(b'preserved evidence\n')
    sha = hashlib.sha256((out / 'evidence.txt').read_bytes()).hexdigest()
    fixtures = [
        ('identity', {'target_id': 'CHEMBL2760', 'taxon_id': '9606'},
         {'target_id': 'CHEMBL2760', 'taxon_id': '9606'}, 'target_id', 'CHEMBL214'),
        ('distance', {'value': 4.58, 'unit': 'angstrom'},
         {'value': 0.458, 'unit': 'nm'}, 'value', 0.458),
        ('duration', {'ns': 6.1}, {'steps': 3050000, 'dt_fs': 2.0}, 'ns', 3.0),
        ('parameters', {'coefficients': {'epsilon': 0.02662782}, 'required_terms': ['LJ12-6']},
         {'coefficients': {'epsilon': 0.02662782}, 'force_terms': ['LJ12-6']},
         'required_terms', ['LJ12-6', 'C4']),
        ('hash', {'sha256': sha}, {'path': 'evidence.txt'}, 'sha256', '0' * 64),
        ('selection', {'definition': 'protein_backbone'},
         {'selected_atoms': [{'name': 'O', 'is_protein': True}]}, None, None),
        ('upper_bound', {'maximum': -6.0}, {'values': [-6.96, -6.34, -6.01]}, 'maximum', -7.0),
        ('residue_mapping', {'crystal_residues': ['A:318', 'A:457']},
         {'contacts': [234, 373], 'topology_to_crystal': {'234': 'A:318', '373': 'A:457'}},
         'crystal_residues', ['A:234', 'A:373']),
        ('chronology', {'phase': 'post_hoc'}, {'phase': 'post_hoc'}, 'phase', 'pre_specified'),
    ]
    cases, labels = [], {}

    def add(cid, record, status):
        cases.append({'id': cid, 'record': copy.deepcopy(record)})
        labels[cid] = status

    for kind, claim, evidence, key, wrong in fixtures:
        record = {'kind': kind, 'claim': claim, 'evidence': evidence}
        add(kind + '-consistent', record, 'PASS')
        mutant = copy.deepcopy(record)
        if kind == 'selection':
            mutant['evidence']['selected_atoms'].append({'name': 'O', 'is_protein': False})
        else:
            mutant['claim'][key] = wrong
        add(kind + '-inconsistent', mutant, 'DEFECT')
        add(kind + '-missing', {'kind': kind, 'claim': claim, 'evidence': {}}, 'UNVERIFIABLE')
    add('empty-numeric-table', {'kind': 'upper_bound', 'claim': {'maximum': -7},
                               'evidence': {'values': []}}, 'UNVERIFIABLE')
    add('legitimate-large-distance', {'kind': 'distance', 'claim': {'value': 120, 'unit': 'angstrom'},
                                     'evidence': {'value': 12, 'unit': 'nm'}}, 'PASS')
    add('consistent-pre-specified', {'kind': 'chronology', 'claim': {'phase': 'pre_specified'},
                                    'evidence': {'phase': 'pre_specified'}}, 'PASS')
    add('unmapped-residue', {'kind': 'residue_mapping', 'claim': {'crystal_residues': ['A:318']},
                             'evidence': {'contacts': [999], 'topology_to_crystal': {'234': 'A:318'}}}, 'UNVERIFIABLE')
    add('wrong-species', {'kind': 'identity', 'claim': {'target_id': 'T', 'taxon_id': '9606'},
                         'evidence': {'target_id': 'T', 'taxon_id': '10090'}}, 'DEFECT')
    for name, value in [('cases.json', cases), ('labels.json', labels)]:
        (out / name).write_text(json.dumps(value, indent=2), encoding='utf-8')
    print(f'Created {len(cases)} disclosed development fixtures in {out}')


if __name__ == '__main__':
    main()
