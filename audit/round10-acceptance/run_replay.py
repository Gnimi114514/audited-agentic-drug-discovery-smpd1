import sys, os, builtins, tempfile, runpy, json
from pathlib import Path
sys.dont_write_bytecode = True
root = Path(__file__).resolve().parents[2]
out = Path(__file__).resolve().parent
os.chdir(root)
tempfile.tempdir = str(out)
original_open = builtins.open
original_unlink = os.unlink
redirects = {str((root / p).resolve()): str(out / Path(p).name) for p in [
    'runs/benchmark-seeded/tmp_nested.json',
    'runs/benchmark-seeded/real_findings_replay_executed.json']}
def mapped(p):
    if isinstance(p, (str, bytes, os.PathLike)):
        return redirects.get(str(Path(p).resolve()), p)
    return p
def audit_open(p, *args, **kwargs):
    return original_open(mapped(p), *args, **kwargs)
def audit_unlink(p, *args, **kwargs):
    return original_unlink(mapped(p), *args, **kwargs)
builtins.open = audit_open
os.unlink = audit_unlink
def guard(event, args):
    if event == 'open':
        p, mode, flags = args
        writing = (isinstance(mode, str) and any(c in mode for c in 'wax+')) or (isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC))
        if writing and isinstance(p, (str, bytes, os.PathLike)) and not Path(p).resolve().is_relative_to(out):
            raise PermissionError('audit write boundary: ' + str(p))
    if event in ('os.remove', 'os.rmdir', 'os.mkdir', 'os.rename'):
        for p in args[:2] if event == 'os.rename' else args[:1]:
            if isinstance(p, (str, bytes, os.PathLike)) and not Path(p).resolve().is_relative_to(out):
                if event == 'os.mkdir' and Path(p).is_dir():
                    continue
                raise PermissionError('audit mutation boundary: ' + str(p))
sys.addaudithook(guard)
runpy.run_path(str(root / 'scripts/findings_replay_executed.py'), run_name='__main__')
