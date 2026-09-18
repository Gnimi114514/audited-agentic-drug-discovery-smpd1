# Round-4 verdict-authority adjudication

Date: 2026-09-14 (Asia/Shanghai). Role: adjudicator, acting under the user's explicit authority to resolve the authoring audit's verdict conflict.

**Final round-4 status: CONFIRM REJECT. Authority conflict: RESOLVED by this adjudication. G6 must remain BLOCKED pending repairs and a fresh acceptance check.**

This ruling is based on the preserved files and current mechanical verification, not a claim of personal recollection or authenticated knowledge of the earlier writer's identity. The requested premise that the acceptance cites post-repair evidence is contradicted by the artifacts.

## Chronology and revision identity

Times below are UTC on 2026-09-13 (add eight hours for local 2026-09-14). Filesystem modification times are supporting observations, not authenticated execution logs. Embedded timestamps and content/hash relationships carry more weight. Paths without a prefix in this section are under `independent-audit/round4-acceptance/`.

| Artifact | Project state represented | Timestamp/order evidence |
|---|---|---|
| `c2_evidence.json`, `c2_verify.py` | Saved MODEL-B AUC passes; only 1/26 legacy MODEL-A probabilities reproduced; no fitted estimators found. Canonical-deduplicated refit differs from legacy raw-data training. | Evidence mtime 16:16:05; script 16:15:57. Evidence explicitly says FAIL. |
| `c45_text_results.json`, `c45_text_checks.py` | D17/round-3 repair claims present, but integrated report contradictions remain; C4's narrow forbidden-claim check and C5 record/blocking check pass. | Evidence mtime 16:19:14; source hashes identify reviewed texts. |
| `c3_evidence.json`, `c3_verify.py` | Old `sections` root manifest: 18/19 matches, stale self-reference; R4 mechanical handoff 6/7, R4 evidence 38/38. | Evidence mtime 16:19:56; measured root SHA256 `269661dc838dc0b30c6a5e1e53a2ae46a8634adb9f6b2cec2c7d6c3c0aba0136`. |
| `c1_evidence.json`, `c1_verify.py` | Independent corrected analysis of existing trajectory: RMSD mean/max 4.579371/5.935443 A; catalytic contacts present. Captured producer summary still says 5.101/11.976 A and uses old residue labels. | Evidence mtime 16:31:06; script 16:30:39. Correct independent computation is not evidence that producer code was repaired. |
| `input_integrity.json` and baseline review | Hash-bound measured revision underlying rejection. | Mtime 16:36:01. Current small inputs differ only at `audit_manifest.json`, `hit-report.md`, and `research-log.md`; notably the producer analysis scripts, pocket output, MODEL-A CSV/provenance, and `final-report.md` still match baseline. |
| Preserved `concurrent-overwrite/verdict.md` and `round4_verdict.json` | Acceptance reinterprets the same evidence; no separate post-fix C1/C2/C3 evidence or input snapshot is supplied. C3 text still requires coordinator action before G6. | Copies mtime 16:37:45; JSON has date only. Their hashes are `6379d68afd872a53c445dcf084171c72499b3a46d7aa4b4f0ac4db03357c79d5` and `01053001a6764fd3849024fe7eb3305bb3fc94bc8397e35ae9738269d18fcd32`. |
| Current root `audit_manifest.json` and R5 handoffs | Later manifest structure removes self-reference and records the acceptance-file hashes and amended hit report, but not repaired C1/C2 source or final report. | Root embedded generation time `2026-09-14 00:36:43` has no timezone; consistent with 16:36:43 UTC if local. Content proves it froze acceptance bytes, regardless of clock interpretation. |
| `concurrent-overwrite/incident.json`, `source_drift.json` | Incident records replacement of verdict and changes to root manifest/hit report; not a successful post-fix verification. | Incident mtime 16:37:45; drift 16:39:23. Drift records root `269661…` to `a8b536…`, hit report `d6e10f…` to `be55e0…`. Two baseline snapshots are explicitly reported contaminated; they are not used as authoritative baseline copies here. |
| `assemble_acceptance.py`, current `round4_checks.json` and `verdict.md` | Reissued REJECT for measured revision, with incident annotation. Despite its filename, the assembler explicitly writes REJECT and C1/C2/C3 FAIL. | Script mtime 16:41:31; checks embedded `generated_at` 16:41:33.270587+00:00. Current checks are therefore a later reassembly of earlier measurements, not merely an untouched mid-session file. |
| Current `round4_verdict.json`, `delivery_integrity.json` | REJECT pointer and verified rejection delivery hashes. | Mtime 16:45:18. Current verdict hash equals delivery hash `37c0107049abe323f9b5f1cf48a5f50ecf008407630536249b084d54a21b0aa7`. |
| `verdict-authority-status.json` | Producer escalates conflict but asserts an unsupported pre-fix/post-fix distinction. | Mtime 16:46:59; subsequent to reissued rejection. |

All five requested session scripts were read. They write historical audit evidence or assembled output; none demonstrates a producer repair. They were not rerun because that would overwrite the preserved evidence. In particular, `assemble_acceptance.py` loads existing evidence, hardcodes the rejection findings, and can snapshot later inputs without recomputing C1-C3. Neither that script's later timestamp nor the acceptance document's heading establishes fresh validation.

## Authoritative verdict ruling

**The evidence-supported REJECT in `round4_checks.json` and the reissued `verdict.md` is authoritative for round 4, subject to this adjudication's more precise chronology and incident qualifications.** The earlier acceptance is retained as conflicting provenance, not a valid post-repair acceptance.

Direct parsed-object comparison establishes that `round4_checks.json` C1 `measured` equals the entire current `c1_evidence.json` summary, C2 `measured` equals current `c2_evidence.json`, and C3 `measured` equals current `c3_evidence.json`. All three comparisons returned **True**. There is no distinct post-fix evidence set behind acceptance:

- C1 acceptance says the data confirm “no-catalytic-contact claims” while reporting catalytic contacts at residues 318/319/457/458. H457 contacts occur in 620/620 frames. Strict 6 A center-plus-contact occupancy of zero does not mean absence of catalytic contacts. The current producer script still mixes A coordinates with nm box vectors and uses the ordinal-plus-one selection; the producer output retains the old summary.
- C2 acceptance attributes discrepancies to RF stochasticity. The saved evidence instead documents a changed training protocol and only 1/26 matching legacy values. Recomputed MODEL-B AUC does not validate MODEL-A identity or prove fitted-model serialization.
- C3 acceptance labels itself “FAIL-THEN-FIXED” while saying regeneration is still required. Its cited evidence is the old failing root/handoff measurement. Later self-hash removal is real, but does not retroactively turn that evidence into a passing check.

The earlier rejection concerns the measured repair revision; it must not automatically reject every possible later revision. Conversely, later file writes cannot supersede a measured rejection without valid repair evidence. Current checks below independently show that the present revision also cannot be accepted.

**Incident qualification:** actual differing verdict bytes are established by preserved copies, incident hashes, the root's acceptance hashes, and the current rejection/delivery hashes. The live paths were replaced/reissued. The records do not establish writer identity, malicious interference, or simultaneous execution; ordinary sequential writes by different processes remain possible. “Unknown concurrent writer” is the prior incident author's attribution, not independently proved here. Replacement alone does not decide authority: substantive evidence does. Even if the writes were normal sequential writes, the acceptance remains unsupported. The incident does not invalidate the unchanged numerical evidence.

## Current mechanical verification

Commands executed from project root, without producer repairs:

```text
python "C:/Users/Gnimi/.agents/skills/ai-drug-discovery-team/scripts/check_handoff.py" runs/audit-20260913/handoff-r5-reports.json --root . --require artifacts
exit code: 1
{
  "mechanical_checks_passed": false,
  "errors": [
    "artifacts[4]: artifact SHA256 mismatch"
  ],
  "scientific_acceptance": "NOT_ASSESSED"
}

python "C:/Users/Gnimi/.agents/skills/ai-drug-discovery-team/scripts/check_handoff.py" runs/audit-20260913/handoff-r5-evidence.json --root . --require artifacts
exit code: 1
{
  "mechanical_checks_passed": false,
  "errors": [
    "artifacts[5]: artifact SHA256 mismatch",
    "artifacts[25]: artifact SHA256 mismatch",
    "artifacts[26]: artifact SHA256 mismatch"
  ],
  "scientific_acceptance": "NOT_ASSESSED"
}
```

Independent streamed SHA256 and optional byte-size checks of every current root `levels` entry and R5 artifact produced:

```text
audit_manifest.json: 47/51 entries match; self_reference=false
  index 5: research-log.md mismatch
  index 25: independent-audit/round4-acceptance/verdict.md mismatch
  index 26: independent-audit/round4-acceptance/round4_verdict.json mismatch
  index 48: research-log.md mismatch (repeated in report level)
handoff-r5-reports.json: 4/5 match; index 4 = research-log.md
handoff-r5-evidence.json: 41/44 match
  index 5 = research-log.md
  index 25 = independent-audit/round4-acceptance/verdict.md
  index 26 = independent-audit/round4-acceptance/round4_verdict.json
```

The stale research-log hash is `a66fe96a5ead46f8ef7d41c4d5df932cbaf2dde5b5f7ffcc663f83a31274fed2`; current is `3b846393c022900bb276db2db51f052c02b3636c334ef7f3a188936ce10505d2`. The manifests still expect the preserved acceptance hashes above. Current `round4_verdict.json` hash is `509f29b7b06e3fa19c25133b63d22691a318eb8ce2017eedf1f660df18f6f9de`. Root entries for the R5 handoff files themselves match; matching outer hashes does not cure their stale internal references.

MODEL-B AUC was recomputed directly from `results/herg_central_repro/models/modelB_test_predictions.npz` using NumPy and SciPy average ranks for ties:

```python
z = np.load('results/herg_central_repro/models/modelB_test_predictions.npz')
y, s = z['y_true'], z['y_prob']
n1, n0 = int((y == 1).sum()), int((y == 0).sum())
auc = (rankdata(s)[y == 1].sum() - n1*(n1+1)/2)/(n1*n0)
```

```text
AUC 0.9091471448597943
n 61376; positive 2749; negative 58627; finite scores True
Rounded to four decimals: 0.9091 — PASS
```

## Remaining mandatory repairs

1. Repair the producer pocket-analysis unit, whole-molecule imaging, common-frame alignment, and residue mapping errors; regenerate analysis from the existing trajectory and verify against independent C1 results. Propagate correct RMSD and contact interpretation to reports and repair records. Remove the current final-report claim of established pocket occupancy from the old COM-imaged metric. No new MD production is required for these corrections.
2. Explicitly distinguish legacy MODEL-A from the canonical-deduplicated MODEL-A refit in both `hit-report.md` and `final-report.md`, with per-model attribution of probabilities and MODEL-B-only AUC. The current hit-report appendix calls the discrepancy “stochastic-approximate”; it does not identify the changed training protocol. The final report remains baseline-identical and still juxtaposes RF300 evaluation with legacy probabilities. A research-log/manuscript refit note does not repair those reports. Fulfill the fitted-estimator serialization claim or withdraw it and clearly limit reproducibility to saved-score evaluation.
3. Close the integrated-report findings R4-T1 through R4-T7 in the existing rejection: pocket interpretation, hERG attribution/AP labeling/unsupported novelty, mean/max range notation, old gate label, false reference-score threshold, ensemble-docking denial, and v1 topology provenance. Preserve C4's narrow PASS without treating it as a blanket consistency approval; obtain a fresh contextual review of the repaired reports.
4. After all leaf/report/provenance updates, regenerate both R5 handoffs and then the root manifest, using the authoritative rejection/adjudication rather than hashes of the superseded acceptance. Keep self-reference absent. Both requested handoff checks and every root entry must pass before claiming freeze completion. Preserve prior artifacts as history rather than silently rewriting historical evidence.

Of the three alleged minor closures, **self-hash removal is verified; nested-manifest closure fails; MODEL-A refit disclosure in both requested reports is not fulfilled**. Real-stock synthesis remains disclosed as NOT_RUN/PROXY; neither this ruling nor AUC verification authorizes scientific or wet-lab acceptance.

## Ruling on `verdict-authority-status.json`

“UNRESOLVED” was a reasonable producer escalation pending adjudication, but **is no longer the current authority status**. The conflict is **RESOLVED — CONFIRM REJECT** by this document. Its statement that the acceptance cites post-fix evidence is factually unsupported and is superseded by the object-equality, source-hash, and current-check findings above. Any paper or status summary should distinguish a resolved authority dispute from outstanding repair acceptance.

The historical status JSON and verdict artifacts are preserved unchanged; this requested adjudication is the controlling resolution. This closes A1-A5, not the mandatory repairs themselves.
