import concurrent.futures
import datetime
import json
from pathlib import Path
import requests

OUT=Path(__file__).resolve().parent
BASE='https://www.ebi.ac.uk/chembl/api/data/'
jobs={
 'mechanisms':(BASE+'mechanism.json',{'target_chembl_id':'CHEMBL2760','limit':1000}),
 'target':(BASE+'target/CHEMBL2760.json',{}),
 'pubmed':('https://www.ebi.ac.uk/europepmc/webservices/rest/search',{'query':'EXT_ID:38337058 OR EXT_ID:37605262 OR EXT_ID:27598773','format':'json','resultType':'core'}),
 'trend':('https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi',{'db':'pubmed','term':'SMPD1 AND inhibitor','retmode':'json','mindate':'2015','maxdate':'2025','datetype':'pdat'}),
}
for mol in ['CHEMBL28172','CHEMBL28132','CHEMBL7385','CHEMBL24974','CHEMBL418376','CHEMBL310981','CHEMBL5284579']:
    params={'molecule_chembl_id':mol,'limit':1000}
    if mol in ['CHEMBL418376','CHEMBL310981','CHEMBL5284579']:
        params['target_chembl_id']='CHEMBL2760'
    jobs[mol]=(BASE+'activity.json',params)
def fetch(item):
    key,(url,params)=item
    try:
        r=requests.get(url,params=params,timeout=35)
        r.raise_for_status()
        return key,dict(url=r.url,status=r.status_code,data=r.json())
    except Exception as e:
        return key,dict(error=str(e))
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    data=dict(pool.map(fetch,jobs.items()))
q='query { target(ensemblId: "ENSG00000166311") { approvedSymbol associatedDiseases(efoIds: ["MONDO_0004975"], page: {index: 0, size: 10}) { rows { disease { id name } score datatypeScores { id score } } } } }'
try:
    r=requests.post('https://api.platform.opentargets.org/api/v4/graphql',json={'query':q},timeout=35)
    data['open_targets']=dict(status=r.status_code,query=q,data=r.json())
except Exception as e:
    data['open_targets']=dict(error=str(e))
data['queried_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
(OUT/'live_results.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
for k,v in data.items():
    if not isinstance(v,dict): continue
    d=v.get('data',{})
    if 'activities' in d:
        print(k,'total',d.get('page_meta',{}).get('total_count'))
        print(json.dumps([{x:a.get(x) for x in ['activity_id','target_chembl_id','target_pref_name','standard_type','standard_relation','standard_value','standard_units','assay_chembl_id','document_chembl_id']} for a in d['activities'][:10]]))
    elif k=='pubmed':
        for a in d.get('resultList',{}).get('result',[]): print(a.get('id'),a.get('title'),a.get('abstractText'))
    else: print(k,json.dumps(v)[:4500])
