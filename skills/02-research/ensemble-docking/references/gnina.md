# GNINA Fallback

## When to Use

- No GPU available
- Validation of top hits
- Cross-method verification

## Installation

```bash
# Download binary
wget https://github.com/gnina/gnina/releases/download/v1.1/gnina
chmod +x gnina
```

## API Call

```python
import subprocess

def gnina_dock(protein, ligand, center, size):
    cmd = [
        "./gnina",
        "--receptor", protein,
        "--ligand", ligand,
        "--center_x", str(center[0]),
        "--center_y", str(center[1]),
        "--center_z", str(center[2]),
        "--size_x", str(size[0]),
        "--size_y", str(size[1]),
        "--size_z", str(size[2]),
        "--cnn_scoring", "rescore"
    ]
    return subprocess.run(cmd, capture_output=True)
```

## CNN Scores

- **CNNscore:** 0-1, probability of good pose
- **CNNaffinity:** Predicted binding affinity
