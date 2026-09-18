import sys,os,runpy
from pathlib import Path
sys.dont_write_bytecode=True
allowed=(Path.cwd()/'independent-audit/round6-acceptance').resolve()
def guard(event,args):
 if event=='open':
  path,mode,flags=args
  if isinstance(path,(str,bytes,os.PathLike)) and ((isinstance(mode,str) and any(c in mode for c in 'wax+')) or (isinstance(flags,int) and flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC))):
   if not Path(path).resolve().is_relative_to(allowed): raise PermissionError('audit write boundary: '+str(path))
sys.addaudithook(guard)
runpy.run_path(str(allowed/'replay_redirected.py'),run_name='__main__')
