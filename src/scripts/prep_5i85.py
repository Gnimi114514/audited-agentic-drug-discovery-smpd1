"""Phase 3: extract receptor (chain A + ZN) and pocket ligand (PC) from 5I85."""
import math

src = 'structures/5i85.pdb'
prot, zn, pc = [], [], []
for line in open(src):
    rec = line[:6].strip()
    if rec == 'ATOM' and line[21] == 'A':
        prot.append(line)
    elif rec == 'HETATM':
        resn = line[17:20].strip()
        if resn == 'ZN' and line[21] == 'A':
            zn.append(line)
        elif resn == 'PC':
            pc.append(line)

# keep standard protein residues + maybe sulfide links; drop glycosylation handled by resn filter implicitly (NAG etc are HETATM so not in ATOM)
with open('structures/5i85_recA_ZN.pdb', 'w') as f:
    f.writelines(prot)
    f.writelines(zn)
    f.write('TER\nEND\n')

with open('structures/5i85_PC.pdb', 'w') as f:
    f.writelines(pc)
    f.write('END\n')

def center(lines):
    xs = [float(l[30:38]) for l in lines]
    ys = [float(l[38:46]) for l in lines]
    zs = [float(l[46:54]) for l in lines]
    return (sum(xs)/len(xs), sum(ys)/len(ys), sum(zs)/len(zs))

c = center(pc)
print('PC heavy atoms:', len(pc), 'center:', [round(x, 2) for x in c])
# pocket residues: protein atoms within 5.0 A of any PC atom
px, py, pz = [], [], []
for l in prot:
    px.append(float(l[30:38])); py.append(float(l[38:46])); pz.append(float(l[46:54]))
resids = set()
pcxyz = [(float(l[30:38]), float(l[38:46]), float(l[46:54])) for l in pc]
for i in range(len(px)):
    pa = (px[i], py[i], pz[i])
    for p in pcxyz:
        if math.dist(pa, p) < 5.0:
            resids.add((prot[i][17:20].strip(), prot[i][22:26].strip()))
            break
res = sorted(resids, key=lambda r: int(r[1]))
print('pocket residues (within 5 A of PC):', [f'{a}{b}' for a, b in res])
with open('structures/box_center.txt', 'w') as f:
    f.write(f'{c[0]:.3f} {c[1]:.3f} {c[2]:.3f}\n')
print('saved structures/5i85_recA_ZN.pdb, structures/5i85_PC.pdb, structures/box_center.txt')
