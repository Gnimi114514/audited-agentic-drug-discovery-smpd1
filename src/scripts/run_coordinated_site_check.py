"""Replay the strict PC diagnostic through lifecycle state; preserve scientific FAIL."""
import argparse
import json
import math
from pathlib import Path
import sys
import time
from workflow_state import Workflow
from workflow_subprocess_adapter import SubprocessAdapter


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    project, root = args.project.resolve(), args.output.resolve()
    root.mkdir(parents=True, exist_ok=False)
    snapshots = root / 'code-snapshot'
    snapshots.mkdir()
    names = ('check_pc_graph_rmsd.py', 'workflow_state.py', 'workflow_subprocess_adapter.py', 'run_coordinated_site_check.py')
    for name in names:
        (snapshots / name).write_bytes((project / 'scripts' / name).read_bytes())
    source = project / 'runs/site-graph-20260915/analysis'
    data = {'ccd': source / 'ccd.cif', 'reference': source / 'reference.pdb',
            'pose': source / 'pose.pdbqt', 'prepared': source / 'prepared.pdbqt'}
    protocol = root / 'protocol.json'
    protocol.write_text(json.dumps({'metric': 'ccd_graph_rmsd_A', 'threshold_A': 2.0,
        'operator': '<=', 'threshold_origin': 'existing campaign pose criterion; replay is not new preregistration',
        'scope': 'strict PC CCD-template diagnostic, no full receptor or potency validation'}, indent=2), encoding='utf-8')
    workflow = Workflow(root, 'project-coordinator')
    workflow.add('site-diagnostic', 'site-check-producer', max_attempts=1)
    workflow.add('scientific-screening', 'screening-producer', dependencies=('site-diagnostic',), max_attempts=1)
    inputs = list(data.values()) + list(snapshots.iterdir()) + [protocol]
    workflow.prepare('site-diagnostic', inputs)
    attempt = workflow.reserve('site-diagnostic')
    folder = Path(attempt['directory'])
    argv = [sys.executable, str(snapshots / 'check_pc_graph_rmsd.py')]
    for key, path in data.items():
        argv.extend(['--' + key, str(path)])
    argv.extend(['--output', str(folder / 'analysis')])
    (folder / 'command.json').write_text(json.dumps({'argv': argv, 'cwd': str(project)}, indent=2), encoding='utf-8')
    adapter = SubprocessAdapter()
    handle = adapter.launch(argv, project, folder)
    workflow.bind_handle('site-diagnostic', handle)
    start = time.monotonic()
    index = 0
    while True:
        path = folder / f'observation-{index:03d}.json'
        obs = adapter.observe(handle, path)
        workflow.observe('site-diagnostic', path)
        if obs['status'] == 'TERMINAL':
            if obs['exit_code'] != 0:
                return obs['exit_code']
            break
        if time.monotonic() - start >= 30:
            return 2
        adapter.wait(handle, 1)
        index += 1
    result = json.loads((folder / 'analysis/result.json').read_bytes())
    value = result['ccd_graph_rmsd_A']
    if type(value) not in (float, int) or not math.isfinite(value) or value < 0:
        raise ValueError('invalid RMSD')
    outcome = 'PASS' if value <= 2.0 else 'FAIL'
    (folder / 'gate-evaluation.json').write_text(json.dumps({'outcome': outcome,
        'rmsd_A': value, 'threshold_A': 2.0, 'scope': 'one diagnostic only',
        'full_G2_accepted': False}, indent=2), encoding='utf-8')
    outputs = [p for p in folder.rglob('*') if p.is_file() and p.name != 'dispatch.json']
    workflow.submit('site-diagnostic', outputs, outcome)
    print(json.dumps({'state': 'REVIEW', 'scientific_outcome': outcome, 'rmsd_A': value,
                      'downstream': 'not dispatched; independent review required'}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
