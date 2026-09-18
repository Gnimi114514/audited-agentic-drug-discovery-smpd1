"""Execute one real route-identity stage into REVIEW; independent acceptance is separate."""
import argparse
import json
from pathlib import Path
import sys
import time
from workflow_state import Workflow
from workflow_subprocess_adapter import SubprocessAdapter


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, required=True)
    parser.add_argument('--source-run', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    project, source, root = args.project.resolve(), args.source_run.resolve(), args.output.resolve()
    root.mkdir(parents=True, exist_ok=False)
    workflow = Workflow(root, 'project-coordinator')
    task = 'route-identity'
    workflow.add(task, 'route-check-producer', max_attempts=1)
    scripts = [project / 'scripts' / name for name in (
        'check_route_reaction_identity.py', 'workflow_state.py',
        'workflow_subprocess_adapter.py', 'run_coordinated_route_check.py')]
    inputs = scripts + [source / 'targets.json'] + sorted(source.glob('*/trees.json'))
    snapshots = root / 'code-snapshot'
    snapshots.mkdir()
    for path in scripts:
        (snapshots / path.name).write_bytes(path.read_bytes())
    workflow.prepare(task, inputs)
    attempt = workflow.reserve(task)
    folder = Path(attempt['directory'])
    argv = [sys.executable, str(snapshots / 'check_route_reaction_identity.py'),
            '--run', str(source), '--output', str(folder / 'analysis')]
    (folder / 'command.json').write_text(json.dumps({'argv': argv, 'cwd': str(project),
        'scope': 'single real stage integration; no science or full scheduler acceptance',
        'observation_budget_seconds': 30}, indent=2), encoding='utf-8')
    adapter = SubprocessAdapter()
    handle = adapter.launch(argv, project, folder)
    workflow.bind_handle(task, handle)
    start = time.monotonic()
    index = 0
    while True:
        path = folder / f'observation-{index:03d}.json'
        obs = adapter.observe(handle, path)
        workflow.observe(task, path)
        if obs['status'] == 'TERMINAL':
            if obs['exit_code'] != 0:
                return obs['exit_code']
            break
        if time.monotonic() - start >= 30:
            # Keep reservation unresolved. A new driver must not relaunch this run.
            return 2
        adapter.wait(handle, 1)
        index += 1
    outputs = [p for p in folder.rglob('*') if p.is_file() and p.name != 'dispatch.json']
    workflow.submit(task, outputs, 'PASS')
    print(json.dumps({'task': task, 'state': workflow.read()['tasks'][task]['state'],
                      'scope': 'route identity checker execution only; independent review pending'}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
