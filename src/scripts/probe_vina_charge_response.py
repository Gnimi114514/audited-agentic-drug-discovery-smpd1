"""Three fixed-pose engine controls; no docking, protonation inference or affinity claim."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    root, out = args.project.resolve(), args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    binary = root / 'bin/vina.exe'
    ligand = (root / 'structures/PC_ref.pdbqt').read_text()
    receptor = (root / 'structures/5i85_recA_ZN_rigid.pdbqt').read_bytes()
    (out / 'receptor.pdbqt').write_bytes(receptor)
    variants = {'baseline': [], 'synthetic_q_only': [], 'translated_x4_A': []}
    for line in ligand.splitlines():
        variants['baseline'].append(line)
        if line.startswith(('ATOM  ', 'HETATM')):
            q = 0.7 if int(line[6:11]) % 2 else -0.7
            variants['synthetic_q_only'].append(line[:70] + f'{q:6.3f}' + line[76:])
            variants['translated_x4_A'].append(line[:30] + f'{float(line[30:38])+4:8.3f}' + line[38:])
        else:
            variants['synthetic_q_only'].append(line)
            variants['translated_x4_A'].append(line)
    for name, lines in variants.items():
        (out / (name + '.pdbqt')).write_text('\n'.join(lines) + '\n', encoding='utf-8')
    help_result = subprocess.run([str(binary), '--help_advanced'], capture_output=True, timeout=10, check=True)
    (out / 'engine-help.txt').write_bytes(help_result.stdout)
    protocol = {'scope': 'fixed-coordinate score-only software feature probe; charge values deliberately synthetic, not a chemical state',
                'scoring': 'vina', 'cpu': 1, 'seed': 42, 'timeout_per_control_seconds': 30,
                'box_center_A': [-13.710, -34.100, -28.720], 'box_size_A': [18, 18, 18],
                'controls': ['baseline', 'synthetic_q_only', 'translated_x4_A'],
                'comparison': 'compare all printed energy terms at their reported precision; geometry control tests score responsiveness',
                'prohibited_inference': ['No protonation preference', 'No metal electrostatics validation', 'No binding affinity or G2 acceptance'],
                'input_sha256': {'binary': hashlib.sha256(binary.read_bytes()).hexdigest(),
                                 'receptor': hashlib.sha256(receptor).hexdigest(),
                                 'original_ligand': hashlib.sha256((root / 'structures/PC_ref.pdbqt').read_bytes()).hexdigest()}}
    (out / 'protocol.json').write_text(json.dumps(protocol, indent=2), encoding='utf-8')
    (out / Path(__file__).name).write_bytes(Path(__file__).read_bytes())
    results = []
    for name in variants:
        argv = [str(binary), '--scoring', 'vina', '--score_only', '--cpu', '1', '--seed', '42',
                '--receptor', str(out / 'receptor.pdbqt'), '--ligand', str(out / (name + '.pdbqt')),
                '--center_x', '-13.710', '--center_y', '-34.100', '--center_z', '-28.720',
                '--size_x', '18', '--size_y', '18', '--size_z', '18']
        started = time.monotonic()
        run = subprocess.run(argv, capture_output=True, timeout=30)
        (out / (name + '-stdout.txt')).write_bytes(run.stdout)
        (out / (name + '-stderr.txt')).write_bytes(run.stderr)
        results.append({'control': name, 'argv': argv, 'exit_code': run.returncode,
                        'elapsed_seconds': time.monotonic() - started})
    (out / 'execution.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
    print(json.dumps(results, indent=2))
    return 0 if all(r['exit_code'] == 0 for r in results) else 2


if __name__ == '__main__':
    raise SystemExit(main())
