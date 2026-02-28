---
name: ensemble-docking
description: Multi-engine ensemble docking pipeline for virtual screening. Use when docking ligand libraries against protein targets with tiered accuracy. Integrates Uni-Dock (GPU fast scan), DiffDock (deep learning), and GNINA (CNN scoring) for consensus-based hit ranking.
license: Apache-2.0
metadata:
  skill-author: PymolCode Team
  tier: production
---

# Ensemble Docking Pipeline

**Tiered accuracy. Consensus confidence. One command.**

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    ENSEMBLE DOCKING                      │
├─────────────────────────────────────────────────────────┤
│  Stage 1: Uni-Dock (GPU)     → Fast scan, top 100      │
│  Stage 2: DiffDock (Deep)    → Flexible binding, top 20│
│  Stage 3: Consensus Scoring  → Aggregated ranking       │
├─────────────────────────────────────────────────────────┤
│  Fallback: GNINA (CPU)       → CNN-scored Vina         │
└─────────────────────────────────────────────────────────┘
```

## CLI API

```bash
# Fast screening (Uni-Dock only)
pymolcode.dock --protein target.pdb --library compounds.sdf --mode fast

# Deep analysis (DiffDock only)
pymolcode.dock --protein target.pdb --library compounds.sdf --mode deep

# Full ensemble pipeline (recommended)
pymolcode.dock --protein target.pdb --library compounds.sdf --mode ensemble

# With options
pymolcode.dock \
  --protein target.pdb \
  --library library.sdf \
  --mode ensemble \
  --top-n 20 \
  --gpu 0 \
  --output results/
```

## Pipeline Modes

| Mode    | Stage 1    | Stage 2    | Output | Use Case |
|---------|------------|------------|--------|----------|
| `fast`  | Uni-Dock   | —          | 100    | Large library screening |
| `deep`  | —          | DiffDock   | 20     | Small set, high accuracy |
| `ensemble` | Uni-Dock | DiffDock | 20 | Production screening |

## Engine Specs

### Tier 1: Uni-Dock
- **Speed:** 50-100 ligands/sec (GPU), 6000/min
- **Accuracy:** Vina-compatible scoring
- **Best for:** Fast library scanning

### Tier 2: DiffDock
- **Speed:** ~1 ligand/sec (GPU)
- **Accuracy:** SOTA, diffusion-based, flexible receptor
- **Best for:** Deep binding analysis

### Tier 3: GNINA (Fallback)
- **Speed:** 1-2 ligands/sec (CPU)
- **Accuracy:** CNN-scored, better than vanilla Vina
- **Best for:** CPU-only environments

## Directory Structure

```
ensemble-docking/
├── SKILL.md                 # This file
├── references/
│   ├── uni-dock.md          # Uni-Dock integration guide
│   ├── diffdock.md          # DiffDock integration guide
│   ├── gnina.md             # GNINA fallback setup
│   ├── consensus.md         # Scoring methodology
│   └── outputs.md           # Result formats
└── scripts/
    ├── pipeline.py          # Main orchestration
    ├── stage1_unidock.py    # Fast scan module
    ├── stage2_diffdock.py   # Deep dock module
    ├── stage3_consensus.py  # Scoring aggregator
    └── fallback_gnina.py    # CPU fallback
```

## Output Format

```json
{
  "job_id": "dock_20260228_abc123",
  "protein": "target.pdb",
  "library_size": 10000,
  "mode": "ensemble",
  "results": [
    {
      "rank": 1,
      "ligand_id": "compound_0042",
      "unidock_score": -9.2,
      "diffdock_confidence": 0.89,
      "consensus_score": 0.92,
      "pose": "poses/compound_0042_best.pdb"
    }
  ],
  "timing": {
    "stage1_unidock": "45s",
    "stage2_diffdock": "180s",
    "stage3_consensus": "2s"
  }
}
```

## Quick Start

```python
from pymolcode.skills.research import EnsembleDocking

# Initialize pipeline
dock = EnsembleDocking(gpu=0)

# Run ensemble docking
results = dock.run(
    protein="target.pdb",
    library="compounds.sdf",
    mode="ensemble",
    top_n=20
)

# Access top hits
for hit in results.top_hits:
    print(f"{hit.ligand_id}: score={hit.consensus_score:.2f}")
```

## Consensus Scoring

**Formula:**
```
consensus_score = 0.4 × norm(unidock) + 0.6 × diffdock_confidence
```

Components:
- **Uni-Dock score:** Normalized binding affinity
- **DiffDock confidence:** Model certainty (0-1)
- **Optional GNINA CNNscore:** When CPU fallback used

## Requirements

- **GPU:** NVIDIA with CUDA 11.8+ (for Uni-Dock, DiffDock)
- **CPU:** 8+ cores (for GNINA fallback)
- **RAM:** 16GB minimum, 32GB recommended
- **Storage:** SSD for ligand libraries

## References

- [Uni-Dock Integration](references/uni-dock.md)
- [DiffDock Setup](references/diffdock.md)
- [GNINA Configuration](references/gnina.md)
- [Consensus Methodology](references/consensus.md)
- [Output Specifications](references/outputs.md)

---

*Designed by Daedalus. Built for elegance.*
