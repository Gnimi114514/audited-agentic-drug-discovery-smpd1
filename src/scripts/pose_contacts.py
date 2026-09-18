"""Phase 5: pose inspection for top hits — qualitative contacts with catalytic site."""
import os, re, math, json, csv

AD2EL = {'OA':'O','O':'O','OS':'O','NA':'N','N':'N','NS':'N','A':'C','C':'C',
         'SA':'S','S':'S','P':'P','Zn':'Zn','F':'F','Cl':'Cl','Br':'Br'}

POCKET = {'ASP206','HIS208','ASP278','HIS282','ASN318','HIS319','HIS425','HIS457','THR458','HIS459','TYR488'}

# receptor pocket atom coordinates from the prepped receptor pdbqt
rec_atoms = []
for l in open('structures/5i85_recA_ZN_rigid.pdbqt'):
    if l.startswith(('ATOM', 'HETATM')):
        resn = l[17:20].strip()
        resi = l[22:26].strip()
        if (resn + resi) in POCKET or resn == 'ZN':
            adt = l.strip().split()[-1]
            el = AD2EL.get(adt, adt)
            rec_atoms.append((resn, resi, el, float(l[30:38]), float(l[38:46]), float(l[46:54])))
zn = [a for a in rec_atoms if a[2] == 'Zn']
print('pocket atoms:', len(rec_atoms), 'Zn:', [(a[3], a[4], a[5]) for a in zn])

def contacts(pdbqt_path, cutoff=4.0):
    lig = []
    for l in open(pdbqt_path):
        if l.startswith(('ATOM', 'HETATM')):
            adt = l.strip().split()[-1]
            el = AD2EL.get(adt, adt)
            if el == 'H':
                continue
            lig.append((el, float(l[30:38]), float(l[38:46]), float(l[46:54])))
    res_contacts = {}
    zn_d = min(math.dist((a[3], a[4], a[5]), (b[1], b[2], b[3])) for a in zn for b in lig) if zn else None
    polar_lig = [b for b in lig if b[0] in ('N', 'O')]
    for a in rec_atoms:
        if a[2] == 'Zn':
            continue
        for b in lig:
            d = math.dist((a[3], a[4], a[5]), (b[1], b[2], b[3]))
            if d <= cutoff:
                key = f'{a[0]}{a[1]}'
                rec = res_contacts.setdefault(key, {'heavy': 0, 'polar': 0})
                rec['heavy'] += 1
                if a[2] in ('N', 'O') and b[0] in ('N', 'O') and d <= 3.5:
                    rec['polar'] += 1
                break
    return res_contacts, zn_d

if __name__ == '__main__':
    top = json.load(open('results/top50.json'))
    rows = []
    for r in top[:20]:
        p = f"docking/out/{r['name']}.out.pdbqt"
        if not os.path.exists(p):
            continue
        c, zd = contacts(p)
        residues = sorted(c.items(), key=lambda kv: -kv[1]['heavy'])
        rows.append({'name': r['name'], 'vina': r['vina_best'],
                     'min_Zn_dist': round(zd, 2) if zd else None,
                     'contacts': '; '.join(f'{k}(h{v["heavy"]},p{v["polar"]})' for k, v in residues)})
        print(rows[-1]['name'], rows[-1]['vina'], 'Zn~', rows[-1]['min_Zn_dist'], '|', rows[-1]['contacts'][:120])
    with open('results/pose_contacts.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=['name', 'vina', 'min_Zn_dist', 'contacts'])
        w.writeheader(); w.writerows(rows)
    print('saved results/pose_contacts.csv')
