"""Single-coordinator persistent lifecycle foundation; not a scheduler or science validator."""
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import uuid
from datetime import datetime, timezone
from contextlib import contextmanager


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def atomic(path, value):
    temp = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    try:
        with open(temp, 'x', encoding='utf-8') as f:
            json.dump(value, f, indent=2, allow_nan=False)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


class Workflow:
    def __init__(self, root, coordinator):
        if not isinstance(coordinator, str) or not coordinator.strip():
            raise ValueError('coordinator identity required')
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.path = self.root / 'state.json'
        self.coordinator = coordinator

    @contextmanager
    def transaction(self):
        lock = self.root / '.writer.lock'
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        try:
            os.write(fd, json.dumps({'pid': os.getpid(), 'at': now()}).encode())
            state = json.loads(self.path.read_text()) if self.path.exists() else {
                'schema_version': 1, 'coordinator': self.coordinator, 'tasks': {}}
            if state['coordinator'] != self.coordinator:
                raise ValueError('coordinator mismatch')
            yield state
            atomic(self.path, state)
        finally:
            os.close(fd)
            lock.unlink()

    def read(self):
        return json.loads(self.path.read_text(encoding='utf-8'))

    def transition(self, task, state, reason):
        if not reason or not isinstance(reason, str):
            raise ValueError('reason required')
        task['history'].append({'from': task['state'], 'to': state, 'at': now(),
                                'owner': self.coordinator, 'reason': reason})
        task['state'] = state

    def add(self, task_id, producer, dependencies=(), max_attempts=3,
            allowed_outcomes=('PASS',), exploratory_reason=None, purpose='scientific_stage'):
        if type(max_attempts) is not int or max_attempts < 1:
            raise ValueError('positive attempt budget required')
        if not allowed_outcomes or set(allowed_outcomes) - {'PASS', 'CONDITIONAL', 'FAIL', 'BLOCKED', 'NOT_RUN'}:
            raise ValueError('invalid dependency outcomes')
        if purpose not in ('scientific_stage', 'review', 'failure_analysis'):
            raise ValueError('invalid task purpose')
        if set(allowed_outcomes) != {'PASS'} and (not exploratory_reason or purpose == 'scientific_stage'):
            raise ValueError('non-PASS dependencies require explicit scoped analysis rationale')
        if not re.fullmatch(r'[A-Za-z0-9_-]+', task_id) or not producer:
            raise ValueError('invalid identity')
        with self.transaction() as s:
            if task_id in s['tasks'] or len(set(dependencies)) != len(dependencies):
                raise ValueError('duplicate task/dependency')
            if any(d not in s['tasks'] for d in dependencies):
                raise ValueError('dependencies must already exist (DAG)')
            s['tasks'][task_id] = {'state': 'PENDING', 'producer': producer,
                'dependencies': list(dependencies), 'accepted': None, 'attempts': [], 'history': [],
                'max_attempts': max_attempts, 'allowed_outcomes': list(allowed_outcomes),
                'exploratory_reason': exploratory_reason, 'purpose': purpose}

    def invalidate(self, task_id, reason):
        with self.transaction() as s:
            self._invalidate(s, task_id, reason)

    def _invalidate(self, s, task_id, reason):
        todo = [task_id]
        seen = set()
        while todo:
            key = todo.pop()
            if key in seen:
                continue
            seen.add(key)
            t = s['tasks'][key]
            t['accepted'] = None
            self.transition(t, 'INVALIDATED', reason)
            todo.extend(k for k, v in s['tasks'].items() if key in v['dependencies'])

    def prepare(self, task_id, inputs):
        """Explicitly rebind dependencies and hash files, including config/model inputs."""
        if not inputs:
            raise ValueError('nonempty input mapping required')
        hashes = {str(Path(p).resolve()): digest(p) for p in inputs}
        with self.transaction() as s:
            t = s['tasks'][task_id]
            if t['state'] not in ('PENDING', 'INVALIDATED', 'REWORK', 'FAILED', 'BLOCKED'):
                raise ValueError('cannot prepare active/accepted task')
            if any(a['execution'] in ('RESERVED', 'RUNNING', 'UNKNOWN') for a in t['attempts']):
                raise ValueError('unresolved execution; cannot duplicate dispatch')
            deps = {d: s['tasks'][d]['accepted'] for d in t['dependencies']}
            if any(v is None for v in deps.values()):
                raise ValueError('dependencies not accepted')
            for d in deps:
                upstream = s['tasks'][d]
                self._verify_accepted(s, upstream)
                if upstream['attempts'][-1]['manifest']['outcome'] not in t['allowed_outcomes']:
                    raise ValueError('dependency scientific outcome does not authorize this stage')
            t['inputs'] = hashes
            t['dependency_revisions'] = deps
            self.transition(t, 'READY', 'inputs and accepted dependency revisions pinned')

    def _check_inputs(self, s, t):
        if any(not Path(p).is_file() or digest(p) != h for p, h in t['inputs'].items()):
            raise ValueError('input changed; invalidate and prepare again')
        if any(s['tasks'][d]['accepted'] != r for d, r in t['dependency_revisions'].items()):
            raise ValueError('dependency changed')
        for d in t['dependency_revisions']:
            self._verify_accepted(s, s['tasks'][d])

    def _verify_accepted(self, s, t):
        if t['state'] != 'ACCEPTED' or t['accepted'] is None:
            raise ValueError('dependency not accepted')
        self._check_inputs(s, t)
        a = t['attempts'][-1]
        if digest(Path(a['directory']) / 'result-manifest.json') != a['manifest_sha256']:
            raise ValueError('accepted manifest changed; invalidate upstream')
        if any(digest(p) != h for p, h in a['manifest']['artifacts'].items()):
            raise ValueError('accepted artifact changed; invalidate upstream')
        if digest(a['review']['path']) != a['review']['sha256']:
            raise ValueError('accepted review changed; invalidate upstream')

    def reserve(self, task_id):
        """Reserve before launch. Crash between reserve and handle binding stays unresolved."""
        with self.transaction() as s:
            t = s['tasks'][task_id]
            if t['state'] != 'READY':
                raise ValueError('not ready')
            if len(t['attempts']) >= t['max_attempts']:
                raise ValueError('attempt budget exhausted; diagnosis required')
            self._check_inputs(s, t)
            attempt_id = uuid.uuid4().hex
            directory = self.root / 'tasks' / task_id / ('attempt-' + attempt_id)
            directory.mkdir(parents=True, exist_ok=False)
            a = {'id': attempt_id, 'directory': str(directory), 'execution': 'RESERVED',
                 'handle': None, 'observations': [], 'inputs': copy.deepcopy(t['inputs']),
                 'dependencies': copy.deepcopy(t['dependency_revisions'])}
            atomic(directory / 'dispatch.json', a)
            t['attempts'].append(a)
            self.transition(t, 'RUNNING', 'unique attempt reserved before external dispatch')
        return a

    def bind_handle(self, task_id, handle):
        """Adapter supplies provider plus opaque unique job/session identifier (not PID alone)."""
        if set(handle) != {'provider', 'id'} or any(not isinstance(x, str) or not x for x in handle.values()):
            raise ValueError('provider and unique id required')
        with self.transaction() as s:
            a = s['tasks'][task_id]['attempts'][-1]
            if a['execution'] != 'RESERVED' or a['handle'] is not None:
                raise ValueError('handle already bound / attempt not reserved')
            a['handle'] = dict(handle)
            a['execution'] = 'RUNNING'

    def observe(self, task_id, evidence_path):
        """Consume a trusted adapter's persisted observation; this does not probe a process.

        Adapter must report LIVE/TERMINAL/UNKNOWN, exact handle, observed_at,
        evidence (raw response text), and integer exit_code for TERMINAL.
        Observation timeouts MUST be UNKNOWN. Missing handle cannot prove termination.
        """
        obs = json.loads(Path(evidence_path).read_text(encoding='utf-8'))
        if obs.get('status') not in ('LIVE', 'TERMINAL', 'UNKNOWN') or not obs.get('evidence'):
            raise ValueError('invalid observation')
        stamp = datetime.fromisoformat(obs['observed_at'])
        if stamp.tzinfo is None or stamp > datetime.now(timezone.utc):
            raise ValueError('invalid observation time')
        if obs['status'] == 'TERMINAL' and type(obs.get('exit_code')) is not int:
            raise ValueError('terminal requires exit_code')
        with self.transaction() as s:
            t = s['tasks'][task_id]
            a = t['attempts'][-1]
            if a['execution'] not in ('RESERVED', 'RUNNING', 'UNKNOWN'):
                raise ValueError('execution already terminal')
            if a['handle'] is None or obs.get('handle') != a['handle']:
                raise ValueError('observation must identify bound handle')
            if a['observations'] and stamp <= datetime.fromisoformat(a['observations'][-1]['observed_at']):
                raise ValueError('stale observation')
            obs['source_sha256'] = digest(evidence_path)
            a['observations'].append(obs)
            a['execution'] = {'LIVE': 'RUNNING', 'TERMINAL': 'TERMINAL', 'UNKNOWN': 'UNKNOWN'}[obs['status']]
            if obs['status'] == 'TERMINAL':
                a['exit_code'] = obs['exit_code']
                if obs['exit_code'] != 0 and t['state'] != 'INVALIDATED':
                    self.transition(t, 'FAILED', 'verified terminal execution failure')
        return obs['status']

    def submit(self, task_id, artifacts, scientific_outcome):
        if scientific_outcome not in ('PASS', 'FAIL', 'CONDITIONAL', 'BLOCKED', 'NOT_RUN'):
            raise ValueError('invalid scientific outcome')
        with self.transaction() as s:
            t = s['tasks'][task_id]
            a = t['attempts'][-1]
            if t['state'] != 'RUNNING' or a['execution'] != 'TERMINAL' or a['exit_code'] != 0:
                raise ValueError('must have verified successful terminal execution')
            self._check_inputs(s, t)
            paths = [Path(p).resolve() for p in artifacts]
            directory = Path(a['directory'])
            if not paths or any(not p.is_relative_to(directory) or p.name in ('dispatch.json', 'result-manifest.json') for p in paths):
                raise ValueError('outputs must belong to this attempt')
            manifest = {'artifacts': {str(p): digest(p) for p in paths}, 'outcome': scientific_outcome}
            atomic(directory / 'result-manifest.json', manifest)
            a['manifest'] = manifest
            a['manifest_sha256'] = digest(directory / 'result-manifest.json')
            self.transition(t, 'REVIEW', 'outputs frozen for independent review')

    def review(self, task_id, reviewer, accepted, review_path):
        if type(accepted) is not bool or not reviewer:
            raise ValueError('explicit reviewer decision required')
        with self.transaction() as s:
            t = s['tasks'][task_id]
            if t['state'] != 'REVIEW' or reviewer == t['producer']:
                raise ValueError('independent review required')
            self._check_inputs(s, t)
            a = t['attempts'][-1]
            if digest(Path(a['directory']) / 'result-manifest.json') != a['manifest_sha256']:
                raise ValueError('manifest mutated')
            if any(digest(p) != h for p, h in a['manifest']['artifacts'].items()):
                raise ValueError('output mutated after submission')
            a['review'] = {'reviewer': reviewer, 'accepted': accepted,
                           'path': str(Path(review_path).resolve()), 'sha256': digest(review_path)}
            if accepted:
                # Conservatively invalidate every descendant, even before its first run.
                for key, v in s['tasks'].items():
                    if task_id in v['dependencies']:
                        self._invalidate(s, key, 'upstream accepted revision changed')
                t['accepted'] = a['id']
                self.transition(t, 'ACCEPTED', 'independent review accepted; science outcome remains separate')
            else:
                self.transition(t, 'REWORK', 'independent review rejected')
