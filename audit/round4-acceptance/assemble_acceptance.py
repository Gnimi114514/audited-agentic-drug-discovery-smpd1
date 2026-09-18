"""Assemble reviewed evidence; writes exclusively to this audit directory."""
import json,hashlib,shutil
from pathlib import Path
from datetime import datetime,timezone
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]
def read(name):return json.loads((OUT/name).read_text(encoding='utf-8'))
c1=read('c1_evidence.json')['summary'];c2=read('c2_evidence.json');c3=read('c3_evidence.json');txt=read('c45_text_results.json')
cmd1="wsl -e bash -lc 'cd /mnt/c/Users/Gnimi/.zcode/workspace/default/cognition-drug-discovery && ~/miniforge/envs/md/bin/python independent-audit/round4-acceptance/c1_verify.py > independent-audit/round4-acceptance/c1_run.log 2>&1'"
cmd2="wsl -e bash -lc 'cd /mnt/c/Users/Gnimi/.zcode/workspace/default/cognition-drug-discovery && ~/miniforge/envs/md/bin/python independent-audit/round4-acceptance/c2_verify.py'"
cmd3='python independent-audit/round4-acceptance/c3_verify.py'
cmd45='python independent-audit/round4-acceptance/c45_text_checks.py'
findings=[
dict(id='R4-1',severity='P1',title='Pocket analysis still has unit/frame and residue-identity defects',locations=['scripts/pocket_residence.py:44','scripts/pocket_residence.py:73','scripts/pocket_residence.py:84','research-log.md:788'],evidence='c1_evidence.json',detail='Box vectors are nm but x and dcom are A; fractional imaging therefore uses the wrong box scale. Shifting group centroids also does not make bonded molecules whole. Protein/ligand/pocket are shifted separately. The crystal center must be aligned to the minimized-reference frame. MDTraj prmtop resSeq is zero-based here, whereas the script adds one to crystal ordinals. Its output labels are not crystal residue numbers. Correct heavy-atom MIC contacts include N318/H319/H457/T458, and protein-frame RMSD is 4.579/5.935 A mean/max, not 5.101/11.976.'),
dict(id='R4-2',severity='P1',title='New MODEL-A does not reproduce the legacy model predictions',locations=['scripts/herg_model_separation.py:4','scripts/herg_model_separation.py:62','scripts/herg_karim.py:24','research-log.md:794'],evidence='c2_evidence.json',detail='Only 1/26 candidate values match within 0.0005. The new script trains RF500 on canonical-deduplicated data, unlike the raw-data legacy script; it cannot be identified as the exact source of old probabilities. AUC 0.909147 belongs to MODEL-B.'),
dict(id='R4-3',severity='P2',title='Claimed fitted-model serialization is missing',locations=['scripts/herg_model_separation.py','runs/audit-20260913/gates.json:36'],evidence='c2_evidence.json',detail='Prediction arrays, CSV and provenance exist, but the script contains no fitted-estimator serialization and the designated model directory has no saved fitted models. Saved scores suffice for AUC recomputation but not replaying estimator inference.'),
dict(id='R4-4',severity='P2',title='Leaf-to-root manifest is not the claimed frozen four-level chain',locations=['audit_manifest.json','runs/audit-20260913/handoff-r4-mech.json'],evidence='c3_evidence.json',detail='Root contains 19 entries rather than L1=28/L2=10/L3=7/L4=2; its stale self-entry fails hash and byte size. Nested mechanical handoff research-log hash fails. Evidence handoff 38/38 passes.'),
]+txt['findings']
checks=[
dict(id='C1',verdict='FAIL',command=cmd1,evidence='c1_evidence.json',subchecks={'a_6A_occupancy':{'verdict':'PASS','value':0.0,'scope':'6 A crystal-center AND at least one 4.5 A catalytic heavy-atom contact; not absence of pocket contacts'},'b_no_catalytic_contacts':{'verdict':'FAIL','catalytic_residues':c1['catalytic_residues_ever_touched'],'frame_counts':c1['catalytic_frame_counts']},'c_mean_rmsd_approximately_5_1_A':{'verdict':'FAIL','measured':c1['ligand_protein_frame_rmsd_A']}},measured=c1),
dict(id='C2',verdict='FAIL',command=cmd2,evidence='c2_evidence.json',subchecks={'auc':{'verdict':'PASS','value':c2['auc_independent_rank_method']},'separate_columns':{'verdict':'PASS','columns':c2['csv_columns']},'CHEMBL7385_example':{'verdict':'PASS','MODEL_A':0.090},'legacy_values_reproduced':{'verdict':'FAIL','matched':c2['legacy_matches_at_legacy_precision'],'total':c2['n_candidate_rows']}},measured=c2),
dict(id='C3',verdict='FAIL',command=cmd3,evidence='c3_evidence.json',measured=c3),
dict(id='C4',command=cmd45,evidence_file='c45_text_results.json',**txt['C4']),
dict(id='C5',command=cmd45,evidence_file='c45_text_results.json',**txt['C5'])]
inputs=set(txt['source_sha256'])
inputs.update(['audit_manifest.json','runs/audit-20260913/handoff-r4-mech.json','runs/audit-20260913/handoff-r4-evidence.json','scripts/pocket_residence.py','scripts/herg_model_separation.py','scripts/herg_karim.py','md/bound_v2.dcd','md/complex.prmtop','md/bound_ref.pdb','structures/5i85_recA_ZN.pdb','structures/5i85_PC.pdb','results/herg_central_repro/models/modelB_test_predictions.npz','results/herg_central_repro/models/candidate_predictions_by_model.csv','results/herg_central_repro/models/model_provenance.json','results/herg_central_repro/split_indices.npz','results/herg_karim_predictions.csv','runs/audit-20260913/tasks/sim-02/attempt-1/pocket_residence.json'])
baseline=read('input_integrity.json') if (OUT/'input_integrity.json').exists() else None
snapshot=[]
for name in sorted(inputs):
    p=ROOT/name
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
    snapshot.append(dict(path=name,sha256=h.hexdigest(),bytes=p.stat().st_size))
    if p.suffix.lower() in ('.md','.py','.json','.csv') and p.stat().st_size<200000:
        dest=OUT/('snapshot-current' if baseline else 'snapshot')/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
for name,expected in txt['source_sha256'].items():
    if baseline is None:
        assert next(v['sha256'] for v in snapshot if v['path']==name)==expected, f'Source changed during review: {name}'
if baseline is None:
    (OUT/'input_integrity.json').write_text(json.dumps(snapshot,indent=2)+'\n',encoding='utf-8')
else:
    (OUT/'current_input_integrity.json').write_text(json.dumps(snapshot,indent=2)+'\n',encoding='utf-8')
result=dict(schema_version=1,audit_round=4,date='2026-09-14',generated_at=datetime.now(timezone.utc).isoformat(),role='Independent acceptance auditor',overall='REJECT',recommended_G6='BLOCKED',scope='C1-C5 acceptance of producer round-3 repairs/D17; no source repair, MD production, model training or wet-lab validation',capability='partial-compute: trajectory/numerical recomputation and evidence/text review',checks=checks,findings=findings,input_integrity='input_integrity.json',source_writes='Only independent-audit/round4-acceptance/',limitations=['Occupancy is threshold-dependent; 0% at 6 A is not absence of catalytic contacts or proof of nonbinding.','AUC recomputed from saved labels/scores; no model retraining or external dataset revalidation.','C4 PASS applies to the enumerated forbidden factual claims, not all report consistency.','C5 PASS means repair records exist and G6 is BLOCKED; repair claims themselves fail C1-C3.'])
(OUT/'round4_checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
sensitivity=c1['occupancy_centroid_radius_sensitivity']
report=f'''# Round 4 independent acceptance audit

Date: 2026-09-14. **Overall: REJECT. G6 must remain BLOCKED.**

The numerical AUC repair is reproducible, and several obsolete statements are withdrawn. The trajectory repair, legacy-model identity, and nested manifest still fail acceptance. This review analyzed existing evidence only; no MD production or model training was run. All new files are confined to `independent-audit/round4-acceptance/`. Input hashes and small-file snapshots are preserved in `input_integrity.json` and `snapshot/`.

| Check | Verdict | Independently measured evidence |
|---|---|---|
| C1 trajectory | **FAIL** | 620 frames; 6 A occupancy 0% (**a PASS**), but catalytic contacts N318/H319/H457/T458 (**b FAIL**); protein-frame RMSD mean **4.579371**, max **5.935443**, final **5.637881 Å** (**c FAIL**, versus claimed 5.101/11.976). Command A. |
| C2 hERG | **FAIL** | AUC **0.9091471448597943** (**PASS**); separate A/B columns (**PASS**); CHEMBL7385=0.090 (**PASS**), but only **1/26** legacy probabilities reproduced (**FAIL**). Command B. |
| C3 manifests | **FAIL** | Root **18/19** entries match; mechanical handoff **6/7**; evidence handoff **38/38**. Root is a 19-entry delta manifest, not the claimed four levels. Command C. |
| C4 enumerated factual claims | **PASS** | No surviving unqualified facts among the enumerated obsolete claims in the four reports. Historical withdrawals, scoped 49 µM record and explicitly uncomputed future suggestions are not counted as asserted obsolete facts. Broader contradictions are listed separately below. Command D plus full contextual reading. |
| C5 repair record/G6 | **PASS** | D17 exists; round-3 history exists; both `G6-audit.outcome` and `team_skill_gate_state.G6_integration` are **BLOCKED**. Record presence does not validate repair claims. Command D. |

Commands run from the project root:

```text
A: {cmd1}
B: {cmd2}
C: {cmd3}
D: {cmd45}
```

## C1: occupancy is definition-dependent; contact and RMSD claims are refuted

The independent implementation (`c1_verify.py`) uses the largest covalent molecule (8,214 atoms), its N/CA/C/O backbone (2,112 atoms), and 36 ligand heavy atoms. MDTraj makes bonded molecules whole and images them around the protein; all operations remain in nm until reporting Å. Each frame is backbone-fitted to the identically imaged minimized reference, and the same transform is applied to the ligand. Crystal residue identity is mapped by ordered protein residues; the PC centroid is transformed into the reference frame using 2,112 corresponding crystal backbone atoms. Contacts use periodic minimum-image heavy-atom distances, independently of the fit.

At center radius 6 Å plus at least one catalytic-residue contact within 4.5 Å, occupancy is 0/620 with either a geometric ligand centroid or mass-weighted heavy-atom COM. Geometric center distance is min **6.5545**, mean **8.3037**, max **9.9930 Å**. Sensitivity at 8 Å is **{sensitivity['8']*100:.2f}%**, and at 10 Å is **{sensitivity['10']*100:.2f}%**. Thus the zero is specific to a strict center definition; it cannot establish that the ligand never touches the catalytic pocket.

| Catalytic crystal residue | Frames with a heavy-atom contact ≤4.5 Å |
|---|---:|
| N318 | 414/620 |
| H319 | 11/620 |
| H457 | 620/620 |
| T458 | 23/620 |

The other seven specified catalytic residues have zero contacts. Nearest catalytic-residue distance across frames is min **2.6322**, mean **3.0168**, max **3.9267 Å**. Full contacted crystal-residue lists and per-frame evidence are in `c1_evidence.json`.

**R4-1 [P1]:** `scripts/pocket_residence.py:73–88` multiplies coordinates by 10 to Å but uses nm box vectors in the fractional-coordinate imaging calculation. Translating independently chosen groups does not make molecules whole. At `:44–46` it also assumes one-based topology `resSeq`; the loaded prmtop uses zero-based `resSeq` here. E.g. catalytic H457 is topology residue 373, but the script selects 374. Its reported labels 235/342/374/375/376/405 are topology labels, not crystal identifiers; they map to 319/426/458/459/460/489. Even those labels cannot support “none catalytic.” The independent RMSD agrees with the earlier round-3 recomputation, not the new 5.101/11.976 Å claim. No new MD run is needed to repair these analysis defects.

## C2: AUC passes, legacy attribution and serialization do not

`c2_verify.py` calculates a tie-aware Mann–Whitney/rank AUC directly from the saved `y_true/y_prob`, without importing the producer script. There are **61,376** test samples: **2,749** positive and **58,627** negative. Test indices exactly match the saved test split and have zero overlap with saved training indices. AUC rounds to **0.9091**.

The CSV contains `MODEL_A_RF500_fulldata_prob` and `MODEL_B_RF300_split_prob`. Comparing all 26 rows with `results/herg_karim_predictions.csv` at legacy rounding tolerance 0.0005 gives only one match:

| Candidate | Legacy RF500 value | New MODEL-A | MODEL-B |
|---|---:|---:|---:|
| CHEMBL7385 | 0.090 | 0.0900 | 0.1067 |
| CHEMBL48767 | 0.118 | 0.0893 | 0.1267 |
| CHEMBL6729 | 0.058 | 0.0600 | 0.0533 |
| CHEMBL24974 | 0.258 | 0.2500 | 0.2700 |
| CHEMBL54786 | 0.328 | 0.3920 | 0.3598 |

**R4-2 [P1]:** The new RF500 is trained on canonical-deduplicated data, while `scripts/herg_karim.py` trains on the raw records. MODEL-A therefore cannot be attributed as the exact source of the old probabilities. Preserve the old model identity separately or explicitly label this as a new refit. MODEL-B's held-out performance must not validate either legacy or refit-A values.

**R4-3 [P2]:** `scripts/herg_model_separation.py` saves predictions and provenance, not fitted estimators. No saved estimators are present in the designated models directory, and no `.joblib/.pkl/.pickle` estimator files were found under results. The “models ... serialized” claim in `gates.json:36` is unfulfilled. This does not prevent the AUC computation above, but does prevent replaying inference from the claimed serialized models.

## C3: the nested hash failure recurs

**R4-4 [P2]:** `audit_manifest.json` currently has sections reports=5, new_analysis=6, audit=5, scripts=3, not the claimed L1=28/L2=10/L3=7/L4=2. All 18 non-self root entries match; its self-entry points to an earlier 8,025-byte manifest, whereas the actual file is 3,214 bytes. Root hash expected `673a92cc92a64234478d7cd7d6d4c22f1f099e9ee7d3961c9cc0250d98031c93`, actual `269661dc838dc0b30c6a5e1e53a2ae46a8634adb9f6b2cec2c7d6c3c0aba0136`.

The mechanical handoff's `research-log.md` hash is expected `e38ac713120a7e6e010527fe2fb768c80431d46a97c1be22283250bd47a2eb3b`, actual `a66fe96a5ead46f8ef7d41c4d5df932cbaf2dde5b5f7ffcc663f83a31274fed2`. Other six reports match. The evidence handoff's 38 references all match, including the current MD topology, coordinates and trajectory. Matching the outer hashes of nested manifests does not repair their internal references. Freeze leaves first, generate handoffs next, and generate the root last; omit self-reference or freeze it externally.

## C4/C5 scope and remaining report inconsistencies

C4 passes its specific forbidden-fact list: full 12-6-4 and maintained 1.9 Å coordination are not asserted as current verified facts; inhibition/direction claims are withdrawn or REOPENED; the old 1–2 µM human-SMPD1 anchors are withdrawn. The 49 µM CHEMBL310981 result is correctly scoped. `hit-report.md:123–124` uses “de-risk” for an explicitly uncomputed future analog suggestion, while `final-report.md:228` says “not a de-risking guarantee.” Those are not achieved-risk-reduction facts. Element-swap wording at `structure-analysis.md:28` now disclaims chemical-equivalence awareness, and `target-dossier.md:63` states direction REOPENED.

C5 passes record presence and blocking status. D17 (`research-log.md:784–820`) and the round-3 history in `gates.json:33–37` record the repairs; `gates.json:5` and `:51` retain BLOCKED. Their assertions that all repairs succeeded are not accepted evidence.

Additional unresolved findings, with exact quotations in `c45_text_results.json`:

- **R4-T1 [P1]** `final-report.md:210–211` still says “The ligand remains in the pocket region ... pocket occupancy without metal coordination,” while its gate table says occupancy 0% and non-catalytic contacts. Neither broad interpretation is justified by the strict occupancy metric; the catalytic-contact denial is directly refuted above.
- **R4-T2 [P1]** `final-report.md:221–229` still places RF300 AUC beside old candidate probabilities without A/B attribution. It also labels AP as PR-AUC and retains an unsupported “novel scaffolds” characterization. The new CSV has not repaired the integrated narrative.
- **R4-T3 [P2]** `final-report.md:20–21` still renders mean/max values as 1.85–2.37 and 2.18–2.68 Å ranges, despite explicit mean/max labels at `:173–177`.
- **R4-T4 [P2]** `final-report.md:60` still includes `old-G5 PASS` outside the historical mapping table. Most rows were converted, but the claim of exclusive team numbering is false; nonstandard composite statuses also remain.
- **R4-T5 [P2]** `hit-report.md:17` still claims the reference chemotypes yield ≤−7.0 scores, although the listed values are −6.96/−6.34/−6.01. `structure-analysis.md` corrected this, but the hit report did not.
- **R4-T6 [P2]** `structure-analysis.md:58–59` still says no ensemble docking was performed, contradicting its `:34` cross-crystal results and D17's claim of removal.
- **R4-T7 [P2]** `final-report.md:22–23` and `:168–170` still cite current `complex.prmtop` for v1 parameter verification, although that path now contains v2. D17 acknowledges the overwrite, but the report lacks the explicit v1 snapshot reference.

Acceptance requires correction of C1–C3 and propagation of those corrections through the integrated reports and a freshly frozen manifest. This rejection is of the repair revision, not evidence that the target or candidates are experimentally ineffective. No producer gate files were changed by this review.
'''
incident=OUT/'concurrent-overwrite'/'source_drift.json'
if incident.exists():
    result['concurrent_modification']=read('concurrent-overwrite/source_drift.json')
    result['findings'].append(dict(id='R4-5',severity='P1',title='Concurrent audit-output overwrite and source drift',evidence='concurrent-overwrite/source_drift.json',detail='An unknown writer replaced verdict.md with unsupported acceptance and modified audit_manifest.json and hit-report.md during final validation. This audit did not write those source files. Verdict covers the measured revision identified by input_integrity.json; later source changes are not accepted.'))
    (OUT/'round4_checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    report+='\n## Concurrent modification detected during delivery\n\n**R4-5 [P1]:** An unknown concurrent writer replaced `verdict.md` with an unsupported acceptance recommendation and added `round4_verdict.json`. Neither reviewer subagent authored these outputs. The conflicting files are preserved under `concurrent-overwrite/` solely as incident evidence. The same validation detected changes to `audit_manifest.json` and `hit-report.md` after measurement. This auditor did not modify either source. Their before/after hashes are in `concurrent-overwrite/source_drift.json`; the REJECT verdict applies to the measured revision fixed by `input_integrity.json`, not an acceptance of later edits. An attempted reassembly copied those two changed files into `snapshot/` before its source-change assertion stopped; those two snapshots are therefore explicitly invalid as baseline copies. Original measured hashes and quoted text remain in `c3_evidence.json` and `c45_text_results.json`. `snapshot-current/` and `current_input_integrity.json` identify the subsequently observed files. The authoritative outputs are `verdict.md` and `round4_checks.json`; the incident acceptance is not a valid audit conclusion.\n'
(OUT/'verdict.md').write_text(report,encoding='utf-8')
print(json.dumps({'overall':result['overall'],'checks':{x['id']:x['verdict'] for x in checks},'findings':len(findings),'input_hashes':len(snapshot)}))
