"""PC-specific CCD graph-constrained pose diagnostic in the unchanged receptor frame.

Does not infer docked protonation from PDBQT or certify general docking validity.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import shlex
from rdkit import Chem, rdBase


def loop(path, prefix):
    lines = path.read_text(encoding='utf-8').splitlines()
    start = next(i for i, line in enumerate(lines) if line.strip().startswith(prefix))
    tags = []
    while lines[start].strip().startswith(prefix):
        tags.append(lines[start].strip())
        start += 1
    tokens = []
    while start < len(lines) and not lines[start].strip().startswith(('#', 'loop_', '_')):
        if lines[start].startswith(';'):
            raise ValueError('multiline CIF values unsupported in this PC-specific parser')
        tokens.extend(shlex.split(lines[start]))
        start += 1
    if not tokens or len(tokens) % len(tags):
        raise ValueError('invalid CCD loop dimensions')
    return [dict(zip(tags, tokens[i:i+len(tags)])) for i in range(0, len(tokens), len(tags))]


def ccd_graph(path):
    atoms, bonds = loop(path, '_chem_comp_atom.'), loop(path, '_chem_comp_bond.')
    mol, indices = Chem.RWMol(), {}
    for row in atoms:
        if row['_chem_comp_atom.comp_id'] != 'PC' or row['_chem_comp_atom.pdbx_stereo_config'] != 'N':
            raise ValueError('only the achiral PC CCD template is supported')
        name = row['_chem_comp_atom.atom_id']
        if name in indices:
            raise ValueError('duplicate CCD atom name')
        atom = Chem.Atom(row['_chem_comp_atom.type_symbol'])
        atom.SetFormalCharge(int(row['_chem_comp_atom.charge']))
        atom.SetProp('ccd_name', name)
        indices[name] = mol.AddAtom(atom)
    orders = {'SING': Chem.BondType.SINGLE, 'DOUB': Chem.BondType.DOUBLE}
    for row in bonds:
        mol.AddBond(indices[row['_chem_comp_bond.atom_id_1']], indices[row['_chem_comp_bond.atom_id_2']],
                    orders[row['_chem_comp_bond.value_order']])
    full = mol.GetMol()
    Chem.SanitizeMol(full)
    return Chem.RemoveHs(full)


def coords(path, pdbqt=False):
    result = {}
    types = {'OA': 'O', 'N': 'N', 'C': 'C', 'P': 'P', 'HD': 'H', 'H': 'H'}
    for line in path.read_text().splitlines():
        if line.startswith('ENDMDL'):
            break
        if not line.startswith(('ATOM  ', 'HETATM')):
            continue
        name = line[12:16].strip()
        element = types[line.split()[-1]] if pdbqt else line[76:78].strip()
        if element == 'H':
            continue
        if name in result:
            raise ValueError('duplicate heavy atom name')
        xyz = tuple(float(line[a:a+8]) for a in (30, 38, 46))
        if not all(math.isfinite(v) for v in xyz):
            raise ValueError('nonfinite coordinates')
        result[name] = {'element': element, 'xyz': xyz}
    if not result:
        raise ValueError('missing heavy atoms')
    return result


def calculate(ccd, reference, pose, prepared):
    mol = ccd_graph(ccd)
    names = [a.GetProp('ccd_name') for a in mol.GetAtoms()]
    ref, dock, initial = coords(reference), coords(pose, True), coords(prepared, True)
    for rows in (ref, dock, initial):
        if set(rows) != set(names):
            raise ValueError('PC heavy atom identity mismatch')
        for atom in mol.GetAtoms():
            if rows[names[atom.GetIdx()]]['element'] != atom.GetSymbol():
                raise ValueError('PC heavy atom element mismatch')
    preparation_shift = max(math.dist(ref[n]['xyz'], initial[n]['xyz']) for n in names)
    if preparation_shift > 0.002:
        raise ValueError('prepared ligand reference frame differs from crystal')
    maps = mol.GetSubstructMatches(mol, uniquify=False, useChirality=True, maxMatches=100001)
    if not maps or len(maps) >= 100001:
        raise ValueError('automorphism enumeration missing or truncated')

    def rmsd(mapping):
        return math.sqrt(sum(math.dist(ref[names[i]]['xyz'], dock[names[j]]['xyz'])**2
                             for i, j in enumerate(mapping)) / len(names))

    best = min(maps, key=rmsd)
    return {'heavy_atoms': len(names), 'graph_automorphisms': len(maps),
            'name_matched_rmsd_A': rmsd(tuple(range(len(names)))),
            'ccd_graph_rmsd_A': rmsd(best),
            'best_name_mapping': {names[i]: names[j] for i, j in enumerate(best)},
            'ccd_formal_charge': Chem.GetFormalCharge(mol),
            'ccd_isomeric_smiles': Chem.MolToSmiles(mol),
            'prepared_reference_max_shift_A': preparation_shift,
            'rdkit_version': rdBase.rdkitVersion,
            'coordinate_convention': 'first docked model, no ligand fitting, original receptor frame assumed',
            'scope': 'strict named CCD bond-order/protonation-template automorphisms; docked graph inherited by atom names',
            'limitations': ['PDBQT does not independently encode a complete bond-order/formal-charge graph',
                            'CCD chemical form is not proof of solution protonation or catalytic suitability',
                            'No symmetry equivalence across alternative protonation/resonance states is asserted',
                            'No receptor preparation, scoring or general docking validation is certified']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('ccd', 'reference', 'pose', 'prepared', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    inputs = {}
    for name in ('ccd', 'reference', 'pose', 'prepared'):
        source = getattr(args, name)
        raw = source.read_bytes()
        (args.output / (name + source.suffix)).write_bytes(raw)
        inputs[name] = {'source': str(source.resolve()), 'sha256': hashlib.sha256(raw).hexdigest()}
    (args.output / Path(__file__).name).write_bytes(Path(__file__).read_bytes())
    result = calculate(args.ccd, args.reference, args.pose, args.prepared)
    result['inputs'] = inputs
    (args.output / 'result.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))
