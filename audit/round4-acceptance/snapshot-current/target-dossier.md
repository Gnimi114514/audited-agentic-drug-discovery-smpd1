# Target Dossier: SMPD1 (acid sphingomyelinase) for cognitive impairment / Alzheimer's disease
(+ runners-up PLCG2 and INPP5D; scope: first-in-class small molecule, human)

## Verdict

**PROCEED (computational stage)** with SMPD1 as the primary structure-based design
target, PLCG2 carried as a high-genetics-confidence target requiring non-docking
modality discovery (activators), and INPP5D held pending direction resolution.
Strongest reason for the SMPD1 pick: it is the only finalist where the **modulation
direction was claimed consistently beneficial — **CORRECTED after external audit
(PMID 27598773 direction counterexample; direction REOPENED)** — but a **co-crystal
structure of the human enzyme with an active-site ligand exists** (PDB 5I85), and the
novelty claim **"no approved small molecule targets ASM" is verifiably true today**
(ChEMBL same-day check) — i.e. a first-in-class hypothesis that can actually be tested
by the docking funnel run in this project.

## Evidence matrix — SMPD1 (primary)

| Dimension | Evidence | Source (ID/date) | Direction | Confidence |
|---|---|---|---|---|
| Pathway/lipidomics | ceramide/sphingomyelin dyshomeostasis in AD; OT affected_pathway 0.85 | Open Targets 2026-09-12 (MONDO_0004975) | supports | medium |
| Literature (direction) | "ASM as pathological & therapeutic target in neurological disorders: focus on AD" | PMID 38337058 (2024) | supports (inhibit) — see counterexample row | medium |
| Literature (functional) | ASM inhibition reduces mitotoxic EV secretion from reactive astrocytes | PMID 37605262 (2023) | supports (inhibit) | medium |
| Behavior/memory link | ASM regulates social behavior and memory — **BUT the same paper reports ASM overexpression WITHOUT measured memory deficits and amitriptyline IMPAIRING object memory in female WT mice with overexpression protection — a direction counterexample** | PMID 27598773 (2016) | **contradicts uniform inhibition-benefit** | high |
| Animal models | Smpd1 KO: abnormal cerebral cortex morphology, abnormal ceramide, Purkinje degeneration, behavioral phenotypes | Open Targets mousePhenotypes (MGI) 2026-09-12 | supports (partial-inhibit strategy) | medium |
| Human genetics | **no association line found** (OT genetic_association = 0.0) | Open Targets 2026-09-12 | **gap** | high (absence checked) |
| Known drugs | no approved drug / no clinical candidate with ASM as primary target; olipudase alfa = enzyme-replacement biologic; tricyclics = functional side-activity; **corrected after external audit: the "1–6 µM dedicated inhibitors" are µM actives of SMPD2 (CHEMBL4712) — vs human SMPD1, the molecule CHEMBL310981 carries a 49 µM IC50 record (activity 375434); this is a single-molecule record, NOT a ranked best over all human-SMPD1 activity records (full target-wide activity survey NOT_RUN)** | ChEMBL re-verified 2026-09-13 | novelty+ (weakened ligand anchor) | high |
| Safety | not DepMap-essential (mean effect −0.113); no OT safety liabilities; biallelic LOF → Niemann-Pick A/B ⇒ **partial** inhibition only | Open Targets 2026-09-12 | manageable risk | high |
| Druggability | soluble lysosomal hydrolase, defined catalytic dizinc pocket; lysosomotropic amines accumulate in lysosome (functional-inhibitor class proves target engagement) | PDB 5I85; ChEMBL ligand set | supports | high |

## Evidence matrix — PLCG2 (runner-up 1)

| Dimension | Evidence | Source (ID/date) | Direction | Confidence |
|---|---|---|---|---|
| Genetics | OT genetic_association 0.854; rare protective GOF variant p.P522R | Open Targets 2026-09-12; PMID 28714976 (2017) | supports | high |
| Literature | PLCG2 downstream of TREM2 in microglia; variants alter microglial state (hiPSC) | PMID 40346446 (2025); 41066163 (2025); 41888907 (2026) | supports | high |
| Direction | "PLCG2 downregulation impairs synaptic function and increases AD hallmarks" | PMID 42601455 (2026) | supports **activation** | medium-high |
| Known drugs | **0 ChEMBL activity records, 0 mechanisms** — maximal novelty | ChEMBL 2026-09-12 (CHEMBL3608199) | novelty+ | high |
| Safety | immune-enriched expression; KO mice: B-cell/NK phenotypes; LOF-intolerant (gnomAD lof 1.0) | Open Targets 2026-09-12 | immune risk | medium |
| Druggability | Enzyme class; **no PDB structure**; required direction (activator) not addressable by standard docking | OT tractability; AlphaFold DB | gap for this modality | high |

## Evidence matrix — INPP5D/SHIP1 (runner-up 2)

| Dimension | Evidence | Source (ID/date) | Direction | Confidence |
|---|---|---|---|---|
| Genetics | OT genetic_association 0.730 (AD GWAS loci) | Open Targets 2026-09-12 | supports | medium-high |
| Literature | INPP5D regulates NLRP3 inflammasome in human microglia | PMID 38016942, 38017562 (2023) | supports (modulate) | medium |
| Literature | SHIP1 **limits** complement-mediated synaptic pruning | PMID 39657671 (2025) | supports **activation** | medium |
| Known drugs | no approved drug; rosiptor (AQX-1125, CHEMBL3989954) = SHIP1 **activator**, Phase 3 (non-CNS); tool inhibitors weak (Ki 3.9–81 µM) | ChEMBL 2026-09-12 | novelty+ (CNS) | high |
| Direction | **CONTESTED**: higher-expression risk haplotype (inhibit) vs pruning/inflammation evidence (activate) | as above | **unresolved** | — |
| Safety | immune KO phenotypes; not DepMap-essential (+0.222) | Open Targets 2026-09-12 | manageable | medium |
| Druggability | phosphatase; no OT pocket flags; no PDB catalytic-domain structure confirmed | OT tractability | gap | medium |

## Prioritization (top of 22-gene panel; full table in research-log.md)

| Gene | Weighted score | Why ranked here |
|---|---|---|
| HFE | 0.660 | top score but no small-molecule pocket → killed for this modality |
| PLCG2 | 0.655 | best human genetics of panel; activation direction ⇒ non-docking discovery path |
| SORL1 | 0.637 | no SM pocket → killed for this modality |
| TREM2 | 0.636 | antibody-first target; SM tractability false |
| ADAM10 | 0.623 | druggable protease but required direction = activation (hard) |
| **SMPD1** | **0.590** | **primary docking target: co-crystal structure exists, novelty verified; direction was claimed consistent — CORRECTED after external audit (PMID 27598773 counterexample; direction REOPENED; applicable model/sex/pharmacology confounders unresolved)** |
| INPP5D | 0.595 | held: direction contested |
| EPHA1 | 0.604 | kinase tractable; biology direction ambiguous; vandetanib "approval" = off-target listing |
| MAPT/CDK5/GSK3B/APH1B/CD33/ACE | ≤0.55 | clinical crowding / approved drugs → not first-in-class |

## Strongest case against the top pick

SMPD1 has **no human-genetic evidence line** — its AD linkage rests on lipidomics,
functional cell biology and animal models, which is the evidence class with the worst
attrition record in AD drug discovery (dozens of pathway-plausible targets have failed
clinically). The disease biology is also a *lipid overload* phenotype: complete enzyme
inhibition causes Niemann-Pick A/B, so the entire therapeutic window depends on
achieving stable **partial** inhibition in CNS macrophages — a bar no approved small
molecule has cleared for ASM; functional inhibitors (tricyclics) hit it incidentally
and only at µM concentrations with polypharmacy. Finally, lysosomal target engagement
for new chemotypes is unproven — the functional-inhibitor precedent is class-specific
(lysosomotropic cations). What would resolve it: (1) human genetics/lipidomics
replication — SMPD1-loss-of-function carrier lipidomics vs AD risk in biobank data;
(2) a cell assay showing partial-ASM-inhibition phenotype reversal in microglia/
astrocytes at ≤1 µM without phospholipidosis markers.

## Risks & limitations

- ChEMBL target IDs for SMPD1 include ortholog entries (bos taurus CHEMBL4295808 was
  queried first by name search) — human entry CHEMBL2760 used for all claims.
- Open Targets `drugAndClinicalCandidates` did not surface TREM2 antibody programs
  (AL002) — treat OT drug coverage as incomplete for biologics.
- "No approved drug targets X" claims verified 2026-09-12 against ChEMBL + OT only;
  patents were not searched (no PATSCOOP/eSpace access attempted) — patent novelty
  NOT assessed.
- DepMap essentiality is cancer-line based; CNS-resident-cell essentiality not captured.
- Microglial expression of the three genes is inferred from single-cell literature, not
  GTEx (OT baselineExpression returned no brain-region rows in the sampled subset).
