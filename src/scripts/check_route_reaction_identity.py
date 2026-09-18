"""Check exported retrosynthesis identities, not reaction feasibility or atom balance."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
from rdkit import Chem, rdBase


def molecule(smiles):
    if not isinstance(smiles, str) or not smiles:
        raise ValueError('missing molecular SMILES')
    mol = Chem.MolFromSmiles(smiles)
    if mol is None or not mol.GetNumAtoms():
        raise ValueError('invalid molecular SMILES')
    return mol


def canonical(smiles):
    mol = molecule(smiles)
    for atom in mol.GetAtoms():
        atom.SetAtomMapNum(0)
    return Chem.MolToSmiles(mol, isomericSmiles=True)


def mapped_atoms(smiles):
    atoms = {}
    for atom in molecule(smiles).GetAtoms():
        key = atom.GetAtomMapNum()
        if key <= 0 or key in atoms:
            raise ValueError('missing or duplicate atom map on one reaction side')
        atoms[key] = (atom.GetAtomicNum(), atom.GetIsotope())
    return atoms


def check_reaction(parent, reaction):
    if parent.get('type') != 'mol' or reaction.get('type') != 'reaction':
        raise ValueError('invalid parent/reaction node type')
    children = reaction.get('children')
    if not isinstance(children, list) or not children or any(c.get('type') != 'mol' for c in children):
        raise ValueError('reaction needs molecular precursors')
    mapped = reaction.get('metadata', {}).get('mapped_reaction_smiles')
    if not isinstance(mapped, str) or mapped.count('>>') != 1:
        raise ValueError('missing or malformed mapped retrosynthetic reaction')
    product, precursors = mapped.split('>>')
    if canonical(product) != canonical(parent['smiles']):
        raise ValueError('mapped product differs from tree parent')
    if Counter(canonical(s) for s in precursors.split('.')) != Counter(canonical(c['smiles']) for c in children):
        raise ValueError('mapped precursors differ from tree children')
    lhs, rhs = mapped_atoms(product), mapped_atoms(precursors)
    if not lhs.keys() <= rhs.keys():
        raise ValueError('product atom mapping lacks precursor origin')
    if any(rhs[k] != v for k, v in lhs.items()):
        raise ValueError('mapped element/isotope changed')
    return {'product': canonical(product), 'precursors': [canonical(c['smiles']) for c in children],
            'product_atom_count': len(lhs), 'precursor_atom_count': len(rhs),
            'extra_precursor_atom_count': len(rhs.keys() - lhs.keys()),
            'status': 'IDENTITY_CONSISTENT'}


def check_tree(tree):
    results = []
    def visit(node, path):
        if node.get('type') != 'mol':
            raise ValueError('expected molecule node')
        canonical(node.get('smiles'))
        children = node.get('children', [])
        if not isinstance(children, list) or len(children) > 1:
            raise ValueError('exported molecule must select at most one reaction')
        for reaction in children:
            result = check_reaction(node, reaction)
            result['tree_path'] = path
            results.append(result)
            for index, child in enumerate(reaction['children']):
                visit(child, path + '/' + str(index))
    visit(tree, 'root')
    return results


def validate_targets(targets):
    if not isinstance(targets, list) or not targets:
        raise ValueError('targets must be a nonempty list')
    seen = set()
    for target in targets:
        if not isinstance(target, dict):
            raise ValueError('target must be an object')
        ident = target.get('id')
        if not isinstance(ident, str) or not re.fullmatch(r'[A-Za-z0-9_-]+', ident) or ident in seen:
            raise ValueError('unsafe or duplicate target identifier')
        canonical(target.get('smiles'))
        seen.add(ident)
    return targets


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    target_path = args.run / 'targets.json'
    target_raw = target_path.read_bytes()
    targets = validate_targets(json.loads(target_raw))
    evidence, results = {str(target_path.resolve()): hashlib.sha256(target_raw).hexdigest()}, []
    for target in targets:
        path = args.run / target['id'] / 'trees.json'
        raw = path.read_bytes()
        evidence[str(path.resolve())] = hashlib.sha256(raw).hexdigest()
        trees = json.loads(raw)
        if not isinstance(trees, list) or not trees:
            raise ValueError('no exported trees')
        for index, tree in enumerate(trees):
            if canonical(tree['smiles']) != canonical(target['smiles']):
                raise ValueError('tree target identity mismatch')
            steps = check_tree(tree)
            results.append({'id': target['id'], 'tree_index': index, 'reaction_count': len(steps), 'reactions': steps})
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / Path(__file__).name).write_bytes(Path(__file__).read_bytes())
    (args.output / 'result.json').write_text(json.dumps({'rdkit_version': rdBase.rdkitVersion,
        'scope': 'mapped reaction/tree identity and element/isotope provenance only; no feasibility, yield, complete atom balance or stereochemical outcome proof',
        'input_sha256': evidence, 'results': results}, indent=2), encoding='utf-8')
    print(json.dumps({'trees': len(results), 'reaction_nodes': sum(r['reaction_count'] for r in results)}))
