#!/usr/bin/env python3
"""
Compound search script - fetches compound properties from PubChem and ChEMBL.
"""

import argparse
import json
import time
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Any, Optional, List
from urllib.parse import quote

import requests


PUBCHEM_PUG = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
CHEMBL_API = "https://www.ebi.ac.uk/chembl/api/data"


@dataclass
class PubChemResult:
    """Compound data from PubChem."""
    compound_name: str
    cid: Optional[int]
    canonical_smiles: Optional[str]
    isomeric_smiles: Optional[str]
    inchi: Optional[str]
    inchikey: Optional[str]
    molecular_formula: Optional[str]
    molecular_weight: Optional[float]
    xlogp: Optional[float]
    tpsa: Optional[float]
    hbd: Optional[int]
    hba: Optional[int]
    rotatable_bonds: Optional[int]
    status: str
    message: Optional[str]
    pubchem_url: Optional[str]


@dataclass
class ChEMBLResult:
    """Compound data from ChEMBL."""
    compound_name: str
    molecule_chembl_id: Optional[str]
    pref_name: Optional[str]
    max_phase: Optional[int]
    molecule_type: Optional[str]
    canonical_smiles: Optional[str]
    inchikey: Optional[str]
    status: str
    message: Optional[str]
    chembl_url: Optional[str]


def _get_json(url: str, timeout_s: int = 30, retries: int = 3) -> dict:
    """Fetch JSON from URL with retries."""
    last_exc = None
    for attempt in range(retries):
        try:
            r = requests.get(url, timeout=timeout_s)
            if r.status_code == 404:
                return {}
            r.raise_for_status()
            return r.json()
        except Exception as e:
            last_exc = e
            time.sleep(0.5 * (2 ** attempt))
    raise RuntimeError(f"Failed after {retries} attempts: {url}") from last_exc


def fetch_pubchem(name: str) -> PubChemResult:
    """Fetch compound properties from PubChem."""
    props = [
        "CanonicalSMILES", "IsomericSMILES", "InChI", "InChIKey",
        "MolecularFormula", "MolecularWeight", "XLogP", "TPSA",
        "HBondDonorCount", "HBondAcceptorCount", "RotatableBondCount"
    ]
    url = f"{PUBCHEM_PUG}/compound/name/{quote(name)}/property/{','.join(props)}/JSON"
    pubchem_url = f"https://pubchem.ncbi.nlm.nih.gov/compound/{quote(name)}"
    
    try:
        data = _get_json(url)
        props_list = data.get("PropertyTable", {}).get("Properties", [])
        
        if not props_list:
            return PubChemResult(
                compound_name=name, cid=None, canonical_smiles=None,
                isomeric_smiles=None, inchi=None, inchikey=None,
                molecular_formula=None, molecular_weight=None, xlogp=None,
                tpsa=None, hbd=None, hba=None, rotatable_bonds=None,
                status="not_found", message="No properties returned",
                pubchem_url=pubchem_url
            )
        
        p = props_list[0]
        return PubChemResult(
            compound_name=name,
            cid=int(p["CID"]) if p.get("CID") else None,
            canonical_smiles=p.get("CanonicalSMILES"),
            isomeric_smiles=p.get("IsomericSMILES"),
            inchi=p.get("InChI"),
            inchikey=p.get("InChIKey"),
            molecular_formula=p.get("MolecularFormula"),
            molecular_weight=float(p["MolecularWeight"]) if p.get("MolecularWeight") else None,
            xlogp=float(p["XLogP"]) if p.get("XLogP") else None,
            tpsa=float(p["TPSA"]) if p.get("TPSA") else None,
            hbd=int(p["HBondDonorCount"]) if p.get("HBondDonorCount") else None,
            hba=int(p["HBondAcceptorCount"]) if p.get("HBondAcceptorCount") else None,
            rotatable_bonds=int(p["RotatableBondCount"]) if p.get("RotatableBondCount") else None,
            status="ok",
            message=None,
            pubchem_url=pubchem_url
        )
    except Exception as e:
        return PubChemResult(
            compound_name=name, cid=None, canonical_smiles=None,
            isomeric_smiles=None, inchi=None, inchikey=None,
            molecular_formula=None, molecular_weight=None, xlogp=None,
            tpsa=None, hbd=None, hba=None, rotatable_bonds=None,
            status="error", message=str(e), pubchem_url=pubchem_url
        )


def fetch_chembl(name: str) -> ChEMBLResult:
    """Fetch compound data from ChEMBL."""
    urls = [
        f"{CHEMBL_API}/molecule?pref_name__iexact={quote(name)}&format=json",
        f"{CHEMBL_API}/molecule/search?q={quote(name)}&format=json",
    ]
    
    for url in urls:
        try:
            data = _get_json(url)
            molecules = data.get("molecules", [])
            if not molecules:
                continue
            
            m = molecules[0]
            mol_id = m.get("molecule_chembl_id")
            structures = m.get("molecule_structures", {})
            
            max_phase = m.get("max_phase")
            try:
                max_phase = int(float(max_phase)) if max_phase else None
            except:
                max_phase = None
            
            return ChEMBLResult(
                compound_name=name,
                molecule_chembl_id=mol_id,
                pref_name=m.get("pref_name"),
                max_phase=max_phase,
                molecule_type=m.get("molecule_type"),
                canonical_smiles=structures.get("canonical_smiles"),
                inchikey=structures.get("standard_inchi_key"),
                status="ok",
                message=None,
                chembl_url=f"https://www.ebi.ac.uk/chembl/compound_report_card/{mol_id}/" if mol_id else None
            )
        except Exception as e:
            continue
    
    return ChEMBLResult(
        compound_name=name, molecule_chembl_id=None, pref_name=None,
        max_phase=None, molecule_type=None, canonical_smiles=None,
        inchikey=None, status="not_found", message="No molecules found",
        chembl_url=None
    )


def format_summary(pubchem_results: List[PubChemResult], chembl_results: List[ChEMBLResult]) -> str:
    """Format compound data as markdown summary."""
    lines = ["# Compound Search Results\n"]
    
    # PubChem section
    lines.append("## PubChem Results\n")
    lines.append("| Compound | CID | SMILES | MW | LogP | Status |")
    lines.append("|----------|-----|--------|-----|------|--------|")
    
    for r in pubchem_results:
        cid = str(r.cid) if r.cid else "-"
        smiles = r.canonical_smiles[:30] + "..." if r.canonical_smiles and len(r.canonical_smiles) > 30 else (r.canonical_smiles or "-")
        mw = f"{r.molecular_weight:.1f}" if r.molecular_weight else "-"
        logp = f"{r.xlogp:.1f}" if r.xlogp else "-"
        lines.append(f"| {r.compound_name} | {cid} | {smiles} | {mw} | {logp} | {r.status} |")
    
    # ChEMBL section
    lines.append("\n## ChEMBL Results\n")
    lines.append("| Compound | ChEMBL ID | Max Phase | Type | Status |")
    lines.append("|----------|-----------|-----------|------|--------|")
    
    for r in chembl_results:
        chembl_id = r.molecule_chembl_id or "-"
        phase = str(r.max_phase) if r.max_phase is not None else "-"
        mol_type = r.molecule_type or "-"
        lines.append(f"| {r.compound_name} | {chembl_id} | {phase} | {mol_type} | {r.status} |")
    
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch compound data from PubChem and ChEMBL")
    parser.add_argument("--names", required=True, help="Comma-separated compound names")
    parser.add_argument("--out-dir", required=True, help="Output directory")
    parser.add_argument("--sleep-s", type=float, default=0.2, help="Sleep between requests")
    args = parser.parse_args()
    
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    names = [n.strip() for n in args.names.split(",") if n.strip()]
    
    pubchem_results: List[PubChemResult] = []
    chembl_results: List[ChEMBLResult] = []
    
    for name in names:
        print(f"Fetching: {name}")
        
        # PubChem
        pubchem_results.append(fetch_pubchem(name))
        time.sleep(args.sleep_s)
        
        # ChEMBL
        chembl_results.append(fetch_chembl(name))
        time.sleep(args.sleep_s)
    
    # Save TSVs
    import pandas as pd
    
    pubchem_df = pd.DataFrame([asdict(r) for r in pubchem_results])
    pubchem_df.to_csv(out_dir / "pubchem_compounds.tsv", sep="\t", index=False)
    
    chembl_df = pd.DataFrame([asdict(r) for r in chembl_results])
    chembl_df.to_csv(out_dir / "chembl_compounds.tsv", sep="\t", index=False)
    
    # Save summary
    summary = format_summary(pubchem_results, chembl_results)
    (out_dir / "compounds_summary.md").write_text(summary)
    
    # Stats
    pubchem_ok = sum(1 for r in pubchem_results if r.status == "ok")
    chembl_ok = sum(1 for r in chembl_results if r.status == "ok")
    print(f"PubChem: {pubchem_ok}/{len(names)} found")
    print(f"ChEMBL: {chembl_ok}/{len(names)} found")
    print(f"Output: {out_dir}")


if __name__ == "__main__":
    main()
