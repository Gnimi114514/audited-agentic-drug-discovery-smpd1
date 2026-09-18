"""Durable local subprocess receipts. Trusted filesystem; no scheduler or signing."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
import psutil
import threading
import ctypes
from ctypes import wintypes
import msvcrt


class JobChild:
    def __init__(self,k,handle,pid):self.k=k;self._handle=handle;self.pid=pid
    def poll(self):
        state=self.k.WaitForSingleObject(self._handle,0)
        if state==258:return None
        if state!=0:raise ctypes.WinError(ctypes.get_last_error())
        value=wintypes.DWORD()
        if not self.k.GetExitCodeProcess(self._handle,ctypes.byref(value)):raise ctypes.WinError(ctypes.get_last_error())
        return value.value
    def wait(self,timeout=2):
        state=self.k.WaitForSingleObject(self._handle,int(timeout*1000))
        if state==258:raise subprocess.TimeoutExpired('job child',timeout)
        if state!=0:raise ctypes.WinError(ctypes.get_last_error())
        return self.poll()
    def kill(self):
        if not self.k.TerminateProcess(self._handle,127):raise ctypes.WinError(ctypes.get_last_error())
    def close(self):self.k.CloseHandle(self._handle)


class WindowsJob:
    """No-breakaway Windows job; child assigned while suspended, before user code."""
    def __init__(self):
        self.k = ctypes.WinDLL('kernel32', use_last_error=True)
        self.k.CreateJobObjectW.argtypes=[ctypes.c_void_p,wintypes.LPCWSTR]
        self.k.CreateJobObjectW.restype=wintypes.HANDLE
        self.k.AssignProcessToJobObject.argtypes=[wintypes.HANDLE,wintypes.HANDLE]
        self.k.TerminateJobObject.argtypes=[wintypes.HANDLE,wintypes.UINT]
        self.k.QueryInformationJobObject.argtypes=[wintypes.HANDLE,ctypes.c_int,ctypes.c_void_p,wintypes.DWORD,ctypes.c_void_p]
        self.k.CloseHandle.argtypes=[wintypes.HANDLE]
        self.k.SetInformationJobObject.argtypes=[wintypes.HANDLE,ctypes.c_int,ctypes.c_void_p,wintypes.DWORD]
        self.handle=self.k.CreateJobObjectW(None,None)
        if not self.handle:raise ctypes.WinError(ctypes.get_last_error())
        class Basic(ctypes.Structure):
            _fields_=[('process_time',ctypes.c_longlong),('job_time',ctypes.c_longlong),('flags',wintypes.DWORD),('minimum',ctypes.c_size_t),('maximum',ctypes.c_size_t),('active_limit',wintypes.DWORD),('affinity',ctypes.c_size_t),('priority',wintypes.DWORD),('scheduling',wintypes.DWORD)]
        class IO(ctypes.Structure):
            _fields_=[(name,ctypes.c_ulonglong) for name in ('read_ops','write_ops','other_ops','read_bytes','write_bytes','other_bytes')]
        class Extended(ctypes.Structure):
            _fields_=[('basic',Basic),('io',IO),('process_memory',ctypes.c_size_t),('job_memory',ctypes.c_size_t),('peak_process_memory',ctypes.c_size_t),('peak_job_memory',ctypes.c_size_t)]
        limits=Extended();limits.basic.flags=0x00002000
        if not self.k.SetInformationJobObject(self.handle,9,ctypes.byref(limits),ctypes.sizeof(limits)):
            self.close();raise ctypes.WinError(ctypes.get_last_error())
    def spawn(self,argv,cwd,out,err):
        """Atomic job membership through PROC_THREAD_ATTRIBUTE_JOB_LIST (Windows 10+)."""
        class Startup(ctypes.Structure):
            _fields_=[('cb',wintypes.DWORD),('reserved',wintypes.LPWSTR),('desktop',wintypes.LPWSTR),('title',wintypes.LPWSTR),('x',wintypes.DWORD),('y',wintypes.DWORD),('xsize',wintypes.DWORD),('ysize',wintypes.DWORD),('xchars',wintypes.DWORD),('ychars',wintypes.DWORD),('fill',wintypes.DWORD),('flags',wintypes.DWORD),('show',wintypes.WORD),('reserved_size',wintypes.WORD),('reserved_data',ctypes.c_void_p),('stdin',wintypes.HANDLE),('stdout',wintypes.HANDLE),('stderr',wintypes.HANDLE)]
        class ExtendedStartup(ctypes.Structure):_fields_=[('startup',Startup),('attributes',ctypes.c_void_p)]
        class ProcessInfo(ctypes.Structure):_fields_=[('process',wintypes.HANDLE),('thread',wintypes.HANDLE),('pid',wintypes.DWORD),('tid',wintypes.DWORD)]
        k=self.k
        k.InitializeProcThreadAttributeList.argtypes=[ctypes.c_void_p,wintypes.DWORD,wintypes.DWORD,ctypes.POINTER(ctypes.c_size_t)]
        k.UpdateProcThreadAttribute.argtypes=[ctypes.c_void_p,wintypes.DWORD,ctypes.c_size_t,ctypes.c_void_p,ctypes.c_size_t,ctypes.c_void_p,ctypes.c_void_p]
        k.DeleteProcThreadAttributeList.argtypes=[ctypes.c_void_p]
        k.CreateProcessW.argtypes=[wintypes.LPCWSTR,wintypes.LPWSTR,ctypes.c_void_p,ctypes.c_void_p,wintypes.BOOL,wintypes.DWORD,ctypes.c_void_p,wintypes.LPCWSTR,ctypes.c_void_p,ctypes.POINTER(ProcessInfo)]
        k.GetExitCodeProcess.argtypes=[wintypes.HANDLE,ctypes.POINTER(wintypes.DWORD)]
        k.WaitForSingleObject.argtypes=[wintypes.HANDLE,wintypes.DWORD]
        k.WaitForSingleObject.restype=wintypes.DWORD
        k.TerminateProcess.argtypes=[wintypes.HANDLE,wintypes.UINT]
        k.ResumeThread.argtypes=[wintypes.HANDLE]
        k.ResumeThread.restype=wintypes.DWORD
        size=ctypes.c_size_t()
        k.InitializeProcThreadAttributeList(None,1,0,ctypes.byref(size))
        buffer=ctypes.create_string_buffer(size.value)
        if not k.InitializeProcThreadAttributeList(buffer,1,0,ctypes.byref(size)):raise ctypes.WinError(ctypes.get_last_error())
        try:
            jobs=(wintypes.HANDLE*1)(self.handle)
            if not k.UpdateProcThreadAttribute(buffer,0,0x0002000D,ctypes.byref(jobs),ctypes.sizeof(jobs),None,None):raise ctypes.WinError(ctypes.get_last_error())
            si=ExtendedStartup();si.startup.cb=ctypes.sizeof(si);si.startup.flags=0x00000100;si.attributes=ctypes.cast(buffer,ctypes.c_void_p)
            with open(os.devnull,'rb') as inp:
                handles=[msvcrt.get_osfhandle(f.fileno()) for f in (inp,out,err)]
                for h in handles:os.set_handle_inheritable(h,True)
                si.startup.stdin,si.startup.stdout,si.startup.stderr=handles
                info=ProcessInfo()
                try:
                    if not k.CreateProcessW(None,ctypes.create_unicode_buffer(subprocess.list2cmdline(argv)),None,None,True,0x00080000|0x08000000|0x4,None,cwd,ctypes.byref(si),ctypes.byref(info)):
                        raise ctypes.WinError(ctypes.get_last_error())
                finally:
                    for h in handles:os.set_handle_inheritable(h,False)
            child=JobChild(k,info.process,info.pid)
            child.identity=identity(info.pid)
            try:
                if k.ResumeThread(info.thread)==0xFFFFFFFF:raise ctypes.WinError(ctypes.get_last_error())
            finally:k.CloseHandle(info.thread)
            return child
        finally:k.DeleteProcThreadAttributeList(buffer)
    def active(self):
        class Accounting(ctypes.Structure):
            _fields_=[('user',ctypes.c_longlong),('kernel',ctypes.c_longlong),('period_user',ctypes.c_longlong),('period_kernel',ctypes.c_longlong),('faults',wintypes.DWORD),('total',wintypes.DWORD),('active',wintypes.DWORD),('terminated',wintypes.DWORD)]
        data=Accounting()
        if not self.k.QueryInformationJobObject(self.handle,1,ctypes.byref(data),ctypes.sizeof(data),None):
            raise ctypes.WinError(ctypes.get_last_error())
        return data.active
    def kill(self):
        if not self.k.TerminateJobObject(self.handle,124):raise ctypes.WinError(ctypes.get_last_error())
    def close(self):self.k.CloseHandle(self.handle)


def stamp():
    return datetime.now(timezone.utc).isoformat()


def atomic(path, data):
    temp = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    with open(temp, 'x', encoding='utf-8') as f:
        json.dump(data, f, allow_nan=False)
        f.flush(); os.fsync(f.fileno())
    os.replace(temp, path)


def command_digest(argv, cwd, timeout):
    return hashlib.sha256(json.dumps({'argv':argv, 'cwd':cwd, 'wall_timeout':timeout}, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def identity(pid):
    p = psutil.Process(pid)
    return {'pid':p.pid, 'birth':p.create_time()}


def matches(info):
    try:
        p = psutil.Process(info['pid'])
        return p.create_time() == info['birth'] and p.is_running() and p.status() != psutil.STATUS_ZOMBIE
    except (psutil.Error, KeyError, TypeError):
        return False


def read_intent(root):
    d = json.loads((root / 'intent.json').read_text(encoding='utf-8'))
    if not isinstance(d,dict) or d.get('schema')!=1 or not isinstance(d.get('argv'),list) or not d['argv'] or any(not isinstance(a,str) or not a for a in d['argv']):
        raise ValueError('invalid intent schema')
    if not isinstance(d.get('cwd'),str) or type(d.get('wall_timeout')) not in (int,float) or not 0<d['wall_timeout']<=3600:
        raise ValueError('invalid command specification')
    if d['digest'] != command_digest(d['argv'], d['cwd'], d['wall_timeout']):
        raise ValueError('command digest mismatch')
    if not isinstance(d['token'], str) or len(d['token']) != 32:
        raise ValueError('invalid token')
    return d


def launch(directory, argv, cwd, wall_timeout=10):
    """An existing directory is never reused, including incomplete launch intent."""
    if os.name != 'nt': raise RuntimeError('verified job containment currently requires Windows')
    if not isinstance(argv, list) or not argv or any(not isinstance(a,str) or not a for a in argv):
        raise ValueError('nonempty string argv required')
    if type(wall_timeout) not in (int,float) or not 0 < wall_timeout <= 3600:
        raise ValueError('wall timeout must be within (0,3600] seconds')
    cwd = str(Path(cwd).resolve(strict=True))
    if not Path(cwd).is_dir(): raise ValueError('cwd must be directory')
    root = Path(directory).resolve()
    root.mkdir(parents=True, exist_ok=False)
    token = uuid.uuid4().hex
    intent = {'schema':1,'token':token,'argv':argv,'cwd':cwd,'wall_timeout':wall_timeout,
              'digest':command_digest(argv,cwd,wall_timeout),'created_at':stamp()}
    atomic(root / 'intent.json', intent)
    # Intent is durable before creating a process. Any subsequent failure is UNKNOWN.
    with open(root/'supervisor.stdout','ab') as out, open(root/'supervisor.stderr','ab') as err:
        options = {'creationflags':subprocess.CREATE_NO_WINDOW} if os.name=='nt' else {'start_new_session':True}
        supervisor=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'_worker',str(root),token],
                         stdin=subprocess.DEVNULL,stdout=out,stderr=err,close_fds=True,**options)
        threading.Thread(target=supervisor.wait,daemon=True).start()
    return {'provider':'local-durable-v1','id':token,'directory':str(root),'digest':intent['digest']}


def observe(handle):
    """Missing process or receipt is UNKNOWN, never evidence of terminal state."""
    if not isinstance(handle,dict):handle={}
    base = {'handle':{'provider':handle.get('provider'),'id':handle.get('id')},
            'observed_at':stamp(),'status':'UNKNOWN','evidence':'unverified durable state'}
    try:
        if handle['provider'] != 'local-durable-v1': raise ValueError('provider mismatch')
        root=Path(handle['directory']); intent=read_intent(root)
        if intent['token']!=handle['id'] or intent['digest']!=handle['digest']:
            raise ValueError('handle mismatch')
        receipt_path=root/'terminal.json'
        if receipt_path.exists():
            r=json.loads(receipt_path.read_text())
            if not isinstance(r,dict) or r.get('schema')!=1:
                raise ValueError('invalid receipt schema')
            if r['token']!=intent['token'] or r['digest']!=intent['digest'] or type(r['exit_code']) is not int or r['cleanup_complete'] is not True:
                raise ValueError('invalid terminal receipt')
            if r['status']!='TERMINAL' or not r['finished_at'] or r.get('containment')!='windows-job-no-breakaway':
                raise ValueError('incomplete receipt')
            finished=datetime.fromisoformat(r['finished_at'])
            if finished.tzinfo is None or finished>datetime.now(timezone.utc):
                raise ValueError('invalid receipt timestamp')
            base.update(status='TERMINAL',exit_code=r['exit_code'],evidence=r)
            return base
        worker=json.loads((root/'worker.json').read_text())
        if not isinstance(worker,dict):raise ValueError('invalid worker record')
        if worker['token']!=intent['token'] or worker['digest']!=intent['digest']:
            raise ValueError('worker identity mismatch')
        if matches(worker['identity']):
            cmd=psutil.Process(worker['identity']['pid']).cmdline()
            if '_worker' not in cmd or intent['token'] not in cmd or str(root) not in cmd:
                raise ValueError('live process command identity mismatch')
            base.update(status='LIVE',evidence={'worker':worker,'verified_cmdline':cmd})
        else:
            base['evidence']='No matching live supervisor and no valid terminal receipt; investigate, do not relaunch'
    except (OSError,ValueError,KeyError,TypeError,AttributeError,psutil.Error) as e:
        base['evidence']='UNKNOWN: '+str(e)
    return base


def worker(directory, token):
    root=Path(directory).resolve(); intent=read_intent(root)
    if token!=intent['token']: raise ValueError('worker token mismatch')
    # Never steal this claim: a crashed worker is not permission for duplicate execution.
    claim=os.open(root/'worker.claim',os.O_WRONLY|os.O_CREAT|os.O_EXCL)
    os.close(claim)
    atomic(root/'worker.json',{'token':token,'digest':intent['digest'],'identity':identity(os.getpid()),'started_at':stamp()})
    started=time.monotonic(); timed_out=False; cleanup=False
    job=WindowsJob()
    p=None
    try:
        with open(root/'command.stdout','xb') as out,open(root/'command.stderr','xb') as err:
            p=job.spawn(intent['argv'],intent['cwd'],out,err)
            atomic(root/'child.json',{'token':token,'digest':intent['digest'],'identity':p.identity})
            while job.active() and time.monotonic()-started < intent['wall_timeout']:
                time.sleep(.02)
            if job.active():
                timed_out=True; job.kill()
                deadline=time.monotonic()+2
                while job.active() and time.monotonic()<deadline:time.sleep(.02)
            cleanup=job.active()==0
            code=124 if timed_out else p.wait(timeout=1)
    except Exception as e:
        code=127
        # A failed launch/containment operation cannot prove whole-job termination.
        cleanup=False
        if p is not None and p.poll() is None:
            p.kill()
            p.wait(timeout=2)
        atomic(root/'launch-error.json',{'error':str(e),'token':token})
    finally:
        job.close()
        if p is not None:p.close()
    atomic(root/'terminal.json',{'schema':1,'status':'TERMINAL','token':token,'digest':intent['digest'],
        'exit_code':code,'timed_out':timed_out,'cleanup_complete':cleanup,
        'elapsed_seconds':time.monotonic()-started,'finished_at':stamp(),'containment':'windows-job-no-breakaway'})


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('mode',choices=['_worker','observe']); parser.add_argument('path'); parser.add_argument('token',nargs='?')
    a=parser.parse_args()
    if a.mode=='_worker': worker(a.path,a.token)
    else: print(json.dumps(observe(json.loads(Path(a.path).read_text()))))

if __name__=='__main__': main()
