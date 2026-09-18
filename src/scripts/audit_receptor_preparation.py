"""Read-only inventory of crystal atoms retained in the prepared docking receptor."""
import argparse
import hashlib
import json
import math
from pathlib import Path


def read(path, qt=False):
    rows = []
    for line in path.read_text().splitlines():
        if line.startswith('ENDMDL'):
            break
        if not line.startswith(('ATOM  ', 'HETATM')):
            continue
        element = line.split()[-1] if qt else line[76:78].strip()
        if element in ('H', 'HD', 'HS'):
            continue
        xyz = [float(line[i:i+8]) for i in (30, 38, 46)]
        if not all(math.isfinite(v) for v in xyz):
            raise ValueError('nonfinite coordinates')
        rows.append({'record': line[:6].strip(), 'chain': line[21], 'residue': line[17:20].strip(),
                     'number': line[22:26].strip(), 'insertion': line[26], 'altloc': line[16],
                     'name': line[12:16].strip(), 'xyz': xyz, 'element_or_type': element})
    if not rows:
        raise ValueError('no heavy atoms')
    return rows


def key(atom):
    return tuple(atom[k] for k in ('chain', 'residue', 'number', 'insertion', 'name'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--crystal', type=Path, required=True)
    parser.add_argument('--prepared', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    crystal, prepared = read(args.crystal), read(args.prepared, True)
    if len({key(a) for a in prepared}) != len(prepared):
        raise ValueError('ambiguous prepared atom identifiers')
    if any(a['altloc'] not in (' ', 'A') for a in crystal):
        raise ValueError('alternative conformers require explicit selection')
    crystal = [a for a in crystal if a['altloc'] in (' ', 'A')]
    if len({key(a) for a in crystal}) != len(crystal):
        raise ValueError('ambiguous crystal identifiers')
    ligand = [a for a in crystal if a['residue'] == 'PC' and a['chain'] == 'A']
    zinc = [a for a in crystal if a['residue'] == 'ZN' and a['chain'] == 'A']
    if not ligand or not zinc:
        raise ValueError('missing ligand or zinc reference')
    lookup = {key(a): a for a in prepared}
    pocket = []
    for atom in crystal:
        dlig = min(math.dist(atom['xyz'], p['xyz']) for p in ligand)
        dzn = min(math.dist(atom['xyz'], p['xyz']) for p in zinc)
        if dlig <= 5 or dzn <= 3:
            row = dict(atom, ligand_min_A=dlig, zinc_min_A=dzn, retained=key(atom) in lookup)
            if row['retained']:
                row['coordinate_shift_A'] = math.dist(atom['xyz'], lookup[key(atom)]['xyz'])
            pocket.append(row)
    protein = [a for a in crystal if a['record'] == 'ATOM' and a['chain'] == 'A']
    missing = [a for a in protein if key(a) not in lookup]
    water = [a for a in pocket if a['residue'] == 'HOH']
    metadata = [l.rstrip() for l in args.crystal.read_text().splitlines()
                if l.startswith(('SOURCE', 'REMARK 280')) or 'PH                             :' in l
                or 'RESOLUTION. ' in l]
    result = {'scope': 'coordinate/identity inventory, not protonation or metal-physics validation',
              'crystal_chain_A_protein_heavy_atoms': len(protein), 'prepared_heavy_atoms': len(prepared),
              'missing_chain_A_protein_atoms': missing,
              'crystal_chain_A_zinc_count': len(zinc),
              'retained_chain_A_zinc_count': sum(key(a) in lookup for a in zinc),
              'pocket_water_atoms': water, 'pocket_atoms': pocket, 'crystal_metadata': metadata}
    result['source_sha256'] = {}
    for name in ('crystal', 'prepared'):
        path = getattr(args, name)
        raw = path.read_bytes()
        (args.output / (name + path.suffix)).write_bytes(raw)
        result['source_sha256'][name] = hashlib.sha256(raw).hexdigest()
    (args.output / Path(__file__).name).write_bytes(Path(__file__).read_bytes())
    (args.output / 'result.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in result.items() if k not in ('pocket_atoms', 'crystal_metadata')}, indent=2))
