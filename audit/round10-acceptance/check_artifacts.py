from pathlib import Path
import json, hashlib, subprocess, sys, ast
root=Path(__file__).resolve().parents[2]; out=Path(__file__).resolve().parent
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()
manifest=json.loads((root/'audit_manifest.json').read_text())
checks=[]
for level,entries in manifest['levels'].items():
    for e in entries:
        p=root/e['path']; actual=sha(p) if p.exists() else None
        checks.append(dict(level=level,**e,actual_sha256=actual,actual_bytes=p.stat().st_size if p.exists() else None,passed=actual==e['sha256'] and p.stat().st_size==e['bytes']))
handoffs=[]
checker=Path('C:/Users/Gnimi/.agents/skills/ai-drug-discovery-team/scripts/check_handoff.py')
for p in sorted((root/'runs/audit-20260913').glob('handoff-r10-*.json')):
    cmd=[sys.executable,'-B',str(checker),str(p),'--root',str(root),'--require','artifacts']
    r=subprocess.run(cmd,capture_output=True,text=True)
    handoffs.append({'command':cmd,'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr})
paper=[]
for section,entries in json.loads((root/'paper/manuscript_revision_manifest.json').read_text())['sections'].items():
    for path,e in entries.items():
        p=root/path; actual=sha(p) if p.exists() else None
        paper.append({'path':path,'expected_sha256':e['sha256'],'actual_sha256':actual,'passed':actual==e['sha256']})
result={'level_counts':{k:len(v) for k,v in manifest['levels'].items()},'total':len(checks),'passed':sum(c['passed'] for c in checks),'entries':checks,'handoffs':handoffs,'supplementary_paper_manifest':paper}
(out/'manifest_checks.json').write_text(json.dumps(result,indent=2))
src=(root/'scripts/findings_replay_executed.py').read_text(encoding='utf8'); lines=src.splitlines()
saved=json.loads((root/'runs/benchmark-seeded/real_findings_replay_executed.json').read_text())
replay={'source_sha256':sha(root/'scripts/findings_replay_executed.py'),'entries':len(saved['replays']),'actual_true':sum(r['detected'] is True for r in saved['replays']),'actual_null':sum(r['detected'] is None for r in saved['replays']),'saved_summary':saved['summary'],'count_line':next(i for i,l in enumerate(lines,1) if l.startswith('detected_n =')),'append_line':next(i for i,l in enumerate(lines,1) if "results['replays'].append({'id': 'R1-10'" in l),'literal_evidence':{str(i):l for i,l in enumerate(lines,1) if any(s in l for s in ['v1 =','heat_first =','True, \'retired','vals =','4.39 vs'])},'reads_bound_run_log':any(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='open' and any(isinstance(a,ast.Constant) and a.value=='md/bound_run.log' for a in n.args) for n in ast.walk(ast.parse(src)))}
(out/'replay_checks.json').write_text(json.dumps(replay,indent=2))
section=(root/'paper/manuscript_results_discussion.md').read_text(encoding='utf8').split('## 3. Results',1)[1].split('## 4. Discussion',1)[0]
assembly=(root/'paper/MANUSCRIPT_DRAFT_v1.md').read_text(encoding='utf8')
reports={'requested_assembled_path_exists':(root/'paper/manuscript_MANUSCRIPT_DRAFT_v1.md').exists(),'actual_assembled_path':'paper/MANUSCRIPT_DRAFT_v1.md','results_section_exactly_synced':section in assembly,'matches':{}}
for name in ['final-report.md','hit-report.md','structure-analysis.md','paper/manuscript_results_discussion.md','paper/MANUSCRIPT_DRAFT_v1.md']:
    reports['matches'][name]=[{'line':i,'text':l} for i,l in enumerate((root/name).read_text(encoding='utf8').splitlines(),1) if any(s in l for s in ['fixed in advance','post hoc','pre-specified','no ensemble docking','yields ≤','persist in every','414/620','11/620','23/620','COM-imaged RMSD 3','3.1 ns','mean 1.847','max 2.370'])]
(out/'report_checks.json').write_text(json.dumps(reports,indent=2,ensure_ascii=False))
print(json.dumps({'manifest_passed':result['passed'],'total':len(checks),'failures':[e['path'] for e in checks if not e['passed']],'handoff_exit_codes':[h['exit_code'] for h in handoffs],'replay':replay,'results_synced':reports['results_section_exactly_synced'],'paper_manifest_failures':[p['path'] for p in paper if not p['passed']]},indent=2))
