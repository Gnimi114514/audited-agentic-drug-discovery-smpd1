# Independent Skill Forward Test

Date: 2026-09-13. Mode: audit-repair (acceptance audit only). Capability used: evidence-only, with deterministic local checks. Reviewer: independently delegated skill forward-test agent.

## Acceptance Decision

Reject the submitted experimental reference and bound-MD analysis revision. No scientific gate passes from this submission. G1 reference-control acceptance is FAIL because the supplied target IDs disagree; this does not establish that human SMPD1 itself is an invalid therapeutic target. G4 analysis acceptance is FAIL because duration, units and protein-backbone selection are invalid. G6 integration is BLOCKED pending corrected, independently reviewed evidence and a frozen manifest. Other stages were not assessed.

CONDITIONAL is not an appropriate waiver for the known identity and unit failures. The simulation having completed is operational evidence, not evidence of stable binding or potency.

## Evidence Examined

Applied `C:/Users/Gnimi/.codex/skills/ai-drug-discovery-team/SKILL.md`, `references/contracts.md`, and `references/scientific-gates.md`. Inspected `scripts/check_handoff.py` before using it. Project-relative input paths and SHA256 snapshots:

| Input | SHA256 |
| --- | --- |
| independent-audit/skill-validation/handoff.json | c3ec0f4ffa6c4eb365543008030fa5050ad98e7056518be63d799e7b47e7cdda |
| md/bound_log.csv | 0a453c7a831e1875d58ef9834cfb7365513c8941e702f5ac956781a51e271eb3 |
| md/bound_run.log | 959c6e33e37f907d100983cb1a0c8e1669f77f9a93399e15d047af7e17bf458c |
| scripts/bound_md.py | 55bbfd7d30f52e90a4e450e63b668763e2f8bc1eb8d3e6c1b9e6c3b7d356309e |

These hashes identify files read by this audit. They are not a producer manifest or proof that the script generated the archived outputs.

## Findings

1. **Experimental reference identity fails the supplied contract.** The handoff expects `CHEMBL2760` but supplies `CHEMBL4712`, activity ID `375432`, `= 1000 nM`, and organism `Homo sapiens`. Comparing these strings establishes inconsistency only. No authoritative target, assay, molecule or activity records were supplied or retrieved in this test. Neither the expected ID's mapping to human SMPD1 nor the reported activity's true target, species, endpoint, value or direct-inhibition interpretation has been independently established. Changing the ID or number to an expected value would not repair the evidence.

2. **The duration is 6.1 ns total, not 3 ns.** `scripts/bound_md.py:31` specifies a 2 fs timestep; line 62 runs 50,000 steps; lines 65-66 run three further segments of 1,000,000 steps each. Therefore total time is 3,050,000 * 2 / 1,000,000 = 6.1 ns: 0.1 ns labeled heating and 6.0 ns subsequent dynamics. The printed 1.0/2.0/3.0 ns entries correspond to cumulative 2.1/4.1/6.1 ns. Independently parsed CSV contains 1,220 records, steps 2,500 through 3,050,000, all intervals exactly 2,500 steps, ending at 6100.000000325234 ps. This corroborates engine-log time and reporter cadence. It does not verify the DCD frame count because no trajectory was opened.

3. **All three logged spatial metrics carry the wrong unit label.** Coordinates and reference are extracted in nm at lines 37 and 48; metrics at lines 49-59 have no conversion, but output uses `A`. The handoff's nm-to-angstrom factor of 1 is incorrect; the factor is 10. The final rounded log values 0.65, 0.19 and 12.54 numerically correspond to approximately 6.5, 1.9 and 125.4 angstrom, respectively. These are unit reinterpretations of rounded, methodologically flawed metrics, not newly validated RMSD/contact results.

4. **The backbone selection is not protein-specific.** Line 26 accepts atom names N/CA/C/O while excluding only residues LIG/ZN, allowing water oxygen. The raw run reports 23,796 selected atoms. The handoff declares 2,112 protein plus 21,684 water atoms, which sums to 23,796 and explicitly admits contamination. Exact class counts remain producer metadata: no topology was parsed to verify them. A water-contaminated fit cannot support a protein-backbone stability claim.

5. **The ligand/contact methods do not support the advertised interpretation.** Line 49 compares absolute ligand coordinates against the minimized reference with no protein/pocket fit; it is neither a fitted pocket-relative displacement nor a ligand-internal RMSD. Line 50 takes an unrestricted nearest Zn-to-ligand-atom Euclidean distance with no explicit minimum-image treatment or fixed donor tracking. No molecule-whole/imaging preprocessing appears before fitting. Periodic artifacts have not been quantified here. The minimized reference exists in memory in this script, but no explicit reference/system serialization is shown. The header's Li-Merz parameter claim has not been verified against a built system.

6. **Provenance is incomplete.** The handoff omits an artifacts section entirely and lacks the activity and MD scientific record fields required by contracts.md. Missing assay provenance, topology/system/reference hashes, atom mapping, actual force parameters and reproducible trajectory-analysis outputs prevent scientific acceptance even after mechanical errors are fixed.

## Actual Checks Performed

Ran the checker with all relevant sections required:

```text
python C:/Users/Gnimi/.codex/skills/ai-drug-discovery-team/scripts/check_handoff.py C:/Users/Gnimi/.zcode/workspace/default/cognition-drug-discovery/independent-audit/skill-validation/handoff.json --root C:/Users/Gnimi/.zcode/workspace/default/cognition-drug-discovery --require artifacts --require activity_controls --require md_checks
```

Exit code 1; `mechanical_checks_passed: false`; `scientific_acceptance: NOT_ASSESSED`. Reported errors: missing artifacts section, activity target/organism mismatch, and duration mismatch implying 6.1 ns.

Used `runpy.run_path` under `python -B` to call `check_bundle` on an in-memory handoff copy. Correcting only duration exposed `RMSD conversion mismatch: expected 10`. Also correcting the conversion exposed `backbone selection includes non-protein atoms`. Neither test modified the source handoff or supplied accepted evidence.

Read the CSV with PowerShell's structured CSV parser and explicit column names after skipping the literal header. The first attempt with `Import-Csv` treated its leading `#` header as a comment and produced a spurious 1,219-row parse. That result was discarded after inspection; the corrected parse retained all 1,220 data records and checked every step interval. Computed the four input hashes above with `Get-FileHash`.

No previous REPORT.md or conversation conclusions were read. No web retrieval, trajectory analysis, full MD, model training, experiments, nested agents, or original-file changes were performed. The sole written artifact is this assessment.

## Next Permitted Actions

1. Preserve the rejected submission and raw outputs. Have the coordinator record these objections and invalidate acceptance of dependent reference-based rankings, MD stability claims and integration conclusions. This audit did not edit shared gate state.
2. Recover authoritative local target/activity/assay/molecule records and resolve human SMPD1 identity, organism and measurement provenance. External retrieval requires a later task scope because this test prohibits web access. If no valid reference exists, mark it unavailable; do not manufacture a positive control or treat missing records as negative experiments.
3. Prepare a separate corrected analysis revision using the actual topology, trajectory, minimized reference and built system where available. Verify atom mapping and metal parameters; partition heating/production correctly; validate trajectory frames and periodic handling; use protein-only alignment and explicitly defined ligand/contact metrics with correct units. If essential artifacts are absent, record BLOCKED and identify exactly what a later authorized recovery or rerun must save. A new full MD run is not authorized by this test.
4. Attach real artifact hashes and complete scientific provenance to the new handoff. Re-run mechanical checks, then independently assess scientific gates. Resume expensive downstream stages only after relevant acceptance. Bounded evidence recovery and analysis repair may proceed without representing the failed evidence as accepted.

## Skill Defect Assessment

The skill led to the appropriate rejection and explicitly distinguishes mechanical checks from scientific acceptance. No material acceptance-policy defect was exposed in this bounded test.

A concrete diagnostic limitation was exposed: `check_handoff.py` raises on the first failed invariant in each record, so the first run concealed the simultaneously present unit and selection errors. A user who treats the error list as exhaustive could repair one field and overlook the remaining faults. The skill's scientific checklist catches them, and successive checks fail closed, so this did not cause false acceptance here. Accumulating independent field errors, or documenting first-error-per-record behavior in contracts.md, would improve repair efficiency. Metadata comparison itself cannot verify database truth, trajectory content or force-field validity; this limitation is clearly documented and is not a newly discovered defect.
