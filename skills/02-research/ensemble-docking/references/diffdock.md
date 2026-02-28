# DiffDock Integration

## Installation

```bash
pip install diffdock
# Or from source
git clone https://github.com/gcorso/DiffDock.git
```

## Model Types

- **DiffDock:** Standard diffusion model
- **DiffDock-BL:** Bigger model, higher accuracy
- **DiffDock-Pocket:** Pocket-aware scoring

## API Call

```python
from diffdock import DiffDock

dock = DiffDock(
    protein="protein.pdb",
    ligands="filtered.sdf",
    samples_per_complex=40,
    inference_steps=20,
    gpu=0
)

results = dock.run(top_n=20)
# Returns confidence scores (0-1)
```

## Output

- `confidence`: Model certainty (higher = better)
- `pose`: 3D binding conformation
- `rmsd`: Estimated RMSD to true pose
