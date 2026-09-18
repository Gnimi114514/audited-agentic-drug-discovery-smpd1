# Round 10 independent acceptance audit

**Overall: REJECT. G6 recommendation: remain BLOCKED.**

Independent commands run on 2026-09-14 confirm the chronology and manifest repairs, but the replay missing-evidence defect and two report residuals remain.

| Producer claim | Verdict | Evidence |
|---|---|---|
| 1. Occupancy chronology | PASS | Both Results versions say defined during audit-driven analysis after the run; abstract and Figure 4 disclose post-hoc provenance. Figure 4 includes 8 A ? 30.3%, 10 A ? 100%. Final-report glance row says post-hoc-defined. The JSON post_hoc_additions agrees. Results synchronization passes. |
| 2. Replay hardening | FAIL, partially repaired | Windows execution produces 13 records, 12 true, one null. R1-2/R3-1 read artifacts and assert discrepancies. R3-6 preserves signs but counts potency numbers as docking evidence and still passes when all three docking scores are missing. |
| 3. Report residuals | FAIL, partially repaired | The hit-report threshold assertion and structure-analysis dangling clause remain. Final-report's r7 evidence citation and superseded-history wording are repaired. |
| 4. Manifest and metadata | PASS | All 76 SHA256 hashes and sizes match. Actual levels are 38/15/11/2/10. Both r10 check_handoff.py runs exit 0. |

## Mandatory findings

**R10-1 ? R3-6 still accepts missing docking evidence.** `scripts/findings_replay_executed.py:172-184` scopes the parser to lines containing the three reference CHEMBL identifiers. The actual document stores all three references on one table line, with potency numbers as well as docking scores. Execution extracts `[1.0, -6.96, 1.8, -6.34, 1.0, 3.3, -6.01]`. The `len(vals) >= 3` assertion therefore does not establish three docking-score observations. Executing the unchanged block against an in-memory variant replacing all three bold docking scores with NA returns `[1.0, 1.8, 1.0, 3.3]` and **detected=True**. This is a demonstrated false pass. Parse one docking-score field for each expected identifier and require all three. The empty-document variant now raises AssertionError, and changing ?6.96 to ?7.96 returns False: those repairs work.

**R10-2 ? Two claimed report removals were not made.** `hit-report.md:15-19` still contains the withdrawn-anchor paragraph, including ?chemotypes still show that the pocket/protocol yields ? ?7.0 scores?. Its three reference scores are ?6.96/?6.34/?6.01, so none supports that assertion. `structure-analysis.md:62` still contains ?campaign); flexible-loop (SMD/MD) effects on the entry channel are unassessed.? Remove/rewrite the residual claims, then freeze the final bytes again.

## Execution and interpretation

Windows `C:/ProgramData/anaconda3/python.exe -B independent-audit/round10-acceptance/run_replay.py` executes the unchanged producer source through runpy. It exits 0; the new JSON exactly equals the saved producer JSON. Counts are derived after all 13 registrations. R1-3 remains null because parmed is unavailable; no new WSL parameter verification was performed. Live ChEMBL succeeds; local TDC data contains 306,893 rows.

R1-2 reads the heat-line print 0.47 and c1 frame-0 RMSD 5.300237293 A; its 1.5 A tolerance accepts 4.70 versus 5.30. R3-1 reads retired last print 0.65 and c1 mean 4.579 A; its discrepancy assertion passes for 6.50 versus 4.579. These are now artifact-backed checks, but comparisons across different metric/time contexts do not alone prove the causal unit/frame explanation. The 12 true flags describe replay outputs, not 12 newly independent scientific validations.

`check_artifacts.py` independently streams hashes and checks byte sizes for every root entry, then invokes the installed `check_handoff.py` for both `handoff-r10-evidence.json` and `handoff-r10-reports.json` with `--root` and `--require artifacts`. Both pass mechanical checks; scientific acceptance is not assessed by that checker. L1 metadata correctly says 38. The older manuscript revision manifest retains seven mismatches and is a historical-snapshot limitation, not a failure of the current root freeze.

Minor surviving presentation/scope notes: final-report's glance row spans physical Markdown lines; line 226 gives 5.6?6.6 A without the manuscript's production-snapshot qualification. The corrected final-report citation points to the r7 summary, whose mean/max are independently read as 4.579/5.935 A; the older file is explicitly labeled superseded r5fix history.

Only `independent-audit/round10-acceptance/` was written. The replay wrapper redirects JSON, canary and temporary writes there and guards filesystem mutations outside it. Evidence is retained in `round10_checks.json`, `replay_execution.json`, `replay_mutation_checks.json`, `manifest_checks.json`, and companion source/report checks. No producer artifact was edited. G6 remains BLOCKED pending correction of R10-1/R10-2 and a fresh freeze/recheck; this review does not waive the existing scientific gate limitations.
