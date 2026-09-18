from pathlib import Path
import json, hashlib
out = Path(__file__).resolve().parent
root = out.parents[1]
def read(name): return json.loads((out/name).read_text(encoding='utf8'))
manifest = read('manifest_checks.json')
execution = read('replay_execution.json')
source = read('replay_checks.json')
generated = read('real_findings_replay_executed.json')
saved = json.loads((root/'runs/benchmark-seeded/real_findings_replay_executed.json').read_text(encoding='utf8'))
reports = read('report_review.json')
items = [
 {'id':'R8-1','verdict':'FAIL','finding':'R9-1','evidence':['paper/manuscript_results_discussion.md:82','paper/MANUSCRIPT_DRAFT_v1.md:30','paper/MANUSCRIPT_DRAFT_v1.md:203','paper/MANUSCRIPT_DRAFT_v1.md:336'],'reason':'Claimed post-hoc unification is absent; abstract, Results and Figure 4 remain unreconciled.'},
 {'id':'R8-2-counting','verdict':'PASS','append_line':source['append_line'],'count_line':source['count_line'],'generated_summary':generated['summary'],'generated_equals_saved':generated==saved,'execution_exit_code':execution['exit_code']},
 {'id':'R8-2-R1-2','verdict':'FAIL','finding':'R9-2','reads_bound_run_log':source['reads_bound_run_log'],'reason':'Literal values; no first-frame artifact check, inaccurate claimed log array.'},
 {'id':'R8-2-R3-1','verdict':'FAIL','finding':'R9-2','reason':'Literal observed string and unconditional True; c1 read elsewhere does not feed this record.'},
 {'id':'R8-2-R3-6','verdict':'FAIL','finding':'R9-2','reason':'Regex loses signs, selects only 6.xx from whole document, accepts empty and contradictory evidence.','probes':read('replay_mutation_checks.json')},
 {'id':'R8-2-R1-3-delegated','verdict':'PASS','scope':'Null correctly reported; WSL parmed verification not newly run, and no WSL dispatch occurs in replay source.'},
 {'id':'R8-3','verdict':'PASS','research_log':next(e for e in manifest['entries'] if e['path']=='research-log.md'),'reason':'Final D22-addendum bytes match freeze; content truth is separately rejected.'},
 {'id':'manifest-all-hashes','verdict':'PASS','total':manifest['total'],'passed':manifest['passed'],'level_counts':manifest['level_counts']},
 {'id':'manifest-level-count-description','verdict':'MINOR_NOTE','expected_L1_claim':39,'actual_L1':38,'actual_total':75,'reason':'Claimed 39/15/11/2/9 would total 76; actual root has 38/15/11/2/9.'},
 {'id':'handoff-r9-evidence','verdict':'PASS','execution':manifest['handoffs'][0]},
 {'id':'handoff-r9-reports','verdict':'PASS','execution':manifest['handoffs'][1]},
]
items.extend(x for x in reports['items'] if x['id'] != 'R8-1')
result = {'audit_round':9,'date':'2026-09-14','overall':'REJECT','g6_recommendation':'BLOCKED',
 'capability_coverage':'partial-compute','write_scope':'independent-audit/round9-acceptance/',
 'items':items,'replay_execution':execution,'replay_source':source,
 'root_manifest_sha256':hashlib.sha256((root/'audit_manifest.json').read_bytes()).hexdigest(),
 'manifest_entries':manifest['entries'],'artifact_frame_recount':reports['c1_frame_array_recount'],
 'additional_sweep_notes':reports['additional_sweep_notes'],
 'limitations':['No new dynamics or trajectory geometry recomputation.','R1-3 parmed delegated/null, not newly verified in WSL.','Mechanical handoff success does not certify scientific acceptance.','Historical paper manifest is not a current freeze.'],
 'supporting_files':['round9-acceptance.md','manifest_checks.json','report_review.json','replay_checks.json','replay_execution.json','replay_stdout.txt','replay_stderr.txt','real_findings_replay_executed.json','replay_mutation_checks.json','check_artifacts.py','run_replay.py','probe_replay.py']}
(out/'round9_checks.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf8')
assert result['overall']=='REJECT' and manifest['passed']==75 and generated==saved
print(json.dumps({'overall':result['overall'],'g6':result['g6_recommendation'],'items':len(items),'manifest_passed':manifest['passed'],'replay_matches_saved':generated==saved}))
