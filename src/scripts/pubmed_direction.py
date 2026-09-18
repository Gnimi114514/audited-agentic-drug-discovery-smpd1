"""Phase 2: fetch PubMed abstracts to verify mechanism direction for finalists."""
import requests, json, time, xml.etree.ElementTree as ET

BASE = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/'

QUERIES = {
    'INPP5D_direction': 'INPP5D AND (Alzheimer OR microglia) AND 2021:2025[dp]',
    'SMPD1_direction': 'sphingomyelinase AND (Alzheimer OR amyloid OR cognition) AND inhibitor',
    'PLCG2_direction': 'PLCG2 AND (Alzheimer OR microglia)',
    'INPP5D_ship_activator': 'SHIP1 AND (Alzheimer OR neuroinflammation)',
    'SMPD1_ama': 'acid sphingomyelinase AND (neurodegeneration OR memory)',
}

out = {}
for key, term in QUERIES.items():
    # search
    r = requests.get(BASE + 'esearch.fcgi', params={'db': 'pubmed', 'term': term,
                      'retmode': 'json', 'retmax': 6, 'sort': 'relevance'}, timeout=30)
    ids = r.json()['esearchresult'].get('idlist', [])
    recs = []
    if ids:
        time.sleep(0.4)
        r2 = requests.get(BASE + 'efetch.fcgi', params={'db': 'pubmed', 'id': ','.join(ids),
                          'retmode': 'xml'}, timeout=60)
        root = ET.fromstring(r2.content)
        for art in root.iter('PubmedArticle'):
            pmid = art.findtext('.//PMID')
            title = art.findtext('.//ArticleTitle') or ''
            year = art.findtext('.//PubDate/Year') or ''
            journal = art.findtext('.//Journal/Title') or ''
            abstract = ' '.join((t.text or '') for t in art.iter('AbstractText'))
            recs.append({'pmid': pmid, 'year': year, 'journal': journal,
                         'title': title, 'abstract': abstract[:1400]})
    out[key] = recs
    print(f'{key}: {len(recs)} records')
    for x in recs:
        print('  -', x['pmid'], x['year'], x['title'][:110])
    time.sleep(0.5)

json.dump(out, open('data/pubmed_direction.json', 'w'), indent=1)
print('saved data/pubmed_direction.json')
