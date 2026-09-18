# Pre-submission status for Scientific Reports

Date: 2026-09-18

## Decision

The local manuscript package has been revised into a pre-submission version, but it is not yet ready for journal upload. The paper can be developed as a transparent computational failure-analysis case study. It currently does not support claims that the audit has general sensitivity, that multi-agent execution improves scientific correctness, or that the SMPD1 candidates are validated leads.

## Completed in this revision

- Retitled the manuscript around the audited SMPD1 case study rather than an unscored three-arm comparison.
- Rewrote the abstract to distinguish the scientific case, development test, and feasibility pilot.
- Removed the zero-false-positive implication and the characterization of the seeded cases as an independently preregistered benchmark.
- Clarified that fresh-context use of the same model family is procedural separation, not model diversity or statistical independence.
- Reconciled the audit narrative with the iterative R1-R11 record and conditional G6 scope.
- Corrected the UniProt 2023 reference and the apo trajectory frame count in the SI index.
- Rewrote the cover letter for Scientific Reports and removed the Digital Discovery mismatch and reviewer placeholder.
- Produced new Word files without overwriting historical drafts.

## Submission blockers

1. **Public data and code deposit:** create a versioned public release with a persistent DOI, license, and complete inventory. Replace the temporary Data Availability statement before submission.
2. **Reference verification:** independently verify every bibliographic record and add complete numbered in-text citations. The existing `reference_verification.json` contains mismatched records and cannot certify the current reference list.
3. **Human scientific sign-off:** the named author must check the manuscript against raw artifacts, confirm the affiliation/contact/ORCID, approve the AI-use description, and take responsibility for every claim. AI-generated text cannot certify this step.
4. **Figure and source-data check:** confirm that all six figure panels reproduce the cited source files and that legends, units, denominators, and model versions match the accepted artifacts.
5. **Journal requirements:** re-check the live Scientific Reports author instructions at the time of upload, including article type, data policy, AI disclosure, file formats, declarations, and submission fields.

## Evidence that remains developmental

- The 15/18 result is coverage of a project-designed seeded test with a corrected label, not a held-out estimate of audit sensitivity.
- The 15 three-arm outputs show execution feasibility only. The tasks were not independently scored for scientific correctness, and the arms had unequal Agent-call budgets.
- The final computational acceptance was scoped and conditional. It did not establish affinity, efficacy, selectivity, safety, purchasability, synthesis feasibility, or experimental validation.
- A public DOI and reader-accessible repository are absent as of this status review.

## Files for human pre-submission review

- `paper/SR_MANUSCRIPT_PRESUBMISSION_v2.md` and `.docx`
- `paper/cover_letter_presubmission_v2.md` and `.docx`
- `paper/supporting_information_presubmission_v2.md` and `Supporting_Information_presubmission_v2.docx`

Do not upload the older files named `SUBMISSION_READY` without reconciling them against this status record.
