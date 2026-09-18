from pathlib import Path
import json,hashlib,subprocess,sys
root=Path.cwd(); out=root/'independent-audit/round6-acceptance'
m=json.loads((root/'audit_manifest.json').read_text()); checks=[]
for level, entries in m['levels'].items():
 for e in entries:
  p=root/e['path']; h=hashlib.file_digest(p.open('rb'),'sha256').hexdigest(); size=p.stat().st_size
  checks.append(dict(level=level,**e,actual_sha256=h,actual_bytes=size,passed=h==e['sha256'] and size==e['bytes']))
r={'entries':checks,'counts':{k:len(v) for k,v in m['levels'].items()},'passed':sum(e['passed'] for e in checks),'handoffs':[]}
for name in ['reports','evidence']:
 p=subprocess.run([sys.executable,'C:/Users/Gnimi/.agents/skills/ai-drug-discovery-team/scripts/check_handoff.py',f'runs/audit-20260913/handoff-r6-{name}.json','--root',str(root)],capture_output=True,text=True)
 r['handoffs'].append(dict(name=name,exit_code=p.returncode,stdout=p.stdout,stderr=p.stderr))
(out/'manifest_checks.json').write_text(json.dumps(r,indent=2))
print(json.dumps({**r,'entries':[x for x in checks if not x['passed']]},indent=2))
# Run pocket source with only output destination replaced.
s=(root/'scripts/pocket_residence_r5fix.py').read_text()
s=s.replace("{WORK}/runs/audit-20260913/tasks/sim-02/attempt-1/pocket_residence_r5fix_summary.json","{WORK}/independent-audit/round6-acceptance/pocket_rerun.json")
(out/'pocket_redirected.py').write_text(s)
# Execute replay without editing its computations; redirect file writes/readbacks and unlink.
s=(root/'scripts/findings_replay_executed.py').read_text(encoding='utf-8')
for old,new in [('runs/benchmark-seeded/real_findings_replay_executed.json','independent-audit/round6-acceptance/replay_results.json'),('runs/benchmark-seeded/tmp_nested.json','independent-audit/round6-acceptance/tmp_nested.json')]: s=s.replace(old,new)
prefix="import tempfile, sys\nsys.dont_write_bytecode=True\ntempfile.tempdir='independent-audit/round6-acceptance'\n"
(out/'replay_redirected.py').write_text(prefix+s+"\nprint('R1-10 computed but not recorded:',r_lenient)\n",encoding='utf-8')
