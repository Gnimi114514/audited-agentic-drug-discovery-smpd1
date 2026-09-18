import json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; OUT=Path(__file__).resolve().parent
names=['final-report.md','hit-report.md','structure-analysis.md']
texts={p:(ROOT/p).read_text(encoding='utf-8') for p in names}
def ev(p,a,b): return dict(path=p,line=a,text='\n'.join(texts[p].splitlines()[a-1:b]))
checks={
 'MODEL_A_lineage_both_reports':dict(status='PASS',details='Both disclose raw-record legacy training, deduplicated refit, and only 1/26 reproduced; final report canonical-dedup context is immediately above the lineage paragraph. MODEL-B alone gets held-out AUC.',evidence=[ev('final-report.md',232,246),ev('hit-report.md',200,213)]),
 'fitted_estimator_serialization_withdrawal':dict(status='PARTIAL',details='No fitted-estimator serialization claim remains in final-report.md, and saved-test-score evaluation is described. No explicit withdrawal or statement that fitted estimators are not archived is present; clarify this to close adjudication repair 2 unambiguously.'),
 'T1_pocket':dict(status='FAIL',details='Center-condition-fails correction is present, but non-catalytic-only surface labels and occupancy from retired COM-imaged metric survive as current conclusions.',evidence=[ev('final-report.md',59,59),ev('final-report.md',202,222)]),
 'T2_lineage':dict(status='PASS',evidence=[ev('final-report.md',232,246)]),
 'T3_average_precision':dict(status='PASS',evidence=[ev('final-report.md',232,235)]),
 'T4_mean_max':dict(status='FAIL',details='Body labels mean/max correctly, but banner still uses unlabeled ranges.',evidence=[ev('final-report.md',19,23),ev('final-report.md',173,177)]),
 'T5_old_gate_labels':dict(status='FAIL',details='The two narrow literal strings in the request are absent, but old-G5 PASS survives outside the mapping table.',literal_old_G1_PASS_absent='old-G1 PASS' not in texts['final-report.md'],literal_G5_PASS_pipe_absent='G5 PASS |' not in texts['final-report.md'],evidence=[ev('final-report.md',60,60)]),
 'T6_threshold':dict(status='FAIL',details='Internal ranking convention is absent from final-report.md. Structure report has it, but hit-report still claims the reference chemotypes yield <= -7.0 despite all three scores being above -7.0.',evidence=[ev('hit-report.md',9,20),ev('structure-analysis.md',36,42)]),
 'T7_v1_topology':dict(status='FAIL',details='No rereview-r3 snapshot citation in final-report.md; v1 attribution still points to current complex.prmtop, now v2.',evidence=[ev('final-report.md',22,23),ev('final-report.md',168,170)]),
 'historical_R4_T6_ensemble_denial':dict(status='FAIL',details='Original round4 IDs differ from the user checklist: original T3=mean/max,T4=old gate,T5=threshold,T6=ensemble denial. This additional historical mandatory closure still fails.',evidence=[ev('structure-analysis.md',34,34),ev('structure-analysis.md',58,59)])
}
result=dict(checklist_numbering='T1..T7 keys follow user round5 enumeration; original round4 mapping is separately noted.',checks=checks,source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in names})
(OUT/'text_checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
