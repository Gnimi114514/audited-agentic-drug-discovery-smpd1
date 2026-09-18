"""Prepare original CCD PC graph only; no docking or solution-state inference."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
import types
from rdkit import Chem,rdBase
from rdkit.Geometry import Point3D
import meeko


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,d):p.write_text(json.dumps(d,indent=2,allow_nan=False),encoding='utf-8')
def pdbqt_rows(text):
    rows={}
    for line in text.splitlines():
        if line.startswith(('ATOM  ','HETATM')):
            serial=int(line[6:11]);rows[serial]={'name':line[12:16].strip(),'xyz':[float(line[x:x+8]) for x in (30,38,46)],'charge':float(line[70:76]),'type':line.split()[-1]}
    return rows

def main(project,output):
    root=Path(project).resolve();out=Path(output).resolve();out.mkdir(parents=True,exist_ok=False)
    sources={'ccd.cif':root/'runs/site-graph-20260915/analysis/ccd.cif','reference.pdb':root/'runs/site-graph-20260915/analysis/reference.pdb','legacy.pdbqt':root/'structures/PC_ref.pdbqt','check_pc_graph_rmsd.py':root/'scripts/check_pc_graph_rmsd.py'}
    for name,p in sources.items():(out/name).write_bytes(p.read_bytes())
    (out/Path(__file__).name).write_bytes(Path(__file__).read_bytes())
    module=types.ModuleType('frozen_graph');module.__file__=str(out/'check_pc_graph_rmsd.py')
    exec(compile((out/'check_pc_graph_rmsd.py').read_bytes(),module.__file__,'exec'),module.__dict__)
    heavy=module.ccd_graph(out/'ccd.cif');reference=module.coords(out/'reference.pdb')
    original_smiles=Chem.MolToSmiles(heavy,isomericSmiles=True)
    conformer=Chem.Conformer(heavy.GetNumAtoms());conformer.Set3D(True)
    for atom in heavy.GetAtoms():
        name=atom.GetProp('ccd_name');conformer.SetAtomPosition(atom.GetIdx(),Point3D(*reference[name]['xyz']))
    heavy.AddConformer(conformer)
    mol=Chem.AddHs(heavy,addCoords=True)
    name_map={};h_counts={}
    for atom in mol.GetAtoms():
        if atom.GetAtomicNum()==1:
            parent=atom.GetNeighbors()[0].GetProp('ccd_name');h_counts[parent]=h_counts.get(parent,0)+1
            name='HO'+parent[1:] if parent in ('O3','O4') else 'H'+str(atom.GetIdx()+1)
        else:name=atom.GetProp('ccd_name')
        name_map[atom.GetIdx()]=name
        info=Chem.AtomPDBResidueInfo();info.SetName(name.rjust(4));info.SetResidueName('PC');info.SetResidueNumber(727);info.SetChainId('A');info.SetIsHeteroAtom(True);atom.SetMonomerInfo(info)
        atom.SetProp('atom_name',name)
    if Chem.GetFormalCharge(mol)!=1 or h_counts.get('O3')!=1 or h_counts.get('O4')!=1:raise ValueError('original PC state not preserved')
    if Chem.MolToSmiles(Chem.RemoveHs(mol),isomericSmiles=True)!=original_smiles:raise ValueError('graph changed')
    mol.SetProp('_Name','PC_original_CCD_plus1_two_OH')
    mol.SetProp('atom_index_to_name_json',json.dumps(name_map))
    writer=Chem.SDWriter(str(out/'pc_original_graph.sdf'));writer.write(mol);writer.close()
    config={'charge_model':'gasteiger','compute_charges':True,'merge_these_atom_types':['H'],'add_index_map':True}
    prep=meeko.MoleculePreparation(**config);setups=prep.prepare(mol)
    if len(setups)!=1:raise ValueError('unexpected multiple preparations')
    setup=setups[0];text,ok,error=meeko.PDBQTWriterLegacy.write_string(setup,add_index_map=True)
    if not ok:raise ValueError(error)
    (out/'pc_meeko.pdbqt').write_text(text,encoding='utf-8');(out/'setup.json').write_text(setup.to_json(),encoding='utf-8')
    index_map={}
    for line in text.splitlines():
        if line.startswith('REMARK INDEX MAP '):
            values=list(map(int,line.split()[3:]));index_map.update({values[i]-1:values[i+1] for i in range(0,len(values),2)})
    rows=pdbqt_rows(text);mapping=[];max_shift=0
    for idx,serial in index_map.items():
        atom=mol.GetAtomWithIdx(idx);row=rows[serial]
        if row['name']!=name_map[idx]:raise ValueError('name mapping mismatch')
        if not math.isfinite(row['charge']):raise ValueError('nonfinite charge')
        if atom.GetAtomicNum()!=1:
            ref=reference[name_map[idx]]
            if ref['element']!=atom.GetSymbol():raise ValueError('element mismatch')
            shift=math.dist(ref['xyz'],row['xyz']);max_shift=max(max_shift,shift)
            if shift>0.00001:raise ValueError('heavy atom coordinates moved')
        mapping.append({'rdkit_index_0':idx,'pdbqt_serial':serial,'name':name_map[idx],'element':atom.GetSymbol(),'formal_charge':atom.GetFormalCharge(),'pdbqt':row})
    mapped_heavy={x['name'] for x in mapping if x['element']!='H'}
    if mapped_heavy!=set(reference):raise ValueError('heavy atom mapping incomplete')
    save(out/'atom_mapping.json',mapping)
    def features(text):
        rows=pdbqt_rows(text)
        return {'atom_count':len(rows),'partial_charge_sum':sum(x['charge'] for x in rows.values()),'nonzero_charge_atoms':sum(x['charge']!=0 for x in rows.values()),'branch_count':sum(x.startswith('BRANCH ') for x in text.splitlines()),'torsdof':[int(x.split()[1]) for x in text.splitlines() if x.startswith('TORSDOF ')],'rows':rows}
    result={'scope':'original CCD graph representation audit only; not G2 validation','versions':{'python':sys.version,'rdkit':rdBase.rdkitVersion,'meeko':meeko.__version__},'config':config,'formal_charge':Chem.GetFormalCharge(mol),'isomeric_smiles':original_smiles,'heavy_atoms':heavy.GetNumAtoms(),'total_explicit_atoms':mol.GetNumAtoms(),'phosphate_bound_H':{x:h_counts[x] for x in ('O3','O4')},'heavy_coordinate_max_shift_A':max_shift,'meeko':features(text),'legacy':features((out/'legacy.pdbqt').read_text()),'input_sources':{name:{'source':str(p),'sha256':sha(p)} for name,p in sources.items()},'limitations':['No docking or state optimization','CCD state is not proof of solution or assay protonation','Gasteiger charges are model-derived, not measured electrostatic validation','Hydrogen positions are RDKit-generated and not minimized','Default Vina lacks explicit Coulomb partial-charge term; charge change alone need not change its score']}
    save(out/'result.json',result)
    save(out/'manifest.json',{p.name:sha(p) for p in out.iterdir() if p.is_file()})
    print(json.dumps({k:result[k] for k in ('formal_charge','heavy_atoms','total_explicit_atoms','heavy_coordinate_max_shift_A')}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--project',required=True);p.add_argument('--output',required=True);a=p.parse_args();main(a.project,a.output)
