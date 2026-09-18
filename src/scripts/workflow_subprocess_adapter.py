"""Observe actual local subprocesses; lost in-memory handles remain UNKNOWN.

This adapter is deliberately not an OS process-recovery service. Never reconstruct a
live handle from a PID or an on-disk RUNNING flag. Workflow reservation precedes launch.
"""
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import uuid


class SubprocessAdapter:
    def __init__(self):
        self._processes = {}

    def _entry(self, handle):
        if (not isinstance(handle, dict) or set(handle) != {'provider', 'id'}
                or any(not isinstance(v, str) or not v for v in handle.values())):
            raise ValueError('provider and nonempty string id required')
        return self._processes.get(handle['id']) if handle['provider'] == 'local-popen-v1' else None

    def launch(self, argv, cwd, output_directory):
        if not isinstance(argv, list) or not argv or any(not isinstance(x, str) or not x for x in argv):
            raise ValueError('nonempty argument vector required; shell commands are not accepted')
        folder = Path(output_directory).resolve()
        folder.mkdir(parents=True, exist_ok=True)
        token = uuid.uuid4().hex
        handle = {'provider': 'local-popen-v1', 'id': token}
        stdout = (folder / (token + '-stdout.log')).open('xb')
        try:
            stderr = (folder / (token + '-stderr.log')).open('xb')
        except BaseException:
            stdout.close()
            raise
        try:
            process = subprocess.Popen(argv, cwd=cwd, stdout=stdout, stderr=stderr, shell=False)
        except BaseException:
            stdout.close()
            stderr.close()
            raise
        self._processes[token] = (process, stdout, stderr)
        return handle

    def observe(self, handle, evidence_path):
        entry = self._entry(handle)
        obs = {'handle': handle, 'observed_at': datetime.now(timezone.utc).isoformat()}
        if entry is None:
            obs.update(status='UNKNOWN', evidence='No owned Popen handle exists in this adapter instance; no OS liveness inference made.')
        else:
            process, stdout, stderr = entry
            code = process.poll()
            if code is None:
                obs.update(status='LIVE', evidence=f'Owned Popen.poll() returned None for PID {process.pid}.')
            else:
                stdout.close()
                stderr.close()
                obs.update(status='TERMINAL', exit_code=code,
                           evidence=f'Owned Popen.poll() returned exit code {code} for PID {process.pid}.')
        with Path(evidence_path).open('x', encoding='utf-8') as stream:
            json.dump(obs, stream, indent=2)
        return obs

    def wait(self, handle, timeout):
        """An observation timeout does not kill or relaunch the subprocess."""
        entry = self._entry(handle)
        if not isinstance(timeout, (int, float)) or isinstance(timeout, bool) or not 0 <= timeout <= 60:
            raise ValueError('bounded wait of at most 60 seconds required')
        if entry is None:
            return None
        process, stdout, stderr = entry
        try:
            code = process.wait(timeout=timeout)
            stdout.close()
            stderr.close()
            return code
        except subprocess.TimeoutExpired:
            return None
