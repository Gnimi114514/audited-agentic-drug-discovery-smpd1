"""Apply deterministic citation and figure-callout edits to the SR manuscript source."""

from pathlib import Path


PATH = Path(__file__).resolve().parents[1] / "paper" / "SR_MANUSCRIPT_PRESUBMISSION_v2.md"

REPLACEMENTS = {
    "SMPD1 (acid sphingomyelinase, UniProt P17405; EC 3.1.4.12) and cognitive impairment provide the case-study context.":
        "SMPD1 (acid sphingomyelinase, UniProt P17405; EC 3.1.4.12) and cognitive impairment provide the case-study context [23].",
    "SMPD1 catalyzes the hydrolysis of sphingomyelin to ceramide and phosphocholine in the lysosome.":
        "SMPD1 catalyzes the hydrolysis of sphingomyelin to ceramide and phosphocholine in the lysosome and has been discussed in neurological disease contexts [14-16].",
    "Contemporary computational workflows draw on": "Contemporary computational workflows draw on",
    "A 22-gene evidence matrix was assembled from Open Targets GraphQL associations, PubMed literature trends, ChEMBL target records, and per-target safety annotations.":
        "A 22-gene evidence matrix was assembled from Open Targets GraphQL associations [1], PubMed literature trends, ChEMBL target records [2,12], and per-target safety annotations.",
    "structure availability (PDB 5I85 with co-crystal phosphocholine)":
        "structure availability in the Protein Data Bank [24] (PDB 5I85 with co-crystal phosphocholine)",
    "The docking protocol was checked by redocking":
        "The docking protocol was checked with AutoDock Vina [3] by redocking",
    "P2Rank 2.5.1 independently ranked": "P2Rank 2.5.1 [6] independently ranked",
    "with the 12-6 subset of the 12-6-4 set": "with the 12-6 subset of the 12-6-4 parameter set [18]",
    "Neither result establishes absence of binding or stable metal coordination.":
        "Neither result establishes absence of binding or stable metal coordination (Figure 4).",
    "Three model artifacts are distinguished.":
        "Three model artifacts are distinguished using data resources and modeling tools described below [7,8] (Figure 5).",
    "The AiZynthFinder installation was checked": "The AiZynthFinder installation [9] was checked",
    "Open Targets GraphQL API v4 (": "Open Targets GraphQL API v4 [1] (",
    "ChEMBL REST API v33 was queried": "ChEMBL REST API v33 [2,12] was queried",
    "PDB 5I85 (human ASM": "PDB 5I85 [24] (human ASM",
    "AutoDock Vina 1.2.7 docking": "AutoDock Vina 1.2.7 [3] docking",
    "A 20,111-molecule library was retrieved from ChEMBL (":
        "A 20,111-molecule library was retrieved from ChEMBL [2,12] (",
    "via RDKit FilterCatalog)": "via RDKit FilterCatalog [10])",
    "Ligands were prepared with RDKit ETKDGv3": "Ligands were prepared with RDKit ETKDGv3 [10]",
    "OpenMM 8.6.1 (": "OpenMM 8.6.1 [4] (",
    "DeepPurpose 0.1.5 (": "DeepPurpose 0.1.5 [7] (",
    "Trained from TDC datasets.": "Trained from Therapeutics Data Commons datasets [8].",
    "AiZynthFinder 4.4.1 with": "AiZynthFinder 4.4.1 [9] with",
}


def main():
    text = PATH.read_text(encoding="utf-8")
    for old, new in REPLACEMENTS.items():
        if old == new:
            continue
        count = text.count(old)
        if count != 1:
            raise RuntimeError(f"Expected exactly one occurrence, found {count}: {old}")
        text = text.replace(old, new)
    related = (
        "AI-agent systems for drug discovery and chemistry have combined tool use with role specialization, "
        "while scientific workflow research has established provenance and reproducibility as distinct requirements."
    )
    addition = related + (
        " Contemporary computational workflows draw on docking [3,5], pocket prediction [6], predictive "
        "modeling [7,8], retrosynthesis [9], and protein-structure prediction [22]."
    )
    if text.count(related) != 1:
        raise RuntimeError("Related-work anchor missing or duplicated")
    text = text.replace(related, addition)
    properties = "Meeko 0.8.0 generated PDBQT files."
    property_note = properties + (
        " Molecule identifiers were cross-checked against PubChem where applicable [11]. Calculated property "
        "definitions were interpreted against established drug-likeness, solubility, and permeability literature [19-21]."
    )
    if text.count(properties) != 1:
        raise RuntimeError("Property anchor missing or duplicated")
    text = text.replace(properties, property_note)
    text = text.replace(
        "PubMed literature trends, ChEMBL target records [2,12]",
        "PubMed literature trends informed by Alzheimer's disease genetics [13], ChEMBL target records [2,12]",
    )
    text = text.replace(
        "**Pocket-residence analysis:** scripts/pocket_residence_r7.py;",
        "**Pocket-residence analysis:** scripts/pocket_residence_r7.py, with trajectory handling cross-checked against MDAnalysis conventions [17];",
    )
    PATH.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
