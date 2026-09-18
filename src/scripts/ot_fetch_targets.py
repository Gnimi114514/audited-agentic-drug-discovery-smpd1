"""Phase 1 (v3): per-target details from Open Targets, with gene-ID validation."""
import requests, json, time

URL = 'https://api.platform.opentargets.org/api/v4/graphql'

GENES = ['TREM2','PLCG2','EPHA1','CR1','CD33','SORL1','ABCA7','BIN1','PICALM','CLU',
         'SPI1','INPP5D','MS4A6A','HFE','ACE','CDK5','GSK3B','SMPD1','CDC25B',
         'ADAM10','APH1B','MAPT']

TQ = """
query ($id: String!) {
  target(ensemblId: $id) {
    id
    approvedSymbol
    approvedName
    biotype
    targetClass { label }
    functionDescriptions
    isEssential
    depMapEssentiality { tissueName screens { geneEffect cellLineName } }
    geneticConstraint { constraintType exp oe score }
    tractability { label modality value }
    safetyLiabilities { event literature }
    drugAndClinicalCandidates { count rows { maxClinicalStage drug { name } } }
    mousePhenotypes { modelPhenotypeLabel }
    baselineExpression { rows { tissueBiosample { biosampleName } median unit } }
    prioritisation { items { key value } }
  }
}
"""

def search_symbol(symbol):
    q = ('{ search(queryString: "%s", entityNames: ["target"], page: {index:0, size:3}) '
         '{ hits { id name entity } } }' % symbol)
    d = requests.post(URL, json={'query': q}, timeout=30).json()
    return [h['id'] for h in d['data']['search']['hits'] if h['entity'] == 'target']

def resolve(gene):
    """Return ensembl id whose approvedSymbol == gene (validated)."""
    for cand in search_symbol(gene):
        vq = '{ target(ensemblId: "%s") { approvedSymbol } }' % cand
        d = requests.post(URL, json={'query': vq}, timeout=30).json()
        sym = d['data']['target']['approvedSymbol']
        if sym == gene:
            return cand
        time.sleep(0.2)
    return None

ids = {}
for g in GENES:
    eid = resolve(g)
    ids[g] = eid
    print(g, '->', eid)
    time.sleep(0.2)
json.dump(ids, open('data/gene_ids.json', 'w'), indent=1)

out = {}
for g in GENES:
    eid = ids.get(g)
    if not eid:
        print(g, 'NO ID'); continue
    d = requests.post(URL, json={'query': TQ, 'variables': {'id': eid}}, timeout=60).json()
    if 'errors' in d:
        print(g, 'ERR:', [e['message'][:60] for e in d['errors']][:2]); continue
    t = d['data']['target']
    if t['approvedSymbol'] != g:
        print(g, 'MISMATCH got', t['approvedSymbol']); continue
    dr = t.get('drugAndClinicalCandidates') or {}
    rows = dr.get('rows') or []
    stages = [r.get('maxClinicalStage') or '' for r in rows]
    n_appr = sum(1 for s in stages if 'approv' in s.lower())
    tr = {x['label']: x['value'] for x in t.get('tractability') or [] if x.get('modality') == 'SM'}
    t['_summary'] = {
        'approved_like': n_appr, 'clinical_rows': len(rows), 'max_stages': sorted(set(stages)),
        'sm_tractable': tr, 'essential': t.get('isEssential'),
        'n_safety': len(t.get('safetyLiabilities') or []),
        'depmap_mean_effect': (sum(s['geneEffect'] for tis in (t.get('depMapEssentiality') or [])
                                    for s in (tis.get('screens') or [])) /
                               max(1, sum(len(tis.get('screens') or []) for tis in (t.get('depMapEssentiality') or []))))
    }
    out[g] = t
    print(f"{g}: appr={n_appr} clinical={len(rows)} smPkt={tr.get('High-Quality Pocket')}/{tr.get('Med-Quality Pocket')} "
          f"smLig={tr.get('High-Quality Ligand')} fam={tr.get('Druggable Family')} ess={t.get('isEssential')} safe={t['_summary']['n_safety']}")
    time.sleep(0.3)

json.dump(out, open('data/ot_target_details.json', 'w'), indent=1)
print('saved', len(out), 'targets')
