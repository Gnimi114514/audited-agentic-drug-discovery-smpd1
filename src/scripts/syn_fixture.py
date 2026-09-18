"""Synthesis-agent fixture: validate the AiZynthFinder pipeline on ASPIRIN (known route:
salicylic acid + acetic anhydride) before touching candidates. Uses the official USPTO
ONNX models + the project proxy stock (chembldr20k) since the official ZINC stock is
service-blocked; closure here is PROXY, clearly labeled.
"""
import subprocess, json, os

# aspirin is in our proxy stock? check
from rdkit import Chem, RDLogger
RDLogger.DisableLog('rdApp.*')
import hashlib

target = 'CC(=O)Oc1ccccc1C(=O)O'  # aspirin
m = Chem.MolFromSmiles(target)
ik = Chem.MolToInchiKey(m)
print('aspirin inchikey:', ik)

in_stock = [l.strip() for l in open('data/stock_chembl20k.csv') if ik in l]
print('aspirin in proxy stock:', bool(in_stock))
sal = Chem.MolFromSmiles('O=C(O)c1ccccc1O')
sal_ik = Chem.MolToInchiKey(sal)
sal_in = [l.strip() for l in open('data/stock_chembl20k.csv') if sal_ik in l]
print('salicylic acid in proxy stock:', bool(sal_in))
json.dump({'fixture': 'aspirin', 'aspirin_in_proxy_stock': bool(in_stock),
           'salicylic_acid_in_proxy_stock': bool(sal_in)},
          open('runs/audit-20260913/tasks/syn-01/attempt-1/fixture_check.json', 'w'), indent=1)
