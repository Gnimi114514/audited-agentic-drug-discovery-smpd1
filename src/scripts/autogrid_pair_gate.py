"""Fail-closed, bounded AutoGrid nbp_r_eps structural/log gate; NOT physics/G2 validation.

Caller JSON: {"required_pairs": [[ligand, receptor], ...],
"unused_pairs": [{"ligand": "SA", "receptor": "ZN", "reason": "..."}]}.
Required pairs are an explicit exact contract, including no unexpected consumed pairs.
Only the observed AutoGrid matched-index log dialect is supported. Logs are not
authenticated execution evidence; bind them to an independently verified runner.
"""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import re


class GateError(ValueError):
    pass


def need(condition, message):
    if not condition:
        raise GateError(message)


def token(value):
    need(isinstance(value, str) and re.fullmatch(r"[A-Za-z][A-Za-z0-9]?", value),
         f"unsupported atom type {value!r}; require one/two ASCII alphanumerics")
    return value


def rows(text):
    return [s.split() for line in text.splitlines() if (s := line.split('#', 1)[0].strip())]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def preflight(gpf, contract):
    gpf = Path(gpf).resolve()
    snapshots = {gpf: gpf.read_bytes()}
    raw = snapshots[gpf].decode('ascii')
    records = rows(raw)
    allowed = {'npts','parameter_file','gridfld','spacing','receptor_types','ligand_types',
               'receptor','gridcenter','smooth','map','elecmap','dsolvmap','dielectric','nbp_r_eps'}
    need(records, 'empty GPF')
    grouped = {}
    for i, row in enumerate(records):
        need(row[0] in allowed, f'unsupported GPF directive {row[0]}')
        grouped.setdefault(row[0], []).append((i, row[1:]))
    for key, values in grouped.items():
        need(key in {'map','nbp_r_eps'} or len(values) == 1, f'duplicate directive {key}')
    def single(key):
        need(key in grouped and len(grouped[key]) == 1, f'missing/duplicate {key}')
        return grouped[key][0][1]
    def file_arg(key):
        value = single(key)
        need(len(value) == 1, f'{key} needs one path')
        return (gpf.parent / value[0]).resolve()
    param = file_arg('parameter_file')
    receptor = file_arg('receptor')
    snapshots.update({p:p.read_bytes() for p in (param,receptor)})
    lig = [token(t) for t in single('ligand_types')]
    rec = [token(t) for t in single('receptor_types')]
    need(lig and rec and len(set(lig)) == len(lig) and len(set(rec)) == len(rec),
         'empty/duplicate ligand or receptor type')
    params = set()
    coefficients = {}
    for row in rows(snapshots[param].decode('ascii')):
        if row[0] == 'atom_par':
            need(len(row) == 12, 'malformed atom_par')
            t = token(row[1])
            need(t not in params, f'duplicate atom_par {t}')
            need(all(math.isfinite(float(v)) for v in row[2:]), 'nonfinite atom_par')
            params.add(t)
        elif row[0].startswith('FE_coeff_'):
            need(len(row) == 2 and row[0] not in coefficients, 'malformed/duplicate coefficient')
            value = float(row[1])
            need(math.isfinite(value) and value >= 0, 'invalid coefficient')
            coefficients[row[0]] = value
        else:
            raise GateError(f'unsupported parameter directive {row[0]}')
    need('FE_coeff_vdW' in coefficients, 'missing FE_coeff_vdW')
    pos = lambda key: grouped[key][0][0]
    need(pos('parameter_file') < min(pos('ligand_types'),pos('receptor_types'))
         and pos('receptor_types') < pos('receptor'), 'unsupported initialization order')
    need(all(i > pos('ligand_types') for i,_ in grouped.get('map',[])), 'map before ligand types')
    need(set(lig + rec) <= params, 'declared types missing exact parameter entries')
    actual = Counter()
    for line in snapshots[receptor].decode('ascii').splitlines():
        if line[:6].strip() in {'ATOM','HETATM'}:
            need(len(line) >= 78, 'short receptor atom record')
            actual[token(line[77:].strip())] += 1
    need(actual and set(actual) == set(rec), 'receptor type set differs from declared types')
    need(isinstance(contract, dict) and set(contract) == {'required_pairs','unused_pairs'},
         'contract must explicitly contain required_pairs and unused_pairs only')
    required = []
    for pair in contract['required_pairs']:
        need(isinstance(pair, list) and len(pair) == 2, 'invalid required pair')
        a, b = map(token, pair)
        need(a in lig and b in rec, f'required pair unavailable {pair}')
        required.append((a,b))
    need(required and len(set(required)) == len(required), 'empty/duplicate required pairs')
    exemptions = set()
    for item in contract['unused_pairs']:
        need(isinstance(item, dict) and set(item) == {'ligand','receptor','reason'}, 'invalid exemption')
        a,b = token(item['ligand']), token(item['receptor'])
        need(isinstance(item['reason'],str) and item['reason'].strip(), 'exemption needs reason')
        need(a in params and b in params and a not in lig and b in rec,
             'exemption cannot waive typo or active/missing receptor pair')
        need((a,b) not in exemptions, 'duplicate exemption')
        exemptions.add((a,b))
    expected = []
    used_exemptions = set()
    seen = set()
    pair_blocks = {}
    for index, args in grouped.get('nbp_r_eps', []):
        need(len(args) == 6, 'nbp_r_eps requires six arguments')
        radius, epsilon = map(float, args[:2])
        need(math.isfinite(radius) and radius > 0 and math.isfinite(epsilon) and epsilon >= 0,
             'invalid radius/epsilon')
        need(all(re.fullmatch(r'[0-9]+', v) for v in args[2:4]), 'invalid exponents')
        n,m = map(int,args[2:4])
        need(0 < m < n <= 100, 'unsupported exponents; require 0 < m < n <= 100')
        try:
            weighted = epsilon * coefficients['FE_coeff_vdW']
            tmp = weighted / (n-m)
            cA,cB = tmp * radius**n * m, tmp * radius**m * n
            need(all(math.isfinite(v) for v in (weighted,cA,cB)), 'nonfinite calculated coefficients')
        except OverflowError:
            raise GateError('overflow calculated coefficients')
        a,b = map(token,args[4:])
        need(a in params and b in params, 'pair lacks exact parameter type')
        identity = tuple(sorted((a,b)))
        need(identity not in seen, 'duplicate/conflicting pair directive')
        seen.add(identity)
        need(index > max(grouped[k][0][0] for k in
                         ('parameter_file','ligand_types','receptor_types','receptor')),
             'pair precedes required initialization')
        matches = [(x,y,lig.index(x),rec.index(y)) for x,y in ((a,b),(b,a)) if x in lig and y in rec]
        need(a != b, 'same-type override unsupported (double assignment ambiguity)')
        if matches:
            expected.extend(matches)
        else:
            choices = {(a,b),(b,a)} & exemptions
            need(len(choices) == 1, f'unconsumed pair without valid exemption {a}-{b}')
            used_exemptions.update(choices)
        pair_blocks[index] = matches
    need(used_exemptions == exemptions, 'unused exemption not bound to an ignored directive')
    need({(a,b) for a,b,_,_ in expected} == set(required),
         'consumed pairs differ from caller required_pairs contract')
    maps = grouped.get('map',[])
    need(len(maps) == len(lig) and all(len(v) == 1 for _,v in maps), 'map cardinality mismatch')
    need(len({v[0] for _,v in maps}) == len(maps), 'duplicate map output')
    hashes = {str(p):hashlib.sha256(data).hexdigest() for p,data in snapshots.items()}
    need(all(digest(p) == h for p,h in hashes.items()), 'inputs changed during preflight')
    return {'gpf': str(gpf), 'input_sha256': hashes,
            'required_pairs': required, 'expected_matches': expected, 'exemptions': sorted(exemptions),
            'records': records, 'pair_blocks': pair_blocks, 'receptor_counts': dict(actual)}


MATCH = re.compile(r'\s*nbp_r_eps or nbp_coeffs: map_index\((\w+)\)=\s*(\d+)\s+rec_index\((\w+)\)=\s*(\d+)\s*')


def postflight(pre, log):
    need(all(digest(p) == h for p,h in pre['input_sha256'].items()), 'inputs changed after preflight')
    lines = Path(log).read_text(encoding='ascii').splitlines()
    echoes, blocks = [], {}
    current = None
    completions = []
    matched_positions = []
    for line_number,line in enumerate(lines):
        if line.startswith('GPF> '):
            r = rows(line[5:])
            if r:
                need(len(r) == 1, 'invalid GPF echo')
                current = len(echoes)
                echoes.append(r[0])
        if 'map_index(' in line or 'rec_index(' in line:
            match = MATCH.fullmatch(line)
            need(match is not None and current is not None, 'malformed/orphan matched-index record')
            a,i,b,j = match.groups()
            matched_positions.append(line_number)
            blocks.setdefault(current,[]).append((a,b,int(i),int(j)))
        if line.endswith(': Successful Completion.'):
            completions.append(line_number)
    need(echoes == pre['records'], 'log GPF echo does not match exact ordered input tokens')
    need(len(completions) == 1 and completions[0] > max(
        i for i,line in enumerate(lines) if line.startswith('GPF> ')), 'missing/early/duplicate completion')
    need(all(i < completions[0] for i in matched_positions), 'matched record after completion')
    need(not any(re.search(r'\b(ERROR|FATAL)\b', line, re.I) for line in lines), 'error in log')
    expected = {i:v for i,v in pre['pair_blocks'].items() if v}
    need(blocks == expected, 'matched records/indices do not match per-directive expected consumption')
    return {'log':str(Path(log).resolve()), 'log_sha256':digest(log), 'matched_records':sum(map(len,blocks.values()))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--gpf',required=True)
    parser.add_argument('--contract',required=True)
    parser.add_argument('--log')
    args = parser.parse_args()
    try:
        result = preflight(args.gpf,json.loads(Path(args.contract).read_text(encoding='utf-8')))
        if args.log:
            result['postflight'] = postflight(result,args.log)
        result.update(status='PASS', scope='structural/log consumption only; not authenticated execution, physical validation or G2',
                      contract_sha256=digest(args.contract))
        print(json.dumps(result,indent=2))
        return 0
    except (GateError,ValueError,TypeError,KeyError,OSError) as exc:
        print(json.dumps({'status':'REJECT','reason':str(exc)}))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
