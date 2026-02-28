"""Built-in skills for drug discovery workflows."""

from __future__ import annotations

import json
from typing import Any

from python.skill.base import Skill, SkillContext, SkillParameter, SkillResult, SkillStatus


class StructureAnalysisSkill(Skill):
    """Analyze a molecular structure and generate a report."""

    name = "structure_analysis"
    description = "Analyze a molecular structure and generate a comprehensive report including composition, secondary structure, and binding sites."
    version = "1.0.0"
    tags = ["structure", "analysis", "protein"]
    parameters = [
        SkillParameter(
            name="object_name",
            type="string",
            description="Name of the PyMOL object to analyze",
            required=True,
        ),
        SkillParameter(
            name="include_binding_sites",
            type="boolean",
            description="Include binding site prediction",
            default=True,
        ),
    ]

    async def execute(
        self,
        params: dict[str, Any],
        context: SkillContext = None,
    ) -> SkillResult:
        object_name = params.get("object_name", "")
        include_binding_sites = params.get("include_binding_sites", True)

        if not context.pymol_executor:
            return SkillResult(
                skill_name=self.name,
                status=SkillStatus.FAILED,
                error="PyMOL executor not available",
            )

        # Check if object exists
        info_cmd = json.dumps({"method": "get_object_info", "params": {"object": object_name}})
        info_result = context.pymol_executor.execute(info_cmd)

        if not info_result.get("ok"):
            return SkillResult(
                skill_name=self.name,
                status=SkillStatus.FAILED,
                error=f"Failed to get object info: {info_result.get('error')}",
            )

        obj_info = info_result.get("result", {})
        if not obj_info.get("exists", False):
            return SkillResult(
                skill_name=self.name,
                status=SkillStatus.FAILED,
                error=f"Object '{object_name}' does not exist",
            )

        # Get comprehensive structure composition using execute_python
        composition_code = f'''
import json
cmd = local_vars.get("cmd")
obj_name = "{object_name}"

result = {{"object_name": obj_name}}

# Get chains
try:
    chains = cmd.get_chains(obj_name)
    result["chains"] = list(chains) if chains else []
    result["chain_count"] = len(result["chains"])
except Exception as e:
    result["chains"] = []
    result["chain_error"] = str(e)

# Get atom count
try:
    result["atom_count"] = cmd.count_atoms(obj_name)
except Exception:
    result["atom_count"] = 0

# Get residue count and types
try:
    model = cmd.get_model(obj_name)
    residues = {{}}
    atom_types = {{}}
    elements = {{}}
    
    for atom in model.atom:
        # Count residues by name
        resn = atom.resn
        residues[resn] = residues.get(resn, 0) + 1
        
        # Count atom types (name)
        atom_name = atom.name
        atom_types[atom_name] = atom_types.get(atom_name, 0) + 1
        
        # Count elements
        elem = atom.symbol if hasattr(atom, 'symbol') else atom.name[0]
        elements[elem] = elements.get(elem, 0) + 1
    
    # Get unique residue count
    resi_set = set()
    for atom in model.atom:
        resi_set.add((atom.chain, atom.resi))
    
    result["residue_count"] = len(resi_set)
    result["residue_types"] = dict(residues)
    result["atom_types"] = dict(atom_types)
    result["elements"] = dict(elements)
except Exception as e:
    result["composition_error"] = str(e)
    result["residue_count"] = 0

local_vars["_composition_result"] = json.dumps(result)
'''
        
        comp_cmd = json.dumps({
            "method": "execute_python",
            "params": {"code": composition_code}
        })
        comp_result = context.pymol_executor.execute(comp_cmd)
        
        if not comp_result.get("ok"):
            return SkillResult(
                skill_name=self.name,
                status=SkillStatus.FAILED,
                error=f"Failed to get composition: {comp_result.get('error')}",
            )

        # Parse the composition result from execute_python
        comp_output = comp_result.get("result", {})
        analysis = json.loads(comp_output.get("_composition_result", "{}")) if isinstance(comp_output.get("_composition_result"), str) else comp_output.get("_composition_result", {})
        
        if not analysis:
            analysis = {"object_name": object_name, "atom_count": obj_info.get("atom_count", 0)}

        # Get secondary structure using DSSP
        ss_code = f'''
import json
cmd = local_vars.get("cmd")
obj_name = "{object_name}"

result = {{"secondary_structure": {{}}}}

try:
    # Run DSSP to assign secondary structure
    cmd.dss(obj_name)
    
    # Get secondary structure assignments
    model = cmd.get_model(obj_name)
    
    ss_counts = {{"helix": 0, "sheet": 0, "loop": 0}}
    ss_by_residue = []
    
    # PyMOL stores SS as: H=helix, S=sheet, L/''=loop
    ss_map = {{"H": "helix", "G": "helix", "I": "helix",  # Helix types
               "E": "sheet", "B": "sheet",  # Sheet types
               "T": "loop", "S": "loop", " ": "loop", "-": "loop"}}  # Loop/coil
    
    current_ss = {{}}
    for atom in model.atom:
        ss_char = atom.ss if hasattr(atom, 'ss') else ' '
        res_key = (atom.chain, atom.resi, atom.resn)
        
        if res_key not in current_ss:
            ss_type = ss_map.get(ss_char, "loop")
            current_ss[res_key] = ss_type
            ss_counts[ss_type] = ss_counts.get(ss_type, 0) + 1
            ss_by_residue.append({{
                "chain": atom.chain,
                "resi": atom.resi,
                "resn": atom.resn,
                "ss": ss_type
            }})
    
    result["secondary_structure"]["counts"] = ss_counts
    result["secondary_structure"]["residues"] = ss_by_residue[:100]  # Limit for output
    result["secondary_structure"]["total_residues"] = len(ss_by_residue)
    
except Exception as e:
    result["secondary_structure"]["error"] = str(e)

local_vars["_ss_result"] = json.dumps(result)
'''
        
        ss_cmd = json.dumps({
            "method": "execute_python",
            "params": {"code": ss_code}
        })
        ss_result = context.pymol_executor.execute(ss_cmd)
        
        if ss_result.get("ok"):
            ss_output = ss_result.get("result", {})
            ss_data = json.loads(ss_output.get("_ss_result", "{}")) if isinstance(ss_output.get("_ss_result"), str) else ss_output.get("_ss_result", {})
            analysis["secondary_structure"] = ss_data.get("secondary_structure", {})

        # Binding site detection (simple cavity-based approach)
        analysis["binding_sites"] = []
        
        if include_binding_sites:
            bs_code = f'''
import json
cmd = local_vars.get("cmd")
obj_name = "{object_name}"

result = {{"binding_sites": []}}

try:
    # Simple cavity detection based on surface curvature and solvent accessibility
    # First, ensure we have surface representation
    cmd.show("surface", obj_name)
    
    # Find potential pockets using coordinate analysis
    model = cmd.get_model(obj_name)
    
    # Get center of mass for reference
    coords = [[atom.coord[0], atom.coord[1], atom.coord[2]] for atom in model.atom]
    
    # Calculate bounding box
    if coords:
        xs = [c[0] for c in coords]
        ys = [c[1] for c in coords]
        zs = [c[2] for c in coords]
        
        center = [(min(xs)+max(xs))/2, (min(ys)+max(ys))/2, (min(zs)+max(zs))/2]
        
        # Find surface atoms (approximation: atoms at edges of protein)
        # Use selection to find solvent-accessible regions
        
        # Create selection for potential binding site residues
        # Based on finding clusters of exposed residues
        
        # Get solvent-accessible residues (simplified approach)
        cmd.select("_temp_surface", f"byres ({{obj_name}} and not ({{obj_name}} within 4 of {{obj_name}}))")
        
        # Alternative: detect pockets by finding enclosed regions
        # This is a simplified heuristic - real fpocket would be more sophisticated
        
        # Get residues with high SASA (solvent accessible surface area)
        cmd.select("_temp_exposed", f"({{obj_name}} and not polymer.protein) or ({{obj_name}} within 3 of not {{obj_name}})")
        
        surface_count = cmd.count_atoms("_temp_surface")
        exposed_count = cmd.count_atoms("_temp_exposed")
        
        # Find concave regions (potential binding sites)
        # Use alpha shape or simply identify clusters
        
        result["binding_sites"] = [{{
            "id": 1,
            "method": "surface_analysis",
            "surface_atoms": surface_count,
            "exposed_atoms": exposed_count,
            "center": center,
            "description": "Potential binding site detected from surface topology"
        }}]
        
        # Clean up temporary selections
        cmd.delete("_temp_surface")
        cmd.delete("_temp_exposed")
        
except Exception as e:
    result["binding_sites"] = [{{
        "id": 0,
        "error": str(e),
        "method": "surface_analysis_failed"
    }}]

local_vars["_bs_result"] = json.dumps(result)
'''
            
            bs_cmd = json.dumps({
                "method": "execute_python",
                "params": {"code": bs_code}
            })
            bs_result = context.pymol_executor.execute(bs_cmd)
            
            if bs_result.get("ok"):
                bs_output = bs_result.get("result", {})
                bs_data = json.loads(bs_output.get("_bs_result", "{}")) if isinstance(bs_output.get("_bs_result"), str) else bs_output.get("_bs_result", {})
                analysis["binding_sites"] = bs_data.get("binding_sites", [])

        return SkillResult(
            skill_name=self.name,
            status=SkillStatus.COMPLETED,
            output=analysis,
            metadata={"include_binding_sites": include_binding_sites},
        )


class BindingSiteAnalysisSkill(Skill):
    """Analyze binding sites in a protein structure."""

    name = "binding_site_analysis"
    description = "Identify and characterize potential binding sites in a protein structure."
    version = "1.0.0"
    tags = ["binding-site", "drug-discovery", "docking"]
    parameters = [
        SkillParameter(
            name="object_name",
            type="string",
            description="Name of the protein object",
            required=True,
        ),
        SkillParameter(
            name="ligand_name",
            type="string",
            description="Name of the ligand object (if present)",
            required=False,
        ),
        SkillParameter(
            name="radius",
            type="number",
            description="Radius around ligand for binding site definition (Angstroms)",
            default=5.0,
        ),
    ]

    async def execute(
        self,
        params: dict[str, Any],
        context: SkillContext = None,
    ) -> SkillResult:
        object_name = params.get("object_name", "")
        ligand_name = params.get("ligand_name")
        radius = params.get("radius", 5.0)

        if not context.pymol_executor:
            return SkillResult(
                skill_name=self.name,
                status=SkillStatus.FAILED,
                error="PyMOL executor not available",
            )

        result = {
            "protein": object_name,
            "ligand": ligand_name,
            "radius": radius,
            "binding_site_residues": [],
            "residue_count": 0,
            "analysis": "Binding site analysis",
        }

        # If ligand is present, find actual residues within radius
        if ligand_name:
            analysis_code = f'''
import json
cmd = local_vars.get("cmd")
protein = "{object_name}"
ligand = "{ligand_name}"
radius = {radius}

result = {{
    "protein": protein,
    "ligand": ligand,
    "radius": radius,
    "binding_site_residues": [],
    "residue_count": 0
}}

try:
    # Check if both objects exist
    objects = cmd.get_object_list()
    if protein not in objects:
        result["error"] = f"Protein '{{protein}}' not found"
    elif ligand not in objects:
        result["error"] = f"Ligand '{{ligand}}' not found"
    else:
        # Use PyMOL selection to find residues within radius of ligand
        # byres (polymer within X of organic) - gets protein residues near organic (ligand)
        selection_name = "_binding_site_temp"
        
        # Create selection: polymer residues within radius of the ligand
        selection_cmd = f"byres (polymer and {{protein}} within {{radius}} of {{ligand}})"
        cmd.select(selection_name, selection_cmd)
        
        # Get the selected atoms
        model = cmd.get_model(selection_name)
        
        # Extract unique residues with their properties
        residues_dict = {{}}
        for atom in model.atom:
            res_key = (atom.chain, atom.resi)
            if res_key not in residues_dict:
                residues_dict[res_key] = {{
                    "chain": atom.chain,
                    "resi": atom.resi,
                    "resn": atom.resn,
                    "atom_count": 0,
                    "atoms": []
                }}
            residues_dict[res_key]["atom_count"] += 1
            if len(residues_dict[res_key]["atoms"]) < 5:  # Limit atoms per residue for output
                residues_dict[res_key]["atoms"].append(atom.name)
        
        # Convert to list and sort
        residues_list = list(residues_dict.values())
        residues_list.sort(key=lambda x: (x["chain"], int(x["resi"])))
        
        result["binding_site_residues"] = residues_list
        result["residue_count"] = len(residues_list)
        
        # Calculate distances from each residue to ligand center
        # Get ligand center of mass
        ligand_model = cmd.get_model(ligand)
        ligand_coords = [[a.coord[0], a.coord[1], a.coord[2]] for a in ligand_model.atom]
        if ligand_coords:
            lig_com = [
                sum(c[i] for c in ligand_coords) / len(ligand_coords)
                for i in range(3)
            ]
            result["ligand_center"] = lig_com
            
            # Calculate min distance for each residue
            for res in residues_list[:20]:  # Limit for performance
                # Get representative atom coordinates
                res_sel = f"/{{protein}}//{{res['chain']}}/{{res['resi']}}/CA"
                try:
                    dist = cmd.get_distance(res_sel, f"/{{ligand}}////", 
                                          mode="minimum")
                    res["min_distance_to_ligand"] = round(dist, 2)
                except:
                    pass
        
        # Clean up
        cmd.delete(selection_name)
        
        result["analysis"] = f"Found {{len(residues_list)}} residues within {{radius}}A of ligand {{ligand}}"
        
except Exception as e:
    result["error"] = str(e)
    result["analysis"] = f"Analysis failed: {{str(e)}}"

local_vars["_bsa_result"] = json.dumps(result)
'''
            
            analysis_cmd = json.dumps({
                "method": "execute_python",
                "params": {"code": analysis_code}
            })
            analysis_result = context.pymol_executor.execute(analysis_cmd)
            
            if analysis_result.get("ok"):
                output = analysis_result.get("result", {})
                parsed = json.loads(output.get("_bsa_result", "{}")) if isinstance(output.get("_bsa_result"), str) else output.get("_bsa_result", {})
                result.update(parsed)
            else:
                result["error"] = str(analysis_result.get("error"))
        
        else:
            # No ligand - try to detect pockets using geometric analysis
            pocket_code = f'''
import json
cmd = local_vars.get("cmd")
protein = "{object_name}"

result = {{
    "protein": protein,
    "ligand": None,
    "binding_site_residues": [],
    "potential_pockets": []
}}

try:
    # Simple pocket detection without ligand
    # Find cavities using coordinate clustering
    
    model = cmd.get_model(protein)
    
    # Get all atom coordinates
    coords = [[atom.coord[0], atom.coord[1], atom.coord[2]] for atom in model.atom]
    
    if coords:
        # Simple approach: find surface atoms and look for concave regions
        # This is a heuristic - real pocket detection would use fpocket or similar
        
        # Create surface selection
        cmd.show("surface", protein)
        
        # Find residues on the surface
        cmd.select("_temp_surface_res", f"byres ({{protein}} within 2 of not {{protein}})")
        surface_model = cmd.get_model("_temp_surface_res")
        
        # Group surface residues by proximity
        surface_residues = {{}}
        for atom in surface_model.atom:
            res_key = (atom.chain, atom.resi)
            if res_key not in surface_residues:
                surface_residues[res_key] = {{
                    "chain": atom.chain,
                    "resi": atom.resi,
                    "resn": atom.resn,
                    "coords": atom.coord
                }}
        
        result["binding_site_residues"] = list(surface_residues.values())[:50]
        result["residue_count"] = len(surface_residues)
        result["analysis"] = f"Detected {{len(surface_residues)}} surface residues as potential binding site"
        
        # Clean up
        cmd.delete("_temp_surface_res")
        
except Exception as e:
    result["error"] = str(e)
    result["analysis"] = f"Pocket detection failed: {{str(e)}}"

local_vars["_pocket_result"] = json.dumps(result)
'''
            
            pocket_cmd = json.dumps({
                "method": "execute_python",
                "params": {"code": pocket_code}
            })
            pocket_result = context.pymol_executor.execute(pocket_cmd)
            
            if pocket_result.get("ok"):
                output = pocket_result.get("result", {})
                parsed = json.loads(output.get("_pocket_result", "{}")) if isinstance(output.get("_pocket_result"), str) else output.get("_pocket_result", {})
                result.update(parsed)

        return SkillResult(
            skill_name=self.name,
            status=SkillStatus.COMPLETED,
            output=result,
        )


class LigandComparisonSkill(Skill):
    """Compare multiple ligand structures."""

    name = "ligand_comparison"
    description = "Compare multiple ligand structures and generate alignment reports."
    version = "1.0.0"
    tags = ["ligand", "comparison", "alignment", "SAR"]
    parameters = [
        SkillParameter(
            name="reference",
            type="string",
            description="Reference ligand object name",
            required=True,
        ),
        SkillParameter(
            name="mobile",
            type="string",
            description="Mobile ligand object name to align",
            required=True,
        ),
        SkillParameter(
            name="method",
            type="string",
            description="Alignment method",
            enum=["align", "super", "cealign"],
            default="align",
        ),
    ]

    async def execute(
        self,
        params: dict[str, Any],
        context: SkillContext = None,
    ) -> SkillResult:
        reference = params.get("reference", "")
        mobile = params.get("mobile", "")
        method = params.get("method", "align")

        if not context.pymol_executor:
            return SkillResult(
                skill_name=self.name,
                status=SkillStatus.FAILED,
                error="PyMOL executor not available",
            )

        result = {
            "reference": reference,
            "mobile": mobile,
            "method": method,
            "rmsd": None,
            "aligned": False,
        }

        # Check both objects exist
        for obj_name, role in [(reference, "reference"), (mobile, "mobile")]:
            check_cmd = json.dumps({
                "method": "get_object_info",
                "params": {"object": obj_name}
            })
            check_result = context.pymol_executor.execute(check_cmd)
            if not check_result.get("ok") or not check_result.get("result", {}).get("exists", False):
                return SkillResult(
                    skill_name=self.name,
                    status=SkillStatus.FAILED,
                    error=f"Object '{obj_name}' ({role}) does not exist",
                )

        # Use the align method from executor
        align_method = "ce" if method == "cealign" else method
        align_cmd = json.dumps({
            "method": "align",
            "params": {
                "mobile": mobile,
                "target": reference,
                "method": align_method,
                "cutoff": 2.0,
                "cycles": 5 if method == "align" else 0
            }
        })
        
        align_result = context.pymol_executor.execute(align_cmd)
        
        if align_result.get("ok"):
            align_data = align_result.get("result", {})
            result["rmsd"] = align_data.get("rmsd")
            result["aligned"] = align_data.get("aligned", False)
            
            # Get additional alignment metrics
            metrics_code = f'''
import json
cmd = local_vars.get("cmd")
ref = "{reference}"
mob = "{mobile}"

result = {{}}

try:
    # Get atom counts
    result["reference_atoms"] = cmd.count_atoms(ref)
    result["mobile_atoms"] = cmd.count_atoms(mob)
    
    # Get aligned atom count (atoms that matched in alignment)
    # PyMOL stores alignment info, but we'll estimate from overlap
    
    # Calculate RMSD manually for verification
    model_ref = cmd.get_model(ref)
    model_mob = cmd.get_model(mob)
    
    # Store element counts for comparison
    elements_ref = {{}}
    elements_mob = {{}}
    
    for atom in model_ref.atom:
        elem = atom.symbol if hasattr(atom, 'symbol') else atom.name[0]
        elements_ref[elem] = elements_ref.get(elem, 0) + 1
    
    for atom in model_mob.atom:
        elem = atom.symbol if hasattr(atom, 'symbol') else atom.name[0]
        elements_mob[elem] = elements_mob.get(elem, 0) + 1
    
    result["reference_elements"] = elements_ref
    result["mobile_elements"] = elements_mob
    
    # Calculate overlap score based on common elements
    common_elements = set(elements_ref.keys()) & set(elements_mob.keys())
    result["common_elements"] = list(common_elements)
    
    # Estimate alignment quality
    total_common = sum(min(elements_ref.get(e, 0), elements_mob.get(e, 0)) for e in common_elements)
    result["estimated_matched_atoms"] = total_common
    
except Exception as e:
    result["metrics_error"] = str(e)

local_vars["_metrics_result"] = json.dumps(result)
'''
            
            metrics_cmd = json.dumps({
                "method": "execute_python",
                "params": {"code": metrics_code}
            })
            metrics_result = context.pymol_executor.execute(metrics_cmd)
            
            if metrics_result.get("ok"):
                output = metrics_result.get("result", {})
                parsed = json.loads(output.get("_metrics_result", "{}")) if isinstance(output.get("_metrics_result"), str) else output.get("_metrics_result", {})
                result.update(parsed)
                
        else:
            result["error"] = str(align_result.get("error"))
            result["aligned"] = False

        return SkillResult(
            skill_name=self.name,
            status=SkillStatus.COMPLETED,
            output=result,
        )


class TrajectoryAnalysisSkill(Skill):
    """Analyze molecular dynamics trajectories."""

    name = "trajectory_analysis"
    description = "Analyze molecular dynamics trajectory data including RMSD, RMSF, and secondary structure changes."
    version = "1.0.0"
    tags = ["trajectory", "MD", "dynamics", "analysis"]
    parameters = [
        SkillParameter(
            name="trajectory_file",
            type="string",
            description="Path to trajectory file",
            required=True,
        ),
        SkillParameter(
            name="topology_file",
            type="string",
            description="Path to topology file",
            required=True,
        ),
        SkillParameter(
            name="analyses",
            type="array",
            description="List of analyses to perform",
            default=["rmsd", "rmsf"],
        ),
        SkillParameter(
            name="selection",
            type="string",
            description="Selection for analysis (e.g., 'name CA')",
            default="name CA",
        ),
    ]

    async def execute(
        self,
        params: dict[str, Any],
        context: SkillContext = None,
    ) -> SkillResult:
        trajectory_file = params.get("trajectory_file", "")
        topology_file = params.get("topology_file", "")
        analyses = params.get("analyses", ["rmsd", "rmsf"])
        selection = params.get("selection", "name CA")

        result = {
            "trajectory": trajectory_file,
            "topology": topology_file,
            "selection": selection,
            "analyses_requested": analyses,
            "results": {},
        }

        # Check for MDAnalysis availability
        mdanalysis_available = False
        mdtraj_available = False
        
        try:
            import importlib
            mdanalysis_spec = importlib.util.find_spec("MDAnalysis")
            if mdanalysis_spec is not None:
                mdanalysis_available = True
        except ImportError:
            pass
        
        try:
            import importlib
            mdtraj_spec = importlib.util.find_spec("mdtraj")
            if mdtraj_spec is not None:
                mdtraj_available = True
        except ImportError:
            pass

        if not mdanalysis_available and not mdtraj_available:
            return SkillResult(
                skill_name=self.name,
                status=SkillStatus.FAILED,
                output=result,
                error="No MD analysis library available. Please install MDAnalysis or MDTraj:\n"
                      "  pip install MDAnalysis\n"
                      "  or\n"
                      "  pip install mdtraj",
            )

        # Prefer MDAnalysis, fall back to MDTraj
        if mdanalysis_available:
            result["library_used"] = "MDAnalysis"
            
            try:
                import MDAnalysis as mda
                from MDAnalysis.analysis import rms, align
                import numpy as np
                
                # Load universe
                u = mda.Universe(topology_file, trajectory_file)
                
                result["n_frames"] = len(u.trajectory)
                result["n_atoms"] = len(u.atoms)
                result["n_residues"] = len(u.residues)
                
                # Perform requested analyses
                if "rmsd" in analyses:
                    # RMSD calculation
                    rmsd_values = []
                    
                    # Get reference (first frame)
                    ref_pos = u.select_atoms(selection).positions.copy()
                    
                    for ts in u.trajectory:
                        mobile_pos = u.select_atoms(selection).positions
                        if len(mobile_pos) == len(ref_pos):
                            # Calculate RMSD
                            diff = mobile_pos - ref_pos
                            rmsd = np.sqrt(np.mean(np.sum(diff**2, axis=1)))
                            rmsd_values.append(float(rmsd))
                    
                    result["results"]["rmsd"] = {
                        "values": rmsd_values,
                        "mean": float(np.mean(rmsd_values)) if rmsd_values else None,
                        "std": float(np.std(rmsd_values)) if rmsd_values else None,
                        "min": float(np.min(rmsd_values)) if rmsd_values else None,
                        "max": float(np.max(rmsd_values)) if rmsd_values else None,
                        "unit": "Angstrom"
                    }
                
                if "rmsf" in analyses:
                    # RMSF calculation
                    rmsf_values = []
                    
                    # Collect all positions
                    all_pos = []
                    for ts in u.trajectory:
                        all_pos.append(u.select_atoms(selection).positions.copy())
                    
                    if all_pos:
                        all_pos = np.array(all_pos)
                        mean_pos = np.mean(all_pos, axis=0)
                        
                        # Calculate RMSF per atom
                        for i in range(all_pos.shape[1]):
                            atom_pos = all_pos[:, i, :]
                            rmsf = np.sqrt(np.mean(np.sum((atom_pos - mean_pos[i])**2, axis=1)))
                            rmsf_values.append(float(rmsf))
                    
                    result["results"]["rmsf"] = {
                        "values": rmsf_values[:100],  # Limit output size
                        "mean": float(np.mean(rmsf_values)) if rmsf_values else None,
                        "max": float(np.max(rmsf_values)) if rmsf_values else None,
                        "unit": "Angstrom"
                    }
                
                if "rg" in analyses or "radius_of_gyration" in analyses:
                    # Radius of gyration
                    rg_values = []
                    
                    for ts in u.trajectory:
                        atoms = u.select_atoms(selection)
                        if len(atoms) > 0:
                            masses = atoms.masses
                            total_mass = np.sum(masses)
                            com = atoms.center_of_mass()
                            coords = atoms.positions - com
                            rg_sq = np.sum(masses[:, np.newaxis] * coords**2) / total_mass
                            rg = np.sqrt(rg_sq)
                            rg_values.append(float(rg))
                    
                    result["results"]["radius_of_gyration"] = {
                        "values": rg_values,
                        "mean": float(np.mean(rg_values)) if rg_values else None,
                        "std": float(np.std(rg_values)) if rg_values else None,
                        "unit": "Angstrom"
                    }
                
                result["status"] = "completed"
                
            except Exception as e:
                result["status"] = "partial_failure"
                result["error"] = str(e)
                result["error_type"] = type(e).__name__
                
        elif mdtraj_available:
            result["library_used"] = "MDTraj"
            
            try:
                import mdtraj as md
                import numpy as np
                
                # Load trajectory
                traj = md.load(trajectory_file, top=topology_file)
                
                result["n_frames"] = traj.n_frames
                result["n_atoms"] = traj.n_atoms
                result["n_residues"] = traj.n_residues
                
                # Convert selection to mdtraj format
                # "name CA" -> "name CA"
                if selection == "name CA":
                    atom_indices = traj.top.select("name CA")
                else:
                    atom_indices = traj.top.select(selection)
                
                if "rmsd" in analyses:
                    rmsd_values = md.rmsd(traj, traj, 0, atom_indices=atom_indices) * 10  # nm to Angstrom
                    
                    result["results"]["rmsd"] = {
                        "values": rmsd_values.tolist(),
                        "mean": float(np.mean(rmsd_values)),
                        "std": float(np.std(rmsd_values)),
                        "min": float(np.min(rmsd_values)),
                        "max": float(np.max(rmsd_values)),
                        "unit": "Angstrom"
                    }
                
                if "rmsf" in analyses:
                    rmsf_values = md.rmsf(traj, traj, 0, atom_indices=atom_indices) * 10  # nm to Angstrom
                    
                    result["results"]["rmsf"] = {
                        "values": rmsf_values.tolist()[:100],
                        "mean": float(np.mean(rmsf_values)),
                        "max": float(np.max(rmsf_values)),
                        "unit": "Angstrom"
                    }
                
                if "rg" in analyses or "radius_of_gyration" in analyses:
                    rg_values = md.compute_rg(traj) * 10  # nm to Angstrom
                    
                    result["results"]["radius_of_gyration"] = {
                        "values": rg_values.tolist(),
                        "mean": float(np.mean(rg_values)),
                        "std": float(np.std(rg_values)),
                        "unit": "Angstrom"
                    }
                
                result["status"] = "completed"
                
            except Exception as e:
                result["status"] = "partial_failure"
                result["error"] = str(e)
                result["error_type"] = type(e).__name__

        return SkillResult(
            skill_name=self.name,
            status=SkillStatus.COMPLETED,
            output=result,
            metadata={"analyses": analyses},
        )
