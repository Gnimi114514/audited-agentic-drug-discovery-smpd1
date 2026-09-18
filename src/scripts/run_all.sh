#!/bin/bash
# run_all.sh — one-command reproduction of the full pipeline (WSL + Windows hybrid).
# Run from the project root on Windows Git Bash. Requires: Windows python (rdkit,
# chembl client, tdc, deeppurpose), conda env `ob`, WSL envs per AUTOMATION.md.
set -e
cd "$(dirname "$0")/.."

echo "== Phase 1: target evidence =="
python scripts/ot_fetch_assoc.py
python scripts/ot_fetch_targets.py
python scripts/ot_scores_trends.py
python scripts/score_panel.py

echo "== Phase 2: dossier + novelty =="
python scripts/chembl_check.py
python scripts/pubmed_direction.py

echo "== Phase 3: structure, pocket, redocking + ensemble =="
python scripts/prep_5i85.py
# obabel receptor prep (add H, pH 7.4) then strip torsion records
OB="C:/ProgramData/anaconda3/envs/ob/Library/bin/obabel.exe"
"$OB" structures/5i85_recA_ZN.pdb -O structures/5i85_recA_ZN_prep.pdbqt -h -p 7.4
python - <<'EOF'
keep = [l for l in open('structures/5i85_recA_ZN_prep.pdbqt')
        if l.startswith(('ATOM', 'HETATM', 'TER', 'END'))]
open('structures/5i85_recA_ZN_rigid.pdbqt', 'w').writelines(keep)
EOF
./bin/vina.exe --config docking/redock_config.txt
python scripts/redock.py || true
python scripts/ensemble_prep.py && python scripts/ensemble_dock.py

echo "== Phase 4: library build + virtual screening =="
python scripts/build_library_v2.py
python scripts/diversity_prefilter.py
python scripts/rdkit_prepare.py data/dock_set.smi
python scripts/dock_runner.py '*.pdbqt'

echo "== Phase 5: triage + ADMET + novelty + selectivity =="
python scripts/triage.py
python scripts/pose_contacts.py
python scripts/admet_predict.py
python scripts/herg_dili.py
python scripts/herg_karim.py

echo "== Phase 6: expansion =="
python scripts/expansion.py

echo "== Phase 7: MD (apo frozen-pocket + bound with real Zn) =="
MSYS_NO_PATHCONV=1 wsl -d CybergymUbuntu -- bash -lc \
  'cd /mnt/c/Users/Gnimi/.zcode/workspace/default/cognition-drug-discovery && ~/miniforge/envs/md/bin/python scripts/md_run.py > md/md_run.log 2>&1 && ~/miniforge/envs/md/bin/python scripts/md_extract.py'
python scripts/md_ensemble_dock.py
MSYS_NO_PATHCONV=1 wsl -d CybergymUbuntu -- bash scripts/build_bound.sh
MSYS_NO_PATHCONV=1 wsl -d CybergymUbuntu -- bash -lc \
  'cd /mnt/c/Users/Gnimi/.zcode/workspace/default/cognition-drug-discovery && ~/miniforge/envs/md/bin/python scripts/bound_md.py > md/bound_run.log 2>&1'

echo "== Phase 8: CNN rescoring + pocket ML =="
MSYS_NO_PATHCONV=1 wsl -d CybergymUbuntu -- bash -lc \
  'export LD_LIBRARY_PATH=~/miniforge/envs/gnina12/lib; python3 scripts/gnina_rescore.py'
MSYS_NO_PATHCONV=1 wsl -d CybergymUbuntu -- bash scripts/p2rank_run.sh

echo "== Phase 9: reports are written by the agent at each gate (final-report.md) =="
echo "ALL PHASES COMPLETE"
