#!/bin/bash
python3 - <<'EOF'
import openmm, os, glob
base = os.path.dirname(openmm.__file__)
print('base:', base)
sos = glob.glob(base + '/**/*.so*', recursive=True)
print(len(sos), 'shared libs:')
for s in sos[:15]:
    print('  ', os.path.relpath(s, base))
plugins = glob.glob(base + '/lib/plugins/*')
for p in plugins[:10]:
    print('  plugin:', os.path.basename(p))
EOF
