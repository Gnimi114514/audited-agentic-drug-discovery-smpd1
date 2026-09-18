"""Phase 1: weighted scoring rubric over the candidate evidence matrix."""
import json

ad = json.load(open('data/ad_scores.json'))
det = json.load(open('data/ot_target_details.json'))
trend = json.load(open('data/pubmed_trends.json'))

GENES = ['TREM2','PLCG2','EPHA1','CR1','CD33','SORL1','ABCA7','BIN1','PICALM','CLU',
         'SPI1','INPP5D','MS4A6A','HFE','ACE','CDK5','GSK3B','SMPD1','CDC25B',
         'ADAM10','APH1B','MAPT']

VITAL = ('heart', 'kidney', 'liver')

rows = []
for g in GENES:
    a = ad.get(g, {})
    t = det.get(g, {})
    s = t.get('_summary', {})
    tr = s.get('sm_tractable', {})

    # 1) genetics + omics (0-1)
    gen = a.get('genetic_association', 0.0)
    rna = a.get('rna_expression', 0.0)
    genetics = 0.8 * gen + 0.2 * rna

    # 2) mechanistic plausibility
    mech = 0.5 * a.get('affected_pathway', 0.0) + 0.5 * a.get('animal_model', 0.0)

    # 3) novelty: approved drugs / clinical crowding / medicinal-chem crowding
    appr = s.get('approved_like', 0)
    nclin = s.get('clinical_rows', 0)
    stages = s.get('max_stages', [])
    inh = trend[g]['inhibitor_1525']
    nov = 1.0
    if appr > 0: nov -= 0.5
    if nclin >= 3: nov -= 0.3
    if inh > 300: nov -= 0.2
    elif inh > 100: nov -= 0.1
    novelty = max(0.0, nov)

    # 4) safety: essentiality, liabilities, vital-tissue expression
    dep = s.get('depmap_mean_effect')
    n_safe = s.get('n_safety', 0)
    vital_tpm = {}
    be = t.get('baselineExpression') or {}
    for r in (be.get('rows') if isinstance(be, dict) else be) or []:
        name = ((r.get('tissueBiosample') or {}).get('biosampleName') or '').lower()
        if any(v in name for v in VITAL):
            vital_tpm[name] = max(vital_tpm.get(name, 0), r.get('median') or 0)
    saf = 1.0 - min(0.6, 0.15 * n_safe)
    if dep is not None and dep < -0.3: saf -= 0.2
    if vital_tpm and max(vital_tpm.values()) > 100: saf -= 0.2
    safety = max(0.0, saf)

    # 5) druggability
    if tr.get('High-Quality Pocket'): drug = 1.0
    elif tr.get('Med-Quality Pocket'): drug = 0.7
    elif tr.get('High-Quality Ligand'): drug = 0.5
    else: drug = 0.2
    if tr.get('Druggable Family'): drug = min(1.0, drug + 0.3)

    total = (0.30*genetics + 0.20*mech + 0.20*novelty + 0.20*safety + 0.10*drug)
    rows.append((total, g, genetics, mech, novelty, safety, drug, appr, nclin, stages, vital_tpm, dep))

rows.sort(reverse=True)
print(f'{"gene":8} {"TOTAL":>6} {"gen30":>6} {"mech20":>6} {"nov20":>6} {"saf20":>6} {"drug10":>6}  appr clin stages')
for r in rows:
    print(f'{r[1]:8} {r[0]:6.3f} {r[2]:6.3f} {r[3]:6.3f} {r[4]:6.3f} {r[5]:6.3f} {r[6]:6.3f}  {r[7]:>4} {r[8]:>4} {r[9]}')
    if r[10] or r[11] is not None:
        print(f'         vitalTPM={ {k: round(v,1) for k,v in r[10].items()} } depmap={round(r[11],3) if r[11] is not None else None}')

# drug names behind approvals/clinical rows
print('\n== drug/clinical candidate names per gene ==')
for g in GENES:
    t = det.get(g, {})
    dr = (t.get('drugAndClinicalCandidates') or {}).get('rows') or []
    names = [f"{(r.get('drug') or {}).get('name')}[{r.get('maxClinicalStage')}]" for r in dr]
    if names:
        print(g, '->', names[:8], ('...' if len(names) > 8 else ''))

json.dump({r[1]: {'total': r[0], 'genetics': r[2], 'mech': r[3], 'novelty': r[4],
                  'safety': r[5], 'druggability': r[6]} for r in rows},
          open('data/panel_scores.json', 'w'), indent=1)
print('\nsaved data/panel_scores.json')
