# Round 9 independent acceptance audit

**Overall: REJECT. G6 recommendation: remain BLOCKED.**

Reviewed the supplied workspace on 2026-09-14. The final-byte freeze and replay counting are repaired, but the submitted source and reports do not support several other repair assertions. Matching hashes certify these bytes, not the correctness of their claims.

| Acceptance item | Verdict | Independently observed result |
|---|---|---|
| R8-1: manuscript post-hoc disclosure | FAIL | Both Results versions retain “fixed in advance”; the abstract retains before-run wording; Figure 4 lacks the claimed explicit post-hoc addition and numerical sensitivity disclosure. |
| R8-2: replay registration/counting | PASS | R1-10 append at source line 167 precedes counting at 173. Windows execution exits 0 and reproduces the complete saved JSON: 13 records, 12 true, one null (R1-3). |
| R8-2: artifact-backed checks | FAIL | R1-2 and R3-1 remain literal checks. R3-6 opens the report but discards signs and accepts missing or contradictory values. |
| R8-3: final-byte research-log freeze | PASS | research-log.md is 63,413 bytes; SHA256 matches both root freeze and reports handoff, including D22 addendum. Its repair assertions remain contradicted by the files. |
| Root manifest and both r9 handoffs | PASS with metadata note | All 75 hashes and byte sizes match; both check_handoff.py executions exit 0. Actual level counts are **38/15/11/2/9**, not advertised 39/15/11/2/9 (which would total 76). |
| R8-4: hit-report threshold | FAIL | The original erroneous “yields ≤ −7.0” statement remains. |
| R8-4: structure-analysis clause | FAIL, partial repair | Ensemble acknowledgment and scoped rotamer caveat are present, but the dangling “campaign);” remains. |
| R8-4: final-report contacts | PASS for numbers; wording/layout notes | All four frequencies match an independent recount of the 620 saved c1 frames. The row still says “pre-registered-style” and spans physical Markdown lines. |
| R8-4: retired-metric inference | PASS | Explicit supersession replaces the pocket-residence inference. |
| R8-4: canonical evidence citation | FAIL | final-report.md cites pocket_residence.json for 4.579/5.935 Å, but that artifact still reports 4.696/6.050 Å. |

## Mandatory findings

**R9-1 — Manuscript chronology remains contradictory (R8-1 open).** `paper/manuscript_results_discussion.md:82` and `paper/MANUSCRIPT_DRAFT_v1.md:203` say “occupancy criterion fixed in advance,” while their lines 96 and 217 say “added post hoc.” The assembled abstract at line 30 still says “an analysis specification recorded before the run.” Figure 4 at lines 336–342 cites the pre-registration-named JSON and only mentions unspecified radius sensitivity; it does not contain the claimed post-hoc disclosure or 8 Å → 30.3%, 10 Å → 100% figures. Those sensitivity figures are present in Results, which does not cure contradictory provenance elsewhere. `md/bound_analysis_pre_registered.json:15` explicitly states that occupancy was not in the original pre-registration. Results-section synchronization passes, but synchronizes the same error.

**R9-2 — Reproducing the replay output does not validate its detections (R8-2 partially open).** `scripts/findings_replay_executed.py:34–40` still compares literal 0.47 × 10 against literal 4.7, without opening bound_run.log or using a c1 first-frame value. Its purported log array also includes 2.96/3.59/4.39, whereas the actual bound_run.log prints ligand RMSD 0.47/0.56/0.69/0.65. `c1_evidence.json` frame 0 contains protein-frame RMSD 5.300237 Å; the source never reads that value for R1-2. These are different run/metric contexts and cannot simply be equated to prove conversion. R3-1 at lines 138–140 supplies a literal observation and unconditional True; the earlier c1 read for R1-7 does not make R3-1 artifact-derived.

R3-6 at lines 159–165 reads structure-analysis.md, but its regex captures only the unsigned `6.xx` part of a negative number, searches the entire document rather than the reference-table row, and never requires three valid observations. The actual execution reports **[6.96, 6.34, 6.01]**, then declares success against a negative threshold. Executing this exact block with an in-memory report variant containing −7.96 instead of −6.96 still returns True (and pulls 6.99 from an unrelated row). An empty report also returns True. See `replay_mutation_checks.json`. Preserve signs, parse the intended row, require the expected entries, and make missing/contradictory evidence fail. The 12 true flags are reproducible program output, not 12 independently established detections. R1-3 is correctly null; the script does not itself launch WSL, and this audit does not claim a new parmed verification.

**R9-3 — Report residuals remain (R8-4 partially open).** `hit-report.md:17` still states that the reference chemotypes yield ≤ −7.0, although its own table at lines 11–13 contains −6.96/−6.34/−6.01 (zero qualifying values). This also contradicts the correctly scoped internal-ranking explanation in `structure-analysis.md:38–43`. The latter's lines 58–61 acknowledge cross-crystal and MD-snapshot ensembles, but line 62 still starts with the dangling “campaign);”.

`final-report.md:213` still cites `runs/audit-20260913/tasks/sim-02/attempt-1/pocket_residence.json` for mean/max RMSD 4.579/5.935 Å. That artifact contains mean/max/final 4.696/6.050/5.753 Å and the rejected centroid-translation method. The separate r7 summary supplies 4.579/5.935/5.638 Å. Both are frozen, but the current citation has not been reconciled; the older canonical file still describes itself as superseding earlier methods instead of pointing to its replacement. This was explicitly part of round 8's R8-4 and remains open.

## Successful repairs and additional sweep notes

- Contact counts at `final-report.md:65–66` are correct: H457 620/620, N318 414/620, T458 23/620, H319 11/620. Recounting saved c1 frame arrays also gives joint occupancy 0/620 at 6 Å, 188/620 at 8 Å, and 620/620 at 10 Å. This is an artifact recount, not a fresh trajectory analysis.
- `final-report.md:229–232` explicitly retires the COM-imaged metric and makes no residence inference from it. That requested repair passes.
- The revised glance row at `final-report.md:63–66` still calls the criterion “pre-registered-style,” unlike the clear post-hoc disclosure at line 217. Splitting a table row over physical lines also breaks its GFM table structure. Use explicit post-hoc wording in the row and keep a valid table row.
- `final-report.md:225` says Zn distance “stays 5.6–6.6 Å” without restricting it to production snapshots, despite the full-frame 4.18–7.71 Å range at line 63. The manuscript makes that distinction explicitly. `paper/MANUSCRIPT_DRAFT_v1.md:363` still describes four manifest levels, while the root now contains five. These are surviving integration issues; this review does not assume they were newly introduced.
- The root manifest note claims L1 evidence 39; independent enumeration finds 38. All 75 actual entries pass. The older `paper/manuscript_revision_manifest.json` still has seven mismatches, retained in `manifest_checks.json` as a historical-snapshot limitation, not a failure of the new root hashes.

## Execution and write boundary

Only `independent-audit/round9-acceptance/` was written. `run_replay.py` runs the **unchanged producer source** through runpy using Windows `C:\ProgramData\anaconda3\python.exe` (Python 3.12.3, win32), with bytecode disabled. It redirects the producer JSON output, nested canary and temporary files into this audit directory and guards writes/removals outside it. TDC reads the existing local hERG_Central cache (306,893 rows); the live ChEMBL lookup succeeds. The initial PowerShell redirection reported native stderr as a shell error; a subsequent captured subprocess independently records Python exit code **0**, stdout and stderr in `replay_execution.json` and companion logs. Generated JSON equals saved producer JSON in full.

`check_artifacts.py` streams SHA256 over every root-manifest entry, checks sizes, and invokes the installed skill's `check_handoff.py` separately for both `handoff-r9-evidence.json` and `handoff-r9-reports.json`, with `--root` and `--require artifacts`. Both report mechanical checks passed and scientific acceptance NOT_ASSESSED. Detailed hashes and exact commands are retained in `manifest_checks.json`. `probe_replay.py` tests the unchanged R3-6 block against in-memory inputs only. The wording sweep covers hit-report, structure-analysis, final-report and both manuscript versions; `report_review.json` records the independent reviewer findings.

G6 must remain **BLOCKED** until the remaining claims, executable checks and canonical citations are actually repaired, outputs regenerated, and the final bytes frozen and independently rechecked. This audit does not waive upstream target-direction, short/unreplicated MD, omitted-C4, graph-aware redocking or real-stock synthesis limitations.
