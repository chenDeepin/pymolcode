#!/usr/bin/env python3
"""
Structure search script - fetches PDB structures from RCSB for a target.
"""

import argparse
import json
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Optional, List

import requests


RCSB_SEARCH = "https://search.rcsb.org/rcsbsearch/v2/query"
RCSB_ENTRY = "https://data.rcsb.org/rest/v1/core/entry"
RCSB_NONPOLY = "https://data.rcsb.org/rest/v1/core/nonpolymer_entity"
RCSB_WEB = "https://www.rcsb.org/structure"


@dataclass
class PDBEntry:
    """PDB structure entry."""
    pdb_id: str
    uniprot_accession: str
    title: Optional[str]
    method: Optional[str]
    resolution: Optional[float]
    pubmed_id: Optional[str]
    release_date: Optional[str]
    ligand_ids: str
    ligand_names: str
    rcsb_url: str
    status: str


def _post_json(url: str, payload: dict, timeout_s: int = 30, retries: int = 3) -> dict:
    """POST JSON with retries."""
    last_exc = None
    for attempt in range(retries):
        try:
            r = requests.post(url, json=payload, timeout=timeout_s,
                            headers={"Accept": "application/json", "User-Agent": "Nanobot-DrugSearch/1.0"})
            if r.status_code == 204:
                return {"result_set": [], "total_count": 0}
            r.raise_for_status()
            return r.json()
        except Exception as e:
            last_exc = e
            time.sleep(0.5 * (2 ** attempt))
    raise RuntimeError(f"Failed after {retries} attempts") from last_exc


def _get_json(url: str, timeout_s: int = 30, retries: int = 3) -> dict:
    """GET JSON with retries."""
    last_exc = None
    for attempt in range(retries):
        try:
            r = requests.get(url, timeout=timeout_s,
                           headers={"Accept": "application/json", "User-Agent": "Nanobot-DrugSearch/1.0"})
            if r.status_code == 204:
                return {}
            r.raise_for_status()
            return r.json()
        except Exception as e:
            last_exc = e
            time.sleep(0.5 * (2 ** attempt))
    raise RuntimeError(f"Failed after {retries} attempts: {url}") from last_exc


def search_pdb_by_uniprot(uniprot: str, max_results: int = 100) -> List[str]:
    """Search PDB entries by UniProt accession."""
    payload = {
        "query": {
            "type": "terminal",
            "service": "text",
            "parameters": {
                "attribute": "rcsb_polymer_entity_container_identifiers.reference_sequence_identifiers.database_accession",
                "operator": "exact_match",
                "value": uniprot,
            },
        },
        "return_type": "entry",
        "request_options": {
            "paginate": {"start": 0, "rows": max_results},
        },
    }
    
    data = _post_json(RCSB_SEARCH, payload)
    pdb_ids = []
    for r in data.get("result_set", []):
        if r.get("identifier"):
            pdb_ids.append(r["identifier"].upper())
    return sorted(set(pdb_ids))


def fetch_entry_details(pdb_id: str) -> dict:
    """Fetch PDB entry details."""
    return _get_json(f"{RCSB_ENTRY}/{pdb_id}")


def extract_ligands(pdb_id: str, entry: dict) -> tuple:
    """Extract ligand information from PDB entry."""
    entity_ids = (entry.get("rcsb_entry_container_identifiers", {})
                  .get("non_polymer_entity_ids", []))
    
    lig_ids = []
    lig_names = []
    
    for ent_id in entity_ids:
        try:
            data = _get_json(f"{RCSB_NONPOLY}/{pdb_id}/{ent_id}")
            nonpoly = data.get("pdbx_entity_nonpoly", {})
            if nonpoly.get("comp_id"):
                lig_ids.append(nonpoly["comp_id"])
            if nonpoly.get("name"):
                lig_names.append(nonpoly["name"])
        except:
            continue
    
    # Deduplicate
    seen_ids = set()
    unique_ids = []
    for lid in lig_ids:
        if lid not in seen_ids:
            seen_ids.add(lid)
            unique_ids.append(lid)
    
    seen_names = set()
    unique_names = []
    for name in lig_names:
        if name not in seen_names:
            seen_names.add(name)
            unique_names.append(name)
    
    return ";".join(unique_ids), ";".join(unique_names)


def extract_resolution(entry: dict) -> Optional[float]:
    """Extract resolution from entry."""
    info = entry.get("rcsb_entry_info", {})
    res = info.get("resolution_combined")
    if isinstance(res, list) and res:
        try:
            return float(res[0])
        except:
            pass
    if isinstance(res, (int, float)):
        return float(res)
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Search RCSB PDB for target structures")
    parser.add_argument("--uniprot", required=True, help="UniProt accession")
    parser.add_argument("--out-dir", required=True, help="Output directory")
    parser.add_argument("--max-results", type=int, default=100, help="Max PDB entries")
    parser.add_argument("--sleep-s", type=float, default=0.05, help="Sleep between requests")
    args = parser.parse_args()
    
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Searching PDB for UniProt: {args.uniprot}")
    pdb_ids = search_pdb_by_uniprot(args.uniprot, args.max_results)
    print(f"Found {len(pdb_ids)} entries")
    
    entries: List[PDBEntry] = []
    
    for pdb_id in pdb_ids:
        try:
            entry = fetch_entry_details(pdb_id)
            time.sleep(args.sleep_s)
            
            lig_ids, lig_names = extract_ligands(pdb_id, entry)
            time.sleep(args.sleep_s)
            
            title = entry.get("struct", {}).get("title")
            method = (entry.get("exptl", [{}])[0] or {}).get("method")
            resolution = extract_resolution(entry)
            pubmed_id = entry.get("rcsb_entry_container_identifiers", {}).get("pubmed_id")
            release_date = entry.get("rcsb_accession_info", {}).get("initial_release_date")
            
            entries.append(PDBEntry(
                pdb_id=pdb_id,
                uniprot_accession=args.uniprot,
                title=title,
                method=method,
                resolution=resolution,
                pubmed_id=str(pubmed_id) if pubmed_id else None,
                release_date=release_date,
                ligand_ids=lig_ids,
                ligand_names=lig_names,
                rcsb_url=f"{RCSB_WEB}/{pdb_id}",
                status="ok"
            ))
        except Exception as e:
            entries.append(PDBEntry(
                pdb_id=pdb_id,
                uniprot_accession=args.uniprot,
                title=None, method=None, resolution=None,
                pubmed_id=None, release_date=None,
                ligand_ids="", ligand_names="",
                rcsb_url=f"{RCSB_WEB}/{pdb_id}",
                status=f"error: {e}"
            ))
    
    # Save manifest TSV
    import pandas as pd
    df = pd.DataFrame([asdict(e) for e in entries])
    if not df.empty:
        df = df.sort_values(["resolution", "pdb_id"], na_position="last")
    df.to_csv(out_dir / "pdb_manifest.tsv", sep="\t", index=False)
    
    # Save PDB ID list
    (out_dir / "pdb_ids.txt").write_text("\n".join(df["pdb_id"].tolist()) + "\n")
    
    # Summary
    ok = sum(1 for e in entries if e.status == "ok")
    with_ligands = sum(1 for e in entries if e.ligand_ids)
    print(f"Processed: {ok}/{len(entries)} entries")
    print(f"With ligands: {with_ligands}")
    print(f"Output: {out_dir}")


if __name__ == "__main__":
    main()
