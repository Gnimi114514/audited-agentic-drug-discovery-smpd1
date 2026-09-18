"""Launch and resume one actual route-check stage in separate coordinator processes."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import uuid


def frozen_module(root, name):
    path = root / 'code-snapshot' / (name + '.py')
    spec = importlib.util.spec_from_file_location('frozen_' + name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def adapter(root):
    return frozen_module(root, 'workflow_durable_process')


def verify_resume_snapshot(root):
    # Validate fixed code before importing it. The coordinator state is trusted;
    # this catches accidental snapshot drift, not malicious consistent rewrites.
    state = json.loads((root / 'state.json').read_bytes())
    inputs = state['tasks']['route-identity']['inputs']
    for name in ('workflow_state.py', 'workflow_durable_process.py',
                 'check_route_reaction_identity.py', 'run_durable_route_stage.py'):
        path = (root / 'code-snapshot' / name).resolve()
        expected = inputs.get(str(path))
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if expected is None or actual != expected:
            raise ValueError('executed snapshot changed: ' + name)
    if Path(__file__).read_bytes() != (root / 'code-snapshot/run_durable_route_stage.py').read_bytes():
        raise ValueError('resume driver differs from pinned revision; use frozen driver')


def start(project, source, root):
    root.mkdir(parents=True, exist_ok=False)
    snapshot = root / 'code-snapshot'
    snapshot.mkdir()
    for name in ('workflow_state.py', 'workflow_durable_process.py',
                 'check_route_reaction_identity.py', 'run_durable_route_stage.py'):
        (snapshot / name).write_bytes((project / 'scripts' / name).read_bytes())
    workflow = frozen_module(root, 'workflow_state').Workflow(root, 'project-coordinator')
    workflow.add('route-identity', 'durable-route-producer', max_attempts=1)
    protocol = root / 'run-protocol.json'
    protocol.write_text(json.dumps({'project': str(project), 'source': str(source),
                                  'python': sys.executable, 'timeout_seconds': 15}, indent=2), encoding='utf-8')
    inputs = sorted(snapshot.glob('*.py')) + [protocol, source / 'targets.json'] + sorted(source.glob('*/trees.json'))
    workflow.prepare('route-identity', inputs)
    attempt = workflow.reserve('route-identity')
    directory = Path(attempt['directory'])
    argv = [sys.executable, str(snapshot / 'check_route_reaction_identity.py'),
            '--run', str(source), '--output', str(directory / 'analysis')]
    handle = adapter(root).launch(directory / 'process', argv, project, wall_timeout=15)
    # A crash before this write leaves an unresolved reservation, never a retry permit.
    with (directory / 'adapter-handle.json').open('x', encoding='utf-8') as f:
        json.dump(handle, f, indent=2)
    workflow.bind_handle('route-identity', {'provider': handle['provider'], 'id': handle['id']})
    return {'state': 'RUNNING', 'scope': 'launcher exits; later resume observes persisted job'}


def resume(root):
    verify_resume_snapshot(root)
    workflow = frozen_module(root, 'workflow_state').Workflow(root, 'project-coordinator')
    task = workflow.read()['tasks']['route-identity']
    if task['state'] in ('REVIEW', 'ACCEPTED', 'FAILED', 'INVALIDATED'):
        return {'state': task['state'], 'scope': 'no new dispatch'}
    if task['state'] != 'RUNNING':
        raise ValueError('no running task to observe')
    attempt = task['attempts'][-1]
    directory = Path(attempt['directory'])
    # Revalidate the complete pinned request before using its command specification.
    for file, expected in task['inputs'].items():
        if hashlib.sha256(Path(file).read_bytes()).hexdigest() != expected:
            raise ValueError('task input changed: ' + file)
    handle = json.loads((directory / 'adapter-handle.json').read_bytes())
    if attempt['handle'] != {'provider': handle['provider'], 'id': handle['id']}:
        raise ValueError('adapter handle does not match reserved task')
    module = adapter(root)
    protocol = json.loads((root / 'run-protocol.json').read_bytes())
    expected_argv = [protocol['python'], str(root / 'code-snapshot/check_route_reaction_identity.py'),
                     '--run', protocol['source'], '--output', str(directory / 'analysis')]
    if (Path(handle['directory']).resolve() != directory / 'process'
            or handle['digest'] != module.command_digest(expected_argv, protocol['project'], protocol['timeout_seconds'])):
        raise ValueError('durable command or process directory does not match task')
    if attempt['execution'] == 'TERMINAL':
        observation = dict(attempt['observations'][-1])
        original_hash = observation.pop('source_sha256')
        matching = [p for p in directory.glob('observation-*.json')
                    if hashlib.sha256(p.read_bytes()).hexdigest() == original_hash]
        if len(matching) != 1 or json.loads(matching[0].read_bytes()) != observation:
            raise ValueError('persisted terminal observation evidence changed')
    else:
        observation = module.observe(handle)
        path = directory / ('observation-' + uuid.uuid4().hex + '.json')
        with path.open('x', encoding='utf-8') as f:
            json.dump(observation, f, indent=2)
        workflow.observe('route-identity', path)
    if observation['status'] != 'TERMINAL':
        return {'state': observation['status'], 'scope': 'original handle only; no redispatch'}
    if observation['exit_code'] != 0:
        return {'state': 'FAILED', 'exit_code': observation['exit_code']}
    result = directory / 'analysis/result.json'
    if not result.is_file():
        raise ValueError('successful process did not produce required result')
    recorded = workflow.read()['tasks']['route-identity']['attempts'][-1]['observations']
    observation_files = list(directory.glob('observation-*.json'))
    by_hash = {hashlib.sha256(p.read_bytes()).hexdigest(): p for p in observation_files}
    if (len(by_hash) != len(observation_files)
            or set(by_hash) != {o['source_sha256'] for o in recorded}):
        raise ValueError('observation files do not exactly match consumed history; reconcile explicitly')
    for item in recorded:
        expected = dict(item)
        source_hash = expected.pop('source_sha256')
        if json.loads(by_hash[source_hash].read_bytes()) != expected:
            raise ValueError('observation content differs from consumed history')
    # Administrative supervisor logs remain outside the scientific output manifest.
    outputs = list((directory / 'analysis').glob('*')) + observation_files + [
        directory / 'adapter-handle.json', directory / 'process/intent.json',
        directory / 'process/terminal.json', directory / 'process/command.stdout',
        directory / 'process/command.stderr']
    workflow.submit('route-identity', outputs, 'PASS')
    return {'state': 'REVIEW', 'scope': 'actual recovered execution; independent acceptance pending'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode', choices=('start', 'resume'))
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--project', type=Path)
    p.add_argument('--source-run', type=Path)
    args = p.parse_args()
    root = args.output.resolve()
    if args.mode == 'start':
        if args.project is None or args.source_run is None:
            p.error('start requires --project and --source-run')
        result = start(args.project.resolve(), args.source_run.resolve(), root)
    else:
        result = resume(root)
    print(json.dumps(result))


if __name__ == '__main__':
    main()
