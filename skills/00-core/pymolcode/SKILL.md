---
name: pymolcode
description: LLM-powered molecular visualization and drug discovery using PyMOL. Use when working with molecular structures, structure-based drug design, molecular visualization, protein-ligand interactions, binding site analysis, structure alignment, or PyMOL commands. Triggers: "visualize protein", "load PDB", "align structures", "show binding pocket", "color by chain", "take screenshot", "analyze interactions", "measure distance", "drug discovery", "molecular docking visualization".
---

# pymolcode

LLM-Enhanced Molecular Visualization Platform for Drug Discovery

## Directory Structure

Artifacts under `~/.pymolcode/artifacts/`:
- `pdb/` - Downloaded PDB files
- `scripts/` - Generated Python scripts
- `screenshots/` - Saved images

## Available Tools

| Tool | Purpose |
|------|---------|
| `pymol_load` | Load PDB files or local structures |
| `pymol_show` | Set representation (cartoon, surface, sticks) |
| `pymol_color` | Apply colors to selections |
| `pymol_zoom` | Zoom camera to selection |
| `pymol_list` | List loaded objects |
| `pymol_align` | Align mobile to target structure |
| `pymol_screenshot` | Save high-quality image |
| `python_exec` | Execute arbitrary PyMOL Python code |

## Selection Algebra

### Logical Operators
```
not S1          # Invert
S1 and S2       # Intersection
S1 or S2        # Union
```

### Identifiers
```
model name      # Object name
chain A         # Chain ID
resn ALA        # Residue name
resi 100-200    # Residue range
name CA         # Atom name
elem C          # Element
```

### Entity Expansion
```
byres S1        # Complete residues
bychain S1      # Complete chains
bymolecule S1   # Connected molecules
```

### Proximity
```
S1 within 5.0 of S2    # Within distance
S1 around 5.0          # Around center
bound_to S1            # Bonded atoms
```

### Properties
```
b < 100         # B-factor
q > 0.9         # Occupancy
ss H+S          # Secondary structure
```

### Chemical Classes
```
organic         # Ligands
solvent         # Water/ions
polymer.protein # Protein
backbone        # Backbone atoms
```

## Common Patterns

### Load and visualize
```python
pymol_load(source="1ubq")
pymol_show(selection="all", representation="cartoon")
pymol_color(selection="chain", color="spectrum")
pymol_zoom(selection="all")
```

### Align structures
```python
pymol_load(source="3kys", name="tead1")
pymol_load(source="5hv0", name="tead2")
pymol_align(mobile="tead2", target="tead1", method="ce")
```

### Binding pocket visualization
```python
python_exec(code='''
cmd.show("sticks", "organic and not solvent")
cmd.show("surface", "byres (polymer within 5 of organic)")
cmd.set("transparency", 0.5, "surface")
cmd.color("yellow", "organic")
''')
```

### Protein-ligand H-bonds
```python
python_exec(code='''
cmd.distance("hbonds", "organic", "polymer", cutoff=3.5, mode=2)
cmd.set("dash_gap", 0.4)
cmd.color("grey50", "hbonds")
''')
```

### Publication quality render
```python
python_exec(code='''
cmd.set("antialias", 2)
cmd.set("ray_shadows", 0.3)
cmd.set("bg_color", "white")
cmd.png("output.png", width=2400, height=2400, ray=1, dpi=300)
''')
```

## Alignment Methods

| Method | Best For |
|--------|----------|
| `align` | >30% sequence identity |
| `cealign` | Low identity, structural similarity |
| `super` | Quick approximate alignment |

## Best Practices

1. **Surface calculations**: `set dot_solvent, 1` for SASA
2. **High accuracy**: `set dot_density, 3`
3. **H-bonds**: `set h_bond_max_angle, 40`
4. **Reproducibility**: Save Python scripts, not just sessions

## References

- [pymol-api.md](references/pymol-api.md) - Complete cmd module documentation
- [PyMOLWiki](https://pymolwiki.org/) - Community docs
