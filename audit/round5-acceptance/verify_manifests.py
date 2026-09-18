import hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''): h.update(b)
    return h.hexdigest()
m=json.loads((ROOT/'audit_manifest.json').read_text(encoding='utf-8'))
rows=[]
for level,entries in m['levels'].items():
    for e in entries:
        p=ROOT/e['path']; actual=digest(p) if p.is_file() else None
        rows.append(dict(level=level,**e,actual_sha256=actual,actual_bytes=p.stat().st_size if p.exists() else None,hash_match=actual==e['sha256'],size_match=p.exists() and p.stat().st_size==e.get('bytes',p.stat().st_size),self_reference=p.resolve()==(ROOT/'audit_manifest.json').resolve()))
checker=Path('C:/Users/Gnimi/.agents/skills/ai-drug-discovery-team/scripts/check_handoff.py')
handoffs=[]
for name in ['reports','evidence']:
    cmd=[sys.executable,'-B',str(checker),f'runs/audit-20260913/handoff-r6-{name}.json','--root',str(ROOT),'--require','artifacts']
    r=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,encoding='utf-8')
    handoffs.append(dict(command=cmd,exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr))
result=dict(root_sha256=digest(ROOT/'audit_manifest.json'),levels=list(m['levels']),entries=rows,total=len(rows),hash_matches=sum(x['hash_match'] for x in rows),size_matches=sum(x['size_match'] for x in rows),self_reference=any(x['self_reference'] for x in rows),handoffs=handoffs)
(OUT/'manifest_checks.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='entries'},indent=2))
