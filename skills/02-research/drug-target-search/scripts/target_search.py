#!/usr/bin/env python3
"""
Target search script - fetches protein/target information from UniProt.
"""

import argparse
import json
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Optional

import requests


UNIPROT_API = "https://rest.uniprot.org/uniprotkb"


@dataclass
class TargetInfo:
    """Protein target information from UniProt."""
    target_name: str
    uniprot_id: str
    gene_name: Optional[str]
    protein_name: Optional[str]
    organism: Optional[str]
    function: Optional[str]
    disease_associations: list[str]
    keywords: list[str]
    length: Optional[int]
    status: str
    message: Optional[str]
    uniprot_url: Optional[str]


def _get_json(url: str, timeout_s: int = 30, retries: int = 3) -> dict:
    """Fetch JSON from URL with retries."""
    last_exc = None
    for attempt in range(retries):
        try:
            r = requests.get(url, timeout=timeout_s, headers={"Accept": "application/json"})
            r.raise_for_status()
            return r.json()
        except Exception as e:
            last_exc = e
            time.sleep(0.5 * (2 ** attempt))
    raise RuntimeError(f"Failed after {retries} attempts: {url}") from last_exc


def fetch_target_info(uniprot_id: str) -> TargetInfo:
    """Fetch target information from UniProt by accession."""
    url = f"{UNIPROT_API}/{uniprot_id}.json"
    uniprot_url = f"https://www.uniprot.org/uniprotkb/{uniprot_id}"
    
    try:
        data = _get_json(url)
        
        # Extract gene name
        gene_name = None
        genes = data.get("genes", [])
        if genes:
            gene_name = genes[0].get("geneName", {}).get("value")
        
        # Extract protein name
        protein_name = None
        protein_desc = data.get("proteinDescription", {})
        if protein_desc:
            rec_name = protein_desc.get("recommendedName", {})
            if rec_name:
                protein_name = rec_name.get("fullName", {}).get("value")
        
        # Extract organism
        organism = None
        organism_data = data.get("organism", {})
        if organism_data:
            organism = organism_data.get("scientificName")
        
        # Extract function
        function = None
        comments = data.get("comments", [])
        for comment in comments:
            if comment.get("commentType") == "FUNCTION":
                texts = comment.get("texts", [])
                if texts:
                    function = texts[0].get("value")
                break
        
        # Extract disease associations
        diseases = []
        for comment in comments:
            if comment.get("commentType") == "DISEASE":
                disease_data = comment.get("disease", {})
                if disease_data.get("diseaseId"):
                    diseases.append(disease_data["diseaseId"])
        
        # Extract keywords
        keywords = []
        for kw in data.get("keywords", []):
            if kw.get("value"):
                keywords.append(kw["value"])
        
        # Get sequence length
        length = None
        sequence = data.get("sequence", {})
        if sequence:
            length = sequence.get("length")
        
        return TargetInfo(
            target_name=gene_name or uniprot_id,
            uniprot_id=uniprot_id,
            gene_name=gene_name,
            protein_name=protein_name,
            organism=organism,
            function=function,
            disease_associations=diseases,
            keywords=keywords[:20],  # Limit keywords
            length=length,
            status="ok",
            message=None,
            uniprot_url=uniprot_url
        )
    
    except requests.HTTPError as e:
        status = "not_found" if e.response.status_code == 404 else "http_error"
        return TargetInfo(
            target_name=uniprot_id,
            uniprot_id=uniprot_id,
            gene_name=None,
            protein_name=None,
            organism=None,
            function=None,
            disease_associations=[],
            keywords=[],
            length=None,
            status=status,
            message=str(e),
            uniprot_url=uniprot_url
        )
    except Exception as e:
        return TargetInfo(
            target_name=uniprot_id,
            uniprot_id=uniprot_id,
            gene_name=None,
            protein_name=None,
            organism=None,
            function=None,
            disease_associations=[],
            keywords=[],
            length=None,
            status="error",
            message=str(e),
            uniprot_url=uniprot_url
        )


def format_summary(info: TargetInfo) -> str:
    """Format target info as markdown summary."""
    lines = [f"# Target: {info.target_name}\n"]
    lines.append(f"**UniProt ID**: [{info.uniprot_id}]({info.uniprot_url})\n")
    
    if info.protein_name:
        lines.append(f"**Protein**: {info.protein_name}\n")
    if info.organism:
        lines.append(f"**Organism**: {info.organism}\n")
    if info.length:
        lines.append(f"**Length**: {info.length} aa\n")
    
    if info.function:
        lines.append(f"\n## Function\n{info.function}\n")
    
    if info.disease_associations:
        lines.append(f"\n## Disease Associations\n")
        for disease in info.disease_associations:
            lines.append(f"- {disease}")
    
    if info.keywords:
        lines.append(f"\n## Keywords\n{', '.join(info.keywords[:10])}\n")
    
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch target info from UniProt")
    parser.add_argument("--target", required=True, help="Target name (for reference)")
    parser.add_argument("--uniprot", required=True, help="UniProt accession (e.g., P56817)")
    parser.add_argument("--out-dir", required=True, help="Output directory")
    args = parser.parse_args()
    
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Fetching target info: {args.target} ({args.uniprot})")
    info = fetch_target_info(args.uniprot)
    
    # Save JSON
    json_path = out_dir / "target_info.json"
    json_path.write_text(json.dumps(asdict(info), indent=2) + "\n")
    
    # Save markdown summary
    summary_path = out_dir / "target_summary.md"
    summary_path.write_text(format_summary(info))
    
    print(f"Status: {info.status}")
    print(f"Output: {out_dir}")


if __name__ == "__main__":
    main()
