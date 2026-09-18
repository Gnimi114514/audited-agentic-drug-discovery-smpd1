import json
from pathlib import Path
import requests
OUT=Path(__file__).resolve().parent
data={}
for mol in ['CHEMBL418376','CHEMBL310981','CHEMBL5284579']:
    r=requests.get('https://www.ebi.ac.uk/chembl/api/data/activity.json',params={'molecule_chembl_id':mol,'limit':1000},timeout=30)
    r.raise_for_status(); data[mol]=r.json()
    print(mol,json.dumps([{k:a.get(k) for k in ['activity_id','target_chembl_id','target_organism','target_pref_name','standard_type','standard_value','standard_units']} for a in r.json()['activities'] if 'sphingo' in a.get('target_pref_name','').lower()]))
q='query { disease(efoId: "MONDO_0004975") { associatedTargets(page: {index: 0, size: 300}) { rows { target { approvedSymbol } score datatypeScores { id score } } } } }'
r=requests.post('https://api.platform.opentargets.org/api/v4/graphql',json={'query':q},timeout=40)
data['ot']=dict(status=r.status_code,query=q,data=r.json())
print('ot',json.dumps([a for a in r.json().get('data',{}).get('disease',{}).get('associatedTargets',{}).get('rows',[]) if a['target']['approvedSymbol'] in ['SMPD1','TREM2','CR1']]))
(OUT/'followup_results.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
