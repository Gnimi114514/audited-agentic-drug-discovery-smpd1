"""Phase 1: AD-specific association scores for all panel genes (bigger page) + PubMed trends."""
import requests, json, time

URL = 'https://api.platform.opentargets.org/api/v4/graphql'
GENES = ['TREM2','PLCG2','EPHA1','CR1','CD33','SORL1','ABCA7','BIN1','PICALM','CLU',
         'SPI1','INPP5D','MS4A6A','HFE','ACE','CDK5','GSK3B','SMPD1','CDC25B',
         'ADAM10','APH1B','MAPT']

# --- 1) AD association scores, top 300 ---
Q = """
query {
  disease(efoId: "MONDO_0004975") {
    associatedTargets(page: {index: 0, size: 300}) {
      rows {
        target { approvedSymbol }
        score
        datatypeScores { id score }
      }
    }
  }
}
"""
d = requests.post(URL, json={'query': Q}, timeout=90).json()
rows = d['data']['disease']['associatedTargets']['rows']
ad = {}
for row in rows:
    sym = row['target']['approvedSymbol']
    dt = {x['id']: x['score'] for x in row['datatypeScores']}
    ad[sym] = {'overall': row['score'], **dt}
print('AD top300 pulled:', len(rows))
for g in GENES:
    if g in ad:
        a = ad[g]
        print(f"{g:8} overall={a['overall']:.3f} genetic={a.get('genetic_association',0):.3f} "
              f"lit={a.get('literature',0):.2f} animal={a.get('animal_model',0):.2f} "
              f"clin={a.get('clinical',0):.2f} pathway={a.get('affected_pathway',0):.2f} "
              f"rnaExp={a.get('rna_expression',0):.2f}")
    else:
        print(f"{g:8} not in AD top300")
json.dump(ad, open('data/ad_scores.json', 'w'), indent=1)

# --- 2) PubMed trends ---
BASE = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi'
def esearch(term, mindate, maxdate):
    p = {'db': 'pubmed', 'term': term, 'retmode': 'json',
         'mindate': mindate, 'maxdate': maxdate, 'datetype': 'pdat'}
    for attempt in range(3):
        try:
            r = requests.get(BASE, params=p, timeout=30)
            return int(r.json()['esearchresult']['count'])
        except Exception as e:
            time.sleep(2)
    return -1

trend = {}
for g in GENES:
    t_early = esearch(f'{g} AND (Alzheimer OR cognitive OR dementia)', 2015, 2019)
    time.sleep(0.35)
    t_late = esearch(f'{g} AND (Alzheimer OR cognitive OR dementia)', 2023, 2025)
    time.sleep(0.35)
    t_inh = esearch(f'{g} AND inhibitor', 2015, 2025)
    time.sleep(0.35)
    trend[g] = {'early_1519': t_early, 'late_2325': t_late, 'inhibitor_1525': t_inh}
    print(f"{g:8} AD/cog pubs 15-19={t_early:5} 23-25={t_late:5}  inhibitor={t_inh:5}")
json.dump(trend, open('data/pubmed_trends.json', 'w'), indent=1)
print('done')
