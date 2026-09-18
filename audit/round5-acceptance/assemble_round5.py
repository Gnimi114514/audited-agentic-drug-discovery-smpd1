import json,hashlib
from pathlib import Path
from datetime import datetime,timezone
OUT=Path(__file__).resolve().parent; ROOT=OUT.parents[1]
def read(name): return json.loads((OUT/name).read_text(encoding='utf-8'))
m=read('manifest_checks.json'); t=read('text_checks.json'); p=read('pocket_checks.json'); b=read('benchmark_checks.json')
sources={**t['source_sha256'],**b['input_sha256'],'audit_manifest.json':m['root_sha256']}
sources['scripts/pocket_residence.py']=hashlib.sha256((ROOT/'scripts/pocket_residence.py').read_bytes()).hexdigest()
drift={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=h for name,h in sources.items()}
result={
 'generated_at':datetime.now(timezone.utc).isoformat(),
 'role':'Fresh-session round-5 acceptance auditor',
 'decision':'REJECT','G6':'BLOCKED; not eligible for acceptance on this revision',
 'write_scope':'independent-audit/round5-acceptance only',
 'checks':{'repair_1':p,'repair_2':{k:v for k,v in t['checks'].items() if k in ['MODEL_A_lineage_both_reports','fitted_estimator_serialization_withdrawal']},'repair_3':{k:v for k,v in t['checks'].items() if k not in ['MODEL_A_lineage_both_reports','fitted_estimator_serialization_withdrawal']},'repair_4':m,'repair_5':b},
 'mandatory_repairs':[
 'Correct residue selection and crystal/reference-frame center transform; rerun pocket analysis and propagate complete catalytic contacts.',
 'Remove surviving pocket, mean/max, old-gate, reference-threshold, ensemble-denial and v1-provenance contradictions. Explicitly withdraw fitted-estimator serialization and describe saved-score/refit limits.',
 'Execute real artifact replay for all 13 claimed cases; derive results from checks, fix stale 18/18 producer summary, and align seeded documentation with executed design.',
 'Freeze all final leaves, regenerate nested handoffs then root, and require both handoffs plus every root hash to pass.'
 ],
 'source_sha256':sources,'source_drift_at_delivery':drift,
 'limitations':['No experimental validation or G6 promotion performed.','Five simplified seeded fixtures are not a general sensitivity benchmark.','Literal requested contact labels pass but conflict with complete independent catalytic mapping; scientific failure is reported explicitly.'],
 'report':'independent-audit/round5-acceptance/round5-acceptance.md'
}
(OUT/'round5_checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
assert not any(drift.values()),drift
assert m['hash_matches']==54 and m['total']==55
assert len(result['checks'])==5
print(json.dumps({'decision':result['decision'],'root_hash_matches':'54/55','source_drift':any(drift.values()),'report_exists':(OUT/'round5-acceptance.md').is_file()}))
