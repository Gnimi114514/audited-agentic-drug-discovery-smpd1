"""Phase 1: pull disease-target associations from Open Targets for the cognition anchor diseases."""
import requests, json, time

URL = 'https://api.platform.opentargets.org/api/v4/graphql'

DISEASES = {
    'MONDO_0004975': 'Alzheimer disease',
    'HP_0100543': 'Cognitive impairment',
    'MONDO_0002039': 'cognitive disorder',
}

Q = """
query ($efoId: String!, $size: Int!) {
  disease(efoId: $efoId) {
    id
    name
    associatedTargets(page: {index: 0, size: $size}) {
      count
      rows {
        target { id approvedSymbol biotype }
        score
        datatypeScores { id score }
      }
    }
  }
}
"""

out = {}
for efo, name in DISEASES.items():
    for attempt in range(3):
        try:
            r = requests.post(URL, json={'query': Q, 'variables': {'efoId': efo, 'size': 60}},
                              timeout=60)
            d = r.json()
            if 'errors' in d:
                print(efo, 'ERRORS:', d['errors'][:1])
                break
            node = d['data']['disease']
            out[efo] = {'name': node['name'], 'count': node['associatedTargets']['count'],
                        'rows': node['associatedTargets']['rows']}
            print(f"{efo} {node['name']}: total={node['associatedTargets']['count']}, pulled={len(out[efo]['rows'])}")
            break
        except Exception as e:
            print(efo, 'attempt', attempt, 'failed:', e)
            time.sleep(3)

with open('data/ot_associations.json', 'w', encoding='utf-8') as f:
    json.dump(out, f, indent=1)
print('saved data/ot_associations.json')
