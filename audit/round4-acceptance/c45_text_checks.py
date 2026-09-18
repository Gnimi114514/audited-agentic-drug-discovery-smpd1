"""Read-only text audit; writes evidence solely beside this script."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
files = ['final-report.md', 'structure-analysis.md', 'target-dossier.md', 'hit-report.md', 'research-log.md', 'runs/audit-20260913/gates.json']
texts = {p: (ROOT / p).read_text(encoding='utf-8') for p in files}
def excerpt(path, start, end):
    return {'path': path, 'start_line': start, 'end_line': end, 'text': '\n'.join(texts[path].splitlines()[start-1:end])}
findings = [
    {'id':'R4-T1','severity':'P1','title':'Pocket residence remains asserted in final report', 'evidence':[excerpt('final-report.md',210,211),excerpt('final-report.md',59,59),excerpt('research-log.md',786,792)]},
    {'id':'R4-T2','severity':'P1','title':'RF300 evaluation and legacy candidate probabilities remain mixed in final report', 'evidence':[excerpt('final-report.md',221,229),excerpt('research-log.md',794,801)]},
    {'id':'R4-T3','severity':'P2','title':'Mean/max range mislabel remains in correction banner', 'evidence':[excerpt('final-report.md',20,21),excerpt('final-report.md',173,177)]},
    {'id':'R4-T4','severity':'P2','title':'Gate table retains old-G5 outside historical mapping', 'evidence':[excerpt('final-report.md',60,60),excerpt('research-log.md',810,811)]},
    {'id':'R4-T5','severity':'P2','title':'False reference-score threshold remains in hit report', 'evidence':[excerpt('hit-report.md',11,19),excerpt('structure-analysis.md',36,42)]},
    {'id':'R4-T6','severity':'P2','title':'Structure report still denies ensemble docking', 'evidence':[excerpt('structure-analysis.md',34,34),excerpt('structure-analysis.md',58,59),excerpt('research-log.md',812,813)]},
    {'id':'R4-T7','severity':'P2','title':'V1 parameter provenance still points to overwritten current complex.prmtop', 'evidence':[excerpt('final-report.md',22,23),excerpt('final-report.md',167,170),excerpt('research-log.md',817,820)]},
]
gates=json.loads(texts['runs/audit-20260913/gates.json'])['gates']
g6=next(x for x in gates if x['gate_id']=='G6-audit')
result={
 'command':'python independent-audit/round4-acceptance/c45_text_checks.py',
 'method':'Full UTF-8 reads of four reports, D17 and gates; contextual review of rg matches. Historical withdrawn claims and proposed uncomputed analog changes do not count as achieved facts.',
 'source_sha256':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files},
 'C4':{'verdict':'PASS','literal_forbidden_factual_claims_subcheck':'PASS','reason':'The enumerated obsolete factual claims are withdrawn or qualified. Broader surviving contradictions are separate new findings, not an expansion of C4.','evidence':[excerpt('hit-report.md',123,124),excerpt('final-report.md',226,229),excerpt('final-report.md',187,193),excerpt('final-report.md',22,25),excerpt('structure-analysis.md',33,42),excerpt('target-dossier.md',63,63)],'notes':['49 uM for CHEMBL310981 is a scoped record, not the withdrawn 1-2 uM SMPD1 benchmark.','hit-report.md:123-124 proposes an uncomputed future analog to de-risk oxidative cleavage; this is not a claim of demonstrated de-risking.','target-dossier.md:63 explicitly says direction REOPENED; R3-7 repaired.','structure-analysis.md:28 explicitly disclaims chemically-equivalence-aware same-element matching; that R3-6 subrepair is present.']},
 'C5':{'verdict':'PASS','D17_present':'## D17 ' in texts['research-log.md'],'round3_history_present':any(x.get('round')==3 for x in g6['history']),'outcome':g6['outcome'],'G6_integration':g6['team_skill_gate_state']['G6_integration'],'evidence':[excerpt('research-log.md',784,820),excerpt('runs/audit-20260913/gates.json',33,37),excerpt('runs/audit-20260913/gates.json',45,51)],'note':'D17 records repair claims; record presence is not proof they were propagated. G6 is not self-passed.'},
 'findings':findings,
}
(OUT/'c45_text_results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'C4':result['C4']['verdict'],'literal_claims':result['C4']['literal_forbidden_factual_claims_subcheck'],'C5':result['C5']['verdict'],'G6':g6['outcome'],'findings':len(findings)}))
