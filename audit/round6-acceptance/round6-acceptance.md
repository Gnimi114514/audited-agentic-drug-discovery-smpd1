# Round 6 acceptance audit

**Overall: REJECT. G6 recommendation: remain BLOCKED.**

Fresh-session re-acceptance, 2026-09-14. Scope: the four claimed round-5 repairs plus the six requested residual checks. Producer artifacts were not modified. This decision concerns artifact acceptance, not experimental validation.

| Repair | Verdict | Independent evidence |
|---|---|---|
| R5-1 Pocket selector/analysis | **FAIL; numerical subcheck PASS** | WSL rerun gives 620 frames, crystal contacts **[318,319,457,458]**, ligand RMSD **mean 4.579 / max 5.935 Å**. Zero-based mapping 122→206 through 404→488 is reproduced. However, primary JSON has **no units_note**, and the script still fails to transform the crystal center into the fitted reference frame. |
| R5-2 MODEL-A disclosure | **PASS** | Both reports disclose raw-record legacy versus deduplicated refit and 1/26 agreement. `stochastic-approximate` is absent from hit-report.md. Final report explicitly withdraws estimator serialization and limits reproducibility to archived scores/refit outputs. |
| R5-3 Executed replay | **FAIL** | Windows rerun records **12 checks / 11 detected / 1 delegated**, not 13/12. R1-10 is computed but never recorded. Several checks still use hardcoded observations rather than the cited artifacts. Independent R1-10 RMSD is **1.756967144 Å**, confirming the numerical repair. |
| R5-4 Manifest freeze | **FAIL** | **51/55** root hashes/sizes match; both handoff checkers exit **1**. The five level counts are correct, but the freeze is stale. |

## Unclosed mandatory defects

**Pocket reference frame.** `scripts/pocket_residence_r5fix.py:83–88` assumes the raw crystal centroid is already in the minimized-reference frame. Independent Kabsch fitting of 2,112 matched backbone atoms maps the center from **(−13.7129, −34.0981, −28.7246) Å** to **(52.1805, 56.8840, 42.4398) Å**, a **132.9814 Å** displacement. The script applies no such transform before comparing ligand-center distances. Reproducing zero occupancy therefore does not validate that calculation. The requested contacts and RMSD genuinely reproduce; both superseded JSON files exist. The primary JSON is now a 733-byte summary/provenance object and lacks the claimed units note.

**Replay semantics.** The script never calls `rec()` for R1-10. R1-2 uses literal values and arithmetic, R3-1 supplies literal observation text and `True`, and R3-6 checks a literal three-score list instead of reading the cited table. R1-7 reads catalytic-residue distances despite describing Zn distances in its comment. Generic hash canaries and a source-substring check are executed, but are not historical artifact replay. The R1-3 Windows fallback occurs as designed; an independent WSL ParmEd check confirms **ε = 0.02662781997945352 kcal/mol**. This does not repair the submitted replay denominator or evidentiary limitations.

**Freeze.** Root mismatches are `pocket_residence.json`, `final-report.md`, `structure-analysis.md`, and `research-log.md`. Reports handoff fails artifacts **0, 2, 5**; evidence handoff fails artifact **15**. Exact expected/actual hashes and sizes are recorded in `manifest_checks.json`. The append-after-hash note exists but cannot make stale hashes pass. The root also omits the two new repair scripts and executed-replay output from its relevant leaf lists.

## Residual regression sweep

| Check | Verdict | Evidence |
|---|---|---|
| R5-T1 Correct contact narrative | **FAIL** | final-report.md:61 retains the obsolete non-catalytic-surface residue sentence; :210 lists only H319/T458; :223–224 still infers pocket occupancy from the retired COM-imaged metric. |
| R5-T2 Reference threshold | **FAIL** | hit-report.md:17 still claims the references yield ≤ −7.0, contradicting its −6.96/−6.34/−6.01 table. |
| R5-T3 Ensemble caveat | **FAIL** | structure-analysis.md:58–60 adds the correct ensemble disclosure, but :61–62 retains “and no ensemble docking was performed / campaign)”. |
| R5-T4 Labels and timing | **FAIL** | final-report.md:20–21 banner ranges remain unlabeled; :61 says v2 3.0 ns. The protocol gives 100 ps heat + 3.0 ns production, but never explicitly labels 3.1 ns total. Later mean/max labels do not fix the banner. |
| R5-T5 Occupancy specification | **FAIL; literal rewording PASS** | Abstract and Figure 4 acknowledge radius sensitivity and remove the requested literal wording. However, abstract :30 still claims the specification predates the run, and Figure 4 :343–345 attributes the conjunction to `md/bound_analysis_pre_registered.json`, which contains no occupancy criterion or 6 Å/4.5 Å thresholds. The unsupported provenance claim remains. |
| R5-T6 Manifest qualifications | **PASS** | Assembled manuscript Positioning :301–304 and Data availability :363–371 explicitly qualify verification with round-4 root/nested findings and unresolved integrity. |

## Execution and evidence

Both producer scripts were copied into this audit directory with output/temp paths redirected, leaving their computations unchanged. The Windows replay ran behind a file-write boundary guard; bytecode writes were disabled. Its full results and terminal completion were observed. PowerShell labeled TDC informational stderr as a native-command error, but there was no Python traceback or write-guard rejection. The pocket rerun exited 0. No training, docking, or new simulation was performed.

Evidence: `round6_checks.json` (per-check verdicts), `manifest_checks.json`, `pocket_rerun.json`, `pocket_stdout.txt`, `replay_results.json`, `replay_stdout.txt`, `independent_rmsd.json`, and `reference_and_zn.json`; corresponding audit scripts are retained here. Independent RMSD uses exhaustive same-element permutations on 11 heavy atoms, without superposition or reuse of the producer's assignment routine.

Acceptance requires correcting the remaining frame/specification and replay defects, propagating report corrections, restoring the units disclosure, and freezing current leaves before nested and root manifests. Require every root entry and both handoff checks to pass before another fresh acceptance review.
