"""Phase 4: diversity prefilter — PAINS/Brenk clean + Murcko scaffold cap -> docking set."""
import csv, json, subprocess, sys, os
from collections import defaultdict
from rdkit import Chem, RDLogger
from rdkit.Chem.Scaffolds import MurckoScaffold

RDLogger.DisableLog('rdApp.*')

lib = json.load(open('data/chembl_library.json'))
print('library:', len(lib))

# write .smi for the bundled filter script
with open('data/library_raw.smi', 'w', encoding='utf-8') as f:
    for m in lib:
        f.write(f"{m['smiles']}\t{m['chembl_id']}\n")

# run bundled filter (property + PAINS/Brenk), keep all rows
subprocess.run([sys.executable,
                r'C:\Users\Gnimi\.agents\skills\ai-drug-discovery\scripts\filter_molecules.py',
                'data/library_raw.smi', '-o', 'data/library_filtered.csv', '--top', '0'],
               check=True)

clean = []
with open('data/library_filtered.csv', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        if r.get('error'):
            continue
        if r.get('alerts'):            # structural alerts -> drop pre-dock
            continue
        if abs(int(r['charge'])) > 1:  # vina-friendly charge range
            continue
        clean.append(r)
print('after PAINS/Brenk/charge filter:', len(clean))

# Murcko scaffold diversity cap
scaf_count = defaultdict(int)
CAP = 4          # per-scaffold cap (tighter for docking budget)
TOTAL_CAP = 3500 # overall docking budget (measured vina throughput)
dock, dropped_for_scaffold = [], 0
for r in clean:
    if len(dock) >= TOTAL_CAP:
        break
    mol = Chem.MolFromSmiles(r['smiles'])
    if mol is None:
        continue
    scaf = MurckoScaffold.GetScaffoldForMol(mol)
    key = Chem.MolToSmiles(scaf)
    if scaf_count[key] >= CAP:
        dropped_for_scaffold += 1
        continue
    scaf_count[key] += 1
    dock.append(r)

print(f'diversity-capped docking set: {len(dock)} (dropped {dropped_for_scaffold} scaffold duplicates, {len(scaf_count)} unique scaffolds)')
with open('data/dock_set.smi', 'w', encoding='utf-8') as f:
    for r in dock:
        f.write(f"{r['smiles']}\t{r['name']}\n")

# reference inhibitors appended with REF_ prefix
refs = json.load(open('data/asm_reference_inhibitors.json'))
with open('data/dock_refs.smi', 'w', encoding='utf-8') as f:
    for m in refs:
        f.write(f"{m['smiles']}\tREF_{m['chembl_id']}\n")
print('wrote data/dock_set.smi and data/dock_refs.smi')
