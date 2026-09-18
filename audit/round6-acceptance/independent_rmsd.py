from pathlib import Path
import json,itertools,math
root=Path.cwd();out=root/'independent-audit/round6-acceptance'
x=[];y=[];mode=0
for l in (root/'structures/5i85_PC.pdb').read_text().splitlines():
 if l.startswith('HETATM'):x.append((l[76:78].strip(),tuple(float(l[a:a+8]) for a in (30,38,46))))
for l in (root/'docking/redock_PC_out.pdbqt').read_text().splitlines():
 if l.startswith('MODEL'):mode=int(l.split()[1])
 if mode==1 and l.startswith(('ATOM','HETATM')):
  typ=l.split()[-1];el={'A':'C','OA':'O','NA':'N','HD':'H'}.get(typ,typ)
  if el!='H':y.append((el,tuple(float(l[a:a+8]) for a in (30,38,46))))
ss=0;details=[]
for el in sorted(set(a[0] for a in x)):
 a=[p for e,p in x if e==el];b=[p for e,p in y if e==el];assert len(a)==len(b)
 val=min(sum(math.dist(p,q)**2 for p,q in zip(a,perm)) for perm in itertools.permutations(b))
 ss+=val;details.append(dict(element=el,count=len(a),minimum_squared_distance_sum=val))
r=dict(method='Independent exhaustive same-element permutations, no alignment, first docked model; no producer parser or Hungarian routine reused',atoms=len(x),element_groups=details,rmsd_A=math.sqrt(ss/len(x)))
(out/'independent_rmsd.json').write_text(json.dumps(r,indent=2));print(r)
