# PyMOL Advanced Techniques for Drug Discovery

## 1. Binding Site/Pocket Analysis

### Surface Area Calculation
```python
# Settings for accurate SASA
cmd.set('dot_solvent', 1)  # Solvent accessible surface
cmd.set('dot_density', 3)    # Higher sampling
cmd.set('solvent_radius', 1.4)  # Water probe

# Calculate total surface area
total_area = cmd.get_area("all")

# Load area per atom into b-factors
cmd.get_area("organic", load_b=1)
cmd.show("surface", "organic")
cmd.spectrum("b", "blue_white_red")
```

### Buried Surface Area
```python
cmd.select("ligand", "organic")
cmd.select("protein", "polymer")
cmd.select("complex", "ligand or protein")

lig_area = cmd.get_area("ligand")
prot_area = cmd.get_area("protein")
complex_area = cmd.get_area("complex")
buried_area = (lig_area + prot_area) - complex_area
```

## 2. Protein-Ligand Interactions

### Hydrogen Bond Detection
```python
# mode=2 shows polar contacts
cmd.distance("hbonds", "ligand", "binding_site", cutoff=3.5, mode=2)

# Customize visualization
cmd.set("dash_gap", 0.4)
cmd.set("dash_radius", 0.05)
cmd.set("h_bond_max_angle", 40)
```

### Interaction Distance Measurements
```python
# Measure from ligand to all binding site residues
stored.dists = {}
cmd.iterate_state(1, "site_ca", 
    'stored.dists[resi] = cmd.distance(None, "ligand", f"/{model}//{chain}//{resi}//CA")')
```

## 3. Structure Alignment

### Align Command (Sequence-based)
```python
# Best for >30% sequence identity
cmd.align("protein_A", "protein_B")
cmd.align("protein_A and n. CA", "protein_B and n. CA")  # CA only

# Save alignment object
cmd.align("protein_A", "protein_B", object="A_on_B")
cmd.save("alignment.aln", "A_on_B")
```

### CEAlign (Structure-based)
```python
# Better for low sequence identity
cmd.cealign("protein_A", "protein_B")
cmd.cealign("protein_A", "protein_B", cycles=5)  # With refinement
```

### Batch Alignment
```python
import glob
cmd.fetch("1abc", "reference")

for pdb_file in glob.glob("structures/*.pdb"):
    name = pdb_file.split("/")[-1].replace(".pdb", "")
    cmd.load(pdb_file, name)
    cmd.cealign(name, "reference")
    cmd.save(f"{name}_aligned.pse")
```

## 4. Surface Analysis

### Per-Residue SASA
```python
from pymol import cmd, stored

stored.residues = []
cmd.iterate('name CA', 'stored.residues.append(resi)')

sasa_per_residue = []
for i in stored.residues:
    sasa = cmd.get_area(f'resi {i}')
    sasa_per_residue.append(sasa)
```

### Relative SASA
```python
# 0.0 = buried, 1.0 = fully exposed
cmd.get_sasa_relative("polymer")
cmd.show("cartoon", "polymer")
cmd.spectrum("b", "blue_white_red", minimum=0, maximum=1)
cmd.cartoon("putty", "polymer")
```

## 5. Distance/Angle Measurements

```python
# Distance
dist = cmd.distance(None, "resi 10 and n. CA", "resi 40 and n. CA")

# Angle
cmd.angle("angle1", "elem C and resi 10", "elem O and resi 10", "elem N and resi 11")
angle_val = cmd.get_angle(...)

# Dihedral
cmd.dihedral("phi", "resi 10 and n. C", "resi 10 and n. N", 
             "resi 10 and n. CA", "resi 10 and n. CB")
phi_val = cmd.get_dihedral(...)
```

## 6. Session Management

### Autosave Functionality
```python
import os, time, threading
from pymol import cmd

def auto_save():
    while True:
        time.sleep(30)
        filename = time.strftime('~/pymol-auto-%Y%m%d-%H%M%S.pse')
        cmd.save(filename, quiet=1)

threading.Thread(target=auto_save, daemon=True).start()
```

### Reproducible Scripts (~/.pymolrc)
```python
cmd.bg_color('white')
cmd.alias('nice', 'as cartoon; show sticks, organic')
cmd.set('ray_trace_gain', 0.1)
cmd.set('antialias', 2)
cmd.set('cartoon_fancy_helices', 1)
```

## 7. Batch Processing

### Process Multiple Structures
```python
import glob
import os
from pymol import cmd

os.makedirs("output", exist_ok=True)

for pdb_file in sorted(glob.glob("structures/*.pdb")):
    name = os.path.splitext(os.path.basename(pdb_file))[0]
    cmd.load(pdb_file)
    
    # Consistent visualization
    cmd.hide("everything", "all")
    cmd.show("cartoon", "polymer")
    cmd.show("sticks", "organic")
    cmd.color("gray", "polymer")
    cmd.color("orange", "organic")
    
    cmd.png(f"output/{name}.png", width=2000, dpi=300, ray=1)
    cmd.delete("all")
```

## 8. Publication Quality Rendering

```python
# High quality settings
cmd.set("antialias", 2)
cmd.set("ray_shadows", 0.3)
cmd.set("bg_color", "white")
cmd.set("ray_trace_depth", 0)
cmd.set("orthoscopic", 0)
cmd.set("ray_smooth", 1)

# DPI calculation: pixels = inches * DPI
# 8 inches at 300 DPI = 2400 pixels
cmd.png("publication.png", width=2400, height=2400, ray=1, dpi=300)
```

## 9. Movie Creation

### Basic Animation
```python
# Create frames
cmd.mset("1x100")  # 100 frames
cmd.mplay()        # Play movie
cmd.mstop()        # Stop

# Render frames
cmd.mpng("frame_", first=1, last=100, ray=1)
```

### Morphing Between States
```python
cmd.morph("morph_obj", "state1", "state2", steps=30)
```

## Key Commands Quick Reference

| Task | Command |
|------|---------|
| Surface area | `get_area selection` |
| H-bonds | `distance name, sel1, sel2, mode=2` |
| Align | `align mobile, target` |
| CE align | `cealign mobile, target` |
| Distance | `distance name, atom1, atom2` |
| Angle | `angle name, a1, a2, a3` |
| Dihedral | `dihedral name, a1, a2, a3, a4` |
| Save session | `save file.pse` |
| Render | `png file.png, ray=1, dpi=300` |
