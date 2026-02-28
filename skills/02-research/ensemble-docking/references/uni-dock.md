# Uni-Dock Integration

## Installation

```bash
# From source
git clone https://github.com/dptech-corp/Uni-Dock.git
cd Uni-Dock && mkdir build && cd build
cmake .. && make -j$(nproc)
```

## GPU Requirements

- CUDA 11.8+
- NVIDIA GPU with 8GB+ VRAM

## API Call

```python
from unidock import UniDock

dock = UniDock(
    receptor="protein.pdbqt",
    ligands="library.sdf",
    center=[10.0, 20.0, 30.0],
    size=[20, 20, 20],
    gpu=0
)

results = dock.run(top_n=100)
```

## Performance

| Library Size | Time (GPU) | Throughput |
|--------------|------------|------------|
| 1,000        | 10s        | 100/s      |
| 10,000       | 100s       | 100/s      |
| 100,000      | 17min      | 100/s      |
