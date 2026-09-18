"""Bounded candidate retrosynthesis against an integrity-verified historical stock."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import time
import yaml
from aizynthfinder.aizynthfinder import AiZynthFinder


def file_hash(path, algorithm):
    digest = hashlib.new(algorithm)
    with path.open('rb') as handle:
        while block := handle.read(8*1024*1024):
            digest.update(block)
    return digest.hexdigest()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('project', 'stock', 'stock-protocol', 'targets', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    source = json.loads(args.stock_protocol.read_bytes())
    if args.stock.stat().st_size != source['size'] or 'md5:' + file_hash(args.stock, 'md5') != source['checksum']:
        raise ValueError('stock does not match source size/checksum')
    targets_raw = args.targets.read_bytes()
    targets = json.loads(targets_raw)
    if not isinstance(targets, list) or not 1 <= len(targets) <= 3:
        raise ValueError('target batch must contain 1-3 entries')
    if any(not re.fullmatch('[A-Za-z0-9_-]+', t['id']) for t in targets) or len({t['id'] for t in targets}) != len(targets):
        raise ValueError('unsafe or duplicate target identifiers')
    root, out = args.project.resolve(), args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    config = yaml.safe_load((root / 'aizynth_config_syn.yml').read_text())
    hashes = {'stock_md5': source['checksum']}
    for category in ('expansion', 'filter'):
        for entry in config[category].values():
            for key in ('model', 'template'):
                if key in entry:
                    path = root / entry[key]
                    hashes[str(path)] = file_hash(path, 'sha256')
                    entry[key] = str(path)
    config['stock'] = {'zinc_snapshot': {'path': str(args.stock.resolve())}}
    config['search'].update(time_limit=30, iteration_limit=100, max_transforms=6,
                            return_first=True, exclude_target_from_stock=True)
    (out / 'protocol.json').write_text(json.dumps({'config': config, 'hashes': hashes,
        'stock_source': source, 'scope': 'historical inventory closure, not current purchasability or chemical validation'}, indent=2), encoding='utf-8')
    (out / 'targets.json').write_bytes(targets_raw)
    (out / Path(__file__).name).write_bytes(Path(__file__).read_bytes())
    finder = AiZynthFinder(configdict=config)
    finder.stock.select('zinc_snapshot')
    finder.expansion_policy.select('uspto')
    finder.filter_policy.select('uspto')
    results = []
    for target in targets:
        folder = out / target['id']
        folder.mkdir()
        finder.stock.reset_exclusion_list()
        finder.target_smiles = target['smiles']
        was_member = finder.target_mol in finder.stock
        finder.prepare_tree()
        if finder.target_mol in finder.stock:
            raise ValueError('target remains in stock; zero-step shortcut not allowed')
        start = time.monotonic()
        finder.tree_search()
        finder.build_routes()
        trees = finder.routes.dicts
        (folder / 'trees.json').write_text(json.dumps(trees, indent=2), encoding='utf-8')

        def summarize(node):
            children = node.get('children', [])
            reactions = int(node.get('type') == 'reaction')
            leaves = [node] if not children and node.get('type') == 'mol' else []
            for child in children:
                count, other = summarize(child)
                reactions += count
                leaves.extend(other)
            return reactions, leaves

        evaluated = []
        for tree in trees:
            count, leaves = summarize(tree)
            evaluated.append({'reaction_count': count, 'terminal_count': len(leaves),
                'closed_nonzero': count > 0 and bool(leaves) and all(n.get('in_stock') is True for n in leaves),
                'terminal_smiles': [n['smiles'] for n in leaves]})
        result = {'id': target['id'], 'elapsed_search_seconds': time.monotonic()-start,
                  'target_was_in_snapshot': was_member, 'exported_tree_count': len(trees),
                  'trees': evaluated, 'statistics': finder.extract_statistics(),
                  'scope': 'exported stock flags require independent membership verification; no purchase or efficacy claim'}
        (folder / 'result.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
        results.append(result)
        print(json.dumps({'id': target['id'], 'closed_nonzero': sum(t['closed_nonzero'] for t in evaluated)}), flush=True)
    (out / 'results.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
