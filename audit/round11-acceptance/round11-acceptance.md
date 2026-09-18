# Round 11 independent acceptance audit

**Overall: ACCEPT-WITH-MINOR-NOTES. G6 recommendation: CONDITIONAL for the frozen computational handoff. Close R10-1 and R10-2; retain inherited scientific limitations.**

Fresh checks executed on 2026-09-14 using Windows `C:/ProgramData/anaconda3/python.exe`. This review verifies the four requested repairs and current freeze, rather than repeating all historical scientific validations.

| Claim | Verdict | Independent evidence |
|---|---|---|
| R10-1: R3-6 replay hardened | PASS | Full producer replay exits 0 with 13 records, 12 detected and 1 delegated. R3-6 observes exactly `[-6.96, -6.34, -6.01]`, detected=true. R1-10 is present at `1.757 A`, detected=true. Missing-score and threshold mutations fail the check as expected. |
| R10-2a: withdrawn hit-report paragraph deleted | PASS | `Their docked scores here are` and `chemotypes still show that the pocket/protocol yields` are absent from hit-report.md. The corrected interpretation remains in structure-analysis.md. |
| R10-2b: dangling structure-analysis clause removed | PASS | `campaign); flexible-loop` is absent. The ensemble bullet contains `rotamer ensembles). Flexible-loop (SMD/MD) effects on the entry channel are unassessed.` |
| Root and handoff manifests rebuilt consistently | PASS | Independently recomputed all 77 SHA256 hashes and byte sizes: 77 match. Actual levels are L1=38, L2=15, L3=11, L4=2, L5=11. Both round-11 handoff checks exit 0 with mechanical_checks_passed=true and no errors. |

The unchanged R3-6 source block was executed against physical document copies retained in this audit directory. Only its document read was redirected; its parsing, assertions and detection expression were unchanged.

| Copy | Observed result |
|---|---|
| Baseline | Three expected negative scores; detected=true. |
| All three bold docking scores replaced with NA | AssertionError: expected 3 bold docking scores, got `[]`. Potency numbers no longer produce a false pass. |
| All three docking scores changed to -8.00 | Values `[-8.0, -8.0, -8.0]`; detected=false. |
| One docking score removed | AssertionError: expected 3 bold docking scores, got `[-6.34, -6.01]`. |
| Empty document | AssertionError: expected the combined reference line, found 0. |

Minor scope notes: R1-3 remains null/delegated because parmed is unavailable in this interpreter; this audit did not newly validate the topology through WSL. The 12 detected flags are replay outcomes, not 12 newly independent scientific validations. R3-6 is a format-specific check of the current combined line, not a general reference-table schema validator. The -8.00 mutation returns detected=false; the overall producer script does not use that boolean to force a nonzero process exit. Consumers must inspect the recorded outcomes. These notes do not reopen the demonstrated missing-score defect.

G6 may advance from the round-10 acceptance block to CONDITIONAL integration of this frozen computational evidence, retaining the existing scientific caveats and incomplete validations. Mechanical handoff checks explicitly report scientific_acceptance=NOT_ASSESSED; this acceptance does not imply experimentally validated affinity, selectivity, safety or synthetic feasibility.

Reproduction: run `python -B independent-audit/round11-acceptance/check_round11.py`. The replay wrapper executes the original producer source via runpy, redirects result/canary/temp writes into this audit directory, and installs a filesystem mutation guard. All 77 manifest-covered files were rehashed after execution and remained unchanged. No producer file was modified. The wrapper was copied from round 10 as execution infrastructure; all reported observations were freshly recomputed.

Detailed per-entry hashes, commands, exit codes, observations and mutation outcomes are in [round11_checks.json](round11_checks.json). Replay output and modified document copies are retained alongside it.
