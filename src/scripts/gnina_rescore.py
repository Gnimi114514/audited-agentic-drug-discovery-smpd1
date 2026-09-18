"""Extract mode-1 poses from Vina outputs and rescore with GNINA CNN."""
import os, re, subprocess, json

WORK = '/mnt/c/Users/Gnimi/.zcode/workspace/default/cognition-drug-discovery'
REC = f'{WORK}/structures/5i85_recA_ZN_rigid.pdbqt'
OUTD = f'{WORK}/docking/gnina'
os.makedirs(OUTD, exist_ok=True)
ENV = '/root/miniforge/envs/gnina12/lib'

LIGS = {
    'CHEMBL7385':  f'{WORK}/docking/out/CHEMBL7385.out.pdbqt',
    'CHEMBL24974': f'{WORK}/docking/out/CHEMBL24974.out.pdbqt',
    'CHEMBL48767': f'{WORK}/docking/out/CHEMBL48767.out.pdbqt',
    'CHEMBL6729':  f'{WORK}/docking/out/CHEMBL6729.out.pdbqt',
    'EXP_CHEMBL7385_CF3':  f'{WORK}/docking/out_exp/EXP_CHEMBL7385_C(F)(F)F_C19.out.pdbqt',
    'EXP_CHEMBL24974_CF3': f'{WORK}/docking/out_exp/EXP_CHEMBL24974_C(F)(F)F_C27.out.pdbqt',
    'REF_CHEMBL418376': f'{WORK}/docking/out/REF_CHEMBL418376.out.pdbqt',
    'REF_CHEMBL5284579': f'{WORK}/docking/out/REF_CHEMBL5284579.out.pdbqt',
    'REF_CHEMBL310981': f'{WORK}/docking/out/REF_CHEMBL310981.out.pdbqt',
}

def extract_mode1(path):
    atoms, in1 = [], False
    for l in open(path):
        if l.startswith('MODEL'):
            in1 = (int(l.split()[1]) == 1)
        elif l.startswith('ENDMDL'):
            if in1:
                break
        elif in1 and l.startswith(('ATOM', 'HETATM')):
            atoms.append(l)
    return atoms

results = {}
for name, path in LIGS.items():
    atoms = extract_mode1(path)
    if not atoms:
        print(name, 'no mode-1 atoms'); continue
    pose = f'{OUTD}/{name}_pose1.pdbqt'
    with open(pose, 'w') as f:
        f.write('ROOT\n')
        f.writelines(atoms)
        f.write('ENDROOT\nTORSDOF 0\n')
    env = dict(os.environ, LD_LIBRARY_PATH=ENV)
    r = subprocess.run(['/tmp/gnina', '--receptor', REC, '--ligand', pose, '--score_only'],
                       capture_output=True, text=True, env=env, timeout=600)
    txt = r.stdout
    cnn_aff = re.findall(r'CNNaffinity:\s*([-\d.]+)', txt)
    cnn_sc = re.findall(r'CNNscore:\s*([\d.]+)', txt)
    vina_aff = re.findall(r'Affinity:\s*([-\d.]+)', txt)
    results[name] = {'cnn_affinity': float(cnn_aff[0]) if cnn_aff else None,
                     'cnn_score': float(cnn_sc[0]) if cnn_sc else None,
                     'vina_affinity': float(vina_aff[0]) if vina_aff else None}
    print(name, results[name], flush=True)

json.dump(results, open(f'{WORK}/results/gnina_rescoring.json', 'w'), indent=1)
print('saved results/gnina_rescoring.json')
