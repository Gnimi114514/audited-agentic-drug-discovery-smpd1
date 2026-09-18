import hashlib,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
    return h.hexdigest()
selected=['structure-analysis.md','target-dossier.md','audit_manifest.json','research-log.md','final-report.md']
(OUT/'snapshot').mkdir(exist_ok=True)
snap={}
for name in selected:
    shutil.copy2(ROOT/name,OUT/'snapshot'/name)
    snap[name]=digest(ROOT/name)
manifest=json.loads((ROOT/'audit_manifest.json').read_text())
checks=[]
for section,files in manifest['sections'].items():
    for name,expected in files.items():
        p=ROOT/name
        actual=digest(p) if p.is_file() else None
        checks.append(dict(section=section,path=name,actual=actual,expected=expected,
          passed=actual==expected['sha256'] and p.stat().st_size==expected['bytes']))
covered={r['path'] for r in checks}
out=dict(snapshot_sha256=snap,manifest_generated=manifest.get('generated'),checks=checks,
 selected_not_covered=[n for n in selected if n not in covered],
 critical_not_covered=[n for n in ['md/bound_v2.dcd','md/complex.prmtop','md/complex.inpcrd','md/bound_ref.pdb','md/bound_v2_log.csv','scripts/bound_md.py','data/herg_central.tab'] if n not in covered])
(OUT/'integrity.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
