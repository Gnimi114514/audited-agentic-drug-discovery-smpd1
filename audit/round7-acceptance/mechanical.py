from pathlib import Path
import json, hashlib, subprocess, sys, ast
root=Path.cwd(); out=root/'independent-audit/round7-acceptance'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
m=json.loads((root/'audit_manifest.json').read_text())
entries=[]
for level, rows in m['levels'].items():
 for r in rows:
  p=root/r['path']; actual=sha(p) if p.exists() else None
  entries.append(dict(level=level,**r,actual_sha256=actual,actual_bytes=p.stat().st_size if p.exists() else None,hash_match=actual==r['sha256'],size_match=p.exists() and p.stat().st_size==r.get('bytes',p.stat().st_size)))
checker=Path('C:/Users/Gnimi/.agents/skills/ai-drug-discovery-team/scripts/check_handoff.py')
handoffs=[]
for name in ['reports','evidence']:
 p=f'runs/audit-20260913/handoff-r7-{name}.json'
 cmd=[sys.executable,'-B',str(checker),p,'--root',str(root),'--require','artifacts']
 r=subprocess.run(cmd,capture_output=True,text=True)
 handoffs.append(dict(path=p,command=cmd,exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr))
result=dict(level_counts={k:len(v) for k,v in m['levels'].items()},entry_count=len(entries),self_reference=any(r['path']=='audit_manifest.json' for r in entries),entries=entries,handoffs=handoffs)
(out/'manifest_checks.json').write_text(json.dumps(result,indent=2))
source=(root/'scripts/findings_replay_executed.py').read_text(encoding='utf-8')
tree=ast.parse(source)
# Execute only the actual R1-10 parser and assignment block; no network/cache/producer writes.
start=source.index('import math'); end=source.index('# R1-11')
ns={}; exec(source[start:end],ns)
j=json.loads((root/'runs/benchmark-seeded/real_findings_replay_executed.json').read_text())
replay=dict(independent_executed_R1_10_A=ns['r_lenient'],records=len(j['replays']),actual_detected=sum(r['detected'] is True for r in j['replays']),actual_delegated=sum(r['detected'] is None for r in j['replays']),stored_summary=j['summary'],R1_10=[r for r in j['replays'] if r['id']=='R1-10'],count_before_append=source.index('detected_n =')<source.index("results['replays'].append({'id': 'R1-10'"),hardcoded_residuals=['R1-2 literal v1/heat_first','R3-1 literal observation and True','R3-6 literal vals'])
(out/'replay_checks.json').write_text(json.dumps(replay,indent=2))
print(json.dumps({'levels':result['level_counts'],'count':len(entries),'mismatches':[r for r in entries if not r['hash_match'] or not r['size_match']],'handoffs':handoffs,'replay':replay},indent=2))
