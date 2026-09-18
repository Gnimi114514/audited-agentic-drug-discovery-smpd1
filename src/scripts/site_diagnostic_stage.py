"""Stage output for the historical strict PC diagnostic; not full site acceptance."""
import argparse
import hashlib
import json
from pathlib import Path
from check_pc_graph_rmsd import calculate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    source = args.source.resolve()
    files = {'ccd': source / 'ccd.cif', 'reference': source / 'reference.pdb',
             'pose': source / 'pose.pdbqt', 'prepared': source / 'prepared.pdbqt'}
    args.output.mkdir(parents=True, exist_ok=False)
    inputs = {}
    for key, path in files.items():
        raw = path.read_bytes()
        copy = args.output / path.name
        copy.write_bytes(raw)
        inputs[key] = {'source': str(path), 'sha256': hashlib.sha256(raw).hexdigest()}
    # Calculate from the retained input copies, not from subsequently mutable originals.
    result = calculate(*(args.output / files[key].name for key in ('ccd', 'reference', 'pose', 'prepared')))
    result.update(inputs=inputs, threshold_A=2.0, threshold_origin='historical campaign; not new preregistration',
                  scientific_outcome='PASS' if result['ccd_graph_rmsd_A'] <= 2.0 else 'FAIL',
                  full_G2_accepted=False)
    for name in ('site_diagnostic_stage.py', 'check_pc_graph_rmsd.py'):
        raw = (Path(__file__).resolve().parent / name).read_bytes()
        (args.output / name).write_bytes(raw)
    (args.output / 'result.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps({'scientific_outcome': result['scientific_outcome'], 'rmsd_A': result['ccd_graph_rmsd_A']}))


if __name__ == '__main__':
    main()
