#!/usr/bin/env python3
"""
Patent search script - searches Google Patents for drug discovery patents.
Supports company/assignee, disease, target, and drug type searches.
"""

import argparse
import json
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List
from datetime import datetime
from urllib.parse import quote

import requests


@dataclass
class PatentResult:
    """Patent search result."""
    patent_id: str
    title: str
    abstract: str
    assignee: str
    inventors: str
    filing_date: Optional[str]
    publication_date: Optional[str]
    priority_date: Optional[str]
    url: str
    relevance: str
    compounds: List[str] = field(default_factory=list)
    targets: List[str] = field(default_factory=list)
    ic50_values: List[str] = field(default_factory=list)
    indications: List[str] = field(default_factory=list)


def search_google_patents(query: str, count: int = 30) -> List[PatentResult]:
    """Search Google Patents and extract results."""
    results = []
    
    try:
        # Build Google Patents search URL
        search_url = f"https://patents.google.com/?q={quote(query)}&oq={quote(query)}&sort=new"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5"
        }
        
        r = requests.get(search_url, headers=headers, timeout=30)
        r.raise_for_status()
        
        html = r.text
        
        # Extract patent data from HTML
        # Look for patent entries in the search results
        
        # Pattern 1: Extract patent IDs
        patent_pattern = r'href="/patent/([A-Z]{2}\d+[A-Z]?)'
        patent_ids = list(dict.fromkeys(re.findall(patent_pattern, html)))[:count]
        
        # Pattern 2: Extract titles (in h3 or article elements)
        title_pattern = r'<h3[^>]*>.*?<a[^>]*>([^<]+)</a>.*?</h3>'
        titles = re.findall(title_pattern, html, re.DOTALL)
        
        # Pattern 3: Extract assignees
        assignee_pattern = r'assignee["\s:]+([^"<>,]+)'
        assignees = re.findall(assignee_pattern, html, re.IGNORECASE)
        
        # Pattern 4: Extract dates
        date_pattern = r'(\d{4}-\d{2}-\d{2})'
        dates = re.findall(date_pattern, html)
        
        # Build results
        for i, pid in enumerate(patent_ids):
            title = titles[i] if i < len(titles) else ""
            assignee = assignees[i] if i < len(assignees) else ""
            
            # Clean up
            title = re.sub(r'\s+', ' ', title).strip()
            assignee = re.sub(r'\s+', ' ', assignee).strip()
            
            results.append(PatentResult(
                patent_id=pid,
                title=title[:200] if title else f"Patent {pid}",
                abstract="",
                assignee=assignee[:100] if assignee else "",
                inventors="",
                filing_date=None,
                publication_date=None,
                priority_date=None,
                url=f"https://patents.google.com/patent/{pid}",
                relevance="high"
            ))
        
    except Exception as e:
        print(f"Warning: Google Patents search error: {e}")
    
    return results


def fetch_patent_details(patent_id: str) -> dict:
    """Fetch detailed information for a single patent."""
    try:
        url = f"https://patents.google.com/patent/{patent_id}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
        
        r = requests.get(url, headers=headers, timeout=15)
        r.raise_for_status()
        
        html = r.text
        
        # Extract title
        title_match = re.search(r'<title>([^|]+)', html)
        title = title_match.group(1).strip() if title_match else ""
        
        # Extract abstract
        abstract_match = re.search(r'<abstract[^>]*>(.*?)</abstract>', html, re.DOTALL)
        abstract = ""
        if abstract_match:
            abstract = re.sub(r'<[^>]+>', '', abstract_match.group(1))
            abstract = re.sub(r'\s+', ' ', abstract).strip()
        
        # Extract assignee
        assignee_match = re.search(r'assignee[^>]*>([^<]+)', html, re.IGNORECASE)
        assignee = assignee_match.group(1).strip() if assignee_match else ""
        
        # Extract dates
        pub_date_match = re.search(r'publication date[^>]*>(\d{4}-\d{2}-\d{2})', html, re.IGNORECASE)
        filing_date_match = re.search(r'filing date[^>]*>(\d{4}-\d{2}-\d{2})', html, re.IGNORECASE)
        priority_date_match = re.search(r'priority date[^>]*>(\d{4}-\d{2}-\d{2})', html, re.IGNORECASE)
        
        # Extract inventors
        inventor_pattern = r'inventor[^>]*name[^>]*>([^<]+)'
        inventors = re.findall(inventor_pattern, html, re.IGNORECASE)
        
        return {
            "title": title[:300],
            "abstract": abstract[:2000],
            "assignee": assignee[:200],
            "inventors": "; ".join(inventors[:5]),
            "publication_date": pub_date_match.group(1) if pub_date_match else None,
            "filing_date": filing_date_match.group(1) if filing_date_match else None,
            "priority_date": priority_date_match.group(1) if priority_date_match else None
        }
        
    except Exception as e:
        return {"error": str(e)}


def build_patent_query(
    company: str = None,
    target: str = None,
    disease: str = None,
    drug_type: str = None,
    mechanism: str = None,
    compound: str = None
) -> str:
    """Build an effective patent search query."""
    terms = []
    
    # Company/Assignee
    if company:
        terms.append(f'assignee:("{company}")')
    
    # Target
    if target:
        terms.append(f'("{target}")')
    
    # Disease indication
    if disease:
        terms.append(f'("{disease}")')
    
    # Drug type
    if drug_type:
        drug_type = drug_type.lower()
        if "small molecule" in drug_type:
            terms.append("(compound OR molecule OR inhibitor OR agonist)")
        elif "antibody" in drug_type:
            terms.append("(antibody OR monoclonal OR mAb)")
        else:
            terms.append(f"({drug_type})")
    
    # Mechanism
    if mechanism:
        terms.append(f'("{mechanism}")')
    
    # Compound
    if compound:
        terms.append(f'("{compound}")')
    
    # Add pharmaceutical context if no company specified
    if not company:
        terms.append("(pharmaceutical OR therapeutic OR drug OR medicine)")
    
    return " ".join(terms)


def format_summary(results: List[PatentResult], query: str, company: str = None) -> str:
    """Format patent results as markdown summary."""
    lines = [f"# Patent Search Results\n"]
    lines.append(f"**Query**: {query}\n")
    if company:
        lines.append(f"**Company Filter**: {company}\n")
    lines.append(f"**Results Found**: {len(results)} patents\n")
    lines.append(f"**Sorted by**: Newest first\n")
    
    if not results:
        lines.append("\nNo patents found. Try different search terms.\n")
        return "\n".join(lines)
    
    lines.append("\n---\n")
    
    for i, p in enumerate(results, 1):
        lines.append(f"## {i}. [{p.patent_id}]({p.url})\n")
        
        if p.title:
            lines.append(f"**Title**: {p.title}\n")
        
        lines.append("| Field | Value |")
        lines.append("|-------|-------|")
        
        if p.assignee:
            lines.append(f"| **Assignee** | {p.assignee} |")
        if p.publication_date:
            lines.append(f"| **Published** | {p.publication_date} |")
        if p.filing_date:
            lines.append(f"| **Filed** | {p.filing_date} |")
        if p.priority_date:
            lines.append(f"| **Priority** | {p.priority_date} |")
        if p.inventors:
            lines.append(f"| **Inventors** | {p.inventors[:100]} |")
        
        lines.append("")
        
        if p.abstract:
            lines.append(f"**Abstract**: {p.abstract[:500]}...\n")
        
        lines.append("---\n")
    
    return "\n".join(lines)


def generate_llm_analysis_prompt(results: List[PatentResult], query: str, company: str = None) -> str:
    """Generate a detailed prompt for LLM analysis."""
    prompt = f"""# Patent Analysis Task

## Search Parameters
- **Query**: {query}
- **Company**: {company or "Not specified"}
- **Patents Found**: {len(results)}

## Analysis Instructions

Please analyze these patents and provide:

### 1. Executive Summary
- What is the overall strategic direction of {company or "the company"}'s R&D?
- What therapeutic areas are they focusing on?

### 2. Key Compounds
List the most interesting novel compounds mentioned:
| Patent | Compound/Example | Indication | Key Data |
|--------|-----------------|------------|----------|

### 3. Target Landscape
What biological targets are being pursued?
| Target | Number of Patents | Disease Area |
|--------|------------------|--------------|

### 4. Technology Trends
- What drug modalities (small molecule, antibody, etc.)?
- What chemical scaffolds are emerging?
- Any novel mechanisms of action?

### 5. Competitive Intelligence
- What's the priority date range? (shows R&D timeline)
- How does this compare to competitors?
- Any surprising pivots or new directions?

### 6. Clinical Potential
- Which patents have the highest clinical potential?
- Any Phase-ready compounds mentioned?

### 7. IP Strategy
- Geographic coverage (US, WO, EP, etc.)
- Breadth of claims
- Key patents to watch

## Patent Data for Analysis

"""
    for i, p in enumerate(results[:15], 1):  # Limit for LLM context
        prompt += f"\n### Patent {i}: {p.patent_id}\n"
        prompt += f"- **Title**: {p.title}\n"
        prompt += f"- **Assignee**: {p.assignee}\n"
        prompt += f"- **Published**: {p.publication_date}\n"
        prompt += f"- **Priority**: {p.priority_date}\n"
        prompt += f"- **Abstract**: {p.abstract[:800] if p.abstract else 'N/A'}\n"
        prompt += f"- **URL**: {p.url}\n"
    
    return prompt


def main() -> None:
    parser = argparse.ArgumentParser(description="Search patents for drug discovery")
    
    # Search parameters
    parser.add_argument("--query", help="Direct patent search query")
    parser.add_argument("--company", help="Company/Assignee name (e.g., 'Novartis')")
    parser.add_argument("--target", help="Target name (e.g., 'CDK4')")
    parser.add_argument("--disease", help="Disease indication (e.g., 'cancer')")
    parser.add_argument("--drug-type", help="Drug type: 'small molecule', 'antibody', etc.")
    parser.add_argument("--mechanism", help="Mechanism (e.g., 'inhibitor')")
    parser.add_argument("--compound", help="Compound name")
    
    # Output options
    parser.add_argument("--out-dir", required=True, help="Output directory")
    parser.add_argument("--count", type=int, default=30, help="Number of results")
    parser.add_argument("--fetch-details", action="store_true", help="Fetch detailed patent info (slower)")
    
    args = parser.parse_args()
    
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # Build query
    if args.query:
        query = args.query
    else:
        query = build_patent_query(
            company=args.company,
            target=args.target,
            disease=args.disease,
            drug_type=args.drug_type,
            mechanism=args.mechanism,
            compound=args.compound
        )
    
    print(f"Searching patents: {query}")
    print(f"Company filter: {args.company or 'None'}")
    
    # Search
    results = search_google_patents(query, args.count)
    print(f"Found {len(results)} patents")
    
    # Fetch details if requested
    if args.fetch_details and results:
        print("Fetching patent details...")
        for i, p in enumerate(results):
            print(f"  [{i+1}/{len(results)}] {p.patent_id}...", end="", flush=True)
            details = fetch_patent_details(p.patent_id)
            if "error" not in details:
                p.title = details.get("title", p.title)
                p.abstract = details.get("abstract", "")
                p.assignee = details.get("assignee", p.assignee)
                p.inventors = details.get("inventors", "")
                p.publication_date = details.get("publication_date")
                p.filing_date = details.get("filing_date")
                p.priority_date = details.get("priority_date")
            print(" done")
            time.sleep(0.5)  # Be polite
    
    # Save JSON
    json_data = []
    for p in results:
        json_data.append({
            "patent_id": p.patent_id,
            "title": p.title,
            "abstract": p.abstract,
            "assignee": p.assignee,
            "inventors": p.inventors,
            "filing_date": p.filing_date,
            "publication_date": p.publication_date,
            "priority_date": p.priority_date,
            "url": p.url,
            "relevance": p.relevance
        })
    
    (out_dir / "patent_results.json").write_text(
        json.dumps(json_data, indent=2) + "\n"
    )
    
    # Save summary
    summary = format_summary(results, query, args.company)
    (out_dir / "patent_summary.md").write_text(summary)
    
    # Generate LLM analysis prompt
    llm_prompt = generate_llm_analysis_prompt(results, query, args.company)
    (out_dir / "patent_llm_prompt.md").write_text(llm_prompt)
    
    print(f"\n{'='*60}")
    print("RESULTS")
    print('='*60)
    print(f"Patents found: {len(results)}")
    print(f"Output directory: {out_dir}")
    print(f"  - patent_results.json")
    print(f"  - patent_summary.md")
    print(f"  - patent_llm_prompt.md")
    
    if results:
        print(f"\nTop 5 Newest Patents:")
        for p in results[:5]:
            print(f"  - [{p.patent_id}] {p.title[:60]}...")
    
    print(f"\n💡 Next step: Ask nanobot to read patent_llm_prompt.md for deep analysis")


if __name__ == "__main__":
    main()
