import csv
import hashlib
import io
import json
from pathlib import Path
import contextlib

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent
def readj(p):
    return json.loads((ROOT / p).read_text(encoding='utf-8'))
def rows(p, delimiter=','):
    with (ROOT / p).open(encoding='utf-8-sig') as f:
        return list(csv.DictReader(f, delimiter=delimiter))
result = {}
checks = []
for section in readj('audit_manifest.json')['sections'].values():
    for name, expected in section.items():
        p = ROOT / name
        h = hashlib.sha256()
        if p.exists():
            with p.open('rb') as f:
                for block in iter(lambda: f.read(8 * 1024 * 1024), b''):
                    h.update(block)
        checks.append(dict(file=name, exists=p.exists(), actual_sha256=h.hexdigest(),
                           actual_bytes=p.stat().st_size if p.exists() else None,
                           expected=expected, passed=p.exists() and h.hexdigest()==expected['sha256'] and p.stat().st_size==expected['bytes']))
result['manifest'] = checks
hits = rows('results/hits_ranked.csv')
result['screen'] = dict(rows=len(hits), unique_names=len({r['name'] for r in hits}),
    below_minus7=sum(float(r['vina_best'])<=-7 for r in hits), first=hits[0],
    energy_min=min(hits,key=lambda r:float(r['vina_best'])),
    raw_lines=sum(1 for _ in (ROOT/'data/chembl_library.jsonl').open()),
    filtered_rows=len(rows('data/library_filtered.csv')),
    dock_set_lines=sum(1 for _ in (ROOT/'data/dock_set.smi').open()),
    prep_failures=readj('data/prep_failures.json'))
result['expansion'] = dict(count=len(readj('results/expansion_results.json')),
                           sample=readj('results/expansion_results.json')[:2])
result['herg_dataset_rows'] = len(rows('data/herg_central.tab','\t'))
result['smpd1_ad'] = readj('data/ad_scores.json').get('SMPD1')
result['bound_log'] = dict(rows=len(rows('md/bound_log.csv')),last=rows('md/bound_log.csv')[-1])
result['apo_log'] = dict(rows=len(rows('md/log.csv')),last=rows('md/log.csv')[-1])
result['cnn'] = readj('results/gnina_rescoring.json')
result['homolog'] = rows('results/homolog_selectivity.csv')
# Recompute the original rubric in memory, suppressing its file write.
source = (ROOT/'scripts/score_panel.py').read_text(encoding='utf-8').split('json.dump(')[0]
import os
os.chdir(ROOT)
scope = {}
with contextlib.redirect_stdout(io.StringIO()):
    exec(compile(source,'score_panel.py','exec'),scope)
actual = {r[1]:r[0] for r in scope['rows']}
result['panel_recompute'] = dict(scores=actual,matches=all(abs(actual[g]-v['total'])<1e-12 for g,v in readj('data/panel_scores.json').items()))
(OUT/'local_results.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k not in ('manifest','cnn','homolog')},indent=2))
print('manifest pass:',sum(r['passed'] for r in checks),'/',len(checks))
