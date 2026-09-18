"""Bounded, non-overwriting replay of the historical PC docking settings."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root, out = args.project.resolve(), args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    files = {'receptor.pdbqt': root / 'structures/5i85_recA_ZN_rigid.pdbqt',
             'ligand.pdbqt': root / 'structures/PC_ref.pdbqt'}
    hashes = {}
    for name, path in files.items():
        raw = path.read_bytes()
        (out / name).write_bytes(raw)
        hashes[name] = hashlib.sha256(raw).hexdigest()
    binary = root / 'bin/vina.exe'
    hashes['vina.exe'] = hashlib.sha256(binary.read_bytes()).hexdigest()
    version = subprocess.run([str(binary), '--version'], capture_output=True, text=True, check=True, timeout=10).stdout
    command = [str(binary), '--receptor', str(out / 'receptor.pdbqt'), '--ligand', str(out / 'ligand.pdbqt'),
               '--center_x', '-13.710', '--center_y', '-34.100', '--center_z', '-28.720',
               '--size_x', '18', '--size_y', '18', '--size_z', '18', '--exhaustiveness', '32',
               '--seed', '42', '--num_modes', '9', '--cpu', '4', '--out', str(out / 'poses.pdbqt')]
    protocol = {'command': command, 'input_sha256': hashes, 'engine_version': version.strip(),
                'timeout_seconds': 120, 'cpu_threads': 4,
                'scope': 'replay existing chemical preparation; no protonation repair or parameter tuning'}
    (out / 'protocol.json').write_text(json.dumps(protocol, indent=2), encoding='utf-8')
    (out / Path(__file__).name).write_bytes(Path(__file__).read_bytes())
    start = time.monotonic()
    with (out / 'stdout.log').open('w') as stdout, (out / 'stderr.log').open('w') as stderr:
        try:
            result = subprocess.run(command, stdout=stdout, stderr=stderr, timeout=120)
            status = {'returncode': result.returncode, 'status': 'EXECUTED' if result.returncode == 0 else 'FAILED'}
        except subprocess.TimeoutExpired:
            status = {'status': 'TIMEOUT'}
    status['elapsed_seconds'] = time.monotonic() - start
    pose = out / 'poses.pdbqt'
    if status['status'] == 'EXECUTED':
        if not pose.is_file() or not any(l.startswith('MODEL') for l in pose.read_text().splitlines()):
            status['status'] = 'FAILED_OUTPUT_CHECK'
        else:
            status['output_sha256'] = hashlib.sha256(pose.read_bytes()).hexdigest()
    (out / 'execution.json').write_text(json.dumps(status, indent=2), encoding='utf-8')
    print(json.dumps(status, indent=2))
    raise SystemExit(0 if status['status'] == 'EXECUTED' else 2)
