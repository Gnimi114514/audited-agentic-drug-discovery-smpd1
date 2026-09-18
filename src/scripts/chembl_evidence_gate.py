"""Fetch or replay ChEMBL activity/assay/target records with exact identity checks.

PASS means the record supports the specified identity and numeric endpoint, not that
the compound is a validated therapeutic lead. No name-search first-hit fallback.
"""
import argparse
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
import re
import urllib.request


def required(record, key):
    value = record[key]
    if not isinstance(value, (str, int, float)) or isinstance(value, bool) or not str(value).strip():
        raise ValueError('missing ' + key)
    return value


def verify(activity, assay, target, expected):
    findings = []
    normalized = None
    try:
        def same(label, observed, wanted):
            if str(observed) != str(wanted):
                findings.append({'field': label, 'observed': observed, 'expected': wanted})

        same('activity_id', required(activity, 'activity_id'), expected['activity_id'])
        same('molecule', required(activity, 'molecule_chembl_id'), expected['molecule'])
        same('activity_target', required(activity, 'target_chembl_id'), expected['target'])
        same('activity_taxon', required(activity, 'target_tax_id'), expected['taxon'])
        same('assay_link', required(activity, 'assay_chembl_id'), required(assay, 'assay_chembl_id'))
        same('assay_target', required(assay, 'target_chembl_id'), activity['target_chembl_id'])
        same('target_link', required(target, 'target_chembl_id'), activity['target_chembl_id'])
        same('target_taxon', required(target, 'tax_id'), expected['taxon'])
        same('assay_taxon', required(assay, 'assay_tax_id'), expected['assay_taxon'])
        same('assignment_relationship', required(assay, 'relationship_type'), expected['assignment_relationship'])
        expected_confidence = {'D': 9, 'H': 8}[expected['assignment_relationship']]
        same('assignment_confidence', required(assay, 'confidence_score'), expected_confidence)
        same('document_link', required(activity, 'document_chembl_id'), required(assay, 'document_chembl_id'))
        same('target_type', required(target, 'target_type'), 'SINGLE PROTEIN')
        components = target['target_components']
        if not isinstance(components, list) or not components:
            raise ValueError('missing target components')
        accessions = [required(c, 'accession') for c in components]
        if accessions != [expected['accession']]:
            findings.append({'field': 'target_accessions', 'observed': accessions,
                             'expected': [expected['accession']]})
        same('endpoint', required(activity, 'standard_type'), expected['endpoint'])
        relation = required(activity, 'standard_relation')
        if relation not in ('=', '<', '>', '<=', '>=', '~'):
            raise ValueError('unsupported activity relationship')
        scales = {'M': Decimal('1000000000'), 'mM': Decimal('1000000'),
                  'uM': Decimal('1000'), 'µM': Decimal('1000'), 'nM': Decimal(1),
                  'pM': Decimal('0.001')}
        unit = required(activity, 'standard_units')
        if unit not in scales:
            raise ValueError('unsupported concentration unit')
        value = Decimal(str(required(activity, 'standard_value')))
        if not value.is_finite() or value <= 0:
            raise ValueError('nonpositive or nonfinite concentration')
        normalized = {'value_nM': str(value * scales[unit]), 'relation': relation,
                      'endpoint': activity['standard_type'],
                      'document': activity.get('document_chembl_id'),
                      'assay_description': assay.get('description'),
                      'assay_taxon': assay['assay_tax_id'],
                      'assay_organism': assay.get('assay_organism'),
                      'target_taxon': target['tax_id'],
                      'assignment_relationship': assay['relationship_type'],
                      'assay_confidence_score': assay.get('confidence_score'),
                      'data_validity_comment': activity.get('data_validity_comment')}
        return {'status': 'DEFECT' if findings else 'PASS', 'findings': findings,
                'measurement': normalized,
                'scope': 'database record identity and numeric extraction; no potency calibration or biological validation'}
    except (KeyError, ValueError, TypeError, InvalidOperation) as exc:
        return {'status': 'UNVERIFIABLE', 'findings': findings, 'error': str(exc),
                'measurement': normalized}


def fetch(kind, identifier, output, log):
    if not re.fullmatch(r'(?:CHEMBL\d+|\d+)', str(identifier)):
        raise ValueError('invalid database identifier')
    url = f'https://www.ebi.ac.uk/chembl/api/data/{kind}/{identifier}.json'
    request = urllib.request.Request(url, headers={'Accept': 'application/json',
                                                  'User-Agent': 'audited-drug-discovery/0.1'})
    with urllib.request.urlopen(request, timeout=25) as response:
        raw = response.read()
        status = response.status
    path = output / (kind + '.json')
    path.write_bytes(raw)
    log.append({'url': url, 'retrieved_utc': datetime.now(timezone.utc).isoformat(),
                'http_status': status, 'file': path.name,
                'sha256': hashlib.sha256(raw).hexdigest()})
    return json.loads(raw)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--activity-id', required=True)
    parser.add_argument('--molecule', required=True)
    parser.add_argument('--target', required=True)
    parser.add_argument('--taxon', required=True)
    parser.add_argument('--accession', required=True)
    parser.add_argument('--endpoint', default='IC50')
    parser.add_argument('--assay-taxon', help='Expected experimental organism; defaults to target taxon')
    parser.add_argument('--assignment-relationship', choices=('D', 'H'), default='D',
                        help='D requires direct target assignment; H explicitly allows homologous assignment')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--replay', type=Path, help='Directory containing raw activity/assay/target JSON')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    expected = {k: getattr(args, k) for k in ('activity_id', 'molecule', 'target', 'taxon', 'accession', 'endpoint')}
    expected['assay_taxon'] = args.assay_taxon or args.taxon
    expected['assignment_relationship'] = args.assignment_relationship
    (args.output / 'request.json').write_text(json.dumps(expected, indent=2), encoding='utf-8')
    # Preserve the executed implementation; replay changes are independently versioned.
    (args.output / 'checker_source.py').write_bytes(Path(__file__).read_bytes())
    log = []
    try:
        if args.replay:
            records = []
            for kind in ('activity', 'assay', 'target'):
                source = args.replay / (kind + '.json')
                raw = source.read_bytes()
                (args.output / source.name).write_bytes(raw)
                log.append({'source': str(source.resolve()), 'file': source.name,
                            'sha256': hashlib.sha256(raw).hexdigest(), 'mode': 'offline_replay'})
                records.append(json.loads(raw))
            activity, assay, target = records
        else:
            activity = fetch('activity', args.activity_id, args.output, log)
            assay = fetch('assay', required(activity, 'assay_chembl_id'), args.output, log)
            target = fetch('target', required(activity, 'target_chembl_id'), args.output, log)
        result = verify(activity, assay, target, expected)
    except Exception as exc:
        result = {'status': 'UNVERIFIABLE', 'error': f'{type(exc).__name__}: {exc}'}
    (args.output / 'retrieval.json').write_text(json.dumps(log, indent=2), encoding='utf-8')
    (args.output / 'result.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))
    return {'PASS': 0, 'DEFECT': 2, 'UNVERIFIABLE': 3}[result['status']]


if __name__ == '__main__':
    raise SystemExit(main())
