import json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
def check(path,sha,size=None):
    p=ROOT/path
    actual=hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None
    n=p.stat().st_size if p.is_file() else None
    return dict(path=path,expected_sha256=sha,actual_sha256=actual,expected_bytes=size,actual_bytes=n,match=actual==sha and (size is None or n==size))
main=json.loads((ROOT/'audit_manifest.json').read_text())
checks={s:[check(p,v['sha256'],v.get('bytes')) for p,v in entries.items()] for s,entries in main['sections'].items()}
nest={}
for name in ('handoff-r4-mech.json','handoff-r4-evidence.json'):
    j=json.loads((ROOT/'runs/audit-20260913'/name).read_text())
    nest[name]=[check(v['path'],v['sha256']) for v in j['artifacts']]
out=dict(root_manifest_sha256=hashlib.sha256((ROOT/'audit_manifest.json').read_bytes()).hexdigest(),root_schema_keys=list(main),root_section_counts={s:len(v) for s,v in checks.items()},claimed_four_levels_present=False,root_checks=checks,nested_checks=nest,root_summary=dict(total=sum(map(len,checks.values())),matched=sum(v['match'] for s in checks.values() for v in s)),nested_summary={k:dict(total=len(v),matched=sum(x['match'] for x in v)) for k,v in nest.items()})
(OUT/'c3_evidence.json').write_text(json.dumps(out,indent=2))
print(json.dumps({k:v for k,v in out.items() if k not in ('root_checks','nested_checks')},indent=2))
print('MISMATCHES',json.dumps([v for vs in list(checks.values())+list(nest.values()) for v in vs if not v['match']],indent=2))
