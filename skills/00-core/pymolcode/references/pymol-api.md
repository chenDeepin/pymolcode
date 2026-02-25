# PyMOL API Reference

Comprehensive cmd module API for pymolcode. Source: [pymol.org/docs](https://pymol.org/dokuwiki/doku.php?id=api)

## Structure Loading/Saving

### cmd.load
```python
cmd.load(filename, object_name='', state=0, format='', finish=1, discrete=-1, quiet=1, multiplex=None, zoom=-1) -> str
```
Load molecules, maps, sessions. Returns object name.

### cmd.save
```python
cmd.save(filename, selection='(all)', state=-1, format='', quiet=1) -> None
```
Write to file. Formats: pdb, sdf, mol2, pse (session).

### cmd.fetch
```python
cmd.fetch(code, name='', state=0, type='pdb', async=-1, path=None, quiet=1) -> str
```
Download from RCSB PDB. Types: pdb, mmcif, mmtf.

### cmd.create
```python
cmd.create(name, selection, source_state=0, target_state=0, discrete=0, zoom=0, quiet=1) -> None
```
Create new object from selection.

## Representations

### cmd.show / cmd.hide
```python
cmd.show(representation, selection='') -> None
cmd.hide(representation, selection='') -> None
```
Types: lines, spheres, sticks, cartoon, ribbon, surface, mesh, dots, labels, everything

### cmd.cartoon
```python
cmd.cartoon(type, selection) -> None
```
Types: automatic, skip, loop, rectangle, oval, tube, arrow, dumbbell

## Selections

### cmd.select
```python
cmd.select(name, selection, enable=1, quiet=1) -> int
```
Returns atom count. Use `(` for temporary selection.

## Coloring

### cmd.color
```python
cmd.color(color, selection='all', quiet=1) -> None
```
Colors: red, blue, green, yellow, cyan, magenta, orange, white, gray, black, spectrum...

### cmd.spectrum
```python
cmd.spectrum(expression, palette, selection='all', minimum=None, maximum=None, byres=0) -> None
```
Expression: b (b-factor), q (occupancy), resi, chain, ss. Palette: blue_white_red, rainbow...

### cmd.set_color
```python
cmd.set_color(name, rgb, mode=0) -> None
```
Define custom color: `cmd.set_color("mycolor", [1.0, 0.5, 0.2])`

## Alignment

### cmd.align
```python
cmd.align(mobile, target, cutoff=2.0, cycles=5, object='', transform=1) -> (rmsd, n_aligned, n_cycles)
```
Sequence alignment + structural superposition with outlier rejection.

### cmd.super
```python
cmd.super(mobile, target, cutoff=2.0, cycles=5) -> (rmsd, n_aligned, n_cycles)
```
Better for low sequence identity (<30%).

### cmd.cealign
```python
cmd.cealign(target, mobile, d0=3.0, window=8, transform=1) -> dict
```
CE (Combinatorial Extension) algorithm. Good for structural alignment without sequence.

### cmd.fit
```python
cmd.fit(mobile, target, mobile_state=-1, target_state=-1, cutoff=2.0, cycles=0) -> (rmsd, n_aligned)
```
Superimpose without sequence alignment (requires matched atoms).

## Analysis

### cmd.distance / cmd.angle / cmd.dihedral
```python
cmd.distance(name, sel1, sel2, cutoff=None) -> None
cmd.angle(name, sel1, sel2, sel3) -> None
cmd.dihedral(name, sel1, sel2, sel3, sel4) -> None
```

### cmd.rms / cmd.rms_cur
```python
cmd.rms(mobile, target, cutoff=2.0) -> float
cmd.rms_cur(mobile, target) -> float  # Current coordinates only
```

### cmd.get_area
```python
cmd.get_area(selection='(all)', state=-1, load_b=1) -> float
```
Solvent-accessible surface area (Å²).

### cmd.get_extent
```python
cmd.get_extent(selection='(all)', state=-1) -> [[min_xyz], [max_xyz]]
```
Bounding box coordinates.

## Visualization

### cmd.zoom
```python
cmd.zoom(selection='(all)', buffer=0.0, complete=0, animate=-1) -> None
```

### cmd.center
```python
cmd.center(selection='(all)', state=0, origin=1) -> None
```

### cmd.orient
```python
cmd.orient(selection='(all)', state=-1) -> None
```
View along principal axes.

### cmd.view / cmd.get_view / cmd.set_view
```python
cmd.view(name, action='store')  # store/recall/delete/list
cmd.get_view() -> list[18 floats]
cmd.set_view(view) -> None
```

## Rendering

### cmd.png
```python
cmd.png(filename, width=-1, height=-1, ray=0, dpi=-1) -> str
```
Save image. ray=1 for ray tracing.

### cmd.ray
```python
cmd.ray(width=-1, height=-1, renderer=0, antialias=0) -> None
```
Ray trace. renderer: 0=internal, 1=POV-Ray.

### cmd.mpng
```python
cmd.mpng(filename, first=0, last=-1, ray=0) -> str
```
Render movie frames.

## Utility

### cmd.count_atoms
```python
cmd.count_atoms(selection='(all)') -> int
```

### cmd.get_names / cmd.get_object_list
```python
cmd.get_names(enabled_only=0) -> list[str]
cmd.get_object_list() -> list[str]
```

### cmd.get_chains
```python
cmd.get_chains(selection='(all)') -> list[str]
```

### cmd.get_model / cmd.get_coords / cmd.get_pdbstr
```python
cmd.get_model(selection, state=-1) -> Model
cmd.get_coords(selection, state=-1) -> list[list[float]]
cmd.get_pdbstr(selection, state=-1) -> str
```

### cmd.iterate / cmd.alter
```python
cmd.iterate(selection, expression)  # Read-only
cmd.alter(selection, expression)    # Modify
```
Example: `cmd.alter("chain A", "b=50.0")`

### cmd.delete / cmd.copy / cmd.enable / cmd.disable
```python
cmd.delete(name)
cmd.copy(new_name, source_name)
cmd.enable(name)
cmd.disable(name)
```

## Selection Language

| Syntax | Description |
|--------|-------------|
| `chain A` | Single chain |
| `chain A+B` | Multiple chains |
| `resi 50-100` | Residue range |
| `resi 50+10` | Residues 50-60 |
| `resn ALA+GLY` | Multiple residue types |
| `name CA` | Atom name |
| `element C` | Element |
| `b > 50` | B-factor filter |
| `q > 0.9` | Occupancy filter |
| `alt A` | Alternate conformation |
| `ss H` | Secondary structure (H/E/L) |
| `id 1-100` | Atom ID range |
| `index 1-100` | Internal index |
| `organic` | Non-polymer organic |
| `inorganic` | Non-polymer inorganic |
| `solvent` | Water and ions |
| `polymer` | Polymer atoms |
| `polymer.protein` | Protein only |
| `polymer.nucleic` | Nucleic acids |
| `byres (selection)` | Expand to residues |
| `byobj (selection)` | Expand to objects |
| `within X of (selection)` | Distance cutoff |
| `bound_to (selection)` | Atoms bound to selection |

### Boolean Operators
```
and, or, not, ( )
chain A and resi 50-100
chain A or chain B
not solvent
(chain A and resi 50) or (chain B and resi 100)
```

## Settings

```python
cmd.set(name, value, object='')
cmd.get(name, object='') -> value
```

Common settings:
- `cartoon_transparency`: 0.0-1.0
- `sphere_transparency`: 0.0-1.0
- `surface_transparency`: 0.0-1.0
- `transparency`: Global transparency
- `ray_shadows`: 0/1
- `ray_trace_mode`: 0-3
- `bg_color`: Background color
- `orthoscopic`: 0/1
- `depth_cue`: 0/1
- `fog`: 0/1
