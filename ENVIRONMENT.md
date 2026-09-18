# Execution Environment

The project was executed across a Windows host and WSL2. Exact availability should be re-probed before reproduction.

## Windows host

- Python 3.12
- RDKit
- AutoDock Vina 1.2.7
- Meeko 0.8.0
- DeepPurpose 0.1.5
- PyTDC
- scikit-learn
- matplotlib
- NVIDIA RTX 5080 Laptop GPU with 16 GB VRAM

## WSL2 CybergymUbuntu

- OpenMM 8.6.1
- pdbfixer
- mdtraj
- ParmEd
- AmberTools
- GROMACS 2026.3
- GNINA 1.3.3
- P2Rank 2.5.1
- AiZynthFinder 4.4.1

The repository does not bundle third-party binaries, model weights, or proprietary credentials. Several scripts record the original environment and absolute paths from the development machine; review them before reuse.
