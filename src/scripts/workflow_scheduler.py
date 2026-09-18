"""Single-job trusted-local scheduler foundation; independent review remains external."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import types
import uuid
from contextlib import contextmanager


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def write(p,d):
    temp=p.with_name(p.name+'.'+uuid.uuid4().hex+'.tmp')
    with open(temp,'x',encoding='utf-8') as f:
        json.dump(d,f,indent=2,allow_nan=False);f.flush();os.fsync(f.fileno())
    os.replace(temp,p)


def load(root):
    root=Path(root).resolve(); manifest=read(root/'snapshot-manifest.json')
    for relative,digest in manifest.items():
        if sha(root/relative)!=digest:raise ValueError('snapshot drift: '+relative)
    if sha(__file__)!=manifest['snapshots/workflow_scheduler.py']:
        raise ValueError('scheduler source differs from frozen revision')
    modules=[]
    for name in ('workflow_state','workflow_durable_process'):
        p=root/'snapshots'/(name+'.py');mod=types.ModuleType(name);mod.__file__=str(p)
        exec(compile(p.read_bytes(),str(p),'exec'),mod.__dict__);modules.append(mod)
    return read(root/'spec.json'),modules[0],modules[1]


def create(directory,spec):
    """Spec is trusted code configuration, not a hostile-code sandbox."""
    if not isinstance(spec,dict) or not isinstance(spec.get('tasks'),list) or not spec['tasks']:
        raise ValueError('nonempty tasks required')
    seen=set()
    for t in spec['tasks']:
        key=t['id']
        if not re.fullmatch('[A-Za-z0-9_-]+',key) or key in seen:raise ValueError('invalid task id')
        if any(d not in seen for d in t.get('dependencies',[])):raise ValueError('tasks must be topologically ordered')
        seen.add(key)
        if not t.get('argv') or any(not isinstance(x,str) for x in t['argv']):raise ValueError('argv required')
        if not Path(t['cwd']).is_dir() or not Path(t['argv'][0]).is_file():raise ValueError('absolute executable/cwd required')
        if not Path(t['cwd']).is_absolute() or not Path(t['argv'][0]).is_absolute():raise ValueError('absolute executable/cwd required')
        if not t.get('inputs') or any(not Path(p).is_file() for p in t['inputs']):raise ValueError('input files required')
        if not t.get('outputs') or t.get('result') not in t['outputs']:raise ValueError('result must be declared output')
        for p in t['outputs']:
            if Path(p).is_absolute() or '..' in Path(p).parts:raise ValueError('output must be attempt-relative')
        if type(t.get('wall_timeout')) not in (float,int) or not 0<t['wall_timeout']<=3600:raise ValueError('bounded wall timeout required')
    root=Path(directory).resolve();root.mkdir(parents=True,exist_ok=False)
    snap=root/'snapshots';snap.mkdir()
    for name in ('workflow_state.py','workflow_durable_process.py','workflow_scheduler.py'):
        shutil.copyfile(Path(__file__).resolve().parent/name,snap/name)
    write(root/'spec.json',spec)
    pins={}
    frozen_inputs=snap/'inputs';frozen_inputs.mkdir()
    for t in spec['tasks']:
        for p in t['inputs']+[t['argv'][0]]:
            p=str(Path(p).resolve());pins[p]=sha(p)
            frozen=frozen_inputs/pins[p]
            if not frozen.exists():shutil.copyfile(p,frozen)
    write(root/'input-pins.json',pins)
    write(root/'snapshot-manifest.json',{str(p.relative_to(root)).replace('\\','/'):sha(p) for p in [p for p in snap.rglob('*') if p.is_file()]+[root/'spec.json',root/'input-pins.json']})
    spec,st,_=load(root);w=st.Workflow(root/'workflow',spec['coordinator'])
    for t in spec['tasks']:
        w.add(t['id'],t['producer'],t.get('dependencies',[]),max_attempts=t.get('max_attempts',3),
              allowed_outcomes=t.get('allowed_outcomes',['PASS']),exploratory_reason=t.get('exploratory_reason'),purpose=t.get('purpose','scientific_stage'))
    return {'run':str(root),'status':'CREATED'}


@contextmanager
def tick_lock(root):
    p=root/'.tick.lock';fd=os.open(p,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
    try:yield
    finally:os.close(fd);p.unlink()


def command(t,a,state):
    directory=Path(a['directory'])
    def expand(text):
        text=text.replace('{attempt}',str(directory))
        def dep(match):
            key,relative=match.group(1),match.group(2)
            if key not in t.get('dependencies',[]):raise ValueError('undeclared command dependency')
            task=state['tasks'][key]
            if task['accepted'] is None:raise ValueError('unaccepted command dependency')
            attempt=task['attempts'][-1];p=(Path(attempt['directory'])/relative).resolve()
            if str(p) not in attempt['manifest']['artifacts']:raise ValueError('dependency file not accepted artifact')
            return str(p)
        return re.sub(r'\{dep:([^:}]+):([^}]+)\}',dep,text)
    return [expand(x) for x in t['argv']]


def tick(directory):
    root=Path(directory).resolve()
    with tick_lock(root):
        spec,st,adapter=load(root);w=st.Workflow(root/'workflow',spec['coordinator']);state=w.read()
        # Verify every consumed observation remains present and hash-identical.
        for task in state['tasks'].values():
            for a in task['attempts']:
                files=list(Path(a['directory']).glob('observation-*.json'))
                hashes={sha(p) for p in files}
                consumed={o['source_sha256'] for o in a['observations']}
                if consumed-hashes:raise ValueError('consumed observation drift')
                if hashes-consumed:raise ValueError('unconsumed observation requires explicit reconciliation')
        active=[(k,t) for k,t in state['tasks'].items() if t['attempts'] and t['attempts'][-1]['execution'] in ('RESERVED','RUNNING','UNKNOWN')]
        if len(active)>1:raise ValueError('single-job invariant violated')
        if active:
            key,t=active[0];a=t['attempts'][-1];p=Path(a['directory']);job=p/'job'
            if not (job/'intent.json').exists():return {'status':'UNKNOWN','task':key,'reason':'reserved without launch intent; no relaunch'}
            try:
                intent=adapter.read_intent(job)
                definition=next(item for item in spec['tasks'] if item['id']==key)
                expected_argv=command(definition,a,state)
                expected_digest=adapter.command_digest(expected_argv,str(Path(definition['cwd']).resolve()),definition['wall_timeout'])
                saved_command=read(p/'command.json')
                if intent['digest']!=expected_digest or saved_command!={'argv':expected_argv,'cwd':definition['cwd'],'wall_timeout':definition['wall_timeout']}:
                    raise ValueError('launch intent differs from frozen task command')
                handle={'provider':'local-durable-v1','id':intent['token'],'directory':str(job),'digest':intent['digest']}
                short={'provider':handle['provider'],'id':handle['id']}
                if a['handle'] is not None and a['handle']!=short:raise ValueError('bound handle mismatch')
                if (p/'handle.json').exists():
                    if read(p/'handle.json')!=handle:raise ValueError('persisted handle mismatch')
                else:write(p/'handle.json',handle)
                if a['handle'] is None:w.bind_handle(key,{'provider':handle['provider'],'id':handle['id']})
                obs=adapter.observe(handle)
            except (ValueError,OSError,KeyError,TypeError):return {'status':'UNKNOWN','task':key,'reason':'unverifiable launch intent'}
            evidence=p/('observation-'+uuid.uuid4().hex+'.json');write(evidence,obs);w.observe(key,evidence)
            if obs['status']!='TERMINAL':return {'status':obs['status'],'task':key}
            if obs['exit_code']!=0:return {'status':'FAILED','task':key,'exit_code':obs['exit_code']}
            state=w.read()
        # Successful terminal execution may have been persisted before a prior tick crashed.
        for t in spec['tasks']:
            task=state['tasks'][t['id']]
            if task['state']=='RUNNING' and task['attempts'][-1]['execution']=='TERMINAL':
                a=task['attempts'][-1];p=Path(a['directory'])
                try:result=read(p/t['result'])
                except (OSError,ValueError):return {'status':'BLOCKED','task':t['id'],'reason':'missing/malformed scientific result; no inferred PASS'}
                if not isinstance(result,dict) or result.get('scientific_outcome') not in ('PASS','FAIL','CONDITIONAL','BLOCKED','NOT_RUN'):
                    return {'status':'BLOCKED','task':t['id'],'reason':'missing explicit scientific_outcome; no inferred PASS'}
                provenance=[p/'command.json',p/'handle.json']+list(p.glob('observation-*.json'))+[x for x in (p/'job').rglob('*') if x.is_file()]
                w.submit(t['id'],[p/x for x in t['outputs']]+provenance,result['scientific_outcome'])
                return {'status':'REVIEW','task':t['id'],'scientific_outcome':result['scientific_outcome']}
        # Review must be performed externally; do not accept or retry failed/rejected work.
        blockers={}
        for t in spec['tasks']:
            task=state['tasks'][t['id']]
            if task['state'] not in ('PENDING','INVALIDATED','READY'):continue
            if any(state['tasks'][d]['accepted'] is None for d in t.get('dependencies',[])):continue
            denied=[d for d in t.get('dependencies',[]) if state['tasks'][d]['attempts'][-1]['manifest']['outcome'] not in t.get('allowed_outcomes',['PASS'])]
            if denied:
                blockers[t['id']]={'reason':'dependency scientific outcome does not authorize stage','dependencies':denied}
                continue
            for p,h in read(root/'input-pins.json').items():
                if sha(p)!=h:raise ValueError('pinned external input changed: '+p)
            if task['state']!='READY':
                w.prepare(t['id'],t['inputs']+[t['argv'][0],str(root/'spec.json')]+[str(p) for p in (root/'snapshots').glob('*.py')])
            a=w.reserve(t['id']);argv=command(t,a,w.read());p=Path(a['directory'])
            write(p/'command.json',{'argv':argv,'cwd':t['cwd'],'wall_timeout':t['wall_timeout']})
            handle=adapter.launch(p/'job',argv,t['cwd'],t['wall_timeout'])
            write(p/'handle.json',handle);w.bind_handle(t['id'],{'provider':handle['provider'],'id':handle['id']})
            return {'status':'RUNNING','task':t['id'],'attempt':a['id']}
        return {'status':'WAITING_REVIEW_OR_DEPENDENCIES','tasks':{k:t['state'] for k,t in state['tasks'].items()},'blockers':blockers}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['create','tick']);p.add_argument('run');p.add_argument('--spec');a=p.parse_args()
    print(json.dumps(create(a.run,read(a.spec)) if a.mode=='create' else tick(a.run)))
