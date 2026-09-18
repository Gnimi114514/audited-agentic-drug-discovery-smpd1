"""Exercise real retrosynthesis with target excluded from proxy stock.

This establishes planner behavior only, not purchasable or experimentally valid routes.
"""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import time
import yaml
from aizynthfinder.aizynthfinder import AiZynthFinder


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--fixture-stock', type=Path,
                        help='Explicit artificial test-stock CSV, not purchase evidence')
    args = parser.parse_args()
    root, out = args.project.resolve(), args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    config = yaml.safe_load((root / 'aizynth_config_syn.yml').read_text())
    stock_name = 'chembl_proxy'
    stock_scope = 'ChEMBL proxy'
    if args.fixture_stock:
        stock_name = 'defined_fixture'
        stock_scope = 'Explicit artificial fixture stock; not purchasability evidence'
        config['stock'] = {stock_name: {'path': str(args.fixture_stock.resolve())}}
    hashes = {}
    for category in ('expansion', 'filter', 'stock'):
        for entry in config[category].values():
            for key in ('model', 'template', 'path'):
                if key in entry:
                    path = root / entry[key]
                    hashes[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
                    entry[key] = str(path)
    config['search'].update(time_limit=30, iteration_limit=30, max_transforms=3,
                            return_first=True, exclude_target_from_stock=True)
    protocol = {'target': 'CC(=O)Oc1ccccc1C(=O)O', 'fixture': 'aspirin', 'stock_scope': stock_scope,
                'config': config, 'input_sha256': hashes,
                'aizynthfinder_version': importlib.metadata.version('aizynthfinder'),
                'scope': 'nonzero reaction-tree software fixture, not synthesis feasibility or purchase evidence'}
    (out / 'protocol.json').write_text(json.dumps(protocol, indent=2), encoding='utf-8')
    (out / Path(__file__).name).write_bytes(Path(__file__).read_bytes())
    finder = AiZynthFinder(configdict=config)
    finder.expansion_policy.select('uspto')
    finder.filter_policy.select('uspto')
    finder.stock.select(stock_name)
    finder.target_smiles = protocol['target']
    original_membership = finder.target_mol in finder.stock
    finder.prepare_tree()
    excluded = finder.target_mol not in finder.stock
    if not excluded:
        raise ValueError('target still admitted by stock; refusing zero-step fixture')
    start = time.monotonic()
    finder.tree_search()
    finder.build_routes()
    routes = finder.routes.dicts
    (out / 'routes.json').write_text(json.dumps(routes, indent=2), encoding='utf-8')

    def count(node):
        return int(node.get('type') == 'reaction') + sum(count(n) for n in node.get('children', []))

    result = {'elapsed_search_seconds': time.monotonic() - start,
              'target_originally_in_selected_stock': original_membership,
              'target_excluded_before_search': excluded, 'exported_tree_count': len(routes),
              'reaction_counts': [count(r) for r in routes],
              'statistics': finder.extract_statistics(),
              'scope': protocol['scope']}
    (out / 'result.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))
